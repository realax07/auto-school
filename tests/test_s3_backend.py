"""Спринт 3, Партия A — BACKEND-тесты контура «инструктор ↔ ученик»
(change add-instructor-student-loop; задачи 1.1, 1.2, 2.1, 3.1, 4.1, 5.1,
6.1, 6.2, сборка 7.1).

Покрывают сценарии specs/ пакета: instructor-documents (FR-23/24/25, ОВ-5),
instructor-cars (FR-26/27/28, ОВ-3/5), instructor-availability (FR-29/30),
student-instructor-choice (FR-31/32/35, MIN-1), reviews (FR-34, NFR-2/5),
student-requests (FR-36/37/38/39, ОВ-1/2/4; MAJ-1/MAJ-2 итерации 2).

TC-трассировка не ведется (backend-тесты, не test-model). Фикстуры —
общий client из conftest (create_app() поверх чистой БД в tmp_path);
каталог загрузок переопределяется env AUTOSCHOOL_UPLOADS_DIR в tmp_path
(механика AUTOSCHOOL_DB_PATH). time.sleep запрещен (спека qa-pipeline).

Инструкторская учетка создается реальным флоу: apply → approve → login
(по паттерну tests/test_instructor_dashboard.py); ученик — /api/register.
"""
import os
import sqlite3
from pathlib import Path

import pytest

from conftest import admin_headers, db_path, register

ROOT = Path(__file__).resolve().parent.parent

JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 64  # валидные magic bytes JPEG
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64  # валидные magic bytes PNG
PDF_BYTES = b"%PDF-1.4\nfake-pdf-bytes\n"  # не изображение
OVERSIZE_JPEG = b"\xff\xd8\xff" + b"\x00" * (5 * 1024 * 1024 + 1)  # >5 МБ

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
    """Базовый валидный набор анкеты инструктора."""
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


def apply_instructor(client, **overrides):
    """POST /api/instructors/apply (JSON-путь, совместимость Спринтов 1–2)."""
    return client.post("/api/instructors/apply", json=apply_body(**overrides))


def approve_instructor(client, email):
    """approve заявки инструктора админ-токеном; возвращает user_id."""
    conn = sqlite3.connect(db_path())
    app_id = conn.execute(
        "SELECT id FROM instructor_applications WHERE email = ?", (email,)
    ).fetchone()[0]
    conn.close()
    resp = client.post(
        f"/api/admin/instructor-applications/{app_id}/approve",
        headers=admin_headers(client),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["user_id"]


def create_instructor(client, email="instr@example.com", experience_years=5):
    """Полный флоу: apply → approve → login; возвращает token и user_id."""
    resp = apply_instructor(
        client, email=email, experience_years=experience_years
    )
    assert resp.status_code == 200, resp.text
    user_id = approve_instructor(client, email)
    login = client.post(
        "/api/auth/login", json={"email": email, "password": INSTR_PASSWORD}
    )
    assert login.status_code == 200, login.text
    return {"token": login.json()["token"], "id": user_id, "email": email}


def create_student(client, email="student@example.com"):
    """Регистрация + вход ученика; возвращает token и user_id."""
    resp = register(
        client,
        email=email,
        phone="+7 (912) 345-67-89",
    )
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


def add_car(client, token, **overrides):
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


def create_request(client, student_token, instructor_id):
    resp = client.post(
        "/api/student/requests",
        json={"instructor_id": instructor_id},
        headers=_headers(student_token),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["request_id"]


def fetch_request_row(request_id):
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM student_requests WHERE id = ?", (request_id,)
    ).fetchone()
    conn.close()
    return row


# --- Миграции (db.py, idempotent) --------------------------------------------


def test_migration_creates_new_tables(client):
    """Задача 7.1: 4 таблицы контура созданы init_db (TestClient startup)."""
    conn = sqlite3.connect(db_path())
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    indexes = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        )
    }
    conn.close()
    assert {
        "instructor_cars",
        "availability",
        "reviews",
        "student_requests",
    } <= tables
    assert {
        "idx_instructor_cars_instructor",
        "idx_availability_instructor",
        "idx_reviews_instructor",
        "idx_student_requests_instructor",
        "idx_student_requests_student",
    } <= indexes


def test_migration_is_idempotent(client):
    """Повторный init_db не падает и не дублирует колонки/таблицы."""
    import backend.db as db

    db.init_db()
    db.init_db()
    conn = sqlite3.connect(db_path())
    license_columns = [
        row[1] for row in conn.execute("PRAGMA table_info(instructor_applications)")
    ]
    users_columns = [row[1] for row in conn.execute("PRAGMA table_info(users)")]
    conn.close()
    assert license_columns.count("license_photo_path") == 1
    assert license_columns.count("experience_years") == 1
    assert users_columns.count("experience_years") == 1


def test_migration_of_legacy_db_without_new_columns(client):
    """База, в которой уже есть записи users, повторно проходит init_db
    без пересоздания: записи остаются, колонки/таблицы добавлены (механика
    users.role — Спринты 0–2 поднимаются без потери данных)."""
    register(client)  # запись users в чистую БД
    conn = sqlite3.connect(db_path())
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] >= 1
    conn.close()

    import backend.db as db

    db.init_db()
    db.init_db()
    conn = sqlite3.connect(db_path())
    users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    assert users >= 1


# --- Домен instructor-cars ----------------------------------------------------


def test_cars_crud_happy_path(api, client):
    """Сценарий «Добавленный автомобиль появляется в списке владельца» +
    редактирование (FR-26, FR-28)."""
    instr = create_instructor(client)
    car_id = add_car(client, instr["token"])

    listed = client.get("/api/instructor/cars", headers=_headers(instr["token"]))
    assert listed.status_code == 200
    cars = listed.json()["cars"]
    assert len(cars) == 1
    assert cars[0]["id"] == car_id
    assert cars[0]["brand"] == "Škoda"
    assert cars[0]["transmission"] == "automatic"

    patched = client.patch(
        f"/api/instructor/cars/{car_id}",
        json={"plate": "В456ВВ777"},
        headers=_headers(instr["token"]),
    )
    assert patched.status_code == 200, patched.text
    cars = client.get(
        "/api/instructor/cars", headers=_headers(instr["token"])
    ).json()["cars"]
    assert cars[0]["plate"] == "В456ВВ777"
    # остальные поля не изменились
    assert cars[0]["brand"] == "Škoda"
    assert cars[0]["year"] == 2020


