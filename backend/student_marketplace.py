"""student_marketplace.py — «Выбор инструктора» ученика (задача 4.1, домен
student-instructor-choice; design.md блок 4).

GET /api/student/instructors — карточки ТОЛЬКО одобренных инструкторов
(users.role='instructor' — следствие approve, Спринт 2; waiting/deny в
users отсутствуют) с query-фильтрами:
- transmission=manual|automatic — наличие авто с такой КПП;
- min_rating=0..5 — средняя оценка ≥ значения; {has_reviews:false} НЕ
  удовлетворяет min_rating>0 и удовлетворяет min_rating=0 (MIN-1);
- min_experience — стаж ≥ значения (users.experience_years, MAJ-3);
- free_weekday + free_from + free_to — пересечение с availability.
Пустой результат — 200 {ok:true, instructors:[]} (FR-32).

GET /api/student/instructors/{id} — профиль: ФИО (склейка на сервере,
ADR-004), стаж, автомобили (марка/модель/год/КПП — БЕЗ фото и госномера),
агрегат рейтинга {average, count} / {has_reviews:false} (FR-35), часы
работы. Несуществующий/неодобренный → 404.

Рейтинг — агрегат AVG/COUNT по reviews на лету, без денормализации
(ADR-004 п.3). SQL — параметризованный (NFR-3).
"""
import re
import sqlite3

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

import backend.db as db
from backend.guards import _error, full_name, require_role

router = APIRouter()

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _unauthorized_like_404() -> JSONResponse:
    return _error(404, "Инструктор не найден")


def _rating_aggregate(conn: sqlite3.Connection, instructor_id: int) -> dict:
    """Агрегат рейтинга инструктора (FR-35, ADR-004): {has_reviews:false}
    при пустом наборе («нет отзывов», не 0.0); иначе {average, count}."""
    row = conn.execute(
        "SELECT COUNT(*) AS cnt, AVG(rating) AS avg_rating"
        " FROM reviews WHERE instructor_id = ?",
        (instructor_id,),
    ).fetchone()
    if row["cnt"] == 0:
        return {"has_reviews": False}
    return {
        "has_reviews": True,
        "average": round(row["avg_rating"], 1),
        "count": row["cnt"],
    }


