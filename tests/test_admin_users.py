"""Тесты GET /api/admin/users и GET /api/admin/users/export.csv
(задачи 3.2, 3.3; sdd.md §3.3, §3.4; MIN-3 тай-брейк, MIN-4 UTC→локаль,
MAJ-2 CSV-санитизация)."""
import os
import sys
from pathlib import Path

import bcrypt
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

TEST_PASSWORD = "admin-pass-2026"
TEST_HASH = bcrypt.hashpw(TEST_PASSWORD.encode(), bcrypt.gensalt()).decode()


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_USER", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", TEST_HASH)
    monkeypatch.setenv("SECRET", "test-secret")
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(tmp_path / "app.db"))
    from fastapi.testclient import TestClient

    from backend.app import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c


def auth_headers(client):
    resp = client.post(
        "/api/admin/login",
        json={"login": "admin", "password": TEST_PASSWORD},
    )
    return {"X-Admin-Token": resp.json()["token"]}


def register(client, **overrides):
    body = {
        "surname": "Иванов",
        "name": "Иван",
        "patronymic": "Иванович",
        "email": "ivanov@example.com",
        "phone": "+7 (912) 000-11-22",
        "password": "secret1234",
        "password_confirm": "secret1234",
    }
    body.update(overrides)
    return client.post("/api/register", json=body)


# --- 3.2: список пользователей ---

def test_users_list_two_users_fresh_first(client):
    register(client, email="first@example.com", surname="Первый")
    import time as t

    t.sleep(1.1)  # гарантированно другая секунда created_at
    register(client, email="second@example.com", surname="Второй")
    resp = client.get("/api/admin/users", headers=auth_headers(client))
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert data["users"][0]["fio"].startswith("Второй")
    assert data["users"][1]["fio"].startswith("Первый")


def test_users_list_fio_is_joined(client):
    register(client)
    data = client.get("/api/admin/users", headers=auth_headers(client)).json()
    user = data["users"][0]
    assert user["fio"] == "Иванов Иван Иванович"
    assert user["email"] == "ivanov@example.com"
    assert user["phone"] == "+7 (912) 000-11-22"
    assert user["created_at"]


def test_users_list_same_second_id_desc_tiebreak(client):
    # MIN-3: обе записи в одну секунду → тай-брейк id DESC (свежий первым)
    register(client, email="a@example.com", surname="Раньше")
    register(client, email="b@example.com", surname="Позже")
    # принудительно выравниваем created_at в одну секунду
    import sqlite3

    conn = sqlite3.connect(os.environ["AUTOSCHOOL_DB_PATH"])
    conn.execute("UPDATE users SET created_at = '2026-10-08 07:00:00'")
    conn.commit()
    conn.close()
    data = client.get("/api/admin/users", headers=auth_headers(client)).json()
    assert data["users"][0]["email"] == "b@example.com"  # больший id первым
    assert data["users"][1]["email"] == "a@example.com"


# --- 3.3: CSV export ---

def test_csv_format_bom_header_delimiter(client):
    register(client)
    resp = client.get("/api/admin/users/export.csv", headers=auth_headers(client))
    assert resp.status_code == 200
    body = resp.content
    assert body.startswith(b"\xef\xbb\xbf")
    text = body.decode("utf-8-sig")
    lines = text.strip().split("\n")
    assert lines[0] == "ФИО;Email;Телефон;Роль;Дата регистрации"
    # строка на каждого пользователя + заголовок
    assert len(lines) == 2
    assert "Ученик" in lines[1]


def test_csv_row_per_user(client):
    register(client, email="a@example.com", surname="А")
    register(client, email="b@example.com", surname="Б")
    resp = client.get("/api/admin/users/export.csv", headers=auth_headers(client))
    text = resp.content.decode("utf-8-sig")
    lines = text.strip().split("\n")
    assert len(lines) == 3
    # свежий (Б) — первым (ORDER BY created_at DESC, id DESC)
    assert lines[1].split(";")[0] == "Б Иван Иванович"
    assert lines[2].split(";")[0] == "А Иван Иванович"


