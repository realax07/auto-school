"""Спринт 8 — BACKEND-тесты (change add-s8-cars-docs-booking; backend-волна:
задачи 1.1, 2.1, 3.1, 4.1 + баг 5.2 регресс).

Покрывают:
- миграция document_versions (idempotent; seed verified v1 существующих
  ВУ/СТС legacy-БД; частичный UNIQUE — одна pending на документ, ОВ-7;
  CHECK «rejected ⇒ причина непуста», ОВ-1) — TC-S8BE-001;
- жизненный цикл версий ВУ: загрузка → pending (license_photo_path и
  файл эндпоинта не меняются — «документ не мигает»), reject без
  причины/с пустой → 422 (ОВ-1), reject с причиной → last_rejected
  виден инструктору, предыдущая версия действует, повторная загрузка →
  новая pending, verify → verified + переключение license_photo_path,
  старая verified — архив; не-pending → 409 — TC-S8BE-002;
- одна pending на документ (повторная загрузка замещает ожидающую,
  version не растет — ОВ-7) — TC-S8BE-002/003;
- СТС: первичная дозагрузка авто без СТС → photo_sts + verified v1
  (FR-69); замена → pending-версия, photo_sts не перезаписывается,
  повторная замещает (ОВ-7); админ pending-список с ФИО/авто+госномером,
  предпросмотр версии, verify переключает photo_sts — TC-S8BE-003;
- ОВ-6: замена СТС у validated НЕ сбрасывает валидацию авто (validated
  остается validated), замена ракурса → validating (MAJ-1 только 5
  ракурсов) — TC-S8BE-004;
- доступ (NFR-22): админ-контур только X-Admin-Token (401), ученик →
  403, гость → 401, чужой документ → 404-неразличение, несуществующая
  версия → 404, недопустимый фильтр статуса → 422 — TC-S8BE-005;
- «Мои документы»: версии/статусы на каждый документ (active_version /
  pending / last_rejected), пустое состояние ВУ без версий сохранено —
  TC-S8BE-006;
- баг 5.2 регресс: список авто выдает URL авторизованных фото-эндпоинтов
  (photos{angle}, sts_url), без файловых путей — плитки переживают
  повторный вход — TC-S8BE-007.

Трассировка TC-S8BE-NNN в docstring каждого теста (rule 6). Тесты
tests/test_s5_backend.py НЕ изменялись. Фикстуры — общий client из
conftest; каталог загрузок — env AUTOSCHOOL_UPLOADS_DIR в tmp_path;
time.sleep запрещен (спека qa-pipeline).
"""
import sqlite3
from pathlib import Path

import pytest

from conftest import admin_headers, db_path, register

ROOT_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
ROOT_PNG = b"\x89PNG\r\n\x1a\x0a" + b"\x00" * 64
ROOT_JPEG2 = b"\xff\xd8\xff\xe1" + b"\x11" * 64
ROOT_PDF = b"%PDF-1.4\nfake-pdf\n"

INSTR_PASSWORD = "Instr1234"


@pytest.fixture()
def api(client, monkeypatch, tmp_path):
    """client + каталог загрузок в tmp_path (NFR-1: вне frontend/)."""
    monkeypatch.setenv("AUTOSCHOOL_UPLOADS_DIR", str(tmp_path / "uploads"))
    return client


# --- helpers -----------------------------------------------------------------


def _headers(token):
    return {"X-Session-Token": token}


def apply_body(**overrides):
    body = {
        "surname": "Иванов",
        "name": "Иван",
        "patronymic": "Иванович",
        "phone": "+7 (911) 222-33-44",
        "email": "instr@example.com",
        "address": "г. Тест, ул. Полевая, 1",
        "work_format": "sber",
        "license_number": "9911223344",
        "license_category": "B",
        "experience_years": 5,
        "password": INSTR_PASSWORD,
        "password_confirm": INSTR_PASSWORD,
        "consent": True,
    }
    body.update(overrides)
    return body


def create_instructor(client, email="instr@example.com"):
    resp = client.post("/api/instructors/apply", json=apply_body(email=email))
    assert resp.status_code == 200, resp.text
    conn = sqlite3.connect(db_path())
    app_id = conn.execute(
        "SELECT id FROM instructor_applications WHERE email = ?", (email,)
    ).fetchone()[0]
    conn.close()
    approved = client.post(
        f"/api/admin/instructor-applications/{app_id}/approve",
        headers=admin_headers(client),
    )
    assert approved.status_code == 200, approved.text
    user_id = approved.json()["user_id"]
    login = client.post(
        "/api/auth/login", json={"email": email, "password": INSTR_PASSWORD}
    )
    assert login.status_code == 200, login.text
    return {
        "token": login.json()["token"],
        "id": user_id,
        "email": email,
        "application_id": app_id,
    }


