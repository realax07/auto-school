"""Задача 1.1 — POST /api/auth/login, /api/auth/logout, GET /api/auth/me,
require_session (sdd.md §10.1–§10.3; спека auth, Requirements «Вход ученика»,
«Единое сообщение об отказе входа», «Хранение учетных данных», «Сессии с
ограниченным сроком действия», «Ограничение попыток входа (анти-брутфорс)»).

Трассировка на кейсы (TC-AUTH-NNN формализуются qa_case_author в
test-model/new/add-auth-cabinet/; на момент задачи 1.1 approved-кейсов домена
auth еще нет — тесты покрывают пункты «Готовность» tasks.md 1.1 напрямую):
- TC-AUTH-001 — успешный вход, токен выдан (test_login_success_issues_token);
- TC-AUTH-002 — пароль проверяется против bcrypt-хэша (…_against_bcrypt_hash);
- TC-AUTH-003 — единое сообщение отказа, причины неразличимы (…_identical_message);
- TC-AUTH-004 — пустые поля → 422 формата Спринта 0 (…_empty_fields_422);
- TC-AUTH-005 — /me возвращает данные записи (…_me_returns_user_record);
- TC-AUTH-006 — нет заголовка → 401 {ok:false} (…_without_token_401);
- TC-AUTH-007 — подделанный токен → 401 (…_forged_token_401);
- TC-AUTH-008 — истекший токен → 401 (…_expired_token_401);
- TC-AUTH-009 — logout аннулирует токен (…_logout_invalidates_token);
- TC-AUTH-010 — logout без валидного токена → 401 (…_without_valid_token_401);
- TC-AUTH-011 — пароль не в логах (…_password_not_in_logs);
- TC-AUTH-012 — блокировка IP без проверки учетных данных, блокировка не
  раскрывается (…_blocks_ip_without_credential_check);
- TC-AUTH-013 — учет по IP, чужой IP не затронут (…_block_is_per_ip);
- TC-AUTH-014 — нарастание и истечение блокировки (…_expires_and_escalates);
- TC-AUTH-015 — сброс счетчика после успеха (…_reset_after_success);
- TC-AUTH-016 — окно наблюдения сбрасывает счетчик, R-BF3 (…_window_reset).

«Готовность» tasks.md 1.1:
- успешный вход (токен выдается);
- все три причины отказа дают 401 с идентичной строкой ошибки;
- logout аннулирует токен (после logout запрос с токеном → 401);
- /me возвращает данные записи;
- истекший/подделанный токен → 401;
- пароль не попадает в логи;
- превышение порога неудачных попыток с одного IP → отказ входа с этого IP
  без проверки учетных данных (тот же 401/сообщение);
- после успешного входа счетчик сброшен.

time.sleep запрещен (qa-pipeline): TTL/блокировки — прямой сдвиг expires/
blocked_until в in-memory реестрах через monkeypatch time.time.
"""
import bcrypt
import pytest
from conftest import register


def _login(client, email="petrova@example.com", password="Qwerty123", **kw):
    body = {"email": email, "password": password}
    body.update(kw)
    return client.post("/api/auth/login", json=body)


def _client_at(client, host):
    """TestClient над тем же app с заданным IP источника (учет
    анти-брутфорса по IP; lifespan идемпотентен — init_db)."""
    from fastapi.testclient import TestClient

    return TestClient(client.app, client=(host, 50000))


def _register_one(client, email):
    resp = register(client, email=email)
    assert resp.status_code == 200, resp.text


@pytest.fixture()
def client(monkeypatch, tmp_path):
    """Локальное перекрытие conftest-фикстуры: create_app() + роутер auth.

    Роутер auth монтируется задачей 3.1; до ее мержа тесты монтируют его
    сами (проверка на уже подключенные маршруты — после 3.1 дубликата не
    будет). Env/БД — как в conftest (чистая БД в tmp_path).
    """
    monkeypatch.setenv("ADMIN_USER", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", "x")
    monkeypatch.setenv("SECRET", "test-secret")
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(tmp_path / "app.db"))
    from fastapi.testclient import TestClient

    from backend.app import create_app
    from backend.auth import router as auth_router

    app = create_app()
    if not any(getattr(r, "path", None) == "/api/auth/login" for r in app.routes):
        app.include_router(auth_router)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def no_bf(monkeypatch):
    """Порог блокировки выше любого числа попыток в тесте — для сценариев,
    где блокировка не должна вмешиваться."""
    from backend import auth

    monkeypatch.setattr(auth, "_BF_MAX_FAILURES", 10_000)


# --- Успешный вход -----------------------------------------------------------


def test_login_success_issues_token(client, no_bf):
    """Спека «Успешный вход ученика»: 200 {ok:true, token}, токен
    secrets.token_urlsafe(32) — 43 символа base64url."""
    _register_one(client, "petrova@example.com")
    resp = _login(client)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    token = data["token"]
    assert isinstance(token, str) and len(token) == 43
    assert token.replace("-", "").replace("_", "").isalnum()


