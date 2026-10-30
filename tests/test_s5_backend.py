"""Спринт 5 — BACKEND-тесты (change add-booking-docs; задачи 1.1, 2.1,
2.2, 3.1, 4.1, 4.2 — backend-волна).

Покрывают: миграции booking + instructor_cars (ракурсы/СТС; Спринт 7:
+status, блокировка заменена статусной моделью), создание авто с
обязательным СТС (FR-44), фото 5 ракурсов и матрица доступа (FR-42, MIN-2,
Спринт 7 ОВ-2: draft скрыт от ученика пары), баг 5.2 (фото в плитках —
URL эндпоинта), комплектность (ОВ-1; block-эндпоинт Спринта 5 удален),
«Мои документы» (FR-45),
бронирование: слоты/брони/confirm/reject, ГОНКИ (NFR-8), PUT availability
× активные брони (MAJ-1), границы lesson_date (MIN-1), пустое авто
(MIN-3), «Занятия на сегодня» (FR-49).

tests/test_s3_backend.py (Спринт 3) НЕ расширяется — все новые кейсы
здесь; трассировка TC-S5BE-NNN в docstring каждого теста (rule 6).
Фикстуры — общий client из conftest; time.sleep запрещен.
"""
import datetime
import sqlite3
import threading
from pathlib import Path

import pytest

from conftest import admin_headers, db_path, register

ROOT = Path(__file__).resolve().parent.parent

ROOT_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
ROOT_PNG = b"\x89PNG\r\n\x1a\x0a" + b"\x00" * 64
ROOT_PDF = b"%PDF-1.4\nfake-pdf\n"
OVERSIZE_JPEG = b"\xff\xd8\xff" + b"\x00" * (5 * 1024 * 1024 + 1)

INSTR_PASSWORD = "Instr1234"

ANGLES = ("front", "rear", "interior", "left", "right")


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


def create_instructor(client, email="instr@example.com", name="Иван"):
    resp = client.post(
        "/api/instructors/apply",
        json=apply_body(email=email, name=name),
    )
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
    return {"token": login.json()["token"], "id": user_id, "email": email,
            "application_id": app_id}


def create_student(client, email="student@example.com"):
    resp = register(client, email=email)
    assert resp.status_code == 200, resp.text
    conn = sqlite3.connect(db_path())
    user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", (email,)
    ).fetchone()[0]
    conn.close()
    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Qwerty123"},
    )
    assert login.status_code == 200, login.text
    return {"token": login.json()["token"], "id": user_id, "email": email}


def add_car_json(client, token, **overrides):
    """Создание авто по пути совместимости (JSON, без СТС) — для аранжировки
    не-СТС кейсов; новые флоу тестирует multipart (FR-44)."""
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


def create_car_multipart(client, token, sts=ROOT_JPEG, **field_overrides):
    """POST /api/instructor/cars multipart с файлом sts_photo (FR-44);
    sts=None — кейс «без файла»."""
    fields = {
        "brand": "Lada",
        "model": "Vesta",
        "year": "2021",
        "plate": "В456ВВ777",
        "transmission": "manual",
    }
    fields.update({k: str(v) for k, v in field_overrides.items()})
    files = None
    if sts is not None:
        files = {"sts_photo": ("sts.jpg", sts, "image/jpeg")}
    return client.post(
        "/api/instructor/cars", data=fields, files=files,
        headers=_headers(token),
    )


def put_availability(client, token, intervals):
    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": intervals},
        headers=_headers(token),
    )
    return resp


def setup_pair(
    client,
    instructor_email="instr@example.com",
    student_email="student@example.com",
    intervals=None,
):
    """Полная аранжировка: инструктор + авто + график + пара accepted."""
    instr = create_instructor(client, email=instructor_email)
    car_id = add_car_json(client, instr["token"])
    if intervals is None:
        intervals = [
            {"weekday": 0, "start_time": "10:00", "end_time": "11:00"},
            {"weekday": 1, "start_time": "12:00", "end_time": "13:00"},
        ]
    saved = put_availability(client, instr["token"], intervals)
    assert saved.status_code == 200, saved.text
    student = create_student(client, email=student_email)
    req = client.post(
        "/api/student/requests",
        json={"instructor_id": instr["id"]},
        headers=_headers(student["token"]),
    )
    assert req.status_code == 200, req.text
    accepted = client.post(
        f"/api/instructor/requests/{req.json()['request_id']}/accept",
        json={"car_id": car_id},
        headers=_headers(instr["token"]),
    )
    assert accepted.status_code == 200, accepted.text
    return {"instr": instr, "student": student, "car_id": car_id}


def get_slots(client, student_token, instructor_id):
    return client.get(
        f"/api/student/instructors/{instructor_id}/slots",
        headers=_headers(student_token),
    )


def book(client, student_token, availability_id):
    return client.post(
        "/api/student/bookings",
        json={"availability_id": availability_id},
        headers=_headers(student_token),
    )


def first_slot_id(client, student_token, instructor_id, state="free"):
    slots = get_slots(client, student_token, instructor_id).json()["slots"]
    return next(s["id"] for s in slots if s["state"] == state)


def fetch_booking(booking_id):
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM booking WHERE id = ?", (booking_id,)
    ).fetchone()
    conn.close()
    return row


def upload_angle(client, token, car_id, angle, content=ROOT_JPEG, ext="jpg"):
    return client.post(
        f"/api/instructor/cars/{car_id}/photo/{angle}",
        files={"photo": (f"{angle}.{ext}", content,
                         "image/png" if ext == "png" else "image/jpeg")},
        headers=_headers(token),
    )


def set_car_status(car_id: int, status: str) -> None:
    """Прямой контроль БД (механика conftest): статус валидации для
    аранжировки (Спринт 7: POST создает авто в 'draft'; существующие
    строки после миграции — 'validated')."""
    conn = sqlite3.connect(db_path())
    conn.execute(
        "UPDATE instructor_cars SET status = ? WHERE id = ?",
        (status, car_id),
    )
    conn.commit()
    conn.close()


# --- Миграции (db.py) --------------------------------------------------------


def test_s5_migration_booking_table_and_indexes(client):
    """TC-S5BE-001 (change add-booking-docs, задача 4.1/2.1): миграции
    создают таблицу booking (student_id, instructor_id, availability_id,
    lesson_date, status, reject_comment) с индексами и частичным UNIQUE,
    а также колонки instructor_cars (5 ракурсов, photo_sts, blocked)."""
    conn = sqlite3.connect(db_path())
    tables = {
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    indexes = {
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        )
    }
    car_columns = [row[1] for row in conn.execute(
        "PRAGMA table_info(instructor_cars)"
    )]
    booking_columns = [row[1] for row in conn.execute(
        "PRAGMA table_info(booking)"
    )]
    conn.close()

    assert "booking" in tables
    assert {"idx_booking_instructor", "idx_booking_student",
            "uq_booking_active_slot"} <= indexes
    assert {"student_id", "instructor_id", "availability_id", "lesson_date",
            "status", "reject_comment", "created_at", "decided_at"} <= set(
        booking_columns)
    assert {"photo_front", "photo_rear", "photo_interior", "photo_left",
            "photo_right", "photo_sts", "blocked"} <= set(car_columns)


