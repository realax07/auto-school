"""TC-ADM-001…TC-ADM-004, TC-ADM-013…TC-ADM-017 — POST /api/admin/login
и механизм токена (задача 3.1, sdd.md §3.2, §3.5).

200 {ok:true, token: secrets.token_urlsafe(32)}; 401 {ok:false} — без
ключа token; админ-API без/с поддельным/с истекшим токеном → 401.
"""
import time

import pytest

from conftest import (
    ADMIN_LOGIN,
    ADMIN_PASSWORD,
    admin_headers,
    count_users,
    register,
)


def login(client, login=ADMIN_LOGIN, password=ADMIN_PASSWORD):
    return client.post(
        "/api/admin/login", json={"login": login, "password": password}
    )


# --- TC-ADM-001: Успешный вход администратора --------------------------------


def test_tc_adm_001_admin_login_success_opens_admin_api(client):
    """TC-ADM-001: Успешный вход администратора.

    POST /api/admin/login с login = ADMIN_USER и паролем, соответствующим
    ADMIN_PASSWORD_HASH → 200 {"ok": true, "token": "<строка>"}; token
    непуст (secrets.token_urlsafe, ≥ 32 символов); GET /api/admin/users с
    X-Admin-Token → 200 {"count": N, "users": [...]} — доступ открыт.
    """
    resp = login(client)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    token = data["token"]
    assert isinstance(token, str) and len(token) >= 32

    resp = client.get("/api/admin/users", headers={"X-Admin-Token": token})
    assert resp.status_code == 200
    assert "count" in resp.json() and "users" in resp.json()


# --- TC-ADM-002: верный логин, неверный пароль -------------------------------


def test_tc_adm_002_wrong_password_no_token_no_access(client):
    """TC-ADM-002: Вход с корректным логином и неверным паролем.

    login = ADMIN_USER, password = "WrongPass1" → 401 {"ok": false}; ключ
    token в теле ОТСУТСТВУЕТ — токен не выдан; GET /api/admin/users без
    валидного токена → 401 — доступ не открыт.
    """
    resp = login(client, password="WrongPass1")
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}
    assert "token" not in resp.json()

    assert client.get("/api/admin/users").status_code == 401


# --- TC-ADM-003: логин не совпадает с ADMIN_USER -----------------------------


def test_tc_adm_003_unknown_login_rejected_with_any_password(client):
    """TC-ADM-003: Вход с логином, не совпадающим с ADMIN_USER.

    login = "root": с верным паролем и с "WrongPass1" — оба прогона →
    401 {"ok": false}; token отсутствует в обоих телах.
    """
    for password in (ADMIN_PASSWORD, "WrongPass1"):
        resp = login(client, login="root", password=password)
        assert resp.status_code == 401
        assert resp.json() == {"ok": False}
        assert "token" not in resp.json()


# --- TC-ADM-004: пустой логин и/или пароль -----------------------------------


@pytest.mark.parametrize(
    "creds",
    [
        ("", ADMIN_PASSWORD),  # пустой логин + верный пароль
        (ADMIN_LOGIN, ""),  # верный логин + пустой пароль
        ("", ""),  # оба пустые
    ],
    ids=["empty-login", "empty-password", "both-empty"],
)
def test_tc_adm_004_empty_credentials_rejected(client, creds):
    """TC-ADM-004: Границы учетных данных — пустой логин и/или пароль.

    Каждый из трех прогонов ({"", верный пароль}; {ADMIN_USER, ""};
    {"", ""}) → 401 {"ok": false}; token в теле отсутствует.
    """
    login_value, password = creds
    resp = login(client, login=login_value, password=password)
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}
    assert "token" not in resp.json()


# --- TC-ADM-013: валидный токен → данные -------------------------------------


def test_tc_adm_013_valid_token_returns_data_matching_db(client):
    """TC-ADM-013: Админ-API отвечает данным при валидном токене.

    Регистрация базового пользователя; успешный вход → token;
    GET /api/admin/users с X-Admin-Token → 200 {"count": 1, "users":
    [...]}; данные совпадают с записью в БД (fio, email, phone,
    created_at).
    """
    assert register(client).status_code == 200
    token = login(client).json()["token"]
    resp = client.get("/api/admin/users", headers={"X-Admin-Token": token})
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    user = data["users"][0]
    assert user["fio"] == "Петрова-Водкина Анна Оттовна"
    assert user["email"] == "petrova@example.com"
    assert user["phone"] == "+7 (912) 345-67-89"
    assert user["created_at"]


