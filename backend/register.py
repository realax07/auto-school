"""POST /api/register (sdd.md §3.1, MAJ-1).

Хендлерная валидация: поля модели имеют дефолты `str = ""`, обязательность
и порядок проверок — в обработчике; возвращается первая ошибка в контрактном
формате `422 {"ok": false, "error": "<поле-ру>: <причина>"}`.

Спринт 9 (add-personal-data-policy, задача 4.1): новое обязательное поле
consent (bool, дефолт False — механика MAJ-1, валидация в хендлере);
проверка 1a — после обязательных полей, до проверки email (механика
instructors.py, MIN-2): consent is not True → 422 «Согласие: поле
обязательно» (FR-78). При успехе INSERT users фиксирует consent_at
(момент сабмита, UTC сервера, формат created_at 'YYYY-MM-DD HH:MM:SS') и
consent_policy_version (policy-version артефакта НА МОМЕНТ САБМИТА —
хелпер backend.policy.current_policy_version, клиентской версии не
доверять, FR-79); артефакт недоступен → 500 {ok:false}, пользователь
НЕ создается. Ответ {ok:true, token} — без изменений.
"""
import datetime

import bcrypt
import sqlite3
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import backend.db as db
import backend.policy as policy

router = APIRouter()

_BCRYPT_ROUNDS = 12

# Спринт 9 (задача 4.1): контрактная ошибка при недоступном артефакте
# в момент сабмита (design.md «Обработка ошибок»), без деталей (NFR-10).
_POLICY_UNAVAILABLE_MESSAGE = (
    "Сервис: политика персональных данных временно недоступна"
)


class RegisterRequest(BaseModel):
    # MAJ-1: дефолты вместо Pydantic-required — валидация в хендлере
    surname: str = ""
    name: str = ""
    patronymic: str = ""
    email: str = ""
    phone: str = ""
    password: str = ""
    password_confirm: str = ""
    # Спринт 9 (задача 4.1, FR-78): согласие обязательно; дефолт False —
    # старые клиенты без consent получают контрактный 422 (1a).
    consent: bool = False


def _validate(data: RegisterRequest) -> str | None:
    """Фиксированный порядок проверок (sdd §3.1); возвращает первую ошибку."""
    fields = [
        ("surname", "Фамилия"),
        ("name", "Имя"),
        ("patronymic", "Отчество"),
        ("email", "Email"),
        ("phone", "Телефон"),
        ("password", "Пароль"),
        ("password_confirm", "Подтверждение пароля"),
    ]
    for attr, label in fields:
        if not getattr(data, attr).strip():
            return f"{label}: поле обязательно"

    # 1a) согласие на обработку персональных данных (Спринт 9, задача 4.1,
    # FR-78): после обязательных полей, до проверки email — механика
    # instructors.py (MIN-2, Спринт 3).
    if data.consent is not True:
        return "Согласие: поле обязательно"

    # формат email: «@» и точка в домене
    local, _, domain = data.email.partition("@")
    if not local or not domain or "." not in domain:
        return "Email: неверный формат"
    domain_name, _, tld = domain.rpartition(".")
    if not domain_name or not tld:
        return "Email: неверный формат"

    # телефон: не менее 10 цифр
    digits = sum(ch.isdigit() for ch in data.phone)
    if digits < 10:
        return "Телефон: укажите не менее 10 цифр"

    # пароль ≥ 8 символов
    if len(data.password) < 8:
        return "Пароль: не менее 8 символов"

    # совпадение подтверждения
    if data.password != data.password_confirm:
        return "Подтверждение пароля: пароли не совпадают"

    return None


def _utc_now() -> str:
    """Момент сабмита по часам сервера, UTC; формат created_at
    ('YYYY-MM-DD HH:MM:SS', SQLite datetime('now')-совместимый —
    design.md «Модель данных»)."""
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


@router.post("/api/register")
def register(data: RegisterRequest):
    error = _validate(data)
    user_id = None
    policy_unavailable = False
    if error is None:
        # уникальность email — последняя проверка (SELECT), вторая линия — UNIQUE в БД
        conn = db.get_conn()
        try:
            exists = conn.execute(
                "SELECT 1 FROM users WHERE email = ?", (data.email,)
            ).fetchone()
            if exists:
                error = "Email: уже зарегистрирован"
            else:
                # Спринт 9 (задача 4.1): версия артефакта НА МОМЕНТ САБМИТА —
                # после проверок, ДО INSERT; артефакт недоступен → 500,
                # пользователь НЕ создается (FR-79, design.md «Обработка
                # ошибок»).
                try:
                    policy_version = policy.current_policy_version()
                except policy.PolicyError:
                    policy_unavailable = True
                else:
                    password_hash = bcrypt.hashpw(
                        data.password.encode("utf-8"),
                        bcrypt.gensalt(rounds=_BCRYPT_ROUNDS),
                    ).decode("utf-8")
                    consent_at = _utc_now()
                    cur = conn.execute(
                        "INSERT INTO users (surname, name, patronymic, email,"
                        " phone, password_hash, consent_at,"
                        " consent_policy_version) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            data.surname,
                            data.name,
                            data.patronymic,
                            data.email,
                            data.phone,
                            password_hash,
                            consent_at,
                            policy_version,
                        ),
                    )
                    user_id = cur.lastrowid
                    conn.commit()
            # Гонка дубликатов (пре-существующий, rev-002 #3): параллельная
            # регистрация одного email проходит SELECT и падает на UNIQUE →
            # контрактный 422 вместо HTTP 500.
        except sqlite3.IntegrityError:
            error = "Email: уже зарегистрирован"
        finally:
            conn.close()

    if policy_unavailable:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": _POLICY_UNAVAILABLE_MESSAGE},
        )
    if error is not None:
        return _contract_422(error)
    if user_id is None:  # защита от логической ошибки валидации
        return _contract_422("Регистрация: внутренняя ошибка")

    # Успешная регистрация → сразу авторизованная сессия (решение Заказчика
    # 2026-10-10: редирект в кабинет, минуя отдельный вход). Тот же механизм
    # сессий, что в auth.login (TTL 12ч).
    from backend.auth import _session_issue

    token = _session_issue(user_id)
    return {"ok": True, "token": token}


def _contract_422(message: str):
    return JSONResponse(
        status_code=422, content={"ok": False, "error": message}
    )