def test_s5_migration_idempotent_keeps_rows(client):
    """TC-S5BE-002 (change add-booking-docs, задача 4.1): повторный
    init_db идемпотентен: колонки/таблицы/индексы не дублируются, записи
    booking и авто сохраняются (механика users.role, NFR-5→NFR-10)."""
    instr = create_instructor(client)
    put_availability(
        client, instr["token"],
        [{"weekday": 0, "start_time": "10:00", "end_time": "11:00"}],
    )
    conn = sqlite3.connect(db_path())
    slot_id = conn.execute(
        "SELECT id FROM availability WHERE instructor_id = ?",
        (instr["id"],),
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO booking (student_id, instructor_id, availability_id,"
        " lesson_date, status) VALUES (1, ?, ?, '2026-01-05', 'new')",
        (instr["id"], slot_id),
    )
    conn.commit()
    conn.close()

    import backend.db as db

    db.init_db()
    db.init_db()

    conn = sqlite3.connect(db_path())
    car_columns = [row[1] for row in conn.execute(
        "PRAGMA table_info(instructor_cars)"
    )]
    bookings = conn.execute("SELECT COUNT(*) FROM booking").fetchone()[0]
    indexes = {
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        )
    }
    conn.close()
    for column in ("photo_front", "photo_rear", "photo_interior",
                   "photo_left", "photo_right", "photo_sts", "blocked"):
        assert car_columns.count(column) == 1
    assert bookings == 1
    assert "uq_booking_active_slot" in indexes


# --- Авто: СТС при создании (FR-44), ракурсы (FR-43) -------------------------


def test_s5_car_creation_requires_sts(api, client):
    """TC-S5BE-003 (change add-booking-docs, задача 2.1): multipart с
    обязательным СТС: с файлом — авто создан, photo_sts сохранен в
    data/uploads/car_sts/; без файла — 422, авто НЕ создан (FR-44)."""
    instr = create_instructor(client)

    ok = create_car_multipart(client, instr["token"])
    assert ok.status_code == 200, ok.text
    car_id = ok.json()["car_id"]

    conn = sqlite3.connect(db_path())
    row = conn.execute(
        "SELECT photo_sts FROM instructor_cars WHERE id = ?", (car_id,)
    ).fetchone()
    conn.close()
    assert row[0], "photo_sts должен быть сохранен"
    assert "car_sts" in row[0].split("/")[-2:]
    from pathlib import Path

    assert Path(row[0]).read_bytes() == ROOT_JPEG

    listed = client.get(
        "/api/instructor/cars", headers=_headers(instr["token"])
    ).json()["cars"][0]
    assert listed["has_sts"] is True
    assert listed["sts_url"] == f"/api/instructor/cars/{car_id}/sts"

    without = create_car_multipart(client, instr["token"], sts=None)
    assert without.status_code == 422
    assert "СТС" in without.json()["error"]
    conn = sqlite3.connect(db_path())
    count = conn.execute("SELECT COUNT(*) FROM instructor_cars").fetchone()[0]
    conn.close()
    assert count == 1, "авто без СТС не создается"


def test_s5_create_car_json_invalid_body_422_not_500(api, client):
    """TC-S5BE-024 (change add-booking-docs, M-2 review-001): легаси-JSON
    путь create_car НЕ 500-ит на клиентском вводе: невалидное значение
    поля ({"year": "abc"} — ValidationError) и не-объект ([1, 2] —
    TypeError) → 422 по первому полю, авто НЕ создан (как до Спринта 5,
    когда тело разбирал Pydantic-параметр хендлера)."""
    instr = create_instructor(client, email="carjson@example.com")
    headers = _headers(instr["token"])

    bad_year = client.post(
        "/api/instructor/cars",
        json={"brand": "Lada", "model": "Vesta", "year": "abc",
              "plate": "А123АА777", "transmission": "manual"},
        headers=headers,
    )
    assert bad_year.status_code == 422
    assert "Год" in bad_year.json()["error"]

    not_object = client.post(
        "/api/instructor/cars", json=[1, 2], headers=headers,
    )
    assert not_object.status_code == 422

    conn = sqlite3.connect(db_path())
    count = conn.execute(
        "SELECT COUNT(*) FROM instructor_cars WHERE instructor_id = ?",
        (instr["id"],),
    ).fetchone()[0]
    conn.close()
    assert count == 0, "невалидное тело не создает авто"


def test_s5_car_sts_file_validation(api, client):
    """TC-S5BE-004 (change add-booking-docs, задача 2.1, NFR-9): СТС не
    JPEG/PNG (PDF) и больше 5 МБ → 422, авто НЕ создается."""
    instr = create_instructor(client)
    for bad in (ROOT_PDF, OVERSIZE_JPEG):
        resp = create_car_multipart(client, instr["token"], sts=bad)
        assert resp.status_code == 422, (bad[:4], resp.text)
        assert "Файл" in resp.json()["error"]
    conn = sqlite3.connect(db_path())
    count = conn.execute("SELECT COUNT(*) FROM instructor_cars").fetchone()[0]
    conn.close()
    assert count == 0


def test_s5_car_photo_angles_upload_replace(api, client):
    """TC-S5BE-005 (change add-booking-docs, задача 2.1, FR-43): каждый
    ракурс сохраняется и выдается отдельно; замена «спереди» остальные
    не трогает; Content-Type image/*."""
    instr = create_instructor(client)
    car_id = create_car_multipart(client, instr["token"]).json()["car_id"]

    for angle in ANGLES:
        uploaded = upload_angle(
            client, instr["token"], car_id, angle,
            content=ROOT_JPEG if angle != "rear" else ROOT_PNG,
            ext="png" if angle == "rear" else "jpg",
        )
        assert uploaded.status_code == 200, (angle, uploaded.text)

    front = client.get(
        f"/api/instructor/cars/{car_id}/photo/front",
        headers=_headers(instr["token"]),
    )
    assert front.status_code == 200
    assert front.headers["content-type"] == "image/jpeg"
    assert front.content == ROOT_JPEG
    rear = client.get(
        f"/api/instructor/cars/{car_id}/photo/rear",
        headers=_headers(instr["token"]),
    )
    assert rear.headers["content-type"] == "image/png"
    assert rear.content == ROOT_PNG

    conn = sqlite3.connect(db_path())
    old_rear = conn.execute(
        "SELECT photo_rear FROM instructor_cars WHERE id = ?", (car_id,)
    ).fetchone()[0]
    conn.close()

    replaced = upload_angle(client, instr["token"], car_id, "front",
                            content=ROOT_JPEG + b"new-bytes")
    assert replaced.status_code == 200

    conn = sqlite3.connect(db_path())
    new_front, new_rear = conn.execute(
        "SELECT photo_front, photo_rear FROM instructor_cars WHERE id = ?",
        (car_id,),
    ).fetchone()
    conn.close()
    assert new_rear == old_rear, "замена front не должна трогать rear"
    assert new_front != old_rear


