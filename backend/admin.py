"""POST /api/admin/login, GET /api/admin/users, GET /api/admin/users/export.csv,
require_admin (sdd.md §3.2–§3.5, задачи 3.1–3.3).

Токен: secrets.token_urlsafe(32), реестр в памяти {token: expires}, TTL 12 ч.
401 тело — {"ok": false}. CSV: UTF-8 с BOM, «;», санитизация MAJ-2,
дата — UTC→локаль (MIN-4), DD.MM.YYYY.
"""
import csv
import io
import secrets
import time
from datetime import datetime, timezone

import bcrypt
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

import backend.config as config
import backend.db as db

router = APIRouter()

_TOKEN_TTL_SECONDS = 12 * 60 * 60  # 12 ч
_CSV_BOM = b"\xef\xbb\xbf"
_DANGEROUS_PREFIXES = ("=", "+", "-", "@")
_ROLE_STUDENT = "Ученик"

# реестр выданных токенов: token -> expires (unix time)
_tokens: dict[str, float] = {}


class AdminLoginRequest(BaseModel):
    login: str = ""
    password: str = ""


def _unauthorized() -> JSONResponse:
    return JSONResponse(status_code=401, content={"ok": False})


@router.post("/api/admin/login")
def admin_login(data: AdminLoginRequest):
    login_ok = data.login == config.admin_user()
    password_ok = False
    if login_ok:
        try:
            password_ok = bcrypt.checkpw(
                data.password.encode("utf-8"),
                config.admin_password_hash().encode("utf-8"),
            )
        except ValueError:
            password_ok = False
    if not (login_ok and password_ok):
        return _unauthorized()

    token = secrets.token_urlsafe(32)
    _tokens[token] = time.time() + _TOKEN_TTL_SECONDS
    return {"ok": True, "token": token}


def require_admin(x_admin_token: str | None = Header(default=None)) -> str:
    """Зависимость: валидный X-Admin-Token (есть, известен, не истек)."""
    token = x_admin_token or ""
    expires = _tokens.get(token)
    if expires is None or expires < time.time():
        raise HTTPException(status_code=401, detail="unauthorized")
    return token


def _fio(row) -> str:
    return f"{row['surname']} {row['name']} {row['patronymic']}"


@router.get("/api/admin/users")
def admin_users(_: str = Header(default=None, alias="X-Admin-Token")):
    try:
        require_admin(x_admin_token=_)
    except HTTPException:
        return _unauthorized()

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT id, surname, name, patronymic, email, phone, created_at"
            " FROM users ORDER BY created_at DESC, id DESC"
        ).fetchall()
    finally:
        conn.close()

    users = [
        {
            "id": row["id"],
            "fio": _fio(row),
            "email": row["email"],
            "phone": row["phone"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    return {"count": len(users), "users": users}


def _sanitize_csv_value(value: str) -> str:
    """MAJ-2: значение из пользовательских полей, начинающееся с =+-@,
    получает префикс ' (формула не исполняется в Excel/LibreOffice)."""
    if value.startswith(_DANGEROUS_PREFIXES):
        return "'" + value
    return value


def _format_local_date(created_at_utc: str) -> str:
    """MIN-4: created_at хранится в UTC (datetime('now')) → локальная зона
    перед форматированием DD.MM.YYYY."""
    parsed = datetime.strptime(created_at_utc, "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    local = parsed.astimezone()
    return local.strftime("%d.%m.%Y")


@router.get("/api/admin/users/export.csv")
def admin_users_export_csv(_: str = Header(default=None, alias="X-Admin-Token")):
    try:
        require_admin(x_admin_token=_)
    except HTTPException:
        return _unauthorized()

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT surname, name, patronymic, email, phone, created_at"
            " FROM users ORDER BY created_at DESC, id DESC"
        ).fetchall()
    finally:
        conn.close()

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", lineterminator="\n")
    writer.writerow(["ФИО", "Email", "Телефон", "Роль", "Дата регистрации"])
    for row in rows:
        writer.writerow(
            [
                _sanitize_csv_value(_fio(row)),
                _sanitize_csv_value(row["email"]),
                _sanitize_csv_value(row["phone"]),
                _ROLE_STUDENT,
                _format_local_date(row["created_at"]),
            ]
        )
    content = _CSV_BOM + buf.getvalue().encode("utf-8")
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="users.csv"'},
    )
