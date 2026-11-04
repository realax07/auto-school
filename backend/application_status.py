"""Спринт 9 (add-application-status-polling, задача 2.1): домен статуса
заявки — GET /api/instructors/application-status и POST
/api/instructors/application-exchange. Контракты — design.md пакета
(«Решение СА», «Эндпоинты», «Порядок обмена», arch-review-002 MAJ-1).

Правило префиксов design.md: оба эндпоинта под /api/instructors/* —
до-сессионный контур заявителя (сессии у него еще нет).

- poll_token (заголовок X-Poll-Token) — многоразовый неперебираемый
  идентификатор опроса; эндпоинт ТОЛЬКО ЧТЕНИЯ (NFR-28): одиночный
  параметризованный SELECT по частичному UNIQUE-индексу, без записи и
  побочных эффектов; внутренний 'deny' маппится в 'rejected', reason =
  review_comment ТОЛЬКО при rejected (иначе null). Токен НЕ потребляется
  чтениями и действует до и после решения — чтение не дает прав.
- exchange_token (тело POST) — одноразовый: обмен на сессию ТОЛЬКО при
  status='approved' (guard — иначе 409, ПЕРЕХОДНАЯ ветка FR-81); строка
  users обязана существовать (создана approve — instructor_admin.py,
  MIN-3), вырожденное «approved без users» → 409, токен сохранен.
  Потребление — УСЛОВНЫЙ UPDATE exchange_token = NULL
  WHERE exchange_token = ? + проверка rowcount (паттерн MIN-1
  Спринта 8: sync-эндпоинты в threadpool, интерливинг SELECT и UPDATE
  не свободен): rowcount=1 — токен захвачен ЭТИМ запросом (ровно один
  200 при параллельном обмене — SQLite сериализует запись);
  rowcount=0 — уже потреблен (в т.ч. параллельным обменом) →
  404-неразличение, сессия НЕ выдается. Сессия — публичная фабрика
  auth.issue_session (единый реестр _sessions, TTL 12 ч, механизм
  логина без изменений; design.md «Порядок обмена» п.5); commit
  фиксирует потребление и выдачу одной транзакцией БД, отказ
  транзакции → rollback — повтор обмена возможен (не возвращенная
  сессия in-memory безвредна: эквивалент «лишнего логина», истечет
  по TTL). Ответ — форма ответа логина: {ok, token, route:'cabinet'}.
- Чужой/несуществующий/уже потребленный токен — 404-неразличение
  (NFR-28, наследование NFR-7): ОДИНАКОВЫЙ ответ для всех причин —
  существование чужих заявок не раскрывается; 404 при approved-потребленном
  exchange_token — терминальное состояние экрана (arch-review-002 MAJ-1).
- Пустые заголовок/токен → 422 (контракт формата запроса, формат
  Спринтов 1–8: {ok:false, error:"<по-русски>"}).
- Токены в URL не пишутся (заголовок/тело — access-логи path+query
  чисты) и в логи не попадают (NFR-3/NFR-10); SQL только
  параметризованный (NFR-10).
"""
from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import backend.auth as auth
import backend.db as db

router = APIRouter()

# 404-неразличение (NFR-28): одно тело на все причины — «чужой»,
# «несуществующий», «уже потреблен» — неотличимы (TC-S9BE-005).
_NOT_FOUND = JSONResponse(
    status_code=404, content={"ok": False, "error": "Заявка не найдена"}
)


def _contract_422(message: str) -> JSONResponse:
    """Формат Спринтов 1–8: 422 {ok:false, error:"<поле-ру>: …"}."""
    return JSONResponse(status_code=422, content={"ok": False, "error": message})


def _conflict(message: str) -> JSONResponse:
    """409 — ПЕРЕХОДНАЯ ветка обмена (FR-81): токен НЕ потреблен, экран
    остается в waiting, повтор обмена возможен на следующем тике."""
    return JSONResponse(status_code=409, content={"ok": False, "error": message})


@router.get("/api/instructors/application-status")
def application_status(
    x_poll_token: str | None = Header(default=None, alias="X-Poll-Token"),
):
    """Статус заявки по неперебираемому poll_token (только чтение,
    design.md «Эндпоинты»): {ok, status:'waiting'|'approved'|'rejected',
    reason:string|null}."""
    token = (x_poll_token or "").strip()
    if not token:
        return _contract_422("Токен опроса: поле обязательно")

    # NFR-28: одиночный параметризованный SELECT по частичному
    # UNIQUE-индексу uq_instructor_applications_poll_token; БЕЗ записи.
    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT status, review_comment FROM instructor_applications"
            " WHERE poll_token = ?",
            (token,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        # чужой/несуществующий — 404-неразличение (NFR-28)
        return _NOT_FOUND

    # внутренний 'deny' → 'rejected'; reason — ТОЛЬКО при rejected
    if row["status"] == "deny":
        return {"ok": True, "status": "rejected", "reason": row["review_comment"]}
    return {"ok": True, "status": row["status"], "reason": None}


class ExchangeRequest(BaseModel):
    # дефолты вместо required — обязательность в хендлере (механика
    # контурных моделей register.py/auth.py/instructors.py)
    exchange_token: str = ""


@router.post("/api/instructors/application-exchange")
def application_exchange(data: ExchangeRequest):
    """Обмен одноразового exchange_token на сессию (design.md «Порядок
    обмена», MIN-1): {ok, token, route:'cabinet'} — форма ответа логина."""
    token = (data.exchange_token or "").strip()
    if not token:
        return _contract_422("Токен обмена: поле обязательно")

    conn = db.get_conn()
    try:
        # п.1: SELECT заявки по exchange_token (параметризованный); нет/
        # потреблен (NULL) → 404-неразличение
        row = conn.execute(
            "SELECT email, status FROM instructor_applications"
            " WHERE exchange_token = ?",
            (token,),
        ).fetchone()
        if row is None:
            return _NOT_FOUND

        # п.2: guard status='approved' — иначе 409 (симметрично
        # guard'ам модерации), токен НЕ потреблен (переходная ветка)
        if row["status"] != "approved":
            return _conflict("Обмен недоступен: заявка не одобрена")

        # п.3: строка users СУЩЕСТВУЕТ (создана approve одной
        # транзакцией, MIN-3); вырожденное «approved без users» (вне
        # контракта модерации) → 409, экран остается в waiting
        user_row = conn.execute(
            "SELECT id FROM users WHERE email = ?", (row["email"],)
        ).fetchone()
        if user_row is None:
            return _conflict("Обмен временно недоступен")

        # п.4: УСЛОВНЫЙ UPDATE + rowcount — атомарное потребление
        # (MIN-1): rowcount=1 — токен захвачен ЭТИМ запросом (ровно один
        # 200 при параллельном обмене); rowcount=0 — уже потреблен →
        # 404-неразличение, сессия НЕ выдается
        cur = conn.execute(
            "UPDATE instructor_applications SET exchange_token = NULL"
            " WHERE exchange_token = ?",
            (token,),
        )
        if cur.rowcount != 1:
            conn.rollback()
            return _NOT_FOUND

        # п.5: сессия фабрикой auth.py (единый реестр, TTL 12 ч,
        # роль instructor по строке users) — commit фиксирует потребление
        # и выдачу одной транзакцией БД; отказ → rollback (сессия
        # in-memory безвредна, повтор обмена возможен — design.md п.5)
        try:
            session_token = auth.issue_session(user_row["id"])
            conn.commit()
        except Exception:
            conn.rollback()
            return _conflict("Обмен временно недоступен")
    finally:
        conn.close()

    return {"ok": True, "token": session_token, "route": "cabinet"}
