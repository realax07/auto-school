"""Общие фикстуры и хелперы API-тестов (TestClient, без сети).

Источник правды — approved-кейсы test-model/approved/add-registration-admin/
(TC-REG-001…018, TC-ADM-001…017, TC-NFR-001…003); контракты — sdd.md §3–§5.
Матрица кейс→тест — tests/README.md.

time.sleep запрещен (спека qa-pipeline): детерминизм достигается прямым
контролем БД (AUTOSCHOOL_DB_PATH в tmp_path) через sqlite3.
"""
import os
import sqlite3
import sys
from functools import lru_cache
from pathlib import Path

import bcrypt
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

os.environ.setdefault("ADMIN_USER", "admin")
os.environ.setdefault("ADMIN_PASSWORD_HASH", "x")
os.environ.setdefault("SECRET", "test-secret")

ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "admin-pass-2026"


@lru_cache(maxsize=1)
def admin_password_hash() -> str:
    """bcrypt-хэш тестового пароля админа (cost 12, как в sdd §5)."""
    return bcrypt.hashpw(
        ADMIN_PASSWORD.encode(), bcrypt.gensalt(rounds=12)
    ).decode()


@pytest.fixture()
def client(monkeypatch, tmp_path):
    """TestClient над create_app() с чистой БД в tmp_path (без сети)."""
    monkeypatch.setenv("ADMIN_USER", ADMIN_LOGIN)
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", admin_password_hash())
    monkeypatch.setenv("SECRET", "test-secret")
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(tmp_path / "app.db"))
    from fastapi.testclient import TestClient

    from backend.app import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c


def valid_body(**overrides):
    """Базовый валидный пользователь (базовый набор approved-кейсов)."""
    body = {
        "surname": "Петрова-Водкина",
        "name": "Анна",
        "patronymic": "Оттовна",
        "email": "petrova@example.com",
        "phone": "+7 (912) 345-67-89",
        "password": "Qwerty123",
        "password_confirm": "Qwerty123",
    }
    body.update(overrides)
    return body


def register(client, **overrides):
    """POST /api/register с базовым набором и переопределениями."""
    return client.post("/api/register", json=valid_body(**overrides))


def admin_headers(client):
    """Успешный вход администратора → заголовок X-Admin-Token."""
    resp = client.post(
        "/api/admin/login",
        json={"login": ADMIN_LOGIN, "password": ADMIN_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
    return {"X-Admin-Token": resp.json()["token"]}


def db_path() -> str:
    return os.environ["AUTOSCHOOL_DB_PATH"]


def fetch_user(email):
    """Прямой SELECT из users (тот же файл, что использует приложение)."""
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return row


def count_users() -> int:
    """SELECT COUNT(*) FROM users."""
    conn = sqlite3.connect(db_path())
    n = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return n
