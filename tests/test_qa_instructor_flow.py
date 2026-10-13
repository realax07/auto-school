"""QA-автоматизация недостающих API-кейсов пакета add-instructor-flow
(test-model/approved/add-instructor-flow/, корреляция 7007d3127b3641f698c8d1bbaa3694b4).

Дополняет tests/test_instructors_apply.py, test_instructor_admin.py,
test_auth_route.py, test_instructor_pages.py, test_qa_sprint1.py —
НЕ дублирует их. Браузерные/manual-кейсы (TC-APP-002/004, TC-AUTH-007,
TC-CAB-001/002/003 браузерные части, TC-MOD-003, design check 6.1) —
manual, сюда не входят (матрица — в отчете QA).

Что автоматизировано здесь (было manual/toBeAutomated в статусах кейсов):
- TC-APP-015 — остальные пары порядка «первая ошибка» §15.1 (шаги 1, 3–8;
  шаг 2 уже automated — test_apply_order_consent_checked_before_email_format);
- TC-APP-017 — повторный apply против заявки в статусах deny/approved
  (waiting-вариант уже automated — test_apply_email_taken_in_applications);
- TC-APP-018 — честное исполнение IntegrityError-пути (D8): monkeypatch-
  обертка db-слоя пропускает SELECT-шаги §15.1, INSERT исполняется на
  занятом email реально → контрактная 422, НЕ 500;
- TC-AUTH-010 — сброс счетчика анти-брутфорса успешным статусным входом
  (pending/rejected);
- TC-AUTH-011 — инструктор-вариант изоляции блокировки по IP + «блокировка
  нигде не названа» (тело/заголовки идентичны единому отказу);
- TC-MOD-001 — все три статуса waiting/approved/deny в одном GET-списке
  (сортировка id DESC при равных created_at);
- TC-MOD-002 — контроль логов (ответ GET заявок не логируется, password_hash
  не в логах) + UI admin-dashboard.html без password_hash;
- TC-NFR-001 — статическая инспекция SQL новых модулей (instructors.py,
  instructor_admin.py, auth.py): только ?-плейсхолдеры, 0 конкатенаций;
- TTL (применимо к TC-AUTH-001/§10.1) — сдвиг времени мимо _TOKEN_TTL_SECONDS:
  сессия одобренного инструктора истекает, /me и /logout → 401, без sleep;
- Замеры времени (TC-INT-001/NFR-1) — POST /api/instructors/apply и
  POST /api/auth/login (route=cabinet): медиана 5 прогонов ≤ 500 мс.

time.sleep запрещен (спека qa-pipeline): TTL — сдвиг clock через
monkeypatch backend.auth.time.time (паттерн test_qa_sprint1.py).
"""
import logging
import re
import sqlite3
import time as _time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import admin_headers, db_path
from tests.test_auth_route import _apply, _application_id, _set_status

ROOT = Path(__file__).resolve().parent.parent
AUTH_FAIL = {"ok": False, "error": "Неверный email или пароль"}


@pytest.fixture(autouse=True)
def _clean_bruteforce_state():
    """Анти-брутфорс backend.auth ведет module-level учет по IP, который
    переживает тесты (механика test_auth_route.py): очищаем до и после
    каждого теста, чтобы не зависеть от порядка файлов."""
    from backend import auth

    auth._bf.clear()
    yield
    auth._bf.clear()


def _apply_body(email, password="Instr1234", **overrides):
    """Тело анкеты (набор test_auth_route._apply) без отправки — для
    прямых POST и таймингов."""
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
    return body


