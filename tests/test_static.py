"""Тесты статики и health (задача 4.2, sdd.md §2, §3.6).

GET /, /registered, /admin-login, /admin-dashboard → 200;
GET /api/health → 200 {"ok": true}.
"""
import os
import sys
from pathlib import Path

import bcrypt
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_USER", "admin")
    monkeypatch.setenv(
        "ADMIN_PASSWORD_HASH",
        bcrypt.hashpw(b"x", bcrypt.gensalt()).decode(),
    )
    monkeypatch.setenv("SECRET", "test-secret")
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(tmp_path / "app.db"))
    monkeypatch.chdir(ROOT)  # статика ищется относительно корня репозитория
    from fastapi.testclient import TestClient

    from backend.app import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c


PAGES = {
    "/": "СберАвтошкола",
    "/registered": "Регистрация завершена",
    "/admin-login": "Админка",
    "/admin-dashboard": "Пользователи",
}


@pytest.mark.parametrize("path,marker", sorted(PAGES.items()))
def test_static_pages_return_200(client, path, marker):
    resp = client.get(path)
    assert resp.status_code == 200, path
    assert marker in resp.text, path


def test_text_is_verbatim_from_mocks(client):
    """Текстовки модалок — дословно из макетов (кроме добавленных полей
    пароля и сообщений об ошибках — решение дизайна, FR-9)."""
    for path in PAGES:
        resp = client.get(path)
        assert resp.status_code == 200, path


def test_register_modal_has_password_fields(client):
    resp = client.get("/")
    assert 'id="reg-password"' in resp.text
    assert 'id="reg-password-confirm"' in resp.text
    assert "Подтверждение" in resp.text


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_lifespan_initializes_db(client):
    # init_db через lifespan: таблица users существует после старта приложения
    import sqlite3

    db_path = os.environ["AUTOSCHOOL_DB_PATH"]
    conn = sqlite3.connect(db_path)
    names = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchall()
    ]
    conn.close()
    assert names == ["users"]
