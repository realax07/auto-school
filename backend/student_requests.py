"""student_requests.py — заявки учеников (задача 6.1, домен
student-requests; design.md блок 6 + arch-review итерация 2: MAJ-1, MAJ-2).

POST   /api/student/requests                     — подача (FR-36, ОВ-1/2)
GET    /api/student/requests                     — «Мои заявки» (FR-38)
GET    /api/instructor/requests                  — входящие (FR-37)
POST   /api/instructor/requests/{id}/accept      — принять (FR-39, ОВ-1/4)
POST   /api/instructor/requests/{id}/deny        — отказ (FR-38)
PATCH  /api/instructor/students/{id}/car         — перекрепление авто (MAJ-2)

Жизненный цикл (design.md): new → accepted (accept: car_id — авто ЭТОГО
инструктора → иначе 422; 0 авто → 409 «заведите автомобиль», ОВ-4);
new → denied (deny: комментарий обязателен → 422). Повторная заявка после
отказа — допустима (ОВ-2); дубликат активной (new/accepted) заявки этому
же инструктору → 409 без записи (FR-36).

ОВ-1 (MAJ-1, итерация 2): accept закрывает ВСЕ остальные АКТИВНЫЕ
('new' И 'accepted') заявки ученика → denied с системным deny_comment
«Заявка закрыта: ученик принят другим инструктором» — одна транзакция.

Гонки (code-review review-001 #6/#7): дубликат активной заявки защищен
частичным UNIQUE-индексом uq_student_requests_active (db.py) +
IntegrityError → 409; переходы accept/deny — UPDATE … WHERE id=? AND
status='new' с проверкой rowcount (0 → 409 «решение уже принято»),
молчаливой перезаписи статуса нет.

Системный отказ и комментарии решений видны ученику в «Моих заявках»
(FR-38). SQL — параметризованный (NFR-3); ФИО учеников не логируются
(NFR-4).
"""
import sqlite3

from fastapi import APIRouter, Header
from pydantic import BaseModel

import backend.db as db
from backend.guards import _error, full_name, require_role

router = APIRouter()

_SYSTEM_DENY_COMMENT = "Заявка закрыта: ученик принят другим инструктором"

_ACTIVE_STATUSES = ("new", "accepted")


class CreateRequestPayload(BaseModel):
    # Дефолты вместо Pydantic-required — валидация в хендлере.
    instructor_id: int = 0


class AcceptPayload(BaseModel):
    car_id: int = 0


class DenyPayload(BaseModel):
    comment: str = ""


class AssignCarPayload(BaseModel):
    car_id: int = 0


def _fetch_request(conn: sqlite3.Connection, request_id: int):
    return conn.execute(
        "SELECT id, student_id, instructor_id, status, deny_comment, car_id,"
        " created_at, decided_at FROM student_requests WHERE id = ?",
        (request_id,),
    ).fetchone()


def _car_brief(conn: sqlite3.Connection, car_id: int | None) -> dict | None:
    """Краткие данные авто для карточек/списков (без госномера и фото)."""
    if not car_id:
        return None
    row = conn.execute(
        "SELECT id, brand, model, year, transmission FROM instructor_cars"
        " WHERE id = ?",
        (car_id,),
    ).fetchone()
    return dict(row) if row is not None else None


# --- Ученик -----------------------------------------------------------------