def test_cars_validation_422_per_field(api, client):
    """Сценарий «Невалидные данные автомобиля отклоняются» (FR-26):
    пустая марка / некорректный год / КПП вне значений → 422."""
    instr = create_instructor(client)
    base_car = {
        "brand": "Škoda",
        "model": "Rapid",
        "year": 2020,
        "plate": "А123АА777",
        "transmission": "automatic",
    }
    for payload, fragment in (
        ({"brand": "  "}, "Марка"),
        ({"year": 1899}, "Год"),
        ({"year": 2999}, "Год"),
        ({"transmission": "variator"}, "КПП"),
        ({"plate": ""}, "Госномер"),
    ):
        resp = client.post(
            "/api/instructor/cars",
            json={**base_car, **payload},
            headers=_headers(instr["token"]),
        )
        assert resp.status_code == 422, (payload, resp.text)
        assert fragment in resp.json()["error"]


def test_cars_access_401_403(api, client):
    """Сценарий «Доступ к разделу без инструкторской сессии отклоняется»:
    гость → 401, ученик → 403, список не возвращается."""
    resp = client.get("/api/instructor/cars")
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}

    student = create_student(client)
    resp = client.get("/api/instructor/cars", headers=_headers(student["token"]))
    assert resp.status_code == 403
    assert resp.json() == {"ok": False}


def test_car_not_visible_to_other_instructor_and_foreign_404(api, client):
    """Сценарии «Автомобиль не виден другому инструктору» и «Чужой
    автомобиль не редактируется и не удаляется» (404, не 403 — не
    раскрываем существование)."""
    first = create_instructor(client, email="first@example.com")
    second = create_instructor(client, email="second@example.com")
    car_id = add_car(client, first["token"])

    listed = client.get(
        "/api/instructor/cars", headers=_headers(second["token"])
    )
    assert listed.status_code == 200
    assert listed.json()["cars"] == []

    assert (
        client.patch(
            f"/api/instructor/cars/{car_id}",
            json={"plate": "Х000ХХ000"},
            headers=_headers(second["token"]),
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/instructor/cars/{car_id}",
            headers=_headers(second["token"]),
        ).status_code
        == 404
    )
    # авто не удален и не изменен
    cars = client.get(
        "/api/instructor/cars", headers=_headers(first["token"])
    ).json()["cars"]
    assert len(cars) == 1 and cars[0]["plate"] == "А123АА777"


def test_car_photo_upload_and_owner_only(api, client, tmp_path):
    """Сценарии фото (FR-27, MIN-2): JPEG привязан и выдается владельцу
    (image/jpeg); PDF/6 МБ → 422; другому инструктору/гостю не выдается;
    свой без фото → 404."""
    instr = create_instructor(client)
    car_id = add_car(client, instr["token"])

    # свой без фото → 404
    assert (
        client.get(
            f"/api/instructor/cars/{car_id}/photo",
            headers=_headers(instr["token"]),
        ).status_code
        == 404
    )

    # PDF → 422, фото не привязано
    bad_type = client.post(
        f"/api/instructor/cars/{car_id}/photo",
        files={"photo": ("doc.pdf", PDF_BYTES, "application/pdf")},
        headers=_headers(instr["token"]),
    )
    assert bad_type.status_code == 422
    assert "JPEG" in bad_type.json()["error"] or "PNG" in bad_type.json()["error"]

    # >5 МБ → 422 (сниффер отклоняет размер до записи)
    bad_size = client.post(
        f"/api/instructor/cars/{car_id}/photo",
        files={"photo": ("big.jpg", OVERSIZE_JPEG, "image/jpeg")},
        headers=_headers(instr["token"]),
    )
    assert bad_size.status_code == 422
    assert "5 МБ" in bad_size.json()["error"]

    # валидный JPEG: привязан, лежит в data/uploads/cars/ (env в tmp_path)
    uploaded = client.post(
        f"/api/instructor/cars/{car_id}/photo",
        files={"photo": ("car.jpg", JPEG_BYTES, "image/jpeg")},
        headers=_headers(instr["token"]),
    )
    assert uploaded.status_code == 200, uploaded.text

    got = client.get(
        f"/api/instructor/cars/{car_id}/photo",
        headers=_headers(instr["token"]),
    )
    assert got.status_code == 200
    assert got.headers["content-type"] == "image/jpeg"
    assert got.content == JPEG_BYTES

    conn = sqlite3.connect(db_path())
    stored_path = conn.execute(
        "SELECT photo_path FROM instructor_cars WHERE id = ?", (car_id,)
    ).fetchone()[0]
    conn.close()
    assert stored_path and Path(stored_path).read_bytes() == JPEG_BYTES
    assert "cars" in Path(stored_path).parts

    # PNG тоже принимается (magic bytes, не Content-Type клиента)
    other = create_instructor(client, email="other@example.com")
    other_car = add_car(client, other["token"])
    png_upload = client.post(
        f"/api/instructor/cars/{other_car}/photo",
        files={"photo": ("car.png", PNG_BYTES, "image/png")},
        headers=_headers(other["token"]),
    )
    assert png_upload.status_code == 200, png_upload.text
    png_get = client.get(
        f"/api/instructor/cars/{other_car}/photo",
        headers=_headers(other["token"]),
    )
    assert png_get.status_code == 200
    assert png_get.headers["content-type"] == "image/png"

    # чужой инструктор → 404; гость → 401; ученик → 403
    assert (
        client.get(
            f"/api/instructor/cars/{car_id}/photo",
            headers=_headers(other["token"]),
        ).status_code
        == 404
    )
    assert client.get(f"/api/instructor/cars/{car_id}/photo").status_code == 401
    student = create_student(client)
    assert (
        client.get(
            f"/api/instructor/cars/{car_id}/photo",
            headers=_headers(student["token"]),
        ).status_code
        == 403
    )


