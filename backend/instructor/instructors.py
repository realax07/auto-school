"""POST /api/instructors/apply (sdd.md §15.1, задача 1.1, MAJ-1; Спринт 3 —
расширение до multipart с файлом ВУ, домен instructor-documents, FR-23).

Публичный эндпоинт заявки инструктора. Хендлерная валидация как
register.py (MAJ-1): поля модели с дефолтами `str = ""`, обязательность
и порядок проверок — в обработчике; первая ошибка в контрактном формате
`422 {"ok": false, "error": "<поле-ру>: <причина>"}`.

Спринт 3 (add-instructor-student-loop, задача 1.1):
- тело принимается и как JSON (обратная совместимость старых клиентов —
  все тесты Спринтов 1–2), и как multipart/form-data;
- multipart-поле license_photo (необязательно, задачей 3.3 фиксируется
  обязательность по макету): проверка содержимого JPEG/PNG ≤5 МБ по
  magic bytes ДО записи (uploads.sniff_image, ОВ-5, NFR-6) → иначе 422,
  заявка НЕ создается; успех — сохранение в data/uploads/license/ и
  license_photo_path в заявке (NFR-1);
- experience_years — стаж числом ≥ 0 (arch-review итерация 2, MAJ-3),
  иначе 422; пусто → NULL.

Успех: bcrypt cost 12 → INSERT instructor_applications (status='waiting');
IntegrityError от UNIQUE instructor_applications.email — вторая линия
защиты гонки параллельных сабмитов → та же контрактная 422
«Email: уже зарегистрирован» (механика register.py:104).

Спринт 9 (add-personal-data-policy, задача 3.1): при успехе INSERT
фиксирует consent_at (момент сабмита, UTC сервера, формат created_at
'YYYY-MM-DD HH:MM:SS') и consent_policy_version (policy-version артефакта
НА МОМЕНТ САБМИТА — хелпер backend.policy.current_policy_version,
клиентской версии не доверять, FR-79); артефакт недоступен в момент
сабмита → 500 {ok:false}, заявка НЕ создается (design.md «Обработка
ошибок»). Проверки и multipart-нормализация consent — без изменений.

Спринт 9 (add-application-status-polling, задача 1.1):
- при создании заявки генерируются и сохраняются ТОКЕНЫ ЗАЯВКИ
  (design.md «Решение СА»): poll_token — многоразовый неперебираемый
  идентификатор опроса статуса (только чтение, не потребляется) и
  exchange_token — одноразовый токен обмена на сессию (потребляется
  эндпоинтом обмена, задача 2.1); оба — secrets.token_urlsafe(32),
  256 бит энтропии (неперебираемость NFR-28), тот же генератор, что у
  сессий Спринта 1. Успешный ответ РАСШИРЕН: {ok, poll_token,
  exchange_token} — обратно-совместимо (NFR-27: старые потребители
  игнорируют новые поля); при 422 заявка не создается и токены НЕ
  выдаются;
- IntegrityError РАЗВЕДЕН по веткам (MIN-2, arch-review-002): гонка
  дубля email (UNIQUE instructor_applications.email, Спринт 2) →
  контрактная 422 БЕЗ регенерации токенов; коллизия poll_token /
  exchange_token (частичные UNIQUE-индексы, uq_instructor_applications_
  poll_token / uq_instructor_applications_exchange_token) → регенерация
  токена и повторная вставка БЕЗ 422. Смешение веток недопустимо:
  иначе гонка email уходит в цикл регенерации, а коллизия токена —
  в ложную 422. Токены в логи не пишутся (NF
"""
import datetime
import json
import secrets
import sqlite3
from typing import Any

import bcrypt
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

import backend.core.db as db
import backend.policy.policy as policy
import backend.core.uploads as uploads

router = APIRouter()

_BCRYPT_ROUNDS = 12

# Спринт 9 (задача 1.1, design.md «Модель данных»): случайность/длина
# токенов — secrets.token_urlsafe(32), 256 бит энтропии (NFR-28).
_TOKEN_BYTES = 32


