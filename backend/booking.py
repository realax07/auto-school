"""booking.py — бронирование слотов (Спринт 5, задача 4.1; design.md
блок C, домен booking — отдельный модуль по директиве Заказчика).

GET  /api/student/instructors/{id}/slots — график инструктора с состояниями
     слотов (только для ПРИНЯТОЙ пары — серверная проверка, FR-46);
POST /api/student/bookings               — запрос брони (FR-47);
GET  /api/student/bookings               — «Мои брони»/календарь ученика
     (FR-48, FR-49);
GET  /api/instructor/bookings            — входящие брони инструктора
     (FR-48, FR-49);
POST /api/instructor/bookings/{id}/confirm — подтверждение (FR-48);
POST /api/instructor/bookings/{id}/reject  — отклонение, комментарий
     обязателен (ОВ-2, FR-48);
POST /api/instructor/bookings/{id}/cancel  — отмена ПОДТВЕРЖДЕННОЙ брони
     (BUG-049), без комментария;
helper blocking_bookings — согласование PUT availability с активными
     бронями (MAJ-1): слоты с бронями 'new'/'confirmed', отсутствующие
     в новом графике, блокируют замену → 409 с перечнем.

Гонки (NFR-8): POST запроса брони — транзакция BEGIN IMMEDIATE + частичный
UNIQUE-индекс uq_booking_active_slot (db.py): INSERT при уже занятом слоте
→ IntegrityError → откат → 409 «Слот уже занят», записи нет. Предварительный
SELECT — только UX-уровень, гарантией является индекс.

lesson_date (MIN-1): материализуется при создании брони — ближайшая дата
weekday слота по ЛОКАЛЬНОЙ ДАТЕ СЕРВЕРА (datetime.date.today()).

Единственность решения (FR-48): confirm/reject — UPDATE … WHERE id=? AND
status='new' с проверкой rowcount (0 → 409), повторное решение → 409.
Связь «ученик принят» — student_requests.status='accepted' (ADR-004).
Блокировка авто (MIN-2) контур брони НЕ затрагивает: существующие брони
видны, новые брони не запрещаются.

SQL — только параметризованный (NFR-10←NFR-3); ФИО/токены не логируются.
"""
import datetime
import sqlite3

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import backend.db as db
from backend.guards import _error, full_name, require_role

router = APIRouter()

_ACTIVE_STATUSES = ("new", "confirmed")

_WEEKDAY_NAMES = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")


class BookingCreatePayload(BaseModel):
    # Дефолты вместо Pydantic-required — валидация в хендлере.
    availability_id: int = 0


class RejectPayload(BaseModel):
    comment: str = ""


def local_today() -> datetime.date:
    """Локальная дата сервера (MIN-1) — единое правило для lesson_date
    и «today» виджета «Занятия на сегодня»."""
    return datetime.date.today()


def materialize_lesson_date(weekday: int) -> str:
    """Ближайшая дата weekday (0=пн) от локальной даты сервера (MIN-1):
    сегодняшний weekday → сегодня, иначе ближайшие впереди."""
    today = local_today()
    days_ahead = (weekday - today.weekday()) % 7
    return (today + datetime.timedelta(days=days_ahead)).isoformat()


def _pair_accepted(
    conn: sqlite3.Connection, student_id: int, instructor_id: int
) -> bool:
    """Связь «ученик принят» (Спринт 3): активная accepted-заявка."""
    return conn.execute(
        "SELECT 1 FROM student_requests"
        " WHERE student_id = ? AND instructor_id = ? AND status = 'accepted'",
        (student_id, instructor_id),
    ).fetchone() is not None