def _instructor_cars(conn: sqlite3.Connection, instructor_id: int) -> list[dict]:
    """Автомобили карточки: марка/модель/год/КПП — БЕЗ фото и госномера
    (design.md блок 4, NFR-1). Спринт 7 (ОВ-2, задача 2.1): в каталоге и
    авто-фильтрах — ТОЛЬКО status='validated' (серверная проверка на
    каждом запросе, NFR-7); инструктор без validated-авто остается в
    каталоге с пустым блоком авто."""
    rows = conn.execute(
        "SELECT id, brand, model, year, transmission FROM instructor_cars"
        " WHERE instructor_id = ? AND status = 'validated' ORDER BY id",
        (instructor_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _instructor_intervals(
    conn: sqlite3.Connection, instructor_id: int
) -> list[dict]:
    rows = conn.execute(
        "SELECT weekday, start_time, end_time FROM availability"
        " WHERE instructor_id = ? ORDER BY weekday, start_time",
        (instructor_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _parse_filters(
    transmission: str,
    min_rating_raw: str,
    min_experience_raw: str,
    free_weekday_raw: str,
    free_from: str,
    free_to: str,
) -> tuple[dict, str | None]:
    """Разбор/валидация query-фильтров → (фильтры, ошибка 422)."""
    filters: dict = {}
    if transmission:
        if transmission not in ("manual", "automatic"):
            return {}, "КПП: укажите manual или automatic"
        filters["transmission"] = transmission
    if min_rating_raw:
        try:
            min_rating = float(min_rating_raw)
        except ValueError:
            return {}, "Рейтинг: число от 0 до 5"
        if min_rating < 0 or min_rating > 5:
            return {}, "Рейтинг: число от 0 до 5"
        filters["min_rating"] = min_rating
    if min_experience_raw:
        try:
            min_experience = int(min_experience_raw)
        except ValueError:
            return {}, "Стаж: целое число лет не меньше 0"
        if min_experience < 0:
            return {}, "Стаж: целое число лет не меньше 0"
        filters["min_experience"] = min_experience
    if free_weekday_raw or free_from or free_to:
        # Фильтр свободного времени — только полным набором (design.md)
        if not (free_weekday_raw and free_from and free_to):
            return {}, "Свободное время: укажите день недели и интервал ЧЧ:ММ"
        try:
            weekday = int(free_weekday_raw)
        except ValueError:
            return {}, "День недели: целое число от 0 (пн) до 6 (вс)"
        if weekday < 0 or weekday > 6:
            return {}, "День недели: целое число от 0 (пн) до 6 (вс)"
        if not _TIME_RE.match(free_from) or not _TIME_RE.match(free_to):
            return {}, "Время: укажите границы интервала в формате ЧЧ:ММ"
        if free_from >= free_to:
            return {}, "Интервал: начало должно быть раньше конца"
        filters["free"] = (weekday, free_from, free_to)
    return filters, None


def _passes_filters(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    rating: dict,
    cars: list[dict],
    intervals: list[dict],
    filters: dict,
) -> bool:
    if "transmission" in filters:
        if not any(car["transmission"] == filters["transmission"] for car in cars):
            return False
    if "min_rating" in filters:
        # MIN-1: без отзывов не проходит min_rating>0, проходит min_rating=0
        if not rating.get("has_reviews", False):
            if filters["min_rating"] > 0:
                return False
        elif rating["average"] < filters["min_rating"]:
            return False
    if "min_experience" in filters:
        if (row["experience_years"] or 0) < filters["min_experience"]:
            return False
    if "free" in filters:
        weekday, free_from, free_to = filters["free"]
        overlaps = any(
            interval["weekday"] == weekday
            and interval["start_time"] < free_to
            and free_from < interval["end_time"]
            for interval in intervals
        )
        if not overlaps:
            return False
    return True


@router.get("/api/student/instructors")
def list_instructors(
    transmission: str = "",
    min_rating: str = "",
    min_experience: str = "",
    free_weekday: str = "",
    free_from: str = "",
    free_to: str = "",
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Каталог одобренных инструкторов с фильтрами (FR-31, FR-32)."""
    student_id, err = require_role(x_session_token, "student")
    if err is not None:
        return err
    del student_id

    filters, error = _parse_filters(
        transmission, min_rating, min_experience,
        free_weekday, free_from, free_to,
    )
    if error is not None:
        return _error(422, error)

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT id, surname, name, patronymic, experience_years"
            " FROM users WHERE role = 'instructor' ORDER BY id"
        ).fetchall()
        instructors = []
        for row in rows:
            rating = _rating_aggregate(conn, row["id"])
            cars = _instructor_cars(conn, row["id"])
            intervals = _instructor_intervals(conn, row["id"])
            if not _passes_filters(conn, row, rating, cars, intervals, filters):
                continue
            instructors.append({
                "id": row["id"],
                "full_name": full_name(row),
                "experience_years": row["experience_years"] or 0,
                "rating": rating,
                "cars": cars,
                "availability": intervals,
            })
    finally:
        conn.close()
    # Пустой результат — корректное пустое состояние, не ошибка (FR-32)
    return {"ok": True, "instructors": instructors}


@router.get("/api/student/instructors/{instructor_id}")
def instructor_card(
    instructor_id: int,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Карточка инструктора (FR-35): ФИО, стаж, авто без фото/госномера,
    агрегат рейтинга, часы работы; несуществующий/неодобренный → 404."""
    _student_id, err = require_role(x_session_token, "student")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT id, surname, name, patronymic, experience_years"
            " FROM users WHERE id = ? AND role = 'instructor'",
            (instructor_id,),
        ).fetchone()
        if row is None:
            return _unauthorized_like_404()
        card = {
            "id": row["id"],
            "full_name": full_name(row),
            "experience_years": row["experience_years"] or 0,
            "rating": _rating_aggregate(conn, row["id"]),
            "cars": _instructor_cars(conn, row["id"]),
            "availability": _instructor_intervals(conn, row["id"]),
        }
    finally:
        conn.close()
    return {"ok": True, "instructor": card}
