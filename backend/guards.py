"""guards.py — общий ролевой guard новых кабинетных эндпоинтов Спринта 3
(change add-instructor-student-loop; правило префиксов design.md).

Механика как dashboard.py: require_session (X-Session-Token) → SELECT
users по id → проверка роли; 401 {\"ok\": false} при отсутствии/неверном
токене, 403 {\"ok\": false} при валидной сессии с чужой ролью. Вынесено
в helper, т.к. новых кабинетных эндпоинтов — 15+ (существующие модули
auth.py/admin.py не изменяются — задача 7.1).
"""
import sqlite3

from fastapi import Header
from fastapi.responses import JSONResponse

import backend.auth as auth
import backend.db as db


def _unauthorized() -> JSONResponse:
    """Тело 401 — {\"ok\": false} (симметрично auth._unauthorized, §10.3)."""
    return JSONResponse(status_code=401, content={"ok": False})


def _forbidden() -> JSONResponse:
    """Тело 403 — {\"ok\": false} (сессия валидна, роль не та)."""
    return JSONResponse(status_code=403, content={"ok": False})


def _error(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"ok": False, "error": message})


def require_role(
    x_session_token: str | None,
    role: str,
) -> tuple[int | None, JSONResponse | None]:
    """(user_id, None) при валидной сессии с ролью role, иначе (None, ответ).

    Заголовок читается в хендлере (Header(default=None, alias=...)),
    проверка — публичный auth.session_user_id (ленивая чистка истекших).
    """
    user_id = auth.session_user_id(x_session_token)
    if user_id is None:
        return None, _unauthorized()
    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT role FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        # Запись users по сессии отсутствует (вырожденный случай) → 401.
        return None, _unauthorized()
    if row["role"] != role:
        return None, _forbidden()
    return user_id, None


def fetch_user_row(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
    """Запись users по id (`?`-плейсхолдер, NFR-3)."""
    return conn.execute(
        "SELECT id, surname, name, patronymic, email, role, experience_years"
        " FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()


def full_name(row: sqlite3.Row) -> str:
    """Склейка ФИО на сервере (ADR-004, механика Спринтов 1–2)."""
    return " ".join(
        part for part in (row["surname"], row["name"], row["patronymic"]) if part
    )