def test_login_checks_password_against_bcrypt_hash(client, no_bf):
    """Спека «Проверка пароля против хэша»: вход разрешен сравнением с
    bcrypt-хэшем из users (в таблице только хэш)."""
    _register_one(client, "petrova@example.com")
    from conftest import fetch_user

    row = fetch_user("petrova@example.com")
    assert "$2b$" in row["password_hash"]
    assert "Qwerty123" != row["password_hash"]
    resp = _login(client)
    assert resp.status_code == 200


# --- Единое сообщение об отказе -----------------------------------------------


def test_login_failures_identical_message(client, no_bf):
    """Спека «Сообщение об отказе не раскрывает причину»: неверный пароль,
    несуществующий email — ответы посимвольно идентичны (код и текст),
    AUTH_FAIL_MESSAGE из sdd §10.1."""
    _register_one(client, "petrova@example.com")
    wrong_password = _login(client, password="wrong-pass")
    unknown_email = _login(client, email="ghost@example.com")
    for resp in (wrong_password, unknown_email):
        assert resp.status_code == 401
        assert resp.json() == {"ok": False, "error": "Неверный email или пароль"}
    assert (
        wrong_password.json()["error"]
        == unknown_email.json()["error"]
    )


# --- 422: хендлерная валидация ------------------------------------------------


def test_login_empty_fields_422(client, no_bf):
    """§10.1: пустое поле → 422 {ok:false, error:"<поле-ру>: поле
    обязательно"} — первая ошибка, формат Спринта 0."""
    resp = _login(client, email="  ")
    assert resp.status_code == 422
    assert resp.json() == {"ok": False, "error": "Email: поле обязательно"}

    resp = _login(client, email="petrova@example.com", password="")
    assert resp.status_code == 422
    assert resp.json() == {"ok": False, "error": "Пароль: поле обязательно"}


# --- /me и сессии --------------------------------------------------------------


def test_me_returns_user_record(client, no_bf):
    """§10.3: /me по токену возвращает {id, surname, name, patronymic, email}."""
    _register_one(client, "petrova@example.com")
    token = _login(client).json()["token"]
    resp = client.get("/api/auth/me", headers={"X-Session-Token": token})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    user = data["user"]
    assert user == {
        "id": 1,
        "surname": "Петрова-Водкина",
        "name": "Анна",
        "patronymic": "Оттовна",
        "email": "petrova@example.com",
    }


def test_me_logout_without_token_401(client, no_bf):
    """§10.2/§10.3: нет заголовка → 401 {ok:false} на /me и /logout."""
    for path in ("/api/auth/me", "/api/auth/logout"):
        resp = client.post(path) if path.endswith("logout") else client.get(path)
        assert resp.status_code == 401
        assert resp.json() == {"ok": False}


def test_forged_token_401(client, no_bf):
    """Спека «Запрос с подделанным токеном»: произвольная строка → 401
    {ok:false}."""
    for path in ("/api/auth/me", "/api/auth/logout"):
        headers = {"X-Session-Token": "forged-token-abc123"}
        resp = (
            client.post(path, headers=headers)
            if path.endswith("logout")
            else client.get(path, headers=headers)
        )
        assert resp.status_code == 401
        assert resp.json() == {"ok": False}


def test_expired_token_401(client, no_bf, monkeypatch):
    """Спека «Запрос с истекшим токеном»: TTL истек → 401; time.sleep не
    используется — сдвиг «сейчас» вперед мимо expires."""
    import backend.auth as auth

    _register_one(client, "petrova@example.com")
    token = _login(client).json()["token"]
    real_time = auth.time.time
    monkeypatch.setattr(
        auth.time, "time", lambda: real_time() + auth._TOKEN_TTL_SECONDS + 5
    )
    resp = client.get("/api/auth/me", headers={"X-Session-Token": token})
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}


def test_logout_invalidates_token(client, no_bf):
    """Спека «Токен не принимается после выхода»: 200 {ok:true}, затем /me с
    тем же токеном → 401."""
    _register_one(client, "petrova@example.com")
    token = _login(client).json()["token"]
    resp = client.post(
        "/api/auth/logout", headers={"X-Session-Token": token}
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}

    me_resp = client.get("/api/auth/me", headers={"X-Session-Token": token})
    assert me_resp.status_code == 401
    assert me_resp.json() == {"ok": False}


def test_logout_without_valid_token_401(client, no_bf):
    """§10.2: токена нет/неверный/истек → 401 {ok:false} — аннулировать
    нечего."""
    resp = client.post(
        "/api/auth/logout", headers={"X-Session-Token": "no-such-token"}
    )
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}


# --- Пароль не в логах ----------------------------------------------------------


def test_password_not_in_logs(client, no_bf, caplog):
    """Спека «Открытый пароль отсутствует в хранилище и логах» (NFR-3):
    после неудачного и успешного входа пароль не встречается в записях
    логгера; запись в users — только bcrypt-хэш."""
    import logging

    _register_one(client, "petrova@example.com")
    with caplog.at_level(logging.DEBUG):
        assert _login(client, password="wrong-pass").status_code == 401
        assert _login(client).status_code == 200

    assert "wrong-pass" not in caplog.text
    assert "Qwerty123" not in caplog.text