def test_s5_car_photo_angle_errors(api, client):
    """TC-S5BE-006 (change add-booking-docs, задача 2.1, FR-43): ракурс
    вне списка → 404; чужой авто при загрузке → 404; свой незагруженный
    ракурс → 404."""
    instr = create_instructor(client)
    other = create_instructor(client, email="other@example.com")
    car_id = create_car_multipart(client, instr["token"]).json()["car_id"]

    bad_angle = upload_angle(client, instr["token"], car_id, "trunk")
    assert bad_angle.status_code == 404
    assert client.get(
        f"/api/instructor/cars/{car_id}/photo/trunk",
        headers=_headers(instr["token"]),
    ).status_code == 404

    foreign = upload_angle(client, other["token"], car_id, "front")
    assert foreign.status_code == 404

    not_loaded = client.get(
        f"/api/instructor/cars/{car_id}/photo/interior",
        headers=_headers(instr["token"]),
    )
    assert not_loaded.status_code == 404


def test_s5_car_photo_access_matrix_and_sts(api, client):
    """TC-S5BE-007 (change add-booking-docs, задачи 2.1/2.2, FR-42, NFR-7,
    MIN-2): ракурсы — владельцу и ученику ПАРЫ; ученик без пары → 403;
    чужой инструктор → 404; гость → 401; блокировка авто скрывает его от
    ученика пары (404), владельцу виден; СТС ученику не выдается (403)."""
    env = setup_pair(client)
    instr, student = env["instr"], env["student"]
    car_id = env["car_id"]
    upload_angle(client, instr["token"], car_id, "front")
    # [test-adapted] Спринт 7 (ОВ-2): фото ученику пары выдается только вне
    # draft — выставляем validated (аранжировка, семантика сохранена).
    set_car_status(car_id, "validated")

    # ученик пары видит
    got = client.get(
        f"/api/instructor/cars/{car_id}/photo/front",
        headers=_headers(student["token"]),
    )
    assert got.status_code == 200
    assert got.content == ROOT_JPEG

    # ученик БЕЗ пары → 403
    outsider = create_student(client, email="outsider@example.com")
    assert client.get(
        f"/api/instructor/cars/{car_id}/photo/front",
        headers=_headers(outsider["token"]),
    ).status_code == 403

    # чужой инструктор → 404; гость → 401
    other = create_instructor(client, email="other@example.com")
    assert client.get(
        f"/api/instructor/cars/{car_id}/photo/front",
        headers=_headers(other["token"]),
    ).status_code == 404
    assert client.get(
        f"/api/instructor/cars/{car_id}/photo/front"
    ).status_code == 401

    # СТС: владелец — 200, ученик пары — 403 (NFR-7), чужой — 404
    assert client.get(
        f"/api/instructor/cars/{car_id}/sts",
        headers=_headers(instr["token"]),
    ).status_code in (200, 404)  # СТС может быть не загружен (JSON-путь)
    assert client.get(
        f"/api/instructor/cars/{car_id}/sts",
        headers=_headers(student["token"]),
    ).status_code == 403
    assert client.get(
        f"/api/instructor/cars/{car_id}/sts",
        headers=_headers(other["token"]),
    ).status_code == 404

    # [test-adapted] Спринт 7 (add-car-validation-booking, ОВ-2): контур
    # блокировки (Спринт 5) замещен статусной моделью — вместо blocked
    # проверяется статусное правило видимости: draft скрыт от ученика
    # пары (404 неразличение), validating/validated — выдается; владелец
    # видит во всех статусах. Семантика кейса («неполный авто скрыт от
    # учеников, владелец видит») сохранена через статус.
    set_car_status(car_id, "draft")
    assert client.get(
        f"/api/instructor/cars/{car_id}/photo/front",
        headers=_headers(student["token"]),
    ).status_code == 404, "draft скрыт от ученика пары (ОВ-2)"
    assert client.get(
        f"/api/instructor/cars/{car_id}/photo/front",
        headers=_headers(instr["token"]),
    ).status_code == 200, "владелец видит фото во всех статусах"
    set_car_status(car_id, "validating")
    assert client.get(
        f"/api/instructor/cars/{car_id}/photo/front",
        headers=_headers(student["token"]),
    ).status_code == 200
    set_car_status(car_id, "validated")
    assert client.get(
        f"/api/instructor/cars/{car_id}/photo/front",
        headers=_headers(student["token"]),
    ).status_code == 200
    listed = client.get(
        "/api/instructor/cars", headers=_headers(instr["token"])
    ).json()["cars"][0]
    assert listed["status"] == "validated"


def test_s5_bug_5_2_photo_survives_relogin(api, client):
    """TC-S5BE-008 (change add-booking-docs, задача 1.1, FR-42): баг 5.2 —
    загруженное и сохраненное фото отображается владельцу после
    «перезагрузки» (повторный запрос списка) и ПОВТОРНОГО ВХОДА (новый
    токен) без повторной загрузки; плитке выдается URL авторизованного
    эндпоинта, а не файловый путь data/uploads (NFR-1)."""
    instr = create_instructor(client)
    car_id = add_car_json(client, instr["token"])
    upload_angle(client, instr["token"], car_id, "front")

    cars = client.get(
        "/api/instructor/cars", headers=_headers(instr["token"])
    ).json()["cars"][0]
    assert cars["photos"]["front"] == f"/api/instructor/cars/{car_id}/photo/front"
    assert not cars["photos"]["front"].startswith("data/")

    # повторный вход → новый токен
    relogin = client.post(
        "/api/auth/login",
        json={"email": instr["email"], "password": INSTR_PASSWORD},
    )
    new_token = relogin.json()["token"]
    assert new_token != instr["token"]

    cars2 = client.get(
        "/api/instructor/cars", headers=_headers(new_token)
    ).json()["cars"][0]
    assert cars2["photos"]["front"] == cars["photos"]["front"]
    got = client.get(
        cars2["photos"]["front"], headers=_headers(new_token)
    )
    assert got.status_code == 200
    assert got.content == ROOT_JPEG
    assert "image/" in got.headers["content-type"]


# --- Админ: комплектность и блокировка (ОВ-1) --------------------------------


def test_s5_admin_cars_completeness(api, client):
    """TC-S5BE-009 (change add-booking-docs, задача 2.2, ОВ-1): GET
    /api/admin/cars/completeness — без/с неверным токеном → 401; с
    токеном — все авто всех инструкторов: владелец, флаги 5 ракурсов +
    СТС, blocked; флаги отражают фактические наборы."""
    instr = create_instructor(client)
    car_full = create_car_multipart(client, instr["token"]).json()["car_id"]
    car_empty = add_car_json(
        client, instr["token"], brand="Lada", model="Kalina"
    )
    upload_angle(client, instr["token"], car_full, "front")
    upload_angle(client, instr["token"], car_full, "rear")

    assert client.get("/api/admin/cars/completeness").status_code == 401
    assert client.get(
        "/api/admin/cars/completeness",
        headers={"X-Admin-Token": "wrong-token"},
    ).status_code == 401

    resp = client.get(
        "/api/admin/cars/completeness", headers=admin_headers(client)
    )
    assert resp.status_code == 200
    cars = {c["id"]: c for c in resp.json()["cars"]}
    assert set(cars) == {car_full, car_empty}
    full = cars[car_full]
    assert full["photos"] == {
        "front": True, "rear": True, "interior": False,
        "left": False, "right": False,
    }
    assert full["has_sts"] is True
    # [test-adapted] Спринт 7 (задача 1.2): blocked — устаревшая колонка,
    # не выдается; вместо нее status + counters (ОВ-1/ОВ-4).
    assert full["status"] == "draft"
    assert full["counters"] == {"angles": 2, "sts": True}
    assert full["instructor_full_name"].startswith("Иванов")
    empty = cars[car_empty]
    assert not any(empty["photos"].values())
    assert empty["has_sts"] is False
    assert empty["status"] == "draft"
    assert empty["counters"] == {"angles": 0, "sts": False}
    assert empty["plate"] == "А123АА777"


