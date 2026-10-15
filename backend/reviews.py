"""reviews.py — отзывы учеников (задача 5.1, домен reviews; design.md
блок 5).

POST /api/student/instructors/{id}/reviews — сессия + role='student';
СЕРВЕРНАЯ проверка связи «ученик принят» (SELECT student_requests:
student, instructor, status='accepted' — NFR-2, UI-скрытие проверкой не
считается) → иначе 403, отзыв не создается. rating — int 1..5, text —
непустой ≤1000 знаков → иначе 422. Повторный отзыв — UNIQUE
(instructor_id, student_id) в DDL + IntegrityError → 409 (NFR-5).

SQL — параметризованный (NFR-3).
"""
import sqlite3

from fastapi import APIRouter, Header
from pydantic import BaseModel

import backend.db as db
from backend.guards import _error, require_role

router = APIRouter()

_MAX_REVIEW_TEXT = 1000


class ReviewPayload(BaseModel):
    # Дефолты вместо Pydantic-required — валидация в хендлере.
    rating: int = 0
    text: str = ""


@router.post("/api/student/instructors/{instructor_id}/reviews")
def create_review(
    instructor_id: int,
    data: ReviewPayload,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Отзыв инструктору (FR-34): связь → иначе 403; rating/text → 422;
    повторный → 409."""
    student_id, err = require_role(x_session_token, "student")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        # Цель — одобренный инструктор (role='instructor'); несуществующий
        # или неодобренный → 404 (не раскрываем существование)
        instructor = conn.execute(
            "SELECT id FROM users WHERE id = ? AND role = 'instructor'",
            (instructor_id,),
        ).fetchone()
        if instructor is None:
            return _error(404, "Инструктор не найден")

        # СЕРВЕРНАЯ проверка связи «принят» (NFR-2, FR-34): параметризо-
        # ванный SELECT к student_requests при каждом POST
        link = conn.execute(
            "SELECT 1 FROM student_requests"
            " WHERE student_id = ? AND instructor_id = ? AND status = 'accepted'",
            (student_id, instructor_id),
        ).fetchone()
        if link is None:
            return _error(
                403, "Отзыв: доступен только ученикам, принятым инструктором"
            )

        # Валидация полей (FR-34): rating int 1..5, text непустой ≤1000
        if data.rating < 1 or data.rating > 5:
            return _error(422, "Оценка: целое число от 1 до 5")
        text = data.text.strip()
        if not text:
            return _error(422, "Текст: поле обязательно")
        if len(text) > _MAX_REVIEW_TEXT:
            return _error(422, f"Текст: не более {_MAX_REVIEW_TEXT} знаков")

        try:
            conn.execute(
                "INSERT INTO reviews (instructor_id, student_id, rating, text)"
                " VALUES (?, ?, ?, ?)",
                (instructor_id, student_id, data.rating, text),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # UNIQUE(instructor_id, student_id) — повторный отзыв (NFR-5)
            return _error(409, "Отзыв: вы уже оставляли отзыв этому инструктору")
    finally:
        conn.close()
    return {"ok": True}
