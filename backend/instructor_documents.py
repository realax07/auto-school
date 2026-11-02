"""instructor_documents.py — «Мои документы» инструктора (Спринт 5,
задача 3.1; Спринт 8 add-s8-cars-docs-booking — РАСШИРЕНИЕ: статусная
модель документов, задачи 1.1/2.1/3.1/4.1).

Домен instructor-documents владеет таблицей document_versions и правилами
версий (директива Заказчика по модульности: версии — внутри своего
домена, существующие модули не раздуваются).

GET /api/instructor/documents            — список СВОИХ документов (FR-45)
     + версии/статусы на каждый документ: active_version (действующая —
     последняя verified) / pending (ожидающая) / last_rejected (последняя
     отклоненная с причиной — ОВ-1);
GET /api/instructor/documents/{doc_id}/file — просмотр/скачивание файла
     ДЕЙСТВУЮЩЕЙ версии (контракт без изменений); чужой/несуществующий
     doc_id → 404 (не раскрываем);
POST /api/instructor/documents/license   — загрузка/замена ВУ (FR-71/72,
     multipart поле file): JPEG/PNG ≤5 МБ по magic bytes → иначе 422;
     ВСЕГДА создает pending-версию (первичная — досыл из FR-72, замена —
     FR-71); license_photo_path и действующая версия НЕ меняются до
     verify («документ не мигает», FR-70); повторная загрузка при
     pending ЗАМЕЩАЕТ ожидающую (файл + uploaded_at той же строки,
     version не растет — ОВ-7).

Админ-контур (X-Admin-Token, механика Спринта 0):
GET  /api/admin/documents?status=pending — версии по фильтру (default
     pending; pending/verified/rejected; иное → 422): тип, версия,
     uploaded_at; license — ФИО инструктора; car_sts — марка/модель/
     госномер авто и владелец; без токена → 401;
GET  /api/admin/documents/{version_id}/file — предпросмотр версии
     (image/*, ОВ-4); несуществующий → 404;
POST /api/admin/documents/{version_id}/verify — только pending → иначе
     409; версия verified, предыдущая verified остается в истории как
     архив, каноническая колонка (license_photo_path / photo_sts)
     переключается на файл версии — ОДНА транзакция; decided_at;
POST /api/admin/documents/{version_id}/reject — body {reason}: причина
     ОБЯЗАТЕЛЬНА (нет/пустая → 422 — ОВ-1); только pending → иначе 409;
     версия rejected с reject_reason, предыдущая verified ОСТАЕТСЯ
     действующей, каноническая колонка не меняется; decided_at.

Статусы документов НЕ влияют на статус авто и активность инструктора
(ОВ-3, NFR-23). Машина статусов: pending → verified | rejected; повторная
загрузка при pending замещает (ОВ-7); «отозвать pending» — точка
расширения.

doc_id — стабильная строка-идентификатор: 'license-<application_id>' /
'sts-<car_id>'; владелец документа вычисляется серверно на каждом
запросе (user_id → своя анкета по email / свое авто по instructor_id).

Даты (MIN-1): дата загрузки ВУ — created_at анкеты; дата СТС — created_at
авто (legacy-состав выдачи сохранен); у версий — свои uploaded_at/decided_at.

SQL — только параметризованный (NFR-10); документы/ФИО/причины отказов
не логируются (NFR-4).
"""
import datetime
import sqlite3
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

import backend.db as db
import backend.uploads as uploads
from backend.admin import require_admin
from backend.guards import _error, _unauthorized, full_name, require_role

router = APIRouter()

_NO_LICENSE_HINT = (
    "Заявка без фото ВУ: заполните анкету и загрузите водительское"
    " удостоверение"
)

_DOCUMENT_STATUSES = ("pending", "verified", "rejected")


def _utcnow() -> str:
    """Момент загрузки/решения (UTC, формат datetime('now') — MIN-1)."""
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# --- Правила-хелперы версий (задача 1.1) -------------------------------------


def _next_version(conn: sqlite3.Connection, target_type: str, target_id: int) -> int:
    """Следующий порядковый номер версии документа."""
    row = conn.execute(
        "SELECT COALESCE(MAX(version), 0) + 1 AS next_version"
        " FROM document_versions WHERE target_type = ? AND target_id = ?",
        (target_type, target_id),
    ).fetchone()
    return int(row["next_version"])