def test_s5_admin_block_removed_bookings_survive(api, client):
    """TC-S5BE-010 (change add-booking-docs, задача 2.2, MIN-2/ОВ-1).
    [test-adapted] Спринт 7 (add-car-validation-booking, задача 1.2,
    MODIFIED/REMOVED-дельта): POST /api/admin/cars/{id}/block УДАЛЕН —
    контур блокировки замещен статусной моделью (design.md); семантика
    кейса «существующие брони не аннулируются, видимость по статусу»
    сохранена: авто в 'validated' (как существующие строки после
    миграции, ОВ-1) — бронь создается, подтверждается и видна ученику с
    авто; новое авто создается в 'draft' (TC-S7BE-003)."""
    env = setup_pair(client)
    instr, student = env["instr"], env["student"]
    car_id = env["car_id"]
    set_car_status(car_id, "validated")  # состояние после миграции (ОВ-1)
    upload_angle(client, instr["token"], car_id, "front")

    # block-эндпоинт отсутствует (замещен статусной моделью)
    assert client.post(
        f"/api/admin/cars/{car_id}/block", headers=admin_headers(client)
    ).status_code in (404, 405)

    slot_id = first_slot_id(client, student["token"], instr["id"])
    created = book(client, student["token"], slot_id)
    assert created.status_code == 200
    booking_id = created.json()["booking_id"]
    assert client.post(
        f"/api/instructor/bookings/{booking_id}/confirm",
        headers=_headers(instr["token"]),
    ).status_code == 200

    mine = client.get(
        "/api/student/bookings", headers=_headers(student["token"])
    ).json()["bookings"]
    assert len(mine) == 1
    assert mine[0]["status"] == "confirmed"
    assert mine[0]["car"]["id"] == car_id, (
        "бронь сохраняется и отображается (MIN-2, видимость по статусу)"
    )
    assert mine[0]["car"]["car_status"] == "validated"
    assert mine[0]["car"]["photo_url"], (
        "validated-авто в брони ученика — с photo_url (ОВ-2, задача 6.1)"
    )


# --- «Мои документы» (FR-45) --------------------------------------------------


def _set_license_photo(client, application_id, content=ROOT_JPEG):
    """Загружает файл ВУ в каталог uploads и прописывает путь в анкету
    (прямой контроль БД — механика conftest; multipart-анкета — другой
    пакет)."""
    import os

    import backend.uploads as uploads

    path = uploads.save_image("license", content, "jpg")
    conn = sqlite3.connect(db_path())
    conn.execute(
        "UPDATE instructor_applications SET license_photo_path = ?"
        " WHERE id = ?",
        (path, application_id),
    )
    conn.commit()
    conn.close()
    return path


def test_s5_documents_list_with_license_and_two_cars(api, client):
    """TC-S5BE-011 (change add-booking-docs, задача 3.1, FR-45): инструктор
    с ВУ и 2 авто видит 3 записи: тип, привязка (марка/модель/госномер),
    дата загрузки."""
    instr = create_instructor(client)
    _set_license_photo(client, instr["application_id"])
    car1 = add_car_json(client, instr["token"])
    car2 = add_car_json(
        client, instr["token"], brand="Lada", model="Kalina",
        plate="В456ВВ777",
    )
    conn = sqlite3.connect(db_path())
    for car in (car1, car2):
        conn.execute(
            "UPDATE instructor_cars SET photo_sts = ? WHERE id = ?",
            (f"data/uploads/car_sts/{car}.jpg", car),
        )
    conn.commit()
    conn.close()

    resp = client.get(
        "/api/instructor/documents", headers=_headers(instr["token"])
    )
    assert resp.status_code == 200
    body = resp.json()
    docs = body["documents"]
    assert len(docs) == 3
    types = [d["type"] for d in docs]
    assert types.count("license") == 1 and types.count("car_sts") == 2
    license_doc = next(d for d in docs if d["type"] == "license")
    assert license_doc["license_number"] == "9911223344"
    assert license_doc["uploaded_at"]
    sts = next(d for d in docs if d["type"] == "car_sts")
    assert sts["car"]["id"] in (car1, car2)
    assert sts["car"]["plate"]
    assert body["license_hint"] is None


