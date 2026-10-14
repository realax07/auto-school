"""POST /api/instructors/apply (sdd.md §15.1, задача 1.1, MAJ-1).

Публичный эндпоинт заявки инструктора. Хендлерная валидация как
register.py (MAJ-1): поля модели с дефолтами `str = ""`, обязательность
и порядок проверок — в обработчике; первая ошибка в контрактном формате
`422 {"ok": false, "error": "<поле-ру>: <причина>"}`.

Успех: bcrypt cost 12 → INSERT instructor_applications (status='waiting');
IntegrityError от UNIQUE instructor_applications.email — вторая линия
защиты гонки параллельных сабмитов → та же контрактная 422
«Email: уже зарегистрирован» (механика register.py:104).
"""
import datetime
import sqlite3

import bcrypt
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import backend.db as db

router = APIRouter()

_BCRYPT_ROUNDS = 12


class InstructorApplyRequest(BaseModel):
    # MAJ-1: дефолты вместо Pydantic-required — валидация в хендлере.
    # ФИО анкеты — одним полем (макет); разбор на surname/name/patronymic
    # — в хендлере (users требует три). Файл ВУ в контракте отсутствует.
    # ФИО: три отдельных поля (правка Заказчика 2026-10-14) либо fio одной
    # строкой (обратная совместимость старых клиентов/тестов)
    surname: str = ""
    name: str = ""
    patronymic: str = ""
    fio: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    work_format: str = ""
    plate: str = ""
    license_number: str = ""
    license_date: str = ""
    license_category: str = ""
    experience: str = ""
    password: str = ""
    password_confirm: str = ""
    consent: bool = False


def _split_fio(fio: str) -> tuple[str, str, str]:
    """Разбор ФИО одного поля на фамилию/имя/отчество (деталь реализации
    1.1): два первых слова — фамилия/имя (поддержка двойных фамилий через
    дефис), остальное — отчество. Недостающие части — пустая строка
    (пустое поле отсечено обязательностью раньше)."""
    parts = fio.split()
    surname = parts[0] if parts else ""
    name = parts[1] if len(parts) > 1 else ""
    patronymic = " ".join(parts[2:]) if len(parts) > 2 else ""
    return surname, name, patronymic


def _validate(data: InstructorApplyRequest) -> str | None:
    """Фиксированный порядок проверок (sdd §15.1); возвращает первую ошибку."""
    # 1) обязательные поля (звездочка макета + пароль + подтверждение)
    required = [
        ("surname", "Фамилия"),
        ("name", "Имя"),
        ("patronymic", "Отчество"),
        ("phone", "Телефон"),
        ("email", "Email"),
        ("address", "Адрес"),
        ("license_number", "Номер ВУ"),
        ("license_category", "Категория прав"),
        ("password", "Пароль"),
        ("password_confirm", "Подтверждение пароля"),
        ("work_format", "Формат работы"),
    ]
    for attr, label in required:
        if not getattr(data, attr).strip():
            return f"{label}: поле обязательно"

    # 1a) согласие на обработку персональных данных (MIN-2)
    if data.consent is not True:
        return "Согласие: поле обязательно"

    # 2) формат email (как register.py / §3.1)
    local, _, domain = data.email.partition("@")
    if not local or not domain or "." not in domain:
        return "Email: неверный формат"
    domain_name, _, tld = domain.rpartition(".")
    if not domain_name or not tld:
        return "Email: неверный формат"

    # 3) телефон: не менее 10 цифр
    digits = sum(ch.isdigit() for ch in data.phone)
    if digits < 10:
        return "Телефон: укажите не менее 10 цифр"

    # 4) пароль ≥ 8 символов
    if len(data.password) < 8:
        return "Пароль: не менее 8 символов"

    # 5) совпадение подтверждения
    if data.password != data.password_confirm:
        return "Подтверждение пароля: пароли не совпадают"

    # 6) госномер обязателен при work_format='own'
    if data.work_format == "own" and not data.plate.strip():
        return "Госномер: поле обязательно"

    # 7) license_date при заполнении — валидная дата YYYY-MM-DD
    if data.license_date.strip():
        try:
            datetime.date.fromisoformat(data.license_date.strip())
        except ValueError:
            return "Дата выдачи ВУ: неверный формат"

    return None


def _contract_422(message: str) -> JSONResponse:
    return JSONResponse(status_code=422, content={"ok": False, "error": message})


@router.post("/api/instructors/apply")
def instructor_apply(data: InstructorApplyRequest):
    error = _validate(data)
    if error is None:
        # 8)–9) уникальность email: users и заявки (единое сообщение, FR-16)
        conn = db.get_conn()
        try:
            exists = conn.execute(
                "SELECT 1 FROM users WHERE email = ?", (data.email,)
            ).fetchone()
            if exists:
                error = "Email: уже зарегистрирован"
            else:
                exists = conn.execute(
                    "SELECT 1 FROM instructor_applications WHERE email = ?",
                    (data.email,),
                ).fetchone()
                if exists:
                    error = "Email: уже зарегистрирован"
                else:
                    password_hash = bcrypt.hashpw(
                        data.password.encode("utf-8"),
                        bcrypt.gensalt(rounds=_BCRYPT_ROUNDS),
                    ).decode("utf-8")
                    if data.surname.strip() and data.name.strip():
                        surname, name, patronymic = (data.surname.strip(),
                                                     data.name.strip(),
                                                     data.patronymic.strip())
                    else:
                        surname, name, patronymic = _split_fio(data.fio.strip())
                    conn.execute(
                        "INSERT INTO instructor_applications (surname, name,"
                        " patronymic, email, phone, address, work_format, plate,"
                        " license_number, license_date, license_category,"
                        " experience, password_hash, status)"
                        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'waiting')",
                        (
                            surname,
                            name,
                            patronymic,
                            data.email,
                            data.phone,
                            data.address,
                            data.work_format,
                            data.plate,
                            data.license_number,
                            data.license_date,
                            data.license_category,
                            data.experience,
                            password_hash,
                        ),
                    )
                    conn.commit()
            # Гонка параллельных сабмитов одного email (MAJ-1): оба проходят
            # SELECT до чужого INSERT, но UNIQUE допускает ровно одну заявку —
            # IntegrityError → та же контрактная 422 (register.py:104).
        except sqlite3.IntegrityError:
            error = "Email: уже зарегистрирован"
        finally:
            conn.close()

    if error is not None:
        return _contract_422(error)
    return {"ok": True}
