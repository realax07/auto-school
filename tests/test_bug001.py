"""BUG-001: регистрация → сессия → кабинет (rev-002 #1, #5).

Трассировка: test-model/bugs/BUG-001-register-redirect-cabinet.md;
TC-AUTH-017…019 (добавлены к семейству AUTH по rev-002).
"""
from fastapi.testclient import TestClient

import backend.db as db
from backend.app import create_app
from backend.db import init_db


def _client(tmp_path, monkeypatch):
    dbfile = tmp_path / "bug001.db"
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(dbfile))
    init_db()
    return TestClient(create_app())


VALID = {
    "email": "bug001@example.com",
    "password": "Pass123!",
    "password_confirm": "Pass123!",
    "surname": "Иванов",
    "name": "Иван",
    "patronymic": "Иванович",
    "phone": "+79990001122",
}


def test_tc_auth_017_register_issues_working_session(tmp_path, monkeypatch):
    """TC-AUTH-017: register 200 {ok, token} → /me по токену 200 {ok, user}.

    Регресс-защита фикса BUG-001 (rev-002 #1): без токена/с невалидным
    токеном тест падает."""
    client = _client(tmp_path, monkeypatch)
    resp = client.post("/api/register", json=VALID)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("ok") is True
    token = body.get("token")
    assert isinstance(token, str) and len(token) == 43  # token_urlsafe(32)

    me = client.get("/api/auth/me", headers={"X-Session-Token": token})
    assert me.status_code == 200
    assert me.json()["ok"] is True
    assert me.json()["user"]["email"] == VALID["email"]


def test_tc_auth_018_register_session_logout_invalidates(tmp_path, monkeypatch):
    """TC-AUTH-018: logout аннулирует сессию, выданную регистрацией."""
    client = _client(tmp_path, monkeypatch)
    client.post("/api/register", json=VALID)
    token = client.post("/api/register", json={**VALID, "email": "b18@example.com"}).json()["token"]
    lo = client.post("/api/auth/logout", headers={"X-Session-Token": token})
    assert lo.status_code == 200
    me = client.get("/api/auth/me", headers={"X-Session-Token": token})
    assert me.status_code == 401


def test_tc_auth_019_register_wiring_fragments():
    """TC-AUTH-019: wiring регистрационной ветки index.html (rev-002 #5):
    fetch /api/register, sessionStorage 'session_token', редирект /cabinet."""
    html = open("frontend/index.html", encoding="utf-8").read()
    assert "fetch('/api/register'" in html
    assert "sessionStorage.setItem('session_token'" in html
    assert "location.href='/cabinet'" in html