def test_s5_documents_empty_license_state(api, client):
    """TC-S5BE-011b (change add-booking-docs, задача 3.1, FR-45): анкета
    без ВУ — пустое состояние с подсказкой, СТС на месте (досыл вне
    объема)."""
    instr = create_instructor(client)
    car_id = add_car_json(client, instr["token"])
    conn = sqlite3.connect(db_path())
    conn.execute(
        "UPDATE instructor_cars SET photo_sts = ? WHERE id = ?",
        (f"data/uploads/car_sts/{car_id}.jpg", car_id),
    )
    conn.commit()
    conn.close()
    resp = client.get(
        "/api/instructor/documents", headers=_headers(instr["token"])
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["license"] is None
    assert "ВУ" in body["license_hint"]
    assert [
        d["type"] for d in body["documents"] if d["type"] == "car_sts"
    ] == ["car_sts"], "СТС на месте при пустом ВУ"


def test_s5_documents_file_access(api, client):
    """TC-S5BE-012 (change add-booking-docs, задача 3.1, FR-45, NFR-7):
    файл документа выдается ТОЛЬКО владельцу: чужой инструктор → 404,
    ученик → 403, гость → 401, неизвестный doc_id → 404; свой → 200
    image/*."""
    instr = create_instructor(client)
    _set_license_photo(client, instr["application_id"])
    docs = client.get(
        "/api/instructor/documents", headers=_headers(instr["token"])
    ).json()["documents"]
    license_doc = next(d for d in docs if d["type"] == "license")
    sts_doc = next(
        (d for d in docs if d["type"] == "car_sts"), None
    )
    assert sts_doc is None, "без СТС в авто — нет СТС-записей"

    url = f"/api/instructor/documents/{license_doc['doc_id']}/file"
    got = client.get(url, headers=_headers(instr["token"]))
    assert got.status_code == 200
    assert "image/" in got.headers["content-type"]
    assert got.content == ROOT_JPEG

    other = create_instructor(client, email="other@example.com")
    assert client.get(
        url, headers=_headers(other["token"])
    ).status_code == 404
    student = create_student(client)
    assert client.get(
        url, headers=_headers(student["token"])
    ).status_code == 403
    assert client.get(url).status_code == 401
    assert client.get(
        "/api/instructor/documents/license-999999/file",
        headers=_headers(instr["token"]),
    ).status_code == 404
    assert client.get(
        "/api/instructor/documents/bogus/file",
        headers=_headers(instr["token"]),
    ).status_code == 404

    # СТС-файл: владелецу выдается
    car_id = add_car_json(client, instr["token"])
    conn = sqlite3.connect(db_path())
    conn.execute(
        "UPDATE instructor_cars SET photo_sts = ? WHERE id = ?",
        (f"data/uploads/car_sts/{car_id}.jpg", car_id),
    )
    conn.commit()
    conn.close()
    assert client.get(
        f"/api/instructor/documents/sts-{car_id}/file",
        headers=_headers(instr["token"]),
    ).status_code == 404  # файла на диске нет — 404, не битая выдача


# --- Бронирование: слоты (FR-46/FR-50) ---------------------------------------


def test_s5_slots_access_guard(api, client):
    """TC-S5BE-013 (change add-booking-docs, задача 4.1, FR-46, NFR-7):
    слоты без пары недоступны ПРЯМЫМ вызовом → 403; несуществующий/не
    одобренный инструктор → 404; гость → 401; инструкторская сессия →
    403."""
    instr = create_instructor(client)
    put_availability(
        client, instr["token"],
        [{"weekday": 0, "start_time": "10:00", "end_time": "11:00"}],
    )
    student = create_student(client)

    assert get_slots(client, student["token"], instr["id"]).status_code == 403
    assert get_slots(client, student["token"], 999999).status_code == 404
    assert client.get(
        f"/api/student/instructors/{instr['id']}/slots"
    ).status_code == 401
    assert get_slots(client, instr["token"], instr["id"]).status_code == 403


def test_s5_slots_states(api, client):
    """TC-S5BE-014 (change add-booking-docs, задача 4.1, FR-47/FR-50):
    состояния слотов: free → pending (свой запрос) / busy (чужая активная
    бронь, БЕЗ раскрытия кем) → после отклонения снова free (ОВ-5)."""
    env = setup_pair(client)
    instr, student = env["instr"], env["student"]
    slots = get_slots(client, student["token"], instr["id"]).json()["slots"]
    assert len(slots) == 2
    assert all(s["state"] == "free" for s in slots)
    assert all(
        set(s) == {"id", "weekday", "start_time", "end_time", "state"}
        for s in slots
    )

    slot_id = slots[0]["id"]
    assert book(client, student["token"], slot_id).status_code == 200
    states = {
        s["id"]: s["state"]
        for s in get_slots(
            client, student["token"], instr["id"]
        ).json()["slots"]
    }
    assert states[slot_id] == "pending"

    # второй принятый ученик того же инструктора видит «занято» без деталей
    student2 = create_student(client, email="student2@example.com")
    req2 = client.post(
        "/api/student/requests",
        json={"instructor_id": instr["id"]},
        headers=_headers(student2["token"]),
    )
    accept2 = client.post(
        f"/api/instructor/requests/{req2.json()['request_id']}/accept",
        json={"car_id": env["car_id"]},
        headers=_headers(instr["token"]),
    )
    assert accept2.status_code == 200, accept2.text
    states2 = {
        s["id"]: s["state"]
        for s in get_slots(
            client, student2["token"], instr["id"]
        ).json()["slots"]
    }
    assert states2[slot_id] == "busy"

    # после отклонения слот освобождается (ОВ-5)
    booking_id = fetch_booking_by_slot(slot_id)
    assert client.post(
        f"/api/instructor/bookings/{booking_id}/reject",
        json={"comment": "не успеваю"},
        headers=_headers(instr["token"]),
    ).status_code == 200
    states3 = {
        s["id"]: s["state"]
        for s in get_slots(
            client, student["token"], instr["id"]
        ).json()["slots"]
    }
    assert states3[slot_id] == "free"


def fetch_booking_by_slot(availability_id):
    conn = sqlite3.connect(db_path())
    row = conn.execute(
        "SELECT id FROM booking WHERE availability_id = ?"
        " AND status IN ('new','confirmed')",
        (availability_id,),
    ).fetchone()
    conn.close()
    assert row is not None
    return row[0]


# --- Бронирование: создание (FR-47, NFR-8, MIN-1) ----------------------------


def test_s5_booking_create_and_lesson_date_boundary(api, client):
    """TC-S5BE-015 (change add-booking-docs, задача 4.1, FR-47, MIN-1):
    бронь создается status='new' и видна инструктору; ГРАНИЦА ДАТЫ:
    lesson_date = ближайшая будущая дата weekday по ЛОКАЛЬНОЙ дате
    сервера (слот сегодняшнего weekday → сегодня; завтрашнего → завтра);
    слот другого инструктора (нет с ним пары) → 404; несуществующий →
    404; без пары → 403."""
    env = setup_pair(
        client,
        intervals=[
            {"weekday": datetime.date.today().weekday(),
             "start_time": "10:00", "end_time": "11:00"},
            {"weekday": (datetime.date.today().weekday() + 1) % 7,
             "start_time": "12:00", "end_time": "13:00"},
        ],
    )
    instr, student = env["instr"], env["student"]
    conn = sqlite3.connect(db_path())
    slots = {
        row[0]: row[1]
        for row in conn.execute(
            "SELECT id, weekday FROM availability WHERE instructor_id = ?",
            (instr["id"],),
        ).fetchall()
    }
    conn.close()
    today = datetime.date.today()
    by_weekday = {weekday: sid for sid, weekday in slots.items()}

    resp_today = book(client, student["token"], by_weekday[today.weekday()])
    assert resp_today.status_code == 200, resp_today.text
    assert resp_today.json()["status"] == "new"
    assert resp_today.json()["lesson_date"] == today.isoformat()

    resp_tomorrow = book(
        client, student["token"], by_weekday[(today.weekday() + 1) % 7]
    )
    assert resp_tomorrow.status_code == 200
    assert resp_tomorrow.json()["lesson_date"] == (
        today + datetime.timedelta(days=1)
    ).isoformat()

    # видна инструктору: ученик (ФИО), слот, статус
    incoming = client.get(
        "/api/instructor/bookings", headers=_headers(instr["token"])
    ).json()["bookings"]
    assert len(incoming) == 2
    assert incoming[0]["status"] == "new"
    assert "Анна" in incoming[0]["student_full_name"]

    # чужой слот (инструктор, с которым нет пары) → 404
    other = create_instructor(client, email="other@example.com")
    put_availability(
        client, other["token"],
        [{"weekday": 2, "start_time": "09:00", "end_time": "10:00"}],
    )
    conn = sqlite3.connect(db_path())
    other_slot = conn.execute(
        "SELECT id FROM availability WHERE instructor_id = ?",
        (other["id"],),
    ).fetchone()[0]
    conn.close()
    assert book(client, student["token"], other_slot).status_code == 404
    assert book(client, student["token"], 999999).status_code == 404

    # совсем без пары → 403 (прямой вызов)
    loner = create_student(client, email="loner@example.com")
    assert book(client, loner["token"], other_slot).status_code == 403


def test_s5_booking_conflict_409_no_record(api, client):
    """TC-S5BE-016 (change add-booking-docs, задача 4.1, FR-47, NFR-8):
    бронь занятого слота → 409 без записи (частичный UNIQUE); повторный
    запрос на СВОЙ слот «на рассмотрении» → 409; после отклонения
    повторный запрос создается (ОВ-5)."""
    env = setup_pair(client)
    instr, student = env["instr"], env["student"]
    slot_id = first_slot_id(client, student["token"], instr["id"])

    first = book(client, student["token"], slot_id)
    assert first.status_code == 200
    booking_id = first.json()["booking_id"]

    # чужой (второй принятый) ученик на тот же слот
    student2 = create_student(client, email="student2@example.com")
    req2 = client.post(
        "/api/student/requests",
        json={"instructor_id": instr["id"]},
        headers=_headers(student2["token"]),
    )
    client.post(
        f"/api/instructor/requests/{req2.json()['request_id']}/accept",
        json={"car_id": env["car_id"]},
        headers=_headers(instr["token"]),
    )
    conflict = book(client, student2["token"], slot_id)
    assert conflict.status_code == 409
    assert "занят" in conflict.json()["error"]

    # повторный запрос на свой pending → 409
    dup = book(client, student["token"], slot_id)
    assert dup.status_code == 409

    conn = sqlite3.connect(db_path())
    count = conn.execute(
        "SELECT COUNT(*) FROM booking WHERE availability_id = ?", (slot_id,)
    ).fetchone()[0]
    conn.close()
    assert count == 1, "409 — без записи"

    # reject освобождает слот → повторный запрос создается (ОВ-5)
    assert client.post(
        f"/api/instructor/bookings/{booking_id}/reject",
        json={"comment": "окно занято"},
        headers=_headers(instr["token"]),
    ).status_code == 200
    retry = book(client, student2["token"], slot_id)
    assert retry.status_code == 200, retry.text


def test_s5_booking_race_two_students_one_409(api, client):
    """TC-S5BE-017 (change add-booking-docs, задача 4.1, NFR-8): ГОНКИ:
    два параллельных POST на один слот — максимум одна бронь, вторая
    получает 409 (BEGIN IMMEDIATE + частичный UNIQUE, без молчаливой
    порчи)."""
    env = setup_pair(client)
    instr = env["instr"]
    student2 = create_student(client, email="student2@example.com")
    req2 = client.post(
        "/api/student/requests",
        json={"instructor_id": instr["id"]},
        headers=_headers(student2["token"]),
    )
    client.post(
        f"/api/instructor/requests/{req2.json()['request_id']}/accept",
        json={"car_id": env["car_id"]},
        headers=_headers(instr["token"]),
    )

    conn = sqlite3.connect(db_path())
    slot_id = conn.execute(
        "SELECT id FROM availability WHERE instructor_id = ?"
        " ORDER BY id LIMIT 1",
        (instr["id"],),
    ).fetchone()[0]
    conn.close()

    barrier = threading.Barrier(2)
    results = []

    def worker(token):
        barrier.wait()
        resp = book(client, token, slot_id)
        results.append(resp.status_code)

    t1 = threading.Thread(target=worker, args=(env["student"]["token"],))
    t2 = threading.Thread(target=worker, args=(student2["token"],))
    t1.start()
    t2.start()
    t1.join(30)
    t2.join(30)

    assert sorted(results) == [200, 409], results
    conn = sqlite3.connect(db_path())
    active = conn.execute(
        "SELECT COUNT(*) FROM booking WHERE availability_id = ?"
        " AND status IN ('new','confirmed')",
        (slot_id,),
    ).fetchone()[0]
    conn.close()
    assert active == 1, "ровно одна активная бронь на слот"


# --- Бронирование: решения инструктора (FR-48, ОВ-2) -------------------------


def test_s5_confirm_flow(api, client):
    """TC-S5BE-018 (change add-booking-docs, задача 4.1, FR-48): confirm —
    своя и 'new' → confirmed + decided_at, виден в обоих календарях с
    учеником и авто; повторный confirm → 409; чужая бронь → 404."""
    env = setup_pair(client)
    instr, student = env["instr"], env["student"]
    slot_id = first_slot_id(client, student["token"], instr["id"])
    booking_id = book(client, student["token"], slot_id).json()["booking_id"]

    other = create_instructor(client, email="other@example.com")
    assert client.post(
        f"/api/instructor/bookings/{booking_id}/confirm",
        headers=_headers(other["token"]),
    ).status_code == 404

    confirmed = client.post(
        f"/api/instructor/bookings/{booking_id}/confirm",
        headers=_headers(instr["token"]),
    )
    assert confirmed.status_code == 200, confirmed.text
    row = fetch_booking(booking_id)
    assert row["status"] == "confirmed"
    assert row["decided_at"] is not None

    assert client.post(
        f"/api/instructor/bookings/{booking_id}/confirm",
        headers=_headers(instr["token"]),
    ).status_code == 409

    instructor_view = client.get(
        "/api/instructor/bookings", headers=_headers(instr["token"])
    ).json()["bookings"][0]
    assert instructor_view["status"] == "confirmed"
    assert instructor_view["car"]["id"] == env["car_id"]

    student_view = client.get(
        "/api/student/bookings", headers=_headers(student["token"])
    ).json()["bookings"][0]
    assert student_view["status"] == "confirmed"
    assert "Иванов" in student_view["instructor_full_name"]


def test_s5_reject_requires_comment_and_frees_slot(api, client):
    """TC-S5BE-019 (change add-booking-docs, задача 4.1, FR-48, ОВ-2):
    reject без комментария (пустой/отсутствующий) → 422, действие
    заблокировано, статус остается 'new'; с комментарием → 'rejected' +
    reject_comment виден ученику; чужая бронь → 404; повторный reject →
    409."""
    env = setup_pair(client)
    instr, student = env["instr"], env["student"]
    slot_id = first_slot_id(client, student["token"], instr["id"])
    booking_id = book(client, student["token"], slot_id).json()["booking_id"]

    other = create_instructor(client, email="other@example.com")
    assert client.post(
        f"/api/instructor/bookings/{booking_id}/reject",
        json={"comment": "x"},
        headers=_headers(other["token"]),
    ).status_code == 404

    empty = client.post(
        f"/api/instructor/bookings/{booking_id}/reject",
        json={"comment": "   "},
        headers=_headers(instr["token"]),
    )
    assert empty.status_code == 422
    missing = client.post(
        f"/api/instructor/bookings/{booking_id}/reject",
        headers=_headers(instr["token"]),
    )
    assert missing.status_code == 422
    assert fetch_booking(booking_id)["status"] == "new", (
        "reject без комментария заблокирован — статус не меняется"
    )

    rejected = client.post(
        f"/api/instructor/bookings/{booking_id}/reject",
        json={"comment": "В это окно не работаю"},
        headers=_headers(instr["token"]),
    )
    assert rejected.status_code == 200
    assert client.post(
        f"/api/instructor/bookings/{booking_id}/reject",
        json={"comment": "повтор"},
        headers=_headers(instr["token"]),
    ).status_code == 409

    view = client.get(
        "/api/student/bookings", headers=_headers(student["token"])
    ).json()["bookings"][0]
    assert view["status"] == "rejected"
    assert view["reject_comment"] == "В это окно не работаю"

    # m-2 review-001: инструкторский список тоже отдает reject_comment —
    # фронт рендерит «Ваш комментарий при отказе» из этого поля
    instructor_view = client.get(
        "/api/instructor/bookings", headers=_headers(instr["token"])
    ).json()["bookings"][0]
    assert instructor_view["status"] == "rejected"
    assert instructor_view["reject_comment"] == "В это окно не работаю"


def test_s5_cancel_confirmed_booking_frees_slot(api, client):
    """BUG-049 (скрины Заказчика 2026-10-23): cancel подтвержденной брони —
    по 'new' → 409 (решения по 'new' — confirm/reject); чужая бронь → 404;
    своя confirmed → 200, статус 'rejected' (CHECK в db.py статуса
    'cancelled' не знает), decided_at проставлен, reject_comment NULL
    (отмена без комментария — за инструктора текст не пишем); повторный
    cancel → 409; слот освобождается — повторный запрос ученика проходит."""
    env = setup_pair(client)
    instr, student = env["instr"], env["student"]
    slot_id = first_slot_id(client, student["token"], instr["id"])
    booking_id = book(client, student["token"], slot_id).json()["booking_id"]

    # guard-статус 'confirmed': по 'new' отмена недоступна
    assert client.post(
        f"/api/instructor/bookings/{booking_id}/cancel",
        headers=_headers(instr["token"]),
    ).status_code == 409

    assert client.post(
        f"/api/instructor/bookings/{booking_id}/confirm",
        headers=_headers(instr["token"]),
    ).status_code == 200

    other = create_instructor(client, email="other-cancel@example.com")
    assert client.post(
        f"/api/instructor/bookings/{booking_id}/cancel",
        headers=_headers(other["token"]),
    ).status_code == 404

    cancelled = client.post(
        f"/api/instructor/bookings/{booking_id}/cancel",
        headers=_headers(instr["token"]),
    )
    assert cancelled.status_code == 200, cancelled.text
    row = fetch_booking(booking_id)
    assert row["status"] == "rejected"
    assert row["decided_at"] is not None
    assert row["reject_comment"] is None

    # единственность решения: повторная отмена → 409
    assert client.post(
        f"/api/instructor/bookings/{booking_id}/cancel",
        headers=_headers(instr["token"]),
    ).status_code == 409

    # ОВ-5: слот освободился — повторный запрос ученика проходит
    rebook = book(client, student["token"], slot_id)
    assert rebook.status_code == 200, rebook.text


# --- PUT availability × активные брони (MAJ-1) -------------------------------


def test_s5_put_availability_blocked_by_active_bookings(api, client):
    """TC-S5BE-020 (change add-booking-docs, задача 4.1, MAJ-1, NFR-8):
    PUT графика без слота с активной бронью ('new'/'confirmed') → 409 с
    ПЕРЕЧНЕМ затронутых слотов, график НЕ изменен; после решения брони
    (confirm/reject) сохранение проходит; слот с только 'rejected' не
    мешает."""
    env = setup_pair(
        client,
        intervals=[
            {"weekday": 0, "start_time": "10:00", "end_time": "11:00"},
            {"weekday": 1, "start_time": "12:00", "end_time": "13:00"},
        ],
    )
    instr, student = env["instr"], env["student"]
    conn = sqlite3.connect(db_path())
    slot_mon = conn.execute(
        "SELECT id FROM availability WHERE instructor_id = ?"
        " AND weekday = 0", (instr["id"],)
    ).fetchone()[0]
    conn.close()

    booking_id = book(client, student["token"], slot_mon).json()["booking_id"]

    # пытаемся заменить график без понедельника → 409
    denied = put_availability(
        client, instr["token"],
        [{"weekday": 1, "start_time": "12:00", "end_time": "13:00"}],
    )
    assert denied.status_code == 409
    body = denied.json()
    assert "10:00" in body["error"] and "11:00" in body["error"]
    assert body["conflicts"][0]["weekday"] == 0
    assert body["conflicts"][0]["booking_statuses"] == ["new"]

    # график прежний
    still = client.get(
        "/api/instructor/availability", headers=_headers(instr["token"])
    ).json()["intervals"]
    assert {"weekday": 0, "start_time": "10:00", "end_time": "11:00"} in still

    # reject брони → сохранение проходит; слот с только 'rejected' не мешает
    client.post(
        f"/api/instructor/bookings/{booking_id}/reject",
        json={"comment": "нет окна"},
        headers=_headers(instr["token"]),
    )
    replaced = put_availability(
        client, instr["token"],
        [{"weekday": 1, "start_time": "12:00", "end_time": "13:00"}],
    )
    assert replaced.status_code == 200, replaced.text

    # и с подтвержденной бронью — тоже блокирует до решения
    put_availability(
        client, instr["token"],
        [
            {"weekday": 0, "start_time": "10:00", "end_time": "11:00"},
            {"weekday": 1, "start_time": "12:00", "end_time": "13:00"},
        ],
    )
    slot_mon = first_slot_id(client, student["token"], instr["id"])
    booking2 = book(client, student["token"], slot_mon).json()["booking_id"]
    client.post(
        f"/api/instructor/bookings/{booking2}/confirm",
        headers=_headers(instr["token"]),
    )
    denied2 = put_availability(
        client, instr["token"],
        [{"weekday": 1, "start_time": "12:00", "end_time": "13:00"}],
    )
    assert denied2.status_code == 409
    assert denied2.json()["conflicts"][0]["booking_statuses"] == ["confirmed"]


def test_s5_put_availability_vs_booking_race_no_orphan(api, client, monkeypatch):
    """TC-S5BE-025 (change add-booking-docs, M-3 review-001, NFR-8): бронь,
    созданная в окне между проверкой конфликтов и удалением слотов, НЕ
    становится сиротой. BEGIN IMMEDIATE до blocking_bookings сериализует
    PUT с create_booking (тоже BEGIN IMMEDIATE): «проигравшая» запись
    брони блокируется write-локом (брони нет), «выигравшая» отклоняет PUT
    (409, слот сохранен). Комбинация «бронь жива + слот удален» (бронь-
    сирота без FK) невозможна."""
    env = setup_pair(
        client,
        intervals=[
            {"weekday": 0, "start_time": "10:00", "end_time": "11:00"},
            {"weekday": 1, "start_time": "12:00", "end_time": "13:00"},
        ],
    )
    instr, student = env["instr"], env["student"]
    conn = sqlite3.connect(db_path())
    slot_mon = conn.execute(
        "SELECT id FROM availability WHERE instructor_id = ? AND weekday = 0",
        (instr["id"],),
    ).fetchone()[0]
    conn.close()

    import backend.instructor_availability as ia

    orig = ia.blocking_bookings
    race: dict = {}

    def check_then_race(conn_, instructor_id_, intervals_):
        # Окно M-3: сразу после проверки конфликтов ученик создает бронь
        # на удаляемый слот ОТДЕЛЬНЫМ соединением (короткий busy_timeout).
        # Без фикса проверка шла в autocommit → INSERT проходит, и PUT
        # молча удаляет слот под живой бронью (бронь-сирота); с фиксом
        # write-лок BEGIN IMMEDIATE сериализует — INSERT получает
        # OperationalError «database is locked».
        conflicts = orig(conn_, instructor_id_, intervals_)
        try:
            rc = sqlite3.connect(db_path(), timeout=0.25)
            try:
                rc.execute(
                    "INSERT INTO booking (student_id, instructor_id,"
                    " availability_id, lesson_date, status)"
                    " VALUES (?, ?, ?, ?, 'new')",
                    (student["id"], instr["id"], slot_mon, "2026-01-05"),
                )
                rc.commit()
                race["created"] = True
            finally:
                rc.close()
        except sqlite3.OperationalError:
            race["created"] = False
        return conflicts

    monkeypatch.setattr(ia, "blocking_bookings", check_then_race)
    resp = put_availability(
        client, instr["token"],
        [{"weekday": 1, "start_time": "12:00", "end_time": "13:00"}],
    )

    conn = sqlite3.connect(db_path())
    slot_alive = conn.execute(
        "SELECT COUNT(*) FROM availability WHERE id = ?", (slot_mon,)
    ).fetchone()[0]
    bookings = conn.execute(
        "SELECT COUNT(*) FROM booking WHERE availability_id = ?", (slot_mon,)
    ).fetchone()[0]
    conn.close()

    if race["created"]:
        # бронь успела до захвата лока → PUT обязан отклонить замену
        assert resp.status_code == 409
        assert slot_alive == 1 and bookings == 1
    else:
        # запись сериализована write-локом PUT'а — брони нет
        assert resp.status_code == 200, resp.text
        assert bookings == 0, "заблокированная запись не оставила записи"
    # главный инвариант: бронь-сирота невозможна ни в одной ветке
    assert not (bookings and not slot_alive)


# --- MIN-3: пустое авто в календарях; FR-49: «Занятия на сегодня» ------------


def test_s5_calendars_survive_car_deletion(api, client):
    """TC-S5BE-021 (change add-booking-docs, задача 4.1, MIN-3): авто пары
    удален (car_id NULL) → календарь ученика и инструктора возвращают
    бронь с пустым авто (car = null), не ошибку."""
    env = setup_pair(client)
    instr, student = env["instr"], env["student"]
    slot_id = first_slot_id(client, student["token"], instr["id"])
    booking_id = book(client, student["token"], slot_id).json()["booking_id"]
    client.post(
        f"/api/instructor/bookings/{booking_id}/confirm",
        headers=_headers(instr["token"]),
    )

    deleted = client.delete(
        f"/api/instructor/cars/{env['car_id']}",
        headers=_headers(instr["token"]),
    )
    assert deleted.status_code == 200

    student_view = client.get(
        "/api/student/bookings", headers=_headers(student["token"])
    )
    assert student_view.status_code == 200
    assert student_view.json()["bookings"][0]["car"] is None
    instructor_view = client.get(
        "/api/instructor/bookings", headers=_headers(instr["token"])
    )
    assert instructor_view.status_code == 200
    assert instructor_view.json()["bookings"][0]["car"] is None


def test_s5_summary_today_lessons(api, client):
    """TC-S5BE-022 (change add-booking-docs, задача 4.2, FR-49, ОВ-6,
    MIN-1/MIN-3): today_lessons — подтвержденные брони на СЕГОДНЯ (по
    локальной дате сервера, то же правило, что lesson_date); брони на
    другую дату не попадают; пусто → []; перекрепление авто видно, после
    удаления авто — запись остается с пустым авто."""
    env = setup_pair(
        client,
        intervals=[
            {"weekday": datetime.date.today().weekday(),
             "start_time": "10:00", "end_time": "11:00"},
            {"weekday": (datetime.date.today().weekday() + 1) % 7,
             "start_time": "12:00", "end_time": "13:00"},
        ],
    )
    instr, student = env["instr"], env["student"]
    empty = client.get(
        "/api/instructor/summary", headers=_headers(instr["token"])
    ).json()
    assert empty["today_lessons"] == []

    conn = sqlite3.connect(db_path())
    slots_by_weekday = {
        row[1]: row[0]
        for row in conn.execute(
            "SELECT id, weekday FROM availability WHERE instructor_id = ?",
            (instr["id"],),
        ).fetchall()
    }
    conn.close()
    today = datetime.date.today()
    slot_today = slots_by_weekday[today.weekday()]
    slot_other = slots_by_weekday[(today.weekday() + 1) % 7]

    b_today = book(client, student["token"], slot_today).json()["booking_id"]
    b_other = book(client, student["token"], slot_other).json()["booking_id"]
    for booking_id in (b_today, b_other):
        assert client.post(
            f"/api/instructor/bookings/{booking_id}/confirm",
            headers=_headers(instr["token"]),
        ).status_code == 200

    lessons = client.get(
        "/api/instructor/summary", headers=_headers(instr["token"])
    ).json()["today_lessons"]
    assert len(lessons) == 1
    lesson = lessons[0]
    assert lesson["booking_id"] == b_today
    assert lesson["lesson_date"] == today.isoformat()
    assert lesson["start_time"] == "10:00"
    assert "Анна" in lesson["student_full_name"]
    assert lesson["car"]["id"] == env["car_id"]

    # ОВ-6: перекрепление — в виджете новое авто
    car2 = add_car_json(
        client, instr["token"], brand="Lada", model="Kalina",
    )
    moved = client.patch(
        f"/api/instructor/students/{student['id']}/car",
        json={"car_id": car2},
        headers=_headers(instr["token"]),
    )
    assert moved.status_code == 200, moved.text
    lessons2 = client.get(
        "/api/instructor/summary", headers=_headers(instr["token"])
    ).json()["today_lessons"]
    assert lessons2[0]["car"]["id"] == car2

    # MIN-3: авто удален — запись виджета остается, авто пустое
    assert client.delete(
        f"/api/instructor/cars/{car2}", headers=_headers(instr["token"])
    ).status_code == 200
    lessons3 = client.get(
        "/api/instructor/summary", headers=_headers(instr["token"])
    ).json()["today_lessons"]
    assert len(lessons3) == 1
    assert lessons3[0]["car"] is None


# --- NFR-10: параметризованный SQL в новых модулях ----------------------------


def test_s5_new_modules_no_sql_concatenation():
    """TC-S5BE-023 (change add-booking-docs, NFR-10←NFR-3): в новых
    модулях Спринта 5 нет f-строк/конкатенаций/format() в SQL."""
    for name in ("booking.py", "instructor_documents.py",
                 "instructor_cars.py", "instructor_availability.py",
                 "instructor_summary.py"):
        src = (ROOT / "backend" / name).read_text(encoding="utf-8")
        for bad in ("f\"SELECT", "f'SELECT", "f\"INSERT", "f'INSERT",
                    "f\"UPDATE", "f'UPDATE", "f\"DELETE", "f'DELETE",
                    "+ \"SELECT", "\"SELECT \" +", "format(SELECT"):
            assert bad not in src, (name, bad)