def document_versions_info(
    conn: sqlite3.Connection, target_type: str, target_id: int
) -> dict:
    """Версии/статусы одного документа: active_version — ДЕЙСТВУЮЩАЯ
    (последняя verified), pending — ожидающая, last_rejected — последняя
    отклоненная с причиной (ОВ-1). Нет версий → все None (легаси-строки
    без версий: каноническая колонка продолжает работать)."""
    info: dict[str, dict | None] = {
        "active_version": None,
        "pending": None,
        "last_rejected": None,
    }
    rows = conn.execute(
        "SELECT version, status, reject_reason, uploaded_at, decided_at"
        " FROM document_versions WHERE target_type = ? AND target_id = ?"
        " ORDER BY version",
        (target_type, target_id),
    ).fetchall()
    for row in rows:
        if row["status"] == "verified":
            # последняя verified → действует (предыдущие — архив)
            info["active_version"] = {
                "version": row["version"],
                "uploaded_at": row["uploaded_at"],
            }
        elif row["status"] == "pending":
            info["pending"] = {
                "version": row["version"],
                "uploaded_at": row["uploaded_at"],
            }
        else:  # rejected (CHECK гарантирует непустую причину — ОВ-1)
            info["last_rejected"] = {
                "version": row["version"],
                "reject_reason": row["reject_reason"],
                "decided_at": row["decided_at"],
            }
    return info


def create_or_replace_pending_version(
    conn: sqlite3.Connection, target_type: str, target_id: int, file_path: str
) -> dict:
    """Новая pending-версия документа; если ожидающая уже есть — она
    ЗАМЕЩАЕТСЯ (файл + uploaded_at той же строки, version не растет до
    верификации — ОВ-7). Вызывается ВНУТРИ транзакции вызывающего кода."""
    now = _utcnow()
    cur = conn.execute(
        "UPDATE document_versions SET file_path = ?, uploaded_at = ?"
        " WHERE target_type = ? AND target_id = ? AND status = 'pending'",
        (file_path, now, target_type, target_id),
    )
    if cur.rowcount:
        row = conn.execute(
            "SELECT version FROM document_versions"
            " WHERE target_type = ? AND target_id = ? AND status = 'pending'",
            (target_type, target_id),
        ).fetchone()
        return {
            "status": "pending",
            "version": int(row["version"]),
            "uploaded_at": now,
        }
    version = _next_version(conn, target_type, target_id)
    conn.execute(
        "INSERT INTO document_versions (target_type, target_id, version,"
        " file_path, status, uploaded_at)"
        " VALUES (?, ?, ?, ?, 'pending', ?)",
        (target_type, target_id, version, file_path, now),
    )
    return {"status": "pending", "version": version, "uploaded_at": now}


def create_verified_version(
    conn: sqlite3.Connection, target_type: str, target_id: int, file_path: str
) -> dict:
    """Первичный документ БЕЗ действующей версии (СТС-дозагрузка FR-69):
    verified сразу — двойная human-верификация одного файла не вводится
    (design.md «Первичная загрузка vs замена»). Вызывается ВНУТРИ
    транзакции вызывающего кода."""
    now = _utcnow()
    version = _next_version(conn, target_type, target_id)
    conn.execute(
        "INSERT INTO document_versions (target_type, target_id, version,"
        " file_path, status, uploaded_at, decided_at)"
        " VALUES (?, ?, ?, ?, 'verified', ?, ?)",
        (target_type, target_id, version, file_path, now, now),
    )
    return {"status": "verified", "version": version, "uploaded_at": now}


def active_version_file(
    conn: sqlite3.Connection, target_type: str, target_id: int
) -> str | None:
    """Файл ДЕЙСТВУЮЩЕЙ версии (последняя verified); версий нет → None —
    выдача падает обратно на каноническую колонку (совместимость с
    легаси-строками)."""
    row = conn.execute(
        "SELECT file_path FROM document_versions"
        " WHERE target_type = ? AND target_id = ? AND status = 'verified'"
        " ORDER BY version DESC LIMIT 1",
        (target_type, target_id),
    ).fetchone()
    return row["file_path"] if row is not None else None


# --- «Мои документы» (владелец-инструктор) -----------------------------------


