"""instructor_cars.py — «Мои автомобили» инструктора (Спринт 3, задача 2.1;
Спринт 5 add-booking-docs — 5 ракурсов, СТС, комплектность; Спринт 7
add-car-validation-booking — РАСШИРЕНИЕ: статусная модель валидации
(draft/validating/validated), задачи 1.1/1.2/2.1/3.1/4.1).

GET/POST /api/instructor/cars; PATCH/DELETE /api/instructor/cars/{id};
POST /api/instructor/cars/{id}/submit — draft→validating (алиас
send-to-validation из ТЗ ПМ), POST …/{id}/withdraw — validating→draft
(ОВ-3, алиас back-to-draft); не в том статусе → 409, чужое/несуществующее
→ 404;
POST/GET /api/instructor/cars/{id}/photo/{angle} — ракурсы
front/rear/interior/left/right + 'sts' (СТС существующего авто, задача
4.1; GET …/photo/sts — только владелец, эквивалент GET …/sts);
GET /api/instructor/cars/{id}/sts — фото СТС, только владельцу (FR-44);
GET /api/admin/cars/completeness (+алиас GET /api/admin/cars из ТЗ ПМ) —
комплектность всех авто + status, фильтр ?status=validating;
POST /api/admin/cars/{id}/validate — validating→validated (X-Admin-Token;
ОВ-4: ≥3 любых ракурса И СТС, иначе 409 с перечнем недостающего).

УДАЛЕНО (Спринт 7, REMOVED-дельты): legacy POST+GET …/photo (одиночное
фото в photo_path — фото-контракт Спринта 3, корень СТС-симптома 4.1) и
POST /api/admin/cars/{id}/block (контур блокировки Спринта 5 заменен
статусной моделью — design.md); колонки photo_path/blocked объявлены
устаревшими — новыми эндпоинтами не читаются и не пишутся.

Доступ: require_session + role='instructor' (guards.require_role):
401 — нет/неверная сессия, 403 — чужая роль. Чужой/несуществующий
автомобиль → 404 (не раскрываем существование, FR-28). Валидации полей —
422 по полю (FR-26): brand/model/plate непустые, year — число в диапазоне,
transmission IN ('manual','automatic').

Создание (FR-44, Спринт 5): multipart-запрос ОБЯЗАТЕЛЬНО несет файл
`sts_photo` (JPEG/PNG ≤5 МБ по magic bytes до записи) — без файла → 422,
авто НЕ создается. JSON-тело (без файла) — путь совместимости Спринта 3
(авто без СТС; для новых авто фронт шлет multipart). НОВОЕ авто создается
в status='draft' — статус пишется ЯВНО в INSERT (DEFAULT колонки
'validated' служит только миграции существующих строк, ОВ-1).

Фото ракурсов (FR-42, MIN-2 + ОВ-2): JPEG/PNG ≤5 МБ по содержимому →
иначе 422; выдача — владелец ИЛИ ученик принятой пары: гость → 401,
иная роль → 403, чужой/несуществующий/ракурс не загружен → 404, ученик
НЕ из пары → 403. Статусное правило (ОВ-2): draft → ученику пары 404
(неразличение, NFR-4); validating/validated → выдается. angle='sts' —
только владельцу (ученику пары → 403, NFR-7). Замена фото/СТС у авто в
status='validated' ВОЗВРАЩАЕТ его в validating (MAJ-1 review-001,
решение ПМ): контент после замены не соответствует подтвержденному
админом — повторная валидация обязательна (гейт ОВ-4 не обходится
задним числом); у draft/validating загрузка статус не меняет.

Баг 5.2 (FR-42, задача 1.1): список авто выдает клиенту URL
авторизованного фото-эндпоинта (photos{angle}), а не файловый путь
data/uploads/... (статикой не раздается — NFR-1): плитка строит <img> от
эндпоинта, фото переживает перезагрузку и повторный вход (файл на диске).

DELETE (ОВ-3): student_requests.car_id привязанных заявок → NULL, связь
«ученик ↔ инструктор» сохраняется. Файлы-сироты в data/uploads/ —
осознанный техдолг (cleanup вне скоупа).

SQL — только параметризованный (NFR-3); токены/файлы не логируются (NFR-4).
"""
import datetime
import sqlite3
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ValidationError