def _new_token() -> str:
    """Неперебираемый токен заявки (poll/exchange): token_urlsafe(32)."""
    return secrets.token_urlsafe(_TOKEN_BYTES)


# MIN-2 (arch-review-002): ветки IntegrityError разведены по сообщению/
# имени индекса. SQLite для нарушения колоночного UNIQUE называет
# таблицу и колонку («UNIQUE constraint failed:
# instructor_applications.email»), для частичного UNIQUE-индекса — ИМЯ
# ИНДЕКСА («UNIQUE constraint failed: index
# 'uq_instructor_applications_poll_token'»). В обоих сообщениях фигурирует
# имя колонки токена → маркер ветки регенерации; всё остальное (прежде
# всего email) — ветка контрактной 422 без регенерации.
_TOKEN_COLLISION_MARKERS = ("poll_token", "exchange_token")


def _integrity_kind(message: str) -> str:
    """Классификация IntegrityError (MIN-2): 'token' — коллизия частичного
    UNIQUE токена (регенерация), 'email' — всё остальное (гонка дубля
    email → 422 без регенерации)."""
    lowered = message.lower()
    if any(marker in lowered for marker in _TOKEN_COLLISION_MARKERS):
        return "token"
    return "email"


class InstructorApplyRequest(BaseModel):
    # MAJ-1: дефолты вместо Pydantic-required — валидация в хендлере.
    # ФИО анкеты — одним полем (макет); разбор на surname/name/patronymic
    # — в хендлере (users требует три). Файл ВУ в JSON-контракте отсутствует
    # (multipart-поле license_photo разбирается в хендлере).
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
    experience_years: int | None = None
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


def _policy_unavailable_500() -> JSONResponse:
    """Контрактная 500 при недоступном артефакте в момент сабмита
    (design.md «Обработка ошибок»): без деталей артефакта (NFR-10)."""
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": "Сервис: политика персональных данных временно недоступна",
        },
    )


def _utc_now() -> str:
    """Момент сабмита по часам сервера, UTC; формат created_at
    ('YYYY-MM-DD HH:MM:SS', SQLite datetime('now')-совместимый —
    design.md «Модель данных»)."""
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def _validate_experience_years(value: int | None) -> str | None:
    """Стаж числом ≥ 0 (arch-review итерация 2, MAJ-3); None — поле пусто."""
    if value is None:
        return None
    if value < 0:
        return "Стаж: укажите целое число лет не меньше 0"
    return None


async def _parse_request(
    request: Request,
) -> tuple[InstructorApplyRequest | None, bytes, str | None]:
    """Разбор тела: JSON (как Спринты 1–2) или multipart/form-data.

    Возвращает (data, file_bytes, error): file_bytes — содержимое поля
    license_photo (b'' — файла нет). Ошибка разбора тела → контрактная 422.
    """
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        fields: dict[str, Any] = {}
        file_bytes = b""
        for key, value in form.multi_items():
            if isinstance(value, str):
                fields[key] = value
            else:
                # UploadFile (license_photo): содержимое читается целиком —
                # валидация по содержимому, не по Content-Type клиента.
                file_bytes = await value.read()
        normalized: dict[str, Any] = dict(fields)
        if "consent" in normalized:
            normalized["consent"] = str(normalized["consent"]).strip().lower() in (
                "true",
                "1",
                "on",
                "да",
            )
        if normalized.get("experience_years") in ("", None):
            normalized.pop("experience_years", None)
        try:
            return InstructorApplyRequest(**normalized), file_bytes, None
        except ValidationError:
            return None, b"", "Тело запроса: неверный формат полей анкеты"

    body = await request.body()
    if not body:
        return InstructorApplyRequest(), b"", None
    try:
        parsed = json.loads(body)
        if not isinstance(parsed, dict):
            raise ValueError("not an object")
        return InstructorApplyRequest(**parsed), b"", None
    except (ValidationError, ValueError):
        return None, b"", "Тело запроса: неверный формат"


