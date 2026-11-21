"""API ИИ-чата «Главной» кабинета ученика (Спринт 19, change
add-ai-chat-home, задача 19.2.3; design.md «Решение 1»/«Решение 2»).

POST /api/ai/chat — {message} → {reply}: генерация ТОЛЬКО через
провайдер-адаптер backend/ai/provider.py (шов смены провайдера — без
правок фронтенда, ограничение Заказчика). Обмен сохраняется в ai_messages
(role user + assistant) — журнал подхватывается при повторном входе
(FR-19.5).

GET /api/ai/chat/history — история СВОЕЙ учетки за последние 14 дней
(role/text/created_at для рендера пузырей). Retention — серверная
механика (FR-19.5, NFR): DELETE записей старше 14 дней выполняется в ОДНОЙ
BEGIN IMMEDIATE транзакции с SELECT истории (DELETE до SELECT —
рекомендация arch-review 001, ответ ОВ-2: параллельные чтения не видят
различающиеся срезы; single-worker-инвариант ADR-001/002 сериализует
записи). Клиентской глубине не доверять — окно считается на сервере по
created_at (SQLite datetime('now'), UTC), не по параметрам запроса.

Auth — require_session ученика (guards.require_role, канон кабинетных
эндпоинтов): 401 {ok:false} без валидной сессии, 403 при чужой роли.
Изоляция: все выборки/вставки строго по user_id сессии, только
параметризованные ?-запросы (NFR-2).

Ошибки — HTTP-кодами, тексты человеческим языком, без кодов/стеков
(FR-19.3): 422 пустое сообщение, 503 провайдер не ответил (ошибка/таймаут
≤30 с). Логов в модуле нет — тексты сообщений, служебные argv и детали
провайдера в логи не попадают (NFR-3); ProviderError наружу не раскрывается.
"""

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import backend.ai.provider as provider
import backend.core.db as db
from backend.core.guards import require_role

router = APIRouter()

# Глубина истории (FR-19.5: последние 14 дней; решение Заказчика
# «последние две недели он помнит»). Окно считается сервером по created_at.
_RETENTION_DAYS = 14


def _retention_modifier() -> str:
    """Модификатор SQLite-даты для окна retention: '-14 days' при
    _RETENTION_DAYS = 14. Значение идет ?-параметром (MIN-1 CR-19.2:
    никакого f-string SQL, даже с константой)."""
    return f"-{_RETENTION_DAYS} days"

# Контекст диалога, отдаваемый провайдеру (provider._CONTEXT_MESSAGE_LIMIT
# берет свои последние; здесь — срез того же окна 14 дней).
_CONTEXT_WINDOW_ROWS = 50

# Человеческие тексты ошибок (FR-19.3: без кодов и механизма).
_EMPTY_MESSAGE = "Сообщение: поле обязательно"
_PROVIDER_DOWN = (
    "Ассистент сейчас не отвечает. Попробуйте написать еще раз чуть позже."
)


class ChatRequest(BaseModel):
    # Хендлерная валидация как §10.1: дефолт вместо required.
    message: str = ""


def _unauthorized() -> JSONResponse:
    """Тело 401 — {ok:false} (симметрично guards._unauthorized)."""
    return JSONResponse(status_code=401, content={"ok": False})


def _contract_422(message: str) -> JSONResponse:
    """Формат Спринта 0: 422 {ok:false, error:"<поле-ру>: …"}."""
    return JSONResponse(status_code=422, content={"ok": False, "error": message})


def _recent_messages(conn: db, user_id: int, limit: int) -> list[dict]:
    """Последние сообщения СВОЕЙ учетки в окне retention (для контекста
    провайдера): параметризованный SELECT по user_id, хронологический
    порядок (created_at ASC, id ASC — порядок секунд разрешается id)."""
    rows = conn.execute(
        "SELECT role, text FROM ai_messages"
        " WHERE user_id = ?"
        " AND created_at >= datetime('now', ?)"
        " ORDER BY created_at DESC, id DESC LIMIT ?",
        (user_id, _retention_modifier(), limit),
    ).fetchall()
    return [dict(row) for row in reversed(rows)]


@router.post("/api/ai/chat")
def ai_chat(
    data: ChatRequest,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Отправка сообщения ассистенту (FR-19.3): {message} → {reply}."""
    user_id, denied = require_role(x_session_token, "student")
    if denied is not None:
        return denied

    text = data.message.strip()
    if not text:
        return _contract_422(_EMPTY_MESSAGE)

    # Контекст — история своей учетки в окне 14 дней + новое сообщение.
    conn = db.get_conn()
    try:
        history = _recent_messages(conn, user_id, _CONTEXT_WINDOW_ROWS)
    finally:
        conn.close()

    try:
        reply = provider.generate_reply(
            history + [{"role": "user", "text": text}]
        )
    except provider.ProviderError:
        # Ошибка/таймаут провайдера: человеческий текст, ничего не
        # сохраняем (история — только состоявшиеся обмены).
        return JSONResponse(
            status_code=503, content={"ok": False, "error": _PROVIDER_DOWN}
        )

    conn = db.get_conn()
    try:
        conn.execute(
            "INSERT INTO ai_messages (user_id, role, text)"
            " VALUES (?, 'user', ?)",
            (user_id, text),
        )
        conn.execute(
            "INSERT INTO ai_messages (user_id, role, text)"
            " VALUES (?, 'assistant', ?)",
            (user_id, reply),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "reply": reply}


@router.get("/api/ai/chat/history")
def ai_chat_history(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """История своей учетки за 14 дней (FR-19.5) + retention: DELETE
    старше 14 дней в одной BEGIN IMMEDIATE транзакции с SELECT
    (review-001 ОВ-2: DELETE до SELECT)."""
    user_id, denied = require_role(x_session_token, "student")
    if denied is not None:
        return denied

    conn = db.get_conn()
    try:
        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        try:
            # Retention (серверная механика, NFR): старше окна — удаляются
            # физически, у всех пользователей (журнал не секретен для
            # механики чистки; строки чужих user_id в ответ не попадают —
            # SELECT строго по user_id сессии).
            conn.execute(
                "DELETE FROM ai_messages"
                " WHERE created_at < datetime('now', ?)",
                (_retention_modifier(),),
            )
            rows = conn.execute(
                "SELECT role, text, created_at FROM ai_messages"
                " WHERE user_id = ?"
                " AND created_at >= datetime('now', ?)"
                " ORDER BY created_at ASC, id ASC",
                (user_id, _retention_modifier()),
            ).fetchall()
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()
    return {"ok": True, "messages": [dict(row) for row in rows]}
