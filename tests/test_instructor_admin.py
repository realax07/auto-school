"""Задача 2.1 — модерация заявок (sdd.md §15.2–§15.4).

Трассировка (rule 6): TC-FR14-001…TC-FR15-005 — плановые ID до
утверждения кейсов QA (6.1); источники — scenarios спек-дельты
openspec/changes/add-instructor-flow/specs/admin-moderation/spec.md:
«Администратор видит все заявки», «Доступ без админ-токена отклоняется»
(TC-FR14-001), «Одобрение заявки waiting», «Одобренная заявка не
одобряется повторно», «Роль одобренного инструктора отличима от роли
ученика», «Вход одобренного инструктора с паролем из анкеты»
(TC-FR16-001…004), «Отклонение без комментария недоступно», «Отклонение
с комментарием», «Повторное отклонение не меняет уже сохраненную
причину», «Отклонение не-waiting заявки отклоняется сервером»
(TC-FR15-001…005).

Роутер instructor_admin подключается напрямую (сборка в app.py — задача
5.1, вне зоны). X-Admin-Token — реестр backend.admin._tokens (механика
admin.py): токен получается через POST /api/admin/login на изолированном
app с обоими роутерами.
"""
import sqlite3

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.db as db
from backend.admin import router as admin_router
from backend.instructor_admin import router as instructor_admin_router
from backend.instructors import router as instructors_router
from tests.conftest import admin_password_hash

from tests.test_instructors_apply import valid_application

COMMENT = "Не подтверждена квалификация"


@pytest.fixture()
def api_client(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_USER", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", admin_password_hash())
    monkeypatch.setenv("SECRET", "test-secret")
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(tmp_path / "app.db"))
    db.init_db()
    app = FastAPI()
    app.include_router(admin_router)
    app.include_router(instructor_admin_router)
    # instructors подключен, чтобы заявки создавались публичным контрактом 1.1
    app.include_router(instructors_router)
    with TestClient(app) as c:
        yield c


def admin_headers(client):
    resp = client.post(
        "/api/admin/login", json={"login": "admin", "password": "admin-pass-2026"}
    )
    assert resp.status_code == 200, resp.text
    return {"X-Admin-Token": resp.json()["token"]}


def create_application(client, **overrides):
    """Заявка через публичный контракт (1.1) → id созданной записи."""
    resp = client.post(
        "/api/instructors/apply", json=valid_application(**overrides)
    )
    assert resp.status_code == 200, resp.text
    conn = db.get_conn()
    row = conn.execute(
        "SELECT id FROM instructor_applications WHERE email = ?",
        (overrides.get("email", "instructor@example.com"),),
    ).fetchone()
    conn.close()
    return row["id"]


def fetch_application_row(app_id):
    conn = db.get_conn()
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM instructor_applications WHERE id = ?", (app_id,)
    ).fetchone()
    conn.close()
    return row


def fetch_user_row(email):
    conn = db.get_conn()
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row


# --- GET /api/admin/instructor-applications ---


def test_list_without_token_401(api_client):
    """401 {"ok": false} без валидного админ-токена (FR-14)."""
    resp = api_client.get("/api/admin/instructor-applications")
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}