# --- TC-ADM-014: запрос без токена -------------------------------------------


def test_tc_adm_014_request_without_token_rejected(client):
    """TC-ADM-014: Запрос к админ-API БЕЗ заголовка X-Admin-Token.

    Ничего не логинясь: GET /api/admin/users → 401 {"ok": false} без
    users/count; GET /api/admin/users/export.csv → 401 {"ok": false},
    тело CSV данных не содержит.
    """
    resp = client.get("/api/admin/users")
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}
    assert "users" not in resp.json() and "count" not in resp.json()

    resp = client.get("/api/admin/users/export.csv")
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}
    assert "ФИО" not in resp.text


# --- TC-ADM-015: поддельный токен --------------------------------------------


def test_tc_adm_015_forged_token_rejected(client):
    """TC-ADM-015: Запрос с подделанным/несуществующим токеном.

    X-Admin-Token: "forged-token-0123456789abcdef" (значение, которое
    система не выдавала): GET /api/admin/users → 401 {"ok": false} без
    данных; GET /api/admin/users/export.csv → 401, тела CSV нет.
    """
    headers = {"X-Admin-Token": "forged-token-0123456789abcdef"}
    resp = client.get("/api/admin/users", headers=headers)
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}
    assert "users" not in resp.json()

    resp = client.get("/api/admin/users/export.csv", headers=headers)
    assert resp.status_code == 401
    assert "ФИО" not in resp.text


# --- TC-ADM-016: истекший токен ----------------------------------------------


def test_tc_adm_016_expired_token_rejected(client):
    """TC-ADM-016: Запрос с истекшим токен (D6: через прямой доступ к
    in-memory реестру backend.admin._tokens — время на уровне API не
    инъецируется).

    Вход → token T; с T доступ работает (200); tokens[T] = now − 1s;
    GET /api/admin/users с T → 401 {"ok": false}, данных нет.
    """
    token = login(client).json()["token"]
    resp = client.get("/api/admin/users", headers={"X-Admin-Token": token})
    assert resp.status_code == 200

    import backend.admin as admin

    admin._tokens[token] = time.time() - 1
    resp = client.get("/api/admin/users", headers={"X-Admin-Token": token})
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}


# --- TC-ADM-017: токен только после успешного входа --------------------------


def test_tc_adm_017_token_only_after_successful_login(client):
    """TC-ADM-017: Токен выдается ТОЛЬКО после успешного входа (FR-8).

    Неудачные входы {ADMIN_USER, "WrongPass1"}, {"root", верный},
    {"", ""} — каждый 401 {"ok": false} без token; до любого успешного
    входа произвольная строка в X-Admin-Token → 401; контроль: успешный
    вход → token, с ним GET /api/admin/users → 200.
    """
    for creds in (
        {"login": ADMIN_LOGIN, "password": "WrongPass1"},
        {"login": "root", "password": ADMIN_PASSWORD},
        {"login": "", "password": ""},
    ):
        resp = login(client, **creds)
        assert resp.status_code == 401
        assert "token" not in resp.json()

    resp = client.get(
        "/api/admin/users", headers={"X-Admin-Token": "anything"}
    )
    assert resp.status_code == 401

    token = login(client).json()["token"]
    resp = client.get("/api/admin/users", headers={"X-Admin-Token": token})
    assert resp.status_code == 200


# --- Регрессионный дубль: экспорт CSV без токена (TC-ADM-014, ветка CSV) -----


def test_tc_adm_014_export_without_token_empty_body(client):
    """TC-ADM-014: GET /api/admin/users/export.csv без заголовка и с
    плохим токеном → 401 и пустое тело данных (дубль-контроль ветки CSV
    вместе с test_tc_adm_014_request_without_token_rejected)."""
    resp = client.get("/api/admin/users/export.csv")
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}

    resp2 = client.get(
        "/api/admin/users/export.csv", headers={"X-Admin-Token": "bad"}
    )
    assert resp2.status_code == 401
    assert resp2.json() == {"ok": False}


# --- Контроль до-очистки: служебная проверка fixture-изоляции ----------------


def test_tc_adm_013_db_isolated_between_tests(client):
    """TC-ADM-013 (контроль изоляции): client дает чистую БД в tmp_path —
    COUNT(*) = 0 до регистраций в этом тесте (поддерживает предусловие
    «таблица users пуста» approved-кейсов)."""
    assert count_users() == 0
    assert admin_headers(client)["X-Admin-Token"]
