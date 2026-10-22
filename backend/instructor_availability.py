"""instructor_availability.py — график часов работы (задача 3.1, домен
instructor-availability; design.md блок 3).

GET/PUT /api/instructor/availability. Доступ: сессия + role='instructor'
(401 гость, 403 иная роль — specs/instructor-availability).

PUT — ПОЛНАЯ замена графика инструктора в одной транзакции (FR-29, FR-30):
тело {intervals: [{weekday, start_time, end_time}]}; weekday 0..6 (0 =
понедельник), start/end — HH:MM, start < end → иначе 422; дубликаты
схлопываются. SQL — параметризованный (NFR-3).
"""
import re
import sqlite3

from fastapi import APIRouter, Header
from pydantic import BaseModel

import backend.db as db
from backend.booking import blocking_bookings, conflict_error_response
from backend.guards import _error, require_role

router = APIRouter()

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class Interval(BaseModel):
    # Дефолты вместо Pydantic-required — валидация в хендлере.
    weekday: int = -1
    start_time: str = ""
    end_time: str = ""


class AvailabilityPayload(BaseModel):
    intervals: list[Interval] = []


def _hhmm_valid(value: str) -> bool:
    return bool(_TIME_RE.match(value or ""))


def _normalized_intervals(
    payload: AvailabilityPayload,
) -> tuple[list[tuple[int, str, str]], str | None]:
    """Валидация intervals; дубликаты схлопываются (design.md блок 3).
    Возвращает (отсортированные уникальные интервалы, ошибка)."""
    seen: set[tuple[int, str, str]] = set()
    for interval in payload.intervals:
        if interval.weekday < 0 or interval.weekday > 6:
            return [], "День недели: целое число от 0 (пн) до 6 (вс)"
        if not _hhmm_valid(interval.start_time) or not _hhmm_valid(
            interval.end_time
        ):
            return [], "Время: укажите границы интервала в формате ЧЧ:ММ"
        if interval.start_time >= interval.end_time:
            return [], "Интервал: начало должно быть раньше конца"
        seen.add((interval.weekday, interval.start_time, interval.end_time))
    return sorted(seen), None


@router.get("/api/instructor/availability")
def get_availability(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Интервалы текущего графика (FR-30), упорядочены по дню и началу."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT weekday, start_time, end_time FROM availability"
            " WHERE instructor_id = ? ORDER BY weekday, start_time, end_time",
            (instructor_id,),
        ).fetchall()
    finally:
        conn.close()
    intervals = [
        {"weekday": row["weekday"], "start_time": row["start_time"],
         "end_time": row["end_time"]}
        for row in rows
    ]
    return {"ok": True, "intervals": intervals}


@router.put("/api/instructor/availability")
def put_availability(
    data: AvailabilityPayload,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Полная замена графика (FR-29/FR-30): DELETE + INSERT уникальных
    интервалов в одной write-транзакции BEGIN IMMEDIATE (M-3 review-001:
    проверка конфликтов внутри той же транзакции — сериализация с
    create_booking, бронь-сирота невозможна); валидация до записи → 422."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    intervals, error = _normalized_intervals(data)
    if error is not None:
        return _error(422, error)

    conn: sqlite3.Connection = db.get_conn()
    try:
        # MAJ-1 (Спринт 5, задача 4.1): замена графика отклоняется 409,
        # если удаляемые слоты имеют брони 'new'/'confirmed'; график НЕ
        # изменяется — инструктор сначала решает брони (booking.py).
        # M-3 (review-001, NFR-8): BEGIN IMMEDIATE ДО проверки конфликтов —
        # проверка (blocking_bookings) и запись (DELETE/INSERT) в одной
        # write-транзакции, сериализуется с create_booking (тоже BEGIN
        # IMMEDIATE): окно TOCTOU «проверка → удаление» закрыто, бронь на
        # удаляемый слот не может появиться после проверки (иначе была бы
        # бронь-сирота без FK booking→availability).
        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        conflicts = blocking_bookings(conn, instructor_id or 0, intervals)
        if conflicts:
            conn.execute("ROLLBACK")
            return conflict_error_response(conflicts)
        # Та же транзакция: полная замена графика (design.md блок 3)
        conn.execute(
            "DELETE FROM availability WHERE instructor_id = ?", (instructor_id,)
        )
        conn.executemany(
            "INSERT INTO availability (instructor_id, weekday, start_time,"
            " end_time) VALUES (?, ?, ?, ?)",
            [(instructor_id, wd, start, end) for wd, start, end in intervals],
        )
        conn.execute("COMMIT")
    finally:
        conn.close()
    return {"ok": True, "intervals": [
        {"weekday": wd, "start_time": start, "end_time": end}
        for wd, start, end in intervals
    ]}
