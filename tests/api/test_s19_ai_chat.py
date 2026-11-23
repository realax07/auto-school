"""API-носитель Спринта 19 — ИИ-чат «Главной» кабинета (change
add-ai-chat-home, задача 19.2.5; ПМ: API-носитель tests/api — за
qa_automation волны 19.4; прецедент test_s16_backend.py).

Трассировка TC-S19-001…TC-S19-012 (change add-ai-chat-home; Requirements —
openspec/changes/add-ai-chat-home/specs/ai-chat/spec.md; из КЕЙСОВ партии
закрыты здесь сценарии доступа/контракта/истории/изоляции/retention/
ошибок — TC-S19-009/010/012 остаются юнит-ногой адаптера провайдера в
tests/unit/test_s19_ai_chat.py, TC-S19-011 (граница retention ±1 с) —
тоже юнит; TC-S19-MAN-001 — боевой smoke hermes, ручной пункт):

- TC-S19-001  Доступ к чату: без X-Session-Token (и с неизвестным
              токеном) POST /api/ai/chat и GET /api/ai/chat/history →
              401 {ok:false}, содержимое не возвращается (Scenario
              «Без валидного токена»; NFR сессии).
- TC-S19-002  Контракт ответа: POST {message} → 200 {ok:true, reply};
              обмен user+assistant сохраняется в ai_messages (Scenario
              «Отправка и ответ», FR-19.3).
- TC-S19-003  История: GET → {ok, messages:[{role, text, created_at}]}
              хронологическим порядком; без сообщений — пустой список
              (Scenario «Пустой чат», FR-19.5).
- TC-S19-004  Изоляция пользователей: две учетки — каждая видит только
              свою историю; чужой user_id недоступен (Scenario
              «Изоляция пользователей»; NFR параметризованный SQL).
- TC-S19-005  Retention 14 дней: записи старше окна не показываются И
              удаляются физически на сервере (Scenario «Retention 14
              дней»; NFR — механика серверная, клиентской глубине не
              доверять).
- TC-S19-006  Границы окна: запись внутри окна (13 дней) остается
              (FR-19.5 «последние 14 дней»).
- TC-S19-007  Ошибка валидации: пустое/пробельное сообщение → 422
              {ok:false, error} человеческим текстом; провайдер НЕ
              вызывается, обмен не сохраняется (FR-19.3 «ошибки —
              человеческим текстом, без кодов»).
- TC-S19-008  Ошибка провайдера (503) — человеческий текст без
              кодов/стеков/механики («ProviderError»/«hermes»/
              «subprocess»); обмен НЕ сохраняется (Scenario «Ожидание и
              ошибка»; NFR ≤30 с).
- ДОПОЛНЕНИЕ (MIN-3 review-19.2, шейп 2): машинный FastAPI-дефолт
              422 {detail:[…]} на невалидном типе message — второй шейп
              ошибки, который фронт сводит к человеческому тексту
              (App.vue aiHumanError); носитель фиксирует его существование.

Провайдер мокается ШВОМ set_provider (backend/ai/provider.py::set_provider
— единственная точка замены активного провайдера; тот же шов, что в
web-носителях): реальных hermes-вызовов из тестов НЕТ (боевой smoke —
ручной пункт TC-S19-MAN-001). Клиент — TestClient над create_app() с
tmp-БД (conftest.client, без сети); time.sleep запрещен (спека
qa-pipeline) — старые записи создаются прямым INSERT с
created_at = datetime('now', '-N days').
"""

import sqlite3

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


class _QaFakeProvider:
    """QA-fake активного провайдера (шов set_provider): фиксированный ответ,
    журнал полученных messages; reply может быть исключением (TC-S19-008)."""

    name = "qa-fake"

    def __init__(self, reply: object = FAKE_REPLY):
        self.reply = reply
        self.calls = []

    def generate(self, messages):
        self.calls.append(list(messages))
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


@pytest.fixture()
def fake_provider():
    """Активный провайдер заменен через set_provider (ТОТ ЖЕ шов, что в
    web-носителях TC-S19-WEB-002); после теста — восстановление прежнего."""
    fake = _QaFakeProvider()
    previous = ai_provider.active_provider()
    ai_provider.set_provider(fake)
    yield fake
    ai_provider.set_provider(previous)


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
    conn.close()


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