def test_list_without_hash_key(api_client):
    """MIN-5: список содержит все данные анкеты, но ключ password_hash
    ОТСУТСТВУЕТ в каждом элементе (хэш хранится, но не выдается API)."""
    app_id = create_application(api_client)
    resp = api_client.get(
        "/api/admin/instructor-applications", headers=admin_headers(api_client)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    item = body["applications"][0]
    assert item["id"] == app_id
    assert "password_hash" not in item
    for key in (
        "surname", "name", "patronymic", "email", "phone", "address",
        "work_format", "plate", "license_number", "license_date",
        "license_category", "experience", "status", "review_comment",
        "created_at",
    ):
        assert key in item
    assert item["status"] == "waiting"


def test_list_sorted_created_desc_id_desc(api_client):
    """Сортировка created_at DESC, id DESC (§15.2)."""
    id1 = create_application(api_client, email="a@example.com")
    id2 = create_application(api_client, email="b@example.com")
    resp = api_client.get(
        "/api/admin/instructor-applications", headers=admin_headers(api_client)
    )
    ids = [item["id"] for item in resp.json()["applications"]]
    assert ids == [id2, id1]


# --- approve ---


def test_approve_creates_user_with_instructor_role_and_same_hash(api_client):
    """Approve: users создан с данными и ХЭШОМ ИЗ ЗАЯВКИ (без повторного
    хэширования, FR-11.1), role='instructor'; статус → approved;
    повторный approve → 409."""
    app_id = create_application(api_client)
    app_row = fetch_application_row(app_id)
    resp = api_client.post(
        f"/api/admin/instructor-applications/{app_id}/approve",
        headers=admin_headers(api_client),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert isinstance(body["user_id"], int)

    user = fetch_user_row("instructor@example.com")
    assert user is not None
    assert user["role"] == "instructor"
    assert user["surname"] == "Иванов"
    assert user["password_hash"] == app_row["password_hash"]

    assert fetch_application_row(app_id)["status"] == "approved"

    resp2 = api_client.post(
        f"/api/admin/instructor-applications/{app_id}/approve",
        headers=admin_headers(api_client),
    )
    assert resp2.status_code == 409
    assert resp2.json() == {"ok": False, "error": "Заявка уже одобрена"}
    # users не задублирован
    conn = db.get_conn()
    count = conn.execute(
        "SELECT COUNT(*) FROM users WHERE email = 'instructor@example.com'"
    ).fetchone()[0]
    conn.close()
    assert count == 1


def test_approve_transaction_rollback_keeps_consistency(api_client, monkeypatch):
    """MIN-3: падение между INSERT и UPDATE не оставляет waiting-заявку
    с пользователем — транзакция откатывается целиком, ответ 409
    (IntegrityError-путь), состояние: заявка waiting, users без записи."""
    app_id = create_application(api_client, email="dup@example.com")
    # чужой пользователь с тем же email появляется ПОСЛЕ SELECT-этапов
    # заявки — approve падает на UNIQUE users.email
    conn = db.get_conn()
    conn.execute(
        "INSERT INTO users (surname, name, patronymic, email, phone,"
        " password_hash) VALUES ('X', 'Y', 'Z', 'dup@example.com',"
        " '+79005556677', 'хэш')"
    )
    conn.commit()
    conn.close()

    resp = api_client.post(
        f"/api/admin/instructor-applications/{app_id}/approve",
        headers=admin_headers(api_client),
    )
    assert resp.status_code == 409
    assert resp.json() == {"ok": False, "error": "Email: уже зарегистрирован"}

    assert fetch_user_row("dup@example.com") is not None  # чужая запись цела
    assert fetch_application_row(app_id)["status"] == "waiting"  # откат
    conn = db.get_conn()
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    assert count == 1


def test_approve_unknown_application_404(api_client):
    resp = api_client.post(
        "/api/admin/instructor-applications/999/approve",
        headers=admin_headers(api_client),
    )
    assert resp.status_code == 404
    assert resp.json() == {"ok": False, "error": "Заявка не найдена"}


# --- deny ---


def test_deny_without_comment_422(api_client):
    """FR-15: комментарий обязателен — пустой/отсутствующий → 422
    «Комментарий: поле обязательно»; статус не меняется."""
    app_id = create_application(api_client)
    for payload in (None, {"comment": ""}, {"comment": "   "}):
        kwargs = {"headers": admin_headers(api_client)}
        if payload is not None:
            kwargs["json"] = payload
        resp = api_client.post(
            f"/api/admin/instructor-applications/{app_id}/deny", **kwargs
        )
        assert resp.status_code == 422
        assert resp.json() == {
            "ok": False,
            "error": "Комментарий: поле обязательно",
        }
    assert fetch_application_row(app_id)["status"] == "waiting"


def test_deny_with_comment_saves_reason(api_client):
    """Deny с комментарием: статус → deny, review_comment = комментарий."""
    app_id = create_application(api_client)
    resp = api_client.post(
        f"/api/admin/instructor-applications/{app_id}/deny",
        json={"comment": COMMENT},
        headers=admin_headers(api_client),
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    row = fetch_application_row(app_id)
    assert row["status"] == "deny"
    assert row["review_comment"] == COMMENT


def test_deny_approved_application_409_users_untouched(api_client):
    """MIN-1: deny не-waiting — guard статуса: approved → 409 «Заявка уже
    одобрена», запись users не меняется."""
    app_id = create_application(api_client)
    assert (
        api_client.post(
            f"/api/admin/instructor-applications/{app_id}/approve",
            headers=admin_headers(api_client),
        )
    ).status_code == 200
    user_before = fetch_user_row("instructor@example.com")

    resp = api_client.post(
        f"/api/admin/instructor-applications/{app_id}/deny",
        json={"comment": COMMENT},
        headers=admin_headers(api_client),
    )
    assert resp.status_code == 409
    assert resp.json() == {"ok": False, "error": "Заявка уже одобрена"}
    assert fetch_user_row("instructor@example.com") == user_before
    assert fetch_application_row(app_id)["status"] == "approved"


def test_deny_twice_409_reason_unchanged(api_client):
    """Повторный deny → 409 «Заявка уже отклонена», причина не меняется."""
    app_id = create_application(api_client)
    first = api_client.post(
        f"/api/admin/instructor-applications/{app_id}/deny",
        json={"comment": COMMENT},
        headers=admin_headers(api_client),
    )
    assert first.status_code == 200
    second = api_client.post(
        f"/api/admin/instructor-applications/{app_id}/deny",
        json={"comment": "другая причина"},
        headers=admin_headers(api_client),
    )
    assert second.status_code == 409
    assert second.json() == {"ok": False, "error": "Заявка уже отклонена"}
    row = fetch_application_row(app_id)
    assert row["status"] == "deny"
    assert row["review_comment"] == COMMENT  # сохраненная причина не меняется


def test_deny_unknown_application_404(api_client):
    resp = api_client.post(
        "/api/admin/instructor-applications/999/deny",
        json={"comment": COMMENT},
        headers=admin_headers(api_client),
    )
    assert resp.status_code == 404
    assert resp.json() == {"ok": False, "error": "Заявка не найдена"}


# --- 401 на все три эндпоинта без токена ---


def test_all_endpoints_without_token_401(api_client):
    app_id = create_application(api_client)
    for method, url, kwargs in (
        ("get", "/api/admin/instructor-applications", {}),
        ("post", f"/api/admin/instructor-applications/{app_id}/approve", {}),
        ("post", f"/api/admin/instructor-applications/{app_id}/deny", {}),
    ):
        resp = getattr(api_client, method)(url, **kwargs)
        assert resp.status_code == 401, url
        assert resp.json() == {"ok": False}

    # невалидный токен — тоже 401
    bad = {"X-Admin-Token": "not-a-token"}
    assert (
        api_client.get(
            "/api/admin/instructor-applications", headers=bad
        )
    ).status_code == 401