import backend.auth as auth
import backend.db as db
import backend.uploads as uploads
from backend.admin import require_admin
from backend.guards import _error, _forbidden, _unauthorized, full_name, require_role

router = APIRouter()

_YEAR_MIN = 1950
_YEAR_MAX = datetime.date.today().year + 1

# 422 по первому полю на легаси-JSON пути (M-2 review-001): человекочитаемая
# метка поля вместо traceback ValidationError/TypeError (было 500).
_CAR_FIELD_LABELS = {
    "brand": "Марка",
    "model": "Модель",
    "year": "Год",
    "plate": "Госномер",
    "transmission": "КПП",
}


class CarPayload(BaseModel):
    # Дефолты вместо Pydantic-required — валидация в хендлере (MAJ-1).
    brand: str = ""
    model: str = ""
    year: int = 0
    plate: str = ""
    transmission: str = ""



def _car_payload_from_body(body) -> tuple[CarPayload | None, str]:
    """Разбор JSON-тела create_car (путь совместимости Спринта 3): не-объект
    (список/строка/null) или невалидное значение поля (например
    year:"abc") → (None, 422-ошибка по первому полю), не исключение."""
    if not isinstance(body, dict):
        return None, "Тело: ожидается JSON-объект автомобиля"
    try:
        return CarPayload(**body), ""
    except ValidationError as exc:
        first = exc.errors()[0] if exc.errors() else None
        loc = first.get("loc", ()) if first else ()
        field = str(loc[0]) if loc else ""
        label = _CAR_FIELD_LABELS.get(field, field or "Тело")
        return None, f"{label}: некорректное значение"
    except TypeError:
        return None, "Тело: ожидается JSON-объект автомобиля"


# Спринт 5 (задача 2.1, ОВ-1): фиксированный набор ракурсов; Спринт 7
# (задача 4.1): + 'sts' — СТС существующего авто (angle, не kind).
ANGLES = ("front", "rear", "interior", "left", "right")
UPLOAD_ANGLES = ANGLES + ("sts",)

# Колонка ракурса — только по валидированному angle; SQL статический
# (без конкатенации — NFR-3, grep-контроль).
_ANGLE_UPDATE_SQL = {
    "front": "UPDATE instructor_cars SET photo_front = ? WHERE id = ?",
    "rear": "UPDATE instructor_cars SET photo_rear = ? WHERE id = ?",
    "interior": "UPDATE instructor_cars SET photo_interior = ? WHERE id = ?",
    "left": "UPDATE instructor_cars SET photo_left = ? WHERE id = ?",
    "right": "UPDATE instructor_cars SET photo_right = ? WHERE id = ?",
    # Спринт 7 (4.1): angle='sts' → photo_sts; замена не трогает ракурсы
    # (статус при validated меняет upload-ручка — MAJ-1 review-001).
    "sts": "UPDATE instructor_cars SET photo_sts = ? WHERE id = ?",
}

_ANGLE_COLUMNS = {
    "front": "photo_front",
    "rear": "photo_rear",
    "interior": "photo_interior",
    "left": "photo_left",
    "right": "photo_right",
    "sts": "photo_sts",
}

def _car_counters(row) -> dict:
    """Комплектность для владельца/админа (задача 1.1): загружено ракурсов
    из 5, СТС да/нет — для кнопок submit и чек-листа ОВ-4."""
    angles = sum(
        1 for angle in ANGLES if row[_ANGLE_COLUMNS[angle]] is not None
    )
    return {"angles": angles, "sts": row["photo_sts"] is not None}



def _validate_car(
    data: CarPayload, require_all: bool
) -> tuple[dict[str, str | int], str | None]:
    """Валидация полей автомобиля; возвращает (update-набор, ошибка).
    PATCH — частичное обновление: проверяются только переданные поля."""
    updates: dict[str, str | int] = {}
    if require_all or data.brand != "":
        if not data.brand.strip():
            return {}, "Марка: поле обязательно"
        updates["brand"] = data.brand.strip()
    if require_all or data.model != "":
        if not data.model.strip():
            return {}, "Модель: поле обязательно"
        updates["model"] = data.model.strip()
    if require_all or data.year != 0:
        if data.year < _YEAR_MIN or data.year > _YEAR_MAX:
            return {}, f"Год: число от {_YEAR_MIN} до {_YEAR_MAX}"
        updates["year"] = data.year
    if require_all or data.plate != "":
        if not data.plate.strip():
            return {}, "Госномер: поле обязательно"
        updates["plate"] = data.plate.strip()
    if require_all or data.transmission != "":
        if data.transmission not in ("manual", "automatic"):
            return {}, "КПП: укажите manual или automatic"
        updates["transmission"] = data.transmission
    return updates, None