# --- TC-S19-001: доступ без валидной сессии ---------------------------------------


def test_tc_s19_001_chat_without_session_unauthorized(client):
    """TC-S19-001: POST и GET без X-Session-Token → 401 {ok:false};
    содержимое чата/истории не возвращается."""
    resp = client.post(CHAT_URL, json={"message": "привет"})
    assert resp.status_code == 401, resp.text
    assert resp.json() == {"ok": False}
    resp = client.get(HISTORY_URL)
    assert resp.status_code == 401, resp.text
    assert resp.json() == {"ok": False}


def test_tc_s19_001_chat_with_bogus_token_unauthorized(client):
    """TC-S19-001: неизвестный/истекший токен — тот же отказ без содержимого
    (Scenario «Без валидного токена»: «или с истекшим»)."""
    headers = {"X-Session-Token": "not-a-real-token"}
    resp = client.post(CHAT_URL, json={"message": "привет"}, headers=headers)
    assert resp.status_code == 401, resp.text
    assert resp.json() == {"ok": False}
    resp = client.get(HISTORY_URL, headers=headers)
    assert resp.status_code == 401, resp.text
    assert ai_rows() == []


# --- TC-S19-002: контракт ответа -------------------------------------------------


def test_tc_s19_002_chat_contract_message_to_reply(client, fake_provider):
    """TC-S19-002: POST {message} → 200 {ok:true, reply}; в провайдер уходит
    сообщение ученика; обмен user+assistant сохранен в ai_messages."""
    headers = student_headers(client, "s19api-a@example.com")
    resp = client.post(
        CHAT_URL, json={"message": "Как проехать круг?"}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["reply"] == FAKE_REPLY

    # в провайдер ушло ровно новое сообщение (история была пуста)
    assert fake_provider.calls == [
        [{"role": "user", "text": "Как проехать круг?"}]
    ]

    rows = ai_rows()
    assert [(r["role"], r["text"]) for r in rows] == [
        ("user", "Как проехать круг?"),
        ("assistant", FAKE_REPLY),
    ]


# --- TC-S19-003: история своей учетки ---------------------------------------------


def test_tc_s19_003_history_shape_and_order(client, fake_provider):
    """TC-S19-003: GET → {ok, messages:[{role, text, created_at}]} в
    хронологическом порядке (user до assistant)."""
    headers = student_headers(client, "s19api-b@example.com")
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
    """TC-S19-003 (Scenario «Пустой чат»): нет сообщений за окно → пустой
    список; приветствие пустого чата решает фронт (ai-empty)."""
    headers = student_headers(client, "s19api-empty@example.com")
    resp = client.get(HISTORY_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"ok": True, "messages": []}


# --- TC-S19-004: изоляция user_id -------------------------------------------------


def test_tc_s19_004_history_isolated_per_user(client, fake_provider):
    """TC-S19-004: две учетки — чужая история недоступна: у B пусто (ни A,
    ни чужие user_id), у A только свои сообщения."""
    headers_a = student_headers(client, "s19api-user-a@example.com")
    headers_b = student_headers(client, "s19api-user-b@example.com")

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


# --- TC-S19-005/006: retention 14 дней ---------------------------------------------


def test_tc_s19_005_retention_deletes_old_rows(client):
    """TC-S19-005: записи старше 14 дней не показываются и удаляются
    физически (retention — серверная механика, NFR; клиентской глубине не
    доверять — окно считается на сервере по created_at)."""
    email = "s19api-retention@example.com"
    headers = student_headers(client, email)
    user_id = fetch_user(email)["id"]  # seed в СВОЮ историю (user_id сессии)
    seed_message(user_id, "Старое сообщение 20 дней", age_days=20)
    seed_message(user_id, "Старое сообщение 15 дней", role="assistant", age_days=15)

    resp = client.get(HISTORY_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"ok": True, "messages": []}

    # удалены физически, а не только скрыты (FR-19.5 «старее скрывается
    # и удаляется»; DELETE в BEGIN IMMEDIATE транзакции с SELECT)
    assert ai_rows() == []


def test_tc_s19_006_retention_window_keeps_recent(client):
    """TC-S19-006: запись внутри окна (13 дней) — в истории и не удалена."""
    email = "s19api-recent@example.com"
    headers = student_headers(client, email)
    user_id = fetch_user(email)["id"]
    seed_message(user_id, "Свежее сообщение 13 дней", age_days=13)

    resp = client.get(HISTORY_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    messages = resp.json()["messages"]
    assert [m["text"] for m in messages] == ["Свежее сообщение 13 дней"]
    assert len(ai_rows()) == 1


# --- TC-S19-007/008: ошибки — человеческие тексты ----------------------------------


def test_tc_s19_007_empty_message_422_human_text(client, fake_provider):
    """TC-S19-007: пустое/пробельное сообщение → 422 {ok:false, error}
    человеческим текстом; провайдер НЕ вызывается, записей нет."""
    headers = student_headers(client, "s19api-validate@example.com")
    for message in ("", "   \n\t "):
        resp = client.post(CHAT_URL, json={"message": message}, headers=headers)
        assert resp.status_code == 422, resp.text
        body = resp.json()
        assert body["ok"] is False
        assert "Сообщение" in body["error"]
    assert fake_provider.calls == []  # адаптер не дергался
    assert ai_rows() == []


def test_tc_s19_007_wrong_type_message_422_detail_shape(client):
    """TC-S19-007 (дополнение, шейп 2 — MIN-3 review-19.2): невалидный тип
    message ловит pydantic ДО хендлера — машинный FastAPI-дефолт
    422 {detail:[…]} (глобального обработчика валидации в app.py нет);
    фронт (aiHumanError) сводит его к человеческому тексту. Носитель
    фиксирует существование второго шейпа."""
    headers = student_headers(client, "s19api-shape@example.com")
    resp = client.post(CHAT_URL, json={"message": 123}, headers=headers)
    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert "detail" in body  # машинный шейп — БЕЗ ok/error
    assert ai_rows() == []


def test_tc_s19_fr196_topics_system_prompt_guard():
    """TC-S19-API-001 нога «темы» (FR-19.6, Scenario «Ограничение тем»,
    объем 19.2.5): ограничение тем на API-носителе — контроль константы
    SYSTEM_PROMPT провайдера (содержательный отказ боевого hermes —
    ручной TC-S19-MAN-001; механика stdin-канала — юнит TC-S19-009).
    Промпт обязан ограничивать темы: ПДД, дорожные ситуации в России,
    ГИБДД; опора на content/pdd и интернет; посторонние вопросы —
    вежливый отказ без ответа по существу."""
    prompt = ai_provider.SYSTEM_PROMPT
    assert "ГигаЧат — помощник по обучению ПДД" in prompt
    assert "Правила дорожного движения" in prompt
    assert "дорожные ситуации в России" in prompt
    assert "ГИБДД" in prompt
    assert "content/pdd" in prompt and "интернет" in prompt
    assert "вежливо отклони" in prompt  # посторонние темы — отказ по существа


def test_tc_s19_008_provider_error_503_human_text(client):
    """TC-S19-008: сбой провайдера → 503 {ok:false, error} — человеческий
    текст, без кодов/стеков/механики; обмен НЕ сохраняется (история —
    только состоявшиеся обмены). Провайдер подменен швом set_provider
    (fake бросает ProviderError — как юнит TC-S19-008)."""

    fake = _QaFakeProvider(reply=ai_provider.ProviderError())
    previous = ai_provider.active_provider()
    ai_provider.set_provider(fake)
    try:
        headers = student_headers(client, "s19api-error@example.com")
        resp = client.post(
            CHAT_URL, json={"message": "Любой вопрос"}, headers=headers
        )
    finally:
        ai_provider.set_provider(previous)

    assert resp.status_code == 503, resp.text
    body = resp.json()
    assert body["ok"] is False
    error = body["error"]
    assert error  # человеческий текст есть
    # без кодов/стеков/механики (FR-19.3): служебные маркеры не просачиваются
    for fragment in ("ProviderError", "Traceback", "hermes", "subprocess", "503"):
        assert fragment not in error
    assert ai_rows() == []