def test_car_delete_unbinds_student_keeps_link(api, client):
    """Сценарий «Удаление автомобиля снимает привязку, связь с
    инструктором сохраняется» (ОВ-3): car_id → NULL, статус accepted."""
    instr = create_instructor(client)
    car_id = add_car(client, instr["token"])
    student = create_student(client)
    request_id = create_request(client, student["token"], instr["id"])
    accepted = client.post(
        f"/api/instructor/requests/{request_id}/accept",
        json={"car_id": car_id},
        headers=_headers(instr["token"]),
    )
    assert accepted.status_code == 200, accepted.text

    deleted = client.delete(
        f"/api/instructor/cars/{car_id}", headers=_headers(instr["token"])
    )
    assert deleted.status_code == 200

    row = fetch_request_row(request_id)
    assert row["status"] == "accepted"
    assert row["car_id"] is None
    # ученик остался в «Моих учениках»
    summary = client.get(
        "/api/instructor/summary", headers=_headers(instr["token"])
    ).json()
    assert len(summary["students"]) == 1


# --- Домен instructor-availability --------------------------------------------


def test_availability_save_and_readback(api, client):
    """Сценарии «Выделенный интервал помечается рабочим» и «График
    восстанавливается после перезахода» (FR-29, FR-30)."""
    instr = create_instructor(client)
    payload = {"intervals": [{"weekday": 0, "start_time": "10:00",
                              "end_time": "14:00"}]}
    put = client.put(
        "/api/instructor/availability", json=payload, headers=_headers(instr["token"])
    )
    assert put.status_code == 200, put.text

    # «перезаход»: новая сессия
    login = client.post(
        "/api/auth/login",
        json={"email": instr["email"], "password": INSTR_PASSWORD},
    )
    fresh = client.get(
        "/api/instructor/availability", headers=_headers(login.json()["token"])
    )
    assert fresh.status_code == 200
    assert fresh.json()["intervals"] == [
        {"weekday": 0, "start_time": "10:00", "end_time": "14:00"}
    ]


def test_availability_full_replace_and_dedup(api, client):
    """Сценарий «Изменение графика перезаписывает сохраненный» (FR-30);
    дубликаты схлопываются (design.md блок 3)."""
    instr = create_instructor(client)
    first = {"intervals": [{"weekday": 0, "start_time": "10:00",
                            "end_time": "14:00"}]}
    assert (
        client.put(
            "/api/instructor/availability",
            json=first,
            headers=_headers(instr["token"]),
        ).status_code
        == 200
    )
    second = {
        "intervals": [
            {"weekday": 2, "start_time": "09:00", "end_time": "12:00"},
            {"weekday": 2, "start_time": "09:00", "end_time": "12:00"},
        ]
    }
    put = client.put(
        "/api/instructor/availability",
        json=second,
        headers=_headers(instr["token"]),
    )
    assert put.status_code == 200
    intervals = client.get(
        "/api/instructor/availability", headers=_headers(instr["token"])
    ).json()["intervals"]
    assert intervals == [{"weekday": 2, "start_time": "09:00", "end_time": "12:00"}]


def test_availability_validation_422(api, client):
    """Сценарий «Некорректный интервал отклоняется»: Пн 14:00–10:00 → 422,
    график не сохраняется; weekday вне 0..6 и не-ЧЧ:ММ → 422."""
    instr = create_instructor(client)
    bad = client.put(
        "/api/instructor/availability",
        json={"intervals": [{"weekday": 0, "start_time": "14:00",
                             "end_time": "10:00"}]},
        headers=_headers(instr["token"]),
    )
    assert bad.status_code == 422
    for payload in (
        {"intervals": [{"weekday": 7, "start_time": "10:00", "end_time": "12:00"}]},
        {"intervals": [{"weekday": 0, "start_time": "25:00", "end_time": "26:00"}]},
    ):
        resp = client.put(
            "/api/instructor/availability",
            json=payload,
            headers=_headers(instr["token"]),
        )
        assert resp.status_code == 422, resp.text
    # график остался пустым
    intervals = client.get(
        "/api/instructor/availability", headers=_headers(instr["token"])
    ).json()["intervals"]
    assert intervals == []


def test_availability_access_401_403(api, client):
    """Сценарий «Доступ к календарю без инструкторской сессии отклоняется»."""
    assert client.get("/api/instructor/availability").status_code == 401
    student = create_student(client)
    resp = client.get(
        "/api/instructor/availability", headers=_headers(student["token"])
    )
    assert resp.status_code == 403


# --- Домен instructor-documents ------------------------------------------------


def test_apply_multipart_saves_license_image(api, client, tmp_path):
    """Сценарий «Заявка с изображением ВУ сохраняет файл» (FR-23): файл в
    data/uploads/license/ (env → tmp_path), license_photo_path в заявке;
    без файла — заявка создается с NULL (правило необязательности, задача
    3.3 не зафиксировала обязательность)."""
    resp = client.post(
        "/api/instructors/apply",
        data={k: str(v) for k, v in apply_body(email="withdoc@example.com").items()},
        files={"license_photo": ("license.jpg", JPEG_BYTES, "image/jpeg")},
    )
    assert resp.status_code == 200, resp.text

    conn = sqlite3.connect(db_path())
    row = conn.execute(
        "SELECT license_photo_path FROM instructor_applications"
        " WHERE email = ?",
        ("withdoc@example.com",),
    ).fetchone()
    conn.close()
    assert row[0], "license_photo_path должен быть сохранен"
    stored = Path(row[0])
    assert stored.read_bytes() == JPEG_BYTES
    assert "license" in stored.parts

    # без файла — создается, path NULL
    resp = apply_instructor(client, email="nodoc@example.com")
    assert resp.status_code == 200, resp.text
    conn = sqlite3.connect(db_path())
    null_row = conn.execute(
        "SELECT license_photo_path FROM instructor_applications"
        " WHERE email = ?",
        ("nodoc@example.com",),
    ).fetchone()
    conn.close()
    assert null_row[0] is None