def _own_car(conn: sqlite3.Connection, car_id: int, instructor_id: int):
    """SELECT СВОЕГО авто (WHERE по id и владельцу); чужой/несуществующий
    → None → 404 (не раскрываем существование). photo_path/blocked —
    устаревшие колонки, новые эндпоинты их не читают (design.md)."""
    return conn.execute(
        "SELECT id, instructor_id, brand, model, year, plate, transmission,"
        " photo_front, photo_rear, photo_interior, photo_left, photo_right,"
        " photo_sts, status, created_at"
        " FROM instructor_cars WHERE id = ? AND instructor_id = ?",
        (car_id, instructor_id),
    ).fetchone()


def _any_car(conn: sqlite3.Connection, car_id: int):
    """SELECT авто по id независимо от владельца (для матрицы доступа
    фото ракурсов: чужой/несуществующий различаются проверками роли)."""
    return conn.execute(
        "SELECT id, instructor_id, brand, model, year, plate, transmission,"
        " photo_front, photo_rear, photo_interior, photo_left, photo_right,"
        " photo_sts, status, created_at"
        " FROM instructor_cars WHERE id = ?",
        (car_id,),
    ).fetchone()


def _require_admin_session(x_admin_token: str | None):
    """X-Admin-Token (механика Спринта 0): валиден → None, иначе ответ 401."""
    try:
        require_admin(x_admin_token=x_admin_token or "")
    except HTTPException:
        return _unauthorized()
    return None


def _serve_image(path: str | None) -> Response | JSONResponse:
    """Выдача файла изображения (Content-Type image/*); путь пуст или
    файл отсутствует на диске → 404 (не битая картинка — задача 1.1)."""
    if not path:
        return _error(404, "Фото не загружено")
    file_path = Path(path)
    if not file_path.is_file():
        return _error(404, "Фото не загружено")
    return Response(
        content=file_path.read_bytes(),
        media_type=uploads.image_media_type(path),
    )


@router.get("/api/instructor/cars")
def list_cars(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Список СВОИХ автомобилей (FR-26) во ВСЕХ статусах (задача 1.1):
    + status, + counters (ракурсов из 5, СТС да/нет — для кнопок и
    бейджей владельца); URL фото-эндпоинтов для плиток (баг 5.2 — клиенту
    выдается ссылка на авторизованный эндпоинт, не файловый путь).
    photo_path/blocked — устаревшие, не выдаются (design.md)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT id, brand, model, year, plate, transmission,"
            " photo_front, photo_rear, photo_interior, photo_left,"
            " photo_right, photo_sts, status, created_at"
            " FROM instructor_cars WHERE instructor_id = ? ORDER BY id",
            (instructor_id,),
        ).fetchall()
    finally:
        conn.close()
    cars = []
    for row in rows:
        car_id = row["id"]
        photos = {
            angle: (
                f"/api/instructor/cars/{car_id}/photo/{angle}"
                if row[_ANGLE_COLUMNS[angle]] is not None
                else None
            )
            for angle in ANGLES
        }
        cars.append(
            {
                key: row[key]
                for key in (
                    "id", "brand", "model", "year", "plate", "transmission",
                    "status", "created_at",
                )
            }
            | {
                "photos": photos,
                "has_sts": row["photo_sts"] is not None,
                "sts_url": (
                    f"/api/instructor/cars/{car_id}/sts"
                    if row["photo_sts"] is not None
                    else None
                ),
                "counters": _car_counters(row),
            }
        )
    return {"ok": True, "cars": cars}


