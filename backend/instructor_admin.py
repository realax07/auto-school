"""Модерация заявок инструктора (sdd.md §15.2–§15.4, задача 2.1).

X-Admin-Token / require_admin — как admin.py (§3.5); 401 тело —
{"ok": false}. GET списка — все данные анкеты БЕЗ password_hash
(решение Заказчика 2026-10-12-hash-not-rendered, MIN-5), сортировка
created_at DESC, id DESC. approve — ОДНА транзакция (MIN-3): INSERT users
с хэшем ИЗ ЗАЯВКИ (без повторного хэширования, FR-11.1, role='instructor')
+ UPDATE статуса; IntegrityError от UNIQUE users.email → 409. deny — guard
статуса (MIN-1) + обязательный комментарий (FR-15).
"""
import sqlite3
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

import backend.db as db
import backend.uploads as uploads
from backend.admin import require_admin

router = APIRouter()

# Порядок и состав ключей ответа GET — sdd §15.2; password_hash в ответ
# не входит (MIN-5: ключ отсутствует, а не пуст).
_APPLICATION_FIELDS = (
    "id",
    "surname",
    "name",
    "patronymic",
    "email",
    "phone",
    "address",
    "work_format",
    "plate",
    "license_number",
    "license_date",
    "license_category",
    "experience",
    "status",
    "review_comment",
    "created_at",
)


def _unauthorized() -> JSONResponse:
    return JSONResponse(status_code=401, content={"ok": False})


def _json(status: int, body: dict) -> JSONResponse:
    return JSONResponse(status_code=status, content=body)


class DenyRequest(BaseModel):
    comment: str = ""


def _fetch_application(conn, application_id: int):
    return conn.execute(
        "SELECT id, email, surname, name, patronymic, phone, password_hash,"
        " experience_years, status FROM instructor_applications WHERE id = ?",
        (application_id,),
    ).fetchone()


@router.get("/api/admin/instructor-applications")
def instructor_applications(
    x_admin_token: str | None = Header(default=None)
):
    try:
        require_admin(x_admin_token=x_admin_token)
    except HTTPException:
        return _unauthorized()

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT id, surname, name, patronymic, email, phone, address,"
            " work_format, plate, license_number, license_date,"
            " license_category, experience, status, review_comment, created_at"
            " FROM instructor_applications ORDER BY created_at DESC, id DESC"
        ).fetchall()
    finally:
        conn.close()

    applications = [{field: row[field] for field in _APPLICATION_FIELDS} for row in rows]
    return {"count": len(applications), "applications": applications}