def test_apply_rejects_bad_file_type_and_size(api, client):
    """Сценарии «Файл недопустимого типа отклоняется» и «Файл больше 5 МБ
    отклоняется» (ОВ-5, NFR-6): 422, заявка НЕ создается; проверка по
    содержимому — JPEG-магия с image/png Content-Type тоже отвергается
    корректно (доверяем байтам, не заголовкам)."""
    resp = client.post(
        "/api/instructors/apply",
        data={k: str(v) for k, v in apply_body(email="pdf@example.com").items()},
        files={"license_photo": ("doc.pdf", PDF_BYTES, "application/pdf")},
    )
    assert resp.status_code == 422
    resp = client.post(
        "/api/instructors/apply",
        data={k: str(v) for k, v in apply_body(email="big@example.com").items()},
        files={"license_photo": ("big.jpg", OVERSIZE_JPEG, "image/jpeg")},
    )
    assert resp.status_code == 422
    assert "5 МБ" in resp.json()["error"]

    conn = sqlite3.connect(db_path())
    count = conn.execute(
        "SELECT COUNT(*) FROM instructor_applications"
        " WHERE email IN (?, ?)",
        ("pdf@example.com", "big@example.com"),
    ).fetchone()[0]
    conn.close()
    assert count == 0, "заявка при невалидном файле не должна создаваться"


def test_apply_experience_years_validation_and_transfer(api, client):
    """MAJ-3 (arch-review итерация 2): стаж числом ≥ 0 → иначе 422;
    approve переносит стаж в users.experience_years."""
    resp = apply_instructor(client, email="neg@example.com", experience_years=-1)
    assert resp.status_code == 422
    assert "Стаж" in resp.json()["error"]

    resp = apply_instructor(client, experience_years=5)
    assert resp.status_code == 200, resp.text
    user_id = approve_instructor(client, "instr@example.com")
    conn = sqlite3.connect(db_path())
    years = conn.execute(
        "SELECT experience_years FROM users WHERE id = ?", (user_id,)
    ).fetchone()[0]
    conn.close()
    assert years == 5


# --- Домен instructor-documents: админ-карточка и выдача ВУ (FR-24/25) ----------


def test_admin_card_and_license_image(api, client):
    """Сценарии «Админ с валидным токеном получает изображение», «без
    токена», «с неверным токеном», «ученическая сессия не дает доступ»
    (FR-24, NFR-1); карточка заявки — полные данные + факт ВУ (FR-25)."""
    resp = client.post(
        "/api/instructors/apply",
        data={k: str(v) for k, v in apply_body(email="doc@example.com").items()},
        files={"license_photo": ("license.png", PNG_BYTES, "image/png")},
    )
    assert resp.status_code == 200, resp.text
    conn = sqlite3.connect(db_path())
    app_id = conn.execute(
        "SELECT id FROM instructor_applications WHERE email = ?",
        ("doc@example.com",),
    ).fetchone()[0]
    conn.close()

    base = f"/api/admin/instructor-applications/{app_id}"

    # карточка: валидный токен → 200 + данные + путь; без токена → 401
    card = client.get(base, headers=admin_headers(client))
    assert card.status_code == 200
    application = card.json()["application"]
    assert application["license_photo_path"]
    assert application["license_number"] == "9911223344"
    assert "password_hash" not in application
    assert client.get(base).status_code == 401
    assert (
        client.get(
            "/api/admin/instructor-applications/999999",
            headers=admin_headers(client),
        ).status_code
        == 404
    )

    # изображение: валидный токен → 200 image/png; иначе 401/404
    image = client.get(f"{base}/license-image", headers=admin_headers(client))
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"
    assert image.content == PNG_BYTES
    assert client.get(f"{base}/license-image").status_code == 401
    assert (
        client.get(
            f"{base}/license-image",
            headers={"X-Admin-Token": "wrong-token"},
        ).status_code
        == 401
    )
    student = create_student(client)
    assert (
        client.get(
            f"{base}/license-image", headers=_headers(student["token"])
        ).status_code
        == 401
    )
    # заявка без ВУ → 404
    apply_instructor(client, email="plain@example.com")
    conn = sqlite3.connect(db_path())
    plain_id = conn.execute(
        "SELECT id FROM instructor_applications WHERE email = ?",
        ("plain@example.com",),
    ).fetchone()[0]
    conn.close()
    no_doc = client.get(
        f"/api/admin/instructor-applications/{plain_id}/license-image",
        headers=admin_headers(client),
    )
    assert no_doc.status_code == 404


def test_license_image_direct_url_not_served(api, client):
    """Сценарий «Прямой URL файла не работает» (NFR-1): каталог загрузок
    не входит в раздаваемую статику."""
    resp = client.post(
        "/api/instructors/apply",
        data={k: str(v) for k, v in apply_body(email="direct@example.com").items()},
        files={"license_photo": ("license.jpg", JPEG_BYTES, "image/jpeg")},
    )
    assert resp.status_code == 200, resp.text
    conn = sqlite3.connect(db_path())
    stored = conn.execute(
        "SELECT license_photo_path FROM instructor_applications"
        " WHERE email = ?",
        ("direct@example.com",),
    ).fetchone()[0]
    conn.close()
    relative = str(Path(stored).relative_to(ROOT)) if stored.startswith(str(ROOT)) \
        else Path(stored).as_posix()
    assert client.get(f"/{relative}").status_code == 404


# --- Домен student-instructor-choice -------------------------------------------