@router.post("/api/student/requests")
def create_request(
    data: CreateRequestPayload,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Подача заявки (FR-36): цель — одобренный инструктор → иначе 404;
    активная (new/accepted) заявка этому инструктору → 409 без записи;
    повторная после отказа — создается (ОВ-2); параллельные заявки разным
    инструкторам — допустимы (ОВ-1)."""
    student_id, err = require_role(x_session_token, "student")
    if err is not None:
        return err
    if data.instructor_id <= 0:
        return _error(422, "Инструктор: поле обязательно")

    conn = db.get_conn()
    try:
        instructor = conn.execute(
            "SELECT id FROM users WHERE id = ? AND role = 'instructor'",
            (data.instructor_id,),
        ).fetchone()
        if instructor is None:
            return _error(404, "Инструктор не найден")

        duplicate = conn.execute(
            "SELECT 1 FROM student_requests"
            " WHERE student_id = ? AND instructor_id = ? AND status IN (?, ?)",
            (student_id, data.instructor_id, *_ACTIVE_STATUSES),
        ).fetchone()
        if duplicate is not None:
            return _error(409, "Заявка: активная заявка этому инструктору уже есть")

        # Гонка дубликата (review-001 #6): параллельный POST может пройти
        # SELECT выше — частичный UNIQUE-индекс uq_student_requests_active
        # (db.py) роняет второй INSERT; IntegrityError → 409 без записи
        # (по образцу reviews.py).
        try:
            cur = conn.execute(
                "INSERT INTO student_requests (student_id, instructor_id, status)"
                " VALUES (?, ?, 'new')",
                (student_id, data.instructor_id),
            )
        except sqlite3.IntegrityError:
            conn.rollback()
            return _error(409, "Заявка: активная заявка этому инструктору уже есть")
        request_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "request_id": request_id}


@router.get("/api/student/requests")
def my_requests(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """«Мои заявки» ученика (FR-38): статус, дата, инструктор,
    deny_comment (включая системный при автозакрытии)."""
    student_id, err = require_role(x_session_token, "student")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT id, instructor_id, status, deny_comment, car_id,"
            " created_at, decided_at FROM student_requests"
            " WHERE student_id = ? ORDER BY id DESC",
            (student_id,),
        ).fetchall()
        requests = []
        for row in rows:
            instructor = conn.execute(
                "SELECT surname, name, patronymic FROM users WHERE id = ?",
                (row["instructor_id"],),
            ).fetchone()
            requests.append({
                "id": row["id"],
                "status": row["status"],
                "created_at": row["created_at"],
                "decided_at": row["decided_at"],
                "deny_comment": row["deny_comment"],
                "instructor_full_name": full_name(instructor) if instructor else "",
                "car": _car_brief(conn, row["car_id"]),
            })
    finally:
        conn.close()
    return {"ok": True, "requests": requests}


# --- Инструктор -------------------------------------------------------------


@router.get("/api/instructor/requests")
def incoming_requests(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Входящие заявки ТОЛЬКО этого инструктора (FR-37): ученик (ФИО),
    дата, статус; чужие заявки не видны."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT id, student_id, status, car_id, created_at, decided_at"
            " FROM student_requests WHERE instructor_id = ?"
            " ORDER BY CASE status WHEN 'new' THEN 0 ELSE 1 END, id DESC",
            (instructor_id,),
        ).fetchall()
        requests = []
        for row in rows:
            student = conn.execute(
                "SELECT surname, name, patronymic, experience_years"
                " FROM users WHERE id = ?",
                (row["student_id"],),
            ).fetchone()
            requests.append({
                "id": row["id"],
                "status": row["status"],
                "created_at": row["created_at"],
                "decided_at": row["decided_at"],
                "student_full_name": full_name(student) if student else "",
                # FR-37 (design.md блок 6): стаж ученика в ответе
                # (review-001 #3 — SELECT выполнялся, поле терялось)
                "student_experience_years": (
                    student["experience_years"] if student is not None else 0
                ),
                "car": _car_brief(conn, row["car_id"]),
            })
    finally:
        conn.close()
    return {"ok": True, "requests": requests}


@router.post("/api/instructor/requests/{request_id}/accept")
def accept_request(
    request_id: int,
    data: AcceptPayload | None = None,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Принять заявку (FR-39): только своя и 'new' → иначе 404/409;
    0 авто → 409 «заведите автомобиль» (ОВ-4); car_id — авто этого
    инструктора → иначе 422. Эффект (ОВ-1, MAJ-1): статус accepted + car_id;
    остальные АКТИВНЫЕ ('new' и 'accepted') заявки ученика → denied с
    системным комментарием — одна транзакция."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        row = _fetch_request(conn, request_id)
        if row is None or row["instructor_id"] != instructor_id:
            return _error(404, "Заявка не найдена")
        if row["status"] != "new":
            return _error(409, "Заявка: решение уже принято")

        cars_count = conn.execute(
            "SELECT COUNT(*) AS cnt FROM instructor_cars WHERE instructor_id = ?",
            (instructor_id,),
        ).fetchone()["cnt"]
        if cars_count == 0:
            # ОВ-4: принятие недоступно до заведения автомобиля
            return _error(409, "Заведите автомобиль, чтобы принять ученика")

        car_id = data.car_id if data is not None else 0
        car = conn.execute(
            "SELECT id FROM instructor_cars WHERE id = ? AND instructor_id = ?",
            (car_id, instructor_id),
        ).fetchone()
        if car is None:
            return _error(422, "Автомобиль: выберите автомобиль этого инструктора")

        # ОВ-1 (MAJ-1) — одна транзакция: принятие + автозакрытие остальных
        # АКТИВНЫХ ('new' и 'accepted') заявок ученика с системным комментарием
        # Гонка перехода статуса (review-001 #7): guard AND status='new' в
        # WHERE + rowcount — интерливинг accept/deny не перезаписывает
        # молча уже выставленное решение (0 строк → 409).
        cur = conn.execute(
            "UPDATE student_requests SET status = 'accepted', car_id = ?,"
            " decided_at = datetime('now') WHERE id = ? AND status = 'new'",
            (car_id, request_id),
        )
        if cur.rowcount == 0:
            return _error(409, "Заявка: решение уже принято")
        conn.execute(
            "UPDATE student_requests SET status = 'denied',"
            " deny_comment = ?, decided_at = datetime('now')"
            " WHERE student_id = ? AND id != ? AND status IN (?, ?)",
            (
                _SYSTEM_DENY_COMMENT,
                row["student_id"],
                request_id,
                *_ACTIVE_STATUSES,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


@router.post("/api/instructor/requests/{request_id}/deny")
def deny_request(
    request_id: int,
    data: DenyPayload | None = None,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Отказ (FR-38): только своя и 'new' → иначе 404/409; комментарий
    обязателен (пустой/отсутствующий → 422, действие заблокировано,
    статус остается 'new'); эффект: denied + deny_comment, видный ученику."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    comment = (data.comment if data is not None else "") or ""
    if not comment.strip():
        # Отказ без комментария заблокирован (FR-38, specs/student-requests)
        return _error(422, "Комментарий: поле обязательно")

    conn = db.get_conn()
    try:
        row = _fetch_request(conn, request_id)
        if row is None or row["instructor_id"] != instructor_id:
            return _error(404, "Заявка не найдена")
        if row["status"] != "new":
            return _error(409, "Заявка: решение уже принято")

        # Гонка перехода статуса (review-001 #7): guard AND status='new'
        # в WHERE + rowcount — молчаливой перезаписи решения нет.
        cur = conn.execute(
            "UPDATE student_requests SET status = 'denied', deny_comment = ?,"
            " decided_at = datetime('now') WHERE id = ? AND status = 'new'",
            (comment.strip(), request_id),
        )
        if cur.rowcount == 0:
            return _error(409, "Заявка: решение уже принято")
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


@router.patch("/api/instructor/students/{student_id}/car")
def assign_student_car(
    student_id: int,
    data: AssignCarPayload,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Перекрепление авто принятого ученика (ОВ-3, MAJ-2 arch-review
    итерация 2): ученик должен быть принят ЭТОМУ инструктору → иначе 404;
    car_id — авто этого инструктора → иначе 422; связь не меняется."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        link = conn.execute(
            "SELECT id FROM student_requests"
            " WHERE student_id = ? AND instructor_id = ? AND status = 'accepted'",
            (student_id, instructor_id),
        ).fetchone()
        if link is None:
            return _error(404, "Принятый ученик не найден")

        car = conn.execute(
            "SELECT id FROM instructor_cars WHERE id = ? AND instructor_id = ?",
            (data.car_id, instructor_id),
        ).fetchone()
        if car is None:
            return _error(422, "Автомобиль: выберите автомобиль этого инструктора")

        conn.execute(
            "UPDATE student_requests SET car_id = ? WHERE id = ?",
            (data.car_id, link["id"]),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}
