"""Задача 3.1 (Спринт 2, часть 1) — change add-instructor-flow.

Трассировка (rule 6): TC-FR13-001…TC-FR13-006 — плановые ID до
утверждения кейсов QA (6.1); источники — scenarios спек-дельты
openspec/changes/add-instructor-flow/specs/instructor-auth/spec.md:
«Вход одобренного инструктора» (TC-FR13-001),
«Заявка waiting — экран ожидания» (TC-FR13-002),
«Заявка deny — экран отказа с причиной» (TC-FR13-003),
«Единое сообщение при отсутствии и пользователя, и заявки»
(TC-FR13-004), «Неверный пароль отклоняется единым сообщением»
(TC-FR13-005); анти-брутфорс — FR-13/R-BF1…R-BF4 (TC-FR13-006).
Сборка 5.1 — контроль регресса и новых маршрутов (задача 5.1, sdd §15.6).

Роутинг входа по статусу (FR-13, sdd.md §15.5):
- users-запись: role='instructor' → route=cabinet; role='student' →
  route=student-cabinet (регресс Спринта 1);
- записи users нет: заявка waiting → 200 {ok, route:'pending'} БЕЗ токена;
  deny → 200 {ok, route:'rejected', reason} БЕЗ токена; заявки нет → 401
  единое сообщение;
- анти-брутфорс: неудачные попытки против заявки учитываются наравне
  с users (единый учет по IP).

Задача 5.1 (сборка) — app.py монтирует роутеры instructors +
instructor_admin и отдает новые статические маршруты (sdd.md §15.6).

Фикстуры — общий client из conftest (create_app() поверх чистой БД).
Заявки создаются через реальный POST /api/instructors/apply (1.1),
статусы меняются прямым UPDATE через sqlite3 (детерминизм, без time.sleep),
approve — через реальный POST /api/admin/instructor-applications/{id}/approve.
"""
import sqlite3

import pytest

from conftest import admin_headers, db_path, register


@pytest.fixture(autouse=True)
def _clean_bruteforce_state():
    """Анти-брутфорс backend.auth ведет module-level учет по IP, который
    переживает тесты (задокументированное ограничение — рестарт процесса
    сбрасывает учет). Тесты этого модуля намеренно копят неудачи и
    блокируют IP «testclient» — очищаем состояние до и после каждого
    теста, чтобы не влиять на соседние файлы и не зависеть от их порядка."""
    from backend import auth

    auth._bf.clear()
    yield
    auth._bf.clear()


def _apply(client, email="instr@example.com", password="Instr1234", **overrides):
    """Валидная анкета инструктора через реальный эндпоинт 1.1."""
    body = {
        "fio": "Инструкторов Тест Отчествович",
        "phone": "+7 (911) 222-33-44",
        "email": email,
        "address": "г. Тест, ул. Полевая, 1",
        "work_format": "sber",
        "license_number": "9911223344",
        "license_category": "B",
        "password": password,
        "password_confirm": password,
        "consent": True,
    }
    body.update(overrides)
    resp = client.post("/api/instructors/apply", json=body)
    assert resp.status_code == 200, resp.text
    return resp


def _set_status(email, status, review_comment=""):
    """Прямой UPDATE статуса заявки (детерминизм, без time.sleep)."""
    conn = sqlite3.connect(db_path())
    conn.execute(
        "UPDATE instructor_applications SET status = ?, review_comment = ?"
        " WHERE email = ?",
        (status, review_comment, email),
    )
    conn.commit()
    conn.close()


