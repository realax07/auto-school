"""instructor_summary.py — виджеты главной кабинета инструктора (задача
6.2; design.md блок 6, FR-40, FR-41).

GET /api/instructor/summary:
- students — принятые ученики (student_requests.status='accepted'):
  ФИО, авто, дата принятия; «новые» заявки в виджет не попадают,
  пустой список — корректное пустое состояние (FR-40);
- today_lessons — всегда [] (честная заглушка: реального расписания
  занятий нет, «Сегодня занятий нет» — FR-41, design.md «Сознательные
  ограничения»).

SQL — параметризованный (NFR-3); ФИО учеников не логируются (NFR-4).
"""
from fastapi import APIRouter, Header

import backend.db as db
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
    finally:
        conn.close()
    return {
        "ok": True,
        "students": students,
        "today_lessons": [],
    }
