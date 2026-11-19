"""Юнит-носитель Спринта 19 — ИИ-чат «Главной» кабинета (change
add-ai-chat-home, волна 19.2; ПМ dc24970: API-носитель tests/api —
за qa_automation на 19.4, dev несет юнит-носитель tests/unit).

Трассировка TC-S19-001…TC-S19-011 (change add-ai-chat-home; Requirements —
openspec/changes/add-ai-chat-home/specs/ai-chat/spec.md; TC-S19-011 —
граничный носитель retention, MIN-2 CR-19.2):

- TC-S19-001  Доступ к чату: без валидного токена POST /api/ai/chat и
              GET /api/ai/chat/history → 401 {ok:false}, содержимое не
              возвращается (Requirement «Доступ…», сценарий «Без валидного
              токена»; NFR сессии X-Session-Token).
- TC-S19-002  Контракт ответа: POST {message} → 200 {ok, reply}; обмен
              user+assistant сохраняется в ai_messages (FR-19.3,
              Requirement «Композер…», сценарий «Отправка и ответ»).
- TC-S19-003  История своей учетки: GET → {ok, messages:[{role, text,
              created_at}]}, хронологический порядок user→assistant
              (FR-19.5, сценарий «Подхват при повторном входе»).
- TC-S19-004  Изоляция пользователей: две учетки — каждая видит только
              свою историю, чужая недоступна (сценарий «Изоляция
              пользователей»; NFR).
- TC-S19-005  Retention 14 дней: записи старше 14 дней не показываются
              и УДАЛЯЮТСЯ на сервере (сценарий «Retention 14 дней»;
              NFR — механика серверная, DELETE в BEGIN IMMEDIATE с
              SELECT — ответ ОВ-2 review-001).
- TC-S19-006  Retention глубина: запись младше окна (13 дней) остается
              в истории (FR-19.5 «последние 14 дней»).
- TC-S19-007  Ошибка валидации: пустое/пробельное сообщение → 422,
              человеческий текст, провайдер не вызывается (FR-19.3
              «ошибки — человеческим текстом, без кодов»).
- TC-S19-008  Ошибка провайдера (таймаут/сбой адаптера): 503 с
              человеческим текстом без кодов/стеков; обмен НЕ сохраняется
              (FR-19.3 сценарий «Ожидание и ошибка»; NFR ≤30 с).
- TC-S19-009  Адаптер-провайдер (unit, Task 19.2.1): текст запроса —
              через --query-file - (stdin), НЕ argv (review-001 MIN-2 /
              review-002: ps-видимость argv); бюджет --run-budget;
              собственный таймаут ≤30 с (NFR).
- TC-S19-010  Адаптер-провайдер: таймаут / ненулевой код / пустой ответ →
              ProviderError без деталей (NFR: секреты/argv не в логах;
              наружу — только человеческий текст routes.py).

Провайдер в тестах МОККИРУЕТСЯ (monkeypatch backend.ai.provider
generate_reply / subprocess.run) — реальных вызовов hermes CLI из тестов
НЕТ (боевой smoke провайдера — 19.4, план прогонов «hermes CLI на хосте»).
Клиент — TestClient над create_app() с tmp-БД (conftest.client, без
сети); time.sleep запрещен (спека qa-pipeline) — старые записи создаются
прямым INSERT с created_at = datetime('now', '-N days').
"""

import sqlite3
import subprocess

import pytest

import backend.ai.provider as ai_provider
from conftest import db_path, fetch_user, register

CHAT_URL = "/api/ai/chat"
HISTORY_URL = "/api/ai/chat/history"
STUDENT_PASSWORD = "Qwerty123"  # пароль базового набора valid_body (conftest)

FAKE_REPLY = "Тестовый ответ ГигаЧата: снижайте скорость перед пешеходным переходом."


# --- helpers -------------------------------------------------------------------


def student_headers(client, email):
    """Регистрация базовым набором + вход → заголовок X-Session-Token."""
    resp = register(client, email=email)
    assert resp.status_code == 200, resp.text
    login = client.post(
        "/api/auth/login", json={"email": email, "password": STUDENT_PASSWORD}
    )
    assert login.status_code == 200, login.text
    assert login.json()["route"] == "student-cabinet"
    return {"X-Session-Token": login.json()["token"]}


@pytest.fixture()
def fake_generate(monkeypatch):
    """Мок провайдера на уровне шва generate_reply (routes.py вызывает
    только его): возвращает FAKE_REPLY, запоминает полученные messages."""
    calls = {}

    def _generate(messages):
        calls["messages"] = messages
        return FAKE_REPLY

    monkeypatch.setattr(ai_provider, "generate_reply", _generate)
    return calls


