"""instructor_documents.py — «Мои документы» инструктора (Спринт 5,
задача 3.1; design.md блок B, домен instructor-documents — НОВЫЙ модуль).

GET /api/instructor/documents            — список СВОИХ документов (FR-45):
     ВУ из instructor_applications (license_photo_path; анкета без ВУ →
     пустое состояние с подсказкой, досыл вне объема) + СТС по каждому
     своему авто (тип, привязка марка/модель/госномер, дата загрузки);
GET /api/instructor/documents/{doc_id}/file — просмотр/скачивание
     (один авторизованный эндпоинт, Content-Type image/*, FR-45, NFR-7):
     чужой/несуществующий doc_id → 404 (не раскрываем).

doc_id — стабильная строка-идентификатор: 'license-<application_id>' /
'sts-<car_id>'; владелец документа вычисляется серверно на каждом
запросе (user_id → своя анкета по email / свое авто по instructor_id).

Даты (MIN-1): дата загрузки ВУ — created_at анкеты; дата СТС — created_at
авто (СТС обязателен при создании авто — FR-44, поэтому для авто нового
контура запись авто и есть момент загрузки СТС).

SQL — только параметризованный (NFR-10); документы/ФИО не логируются.
"""
import sqlite3
from pathlib import Path

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse, Response

import backend.db as db
import backend.uploads as uploads
from backend.guards import _error, require_role

router = APIRouter()

_NO_LICENSE_HINT = (
    "Заявка без фото ВУ: заполните анкету и загрузите водительское"
    " удостоверение"
)


def _license_document(
    conn: sqlite3.Connection, email: str
) -> dict | None:
    """ВУ текущего инструктора: анкета ищется по email (approve создает
    users из заявки — Спринт 2). Нет анкеты / анкета без ВУ → None
    (пустое состояние с подсказкой, FR-45)."""
    row = conn.execute(
        "SELECT id, license_photo_path, license_number, created_at"
        " FROM instructor_applications WHERE email = ?",
        (email,),
    ).fetchone()
    if row is None or not row["license_photo_path"]:
        return None
    return {
        "doc_id": f"license-{row['id']}",
        "type": "license",
        "title": "Водительское удостоверение",
        "license_number": row["license_number"],
        "uploaded_at": row["created_at"],
    }


def _sts_documents(conn: sqlite3.Connection, instructor_id: int) -> list[dict]:
    """СТС по каждому СВОЕМУ авто (привязка марка/модель/госномер, дата);
    авто БЕЗ СТС (легаси-JSON-путь Спринта 3) ЯВНО пропускаются (continue)
    — в «Мои документы» не попадают (видимы админу через completeness)."""
    rows = conn.execute(
        "SELECT id, brand, model, plate, photo_sts, created_at"
        " FROM instructor_cars WHERE instructor_id = ? ORDER BY id",
        (instructor_id,),
    ).fetchall()
    documents = []
    for row in rows:
        if not row["photo_sts"]:
            continue
        documents.append({
            "doc_id": f"sts-{row['id']}",
            "type": "car_sts",
            "title": "СТС автомобиля",
            "car": {
                "id": row["id"],
                "brand": row["brand"],
                "model": row["model"],
                "plate": row["plate"],
            },
            "uploaded_at": row["created_at"],
        })
    return documents


@router.get("/api/instructor/documents")
def my_documents(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Список СВОИХ документов (FR-45): ВУ анкеты + СТС по каждому авто;
    чужая роль → 403; анкета без ВУ → пустое состояние ВУ с подсказкой."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        user = conn.execute(
            "SELECT email FROM users WHERE id = ?", (instructor_id,)
        ).fetchone()
        license_doc = _license_document(conn, user["email"] if user else "")
        documents: list[dict] = []
        if license_doc is not None:
            documents.append(license_doc)
        documents.extend(_sts_documents(conn, instructor_id or 0))
    finally:
        conn.close()
    return {
        "ok": True,
        "documents": documents,
        "license": license_doc,
        "license_hint": None if license_doc is not None else _NO_LICENSE_HINT,
    }


@router.get("/api/instructor/documents/{doc_id}/file")
def document_file(
    doc_id: str,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Файл документа (FR-45, NFR-7): только владельцу; чужой/неизвестный
    doc_id → 404 (не раскрываем); ученик → 403; гость → 401. Просмотр и
    скачивание — один и тот же авторизованный эндпоинт (Content-Type
    image/*; Content-Disposition — деталь клиента)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    kind, _, raw_id = doc_id.partition("-")
    if kind not in ("license", "sts") or not raw_id.isdigit():
        return _error(404, "Документ не найден")
    entity_id = int(raw_id)

    conn = db.get_conn()
    try:
        path: str | None = None
        if kind == "license":
            user = conn.execute(
                "SELECT email FROM users WHERE id = ?", (instructor_id,)
            ).fetchone()
            row = conn.execute(
                "SELECT license_photo_path FROM instructor_applications"
                " WHERE id = ? AND email = ?",
                (entity_id, user["email"] if user else ""),
            ).fetchone()
            path = row["license_photo_path"] if row is not None else None
        else:
            row = conn.execute(
                "SELECT photo_sts FROM instructor_cars"
                " WHERE id = ? AND instructor_id = ?",
                (entity_id, instructor_id),
            ).fetchone()
            path = row["photo_sts"] if row is not None else None
    finally:
        conn.close()

    if not path:
        return _error(404, "Документ не найден")
    file_path = Path(path)
    if not file_path.is_file():
        return _error(404, "Документ не найден")
    return Response(
        content=file_path.read_bytes(),
        media_type=uploads.image_media_type(path),
    )