@router.post("/api/instructor/cars")
async def create_car(
    request: Request,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Создание автомобиля (FR-26 + FR-44 Спринт 5): multipart с
    ОБЯЗАТЕЛЬНЫМ sts_photo (JPEG/PNG ≤5 МБ; без файла/невалидный → 422,
    авто НЕ создается); JSON-тело — путь совместимости Спринта 3
    (валидации → 422 по первому полю, как прежде)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    content_type = request.headers.get("content-type", "")
    sts_path: str | None = None
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        def _field(name: str) -> str:
            value = form.get(name)
            return value if isinstance(value, str) else ""

        try:
            year = int(_field("year") or "0")
        except ValueError:
            year = 0
        data = CarPayload(
            brand=_field("brand"),
            model=_field("model"),
            year=year,
            plate=_field("plate"),
            transmission=_field("transmission"),
        )
        updates, error = _validate_car(data, require_all=True)
        if error is not None:
            return _error(422, error)

        value = form.get("sts_photo")
        if value is None or isinstance(value, str):
            return _error(422, "Файл: загрузите фото СТС")
        content = await value.read()
        ext, error = uploads.sniff_image(content)
        if error is not None:
            return _error(422, error)
        sts_path = uploads.save_image("car_sts", content, ext or "jpg")
    else:
        # Не-multipart без файла СТС → 422 (FR-44); JSON-путь —
        # совместимость Спринта 3 (валидации → 422 по первому полю).
        try:
            body = await request.json()
        except Exception:
            return _error(422, "Файл: загрузите фото СТС")
        # M-2 (review-001): легаси-JSON путь не должен 500-ить на
        # клиентском вводе (year:"abc" → ValidationError, [1,2] →
        # TypeError) — 422 по первому полю, как докстритит эндпоинт.
        parsed = _car_payload_from_body(body)
        if parsed[0] is None:
            return _error(422, parsed[1])
        data = parsed[0]
        updates, error = _validate_car(data, require_all=True)
        if error is not None:
            return _error(422, error)

    conn = db.get_conn()
    try:
        # Спринт 7 (задача 1.1): новое авто создается в 'draft' ЯВНО —
        # DEFAULT колонки ('validated') в новом коде не используется
        # (защита от «молчаливого validated» при будущих INSERT).
        try:
            cur = conn.execute(
                "INSERT INTO instructor_cars (instructor_id, brand, model,"
                " year, plate, transmission, photo_sts, status)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, 'draft')",
                (
                    instructor_id,
                    updates["brand"],
                    updates["model"],
                    updates["year"],
                    updates["plate"],
                    updates["transmission"],
                    sts_path,
                ),
            )
        except sqlite3.Error:
            # NIT-4 (review-001): сбой INSERT — сохраненный СТС-файл
            # не остается сиротой в data/uploads/car_sts/
            if sts_path:
                Path(sts_path).unlink(missing_ok=True)
            raise
        car_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "car_id": car_id}


# --- Спринт 7 (задача 1.1): переходы статусной модели (ОВ-3) -----------------


def _car_transition(
    car_id: int,
    x_session_token: str | None,
    required_status: str,
    target_status: str,
    not_in_status_error: str,
):
    """Общий механизм перехода статуса ТОЛЬКО СВОЕГО авто: чужое/
    несуществующее → 404 (NFR-7, не раскрываем); авто не в требуемом
    статусе → 409; иначе UPDATE + 200 с новым статусом."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        row = _own_car(conn, car_id, instructor_id or 0)
        if row is None:
            return _error(404, "Автомобиль не найден")
        if row["status"] != required_status:
            return _error(409, not_in_status_error)
        # NIT-3 (review-001): guard-WHERE — единый паттерн с accept/deny
        # в student_requests.py (гонка check-then-act закрыта условием
        # в WHERE + rowcount, не только SELECT-проверкой).
        cur = conn.execute(
            "UPDATE instructor_cars SET status = ?"
            " WHERE id = ? AND status = ?",
            (target_status, car_id, required_status),
        )
        if cur.rowcount == 0:
            conn.rollback()
            return _error(409, not_in_status_error)
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "status": target_status}


@router.post("/api/instructor/cars/{car_id}/submit")
@router.post("/api/instructor/cars/{car_id}/send-to-validation")
def submit_car(
    car_id: int,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Отправка на валидацию (draft→validating): только владелец; авто не
    в draft → 409 «Автомобиль не в статусе черновика»; чужой/
    несуществующий → 404. send-to-validation — алиас из ТЗ ПМ."""
    return _car_transition(
        car_id,
        x_session_token,
        "draft",
        "validating",
        "Автомобиль не в статусе черновика",
    )


