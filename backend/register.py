"""POST /api/register (sdd.md §3.1, MAJ-1).

Хендлерная валидация: поля модели имеют дефолты `str = ""`, обязательность
и порядок проверок — в обработчике; возвращается первая ошибка в контрактном
формате `422 {"ok": false, "error": "<поле-ру>: <причина>"}`.
"""
import bcrypt
from fastapi import APIRouter
from pydantic import BaseModel

import backend.db as db

router = APIRouter()

_BCRYPT_ROUNDS = 12


class RegisterRequest(BaseModel):
    # MAJ-1: дефолты вместо Pydantic-required — валидация в хендлере
    surname: str = ""
    name: str = ""
    patronymic: str = ""
    email: str = ""
    phone: str = ""
    password: str = ""
    password_confirm: str = ""


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


@router.post("/api/register")
def register(data: RegisterRequest):
    error = _validate(data)
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
                password_hash = bcrypt.hashpw(
                    data.password.encode("utf-8"),
                    bcrypt.gensalt(rounds=_BCRYPT_ROUNDS),
                ).decode("utf-8")
                conn.execute(
                    "INSERT INTO users (surname, name, patronymic, email, phone,"
                    " password_hash) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        data.surname,
                        data.name,
                        data.patronymic,
                        data.email,
                        data.phone,
                        password_hash,
                    ),
                )
                conn.commit()
        finally:
            conn.close()

    if error is not None:
        return _contract_422(error)

    return {"ok": True}


def _contract_422(message: str):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=422, content={"ok": False, "error": message}
    )
