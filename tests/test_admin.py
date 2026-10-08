"""Тесты POST /api/admin/login + require_admin (задача 3.1, sdd.md §3.2, §3.5).

200 {ok:true, token}; 401 {ok:false} без токена; админ-API без/с поддельным/
с истекшим токеном → 401.
"""
import os
import sys
import time
from pathlib import Path

import bcrypt
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

TEST_PASSWORD = "admin-pass-2026"
TEST_HASH = bcrypt.hashpw(
    TEST_PASSWORD.encode(), bcrypt.gensalt(rounds=12)
).decode()


@pytest.fixture()
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_USER", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", TEST_HASH)
    monkeypatch.setenv("SECRET", "test-secret")
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(tmp_path / "app.db"))
    return env


@pytest.fixture()
def client(env):
    from fastapi.testclient import TestClient

    from backend.app import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c


def login(client, login="admin", password=TEST_PASSWORD):
    return client.post("/api/admin/login", json={"login": login, "password": password})


# --- Вход администратора ---

def test_admin_login_success(client):
    resp = login(client)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    token = data["token"]
    assert isinstance(token, str) and len(token) >= 32


def test_admin_login_wrong_password(client):
    resp = login(client, password="wrong-password")
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}


def test_admin_login_unknown_login(client):
    resp = login(client, login="hacker", password=TEST_PASSWORD)
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}
    assert "token" not in resp.json()


# --- Токен-механизм (require_admin) ---

def test_users_endpoint_requires_token(client):
    resp = client.get("/api/admin/users")
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}


def test_users_endpoint_rejects_fake_token(client):
    resp = client.get("/api/admin/users", headers={"X-Admin-Token": "fake-token"})
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}


def test_users_endpoint_accepts_valid_token(client):
    token = login(client).json()["token"]
    resp = client.get("/api/admin/users", headers={"X-Admin-Token": token})
    assert resp.status_code == 200


def test_expired_token_rejected(client, env):
    token = login(client).json()["token"]
    # форсируем истечение TTL в реестре
    import backend.admin as admin

    admin._tokens[token] = time.time() - 1
    resp = client.get("/api/admin/users", headers={"X-Admin-Token": token})
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}


def test_export_endpoint_requires_token(client):
    resp = client.get("/api/admin/users/export.csv")
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}
    assert resp.content in (b"", b'{"ok":false}')