def _login(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _count_applications(email=None):
    conn = sqlite3.connect(db_path())
    if email is None:
        n = conn.execute(
            "SELECT COUNT(*) FROM instructor_applications"
        ).fetchone()[0]
    else:
        n = conn.execute(
            "SELECT COUNT(*) FROM instructor_applications WHERE email = ?",
            (email,),
        ).fetchone()[0]
    conn.close()
    return n


def _client_at(client, host):
    """TestClient над тем же app с заданным IP источника (изоляция
    состояния анти-брутфорса по IP; паттерн test_qa_sprint1.py)."""
    return TestClient(client.app, client=(host, 50000))


def _approve(client, email="instr@example.com"):
    """Заявка создается публичным контрактом 1.1 (если еще нет) + approve."""
    if _count_applications(email) == 0:
        resp = client.post("/api/instructors/apply", json=_apply_body(email))
        assert resp.status_code == 200, resp.text
    resp = client.post(
        f"/api/admin/instructor-applications/{_application_id(email)}/approve",
        headers=admin_headers(client),
    )
    assert resp.status_code == 200, resp.text
    return resp


# --- TC-APP-015: порядок валидации, «первая ошибка» (пары 1, 3–8) --------------


@pytest.mark.parametrize(
    "overrides, expected_error",
    [
        # шаг 1: обязательное поле раньше согласия и формата email
        (
            {"fio": "", "email": "broken", "consent": False},
            "ФИО: поле обязательно",
        ),
        # шаг 2 уже automated (test_apply_order_consent_checked_before_email_format)
        # шаг 3: формат email раньше длины телефона
        (
            {"email": "broken", "phone": "+7 123 456"},
            "Email: неверный формат",
        ),
        # шаг 4: телефон раньше длины пароля
        (
            {"phone": "+7 123 456", "password": "short", "password_confirm": "short"},
            "Телефон: укажите не менее 10 цифр",
        ),
        # шаг 5: длина пароля раньше совпадения подтверждения
        (
            {"password": "short", "password_confirm": "other"},
            "Пароль: не менее 8 символов",
        ),
        # шаг 6: совпадение подтверждения раньше госномера при own
        (
            {"password_confirm": "OtherPass123", "work_format": "own", "plate": ""},
            "Подтверждение пароля: пароли не совпадают",
        ),
        # шаг 7: госномер при own раньше валидности license_date
        (
            {"work_format": "own", "plate": "", "license_date": "not-a-date"},
            "Госномер: поле обязательно",
        ),
        # шаг 8: license_date — последняя проверка валидации
        ({"license_date": "01.05.2020"}, "Дата выдачи ВУ: неверный формат"),
    ],
)
def test_tcapp015_order_first_error_wins(client, overrides, expected_error):
    """TC-APP-015 (пары шагов 1, 3–8): при нескольких нарушениях сообщается
    ПЕРВАЯ ошибка фиксированного порядка §15.1; заявка не создается.
    Шаг 2 (consent до email) — test_apply_order_consent_checked_before_email_format."""
    body = _apply_body("order@example.com")
    body.update(overrides)
    resp = client.post("/api/instructors/apply", json=body)
    assert resp.status_code == 422
    assert resp.json() == {"ok": False, "error": expected_error}
    assert _count_applications() == 0


# --- TC-APP-017: повторный apply против заявки в статусах deny/approved --------


@pytest.mark.parametrize("status", ["deny", "approved"])
def test_tcapp017_reapply_against_nonwaiting_application_422(client, status):
    """TC-APP-017 (прогоны deny/approved; waiting уже automated): заявка в
    ЛЮБОМ статусе блокирует повторный apply тем же email — 422 «Email: уже
    зарегистрирован», вторая заявка не создана (COUNT = 1)."""
    email = f"dup-{status}@example.com"
    assert client.post(
        "/api/instructors/apply", json=_apply_body(email)
    ).status_code == 200
    _set_status(email, status, review_comment="Не подтверждена квалификация")

    resp = client.post("/api/instructors/apply", json=_apply_body(email))
    assert resp.status_code == 422
    assert resp.json() == {"ok": False, "error": "Email: уже зарегистрирован"}
    assert _count_applications(email) == 1


# --- TC-APP-018: честное исполнение IntegrityError-пути (D8) -------------------


def test_tcapp018_integrityerror_path_honest_d8(client, monkeypatch):
    """TC-APP-018 шаг 4 (усиление D8): SELECT-шаги §15.1 (8–9) пропущены
    monkeypatch-оберткой db-слоя, INSERT исполняется на занятом email
    РЕАЛЬНО → sqlite3.IntegrityError от UNIQUE перехвачен хендлером —
    контрактная 422 «Email: уже зарегистрирован», НЕ 500; ровно одна заявка."""
    import backend.db as db

    assert client.post(
        "/api/instructors/apply", json=_apply_body("race@example.com")
    ).status_code == 200

    real_get_conn = db.get_conn

    class _SkipSelectConn:
        """Прокручивает SELECT-проверки уникальности (возвращают «нет»),
        всё остальное — в реальный коннект (INSERT падает на UNIQUE)."""

        def __init__(self, conn):
            self._conn = conn

        def execute(self, sql, params=()):
            if sql.lstrip().upper().startswith("SELECT 1 FROM"):
                class _Empty:
                    def fetchone(self):
                        return None

                return _Empty()
            return self._conn.execute(sql, params)

        def __getattr__(self, name):
            return getattr(self._conn, name)

    class _RaceDB:
        """Подмена db-слоя в backend.instructors: get_conn возвращает
        обертку, пропускающую SELECT-шаги §15.1 (8–9)."""

        @staticmethod
        def get_conn():
            return _SkipSelectConn(real_get_conn())

    monkeypatch.setattr("backend.instructors.db", _RaceDB)

    resp = client.post("/api/instructors/apply", json=_apply_body("race@example.com"))
    assert resp.status_code == 422  # НЕ 500 — IntegrityError перехвачен
    assert resp.json() == {"ok": False, "error": "Email: уже зарегистрирован"}
    assert _count_applications("race@example.com") == 1


# --- TC-AUTH-010: сброс счетчика анти-брутфорса статусным входом ---------------


@pytest.mark.parametrize("status, route", [("waiting", "pending"), ("deny", "rejected")])
def test_tcauth010_status_login_resets_bf_counter(client, status, route):
    """TC-AUTH-010 (сброс при статусном входе — toBeAutomated): неудачные
    попытки против заявки учитываются единообразно; успешный вход по статусу
    (pending/rejected) СБРАСЫВАЕТ счетчик IP — следующие неудачи копятся с
    нуля и до блокировки не доходят."""
    import backend.auth as auth

    email = f"reset-{status}@example.com"
    assert client.post(
        "/api/instructors/apply", json=_apply_body(email)
    ).status_code == 200
    _set_status(email, status, review_comment="Не подтверждена квалификация")

    ip = "10.0.7.10"
    scoped = _client_at(client, ip)
    for _ in range(auth._BF_MAX_FAILURES - 1):
        assert _login(scoped, email, "WrongPass1").status_code == 401
    st = auth._bf.get(ip)
    assert st is not None and st["fails"] == auth._BF_MAX_FAILURES - 1

    # успешный статусный вход — сброс учета (R-BF3)
    ok = _login(scoped, email, "Instr1234")
    assert ok.status_code == 200
    assert ok.json() == (
        {"ok": True, "route": route}
        if status == "waiting"
        else {"ok": True, "route": route, "reason": "Не подтверждена квалификация"}
    )
    st = auth._bf.get(ip)
    assert st["fails"] == 0 and st["level"] == 0 and st["blocked_until"] == 0.0

    # после сброса одна неудача не блокирует — счетчик шел с нуля
    assert _login(scoped, email, "WrongPass1").status_code == 401
    assert auth._bf.get(ip)["fails"] == 1
    assert not auth._is_blocked(ip, auth.time.time())


# --- TC-AUTH-011: изоляция блокировки по IP; блокировка не называется ----------


def test_tcauth011_block_isolated_per_ip_and_never_named(client):
    """TC-AUTH-011 (инструктор-вариант, toBeAutomated): блокировка IP-A не
    влияет на IP-B (штатный вход 200 route=cabinet); ответ заблокированного
    IP-A с КОРРЕКТНЫМИ кредами идентичен единому отказу 401 — тело и
    заголовки без каких-либо признаков блокировки (нет Retry-After)."""
    import backend.auth as auth

    assert _approve(client).status_code == 200

    ip_a, ip_b = "10.0.8.10", "10.0.8.20"
    a = _client_at(client, ip_a)
    b = _client_at(client, ip_b)

    for _ in range(auth._BF_MAX_FAILURES):
        assert _login(a, "instr@example.com", "WrongPass1").status_code == 401
    assert auth._is_blocked(ip_a, auth.time.time())

    # IP-B не затронут: штатный вход одобренного инструктора
    resp_b = _login(b, "instr@example.com", "Instr1234")
    assert resp_b.status_code == 200
    assert resp_b.json()["route"] == "cabinet"
    assert resp_b.json()["token"]

    # IP-A: верные креды, но блокировка — тело идентично единому отказу
    blocked = _login(a, "instr@example.com", "Instr1234")
    reference = _login(b, "instr@example.com", "TotallyWrong")
    assert blocked.status_code == 401
    assert blocked.json() == AUTH_FAIL
    assert blocked.json() == reference.json()
    assert blocked.text == reference.text
    # блокировка нигде не названа: ни в теле, ни в заголовках
    assert "Retry-After" not in blocked.headers
    assert "block" not in blocked.text.lower() and "блок" not in blocked.text
    assert set(blocked.headers) == set(reference.headers)


# --- TC-MOD-001: все три статуса в одном GET-списке -----------------------------


def test_tcmod001_list_contains_all_statuses_sorted(client):
    """TC-MOD-001 (статусы waiting/approved/deny в одном списке —
    toBeAutomated): 3 заявки со всеми статусами, порядок id по убыванию,
    состав полей §15.2."""
    resp_a = client.post("/api/instructors/apply", json=_apply_body("a@example.com"))
    assert resp_a.status_code == 200
    id_a = _application_id("a@example.com")
    resp_b = client.post("/api/instructors/apply", json=_apply_body("b@example.com"))
    assert resp_b.status_code == 200
    id_b = _application_id("b@example.com")
    resp_c = client.post("/api/instructors/apply", json=_apply_body("c@example.com"))
    assert resp_c.status_code == 200
    id_c = _application_id("c@example.com")

    assert _approve(client, "b@example.com").status_code == 200
    deny = client.post(
        f"/api/admin/instructor-applications/{id_c}/deny",
        json={"comment": "Не подтверждена квалификация"},
        headers=admin_headers(client),
    )
    assert deny.status_code == 200

    listing = client.get(
        "/api/admin/instructor-applications", headers=admin_headers(client)
    )
    assert listing.status_code == 200
    body = listing.json()
    assert body["count"] == 3
    items = body["applications"]
    assert [item["id"] for item in items] == [id_c, id_b, id_a]
    by_email = {item["email"]: item for item in items}
    assert by_email["a@example.com"]["status"] == "waiting"
    assert by_email["b@example.com"]["status"] == "approved"
    assert by_email["c@example.com"]["status"] == "deny"
    assert by_email["c@example.com"]["review_comment"] == "Не подтверждена квалификация"
    for item in items:
        assert "password_hash" not in item


# --- TC-MOD-002: ответ GET заявок не логируется; UI без password_hash -----------


def test_tcmod002_get_not_logged_no_hash_in_logs_or_ui(client, caplog):
    """TC-MOD-002 (контроль логов + инспекция UI — toBeAutomated): в логах
    нет password_hash (значения и ключа), ответ GET не логируется; в
    admin-dashboard.html строка password_hash отсутствует (не рендерится)."""
    email = "hashlog@example.com"
    assert client.post(
        "/api/instructors/apply", json=_apply_body(email)
    ).status_code == 200

    conn = sqlite3.connect(db_path())
    stored_hash = conn.execute(
        "SELECT password_hash FROM instructor_applications WHERE email = ?", (email,)
    ).fetchone()[0]
    conn.close()

    with caplog.at_level(logging.DEBUG):
        listing = client.get(
            "/api/admin/instructor-applications", headers=admin_headers(client)
        )
        assert listing.status_code == 200

    assert stored_hash not in caplog.text
    assert "password_hash" not in caplog.text
    assert listing.text not in caplog.text  # ответ GET не логируется

    ui = (ROOT / "frontend" / "admin-dashboard.html").read_text(encoding="utf-8")
    assert "password_hash" not in ui
    assert stored_hash not in ui


# --- TC-NFR-001: статическая инспекция SQL новых модулей ------------------------


def test_tcnfr001_sql_parameterized_static_inspection():
    """TC-NFR-001 шаг 1 (инспекция исходников — toBeAutomated): в SQL новых
    модулей (instructors.py, instructor_admin.py, ветки auth.py) — только
    ?-плейсхолдеры, параметры кортежем; конкатенации/f-string SQL
    отсутствуют. Динамические пробы — test_apply_validation_contract_422
    (инъекция в email apply) и test_qa_sprint1.py::test_nfr002 (login)."""
    modules = [
        "backend/instructors.py",
        "backend/instructor_admin.py",
        "backend/auth.py",
    ]
    found = 0
    for rel in modules:
        src = (ROOT / rel).read_text(encoding="utf-8")
        # f-строки с SQL недопустимы
        for fsql in re.findall(r'f"((?:SELECT|INSERT|UPDATE)[^"]*)"', src):
            raise AssertionError(f"{rel}: f-string SQL: {fsql[:60]}")
        # SQL-литералы собираются из смежных строковых конкатенаций — склейка
        # через ast.literal_eval константы (не анализируем + в коде вокруг)
        import ast

        tree = ast.parse(src)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                continue
            sql = node.value
            if not re.match(r"\s*(SELECT|INSERT|UPDATE)\b", sql, re.IGNORECASE):
                continue
            found += 1
            # NFR-2: конкатенация/интерполяция пользовательских данных
            # в SQL-строку отсутствует; фильтры — только через ?-плейсхолдер
            # (SELECT-список без WHERE — константный запрос, параметров нет)
            assert "+" not in sql and "%s" not in sql and "{" not in sql, (
                f"{rel}: подозрение на конкатенацию SQL: {sql[:60]}"
            )
            if re.search(r"\bWHERE\b", sql, re.IGNORECASE):
                assert "?" in sql, (
                    f"{rel}: фильтр без ?-плейсхолдера: {sql[:60]}"
                )
    assert found >= 5, f"ожидались SQL запросы новых модулей, найдено {found}"


# --- TTL: сессия одобренного инструктора истекает по §10.1 ----------------------


def test_ttl_instructor_session_expires_token_shift(client, monkeypatch):
    """TTL-сценарий (TC-AUTH-001: сессия «как §10.1», применимо): после
    сдвига «сейчас» мимо expires (12 ч, backend.auth._TOKEN_TTL_SECONDS)
    /api/auth/me и /api/auth/logout с токеном инструктора → 401 {ok:false}.
    time.sleep запрещен — прямой сдвиг clock (паттерн test_qa_sprint1)."""
    import backend.auth as auth

    assert _approve(client).status_code == 200
    login = _login(client, "instr@example.com", "Instr1234")
    assert login.status_code == 200
    token = login.json()["token"]

    real_time = auth.time.time
    now = [real_time()]
    monkeypatch.setattr(auth.time, "time", lambda: now[0])

    me = client.get("/api/auth/me", headers={"X-Session-Token": token})
    assert me.status_code == 200
    assert me.json()["user"]["email"] == "instr@example.com"

    now[0] += auth._TOKEN_TTL_SECONDS + 1
    me2 = client.get("/api/auth/me", headers={"X-Session-Token": token})
    assert me2.status_code == 401
    assert me2.json() == {"ok": False}
    logout = client.post("/api/auth/logout", headers={"X-Session-Token": token})
    assert logout.status_code == 401
    assert logout.json() == {"ok": False}


# --- Замеры времени: apply и login-route ≤ 500 мс (NFR-1, TC-INT-001) -----------


def test_timing_apply_latency_under_500ms(client):
    """Замер POST /api/instructors/apply (§15.1): 5 прогонов с уникальными
    email, time.perf_counter вокруг HTTP-вызова TestClient (без сети);
    медиана ≤ 500 мс (бюджет с bcrypt cost 12; max фиксируется)."""
    timings_ms = []
    for i in range(1, 6):
        start = _time.perf_counter()
        resp = client.post(
            "/api/instructors/apply", json=_apply_body(f"perf-apply{i}@example.com")
        )
        elapsed_ms = (_time.perf_counter() - start) * 1000
        assert resp.status_code == 200, resp.text
        timings_ms.append(elapsed_ms)
    median_ms = sorted(timings_ms)[2]
    print(
        f"apply: медиана {median_ms:.0f} мс, max {max(timings_ms):.0f} мс"
    )
    assert median_ms <= 500.0, (
        f"медиана apply {median_ms:.1f} мс > 500 мс; прогоны {timings_ms}"
    )


def test_timing_login_route_latency_under_500ms(client):
    """Замер POST /api/auth/login route=cabinet (§15.5, инструктор-ветка):
    apply + approve, 5 прогонов входа с корректными данными; медиана ≤ 500 мс
    (фиктивная bcrypt-проверка/проверка против заявки в бюджете)."""
    assert _approve(client).status_code == 200

    timings_ms = []
    for _ in range(5):
        start = _time.perf_counter()
        resp = _login(client, "instr@example.com", "Instr1234")
        elapsed_ms = (_time.perf_counter() - start) * 1000
        assert resp.status_code == 200, resp.text
        assert resp.json()["route"] == "cabinet"
        timings_ms.append(elapsed_ms)
    median_ms = sorted(timings_ms)[2]
    print(
        f"login(route=cabinet): медиана {median_ms:.0f} мс, "
        f"max {max(timings_ms):.0f} мс"
    )
    assert median_ms <= 500.0, (
        f"медиана login {median_ms:.1f} мс > 500 мс; прогоны {timings_ms}"
    )