def _license_document(
    conn: sqlite3.Connection, email: str
) -> dict | None:
    """ВУ текущего инструктора: анкета ищется по email (approve создает
    users из заявки — Спринт 2). Показ анкеты при наличии ВУ ИЛИ версий
    (первичная pending-загрузка видна с бейджем «Ожидает проверки»);
    нет ни того, ни другого → None (пустое состояние с подсказкой)."""
    row = conn.execute(
        "SELECT id, license_photo_path, license_number, created_at"
        " FROM instructor_applications WHERE email = ?",
        (email,),
    ).fetchone()
    if row is None:
        return None
    versions = document_versions_info(conn, "license", row["id"])
    if not row["license_photo_path"] and versions["pending"] is None:
        return None
    return {
        "doc_id": f"license-{row['id']}",
        "type": "license",
        "title": "Водительское удостоверение",
        "license_number": row["license_number"],
        "uploaded_at": row["created_at"],
    } | versions


def _sts_documents(conn: sqlite3.Connection, instructor_id: int) -> list[dict]:
    """СТС по каждому СВОЕМУ авто (привязка марка/модель/госномер, дата);
    авто БЕЗ СТС и без версий ЯВНО пропускаются (continue) — в «Мои
    документы» не попадают (видимы админу через completeness)."""
    rows = conn.execute(
        "SELECT id, brand, model, plate, photo_sts, created_at"
        " FROM instructor_cars WHERE instructor_id = ? ORDER BY id",
        (instructor_id,),
    ).fetchall()
    documents = []
    for row in rows:
        versions = document_versions_info(conn, "car_sts", row["id"])
        if not row["photo_sts"] and versions["pending"] is None:
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
        } | versions)
    return documents


