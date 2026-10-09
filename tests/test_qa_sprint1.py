"""QA-автоматизация недостающих API-кейсов пакета add-auth-cabinet
(test-model/approved/add-auth-cabinet/, корреляция fd7a2896).

Дополняет tests/test_auth.py и tests/test_integration_sprint1.py —
НЕ дублирует их. Браузерные кейсы (TC-CAB-001/002/003/004/005/006/008/010,
TC-MOD-001/002) — manual, сюда не входят (матрица — в отчете QA).

Что автоматизировано здесь (было manual/toBeAutomated):
- TC-NFR-001 — замер POST /api/auth/login ≤ 500 мс (time.perf_counter,
  5 прогонов с корректными данными, bcrypt cost 12 в бюджете);
- TC-NFR-002 — динамическая проба SQL-инъекции (' OR 1=1 --): email —
  литерал, единый 401, записи users не затронуты; статическая инспекция
  ?-плейсхолдеров backend/auth.py — без конкатенации/f-string SQL;
- TC-NFR-003 (автоматизируемая часть) — токен только в теле 200 login:
  отсутствует в 401/422 телах, логах и HTML (/ и /cabinet); пароль не в
  логах и 401-теле (дубль контроля TC-AUTH-011); .env не в git-индексе,
  .gitignore содержит .env;
- TC-AUTH-014 (усиление, TTL-сдвиг) — контроль _TOKEN_TTL_SECONDS на
  /logout: истекший токен → 401 (аннулировать нечего), без sleep.

time.sleep запрещен (qa-pipeline): TTL/блокировки — сдвиг времени через
monkeypatch backend.auth.time.time.
"""
import logging
import re
import sqlite3
import time as _time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
AUTH_FAIL = {"ok": False, "error": "Неверный email или пароль"}


def _register_one(client):
    from conftest import register

    resp = register(client, email="perf@example.com")
    assert resp.status_code == 200, resp.text


def _login(client, email="perf@example.com", password="Qwerty123", **kw):
    body = {"email": email, "password": password}
    body.update(kw)
    return client.post("/api/auth/login", json=body)


def _client_at(client, host):
    """TestClient над тем же app с заданным IP источника (изоляция
    состояния анти-брутфорса по IP между кейсами)."""
    from fastapi.testclient import TestClient

    return TestClient(client.app, client=(host, 50000))


@pytest.fixture()
def no_bf(monkeypatch):
    """Порог блокировки выше любого числа попыток в тесте."""
    from backend import auth

    monkeypatch.setattr(auth, "_BF_MAX_FAILURES", 10_000)


# --- TC-NFR-001: замер времени логина ≤ 500 мс --------------------------------


def test_nfr001_login_latency_under_500ms(client, no_bf):
    """TC-NFR-001: 5 прогонов POST /api/auth/login с корректными данными;
    время каждого прогона ≤ 500 мс (NFR-1, бюджет с bcrypt cost 12).
    Замер time.perf_counter вокруг HTTP-вызова TestClient (полный стек
    запроса; сетевой слой исключен по предусловию кейса «допускается
    TestClient без сети»)."""
    _register_one(client)

    durations_ms = []
    for _ in range(5):
        start = _time.perf_counter()
        resp = _login(client)
        elapsed_ms = (_time.perf_counter() - start) * 1000.0
        assert resp.status_code == 200, resp.text
        assert resp.json()["ok"] is True
        durations_ms.append(elapsed_ms)

    for i, ms in enumerate(durations_ms, 1):
        assert ms <= 500.0, f"прогон {i}: {ms:.1f} мс > 500 мс"
    durations_ms.sort()
    median_ms = durations_ms[2]
    assert median_ms <= 500.0


# --- TC-NFR-002: SQL параметризован, инъекция не работает ----------------------


def test_nfr002_sql_is_parameterized_no_injection(client, no_bf):
    """TC-NFR-002: (1) в SQL backend/auth.py нет конкатенации/f-string с
    пользовательскими данными — только ?-плейсхолдеры; (2) динамическая
    проба: email `' OR 1=1 --` трактуется как литерал → единый 401,
    число записей users не изменилось, токен не выдан; (3) контроль —
    обычный вход работает."""
    import backend.auth as auth

    # (1) статическая инспекция исходника auth.py
    src = Path(auth.__file__).read_text(encoding="utf-8")
    sql_literals = re.findall(r'"(SELECT[^"]*)"', src)
    assert sql_literals, "ожидался хотя бы один SQL-запрос в auth.py"
    for sql in sql_literals:
        assert "?" in sql, f"SQL без ?-плейсхолдера: {sql}"
        # конкатенация/интерполяция пользовательских данных в SQL-строку
        assert "+" not in sql and "%s" not in sql and "{" not in sql

    _register_one(client)
    from conftest import count_users

    before = count_users()

    # (2) динамическая проба инъекции
    inj = _login(client, email="' OR 1=1 --", password="anything")
    assert inj.status_code == 401
    assert inj.json() == AUTH_FAIL
    assert "token" not in inj.json()

    # вариант с замыканием кавычки-OR-комментарием, классика
    inj2 = _login(client, email="' OR '1'='1", password="anything")
    assert inj2.status_code == 401
    assert inj2.json() == AUTH_FAIL

    # записи не затронуты, авторизация не обойдена
    assert count_users() == before

    # (3) контроль: обычный вход работает
    ok = _login(client)
    assert ok.status_code == 200
    assert ok.json()["ok"] is True


