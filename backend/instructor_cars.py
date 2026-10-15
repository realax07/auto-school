"""instructor_cars.py — «Мои автомобили» инструктора (задача 2.1, домен
instructor-cars; design.md блок 2).

GET/POST /api/instructor/cars; PATCH/DELETE /api/instructor/cars/{id};
POST+GET /api/instructor/cars/{id}/photo.

Доступ: require_session + role='instructor' (guards.require_role):
401 — нет/неверная сессия, 403 — чужая роль. Чужой/несуществующий
автомобиль → 404 (не раскрываем существование, FR-28). Валидации полей —
422 по полю (FR-26): brand/model/plate непустые, year — число в диапазоне,
transmission IN ('manual','automatic').

Фото (FR-27, NFR-1/6, MIN-2): JPEG/PNG ≤5 МБ по magic bytes до записи
(uploads.sniff_image) → иначе 422; выдача только владельцу: гость → 401,
чужая роль → 403, чужой/несуществующий/без фото → 404.

DELETE (ОВ-3): student_requests.car_id привязанных заявок → NULL, связь
«ученик ↔ инструктор» (status='accepted') сохраняется. Файлы-сироты в
data/uploads/cars/ — осознанный техдолг (MIN-3 arch-review, cleanup вне
скоупа).

SQL — только параметризованный (NFR-3); токены/файлы не логируются (NFR-4).
"""
import datetime
import sqlite3
from pathlib import Path

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

import backend.db as db
import backend.uploads as uploads
from backend.guards import _error, require_role

router = APIRouter()

_YEAR_MIN = 1950
_YEAR_MAX = datetime.date.today().year + 1


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
        " photo_path FROM instructor_cars WHERE id = ? AND instructor_id = ?",
        (car_id, instructor_id),
    ).fetchone()


@router.get("/api/instructor/cars")
def list_cars(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Список СВОИХ автомобилей (FR-26)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT id, brand, model, year, plate, transmission, photo_path,"
            " created_at FROM instructor_cars WHERE instructor_id = ?"
            " ORDER BY id",
            (instructor_id,),
        ).fetchall()
    finally:
        conn.close()
    cars = [
        {key: row[key] for key in row.keys() if key != "photo_path"}
        | {"has_photo": row["photo_path"] is not None}
        for row in rows
    ]
    return {"ok": True, "cars": cars}


@router.post("/api/instructor/cars")
def create_car(
    data: CarPayload,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Создание автомобиля (FR-26): валидации → 422 по первому полю."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    updates, error = _validate_car(data, require_all=True)
    if error is not None:
        return _error(422, error)

    conn = db.get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO instructor_cars (instructor_id, brand, model, year,"
            " plate, transmission) VALUES (?, ?, ?, ?, ?, ?)",
            (
                instructor_id,
                updates["brand"],
                updates["model"],
                updates["year"],
                updates["plate"],
                updates["transmission"],
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
    заявок → NULL, связь ученик ↔ инструктор сохраняется."""
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

    form = await request.form()
    value = form.get("photo")
    if value is None or isinstance(value, str):
        return _error(422, "Файл: поле обязательно")
    content = await value.read()
    ext, error = uploads.sniff_image(content)
    if error is not None:
        return _error(422, error)

    path = uploads.save_image("cars", content, ext or "jpg")
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
    path = row["photo_path"]
    if not path:
        return _error(404, "Фото не загружено")
    file_path = Path(path)
    if not file_path.is_file():
        return _error(404, "Фото не загружено")
    return Response(
        content=file_path.read_bytes(),
        media_type=uploads.image_media_type(path),
    )