@router.post("/api/admin/instructor-applications/{application_id}/approve")
def instructor_application_approve(
    application_id: int,
    x_admin_token: str | None = Header(default=None),
):
    try:
        require_admin(x_admin_token=x_admin_token)
    except HTTPException:
        return _unauthorized()

    conn = db.get_conn()
    try:
        app_row = _fetch_application(conn, application_id)
        if app_row is None:
            return _json(404, {"ok": False, "error": "Заявка не найдена"})
        # guard статуса: операция — только над waiting (иначе повторный
        # approve после deny дал бы дублирующую запись users)
        if app_row["status"] != "waiting":
            return _json(409, {"ok": False, "error": "Заявка уже одобрена"})

        try:
            # ОДНА транзакция (MIN-3): INSERT users с хэшем ИЗ ЗАЯВКИ
            # (без повторного хэширования, FR-11.1) + UPDATE статуса,
            # commit один — симметрично register.py.
            cur = conn.execute(
                "INSERT INTO users (surname, name, patronymic, email, phone,"
                " password_hash, role, experience_years)"
                " VALUES (?, ?, ?, ?, ?, ?, 'instructor', ?)",
                (
                    app_row["surname"],
                    app_row["name"],
                    app_row["patronymic"],
                    app_row["email"],
                    app_row["phone"],
                    app_row["password_hash"],
                    # MAJ-3 (arch-review итерация 2): стаж переносится при
                    # approve; NULL анкеты → 0.
                    app_row["experience_years"] if app_row["experience_years"] is not None else 0,
                ),
            )
            user_id = cur.lastrowid  # research.md §3
            conn.execute(
                "UPDATE instructor_applications SET status = 'approved'"
                " WHERE id = ?",
                (application_id,),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # гонка дубля email (users.email UNIQUE, FR-16): транзакция
            # откатывается, заявка остается waiting
            conn.rollback()
            return _json(409, {"ok": False, "error": "Email: уже зарегистрирован"})
    finally:
        conn.close()
    return {"ok": True, "user_id": user_id}


@router.post("/api/admin/instructor-applications/{application_id}/deny")
def instructor_application_deny(
    application_id: int,
    data: DenyRequest | None = None,
    x_admin_token: str | None = Header(default=None),
):
    try:
        require_admin(x_admin_token=x_admin_token)
    except HTTPException:
        return _unauthorized()

    # комментарий обязателен (FR-15): пустой/отсутствующий → 422
    # (отсутствующее тело приравнено к пустому комментарию)
    comment = (data.comment if data is not None else "") or ""
    if not comment.strip():
        return _json(422, {"ok": False, "error": "Комментарий: поле обязательно"})

    conn = db.get_conn()
    try:
        app_row = _fetch_application(conn, application_id)
        if app_row is None:
            return _json(404, {"ok": False, "error": "Заявка не найдена"})
        # guard статуса (MIN-1, симметрично approve): только waiting;
        # повторный deny не меняет сохраненную причину
        if app_row["status"] == "approved":
            return _json(409, {"ok": False, "error": "Заявка уже одобрена"})
        if app_row["status"] == "deny":
            return _json(409, {"ok": False, "error": "Заявка уже отклонена"})

        conn.execute(
            "UPDATE instructor_applications SET status = 'deny',"
            " review_comment = ? WHERE id = ?",
            (comment, application_id),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


# --- Спринт 3 (add-instructor-student-loop, задача 1.2): карточка заявки ---
# и выдача изображения ВУ — только по валидному X-Admin-Token (FR-24, NFR-1).


@router.get("/api/admin/instructor-applications/{application_id}")
def instructor_application_card(
    application_id: int,
    x_admin_token: str | None = Header(default=None),
):
    """Полные данные заявки + факт/путь ВУ (FR-25); 404 при отсутствии
    (чужой объект не отличим от несуществующего)."""
    try:
        require_admin(x_admin_token=x_admin_token)
    except HTTPException:
        return _unauthorized()

    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT id, surname, name, patronymic, email, phone, address,"
            " work_format, plate, license_number, license_date,"
            " license_category, experience, experience_years, status,"
            " review_comment, created_at, license_photo_path"
            " FROM instructor_applications WHERE id = ?",
            (application_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return _json(404, {"ok": False, "error": "Заявка не найдена"})
    application = {field: row[field] for field in row.keys()}
    return {"ok": True, "application": application}


@router.get("/api/admin/instructor-applications/{application_id}/license-image")
def instructor_application_license_image(
    application_id: int,
    x_admin_token: str | None = Header(default=None),
):
    """Изображение ВУ (FR-24, NFR-1): только валидный X-Admin-Token;
    без/с неверным токеном — 401, изображение не возвращается; заявка
    без ВУ (или несуществующая) — 404. Content-Type — image/jpeg|image/png
    по сохраненному файлу (uploads.image_media_type)."""
    try:
        require_admin(x_admin_token=x_admin_token)
    except HTTPException:
        return _unauthorized()

    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT license_photo_path FROM instructor_applications"
            " WHERE id = ?",
            (application_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return _json(404, {"ok": False, "error": "Заявка не найдена"})
    path = row["license_photo_path"]
    if not path:
        return _json(404, {"ok": False, "error": "ВУ не загружено"})
    file_path = Path(path)
    if not file_path.is_file():
        # Файл-сирота (cleanup вне скоупа, MIN-3 arch-review) — 404.
        return _json(404, {"ok": False, "error": "ВУ не загружено"})
    return Response(
        content=file_path.read_bytes(),
        media_type=uploads.image_media_type(path),
    )