def test_marketplace_lists_only_approved(api, client):
    """Сценарий «Ученик видит карточки одобренных инструкторов» +
    «waiting/deny не попадают в каталог» (FR-31): users.role заводится
    только approve; карточка содержит ФИО, стаж, авто без фото/госномера,
    рейтинг, часы работы."""
    instr = create_instructor(client, experience_years=7)
    add_car(client, instr["token"])
    client.put(
        "/api/instructor/availability",
        json={"intervals": [{"weekday": 0, "start_time": "10:00",
                             "end_time": "14:00"}]},
        headers=_headers(instr["token"]),
    )
    # заявка в waiting — в users записи нет
    apply_instructor(client, email="waiting@example.com")

    student = create_student(client)
    resp = client.get(
        "/api/student/instructors", headers=_headers(student["token"])
    )
    assert resp.status_code == 200
    instructors = resp.json()["instructors"]
    assert len(instructors) == 1
    card = instructors[0]
    assert card["id"] == instr["id"]
    assert card["full_name"] == "Иванов Иван Иванович"
    assert card["experience_years"] == 7
    assert card["cars"][0]["brand"] == "Škoda"
    assert "plate" not in card["cars"][0]
    assert "photo_path" not in card["cars"][0]
    assert card["rating"] == {"has_reviews": False}
    assert card["availability"] == [
        {"weekday": 0, "start_time": "10:00", "end_time": "14:00"}
    ]


def test_marketplace_access_401_403(api, client):
    """Сценарий «Каталог недоступен без сессии ученика»: гость → 401,
    инструктор → 403."""
    assert client.get("/api/student/instructors").status_code == 401
    instr = create_instructor(client)
    resp = client.get(
        "/api/student/instructors", headers=_headers(instr["token"])
    )
    assert resp.status_code == 403


def test_marketplace_filters(api, client):
    """Сценарии фильтров (FR-32): по КПП, по рейтингу (MIN-1: без отзывов
    не проходит min_rating>0, проходит min_rating=0), по стажу, по
    свободному времени; пустой результат — 200 [] (пустое состояние)."""
    auto = create_instructor(client, email="auto@example.com", experience_years=3)
    add_car(client, auto["token"])  # automatic
    manual = create_instructor(client, email="manual@example.com", experience_years=10)
    manual_car = add_car(
        client, manual["token"], transmission="manual", plate="В777ВВ777"
    )
    client.put(
        "/api/instructor/availability",
        json={"intervals": [{"weekday": 0, "start_time": "10:00",
                             "end_time": "12:00"}]},
        headers=_headers(manual["token"]),
    )
    # отзыв manual-инструктору: ученик принят им
    student = create_student(client)
    rid = create_request(client, student["token"], manual["id"])
    client.post(
        f"/api/instructor/requests/{rid}/accept",
        json={"car_id": manual_car},
        headers=_headers(manual["token"]),
    )
    client.post(
        f"/api/student/instructors/{manual['id']}/reviews",
        json={"rating": 5, "text": "Отличный инструктор"},
        headers=_headers(student["token"]),
    )

    def ids(query):
        resp = client.get(
            f"/api/student/instructors{query}",
            headers=_headers(student["token"]),
        )
        assert resp.status_code == 200, resp.text
        return [c["id"] for c in resp.json()["instructors"]]

    # фильтр по КПП: механика → только manual-инструктор
    assert "?transmission=manual" and ids("?transmission=manual") == [manual["id"]]
    assert ids("?transmission=automatic") == [auto["id"]]
    assert client.get(
        "/api/student/instructors?transmission=variator",
        headers=_headers(student["token"]),
    ).status_code == 422

    # фильтр по рейтингу: auto без отзывов — при min_rating=4 не проходит,
    # при min_rating=0 проходит (MIN-1)
    assert ids("?min_rating=4") == [manual["id"]]
    assert set(ids("?min_rating=0")) == {auto["id"], manual["id"]}
    assert client.get(
        "/api/student/instructors?min_rating=6",
        headers=_headers(student["token"]),
    ).status_code == 422

    # фильтр по стажу
    assert ids("?min_experience=5") == [manual["id"]]
    assert set(ids("?min_experience=1")) == {auto["id"], manual["id"]}

    # фильтр по свободному времени: пересечение Пн 10:00–11:00 → manual
    assert ids("?free_weekday=0&free_from=10:00&free_to=11:00") == [manual["id"]]
    # непересекающийся интервал → пустой результат 200 (пустое состояние)
    assert ids("?free_weekday=4&free_from=18:00&free_to=20:00") == []
    assert client.get(
        "/api/student/instructors?free_weekday=0",
        headers=_headers(student["token"]),
    ).status_code == 422


def _any_car_id(instructor_id):
    conn = sqlite3.connect(db_path())
    car_id = conn.execute(
        "SELECT id FROM instructor_cars WHERE instructor_id = ? ORDER BY id LIMIT 1",
        (instructor_id,),
    ).fetchone()[0]
    conn.close()
    return car_id