def create_student(client, email="student@example.com"):
    resp = register(client, email=email)
    assert resp.status_code == 200, resp.text
    conn = sqlite3.connect(db_path())
    user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", (email,)
    ).fetchone()[0]
    conn.close()
    login = client.post(
        "/api/auth/login", json={"email": email, "password": "Qwerty123"}
    )
    assert login.status_code == 200, login.text
    return {"token": login.json()["token"], "id": user_id, "email": email}


def add_car_json(client, token, **overrides):
    """Создание авто JSON-путем (совместимость Спринта 3 — без СТС)."""
    payload = {
        "brand": "Škoda",
        "model": "Rapid",
        "year": 2020,
        "plate": "А123АА777",
        "transmission": "automatic",
    }
    payload.update(overrides)
    resp = client.post(
        "/api/instructor/cars", json=payload, headers=_headers(token)
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["car_id"]


def upload_sts(client, token, car_id, content=ROOT_JPEG, ext="jpg"):
    return client.post(
        f"/api/instructor/cars/{car_id}/photo/sts",
        files={"photo": (f"sts.{ext}", content,
                         "image/png" if ext == "png" else "image/jpeg")},
        headers=_headers(token),
    )


def upload_angle(client, token, car_id, angle, content=ROOT_JPEG):
    return client.post(
        f"/api/instructor/cars/{car_id}/photo/{angle}",
        files={"photo": (f"{angle}.jpg", content, "image/jpeg")},
        headers=_headers(token),
    )


def upload_license(client, token, content=ROOT_JPEG, field="file"):
    return client.post(
        "/api/instructor/documents/license",
        files={field: ("license.jpg", content, "image/jpeg")},
        headers=_headers(token),
    )


def set_car_status(car_id: int, status: str) -> None:
    """Прямой контроль БД (механика conftest) — аранжировка статусов."""
    conn = sqlite3.connect(db_path())
    conn.execute(
        "UPDATE instructor_cars SET status = ? WHERE id = ?", (status, car_id)
    )
    conn.commit()
    conn.close()


def doc_versions(car_or_app: int, target_type: str) -> list[tuple]:
    """Все версии документа из БД: [(version, status, file_path)]."""
    conn = sqlite3.connect(db_path())
    rows = conn.execute(
        "SELECT version, status, file_path FROM document_versions"
        " WHERE target_type = ? AND target_id = ? ORDER BY version",
        (target_type, car_or_app),
    ).fetchall()
    conn.close()
    return rows


# --- Миграция document_versions + seed (задача 1.1, NFR-24) -------------------


_LEGACY_DDL = """
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  surname TEXT NOT NULL,
  name TEXT NOT NULL,
  patronymic TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  phone TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE instructor_applications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  surname TEXT NOT NULL,
  name TEXT NOT NULL,
  patronymic TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  phone TEXT NOT NULL,
  address TEXT NOT NULL,
  work_format TEXT NOT NULL,
  plate TEXT NOT NULL DEFAULT '',
  license_number TEXT NOT NULL,
  license_date TEXT NOT NULL DEFAULT '',
  license_category TEXT NOT NULL,
  experience TEXT NOT NULL DEFAULT '',
  password_hash TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'waiting',
  review_comment TEXT NOT NULL DEFAULT '',
  experience_years INTEGER,
  license_photo_path TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE instructor_cars (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  instructor_id INTEGER NOT NULL,
  brand TEXT NOT NULL,
  model TEXT NOT NULL,
  year INTEGER NOT NULL,
  plate TEXT NOT NULL,
  transmission TEXT NOT NULL CHECK (transmission IN ('manual','automatic')),
  photo_path TEXT,
  photo_front TEXT,
  photo_rear TEXT,
  photo_interior TEXT,
  photo_left TEXT,
  photo_right TEXT,
  photo_sts TEXT,
  blocked INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'validated'
    CHECK (status IN ('draft','validating','validated')),
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def test_s8_migration_legacy_seed_and_schema_guards(monkeypatch, tmp_path):
    """TC-S8BE-001 (change add-s8-cars-docs-booking, задача 1.1, FR-70,
    NFR-24): предсозданная legacy-БД (Спринт 7, без document_versions) со
    старыми строками → init_db создает таблицу и засеивает verified v1
    (тот же файл, uploaded_at = created_at) для ВУ и СТС; строки без
    документа не засеиваются; повторный запуск ничего не меняет
    (idempotent); частичный UNIQUE — вторая pending на документ
    невозможна (ОВ-7); CHECK отклоняет rejected без причины (ОВ-1)."""
    import backend.db as db

    db_file = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_file)
    conn.executescript(_LEGACY_DDL)
    conn.execute(
        "INSERT INTO instructor_applications"
        " (surname, name, patronymic, email, phone, address, work_format,"
        " license_number, license_category, password_hash, created_at,"
        " license_photo_path)"
        " VALUES ('Петров', 'Петь', 'Петрович', 'old@example.com',"
        " '+7 900 000-00-00', 'addr', 'any', '123', 'B', 'hash',"
        " '2026-01-01 10:00:00', 'data/uploads/license/old1.jpg')"
    )
    conn.execute(
        "INSERT INTO instructor_applications"
        " (surname, name, patronymic, email, phone, address, work_format,"
        " license_number, license_category, password_hash, created_at)"
        " VALUES ('Сидоров', 'Сид', 'Сидорович', 'no-license@example.com',"
        " '+7 900 000-00-01', 'addr', 'any', '456', 'B', 'hash',"
        " '2026-01-01 11:00:00')"
    )
    conn.execute(
        "INSERT INTO instructor_cars (instructor_id, brand, model, year,"
        " plate, transmission, photo_sts, created_at)"
        " VALUES (1, 'Lada', 'Vesta', 2021, 'В456ВВ777', 'manual',"
        " 'data/uploads/car_photo/old-sts.jpg', '2026-01-02 12:00:00')"
    )
    conn.execute(
        "INSERT INTO instructor_cars (instructor_id, brand, model, year,"
        " plate, transmission, created_at)"
        " VALUES (1, 'Kia', 'Rio', 2022, 'К777КК777', 'automatic',"
        " '2026-01-03 13:00:00')"
    )
    conn.commit()
    conn.close()

    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(db_file))
    db.init_db()

    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    # ровно одна verified v1 у каждого документа с файлом, тот же файл
    rows = conn.execute(
        "SELECT target_type, target_id, version, file_path, status,"
        " uploaded_at, decided_at, reject_reason FROM document_versions"
        " ORDER BY id"
    ).fetchall()
    assert [(r["target_type"], r["target_id"]) for r in rows] == [
        ("license", 1),
        ("car_sts", 1),
    ]
    for row in rows:
        assert row["version"] == 1 and row["status"] == "verified"
        assert row["reject_reason"] is None
        assert row["decided_at"] == row["uploaded_at"]
    assert rows[0]["file_path"] == "data/uploads/license/old1.jpg"
    assert rows[0]["uploaded_at"] == "2026-01-01 10:00:00"
    assert rows[1]["file_path"] == "data/uploads/car_photo/old-sts.jpg"
    assert rows[1]["uploaded_at"] == "2026-01-02 12:00:00"
    # анкета без ВУ / авто без СТС — строк не создали (пустые состояния)
    assert conn.execute(
        "SELECT COUNT(*) FROM document_versions WHERE target_id IN (2)"
        " AND target_type = 'license'"
    ).fetchone()[0] == 0
    assert conn.execute(
        "SELECT COUNT(*) FROM document_versions WHERE target_id = 2"
        " AND target_type = 'car_sts'"
    ).fetchone()[0] == 0
    conn.close()

    # повторный запуск init_db ничего не меняет (idempotent, NFR-24)
    db.init_db()
    conn = sqlite3.connect(db_file)
    assert conn.execute("SELECT COUNT(*) FROM document_versions").fetchone()[0] == 2
    # частичный UNIQUE (ОВ-7): первая pending ок, вторая — IntegrityError
    conn.execute(
        "INSERT INTO document_versions (target_type, target_id, version,"
        " file_path, status, uploaded_at)"
        " VALUES ('license', 1, 2, 'p1.jpg', 'pending', '2026-01-04 00:00:00')"
    )
    try:
        conn.execute(
            "INSERT INTO document_versions (target_type, target_id, version,"
            " file_path, status, uploaded_at)"
            " VALUES ('license', 1, 3, 'p2.jpg', 'pending', '2026-01-04 00:00:01')"
        )
        raise AssertionError("вторая pending на документ должна быть отклонена")
    except sqlite3.IntegrityError:
        pass
    # UNIQUE (target_type, target_id, version)
    try:
        conn.execute(
            "INSERT INTO document_versions (target_type, target_id, version,"
            " file_path, status, uploaded_at, decided_at, reject_reason)"
            " VALUES ('license', 1, 1, 'dup.jpg', 'rejected',"
            " '2026-01-04 00:00:00', '2026-01-04 00:00:00', 'dup version')"
        )
        raise AssertionError("дубль version должен быть отклонен")
    except sqlite3.IntegrityError:
        pass
    # CHECK (ОВ-1): rejected без причины / с пустой — отклоняется
    for reason in (None, ""):
        try:
            conn.execute(
                "INSERT INTO document_versions (target_type, target_id,"
                " version, file_path, status, uploaded_at, decided_at,"
                " reject_reason)"
                " VALUES ('car_sts', 1, 9, 'r.jpg', 'rejected',"
                " '2026-01-04 00:00:00', '2026-01-04 00:00:00', ?)",
                (reason,),
            )
            raise AssertionError("rejected без причины должен быть отклонен")
        except sqlite3.IntegrityError:
            pass
    conn.execute(
        "INSERT INTO document_versions (target_type, target_id, version,"
        " file_path, status, uploaded_at, decided_at, reject_reason)"
        " VALUES ('car_sts', 1, 9, 'r.jpg', 'rejected',"
        " '2026-01-04 00:00:00', '2026-01-04 00:00:00', 'нечитаемо')"
    )
    conn.rollback()
    conn.close()


# --- ВУ: жизненный цикл версий (задачи 2.1/4.1, FR-70/71/72, ОВ-1/ОВ-7) -------


def test_s8_license_version_lifecycle_and_reject_reason(api, client):
    """TC-S8BE-002 (change add-s8-cars-docs-booking, задачи 2.1/4.1):
    загрузка ВУ → pending v1, license_photo_path и файл doc-эндпоинта НЕ
    изменились («документ не мигает»); reject: без поля/пустая/пробелы →
    422 (ОВ-1), с причиной → rejected, предыдущая версия действует,
    причина видна инструктору (last_rejected); повторная загрузка →
    pending v2; verify → verified + license_photo_path переключен, файл
    эндпоинта выдает новую версию, старая verified — архив; повторный
    verify/reject не-pending → 409."""
    import backend.uploads as uploads

    instr = create_instructor(client)
    admin = admin_headers(client)

    # легаси-ВУ анкеты ( canonical-колонка; версий нет — seed был до записи)
    legacy_path = uploads.save_image("license", ROOT_JPEG, "jpg")
    conn = sqlite3.connect(db_path())
    conn.execute(
        "UPDATE instructor_applications SET license_photo_path = ?"
        " WHERE id = ?",
        (legacy_path, instr["application_id"]),
    )
    conn.commit()
    conn.close()

    # PDF → 422, прежний файл не затронут
    resp = client.post(
        "/api/instructor/documents/license",
        files={"file": ("doc.pdf", ROOT_PDF, "application/pdf")},
        headers=_headers(instr["token"]),
    )
    assert resp.status_code == 422
    resp = client.post(
        "/api/instructor/documents/license",
        files={"file": ("big.jpg", b"\xff\xd8\xff" + b"\x00" * (5 * 1024 * 1024 + 1),
                         "image/jpeg")},
        headers=_headers(instr["token"]),
    )
    assert resp.status_code == 422 and "5 МБ" in resp.json()["error"]

    # первичная загрузка (анкета уже с легаси-ВУ — замена) → pending v1
    resp = upload_license(client, instr["token"], ROOT_PNG, field="file")
    assert resp.status_code == 200, resp.text
    doc = resp.json()["document"]
    assert doc["status"] == "pending" and doc["version"] == 1
    assert doc["uploaded_at"]
    conn = sqlite3.connect(db_path())
    canonical = conn.execute(
        "SELECT license_photo_path FROM instructor_applications WHERE id = ?",
        (instr["application_id"],),
    ).fetchone()[0]
    conn.close()
    assert canonical == legacy_path, "license_photo_path не меняется до verify"

    # файл doc-эндпоинта — прежний (действующая версия не мигает)
    file_url = f"/api/instructor/documents/license-{instr['application_id']}/file"
    got = client.get(file_url, headers=_headers(instr["token"]))
    assert got.status_code == 200 and got.content == ROOT_JPEG

    # reject: причина ОБЯЗАТЕЛЬНА (ОВ-1)
    conn = sqlite3.connect(db_path())
    version_id = conn.execute(
        "SELECT id FROM document_versions WHERE target_type = 'license'"
        " AND target_id = ? AND status = 'pending'",
        (instr["application_id"],),
    ).fetchone()[0]
    conn.close()
    assert (
        client.post(f"/api/admin/documents/{version_id}/reject", headers=admin)
        .status_code
        == 422
    ), "без тела — 422"
    for reason in ("", "   "):
        resp = client.post(
            f"/api/admin/documents/{version_id}/reject",
            json={"reason": reason},
            headers=admin,
        )
        assert resp.status_code == 422, "пустая причина — 422 (ОВ-1)"

    # reject с причиной → rejected, каноническая колонка не меняется
    resp = client.post(
        f"/api/admin/documents/{version_id}/reject",
        json={"reason": "Блик закрывает номер"},
        headers=admin,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["document"]["status"] == "rejected"
    versions = doc_versions(instr["application_id"], "license")
    assert versions[0][1] == "rejected"
    assert versions[0][2] != legacy_path
    got = client.get(file_url, headers=_headers(instr["token"]))
    assert got.content == ROOT_JPEG, "предыдущая версия продолжает действовать"

    # инструктор видит rejected с причиной (ОВ-1)
    docs = client.get(
        "/api/instructor/documents", headers=_headers(instr["token"])
    ).json()["documents"]
    license_doc = next(d for d in docs if d["type"] == "license")
    assert license_doc["active_version"] is None
    assert license_doc["pending"] is None
    assert license_doc["last_rejected"]["version"] == 1
    assert license_doc["last_rejected"]["reject_reason"] == "Блик закрывает номер"
    assert license_doc["last_rejected"]["decided_at"]

    # повторная загрузка → НОВАЯ pending v2; повтор при pending замещает
    resp = upload_license(client, instr["token"], ROOT_JPEG2)
    assert resp.status_code == 200
    assert resp.json()["document"]["version"] == 2
    resp = upload_license(client, instr["token"], ROOT_JPEG2)
    assert resp.status_code == 200
    assert resp.json()["document"]["version"] == 2, "version не растет до verify"
    versions = doc_versions(instr["application_id"], "license")
    assert [(v, s) for v, s, _ in versions] == [(1, "rejected"), (2, "pending")]
    conn = sqlite3.connect(db_path())
    version_id = conn.execute(
        "SELECT id FROM document_versions WHERE target_type = 'license'"
        " AND target_id = ? AND status = 'pending'",
        (instr["application_id"],),
    ).fetchone()[0]
    pending_file = conn.execute(
        "SELECT file_path FROM document_versions WHERE id = ?", (version_id,)
    ).fetchone()[0]
    conn.close()
    assert Path(pending_file).read_bytes() == ROOT_JPEG2, "файл замещен"

    # verify → verified, license_photo_path переключен (одна транзакция)
    resp = client.post(f"/api/admin/documents/{version_id}/verify", headers=admin)
    assert resp.status_code == 200, resp.text
    assert resp.json()["document"]["status"] == "verified"
    conn = sqlite3.connect(db_path())
    canonical = conn.execute(
        "SELECT license_photo_path FROM instructor_applications WHERE id = ?",
        (instr["application_id"],),
    ).fetchone()[0]
    conn.close()
    assert canonical == pending_file, "каноническая колонка переключена"
    got = client.get(file_url, headers=_headers(instr["token"]))
    assert got.status_code == 200 and got.content == ROOT_JPEG2
    versions = doc_versions(instr["application_id"], "license")
    assert [(v, s) for v, s, _ in versions] == [
        (1, "rejected"),
        (2, "verified"),
    ]
    docs = client.get(
        "/api/instructor/documents", headers=_headers(instr["token"])
    ).json()["documents"]
    license_doc = next(d for d in docs if d["type"] == "license")
    assert license_doc["active_version"]["version"] == 2
    assert license_doc["pending"] is None
    assert license_doc["last_rejected"]["version"] == 1

    # не-pending → 409 (машина статусов)
    assert (
        client.post(f"/api/admin/documents/{version_id}/verify", headers=admin)
        .status_code
        == 409
    )
    assert (
        client.post(
            f"/api/admin/documents/{version_id}/reject",
            json={"reason": "повторно"},
            headers=admin,
        ).status_code
        == 409
    )
    # админ pending-список больше не содержит решенную версию
    pending_list = client.get(
        "/api/admin/documents", headers=admin
    ).json()["documents"]
    assert all(d["id"] != version_id for d in pending_list)


# --- СТС: версии (задача 3.1), админ-список/предпросмотр (задача 4.1) ---------


def test_s8_sts_primary_replacement_and_admin_flow(api, client):
    """TC-S8BE-003 (change add-s8-cars-docs-booking, задачи 3.1/4.1,
    FR-69/FR-70, ОВ-2/ОВ-7): первичная дозагрузка СТС авто без СТС →
    photo_sts + verified v1; замена → pending-версия (photo_sts не
    перезаписан, повторная загрузка замещает ожидающую); админ
    pending-список содержит марку/модель/госномер + ФИО владельца;
    предпросмотр версии отдает файл версии (ОВ-4); verify переключает
    photo_sts на файл новой версии; инструктор видит active_version."""
    instr = create_instructor(client)
    admin = admin_headers(client)
    car_id = add_car_json(client, instr["token"])

    # первичная дозагрузка (FR-69) → verified v1 сразу, статус авто не меняется
    resp = upload_sts(client, instr["token"], car_id, ROOT_JPEG)
    assert resp.status_code == 200, resp.text
    assert resp.json()["document"] ["status"] == "verified"
    assert resp.json()["document"]["version"] == 1
    assert resp.json()["status"] == "draft", "первичная загрузка статус не меняет"
    conn = sqlite3.connect(db_path())
    sts_path = conn.execute(
        "SELECT photo_sts FROM instructor_cars WHERE id = ?", (car_id,)
    ).fetchone()[0]
    conn.close()
    assert Path(sts_path).read_bytes() == ROOT_JPEG
    assert doc_versions(car_id, "car_sts") == [
        (1, "verified", sts_path)
    ]

    # замена → pending, photo_sts не перезаписан; повторная — замещает (ОВ-7)
    resp = upload_sts(client, instr["token"], car_id, ROOT_PNG, ext="png")
    assert resp.status_code == 200
    assert resp.json()["document"]["status"] == "pending"
    assert resp.json()["document"]["version"] == 2
    resp = upload_sts(client, instr["token"], car_id, ROOT_JPEG2)
    assert resp.status_code == 200
    assert resp.json()["document"]["version"] == 2, "ОВ-7: version не растет"
    conn = sqlite3.connect(db_path())
    sts_path2 = conn.execute(
        "SELECT photo_sts FROM instructor_cars WHERE id = ?", (car_id,)
    ).fetchone()[0]
    conn.close()
    assert sts_path2 == sts_path, "photo_sts не перезаписывается до верификации"
    assert Path(sts_path2).read_bytes() == ROOT_JPEG

    # админ pending-список: тип, версия, авто + ФИО владельца
    pending_list = client.get(
        "/api/admin/documents?status=pending", headers=admin
    ).json()["documents"]
    entry = next(d for d in pending_list if d["target_type"] == "car_sts")
    assert entry["version"] == 2 and entry["target_id"] == car_id
    assert entry["car"]["brand"] == "Škoda" and entry["car"]["model"] == "Rapid"
    assert entry["car"]["plate"] == "А123АА777"
    assert "Иванов" in entry["instructor_full_name"]
    assert entry["uploaded_at"]

    # предпросмотр версии (ОВ-4): файл ИМЕННО pending-версии
    preview = client.get(
        f"/api/admin/documents/{entry['id']}/file", headers=admin
    )
    assert preview.status_code == 200
    assert "image/" in preview.headers["content-type"]
    assert preview.content == ROOT_JPEG2

    # verify → photo_sts переключен на файл версии
    resp = client.post(f"/api/admin/documents/{entry['id']}/verify", headers=admin)
    assert resp.status_code == 200, resp.text
    conn = sqlite3.connect(db_path())
    sts_path3 = conn.execute(
        "SELECT photo_sts FROM instructor_cars WHERE id = ?", (car_id,)
    ).fetchone()[0]
    conn.close()
    assert sts_path3 != sts_path
    assert Path(sts_path3).read_bytes() == ROOT_JPEG2
    versions = doc_versions(car_id, "car_sts")
    assert [(v, s) for v, s, _ in versions] == [(1, "verified"), (2, "verified")]

    # инструктор видит active_version v2 и файл по doc-эндпоинту
    docs = client.get(
        "/api/instructor/documents", headers=_headers(instr["token"])
    ).json()["documents"]
    sts_doc = next(d for d in docs if d["type"] == "car_sts")
    assert sts_doc["active_version"]["version"] == 2
    assert sts_doc["pending"] is None
    got = client.get(
        f"/api/instructor/documents/sts-{car_id}/file",
        headers=_headers(instr["token"]),
    )
    assert got.status_code == 200 and got.content == ROOT_JPEG2


def test_s8_sts_replacement_keeps_validated_ov6(api, client):
    """TC-S8BE-004 (change add-s8-cars-docs-booking, задача 3.1, ОВ-6):
    замена СТС у авто в validated НЕ сбрасывает валидацию (validated
    остается validated, photo_sts/ракурсы/has_sts не меняются), замена
    ракурса при этом возвращает validating (MAJ-1 — только 5 ракурсов)."""
    instr = create_instructor(client)
    car_id = add_car_json(client, instr["token"])
    upload_sts(client, instr["token"], car_id, ROOT_JPEG)
    for angle in ("front", "rear", "left"):
        upload_angle(client, instr["token"], car_id, angle)
    set_car_status(car_id, "validated")

    # замена СТС у validated → статус НЕ меняется (ОВ-6)
    conn = sqlite3.connect(db_path())
    sts_before = conn.execute(
        "SELECT photo_sts FROM instructor_cars WHERE id = ?", (car_id,)
    ).fetchone()[0]
    conn.close()
    resp = upload_sts(client, instr["token"], car_id, ROOT_PNG, ext="png")
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "validated", "ОВ-6: сброса нет"
    assert resp.json()["document"]["status"] == "pending"
    conn = sqlite3.connect(db_path())
    sts_after, front = conn.execute(
        "SELECT photo_sts, photo_front FROM instructor_cars WHERE id = ?",
        (car_id,),
    ).fetchone()
    conn.close()
    assert sts_after == sts_before, "photo_sts не перезаписан (FR-70)"
    assert front, "ракурсы не тронуты"
    assert [(v, s) for v, s, _ in doc_versions(car_id, "car_sts")] == [
        (1, "verified"),
        (2, "pending"),
    ]

    # замена ракурса у validated → validating (MAJ-1, только 5 ракурсов)
    resp = upload_angle(client, instr["token"], car_id, "right", ROOT_JPEG2)
    assert resp.status_code == 200
    assert resp.json()["status"] == "validating", "MAJ-1 для ракурсов сохранен"
    conn = sqlite3.connect(db_path())
    status = conn.execute(
        "SELECT status FROM instructor_cars WHERE id = ?", (car_id,)
    ).fetchone()[0]
    conn.close()
    assert status == "validating"


# --- Доступ (NFR-22) ----------------------------------------------------------


def test_s8_access_matrix(api, client):
    """TC-S8BE-005 (change add-s8-cars-docs-booking, NFR-22, ОВ-4):
    админ-контур — только X-Admin-Token (без/неверный → 401, сессия
    инструктора/ученика не помогает); загрузка ВУ и «Мои документы» —
    гость 401, ученик 403, инструктор — свои; чужой doc-файл →
    404-неразличение; несуществующая версия → 404 (file/verify/reject);
    недопустимый фильтр статуса → 422."""
    instr = create_instructor(client)
    other = create_instructor(client, email="other@example.com")
    student = create_student(client)

    admin_get_urls = (
        "/api/admin/documents",
        "/api/admin/documents?status=verified",
        "/api/admin/documents/1/file",
    )
    for url in admin_get_urls:
        assert client.get(url).status_code == 401, url
        assert client.get(url, headers={"X-Admin-Token": "bogus"}).status_code == 401
        assert (
            client.get(url, headers=_headers(instr["token"])).status_code == 401
        ), "сессия инструктора не заменяет админ-токен"
    method_urls = (
        ("post", {}, "/api/admin/documents/1/verify"),
        ("post", {}, "/api/admin/documents/1/reject"),
        ("post", {"reason": "х"}, "/api/admin/documents/1/reject"),
    )
    for method, payload, url in method_urls:
        assert getattr(client, method)(url).status_code == 401
        assert (
            getattr(client, method)(url, headers=_headers(instr["token"])).status_code
            == 401
        )
        assert (
            getattr(client, method)(url, json=payload, headers=_headers(instr["token"]))
            .status_code
            == 401
        )

    # фильтр статуса: допустимые значения, иное → 422
    admin = admin_headers(client)
    for status in ("pending", "verified", "rejected"):
        resp = client.get(
            f"/api/admin/documents?status={status}", headers=admin
        )
        assert resp.status_code == 200, status
    resp = client.get("/api/admin/documents?status=bogus", headers=admin)
    assert resp.status_code == 422

    # загрузка ВУ / список документов: гость 401, ученик 403
    assert client.post("/api/instructor/documents/license").status_code == 401
    assert (
        client.post(
            "/api/instructor/documents/license",
            files={"file": ("l.jpg", ROOT_JPEG, "image/jpeg")},
            headers=_headers(student["token"]),
        ).status_code
        == 403
    )
    assert client.get("/api/instructor/documents").status_code == 401
    assert (
        client.get(
            "/api/instructor/documents", headers=_headers(student["token"])
        ).status_code
        == 403
    )

    # чужой документ → 404-неразличение (NFR-22, фикс review-002 #1):
    # проверка на документах с ДЕЙСТВУЮЩЕЙ версией — ВУ (upload + admin
    # verify) и СТС (первичная загрузка → verified v1): чужая сессия
    # получает 404 (никогда 403/200), владелец — 200 со своим файлом
    car_id = add_car_json(client, instr["token"])
    assert upload_sts(client, instr["token"], car_id, ROOT_JPEG).status_code == 200
    assert upload_license(client, instr["token"], ROOT_PNG).status_code == 200
    conn = sqlite3.connect(db_path())
    pending_id = conn.execute(
        "SELECT id FROM document_versions WHERE target_type = 'license'"
        " AND target_id = ? AND status = 'pending'",
        (instr["application_id"],),
    ).fetchone()[0]
    conn.close()
    resp = client.post(
        f"/api/admin/documents/{pending_id}/verify", headers=admin
    )
    assert resp.status_code == 200, resp.text

    own_docs = client.get(
        "/api/instructor/documents", headers=_headers(instr["token"])
    ).json()
    license_doc = own_docs["license"]
    assert license_doc is not None, "ВУ с verified-версией виден владельцу"
    license_url = f"/api/instructor/documents/{license_doc['doc_id']}/file"
    sts_url = f"/api/instructor/documents/sts-{car_id}/file"
    got = client.get(license_url, headers=_headers(instr["token"]))
    assert got.status_code == 200 and got.content == ROOT_PNG
    got = client.get(sts_url, headers=_headers(instr["token"]))
    assert got.status_code == 200 and got.content == ROOT_JPEG
    assert (
        client.get(license_url, headers=_headers(other["token"])).status_code
        == 404
    ), "чужой ВУ → 404-неразличение"
    assert (
        client.get(sts_url, headers=_headers(other["token"])).status_code
        == 404
    ), "чужой СТС → 404-неразличение"
    assert (
        client.get(license_url, headers=_headers(student["token"])).status_code
        == 403
    )
    assert (
        client.get(sts_url, headers=_headers(student["token"])).status_code
        == 403
    )
    assert (
        client.get(
            "/api/instructor/documents/license-999999/file",
            headers=_headers(instr["token"]),
        ).status_code
        == 404
    )
    assert (
        client.get(
            "/api/instructor/documents/sts-999999/file",
            headers=_headers(instr["token"]),
        ).status_code
        == 404
    )

    # несуществующая версия: file/verify/reject → 404
    assert (
        client.get("/api/admin/documents/999999/file", headers=admin).status_code
        == 404
    )
    assert (
        client.post("/api/admin/documents/999999/verify", headers=admin).status_code
        == 404
    )
    assert (
        client.post(
            "/api/admin/documents/999999/reject",
            json={"reason": "нет такой"},
            headers=admin,
        ).status_code
        == 404
    )


# --- «Мои документы»: версии/статусы (задача 2.1) ------------------------------


def test_s8_my_documents_versions_and_empty_state(api, client):
    """TC-S8BE-006 (change add-s8-cars-docs-booking, задача 2.1, FR-70):
    «Мои документы» показывает на каждый документ active_version /
    pending / last_rejected; первичная pending-загрузка ВУ делает анкету
    БЕЗ ВУ видимой (бейдж «Ожидает проверки»); анкета без ВУ и без
    версий — прежнее пустое состояние с подсказкой (совместимость,
    regression TC-S5BE-011b)."""
    instr = create_instructor(client)
    car_id = add_car_json(client, instr["token"])

    # анкета без ВУ, версий нет → пустое состояние с подсказкой
    body = client.get(
        "/api/instructor/documents", headers=_headers(instr["token"])
    ).json()
    assert body["license"] is None and "ВУ" in body["license_hint"]
    assert body["documents"] == [], "авто без СТС и версий не попадает в список"

    # первичная pending-загрузка ВУ → документ появился с pending
    resp = upload_license(client, instr["token"], ROOT_JPEG)
    assert resp.status_code == 200
    body = client.get(
        "/api/instructor/documents", headers=_headers(instr["token"])
    ).json()
    assert body["license_hint"] is None
    license_doc = next(
        d for d in body["documents"] if d["type"] == "license"
    )
    assert license_doc["active_version"] is None
    assert license_doc["pending"]["version"] == 1
    assert license_doc["last_rejected"] is None

    # СТС: до загрузки авто без СТС не в списке; после первичной — с verified
    upload_sts(client, instr["token"], car_id, ROOT_JPEG)
    body = client.get(
        "/api/instructor/documents", headers=_headers(instr["token"])
    ).json()
    sts_docs = [d for d in body["documents"] if d["type"] == "car_sts"]
    assert len(sts_docs) == 1
    assert sts_docs[0]["active_version"]["version"] == 1
    assert sts_docs[0]["pending"] is None
    assert sts_docs[0]["last_rejected"] is None
    assert sts_docs[0]["car"]["id"] == car_id


# --- Баг 5.2: плитки от авторизованных эндпоинтов (регресс) -------------------


def test_s8_car_tiles_use_photo_endpoints_bug52(api, client):
    """TC-S8BE-007 (баг 5.2, FR-42 — регресс Спринта 8, задача 3 задания):
    список авто выдает клиенту URL авторизованных фото-эндпоинтов
    (photos{angle}, sts_url), НЕ файловые пути data/uploads (плитка
    строит <img> от эндпоинта); ключ photo_path не выдается; URL
    рабочие — картинки отдаются владельцу и переживают повторный вход."""
    instr = create_instructor(client)
    car_id = add_car_json(client, instr["token"])
    upload_angle(client, instr["token"], car_id, "front")
    upload_sts(client, instr["token"], car_id, ROOT_JPEG)

    listed = client.get(
        "/api/instructor/cars", headers=_headers(instr["token"])
    ).json()["cars"][0]
    assert listed["photos"]["front"] == (
        f"/api/instructor/cars/{car_id}/photo/front"
    )
    assert listed["photos"]["rear"] is None
    assert listed["sts_url"] == f"/api/instructor/cars/{car_id}/sts"
    assert listed["has_sts"] is True
    serialized = str(listed)
    assert "data/" not in serialized, "файловые пути клиенту не выдаются"
    assert "photo_path" not in listed, "устаревшая колонка не выдается"

    # плитка переживает перезагрузку: эндпоинты отвечают содержимым
    front = client.get(
        f"/api/instructor/cars/{car_id}/photo/front",
        headers=_headers(instr["token"]),
    )
    assert front.status_code == 200 and front.content == ROOT_JPEG
    sts = client.get(
        f"/api/instructor/cars/{car_id}/sts", headers=_headers(instr["token"])
    )
    assert sts.status_code == 200 and sts.content == ROOT_JPEG
    listed_again = client.get(
        "/api/instructor/cars", headers=_headers(instr["token"])
    ).json()["cars"][0]
    assert listed_again["photos"] == listed["photos"]