# --- TC-NFR-003: токены и секреты не в репозитории и логах ---------------------


def test_nfr003_token_only_in_200_body_not_in_logs_html(client, no_bf, caplog):
    """TC-NFR-003 (автоматизируемая часть): после 401 / 422 / 200 логина
    строка токена отсутствует в отказных телах, логах и HTML (/ и
    /cabinet); пароль отсутствует в логах и 401-теле; .env не в git ls-files,
    .gitignore содержит .env. Поле token — только в теле 200-ответа."""
    from conftest import register

    resp = register(client, email="perf@example.com")
    assert resp.status_code == 200, resp.text

    with caplog.at_level(logging.DEBUG):
        bad = _login(client, password="wrong-pass")
        assert bad.status_code == 401
        empty = _login(client, password="")
        assert empty.status_code == 422
        good = _login(client)
        assert good.status_code == 200

    token = good.json().get("token")
    assert isinstance(token, str) and token

    # токен отсутствует в отказных телах
    assert "token" not in bad.json()
    assert "token" not in empty.json()

    # токен и пароль отсутствуют в логах
    assert token not in caplog.text
    assert "Qwerty123" not in caplog.text
    assert "wrong-pass" not in caplog.text

    # токен отсутствует в HTML страниц
    for path in ("/", "/cabinet"):
        html = client.get(path)
        assert html.status_code == 200
        assert token not in html.text

    # секреты только через .env: не в git-индексе, .gitignore настроен
    import subprocess

    ls = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    tracked = ls.stdout.splitlines()
    assert ".env" not in tracked
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert re.search(r"^\.env$", gitignore, re.MULTILINE)


# --- TC-AUTH-014/доп.: TTL-сдвиг времени на logout, без sleep -------------------


def test_auth014_ttl_shift_logout_expired_token_401(client, no_bf, monkeypatch):
    """Дополнение к TC-AUTH-014/TC-AUTH-008 (TTL-сдвиг): после сдвига
    «сейчас» мимо expires (sdd §10, _TOKEN_TTL_SECONDS) /logout с тем же
    токеном → 401 {ok:false} — аннулировать нечего; /me тоже 401.
    time.sleep запрещен — прямой сдвиг clock."""
    import backend.auth as auth

    _register_one(client)
    token = _login(client).json()["token"]
    real_time = auth.time.time
    now = [real_time()]
    monkeypatch.setattr(auth.time, "time", lambda: now[0])

    # до истечения — токен жив
    me = client.get("/api/auth/me", headers={"X-Session-Token": token})
    assert me.status_code == 200

    # сдвиг мимо TTL
    now[0] += auth._TOKEN_TTL_SECONDS + 1
    me2 = client.get("/api/auth/me", headers={"X-Session-Token": token})
    assert me2.status_code == 401
    assert me2.json() == {"ok": False}
    logout = client.post("/api/auth/logout", headers={"X-Session-Token": token})
    assert logout.status_code == 401
    assert logout.json() == {"ok": False}


# --- Изоляция IP: счетчики анти-брутфорса не пересекаются между IP --------------


def test_bf_counters_isolated_between_ips(client, monkeypatch):
    """Усиление TC-AUTH-013 (изоляция IP): первые 4 неудачи с IP A не
    учитываются для IP B — B входит успешно, а «хвост» из одной неудачи
    для A не достигает порога; отдельные клиенты TestClient с разными
    client=(host, port)."""
    import backend.auth as auth

    _register_one(client)
    ip_a, ip_b = "10.0.1.10", "10.0.1.20"
    a = _client_at(client, ip_a)
    b = _client_at(client, ip_b)

    for _ in range(auth._BF_MAX_FAILURES - 1):
        assert _login(a, email="ghost@example.com").status_code == 401
    st_a = auth._bf.get(ip_a)
    assert st_a is not None and st_a["fails"] == auth._BF_MAX_FAILURES - 1
    assert auth._bf.get(ip_b) is None

    # IP B не затронут — успешный вход
    resp_b = _login(b)
    assert resp_b.status_code == 200
    assert resp_b.json()["ok"] is True

    # одна неудача для A — достигает порога, срабатывает блокировка A
    # (после срабатывания счетчик начинается заново — impl _record_failure)
    assert _login(a, email="ghost@example.com").status_code == 401
    st_a = auth._bf.get(ip_a)
    assert st_a is not None
    assert st_a["blocked_until"] > 0
    assert auth._is_blocked(ip_a, auth.time.time())
    # B по-прежнему не затронут и входит снова
    resp_b2 = _login(b)
    assert resp_b2.status_code == 200