@router.get("/api/instructor/documents")
def my_documents(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Список СВОИХ документов (FR-45 + Спринт 8): ВУ анкеты + СТС по
    каждому авто; на каждый документ — active_version / pending /
    last_rejected (бейджи «Ожидает проверки замены» и причины отказа,
    ОВ-1); чужая роль → 403; анкета без ВУ → пустое состояние ВУ с
    подсказкой."""
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


def _serve_document_file(path: str | None) -> Response | JSONResponse:
    """Выдача файла изображения (image/*); путь пуст или файл отсутствует
    на диске → 404 (не битая выдача)."""
    if not path:
        return _error(404, "Документ не найден")
    file_path = Path(path)
    if not file_path.is_file():
        return _error(404, "Документ не найден")
    return Response(
        content=file_path.read_bytes(),
        media_type=uploads.image_media_type(path),
    )


@router.get("/api/instructor/documents/{doc_id}/file")
def document_file(
    doc_id: str,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Файл документа (FR-45, NFR-7): только владельцу; выдается файл
    ДЕЙСТВУЮЩЕЙ версии (после seed-миграции — прежний файл, после verify —
    файл новой; легаси-строки без версий — каноническая колонка);
    чужой/неизвестный doc_id → 404 (не раскрываем); ученик → 403;
    гость → 401."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    kind, _, raw_id = doc_id.partition("-")
    if kind not in ("license", "sts") or not raw_id.isdigit():
        return _error(404, "Документ не найден")
    entity_id = int(raw_id)
    target_type = "license" if kind == "license" else "car_sts"

    conn = db.get_conn()
    try:
        path = active_version_file(conn, target_type, entity_id)
        if path is None:
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

    return _serve_document_file(path)


# --- Загрузка/замена ВУ (FR-71/FR-72) -----------------------------------------


async def _read_upload(
    request: Request, field: str
) -> "tuple[bytes, str] | JSONResponse":
    """Чтение и валидация файла из multipart-формы: (bytes, ext) при
    успехе; JSONResponse 422 (не multipart / нет файла / не JPEG-PNG /
    >5 МБ). Механика uploads.py без изменений (NFR-9)."""
    if not request.headers.get("content-type", "").startswith("multipart/form-data"):
        return _error(422, "Файл: поле обязательно")
    form = await request.form()
    value = form.get(field)
    if value is None or isinstance(value, str):
        return _error(422, "Файл: поле обязательно")
    content = await value.read()
    ext, error = uploads.sniff_image(content)
    if error is not None:
        return _error(422, error)
    return content, ext or "jpg"


@router.post("/api/instructor/documents/license")
async def upload_license_document(
    request: Request,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Загрузка/замена ВУ (FR-71/FR-72, задача 2.1): multipart поле file,
    JPEG/PNG ≤5 МБ по содержимому → иначе 422 (прежний файл не затронут).
    ВСЕГДА pending-версия (первичная — досыл FR-72; замена — FR-71,
    асимметрия с СТС задокументирована в design.md): license_photo_path и
    действующая версия НЕ меняются до verify; повторная загрузка при
    pending замещает ожидающую (ОВ-7). Ответ: {ok, document:{status,
    version, uploaded_at}}. Файл при сбое INSERT удаляется (NIT-4)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        user = conn.execute(
            "SELECT email FROM users WHERE id = ?", (instructor_id,)
        ).fetchone()
        row = conn.execute(
            "SELECT id FROM instructor_applications WHERE email = ?",
            (user["email"] if user else "",),
        ).fetchone()
        if row is None:
            return _error(404, "Анкета не найдена")
        application_id = int(row["id"])
    finally:
        conn.close()

    read = await _read_upload(request, "file")
    if isinstance(read, JSONResponse):
        return read
    content, ext = read
    path = uploads.save_image("license", content, ext)

    conn = db.get_conn()
    try:
        try:
            document = create_or_replace_pending_version(
                conn, "license", application_id, path
            )
        except sqlite3.Error:
            # NIT-4: сбой записи версии — файл не остается сиротой
            Path(path).unlink(missing_ok=True)
            raise
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "document": document}


# --- Админ-верификация документов (X-Admin-Token, ОВ-1/ОВ-4) ------------------


def _require_admin_token(
    x_admin_token: str | None,
) -> JSONResponse | None:
    """X-Admin-Token (механика Спринта 0): валиден → None, иначе 401."""
    try:
        require_admin(x_admin_token=x_admin_token or "")
    except HTTPException:
        return _unauthorized()
    return None


@router.get("/api/admin/documents")
def admin_documents(
    status: str = "pending",
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    """Версии документов по фильтру (default pending; pending/verified/
    rejected, иное → 422): тип, версия, uploaded_at, decided_at, причина
    отказа; license — ФИО инструктора (ФИО только из users, ADR-004;
    у заявки вне users — ФИО заявки), car_sts — марка/модель/госномер
    авто и владелец. Без/с неверным токеном → 401."""
    unauthorized = _require_admin_token(x_admin_token)
    if unauthorized is not None:
        return unauthorized
    if status not in _DOCUMENT_STATUSES:
        return _error(422, "Статус: укажите pending, verified или rejected")

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT id, target_type, target_id, version, status,"
            " reject_reason, uploaded_at, decided_at"
            " FROM document_versions WHERE status = ?"
            " ORDER BY uploaded_at DESC, id DESC",
            (status,),
        ).fetchall()
        documents = []
        for row in rows:
            item = {
                "id": row["id"],
                "target_type": row["target_type"],
                "target_id": row["target_id"],
                "version": row["version"],
                "status": row["status"],
                "uploaded_at": row["uploaded_at"],
                "decided_at": row["decided_at"],
                "reject_reason": row["reject_reason"],
                "instructor_full_name": "",
                "car": None,
            }
            if row["target_type"] == "license":
                app_row = conn.execute(
                    "SELECT surname, name, patronymic, email"
                    " FROM instructor_applications WHERE id = ?",
                    (row["target_id"],),
                ).fetchone()
                user_row = None
                if app_row is not None:
                    user_row = conn.execute(
                        "SELECT surname, name, patronymic FROM users"
                        " WHERE email = ?",
                        (app_row["email"],),
                    ).fetchone()
                fio_row = user_row if user_row is not None else app_row
                if fio_row is not None:
                    item["instructor_full_name"] = full_name(fio_row)
            else:
                car_row = conn.execute(
                    "SELECT id, brand, model, plate, instructor_id"
                    " FROM instructor_cars WHERE id = ?",
                    (row["target_id"],),
                ).fetchone()
                if car_row is not None:
                    item["car"] = {
                        "id": car_row["id"],
                        "brand": car_row["brand"],
                        "model": car_row["model"],
                        "plate": car_row["plate"],
                    }
                    owner_row = conn.execute(
                        "SELECT surname, name, patronymic FROM users"
                        " WHERE id = ?",
                        (car_row["instructor_id"],),
                    ).fetchone()
                    if owner_row is not None:
                        item["instructor_full_name"] = full_name(owner_row)
            documents.append(item)
    finally:
        conn.close()
    return {"ok": True, "documents": documents}


@router.get("/api/admin/documents/{version_id}/file")
def admin_document_file(
    version_id: int,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    """Предпросмотр версии (image/*, ОВ-4 — изображение открывается);
    несуществующая версия / файл на диске → 404. Без токена → 401."""
    unauthorized = _require_admin_token(x_admin_token)
    if unauthorized is not None:
        return unauthorized

    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT file_path FROM document_versions WHERE id = ?",
            (version_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return _error(404, "Версия не найдена")
    return _serve_document_file(row["file_path"])


@router.post("/api/admin/documents/{version_id}/verify")
def admin_verify_document(
    version_id: int,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    """Подтверждение версии (задача 4.1): только pending → иначе 409;
    несуществующая → 404. Эффект — ОДНА транзакция: версия verified
    (decided_at), предыдущая verified остается в истории как архив,
    каноническая колонка (license_photo_path / photo_sts) переключается
    на файл версии. Без токена → 401."""
    unauthorized = _require_admin_token(x_admin_token)
    if unauthorized is not None:
        return unauthorized

    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT id, target_type, target_id, version, status, file_path"
            " FROM document_versions WHERE id = ?",
            (version_id,),
        ).fetchone()
        if row is None:
            return _error(404, "Версия не найдена")
        if row["status"] != "pending":
            return _error(409, "Версия не ожидает проверки")
        cur = conn.execute(
            "UPDATE document_versions SET status = 'verified', decided_at = ?"
            " WHERE id = ? AND status = 'pending'",
            (_utcnow(), version_id),
        )
        if cur.rowcount == 0:
            # guard-WHERE (паттерн NIT-3): гонка check-then-act закрыта
            conn.rollback()
            return _error(409, "Версия не ожидает проверки")
        # Каноническая колонка переключается на файл версии; SQL — два
        # статических запроса (без конкатенаций — NFR-10, grep-контроль),
        # значения параметризованы.
        if row["target_type"] == "license":
            conn.execute(
                "UPDATE instructor_applications SET license_photo_path = ?"
                " WHERE id = ?",
                (row["file_path"], row["target_id"]),
            )
        else:
            conn.execute(
                "UPDATE instructor_cars SET photo_sts = ? WHERE id = ?",
                (row["file_path"], row["target_id"]),
            )
        conn.commit()
    finally:
        conn.close()
    return {
        "ok": True,
        "document": {
            "id": version_id,
            "target_type": row["target_type"],
            "target_id": row["target_id"],
            "version": row["version"],
            "status": "verified",
        },
    }


class RejectRequest(BaseModel):
    reason: str = ""


@router.post("/api/admin/documents/{version_id}/reject")
def admin_reject_document(
    version_id: int,
    data: RejectRequest | None = None,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    """Отклонение версии (задача 4.1, ОВ-1): body {reason} — причина
    ОБЯЗАТЕЛЬНА (нет поля/пустая/пробелы → 422); только pending → иначе
    409; несуществующая → 404. Эффект: версия rejected с reject_reason
    (decided_at), предыдущая verified ОСТАЕТСЯ действующей, каноническая
    колонка НЕ меняется (инструктор не остается без документа). Причина
    не логируется (NFR-4). Без токена → 401."""
    unauthorized = _require_admin_token(x_admin_token)
    if unauthorized is not None:
        return unauthorized

    reason = (data.reason if data is not None else "") or ""
    if not reason.strip():
        return _error(422, "Причина: поле обязательно")

    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT id, target_type, target_id, version, status"
            " FROM document_versions WHERE id = ?",
            (version_id,),
        ).fetchone()
        if row is None:
            return _error(404, "Версия не найдена")
        if row["status"] != "pending":
            return _error(409, "Версия не ожидает проверки")
        cur = conn.execute(
            "UPDATE document_versions SET status = 'rejected',"
            " reject_reason = ?, decided_at = ?"
            " WHERE id = ? AND status = 'pending'",
            (reason, _utcnow(), version_id),
        )
        if cur.rowcount == 0:
            conn.rollback()
            return _error(409, "Версия не ожидает проверки")
        # Каноническая колонка не меняется — предыдущая verified действует
        conn.commit()
    finally:
        conn.close()
    return {
        "ok": True,
        "document": {
            "id": version_id,
            "target_type": row["target_type"],
            "target_id": row["target_id"],
            "version": row["version"],
            "status": "rejected",
            "reject_reason": reason,
        },
    }
