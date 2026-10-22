"""instructor_cars.py — «Мои автомобили» инструктора (Спринт 3, задача 2.1;
Спринт 5 add-booking-docs — РАСШИРЕНИЕ: 5 ракурсов, СТС, комплектность,
блокировка, задачи 2.1/2.2/1.1).

GET/POST /api/instructor/cars; PATCH/DELETE /api/instructor/cars/{id};
POST+GET /api/instructor/cars/{id}/photo (одиночное фото — устаревший
маршрут совместимости Спринта 3, пишет photo_path; design.md MIN-4
предусматривает его удаление вместе с photo_path, но снятие ломало бы
регресс Спринта 3 — удаление отложено, колонка объявлена устаревшей);
POST+GET /api/instructor/cars/{id}/photo/{angle} — ракурсы
front/rear/interior/left/right (FR-42, FR-43);
GET /api/instructor/cars/{id}/sts — фото СТС, только владельцу (FR-44);
GET /api/admin/cars/completeness — комплектность всех авто (ОВ-1);
POST /api/admin/cars/{id}/block — блокировка авто админом (ОВ-1, MIN-2).

Доступ: require_session + role='instructor' (guards.require_role):
401 — нет/неверная сессия, 403 — чужая роль. Чужой/несуществующий
автомобиль → 404 (не раскрываем существование, FR-28). Валидации полей —
422 по полю (FR-26): brand/model/plate непустые, year — число в диапазоне,
transmission IN ('manual','automatic').

Создание (FR-44, Спринт 5): multipart-запрос ОБЯЗАТЕЛЬНО несет файл
`sts_photo` (JPEG/PNG ≤5 МБ по magic bytes до записи) — без файла → 422,
авто НЕ создается. JSON-тело (без файла) — путь совместимости Спринта 3
(авто без СТС; для новых авто фронтенд шлет multipart).

Фото ракурсов (FR-42, MIN-2): JPEG/PNG ≤5 МБ по содержимому → иначе 422;
выдача — владелец ИЛИ ученик принятой пары: гость → 401, иная роль → 403,
чужой/несуществующий/ракурс не загружен → 404, ученик НЕ из пары → 403.
Заблокированное админом авто (blocked=1) скрыто от учеников — выдача фото
ученику пары → 404 (ОВ-1); владельцу — видна (пометка в списке).
STC (СТС) ученикам не выдается — даже из пары → 403 (FR-44, NFR-7).

Баг 5.2 (FR-42, задача 1.1): список авто выдает клиенту URL авторизованного
фото-эндпоинта (photo_url / photos{angle}), а не файловый путь
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


# Спринт 5 (задача 2.1, ОВ-1): фиксированный набор ракурсов.
ANGLES = ("front", "rear", "interior", "left", "right")

# Колонка ракурса — только по валидированному angle; SQL статический
# (без конкатенации — NFR-3, grep-контроль).
_ANGLE_UPDATE_SQL = {
    "front": "UPDATE instructor_cars SET photo_front = ? WHERE id = ?",
    "rear": "UPDATE instructor_cars SET photo_rear = ? WHERE id = ?",
    "interior": "UPDATE instructor_cars SET photo_interior = ? WHERE id = ?",
    "left": "UPDATE instructor_cars SET photo_left = ? WHERE id = ?",
    "right": "UPDATE instructor_cars SET photo_right = ? WHERE id = ?",
}

_ANGLE_COLUMNS = {
    "front": "photo_front",
    "rear": "photo_rear",
    "interior": "photo_interior",
    "left": "photo_left",
    "right": "photo_right",
}


class CarPayload(BaseModel):
    # Дефолты вместо Pydantic-required — валидация в хендлере (MAJ-1).
    brand: str = ""
    model: str = ""
    year: int = 0
    plate: str = ""
    transmission: str = ""


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
    → None → 404 (не раскрываем существование)."""
    return conn.execute(
        "SELECT id, instructor_id, brand, model, year, plate, transmission,"
        " photo_path, photo_front, photo_rear, photo_interior, photo_left,"
        " photo_right, photo_sts, blocked, created_at"
        " FROM instructor_cars WHERE id = ? AND instructor_id = ?",
        (car_id, instructor_id),
    ).fetchone()