def _car_brief(
    conn: sqlite3.Connection, car_id: int | None
) -> dict | None:
    """Авто пары для календарей (MIN-3): car_id NULL/удален → None («—»),
    не ошибка; заблокированное авто (MIN-2) календарь НЕ скрывает."""
    if not car_id:
        return None
    row = conn.execute(
        "SELECT id, brand, model, year, transmission FROM instructor_cars"
        " WHERE id = ?",
        (car_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def _pair_car(
    conn: sqlite3.Connection, student_id: int, instructor_id: int
) -> dict | None:
    """Авто пары «следует за перекреплением» (ОВ-6): car_id берется из
    ТЕКУЩЕЙ accepted-заявки на момент выдачи."""
    row = conn.execute(
        "SELECT car_id FROM student_requests"
        " WHERE student_id = ? AND instructor_id = ? AND status = 'accepted'",
        (student_id, instructor_id),
    ).fetchone()
    if row is None:
        return None
    return _car_brief(conn, row["car_id"])


def blocking_bookings(
    conn: sqlite3.Connection,
    instructor_id: int,
    intervals: list[tuple[int, str, str]],
) -> list[dict]:
    """MAJ-1: слоты инструктора с активными бронями ('new'/'confirmed'),
    ОТСУТСТВУЮЩИЕ в новом графике. Пустой список → замена допустима;
    слоты с только 'rejected' бронями не мешают (design.md)."""
    keep = set(intervals)
    rows = conn.execute(
        "SELECT DISTINCT a.weekday, a.start_time, a.end_time, b.status"
        " FROM booking AS b JOIN availability AS a ON a.id = b.availability_id"
        " WHERE a.instructor_id = ? AND b.status IN (?, ?)",
        (instructor_id, *_ACTIVE_STATUSES),
    ).fetchall()
    conflicts: dict[tuple[int, str, str], list[str]] = {}
    for row in rows:
        slot = (row["weekday"], row["start_time"], row["end_time"])
        if slot not in keep:
            conflicts.setdefault(slot, []).append(row["status"])
    return [
        {
            "weekday": weekday,
            "start_time": start,
            "end_time": end,
            "booking_statuses": sorted(statuses),
        }
        for (weekday, start, end), statuses in sorted(conflicts.items())
    ]


def _slot_conflict_text(conflicts: list[dict]) -> str:
    parts = [
        "{} {}–{} ({})".format(
            _WEEKDAY_NAMES[c["weekday"]],
            c["start_time"],
            c["end_time"],
            ", ".join(c["booking_statuses"]),
        )
        for c in conflicts
    ]
    return (
        "В графике есть слоты с активными бронями: "
        + "; ".join(parts)
        + ". Сначала решите брони (подтвердите или отклоните)"
    )


def conflict_error_response(conflicts: list[dict]) -> JSONResponse:
    """409 PUT availability (MAJ-1) с ПЕРЕЧНЕМ затронутых слотов
    (weekday, интервал, статус брони) — график не изменен."""
    return JSONResponse(
        status_code=409,
        content={
            "ok": False,
            "error": _slot_conflict_text(conflicts),
            "conflicts": conflicts,
        },
    )


# --- Ученик -----------------------------------------------------------------


@router.get("/api/student/instructors/{instructor_id}/slots")
def instructor_slots(
    instructor_id: int,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """График инструктора для ПРИНЯТОГО ученика (FR-46, FR-50): серверная
    проверка пары — иначе 403 (в т.ч. прямой вызов мимо UI); инструктор
    не существует/не одобрен → 404. Состояния слотов: free / busy (чужая
    ИЛИ своя подтвержденная активная бронь, кем — не раскрывается) /
    pending (СВОЙ запрос 'new')."""
    student_id, err = require_role(x_session_token, "student")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        instructor = conn.execute(
            "SELECT id FROM users WHERE id = ? AND role = 'instructor'",
            (instructor_id,),
        ).fetchone()
        if instructor is None:
            return _error(404, "Инструктор не найден")
        if not _pair_accepted(conn, student_id or 0, instructor_id):
            return _error(403, "Нет принятой пары с этим инструктором")

        intervals = conn.execute(
            "SELECT id, weekday, start_time, end_time FROM availability"
            " WHERE instructor_id = ? ORDER BY weekday, start_time, end_time",
            (instructor_id,),
        ).fetchall()
        active = conn.execute(
            "SELECT availability_id, student_id, status FROM booking"
            " WHERE instructor_id = ? AND status IN (?, ?)",
            (instructor_id, *_ACTIVE_STATUSES),
        ).fetchall()
    finally:
        conn.close()

    mine = {row["availability_id"]: row["status"] for row in active
            if row["student_id"] == student_id}
    busy = {row["availability_id"] for row in active}
    slots = [
        {
            "id": row["id"],
            "weekday": row["weekday"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "state": (
                "pending" if mine.get(row["id"]) == "new"
                else "busy" if row["id"] in busy
                else "free"
            ),
        }
        for row in intervals
    ]
    return {"ok": True, "slots": slots}


@router.post("/api/student/bookings")
def create_booking(
    data: BookingCreatePayload,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Запрос брони (FR-47, NFR-8): слот не существует → 404; нет принятой
    пары с инструктором слота → 403; слот занят (частичный UNIQUE в
    транзакции BEGIN IMMEDIATE) → 409 без записи; повторный запрос на
    свой слот «на рассмотрении» → 409. lesson_date — ближайшая будущая
    дата weekday слота по локальной дате сервера (MIN-1)."""
    student_id, err = require_role(x_session_token, "student")
    if err is not None:
        return err
    if data.availability_id <= 0:
        return _error(422, "Слот: поле обязательно")

    conn = db.get_conn()
    try:
        # Пара (FR-46/FR-47): совсем нет принятой пары → 403; слот не
        # существует либо принадлежит НЕ инструктору пары → 404.
        pairs = {
            row["instructor_id"]
            for row in conn.execute(
                "SELECT DISTINCT instructor_id FROM student_requests"
                " WHERE student_id = ? AND status = 'accepted'",
                (student_id,),
            ).fetchall()
        }
        if not pairs:
            return _error(403, "Нет принятой пары с инструктором")

        # Гонка (NFR-8): запись лочится до конца транзакции — параллельный
        # INSERT проигравшего роняет частичный UNIQUE-индекс, а не портит данные.
        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        slot = conn.execute(
            "SELECT id, instructor_id, weekday FROM availability WHERE id = ?",
            (data.availability_id,),
        ).fetchone()
        if slot is None or slot["instructor_id"] not in pairs:
            conn.execute("ROLLBACK")
            return _error(404, "Слот не найден")

        lesson_date = materialize_lesson_date(slot["weekday"])
        try:
            cur = conn.execute(
                "INSERT INTO booking (student_id, instructor_id,"
                " availability_id, lesson_date, status)"
                " VALUES (?, ?, ?, ?, 'new')",
                (student_id, slot["instructor_id"], data.availability_id,
                 lesson_date),
            )
        except sqlite3.IntegrityError:
            conn.execute("ROLLBACK")
            return _error(409, "Слот уже занят")
        booking_id = cur.lastrowid
        conn.execute("COMMIT")
    finally:
        conn.close()
    return {
        "ok": True,
        "booking_id": booking_id,
        "status": "new",
        "lesson_date": lesson_date,
    }


def _booking_row(conn: sqlite3.Connection, booking_id: int):
    return conn.execute(
        "SELECT b.id, b.student_id, b.instructor_id, b.status,"
        " b.reject_comment, b.lesson_date, b.created_at, b.decided_at,"
        " a.weekday, a.start_time, a.end_time"
        " FROM booking AS b JOIN availability AS a ON a.id = b.availability_id"
        " WHERE b.id = ?",
        (booking_id,),
    ).fetchone()


@router.get("/api/student/bookings")
def my_bookings(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """«Мои брони»/календарь ученика (FR-48, FR-49): статус, дата/время
    слота, инструктор (ФИО), авто пары (следует за перекреплением, ОВ-6;
    удален → null — корректное пустое состояние, MIN-3), reject_comment
    при отклонении (ОВ-2)."""
    student_id, err = require_role(x_session_token, "student")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT b.id, b.instructor_id, b.status, b.reject_comment,"
            " b.lesson_date, b.created_at, b.decided_at,"
            " a.weekday, a.start_time, a.end_time"
            " FROM booking AS b JOIN availability AS a"
            " ON a.id = b.availability_id"
            " WHERE b.student_id = ?"
            " ORDER BY b.lesson_date, a.start_time, b.id",
            (student_id,),
        ).fetchall()
        bookings = []
        for row in rows:
            instructor = conn.execute(
                "SELECT surname, name, patronymic FROM users WHERE id = ?",
                (row["instructor_id"],),
            ).fetchone()
            bookings.append({
                "id": row["id"],
                "status": row["status"],
                "lesson_date": row["lesson_date"],
                "weekday": row["weekday"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "instructor_full_name": (
                    full_name(instructor) if instructor else ""
                ),
                "car": _pair_car(conn, student_id or 0, row["instructor_id"]),
                "reject_comment": (
                    row["reject_comment"] if row["status"] == "rejected" else None
                ),
                "created_at": row["created_at"],
                "decided_at": row["decided_at"],
            })
    finally:
        conn.close()
    return {"ok": True, "bookings": bookings}


# --- Инструктор -------------------------------------------------------------


@router.get("/api/instructor/bookings")
def instructor_bookings(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Входящие брони ТОЛЬКО этого инструктора (FR-48): ученик (ФИО),
    слот (дата/время), статус, авто пары (null при удалении — MIN-3);
    reject_comment при отклонении (ОВ-2) — рендерится в разделе
    «Бронирования» как «Ваш комментарий при отказе»."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT b.id, b.student_id, b.status, b.reject_comment,"
            " b.lesson_date, b.created_at, b.decided_at,"
            " a.weekday, a.start_time, a.end_time"
            " FROM booking AS b JOIN availability AS a"
            " ON a.id = b.availability_id"
            " WHERE b.instructor_id = ?"
            " ORDER BY b.lesson_date, a.start_time, b.id",
            (instructor_id,),
        ).fetchall()
        bookings = []
        for row in rows:
            student = conn.execute(
                "SELECT surname, name, patronymic FROM users WHERE id = ?",
                (row["student_id"],),
            ).fetchone()
            bookings.append({
                "id": row["id"],
                "status": row["status"],
                "lesson_date": row["lesson_date"],
                "weekday": row["weekday"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "student_full_name": full_name(student) if student else "",
                "car": _pair_car(conn, row["student_id"], instructor_id or 0),
                "reject_comment": (
                    row["reject_comment"] if row["status"] == "rejected" else None
                ),
                "created_at": row["created_at"],
                "decided_at": row["decided_at"],
            })
    finally:
        conn.close()
    return {"ok": True, "bookings": bookings}


@router.post("/api/instructor/bookings/{booking_id}/confirm")
def confirm_booking(
    booking_id: int,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Подтверждение (FR-48, NFR-8): только своя бронь → иначе 404;
    только 'new' → иначе 409; БЕЗ комментария (ОВ-2). Атомарно: guard
    AND status='new' + rowcount; конкурирующая бронь на слоте невозможна
    (частичный UNIQUE держит слот этой бронью)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        row = _booking_row(conn, booking_id)
        if row is None or row["instructor_id"] != instructor_id:
            return _error(404, "Бронь не найдена")
        cur = conn.execute(
            "UPDATE booking SET status = 'confirmed', decided_at = datetime('now')"
            " WHERE id = ? AND status = 'new'",
            (booking_id,),
        )
        if cur.rowcount == 0:
            return _error(409, "Бронь: решение уже принято")
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "status": "confirmed"}


@router.post("/api/instructor/bookings/{booking_id}/cancel")
def cancel_booking(
    booking_id: int,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Отмена ПОДТВЕРЖДЕННОЙ брони (BUG-049, скрины Заказчика 2026-10-23):
    только своя бронь → иначе 404; guard-статус 'confirmed' (решения по
    'new' — confirm/reject) → иначе 409; БЕЗ комментария (аналог confirm —
    за инструктора текст не пишем, reject_comment остается NULL).
    Эффект: status='rejected' (CHECK в db.py статуса 'cancelled' не знает),
    decided_at; слот освобождается — 'rejected' выпадает из частичного
    индекса uq_booking_active_slot (ОВ-5). Атомарно: guard
    AND status='confirmed' + rowcount (0 → 409)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        row = _booking_row(conn, booking_id)
        if row is None or row["instructor_id"] != instructor_id:
            return _error(404, "Бронь не найдена")
        cur = conn.execute(
            "UPDATE booking SET status = 'rejected',"
            " decided_at = datetime('now') WHERE id = ? AND status = 'confirmed'",
            (booking_id,),
        )
        if cur.rowcount == 0:
            return _error(409, "Бронь: решение уже принято")
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "status": "rejected"}


@router.post("/api/instructor/bookings/{booking_id}/reject")
def reject_booking(
    booking_id: int,
    data: RejectPayload | None = None,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Отклонение (ОВ-2, FR-48): комментарий непустой обязателен —
    пустой/отсутствующий → 422, действие заблокировано, статус 'new'
    остается; только своя и 'new' → иначе 404/409. Эффект: 'rejected' +
    reject_comment; слот освобождается (ОВ-5) — повторный запрос
    возможен (rejected выпадает из частичного индекса)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    comment = (data.comment if data is not None else "") or ""
    if not comment.strip():
        return _error(422, "Комментарий: поле обязательно")

    conn = db.get_conn()
    try:
        row = _booking_row(conn, booking_id)
        if row is None or row["instructor_id"] != instructor_id:
            return _error(404, "Бронь не найдена")
        cur = conn.execute(
            "UPDATE booking SET status = 'rejected', reject_comment = ?,"
            " decided_at = datetime('now') WHERE id = ? AND status = 'new'",
            (comment.strip(), booking_id),
        )
        if cur.rowcount == 0:
            return _error(409, "Бронь: решение уже принято")
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "status": "rejected"}
