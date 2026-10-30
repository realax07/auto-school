"""instructor_summary.py — виджеты главной кабинета инструктора (задача
6.2; design.md блок 6, FR-40, FR-41; Спринт 5 задача 4.2 — расширение).

GET /api/instructor/summary:
- students — принятые ученики (student_requests.status='accepted'):
  ФИО, авто, дата принятия; «новые» заявки в виджет не попадают,
  пустой список — корректное пустое состояние (FR-40);
- today_lessons (Спринт 5, FR-49, ОВ-6) — подтвержденные брони
  инструктора на текущую дату (booking.lesson_date = today, «today» —
  ЛОКАЛЬНАЯ дата сервера, то же правило, что materialize_lesson_date —
  MIN-1): ученик (ФИО), время слота, авто пары (следует за
  перекреплением — ОВ-6; авто удален/не привязан → car=null —
  корректное пустое состояние «—», не ошибка — MIN-3). Пусто → []
  (прежнее «Сегодня занятий нет»). Блокировка авто (MIN-2) виджет НЕ
  скрывает: существующие подтвержденные брони отображаются как прежде.

SQL — параметризованный (NFR-3); ФИО учеников не логируются (NFR-4).
"""
from fastapi import APIRouter, Header

import backend.db as db
from backend.booking import _car_brief, _pair_car, local_today
from backend.guards import full_name, require_role

router = APIRouter()


@router.get("/api/instructor/summary")
def instructor_summary(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Виджеты главной: «Привязанные ученики» + «Занятия на сегодня»."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT sr.student_id, sr.car_id, sr.decided_at"
            " FROM student_requests AS sr"
            " WHERE sr.instructor_id = ? AND sr.status = 'accepted'"
            " ORDER BY sr.decided_at, sr.id",
            (instructor_id,),
        ).fetchall()
        students = []
        for row in rows:
            student = conn.execute(
                "SELECT surname, name, patronymic FROM users WHERE id = ?",
                (row["student_id"],),
            ).fetchone()
            car = None
            if row["car_id"]:
                car_row = conn.execute(
                    "SELECT brand, model, year FROM instructor_cars"
                    " WHERE id = ?",
                    (row["car_id"],),
                ).fetchone()
                if car_row is not None:
                    car = " ".join(
                        part
                        for part in (
                            car_row["brand"],
                            car_row["model"],
                            str(car_row["year"]),
                        )
                        if part
                    )
            students.append({
                "student_id": row["student_id"],
                "full_name": full_name(student) if student else "",
                "car": car,
                "decided_at": row["decided_at"],
            })

        # Спринт 5 (задача 4.2, FR-49): подтвержденные брони на СЕГОДНЯ
        # (локальная дата сервера — MIN-1), заглушка FR-41 закрывается.
        today = local_today().isoformat()
        lesson_rows = conn.execute(
            "SELECT b.id, b.student_id, b.lesson_date,"
            " a.start_time, a.end_time"
            " FROM booking AS b JOIN availability AS a"
            " ON a.id = b.availability_id"
            " WHERE b.instructor_id = ? AND b.status = 'confirmed'"
            " AND b.lesson_date = ?"
            " ORDER BY a.start_time, b.id",
            (instructor_id, today),
        ).fetchall()
        today_lessons = []
        for row in lesson_rows:
            student = conn.execute(
                "SELECT surname, name, patronymic FROM users WHERE id = ?",
                (row["student_id"],),
            ).fetchone()
            today_lessons.append({
                "booking_id": row["id"],
                "student_full_name": full_name(student) if student else "",
                "lesson_date": row["lesson_date"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                # ОВ-6 (следует за перекреплением) + MIN-3 (удален → None);
                # MIN-2 (review-001): viewer="instructor" ЯВНО — инструктор-
                # виджет видит photo_url своего авто во всех статусах
                # (правило владельца в booking._car_brief), дефолт
                # 'student' здесь — шейп-мисматч.
                "car": _pair_car(
                    conn, row["student_id"], instructor_id or 0,
                    viewer="instructor",
                ),
            })
    finally:
        conn.close()
    return {
        "ok": True,
        "students": students,
        "today_lessons": today_lessons,
    }