def _any_car(conn: sqlite3.Connection, car_id: int):
    """SELECT авто по id независимо от владельца (для матрицы доступа
    фото ракурсов: чужой/несуществующий различаются проверками роли)."""
    return conn.execute(
        "SELECT id, instructor_id, photo_path, photo_front, photo_rear,"
        " photo_interior, photo_left, photo_right, photo_sts, blocked"
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
    """Список СВОИХ автомобилей (FR-26) + Спринт 5: URL фото-эндпоинтов
    для плиток (баг 5.2 — клиенту выдается ссылка на авторизованный
    эндпоинт, не файловый путь), флаги ракурсов/СТС, blocked (ОВ-1)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT id, brand, model, year, plate, transmission, photo_path,"
            " photo_front, photo_rear, photo_interior, photo_left,"
            " photo_right, photo_sts, blocked, created_at"
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
                    "created_at",
                )
            }
            | {
                "has_photo": row["photo_path"] is not None,
                # Устаревший одиночный маршрут совместимости Спринта 3.
                "photo_url": (
                    f"/api/instructor/cars/{car_id}/photo"
                    if row["photo_path"] is not None
                    else None
                ),
                "photos": photos,
                "has_sts": row["photo_sts"] is not None,
                "sts_url": (
                    f"/api/instructor/cars/{car_id}/sts"
                    if row["photo_sts"] is not None
                    else None
                ),
                "blocked": bool(row["blocked"]),
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
        cur = conn.execute(
            "INSERT INTO instructor_cars (instructor_id, brand, model, year,"
            " plate, transmission, photo_sts) VALUES (?, ?, ?, ?, ?, ?, ?)",
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
        car_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "car_id": car_id}


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
    """Загрузка/замена ОДНОГО ракурса (FR-43): angle ∈
    front/rear/interior/left/right → иначе 404; только владелец (чужой
    авто → 404); JPEG/PNG ≤5 МБ по содержимому → иначе 422; файл —
    data/uploads/car_photo/<uuid>.<ext>; замена ракурса остальные
    не трогает."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err
    if angle not in ANGLES:
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
        conn.execute(
            _ANGLE_UPDATE_SQL[angle],
            (path, car_id),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "url": f"/api/instructor/cars/{car_id}/photo/{angle}"}


@router.get("/api/instructor/cars/{car_id}/photo/{angle}")
def get_car_photo_angle(
    car_id: int,
    angle: str,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Фото ракурса (FR-42, MIN-2): владелец ИЛИ ученик принятой пары;
    гость → 401; иная роль → 403; чужой/несуществующий авто → 404;
    ученик НЕ из пары → 403; заблокированное авто от ученика скрыто
    (ОВ-1) → 404; ракурс вне списка/не загружен → 404. Ответ image/*."""
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
            if car["blocked"]:
                # ОВ-1/MIN-2: заблокированное авто скрыто от учеников
                return _error(404, "Автомобиль не найден")
            paired = conn.execute(
                "SELECT 1 FROM student_requests"
                " WHERE student_id = ? AND instructor_id = ?"
                " AND status = 'accepted'",
                (user_id, car["instructor_id"]),
            ).fetchone()
            if paired is None:
                return _error(403, "Нет доступа к фото этого автомобиля")

        if angle not in ANGLES:
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


# --- Спринт 5, задача 2.2: комплектность и блокировка (админ) ---------------


@router.get("/api/admin/cars/completeness")
def admin_cars_completeness(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    """Комплектность всех авто всех инструкторов (ОВ-1): марка/модель/
    госномер, владелец, флаги 5 ракурсов + СТС, флаг blocked.
    Без/с неверным админ-токеном → 401."""
    unauthorized = _require_admin_session(x_admin_token)
    if unauthorized is not None:
        return unauthorized

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT c.id, c.instructor_id, c.brand, c.model, c.plate,"
            " c.photo_front, c.photo_rear, c.photo_interior, c.photo_left,"
            " c.photo_right, c.photo_sts, c.blocked,"
            " u.surname, u.name, u.patronymic"
            " FROM instructor_cars AS c JOIN users AS u"
            " ON u.id = c.instructor_id ORDER BY c.id",
        ).fetchall()
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
            "blocked": bool(row["blocked"]),
        }
        for row in rows
    ]
    return {"ok": True, "cars": cars}


@router.post("/api/admin/cars/{car_id}/block")
def admin_block_car(
    car_id: int,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    """Блокировка авто (ОВ-1, назначение — авто с неполным комплектом):
    blocked=1, идемпотентно (повторное — 200 без ошибки). Эффект (MIN-2):
    авто скрыт от учеников (выдача фото ученику пары → 404), НЕ
    ретроактивен для броней; разблокировка — вне объема. Без токена → 401;
    несуществующий → 404."""
    unauthorized = _require_admin_session(x_admin_token)
    if unauthorized is not None:
        return unauthorized

    conn = db.get_conn()
    try:
        cur = conn.execute(
            "UPDATE instructor_cars SET blocked = 1 WHERE id = ?",
            (car_id,),
        )
        if cur.rowcount == 0:
            return _error(404, "Автомобиль не найден")
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "blocked": True}


# --- Устаревший одиночный маршрут Спринта 3 (совместимость; MIN-4: removal
# отложен — см. докстринг модуля). photo_path объявлена устаревшей. -------


@router.post("/api/instructor/cars/{car_id}/photo")
async def upload_car_photo(
    car_id: int,
    request: Request,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Загрузка фото СВОЕГО автомобиля (FR-27): JPEG/PNG ≤5 МБ по
    содержимому (magic bytes) до записи на диск → иначе 422; файл
    сохраняется в data/uploads/cars/<uuid>.<ext> (NFR-1, NFR-6)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

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
    path = uploads.save_image("cars", content, ext)
    conn = db.get_conn()
    try:
        conn.execute(
            "UPDATE instructor_cars SET photo_path = ? WHERE id = ?",
            (path, car_id),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


@router.get("/api/instructor/cars/{car_id}/photo")
def get_car_photo(
    car_id: int,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Фото автомобиля — только владельцу (MIN-2): гость → 401, чужая
    роль → 403, чужой/несуществующий/без фото → 404; ответ image/*."""
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
    return _serve_image(row["photo_path"])
