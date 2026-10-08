"""Тесты POST /api/register (задача 2.1, sdd.md §3.1).

Контракт: 200 {ok:true}; 422 {ok:false, error:"<поле-ру>: <причина>"} —
первая ошибка; хендлерная валидация (MAJ-1): отсутствующий ключ JSON = пустое
поле → контрактный 422, не Pydantic {detail:[...]}.
Порядок проверок: обязательность всех полей → формат email → телефон ≥ 10
цифр → пароль ≥ 8 → совпадение подтверждения → уникальность email.
"""
import os
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

os.environ.setdefault("ADMIN_USER", "admin")
os.environ.setdefault("ADMIN_PASSWORD_HASH", "x")
os.environ.setdefault("SECRET", "test-secret")

from fastapi.testclient import TestClient  # noqa: E402

import backend.db as db  # noqa: E402
from backend.app import create_app  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(tmp_path / "app.db"))
    app = create_app()
    with TestClient(app) as c:
        yield c


def valid_body(**overrides):
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
    return body


def fetch_user(client, email):
    # прямой доступ к БД через тот же путь, что и приложение
    import backend.app as appmod

    db_path = os.environ["AUTOSCHOOL_DB_PATH"]
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return row


def count_users():
    db_path = os.environ["AUTOSCHOOL_DB_PATH"]
    conn = sqlite3.connect(db_path)
    n = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return n


# --- Успешная регистрация ---

def test_register_success(client):
    resp = client.post("/api/register", json=valid_body())
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_register_creates_record_with_all_fields(client):
    client.post("/api/register", json=valid_body())
    row = fetch_user(client, "ivanov@example.com")
    assert row is not None
    assert row["surname"] == "Иванов"
    assert row["name"] == "Иван"
    assert row["patronymic"] == "Иванович"
    assert row["email"] == "ivanov@example.com"
    assert row["phone"] == "+7 (912) 000-11-22"


def test_password_stored_as_bcrypt_hash_not_plaintext(client):
    client.post("/api/register", json=valid_body())
    row = fetch_user(client, "ivanov@example.com")
    import bcrypt

    assert row["password_hash"] != "secret1234"
    assert bcrypt.checkpw(b"secret1234", row["password_hash"].encode())
    assert row["password_hash"].startswith("$2")
    # cost 12
    assert int(row["password_hash"].split("$")[2]) == 12


# --- Негативные случаи FR-2 ---

def test_missing_field_returns_contract_422(client):
    # MAJ-1: ключ email отсутствует в JSON → контрактный формат, не Pydantic detail
    body = valid_body()
    del body["email"]
    resp = client.post("/api/register", json=body)
    assert resp.status_code == 422
    data = resp.json()
    assert data["ok"] is False
    assert data["error"].startswith("Email")
    assert "detail" not in data


def test_empty_required_field_rejected(client):
    resp = client.post("/api/register", json=valid_body(surname=""))
    assert resp.status_code == 422
    data = resp.json()
    assert data["ok"] is False
    assert data["error"].startswith("Фамилия") or data["error"].startswith("фамилия")


def test_first_error_wins_field_order(client):
    # несколько ошибок одновременно → возвращается первая по порядку полей
    resp = client.post(
        "/api/register",
        json=valid_body(surname="", name="", email="bad", password="123"),
    )
    assert resp.status_code == 422
    err = resp.json()["error"]
    assert "Фамилия" in err or "фамилия" in err


def test_invalid_email_format_rejected(client):
    for bad in ("no-at-marker", "a@b", "a@b.", "ab@example"):
        resp = client.post("/api/register", json=valid_body(email=bad))
        assert resp.status_code == 422, bad
        assert "email" in resp.json()["error"].lower() or "Email" in resp.json()["error"]


def test_phone_needs_10_digits(client):
    resp = client.post("/api/register", json=valid_body(phone="+7 (912) 000-00"))
    assert resp.status_code == 422
    assert "елефон" in resp.json()["error"]


def test_password_too_short_rejected(client):
    resp = client.post(
        "/api/register",
        json=valid_body(password="s1x", password_confirm="s1x"),
    )
    assert resp.status_code == 422
    assert "ароль" in resp.json()["error"]


def test_password_mismatch_rejected(client):
    resp = client.post(
        "/api/register",
        json=valid_body(password="secret1234", password_confirm="secret4321"),
    )
    assert resp.status_code == 422
    err = resp.json()["error"].lower()
    assert "овпадение" in err or "подтвержден" in err


def test_duplicate_email_rejected_as_422_not_500(client):
    client.post("/api/register", json=valid_body())
    resp = client.post(
        "/api/register",
        json=valid_body(surname="Петров", name="Петр", patronymic="Петрович"),
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["ok"] is False
    assert "mail" in data["error"] or "email" in data["error"].lower()


def test_no_record_created_on_rejection(client):
    for body in (
        valid_body(email="bad"),
        valid_body(phone="123"),
        valid_body(password="short", password_confirm="short"),
        valid_body(password="secret1234", password_confirm="other1234"),
    ):
        client.post("/api/register", json=body)
    assert count_users() == 0


def test_missing_surname_key_order(client):
    # отсутствие самого первого ключа → ошибка по surname
    body = valid_body()
    del body["surname"]
    resp = client.post("/api/register", json=body)
    assert resp.status_code == 422
    err = resp.json()["error"]
    assert "амилия" in err
    assert "detail" not in resp.json()
