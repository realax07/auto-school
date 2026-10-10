"""POST /api/auth/login, POST /api/auth/logout, GET /api/auth/me,
require_session (sdd.md §10.1–§10.3, задача 1.1).

Токен: secrets.token_urlsafe(32), реестр в памяти
{token: (expires, user_id)}, TTL 12 ч — механизм и ограничения те же, что у
admin-токена Спринта 0 (§3.2), но с привязкой к записи users (источник /me).
Единое сообщение об отказе входа — AUTH_FAIL_MESSAGE, одна строка на все
причины (FR-2). Анти-брутфорс: in-memory учет неудачных попыток по IP, порог
_BF_MAX_FAILURES, нарастающая блокировка 30 с → 15 мин, сброс при успехе
(R-BF1…R-BF4, design.md; рестарт процесса сбрасывает учет — документированное
ограничение). Пароли и токены в логи не пишутся (NFR-3); SQL — только
параметризованный (NFR-2).
"""
import secrets
import time

import bcrypt
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import backend.db as db

router = APIRouter()

AUTH_FAIL_MESSAGE = "Неверный email или пароль"

_TOKEN_TTL_SECONDS = 12 * 60 * 60  # 12 ч
_BCRYPT_ROUNDS = 12

# Анти-брутфорс: значения фиксирует разработчик в пределах задачи
# (порог 3–10 попыток, блокировка 30 с…15 мин) — tasks.md 1.1, R-BF1/R-BF2.
_BF_MAX_FAILURES = 5  # порог неудачных попыток подряд
_BF_BASE_BLOCK_SECONDS = 30  # первая блокировка
_BF_MAX_BLOCK_SECONDS = 15 * 60  # верхняя граница 15 мин
# R-BF3: окно наблюдения без неудачных попыток, сбрасывающее счетчик.
_BF_WINDOW_SECONDS = 15 * 60

# Фиктивный хэш: bcrypt-проверка при отсутствующей записи — выравнивание
# времени ответа (design.md, timing-замечание к потоку 1).
_DUMMY_HASH = bcrypt.hashpw(
    secrets.token_bytes(18), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
)

# реестр выданных сессий: token -> (expires, user_id)
_sessions: dict[str, tuple[float, int]] = {}

# учет анти-брутфорса: ip -> {"fails", "last_fail", "level", "blocked_until"}
_bf: dict[str, dict] = {}


class LoginRequest(BaseModel):
    # хендлерная валидация как §3.1/§10.1: дефолты вместо required
    email: str = ""
    password: str = ""


def _unauthorized() -> JSONResponse:
    """Тело 401 защищенных эндпоинтов (§10.2, §10.3)."""
    return JSONResponse(status_code=401, content={"ok": False})


def _login_fail() -> JSONResponse:
    """Единый отказ входа: одна строка на все причины и блокировку (FR-2,
    R-BF4)."""
    return JSONResponse(
        status_code=401, content={"ok": False, "error": AUTH_FAIL_MESSAGE}
    )


def _contract_422(message: str) -> JSONResponse:
    """Формат Спринта 0: 422 {ok:false, error:"<поле-ру>: …"}."""
    return JSONResponse(status_code=422, content={"ok": False, "error": message})


def _validate(data: LoginRequest) -> str | None:
    """Обязательность полей в порядке §10.1; возвращает первую ошибку."""
    for attr, label in (("email", "Email"), ("password", "Пароль")):
        if not getattr(data, attr).strip():
            return f"{label}: поле обязательно"
    return None


def _session_user_id(token: str | None) -> int | None:
    """user_id сессии или None (нет/неверный/истек). Истекшие записи
    вычищаются лениво при проверке (design.md, поток 4)."""
    entry = _sessions.get(token or "")
    if entry is None:
        return None
    expires, user_id = entry
    if expires < time.time():
        _sessions.pop(token or "", None)
        return None
    return user_id