# --- Анти-брутфорс ---------------------------------------------------------------


def _bf_state():
    from backend import auth

    return auth._bf


def test_bruteforce_blocks_ip_without_credential_check(client, monkeypatch):
    """Спека «Блокировка после превышения порога попыток» + «Заблокированная
    попытка не раскрывает блокировку»: после _BF_MAX_FAILURES неудач с одного
    IP попытка с КОРРЕКТНЫми учетными данными отклоняется тем же 401/текстом
    без проверки учетных данных, токен не выдается."""
    import backend.auth as auth

    _register_one(client, "petrova@example.com")
    other = _client_at(client, "10.0.0.1")
    for _ in range(auth._BF_MAX_FAILURES):
        resp = _login(other, email="ghost@example.com")
        assert resp.status_code == 401

    resp = _login(other)  # верные учетные данные, но IP заблокирован
    assert resp.status_code == 401
    assert resp.json() == {"ok": False, "error": "Неверный email или пароль"}


def test_bruteforce_block_is_per_ip(client, monkeypatch):
    """Учет по IP: другой IP не затронут блокировкой и входит успешно."""
    import backend.auth as auth

    _register_one(client, "petrova@example.com")
    blocked = _client_at(client, "10.0.0.2")
    for _ in range(auth._BF_MAX_FAILURES):
        _login(blocked, email="ghost@example.com")

    other = _client_at(client, "10.0.0.3")
    resp = _login(other)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_bruteforce_block_expires_and_escalates(client, monkeypatch):
    """Спека «Длительность блокировки нарастает»: вторая блокировка длиннее
    первой; истекшая блокировка снимается (сдвиг времени, без sleep)."""
    import backend.auth as auth

    _register_one(client, "petrova@example.com")
    ip = "10.0.0.4"
    c = _client_at(client, ip)
    real_time = auth.time.time
    now = [real_time()]
    monkeypatch.setattr(auth.time, "time", lambda: now[0])

    # первая блокировка
    for _ in range(auth._BF_MAX_FAILURES):
        _login(c, email="ghost@example.com")
    st = _bf_state()[ip]
    first_block = st["blocked_until"] - now[0]
    assert auth._BF_BASE_BLOCK_SECONDS <= first_block <= auth._BF_MAX_BLOCK_SECONDS

    # попытки во время блокировки не проверяют учетные данные и не меняют level
    before_level = st["level"]
    resp = _login(c, email="ghost@example.com")
    assert resp.status_code == 401
    assert st["level"] == before_level

    # блокировка истекла
    now[0] = st["blocked_until"] + 1
    assert not auth._is_blocked(ip, now[0])

    # второй цикл неудач → вторая блокировка длиннее (нарастание)
    for _ in range(auth._BF_MAX_FAILURES):
        _login(c, email="ghost@example.com")
    second_block = st["blocked_until"] - now[0]
    assert second_block > first_block
    assert second_block <= auth._BF_MAX_BLOCK_SECONDS


def test_bruteforce_reset_after_success(client, monkeypatch):
    """Спека «Счетчик сбрасывается после успешного входа»: несколько неудач
    (меньше порога) → успех → счетчик обнулен, последующие изолированные
    неудачи не блокируют."""
    import backend.auth as auth

    _register_one(client, "petrova@example.com")
    ip = "10.0.0.5"
    c = _client_at(client, ip)
    for _ in range(auth._BF_MAX_FAILURES - 2):
        assert _login(c, email="ghost@example.com").status_code == 401
    assert _bf_state()[ip]["fails"] == auth._BF_MAX_FAILURES - 2

    # успешный вход с того же IP
    resp = _login(c)
    assert resp.status_code == 200
    assert _bf_state()[ip]["fails"] == 0

    # изолированные неудачи снова не доходят до порога
    for _ in range(auth._BF_MAX_FAILURES - 2):
        _login(c, email="ghost@example.com")
    resp = _login(c)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_bruteforce_window_reset(client, monkeypatch):
    """R-BF3: окно наблюдения (≥15 мин без неудач) сбрасывает счетчик — без
    сна, сдвигом времени."""
    import backend.auth as auth

    _register_one(client, "petrova@example.com")
    ip = "10.0.0.6"
    c = _client_at(client, ip)
    real_time = auth.time.time
    now = [real_time()]
    monkeypatch.setattr(auth.time, "time", lambda: now[0])

    for _ in range(auth._BF_MAX_FAILURES - 1):
        _login(c, email="ghost@example.com")
    assert _bf_state()[ip]["fails"] == auth._BF_MAX_FAILURES - 1

    now[0] += auth._BF_WINDOW_SECONDS + 1  # окно истекло
    _login(c, email="ghost@example.com")
    assert _bf_state()[ip]["fails"] == 1