def test_marketplace_card_detail_and_aggregate(api, client):
    """Сценарии агрегата (FR-35): {average, count} при отзывах (5,4 → 4.5,
    count 2); «нет отзывов», а не 0.0, при пустом наборе; 404 для
    несуществующего/неодобренного."""
    instr = create_instructor(client)
    student1 = create_student(client)
    rid = create_request(client, student1["token"], instr["id"])
    car_id = add_car(client, instr["token"])
    client.post(
        f"/api/instructor/requests/{rid}/accept",
        json={"car_id": car_id},
        headers=_headers(instr["token"]),
    )
    # второй принятый ученик — второй отзыв
    student2 = create_student(client, email="second-student@example.com")
    # у student2 уже есть accepted к этому инструктору? нет — ОВ-1 закрыл бы
    # заявку student2... student2 подает после принятия student1 — допустимо
    rid2 = create_request(client, student2["token"], instr["id"])
    client.post(
        f"/api/instructor/requests/{rid2}/accept",
        json={"car_id": car_id},
        headers=_headers(instr["token"]),
    )
    for token, text in ((student1["token"], "Первый"), (student2["token"], "Второй")):
        resp = client.post(
            f"/api/student/instructors/{instr['id']}/reviews",
            json={"rating": 5 if text == "Первый" else 4, "text": text},
            headers=_headers(token),
        )
        assert resp.status_code == 200, resp.text

    viewer = create_student(client, email="viewer@example.com")
    card = client.get(
        f"/api/student/instructors/{instr['id']}",
        headers=_headers(viewer["token"]),
    )
    assert card.status_code == 200
    rating = card.json()["instructor"]["rating"]
    assert rating["has_reviews"] is True
    assert rating["average"] == 4.5
    assert rating["count"] == 2

    # инструктор без отзывов: «нет отзывов» (не 0.0)
    other = create_instructor(client, email="noreviews@example.com")
    card = client.get(
        f"/api/student/instructors/{other['id']}",
        headers=_headers(viewer["token"]),
    )
    assert card.json()["instructor"]["rating"] == {"has_reviews": False}

    # несуществующий → 404
    assert (
        client.get(
            "/api/student/instructors/999999",
            headers=_headers(viewer["token"]),
        ).status_code
        == 404
    )


# --- Домен reviews ---------------------------------------------------------------


def test_review_requires_accepted_link_server_side(api, client):
    """Сценарии «Ученик без принятой заявки получает отказ» и «Прямой
    вызов API без UI тоже отклоняется» (FR-34, NFR-2): 403, отзыв не
    создан — проверка связи на сервере."""
    instr = create_instructor(client)
    student = create_student(client)
    # есть только 'new'-заявка — связи accepted нет
    create_request(client, student["token"], instr["id"])
    resp = client.post(
        f"/api/student/instructors/{instr['id']}/reviews",
        json={"rating": 5, "text": "Попытка мимо UI"},
        headers=_headers(student["token"]),
    )
    assert resp.status_code == 403

    # и вовсе без заявки
    stranger = create_student(client, email="stranger@example.com")
    resp = client.post(
        f"/api/student/instructors/{instr['id']}/reviews",
        json={"rating": 5, "text": "Отзыв чужого человека"},
        headers=_headers(stranger["token"]),
    )
    assert resp.status_code == 403

    conn = sqlite3.connect(db_path())
    count = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    conn.close()
    assert count == 0


def test_review_happy_duplicate_and_validation(api, client):
    """Сценарии «Принятый ученик оставляет отзыв», «Повторный отзыв
    отклоняется» (409), «Некорректная оценка отклоняется» (422) (FR-34,
    NFR-5)."""
    instr = create_instructor(client)
    car_id = add_car(client, instr["token"])
    student = create_student(client)
    rid = create_request(client, student["token"], instr["id"])
    client.post(
        f"/api/instructor/requests/{rid}/accept",
        json={"car_id": car_id},
        headers=_headers(instr["token"]),
    )

    first = client.post(
        f"/api/student/instructors/{instr['id']}/reviews",
        json={"rating": 5, "text": "Всё понравилось"},
        headers=_headers(student["token"]),
    )
    assert first.status_code == 200, first.text

    duplicate = client.post(
        f"/api/student/instructors/{instr['id']}/reviews",
        json={"rating": 4, "text": "Второй раз"},
        headers=_headers(student["token"]),
    )
    assert duplicate.status_code == 409

    for payload in (
        {"rating": 0, "text": "ноль"},
        {"rating": 6, "text": "шесть"},
        {"rating": 5, "text": "   "},
        {"rating": 5, "text": "ж" * 1001},
    ):
        resp = client.post(
            f"/api/student/instructors/{instr['id']}/reviews",
            json=payload,
            headers=_headers(student["token"]),
        )
        assert resp.status_code == 422, (payload, resp.text)

    # в БД ровно один отзыв
    conn = sqlite3.connect(db_path())
    count = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    conn.close()
    assert count == 1


# --- Домен student-requests --------------------------------------------------------


def test_request_submit_duplicate_parallel_and_repeat(api, client):
    """Сценарии подачи (FR-36, ОВ-1/ОВ-2): новая → создана; повторная
    активная тому же → 409 без записи; параллельная другому инструктору →
    создается; повторная после отказа → создается."""
    instr_a = create_instructor(client, email="a@example.com")
    instr_b = create_instructor(client, email="b@example.com")
    student = create_student(client)

    rid_a = create_request(client, student["token"], instr_a["id"])
    assert fetch_request_row(rid_a)["status"] == "new"

    # дубликат активной → 409, записи нет
    dup = client.post(
        "/api/student/requests",
        json={"instructor_id": instr_a["id"]},
        headers=_headers(student["token"]),
    )
    assert dup.status_code == 409
    conn = sqlite3.connect(db_path())
    count = conn.execute(
        "SELECT COUNT(*) FROM student_requests WHERE student_id = ?"
        " AND instructor_id = ?",
        (student["id"], instr_a["id"]),
    ).fetchone()[0]
    conn.close()
    assert count == 1

    # параллельная другому инструктору — допустима (ОВ-1)
    rid_b = create_request(client, student["token"], instr_b["id"])
    assert fetch_request_row(rid_b)["status"] == "new"

    # отказ + повторная (ОВ-2)
    denied = client.post(
        f"/api/instructor/requests/{rid_b}/deny",
        json={"comment": "Нет мест"},
        headers=_headers(instr_b["token"]),
    )
    assert denied.status_code == 200
    again = client.post(
        "/api/student/requests",
        json={"instructor_id": instr_b["id"]},
        headers=_headers(student["token"]),
    )
    assert again.status_code == 200, again.text


def test_request_to_unapproved_instructor_404(api, client):
    """Сценарий «Заявка неодобренному инструктору отклоняется»: waiting/
    deny не имеют записи users → 404, заявки нет."""
    apply_instructor(client, email="waiting2@example.com")  # waiting
    student = create_student(client)
    resp = client.post(
        "/api/student/requests",
        json={"instructor_id": 999999},
        headers=_headers(student["token"]),
    )
    assert resp.status_code == 404