def require_session(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
) -> int:
    """Зависимость: валидный X-Session-Token (есть, известен, не истек);
    возвращает user_id из реестра сессий (§10.3). Механизм аналогичен
    require_admin (§3.5)."""
    user_id = _session_user_id(x_session_token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return user_id


def _block_seconds(level: int) -> int:
    """Длительность блокировки уровня level (R-BF2): 30 с после первого
    срабатывания, удвоение за каждое следующее, потолок 15 мин."""
    return min(_BF_BASE_BLOCK_SECONDS * 2 ** (level - 1), _BF_MAX_BLOCK_SECONDS)


def _is_blocked(ip: str, now: float) -> bool:
    st = _bf.get(ip)
    if st is None:
        return False
    if now < st["blocked_until"]:
        return True
    if st["blocked_until"]:
        st["blocked_until"] = 0.0  # блокировка истекла — счетчик уже с нуля
    return False


def _record_failure(ip: str, now: float) -> None:
    """Учет неудачной попытки (R-BF1–R-BF3): окно наблюдения, порог,
    нарастающая блокировка."""
    st = _bf.setdefault(
        ip, {"fails": 0, "last_fail": 0.0, "level": 0, "blocked_until": 0.0}
    )
    if now - st["last_fail"] > _BF_WINDOW_SECONDS:
        st["fails"] = 0  # R-BF3: окно без неудач сбрасывает счетчик
    st["fails"] += 1
    st["last_fail"] = now
    if st["fails"] >= _BF_MAX_FAILURES:
        st["level"] += 1
        st["blocked_until"] = now + _block_seconds(st["level"])
        st["fails"] = 0  # после срабатывания счетчик начинается заново


def _reset_failures(ip: str) -> None:
    """Сброс учета после успешного входа (R-BF3), включая эскалацию."""
    st = _bf.get(ip)
    if st is not None:
        st["fails"] = 0
        st["last_fail"] = 0.0
        st["level"] = 0
        st["blocked_until"] = 0.0


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else ""


@router.post("/api/auth/login")
def login(data: LoginRequest, request: Request):
    ip = _client_ip(request)
    now = time.time()

    if _is_blocked(ip, now):
        # R-BF1/R-BF4: отказ без проверки учетных данных, тот же 401/строка
        return _login_fail()

    error = _validate(data)
    if error is not None:
        return _contract_422(error)

    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = ?", (data.email,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        # отсутствующая запись: фиктивная bcrypt-проверка (тайминг) + учет
        bcrypt.checkpw(data.password.encode("utf-8"), _DUMMY_HASH)
        _record_failure(ip, now)
        return _login_fail()

    try:
        password_ok = bcrypt.checkpw(
            data.password.encode("utf-8"),
            row["password_hash"].encode("utf-8"),
        )
    except ValueError:
        password_ok = False
    if not password_ok:
        _record_failure(ip, now)
        return _login_fail()

    _reset_failures(ip)  # R-BF3: сброс счетчика при успехе
    token = secrets.token_urlsafe(32)
    _sessions[token] = (time.time() + _TOKEN_TTL_SECONDS, row["id"])
    return {"ok": True, "token": token}


def _session_issue(user_id: int) -> str:
    """Выдача сессии для только что созданной учетной записи (register.py).
    Тот же реестр и TTL, что у login — единый механизм (sdd §10.1)."""
    token = secrets.token_urlsafe(32)
    _sessions[token] = (time.time() + _TOKEN_TTL_SECONDS, user_id)
    return token


@router.post("/api/auth/logout")
def logout(x_session_token: str | None = Header(default=None, alias="X-Session-Token")):
    """Аннулирование токена (§10.2). Проверка — как require_session, но
    ошибкой возвращается контрактный JSONResponse {ok:false} (HTTPException
    отдавал бы {"detail": ...})."""
    if _session_user_id(x_session_token) is None:
        return _unauthorized()
    _sessions.pop(x_session_token or "", None)
    return {"ok": True}


@router.get("/api/auth/me")
def me(x_session_token: str | None = Header(default=None, alias="X-Session-Token")):
    """Данные записи users по сессии (§10.3): {id, surname, name, patronymic,
    email}."""
    user_id = _session_user_id(x_session_token)
    if user_id is None:
        return _unauthorized()

    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT id, surname, name, patronymic, email FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return _unauthorized()
    return {
        "ok": True,
        "user": {
            "id": row["id"],
            "surname": row["surname"],
            "name": row["name"],
            "patronymic": row["patronymic"],
            "email": row["email"],
        },
    }