def seed_message(user_id, text, role="user", age_days=0):
    """Прямой INSERT в ai_messages (тот же файл БД, что использует
    приложение) с created_at = now - age_days; детерминизм без time.sleep."""
    conn = sqlite3.connect(db_path())
    conn.execute(
        "INSERT INTO ai_messages (user_id, role, text, created_at)"
        " VALUES (?, ?, ?, datetime('now', ?))",
        (user_id, role, text, f"-{age_days} days"),
    )
    conn.commit()
    user_ids = conn.execute(
        "SELECT id FROM ai_messages WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    return user_ids


def ai_rows():
    """Все строки ai_messages (проверки сохранения/удаления)."""
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT user_id, role, text, created_at FROM ai_messages"
        " ORDER BY created_at ASC, id ASC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# --- TC-S19-001: auth 401 --------------------------------------------------------


def test_tc_s19_001_chat_without_session_unauthorized(client):
    """TC-S19-001: POST и GET без X-Session-Token → 401 {ok:false}."""
    resp = client.post(CHAT_URL, json={"message": "привет"})
    assert resp.status_code == 401, resp.text
    assert resp.json() == {"ok": False}
    resp = client.get(HISTORY_URL)
    assert resp.status_code == 401, resp.text
    assert resp.json() == {"ok": False}


def test_tc_s19_001_chat_with_bogus_token_unauthorized(client):
    """TC-S19-001: неизвестный/истекший токен — тот же отказ без содержимого."""
    headers = {"X-Session-Token": "not-a-real-token"}
    resp = client.post(CHAT_URL, json={"message": "привет"}, headers=headers)
    assert resp.status_code == 401, resp.text
    resp = client.get(HISTORY_URL, headers=headers)
    assert resp.status_code == 401, resp.text
    assert ai_rows() == []


# --- TC-S19-002: контракт ответа -------------------------------------------------


def test_tc_s19_002_chat_contract_message_to_reply(client, fake_generate):
    """TC-S19-002: POST {message} → 200 {ok:true, reply}; в провайдер
    уходит сообщение ученика; обмен user+assistant сохранен в БД."""
    headers = student_headers(client, "s19chat-a@example.com")
    resp = client.post(CHAT_URL, json={"message": "Как проехать круг?"}, headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["reply"] == FAKE_REPLY

    # Провайдер получил ровно новое сообщение (история была пуста).
    assert fake_generate["messages"] == [{"role": "user", "text": "Как проехать круг?"}]

    rows = ai_rows()
    assert [(r["role"], r["text"]) for r in rows] == [
        ("user", "Как проехать круг?"),
        ("assistant", FAKE_REPLY),
    ]


# --- TC-S19-003: история своей учетки ---------------------------------------------


def test_tc_s19_003_history_shape_and_order(client, fake_generate):
    """TC-S19-003: GET → {ok, messages:[{role, text, created_at}]} в
    хронологическом порядке (user до assistant)."""
    headers = student_headers(client, "s19chat-b@example.com")
    client.post(CHAT_URL, json={"message": "Первый вопрос"}, headers=headers)
    client.post(CHAT_URL, json={"message": "Второй вопрос"}, headers=headers)

    resp = client.get(HISTORY_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    messages = body["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant", "user", "assistant"]
    assert [m["text"] for m in messages] == [
        "Первый вопрос", FAKE_REPLY, "Второй вопрос", FAKE_REPLY,
    ]
    for message in messages:
        assert set(message) == {"role", "text", "created_at"}
        assert message["created_at"]  # серверная метка SQLite datetime


def test_tc_s19_003_history_empty(client):
    """TC-S19-003: нет сообщений за окно → пустой список (пустой чат —
    приветствие решает фронт, сервер отдает пустой журнал)."""
    headers = student_headers(client, "s19chat-empty@example.com")
    resp = client.get(HISTORY_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"ok": True, "messages": []}


# --- TC-S19-004: изоляция user_id --------------------------------------------------


def test_tc_s19_004_history_isolated_per_user(client, fake_generate):
    """TC-S19-004: две учетки — чужая история недоступна: у B пусто,
    у A только свои сообщения; POST B не смешивается с A."""
    headers_a = student_headers(client, "s19chat-user-a@example.com")
    headers_b = student_headers(client, "s19chat-user-b@example.com")

    client.post(CHAT_URL, json={"message": "Вопрос ученика A"}, headers=headers_a)
    seed_message(999999, "Чужая строка другого user_id", role="assistant")

    resp_b = client.get(HISTORY_URL, headers=headers_b)
    assert resp_b.status_code == 200, resp_b.text
    assert resp_b.json()["messages"] == []  # B не видит ни A, ни чужие user_id

    resp_a = client.get(HISTORY_URL, headers=headers_a)
    assert resp_a.status_code == 200, resp_a.text
    assert [(m["role"], m["text"]) for m in resp_a.json()["messages"]] == [
        ("user", "Вопрос ученика A"),
        ("assistant", FAKE_REPLY),
    ]


# --- TC-S19-005/006: retention 14 дней ----------------------------------------------


def test_tc_s19_005_retention_deletes_old_rows(client):
    """TC-S19-005: записи старше 14 дней не показываются и удаляются
    физически (retention — серверная механика, NFR)."""
    email = "s19chat-retention@example.com"
    headers = student_headers(client, email)
    user_id = fetch_user(email)["id"]  # seed в СВОЮ историю (user_id сессии)
    seed_message(user_id, "Старое сообщение 20 дней", age_days=20)
    seed_message(user_id, "Старое сообщение 15 дней", role="assistant", age_days=15)

    resp = client.get(HISTORY_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"ok": True, "messages": []}

    # Удалены физически, а не только скрыты (FR-19.5 «старее скрывается
    # и удаляется»; удаление в BEGIN IMMEDIATE транзакции с SELECT).
    assert ai_rows() == []


def test_tc_s19_006_retention_window_keeps_recent(client):
    """TC-S19-006: запись внутри окна (13 дней) — в истории и не удалена."""
    email = "s19chat-recent@example.com"
    headers = student_headers(client, email)
    user_id = fetch_user(email)["id"]
    seed_message(user_id, "Свежее сообщение 13 дней", age_days=13)

    resp = client.get(HISTORY_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    messages = resp.json()["messages"]
    assert [m["text"] for m in messages] == ["Свежее сообщение 13 дней"]
    assert len(ai_rows()) == 1


def test_tc_s19_011_retention_exact_boundary(client):
    """TC-S19-011 (MIN-2 CR-19.2): граничное поведение retention —
    строка на 1 секунду старше 14 дней удаляется физически; строка на
    границе окна (13d23h59m59s) остается. Детерминизм — прямым контролем
    БД (конвенция файла: без time.sleep): delete-строка (floored
    T0−14d−1с) строго старше границы при любом времени запроса,
    keep-строка (floored T0−14d+1с) строго моложе — при любой реальной
    латентности запроса < ~1с."""
    import sqlite3

    email = "s19chat-boundary@example.com"
    headers = student_headers(client, email)
    user_id = fetch_user(email)["id"]
    conn = sqlite3.connect(db_path())
    conn.execute(
        "INSERT INTO ai_messages (user_id, role, text, created_at)"
        " VALUES (?, ?, ?, datetime('now', '-14 days', '-1 seconds'))",
        (user_id, "user", "За границей на 1 секунду"),
    )
    conn.execute(
        "INSERT INTO ai_messages (user_id, role, text, created_at)"
        " VALUES (?, ?, ?, datetime('now', '-13 days', '-23 hours'"
        ", '-59 minutes', '-59 seconds'))",
        (user_id, "assistant", "На границе окна"),
    )
    conn.commit()
    conn.close()

    resp = client.get(HISTORY_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    messages = resp.json()["messages"]
    assert [m["text"] for m in messages] == ["На границе окна"]
    remaining = [r["text"] for r in ai_rows()]
    assert remaining == ["На границе окна"]


# --- TC-S19-007/008: ошибки ----------------------------------------------------------


def test_tc_s19_007_empty_message_422_human_text(client, fake_generate):
    """TC-S19-007: пустое/пробельное сообщение → 422 {ok:false, error}
    человеческим текстом; провайдер НЕ вызывается, записей нет."""
    headers = student_headers(client, "s19chat-validate@example.com")
    for message in ("", "   \n\t "):
        resp = client.post(CHAT_URL, json={"message": message}, headers=headers)
        assert resp.status_code == 422, resp.text
        body = resp.json()
        assert body["ok"] is False
        assert "Сообщение" in body["error"]
    assert "messages" not in fake_generate  # адаптер не дергался
    assert ai_rows() == []


def test_tc_s19_008_provider_error_503_human_text(client, monkeypatch):
    """TC-S19-008: сбой провайдера → 503 {ok:false, error} — человеческий
    текст, без кодов/стеков/механики; обмен НЕ сохраняется (история —
    только состоявшиеся обмены)."""

    def _boom(messages):
        raise ai_provider.ProviderError

    monkeypatch.setattr(ai_provider, "generate_reply", _boom)
    headers = student_headers(client, "s19chat-error@example.com")
    resp = client.post(CHAT_URL, json={"message": "Любой вопрос"}, headers=headers)
    assert resp.status_code == 503, resp.text
    body = resp.json()
    assert body["ok"] is False
    error = body["error"]
    assert error  # человеческий текст есть
    # без кодов/стеков/механики (FR-19.3): служебные маркеры не просачиваются
    for fragment in ("ProviderError", "Traceback", "hermes", "subprocess", "503"):
        assert fragment not in error
    assert ai_rows() == []


# --- TC-S19-009/010: адаптер-провайдер (unit чистой механики 19.2.1) ------------------


class _FakeCompleted:
    def __init__(self, returncode=0, stdout=FAKE_REPLY):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = ""


def test_tc_s19_009_provider_sends_text_via_stdin_not_argv(monkeypatch):
    """TC-S19-009 (MIN-2 review-001/review-002): текст запроса (системный
    промпт + сообщение ученика) — через --query-file '-' (stdin), НЕ argv;
    бюджет --run-budget; собственный таймаут ≤30 с."""
    captured = {}

    def _fake_run(command, input=None, capture_output=True, text=True, timeout=None):
        captured["argv"] = command
        captured["stdin"] = input
        captured["timeout"] = timeout
        return _FakeCompleted()

    monkeypatch.setattr(ai_provider.subprocess, "run", _fake_run)
    reply = ai_provider.HermesSessionProvider().generate(
        [
            {"role": "user", "text": "Вопрос до"},
            {"role": "assistant", "text": "Ответ до"},
            {"role": "user", "text": "Сообщение с $(подсказкой) и `кавычками`"},
        ]
    )
    assert reply == FAKE_REPLY

    argv = captured["argv"]
    assert "hermes" == argv[0] and "chat" == argv[1]
    # канал текста — файл/stdin, мимо argv (ps-видимость): --query-file '-'
    assert "--query-file" in argv
    assert argv[argv.index("--query-file") + 1] == "-"
    # бюджет hermes + собственный таймаут ≤30 с (NFR)
    assert "--run-budget" in argv
    assert int(argv[argv.index("--run-budget") + 1]) <= 30
    assert captured["timeout"] == ai_provider.PROVIDER_TIMEOUT_SECONDS <= 30
    # ни сообщение ученика, ни системный промпт НЕ в argv (MIN-2)
    joined = " ".join(argv)
    assert "Сообщение с $(подсказкой)" not in joined
    assert ai_provider.SYSTEM_PROMPT not in joined
    assert "ГигаЧат — помощник по обучению ПДД" in ai_provider.SYSTEM_PROMPT
    assert "ГИБДД" in ai_provider.SYSTEM_PROMPT
    # текст ушел в stdin: системный промпт + стенограмма + приглашение
    stdin_text = captured["stdin"]
    assert "Сообщение с $(подсказкой) и `кавычками`" in stdin_text
    assert "Вопрос до" in stdin_text  # контекст истории
    assert stdin_text.endswith("ГигаЧат:")


def test_tc_s19_010_provider_failure_modes_raise_provider_error(monkeypatch):
    """TC-S19-010: таймаут / ненулевой код / пустой ответ → ProviderError
    (без деталей: наружу routes.py отдаст только человеческий текст)."""
    provider = ai_provider.HermesSessionProvider()
    messages = [{"role": "user", "text": "вопрос"}]

    def _timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="hermes chat", timeout=30)

    monkeypatch.setattr(ai_provider.subprocess, "run", _timeout)
    with pytest.raises(ai_provider.ProviderError):
        provider.generate(messages)

    monkeypatch.setattr(
        ai_provider.subprocess, "run", lambda *a, **k: _FakeCompleted(returncode=1)
    )
    with pytest.raises(ai_provider.ProviderError):
        provider.generate(messages)

    monkeypatch.setattr(
        ai_provider.subprocess, "run", lambda *a, **k: _FakeCompleted(stdout="  \n ")
    )
    with pytest.raises(ai_provider.ProviderError):
        provider.generate(messages)

    # детали в исключении не хранятся (NFR-3)
    assert not ai_provider.ProviderError().args