def test_instructor_sees_only_own_requests(api, client):
    """Сценарии «Новая заявка видна в списке с учеником и датой» и «Чужие
    заявки не видны» (FR-37)."""
    instr_a = create_instructor(client, email="a@example.com")
    instr_b = create_instructor(client, email="b@example.com")
    student = create_student(client)
    create_request(client, student["token"], instr_a["id"])
    create_request(client, student["token"], instr_b["id"])

    list_a = client.get(
        "/api/instructor/requests", headers=_headers(instr_a["token"])
    ).json()["requests"]
    assert len(list_a) == 1
    assert list_a[0]["student_full_name"] == "Петрова-Водкина Анна Оттовна"
    assert list_a[0]["status"] == "new"
    assert list_a[0]["created_at"]

    list_b = client.get(
        "/api/instructor/requests", headers=_headers(instr_b["token"])
    ).json()["requests"]
    assert len(list_b) == 1
    assert list_b[0]["id"] != list_a[0]["id"]


def test_deny_requires_comment_and_visible_to_student(api, client):
    """Сценарии «Отказ без комментария заблокирован» (422, статус остается
    new) и «Отказ с комментарием виден ученику» (FR-38)."""
    instr = create_instructor(client)
    student = create_student(client)
    rid = create_request(client, student["token"], instr["id"])

    # без комментария — 422, действие заблокировано
    for payload in (None, {"comment": ""}, {"comment": "   "}):
        resp = client.post(
            f"/api/instructor/requests/{rid}/deny",
            json=payload if payload is not None else {},
            headers=_headers(instr["token"]),
        )
        assert resp.status_code == 422, resp.text
    assert fetch_request_row(rid)["status"] == "new"

    # с комментарием — denied, комментарий виден ученику
    denied = client.post(
        f"/api/instructor/requests/{rid}/deny",
        json={"comment": "Свободных окон нет"},
        headers=_headers(instr["token"]),
    )
    assert denied.status_code == 200
    row = fetch_request_row(rid)
    assert row["status"] == "denied"
    assert row["deny_comment"] == "Свободных окон нет"

    mine = client.get(
        "/api/student/requests", headers=_headers(student["token"])
    ).json()["requests"]
    target = [r for r in mine if r["id"] == rid][0]
    assert target["status"] == "denied"
    assert target["deny_comment"] == "Свободных окон нет"


def test_deny_and_accept_of_foreign_request_404_and_double_409(api, client):
    """Сценарии «Чужую заявку отклонить нельзя» (404) и повторное решение
    → 409 (guard статуса)."""
    instr_a = create_instructor(client, email="a@example.com")
    instr_b = create_instructor(client, email="b@example.com")
    student = create_student(client)
    rid = create_request(client, student["token"], instr_a["id"])

    assert (
        client.post(
            f"/api/instructor/requests/{rid}/deny",
            json={"comment": "чужое"},
            headers=_headers(instr_b["token"]),
        ).status_code
        == 404
    )
    car_id = add_car(client, instr_b["token"])
    assert (
        client.post(
            f"/api/instructor/requests/{rid}/accept",
            json={"car_id": car_id},
            headers=_headers(instr_b["token"]),
        ).status_code
        == 404
    )
    assert fetch_request_row(rid)["status"] == "new"

    # первое решение instr_a — accept; повторное — 409
    own_car = add_car(client, instr_a["token"])
    first = client.post(
        f"/api/instructor/requests/{rid}/accept",
        json={"car_id": own_car},
        headers=_headers(instr_a["token"]),
    )
    assert first.status_code == 200
    second = client.post(
        f"/api/instructor/requests/{rid}/accept",
        json={"car_id": own_car},
        headers=_headers(instr_a["token"]),
    )
    assert second.status_code == 409


def test_accept_requires_car_zero_cars_409_foreign_car_422(api, client):
    """Сценарии «Принятие при 0 автомобилей недоступно» (409, ОВ-4) и
    «Принятие с чужим автомобилем отклоняется» (422)."""
    instr = create_instructor(client)
    student = create_student(client)
    rid = create_request(client, student["token"], instr["id"])

    # 0 авто → 409 с подсказкой
    no_cars = client.post(
        f"/api/instructor/requests/{rid}/accept",
        json={},
        headers=_headers(instr["token"]),
    )
    assert no_cars.status_code == 409
    assert "автомобиль" in no_cars.json()["error"].lower()
    assert fetch_request_row(rid)["status"] == "new"

    # после заведения СВОЕГО авто: чужое авто → 422
    own_car = add_car(client, instr["token"])
    other = create_instructor(client, email="other@example.com")
    foreign_car = add_car(client, other["token"])
    resp = client.post(
        f"/api/instructor/requests/{rid}/accept",
        json={"car_id": foreign_car},
        headers=_headers(instr["token"]),
    )
    assert resp.status_code == 422
    assert fetch_request_row(rid)["status"] == "new"

    # своим авто — принимается
    ok = client.post(
        f"/api/instructor/requests/{rid}/accept",
        json={"car_id": own_car},
        headers=_headers(instr["token"]),
    )
    assert ok.status_code == 200
    row = fetch_request_row(rid)
    assert row["status"] == "accepted"
    assert row["car_id"] == own_car