@router.post("/api/instructors/apply")
async def instructor_apply(request: Request):
    data, license_bytes, parse_error = await _parse_request(request)
    if parse_error is not None or data is None:
        return _contract_422(parse_error or "Тело запроса: неверный формат")

    error = _validate(data)
    if error is None:
        error = _validate_experience_years(data.experience_years)

    # Валидация файла ВУ ДО записи на диск и ДО создания заявки (design.md:
    # «заявка не создается», NFR-6, ОВ-5).
    license_ext: str | None = None
    if error is None and license_bytes:
        license_ext, file_error = uploads.sniff_image(license_bytes)
        if file_error is not None:
            error = file_error

    policy_unavailable = False
    if error is None:
        # Спринт 9 (задача 1.1): токены заявки. Значения не None на
        # успешном пути — он проходит через INSERT, где оба токена
        # сгенерированы и сохранены в заявке; при 422 ниже остаются None
        # и в ответ не попадают (токены не выдаются).
        poll_token: str | None = None
        exchange_token: str | None = None
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
                    # Спринт 9 (задача 3.1): версия артефакта НА МОМЕНТ
                    # САБМИТА — после всех проверок (порядок sdd §15.1 не
                    # меняется), ДО INSERT; артефакт недоступен → 500,
                    # заявка НЕ создается (FR-79, design.md «Обработка
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
                        if data.surname.strip() and data.name.strip():
                            surname, name, patronymic = (data.surname.strip(),
                                                         data.name.strip(),
                                                         data.patronymic.strip())
                        else:
                            surname, name, patronymic = _split_fio(data.fio.strip())
                        consent_at = _utc_now()
                        # Спринт 9 (add-application-status-polling, задача 1.1):
                        # токены выдаются ОДИН РАЗ — при создании заявки; той же
                        # транзакцией (design.md «Модель данных»).
                        poll_token = _new_token()
                        exchange_token = _new_token()
                        while True:
                            try:
                                cur = conn.execute(
                                    "INSERT INTO instructor_applications"
                                    " (surname, name, patronymic, email, phone,"
                                    " address, work_format, plate, license_number,"
                                    " license_date, license_category, experience,"
                                    " experience_years, password_hash, consent_at,"
                                    " consent_policy_version, poll_token,"
                                    " exchange_token, status)"
                                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,"
                                    " ?, ?, ?, ?, ?, ?, 'waiting')",
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
                                        data.experience_years,
                                        password_hash,
                                        consent_at,
                                        policy_version,
                                        poll_token,
                                        exchange_token,
                                    ),
                                )
                                break
                            except sqlite3.IntegrityError as exc:
                                # MIN-2: коллизия частичного UNIQUE токена →
                                # регенерация и повторная попытка БЕЗ 422
                                # (вероятность коллизии 256-битного токена
                                # пренебрежима); гонка дубля email → проброс
                                # в обработчик ниже → 422 БЕЗ регенерации
                                # (смешение веток недопустимо).
                                if _integrity_kind(str(exc)) != "token":
                                    raise
                                poll_token = _new_token()
                                exchange_token = _new_token()
                        application_id = cur.lastrowid
                        if license_ext is not None:
                            # Имя генерирует сервер, каталог вне frontend/
                            # (NFR-1): data/uploads/license/<uuid>.<ext>
                            path = uploads.save_image(
                                "license", license_bytes, license_ext
                            )
                            conn.execute(
                                "UPDATE instructor_applications SET"
                                " license_photo_path = ? WHERE id = ?",
                                (path, application_id),
                            )
                        conn.commit()
            # Гонка параллельных сабмитов одного email (MAJ-1): оба проходят
            # SELECT до чужого INSERT, но UNIQUE допускает ровно одну заявку —
            # IntegrityError → та же контрактная 422 (register.py:104).
        except sqlite3.IntegrityError:
            error = "Email: уже зарегистрирован"
        finally:
            conn.close()

    if policy_unavailable:
        return _policy_unavailable_500()
    if error is not None:
        return _contract_422(error)
    # Спринт 9 (задача 1.1): расширение успешного ответа токенами заявки —
    # обратно-совместимо (NFR-27); при 422 (выше) токены не выдаются.
    return {"ok": True, "poll_token": poll_token, "exchange_token": exchange_token}