def test_csv_content_disposition(client):
    resp = client.get("/api/admin/users/export.csv", headers=auth_headers(client))
    assert resp.headers["content-type"].startswith("text/csv")
    assert 'attachment; filename="users.csv"' in resp.headers["content-disposition"]


def test_csv_sanitizes_formula_prefix(client):
    # email `=1+1@x` из примера tasks.md не проходит контрактную проверку
    # формата email (нет точки в домене, sdd §3.1), поэтому используем
    # допустимую альтернативу из tasks.md: ФИО `=1+1` + email с опасным
    # префиксом и валидным доменом
    register(
        client,
        email="=1+1@x.ru",
        surname="=1+1",
        name="Опасный",
        patronymic="Тест",
    )
    resp = client.get("/api/admin/users/export.csv", headers=auth_headers(client))
    text = resp.content.decode("utf-8-sig")
    assert "'=1+1@x.ru" in text
    assert "'=1+1 Опасный" in text
    # сырая формула без префикса не встречается в начале ячейки
    assert ";=1+1@x.ru" not in text


def test_csv_sanitize_plus_prefix(client):
    register(client, phone="+79001234567", email="plus@example.com")
    resp = client.get("/api/admin/users/export.csv", headers=auth_headers(client))
    text = resp.content.decode("utf-8-sig")
    assert "'+79001234567" in text


def test_csv_date_in_local_timezone(client):
    # MIN-4: created_at хранится в UTC; в CSV — локальный календарный день.
    # В тестовой зоне (UTC+3, МСК) регистрация в 00:30 UTC = 03:30 локального
    # того же дня; регистрация в 21:30 UTC предыдущего дня = 00:30 локального
    # следующего дня. Проверяем соответствие локальному дню для текущей записи.
    import sqlite3
    from datetime import datetime, timedelta, timezone

    register(client)
    conn = sqlite3.connect(os.environ["AUTOSCHOOL_DB_PATH"])
    # 00:30 UTC сегодня по локали может приходиться на другой локальный день,
    # поэтому берем «опасный» случай: 23:40 UTC вчерашнего дня → локальный
    # сегоднияшний день (при положительном смещении зоны)
    now_local = datetime.now().astimezone()
    utc_yesterday = (now_local - timedelta(days=1)).astimezone(timezone.utc)
    danger_utc = utc_yesterday.strftime("%Y-%m-%d") + " 23:40:00"
    conn.execute("UPDATE users SET created_at = ?", (danger_utc,))
    conn.commit()
    conn.close()

    resp = client.get("/api/admin/users/export.csv", headers=auth_headers(client))
    text = resp.content.decode("utf-8-sig")
    row = text.strip().split("\n")[1]
    date_str = row.split(";")[4]
    expected_local_day = (utc_yesterday + timedelta(hours=3)).strftime("%d.%m.%Y")
    # локальный день регистрации (для UTC+3 — день после UTC-дня)
    expected_local = datetime.strptime(
        danger_utc, "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=timezone.utc).astimezone().strftime("%d.%m.%Y")
    assert date_str == expected_local
    assert date_str == expected_local_day or expected_local == date_str


def test_csv_empty_no_users(client):
    resp = client.get("/api/admin/users/export.csv", headers=auth_headers(client))
    assert resp.status_code == 200
    body = resp.content
    assert body.startswith(b"\xef\xbb\xbf")
    text = body.decode("utf-8-sig")
    lines = text.strip().split("\n")
    assert lines == ["ФИО;Email;Телефон;Роль;Дата регистрации"]


def test_csv_unauthorized_empty_body(client):
    # без токена и с плохим токеном → 401 и пустое тело
    resp = client.get("/api/admin/users/export.csv")
    assert resp.status_code == 401
    assert resp.content == b'{"ok":false}'
    resp2 = client.get(
        "/api/admin/users/export.csv", headers={"X-Admin-Token": "bad"}
    )
    assert resp2.status_code == 401
    assert resp2.content == b'{"ok":false}'