def test_accept_closes_other_active_requests_new_and_accepted(api, client):
    """Сценарии «Принятие закрывает остальные активные заявки ученика» +
    MAJ-1 (итерация 2): закрываются и 'new', и 'accepted' чужих
    инструкторов; системный комментарий виден ученику; обе ветки в одной
    транзакции."""
    instr_a = create_instructor(client, email="a@example.com")
    instr_b = create_instructor(client, email="b@example.com")
    instr_c = create_instructor(client, email="c@example.com")
    car_a = add_car(client, instr_a["token"])
    car_b = add_car(client, instr_b["token"])
    car_c = add_car(client, instr_c["token"])

    student = create_student(client)
    rid_b = create_request(client, student["token"], instr_b["id"])
    rid_c = create_request(client, student["token"], instr_c["id"])
    # заявка к B принимается ДО принятия A: 'accepted' у B должна разорваться
    assert (
        client.post(
            f"/api/instructor/requests/{rid_b}/accept",
            json={"car_id": car_b},
            headers=_headers(instr_b["token"]),
        ).status_code
        == 200
    )
    rid_a = create_request(client, student["token"], instr_a["id"])

    accepted = client.post(
        f"/api/instructor/requests/{rid_a}/accept",
        json={"car_id": car_a},
        headers=_headers(instr_a["token"]),
    )
    assert accepted.status_code == 200

    row_a = fetch_request_row(rid_a)
    assert row_a["status"] == "accepted"
    assert row_a["car_id"] == car_a

    system_comment = "Заявка закрыта: ученик принят другим инструктором"
    for rid in (rid_b, rid_c):
        row = fetch_request_row(rid)
        assert row["status"] == "denied", rid
        assert row["deny_comment"] == system_comment, rid
        assert row["decided_at"]

    # ученик видит системный комментарий в «Моих заявках» (FR-38)
    mine = client.get(
        "/api/student/requests", headers=_headers(student["token"])
    ).json()["requests"]
    closed = [r for r in mine if r["id"] == rid_b][0]
    assert closed["deny_comment"] == system_comment

    # ровно одна активная связь «принят»
    summary_a = client.get(
        "/api/instructor/summary", headers=_headers(instr_a["token"])
    ).json()
    summary_b = client.get(
        "/api/instructor/summary", headers=_headers(instr_b["token"])
    ).json()
    assert len(summary_a["students"]) == 1
    assert summary_b["students"] == []


def test_accept_401_403(api, client):
    """Кабинетные действия без сессии/с чужой ролью → 401/403."""
    assert client.post("/api/instructor/requests/1/accept", json={}).status_code == 401
    student = create_student(client)
    resp = client.post(
        "/api/instructor/requests/1/accept",
        json={},
        headers=_headers(student["token"]),
    )
    assert resp.status_code == 403


def test_assign_student_car_rebind_and_guards(api, client):
    """MAJ-2 (arch-review итерация 2): перекрепление авто принятого
    ученика — свое авто → 200, чужое → 422, не-принятый ученик → 404."""
    instr = create_instructor(client)
    car1 = add_car(client, instr["token"], plate="А111АА111")
    car2 = add_car(client, instr["token"], plate="А222АА222")
    student = create_student(client)
    rid = create_request(client, student["token"], instr["id"])
    client.post(
        f"/api/instructor/requests/{rid}/accept",
        json={"car_id": car1},
        headers=_headers(instr["token"]),
    )

    other = create_instructor(client, email="other@example.com")
    foreign = add_car(client, other["token"])

    assert (
        client.patch(
            f"/api/instructor/students/{student['id']}/car",
            json={"car_id": foreign},
            headers=_headers(instr["token"]),
        ).status_code
        == 422
    )
    assert fetch_request_row(rid)["car_id"] == car1  # связь не меняется

    stranger = create_student(client, email="stranger@example.com")
    assert (
        client.patch(
            f"/api/instructor/students/{stranger['id']}/car",
            json={"car_id": car2},
            headers=_headers(instr["token"]),
        ).status_code
        == 404
    )

    ok = client.patch(
        f"/api/instructor/students/{student['id']}/car",
        json={"car_id": car2},
        headers=_headers(instr["token"]),
    )
    assert ok.status_code == 200
    assert fetch_request_row(rid)["car_id"] == car2
    assert fetch_request_row(rid)["status"] == "accepted"


# --- Домен instructor-summary -------------------------------------------------


def test_summary_widgets(api, client):
    """Сценарии виджетов (FR-40, FR-41): до принятия — students == []
    (только 'new' в виджет не попадает); после принятия — ученик в списке
    с авто и датой; today_lessons — всегда честный []."""
    instr = create_instructor(client)
    student = create_student(client)
    rid = create_request(client, student["token"], instr["id"])

    before = client.get(
        "/api/instructor/summary", headers=_headers(instr["token"])
    ).json()
    assert before["students"] == []
    assert before["today_lessons"] == []

    car_id = add_car(client, instr["token"])
    client.post(
        f"/api/instructor/requests/{rid}/accept",
        json={"car_id": car_id},
        headers=_headers(instr["token"]),
    )
    after = client.get(
        "/api/instructor/summary", headers=_headers(instr["token"])
    ).json()
    assert len(after["students"]) == 1
    entry = after["students"][0]
    assert entry["full_name"] == "Петрова-Водкина Анна Оттовна"
    assert entry["student_id"] == student["id"]
    assert entry["car"] and "Škoda" in entry["car"]
    assert entry["decided_at"]
    assert after["today_lessons"] == []


def test_summary_access_401_403(api, client):
    assert client.get("/api/instructor/summary").status_code == 401
    student = create_student(client)
    assert (
        client.get(
            "/api/instructor/summary", headers=_headers(student["token"])
        ).status_code
        == 403
    )


# --- NFR: параметризованный SQL в новых модулях ---------------------------------


def test_new_modules_no_sql_concatenation():
    """NFR-3: в новых модулях нет f-строк/конкатенаций/ format() в SQL."""
    for name in (
        "instructor_cars.py",
        "instructor_availability.py",
        "student_marketplace.py",
        "reviews.py",
        "student_requests.py",
        "instructor_summary.py",
        "guards.py",
        "uploads.py",
    ):
        src = (ROOT / "backend" / name).read_text(encoding="utf-8")
        for bad in ("f\"SELECT", "f'SELECT", "f\"INSERT", "f'INSERT",
                    "f\"UPDATE", "f'UPDATE", "f\"DELETE", "f'DELETE",
                    "+ \"SELECT", "\"SELECT \" +", "format(SELECT"):
            assert bad not in src, (name, bad)