@router.post("/api/instructor/cars/{car_id}/withdraw")
@router.post("/api/instructor/cars/{car_id}/back-to-draft")
def withdraw_car(
    car_id: int,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Отзыв на доработку (validating→draft, ОВ-3): только владелец; авто
    не в validating → 409; чужой/несуществующий → 404. back-to-draft —
    алиас из ТЗ ПМ."""
    return _car_transition(
        car_id,
        x_session_token,
        "validating",
        "draft",
        "Автомобиль не на валидации",
    )


@router.patch("/api/instructor/cars/{car_id}")
def patch_car(
    car_id: int,
    data: CarPayload,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Редактирование ТОЛЬКО СВОЕГО автомобиля (FR-28); частичное
    обновление — проверяются переданные поля (валидации как POST)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    updates, error = _validate_car(data, require_all=False)
    if error is not None:
        return _error(422, error)
    if not updates:
        return _error(422, "Данные: не указано ни одного поля для изменения")

    conn = db.get_conn()
    try:
        row = _own_car(conn, car_id, instructor_id or 0)
        if row is None:
            return _error(404, "Автомобиль не найден")
        # Частичное обновление: не переданные поля — текущие значения;
        # статический SQL без конкатенации (NFR-3).
        brand = str(updates.get("brand") or row["brand"])
        model = str(updates.get("model") or row["model"])
        year = int(updates.get("year") or row["year"])
        plate = str(updates.get("plate") or row["plate"])
        transmission = str(updates.get("transmission") or row["transmission"])
        conn.execute(
            "UPDATE instructor_cars SET brand = ?, model = ?, year = ?,"
            " plate = ?, transmission = ? WHERE id = ?",
            (brand, model, year, plate, transmission, car_id),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


@router.delete("/api/instructor/cars/{car_id}")
def delete_car(
    car_id: int,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Удаление ТОЛЬКО СВОЕГО автомобиля (FR-28); ОВ-3: car_id принятых
    заявок → NULL, связь ученик ↔ инструктор сохраняется. MIN-3: брони
    пары остаются видимыми с пустым авто (не удаляются)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        row = _own_car(conn, car_id, instructor_id or 0)
        if row is None:
            return _error(404, "Автомобиль не найден")
        # ОВ-3 — одна транзакция: снятие привязки + удаление
        conn.execute(
            "UPDATE student_requests SET car_id = NULL WHERE car_id = ?",
            (car_id,),
        )
        conn.execute(
            "DELETE FROM instructor_cars WHERE id = ?",
            (car_id,),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


async def _read_form_file(
    request: Request, field: str
) -> "tuple[bytes, str] | JSONResponse":
    """Чтение и валидация файла из multipart-формы: (bytes, ext) при
    успехе; JSONResponse 422 (нет файла / не JPEG-PNG / >5 МБ)."""
    if not request.headers.get("content-type", "").startswith("multipart/form-data"):
        return _error(422, "Файл: поле обязательно")
    form = await request.form()
    value = form.get(field)
    if value is None or isinstance(value, str):
        return _error(422, "Файл: поле обязательно")
    content = await value.read()
    ext, error = uploads.sniff_image(content)
    if error is not None:
        return _error(422, error)
    return content, ext or "jpg"


@router.post("/api/instructor/cars/{car_id}/photo/{angle}")
async def upload_car_photo_angle(
    car_id: int,
    angle: str,
    request: Request,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Загрузка/замена ОДНОГО ракурса (FR-43 + задача 4.1): angle ∈
    front/rear/interior/left/right + НОВОЕ 'sts' (СТС существующего авто
    → photo_sts; корень симптома «kind=car_sts не сохраняется» — legacy
    маршрут удален) → иначе 404; только владелец (чужой авто → 404);
    JPEG/PNG ≤5 МБ по содержимому → иначе 422; остальные ракурсы не
    трогает. MAJ-1 (review-001, решение ПМ): у авто в status='validated'
    замена ЛЮБОГО ракурса/СТС возвращает его в validating (та же
    транзакция, guard-WHERE) — валидатор обязан видеть актуальные фото,
    гейт ОВ-4 не обходится задним числом; ответ содержит итоговый status.
    Файл, записанный на диск при сбое UPDATE, удаляется (NIT-4)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err
    if angle not in UPLOAD_ANGLES:
        return _error(404, "Ракурс не найден")

    conn = db.get_conn()
    try:
        row = _own_car(conn, car_id, instructor_id or 0)
        if row is None:
            return _error(404, "Автомобиль не найден")
    finally:
        conn.close()

    read = await _read_form_file(request, "photo")
    if isinstance(read, JSONResponse):
        return read
    content, ext = read
    path = uploads.save_image("car_photo", content, ext)

    conn = db.get_conn()
    try:
        try:
            cur = conn.execute(_ANGLE_UPDATE_SQL[angle], (path, car_id))
        except sqlite3.Error:
            # NIT-4 (review-001): сбой UPDATE — файл не остается сиротой
            Path(path).unlink(missing_ok=True)
            raise
        if cur.rowcount == 0:
            conn.rollback()
            Path(path).unlink(missing_ok=True)
            return _error(404, "Автомобиль не найден")
        # MAJ-1 (review-001, решение ПМ): validated → validating при
        # замене контента — в той же транзакции, guard-WHERE (паттерн
        # NIT-3); draft/validating загрузка статус не меняет (ОВ-7).
        row = conn.execute(
            "SELECT status FROM instructor_cars WHERE id = ?", (car_id,)
        ).fetchone()
        status = row["status"] if row is not None else None
        if status == "validated":
            gated = conn.execute(
                "UPDATE instructor_cars SET status = 'validating'"
                " WHERE id = ? AND status = 'validated'",
                (car_id,),
            )
            if gated.rowcount:
                status = "validating"
        conn.commit()
    finally:
        conn.close()
    return {
        "ok": True,
        "url": f"/api/instructor/cars/{car_id}/photo/{angle}",
        "status": status,
    }


@router.get("/api/instructor/cars/{car_id}/photo/{angle}")
def get_car_photo_angle(
    car_id: int,
    angle: str,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Фото ракурса (FR-42, MIN-2 + ОВ-2, задача 2.1): владелец ИЛИ ученик
    принятой пары; гость → 401; иная роль → 403; чужой/несуществующий
    авто → 404; ученик НЕ из пары → 403; Статусное правило: draft →
    ученику пары 404 (неразличение, NFR-4); validating/validated →
    выдается; angle='sts' — только владельцу (ученику пары → 403, NFR-7);
    ракурс вне списка/не загружен → 404. Ответ image/*."""
    user_id = auth.session_user_id(x_session_token)
    if user_id is None:
        return _unauthorized()

    conn = db.get_conn()
    try:
        role_row = conn.execute(
            "SELECT role FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if role_row is None:
            return _unauthorized()
        role = role_row["role"]
        if role not in ("instructor", "student"):
            return _forbidden()

        car = _any_car(conn, car_id)
        if car is None:
            return _error(404, "Автомобиль не найден")

        if role == "instructor":
            if car["instructor_id"] != user_id:
                return _error(404, "Автомобиль не найден")
        else:
            paired = conn.execute(
                "SELECT 1 FROM student_requests"
                " WHERE student_id = ? AND instructor_id = ?"
                " AND status = 'accepted'",
                (user_id, car["instructor_id"]),
            ).fetchone()
            if paired is None:
                return _error(403, "Нет доступа к фото этого автомобиля")
            # ОВ-2 (задача 2.1): draft скрыт от ученика пары — 404
            # неразличение (серверная проверка на каждом запросе, NFR-4/7).
            if car["status"] == "draft":
                return _error(404, "Автомобиль не найден")
            # СТС ученику не выдается во всех статусах (NFR-7).
            if angle == "sts":
                return _error(403, "Нет доступа к фото этого автомобиля")

        if angle not in UPLOAD_ANGLES:
            return _error(404, "Ракурс не найден")
        path = car[_ANGLE_COLUMNS[angle]]
    finally:
        conn.close()
    return _serve_image(path)


@router.get("/api/instructor/cars/{car_id}/sts")
def get_car_sts(
    car_id: int,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Фото СТС — ТОЛЬКО владельцу (FR-44, NFR-7): ученику пары и всем
    прочим — 403/404; гость → 401; чужой/несуществующий/без СТС → 404."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        row = _own_car(conn, car_id, instructor_id or 0)
    finally:
        conn.close()
    if row is None:
        return _error(404, "Автомобиль не найден")
    return _serve_image(row["photo_sts"])


# --- Спринт 7 (задача 1.2): админ — все авто, validate (ОВ-4) ----------------
# POST /api/admin/cars/{id}/block (Спринт 5) УДАЛЕН: контур блокировки
# замещен статусной моделью (design.md «Замена контура блокировки»).


@router.get("/api/admin/cars/completeness")
@router.get("/api/admin/cars")
def admin_cars_completeness(
    status: str = "",
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    """Комплектность всех авто всех инструкторов (ОВ-1 + задача 1.2):
    марка/модель/госномер, владелец, флаги 5 ракурсов + СТС, + status
    каждого авто; фильтр ?status=validating — «На валидации» (недопустимое
    значение фильтра → 422). GET /api/admin/cars — алиас из ТЗ ПМ.
    Без/с неверным админ-токеном → 401. blocked/photo_path — устаревшие,
    не читаются."""
    unauthorized = _require_admin_session(x_admin_token)
    if unauthorized is not None:
        return unauthorized
    if status and status not in ("draft", "validating", "validated"):
        return _error(422, "Статус: укажите draft, validating или validated")

    conn = db.get_conn()
    try:
        # NIT-2 (review-001): один SELECT — опциональный WHERE по фильтру
        sql = (
            "SELECT c.id, c.instructor_id, c.brand, c.model, c.plate,"
            " c.photo_front, c.photo_rear, c.photo_interior, c.photo_left,"
            " c.photo_right, c.photo_sts, c.status,"
            " u.surname, u.name, u.patronymic"
            " FROM instructor_cars AS c JOIN users AS u"
            " ON u.id = c.instructor_id"
        )
        params: tuple = ()
        if status:
            sql += " WHERE c.status = ?"
            params = (status,)
        sql += " ORDER BY c.id"
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    cars = [
        {
            "id": row["id"],
            "instructor_id": row["instructor_id"],
            "instructor_full_name": full_name(row),
            "brand": row["brand"],
            "model": row["model"],
            "plate": row["plate"],
            "photos": {
                "front": row["photo_front"] is not None,
                "rear": row["photo_rear"] is not None,
                "interior": row["photo_interior"] is not None,
                "left": row["photo_left"] is not None,
                "right": row["photo_right"] is not None,
            },
            "has_sts": row["photo_sts"] is not None,
            "status": row["status"],
            "counters": _car_counters(row),
        }
        for row in rows
    ]
    return {"ok": True, "cars": cars}


@router.post("/api/admin/cars/{car_id}/validate")
def admin_validate_car(
    car_id: int,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    """Подтверждение авто админом (ОВ-4, задача 1.2): validating→validated;
    предусловие — загружены ЛЮБЫЕ 3 ракурса из 5 И photo_sts, иначе 409 с
    перечнем недостающего; авто не в validating → 409; несуществующий →
    404; без/с неверным токеном → 401. Эффект — авто виден в каталоге,
    бейдж «Проверено»."""
    unauthorized = _require_admin_session(x_admin_token)
    if unauthorized is not None:
        return unauthorized

    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT id, photo_front, photo_rear, photo_interior,"
            " photo_left, photo_right, photo_sts, status"
            " FROM instructor_cars WHERE id = ?",
            (car_id,),
        ).fetchone()
        if row is None:
            return _error(404, "Автомобиль не найден")
        if row["status"] != "validating":
            return _error(409, "Автомобиль не на валидации")

        missing = [
            angle
            for angle in ANGLES
            if row[_ANGLE_COLUMNS[angle]] is None
        ]
        loaded = len(ANGLES) - len(missing)
        if loaded < 3 or row["photo_sts"] is None:
            parts = []
            if loaded < 3:
                parts.append(
                    "загружено ракурсов: {} из 5 (нужно минимум 3;"
                    " не хватает: {})".format(loaded, ", ".join(missing))
                )
            if row["photo_sts"] is None:
                parts.append("нет фото СТС")
            return _error(409, "Комплект неполный: " + "; ".join(parts))
        conn.execute(
            "UPDATE instructor_cars SET status = 'validated' WHERE id = ?",
            (car_id,),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "status": "validated"}