def _application_id(email):
    conn = sqlite3.connect(db_path())
    row = conn.execute(
        "SELECT id FROM instructor_applications WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return row[0]


# --- 3.1: users-запись → route по role ------------------------------------------


def test_login_instructor_approved_route_cabinet(client):
    """approved-инструктор (запись users, role='instructor'): сессия + route=cabinet."""
    _apply(client)
    headers = admin_headers(client)
    resp = client.post(
        f"/api/admin/instructor-applications/{_application_id('instr@example.com')}"
        "/approve",
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    login = client.post(
        "/api/auth/login",
        json={"email": "instr@example.com", "password": "Instr1234"},
    )
    assert login.status_code == 200
    data = login.json()
    assert data["ok"] is True
    assert data["route"] == "cabinet"
    # сессия выдается как §10.1
    token = data["token"]
    assert isinstance(token, str) and token
    me = client.get("/api/auth/me", headers={"X-Session-Token": token})
    assert me.status_code == 200
    assert me.json()["user"]["email"] == "instr@example.com"


def test_login_student_route_student_cabinet(client):
    """Регресс Спринта 1: ученик получает route=student-cabinet (токен выдается)."""
    assert register(client).status_code == 200
    login = client.post(
        "/api/auth/login",
        json={"email": "petrova@example.com", "password": "Qwerty123"},
    )
    assert login.status_code == 200
    data = login.json()
    assert data["ok"] is True
    assert data["route"] == "student-cabinet"
    assert data["token"]


# --- 3.1: заявка без записи users ------------------------------------------------


def test_login_waiting_application_pending_no_session(client):
    """waiting-заявка: 200 {ok, route:'pending'} БЕЗ токена (сессию выдавать нечего)."""
    _apply(client)
    login = client.post(
        "/api/auth/login",
        json={"email": "instr@example.com", "password": "Instr1234"},
    )
    assert login.status_code == 200
    data = login.json()
    assert data["ok"] is True
    assert data["route"] == "pending"
    assert "token" not in data


def test_login_denied_application_rejected_with_reason(client):
    """deny-заявка: 200 {ok, route:'rejected', reason=review_comment} БЕЗ токена."""
    _apply(client)
    reason = "Опыт работы не подтвержден"
    _set_status("instr@example.com", "deny", reason)

    login = client.post(
        "/api/auth/login",
        json={"email": "instr@example.com", "password": "Instr1234"},
    )
    assert login.status_code == 200
    data = login.json()
    assert data["ok"] is True
    assert data["route"] == "rejected"
    assert data["reason"] == reason
    assert "token" not in data


def test_login_unknown_credentials_unified_401(client):
    """Ни users, ни заявки → единый 401 (AUTH_FAIL_MESSAGE, без изменений)."""
    from backend.auth import AUTH_FAIL_MESSAGE

    login = client.post(
        "/api/auth/login",
        json={"email": "ghost@example.com", "password": "Whatever123"},
    )
    assert login.status_code == 401
    assert login.json() == {"ok": False, "error": AUTH_FAIL_MESSAGE}


def test_login_wrong_password_against_application_401(client):
    """Неверный пароль против заявки → единый 401 (та же схема, что users)."""
    from backend.auth import AUTH_FAIL_MESSAGE

    _apply(client)
    login = client.post(
        "/api/auth/login",
        json={"email": "instr@example.com", "password": "WrongPass1"},
    )
    assert login.status_code == 401
    assert login.json() == {"ok": False, "error": AUTH_FAIL_MESSAGE}


def test_bruteforce_on_application_counts(client):
    """Неудачные попытки против заявки учитываются анти-брутфорсом (единый
    учет по IP, §15.5): порог → блокировка, даже верный пароль отклоняется."""
    _apply(client)
    for _ in range(5):  # _BF_MAX_FAILURES = 5
        resp = client.post(
            "/api/auth/login",
            json={"email": "instr@example.com", "password": "WrongPass1"},
        )
        assert resp.status_code == 401

    # 6-я попытка — уже с верным паролем, но IP заблокирован: единый 401
    blocked = client.post(
        "/api/auth/login",
        json={"email": "instr@example.com", "password": "Instr1234"},
    )
    assert blocked.status_code == 401
    assert blocked.json()["ok"] is False


# --- 5.1: сборка -----------------------------------------------------------------


def test_health_ok_after_mount(client):
    """/api/health зеленый после монтирования роутеров instructors +
    instructor_admin (регресс каркаса)."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_regression_sprint0_1(client):
    """Регресс Спринтов 0–1: /api/register, /api/auth/login,
    /api/admin/users работают как раньше."""
    assert register(client).status_code == 200
    login = client.post(
        "/api/auth/login",
        json={"email": "petrova@example.com", "password": "Qwerty123"},
    )
    assert login.status_code == 200

    headers = admin_headers(client)
    users = client.get("/api/admin/users", headers=headers)
    assert users.status_code == 200
    assert users.json()["count"] == 1


def test_new_static_routes_served(client):
    """Новые статические маршруты (§15.6) отдаются с 200 и text/html."""
    for path in (
        "/instructors",
        "/instructors/apply",
        "/instructors/pending",
        "/instructors/rejected",
        "/instructor/cabinet-stub",
    ):
        resp = client.get(path)
        assert resp.status_code == 200, path
        assert "text/html" in resp.headers["content-type"], path
