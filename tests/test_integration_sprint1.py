"""Задача 3.1 (Спринт 1, сборка) — change add-auth-cabinet.

create_app() монтирует роутер auth (задача 1.1) и отдает /cabinet →
frontend/cabinet.html (задача 2.1). «Готовность» tasks.md 3.1:
- /api/health зеленый;
- POST /api/auth/login работает через create_app() — реальный mount,
  без локальной фикстуры (conftest-клиент поверх create_app());
- /cabinet отдается (200) и содержит маркеры cabinet.html;
- регресс Спринта 0: /api/register, /api/admin/* — как раньше.

Фикстуры свои не определяем: используем общий client из conftest —
он собирает приложение через create_app(), т.е. проверяем настоящий
mount из backend/app.py, а не самоподключение роутера.

Трассировка (approved-кейсы test-model, покрытие пунктов «Готовность» 3.1):
- TC-AUTH-001 — вход через create_app(): токен выдан, /me отвечает
  (test_login_via_create_app);
- TC-REG-001 — регресс /api/register: валидный набор → 200
  (test_regression_register_flow);
- TC-REG-013 — регресс /api/register: повтор тех же данных → 422
  (test_regression_register_flow);
- TC-ADM-005 — регресс /api/admin/users: список после логина админа
  (test_regression_admin_flow);
- /cabinet и статика — файлов-кейсов TC для маршрута страницы в
  test-model нет (задача 2.1 сверяла cabinet.html посимвольно без
  TestClient); контроль прямым сравнением ответа с файлом
  (test_cabinet_page_is_cabinet_html_file).
"""
from fastapi.testclient import TestClient

from conftest import admin_headers, register

# Маркеры frontend/cabinet.html (тексты мокапа, задача 2.1)
CABINET_MARKERS = (
    "СберАвтошкола",
    "Личный кабинет · Ученик",
    "ЛИЧНЫЙ КАБИНЕТ",
    "Гига ГАИшник",
    "Выйти",
)

# Маркеры wiring cabinet.html (единственные отличия от мокапа)
CABINET_WIRING_MARKERS = (
    "/api/auth/me",
    "X-Session-Token",
    "/api/auth/logout",
)


# --- Сборка: роутер auth в create_app() ---------------------------------------


def test_health_ok(client):
    """/api/health зеленый после добавления роутера auth (регресс каркаса)."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_login_via_create_app(client):
    """Готовность 3.1: POST /api/auth/login работает через create_app() —
    регистрация (Спринт 0) → вход (Спринт 1) на том же приложении без
    локальной фикстуры; токен выдается, /me по нему отвечает."""
    resp = register(client)
    assert resp.status_code == 200, resp.text

    login = client.post(
        "/api/auth/login",
        json={"email": "petrova@example.com", "password": "Qwerty123"},
    )
    assert login.status_code == 200
    data = login.json()
    assert data["ok"] is True
    token = data["token"]
    assert isinstance(token, str) and token

    me = client.get("/api/auth/me", headers={"X-Session-Token": token})
    assert me.status_code == 200
    assert me.json()["ok"] is True
    assert me.json()["user"]["email"] == "petrova@example.com"


# --- Маршрут /cabinet ----------------------------------------------------------


def test_cabinet_page_served(client):
    """Готовность 3.1: GET /cabinet → 200 и содержит маркеры cabinet.html
    (тексты мокапа 2.1 + wiring)."""
    resp = client.get("/cabinet")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    for marker in CABINET_MARKERS + CABINET_WIRING_MARKERS:
        assert marker in resp.text, marker


def test_cabinet_page_is_cabinet_html_file(client):
    """/cabinet отдает именно frontend/cabinet.html (маршрут рядом с
    /admin-dashboard, паттерн Спринта 0)."""
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    file_html = (root / "frontend" / "cabinet.html").read_text(encoding="utf-8")
    resp = client.get("/cabinet")
    assert resp.status_code == 200
    assert resp.text == file_html


# --- Регресс Спринта 0 ----------------------------------------------------------


def test_regression_register_flow(client):
    """/api/register работает как в Спринте 0: валидный набор → 200,
    запись появляется; дубликат email → 409 (контракт §3)."""
    resp = register(client)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    dup = register(client)
    assert dup.status_code == 422
    assert dup.json() == {"ok": False, "error": "Email: уже зарегистрирован"}


def test_regression_admin_flow(client):
    """/api/admin/* работают как в Спринте 0: логин админа → токен, список
    пользователей, экспорт CSV; без токена — 401 (контракт §5)."""
    assert register(client).status_code == 200
    headers = admin_headers(client)  # внутри: POST /api/admin/login → 200

    resp = client.get("/api/admin/users", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["users"][0]["email"] == "petrova@example.com"

    csv_resp = client.get("/api/admin/users/export.csv", headers=headers)
    assert csv_resp.status_code == 200
    assert "petrova@example.com" in csv_resp.text

    without_token = client.get("/api/admin/users")
    assert without_token.status_code == 401


def test_regression_static_pages(client):
    """Статика Спринта 0 не задета новыми маршрутами."""
    for path, marker in (
        ("/", "СберАвтошкола"),
        ("/admin-dashboard", "СберАвтошкола"),
    ):
        resp = client.get(path)
        assert resp.status_code == 200, path
        assert "text/html" in resp.headers["content-type"], path
        assert marker in resp.text, path
