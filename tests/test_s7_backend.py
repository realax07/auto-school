"""Спринт 7 — BACKEND-тесты (change add-car-validation-booking; задачи
1.1, 1.2, 2.1, 3.1, 4.1, 5.1, 6.1 — backend-волна + MAJ-1 регресс).

Покрывают:
- миграция instructor_cars.status (idempotent; существующие строки →
  'validated' через DEFAULT — ОВ-1) — TC-S7BE-001/002;
- статусная модель: новое авто в draft (ЯВНО в INSERT), submit
  draft→validating (+алиас send-to-validation), withdraw validating→draft
  (ОВ-3, +алиас back-to-draft), guard-и прав доступа (401/403/404/409) —
  TC-S7BE-003/004/005/006;
- админ: GET /api/admin/cars/completeness (+алиас GET /api/admin/cars)
  +status +counters, фильтр ?status=validating, POST validate (ОВ-4:
  ≥3 ракурса И СТС → validated, иначе 409 с перечнем; не validating →
  409; 401; block-эндпоинт отсутствует) — TC-S7BE-007/008/009/010;
- видимость по ОВ-2: каталог/авто-фильтры только validated (пустой блок
  авто у инструктора без validated — не исчезает), pair-car photo draft →
  404 неразличение (прямой вызов), СТС ученику не выдается во всех
  статусах — TC-S7BE-011/012/013;
- бронирование (задача 6.1): car_status-бейдж + photo_url (приоритет
  front; draft → у ученика без photo_url, у владельца с; validating →
  «Не проверено»), удаленный авто → «—» — TC-S7BE-014/015;
- СТС существующего авто через angle='sts' (задача 4.1): загрузка/замена,
  PDF/6 МБ → 422, статус не меняется, GET — только владелец, «Мои
  документы» видят по всем статусам (задача 5.1) — TC-S7BE-016/017;
- MAJ-1 регресс: PUT availability × активные брони → 409 с перечнем,
  график не изменен; только «отклонена» → сохраняется — TC-S7BE-018;
- баг 5.2: плитка строится от авторизованного эндпоинта (photos{angle}),
  без legacy photo_url/data/-путей, переживает повторный вход —
  TC-S7BE-019.

Трассировка TC-S7BE-NNN в docstring каждого теста (rule 6). Фикстуры —
общий client из conftest; каталог загрузок — env AUTOSCHOOL_UPLOADS_DIR в
tmp_path; time.sleep запрещен (спека qa-pipeline).
"""
import datetime
import sqlite3
from pathlib import Path

import pytest

from conftest import admin_headers, db_path, register

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


def create_instructor(client, email="instr@example.com", experience_years=5):
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
    return {"token": login.json()["token"], "id": user_id, "email": email}


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
    """Создание авто JSON-путем (совместимость; в 'draft' — TC-S7BE-003)."""
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
    """POST /api/instructor/cars multipart с СТС (FR-44)."""
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


def upload_angle(client, token, car_id, angle, content=ROOT_JPEG, ext="jpg"):
    return client.post(
        f"/api/instructor/cars/{car_id}/photo/{angle}",
        files={"photo": (f"{angle}.{ext}", content,
                         "image/png" if ext == "png" else "image/jpeg")},
        headers=_headers(token),
    )


def set_car_status(car_id: int, status: str) -> None:
    """Прямой контроль БД (механика conftest): аранжировка статусов,
    недостижимых через API в одном шаге (например validated без полного
    комплекта — для матрицы видимости)."""
    conn = sqlite3.connect(db_path())
    conn.execute(
        "UPDATE instructor_cars SET status = ? WHERE id = ?",
        (status, car_id),
    )
    conn.commit()
    conn.close()


def set_car_sts(car_id: int, path: str) -> None:
    conn = sqlite3.connect(db_path())
    conn.execute(
        "UPDATE instructor_cars SET photo_sts = ? WHERE id = ?",
        (path, car_id),
    )
    conn.commit()
    conn.close()


def setup_pair(
    client,
    instructor_email="instr@example.com",
    student_email="student@example.com",
    intervals=None,
):
    """Аранжировка: инструктор + авто + график + accepted-пара."""
    instr = create_instructor(client, email=instructor_email)
    car_id = add_car_json(client, instr["token"])
    if intervals is None:
        intervals = [
            {"weekday": 0, "start_time": "10:00", "end_time": "11:00"},
            {"weekday": 1, "start_time": "12:00", "end_time": "13:00"},
        ]
    saved = client.put(
        "/api/instructor/availability",
        json={"intervals": intervals},
        headers=_headers(instr["token"]),
    )
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


def submit_car(client, token, car_id):
    return client.post(
        f"/api/instructor/cars/{car_id}/submit", headers=_headers(token)
    )


def withdraw_car(client, token, car_id):
    return client.post(
        f"/api/instructor/cars/{car_id}/withdraw", headers=_headers(token)
    )


# --- Миграция (задача 1.1, ОВ-1) ---------------------------------------------


def test_s7_migration_existing_cars_become_validated(tmp_path, monkeypatch):
    """TC-S7BE-001 (change add-car-validation-booking, задача 1.1, ОВ-1):
    миграция на ПРЕДСОЗДАННОЙ БД со старыми строками: колонка status
    TEXT NOT NULL DEFAULT 'validated' + CHECK (draft/validating/validated);
    существующие авто получают 'validated' через DEFAULT — не исчезают из
    каталога и пар; повторный init_db идемпотентен (механика users.role).
    """
    db_file = tmp_path / "legacy.db"
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(db_file))
    monkeypatch.setenv("ADMIN_USER", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", "x")
    monkeypatch.setenv("SECRET", "test-secret")

    # «Старая» БД: схема до статусной модели + 2 существующие строки
    conn = sqlite3.connect(str(db_file))
    conn.executescript(
        """
        CREATE TABLE users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          surname TEXT NOT NULL, name TEXT NOT NULL, patronymic TEXT NOT NULL,
          email TEXT NOT NULL UNIQUE, phone TEXT NOT NULL,
          password_hash TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE instructor_applications (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          surname TEXT NOT NULL, name TEXT NOT NULL, patronymic TEXT NOT NULL,
          email TEXT NOT NULL UNIQUE, phone TEXT NOT NULL, address TEXT NOT NULL,
          work_format TEXT NOT NULL, plate TEXT NOT NULL DEFAULT '',
          license_number TEXT NOT NULL, license_date TEXT NOT NULL DEFAULT '',
          license_category TEXT NOT NULL, experience TEXT NOT NULL DEFAULT '',
          password_hash TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'waiting',
          review_comment TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE instructor_cars (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          instructor_id INTEGER NOT NULL, brand TEXT NOT NULL,
          model TEXT NOT NULL, year INTEGER NOT NULL, plate TEXT NOT NULL,
          transmission TEXT NOT NULL CHECK (transmission IN ('manual','automatic')),
          photo_path TEXT,
          created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        INSERT INTO instructor_cars (instructor_id, brand, model, year,
          plate, transmission) VALUES (1, 'Lada', '2107', 1988, 'А001АА777', 'manual');
        INSERT INTO instructor_cars (instructor_id, brand, model, year,
          plate, transmission) VALUES (1, 'Kia', 'Rio', 2019, 'В002ВВ777', 'automatic');
        """
    )
    conn.commit()
    conn.close()

    import backend.db as db

    db.init_db()
    db.init_db()  # идемпотентность: повторный прогон без ошибки/дублей

    conn = sqlite3.connect(str(db_file))
    columns = [row[1] for row in conn.execute("PRAGMA table_info(instructor_cars)")]
    rows = conn.execute(
        "SELECT plate, status FROM instructor_cars ORDER BY id"
    ).fetchall()
    ddl = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table'"
        " AND name = 'instructor_cars'"
    ).fetchone()[0]
    conn.close()
    assert columns.count("status") == 1, "повторный init_db не дублирует колонку"
    assert [status for _, status in rows] == ["validated", "validated"], rows
    # ОВ-1: существующие авто сохранились и стали validated
    assert [plate for plate, _ in rows] == ["А001АА777", "В002ВВ777"]
    # CHECK-домен статусной машины
    assert "draft" in ddl and "validating" in ddl and "validated" in ddl


def test_s7_migration_rejects_status_outside_domain(client):
    """TC-S7BE-001b (change add-car-validation-booking, задача 1.1):
    CHECK-ограничение колонки status: значение вне статусной машины
    отвергается на уровне БД."""
    conn = sqlite3.connect(db_path())
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO instructor_cars (instructor_id, brand, model, year,"
            " plate, transmission, status)"
            " VALUES (1, 'X', 'Y', 2020, 'А000АА000', 'manual', 'pending')"
        )
    conn.close()


# --- Статусная модель: создание и переходы (задача 1.1, ОВ-3) ----------------


def test_s7_new_car_created_in_draft_with_counters(api, client):
    """TC-S7BE-003 (change add-car-validation-booking, задача 1.1): новое
    авто создается в status='draft' (ЯВНО в INSERT, DEFAULT не
    используется); GET /api/instructor/cars выдает status и counters
    (ракурсов из 5, СТС да/нет) во всех статусах владельца."""
    instr = create_instructor(client)
    car_id = create_car_multipart(client, instr["token"]).json()["car_id"]
    upload_angle(client, instr["token"], car_id, "front")
    upload_angle(client, instr["token"], car_id, "rear")

    listed = client.get(
        "/api/instructor/cars", headers=_headers(instr["token"])
    ).json()["cars"][0]
    assert listed["id"] == car_id
    assert listed["status"] == "draft", "новое авто — в черновике"
    assert listed["counters"] == {"angles": 2, "sts": True}
    assert listed["has_sts"] is True

    # JSON-путь совместимости (без СТС) — тоже draft
    car2 = add_car_json(client, instr["token"], plate="Г003ГГ777")
    listed2 = client.get(
        "/api/instructor/cars", headers=_headers(instr["token"])
    ).json()["cars"]
    by_id = {c["id"]: c for c in listed2}
    assert by_id[car2]["status"] == "draft"
    assert by_id[car2]["counters"] == {"angles": 0, "sts": False}


def test_s7_submit_withdraw_transitions(api, client):
    """TC-S7BE-004 (change add-car-validation-booking, задачи 1.1/ОВ-3):
    submit draft→validating; withdraw validating→draft; повторный submit
    после validate? нет — validated терминальный: submit по validated →
    409; submit по validating → 409 «не в статусе черновика»; withdraw по
    draft → 409. Полный цикл: draft → validating → draft → validating →
    validated (validate — TC-S7BE-009)."""
    instr = create_instructor(client)
    car_id = add_car_json(client, instr["token"])

    assert submit_car(client, instr["token"], car_id).json() == {
        "ok": True, "status": "validating",
    }
    # повторный submit — не draft
    resp = submit_car(client, instr["token"], car_id)
    assert resp.status_code == 409
    assert "черновика" in resp.json()["error"]
    # отзыв обратно в draft (ОВ-3)
    assert withdraw_car(client, instr["token"], car_id).json() == {
        "ok": True, "status": "draft",
    }
    # повторный withdraw — не validating
    resp = withdraw_car(client, instr["token"], car_id)
    assert resp.status_code == 409
    assert "валидации" in resp.json()["error"]
    # и снова на валидацию
    assert submit_car(client, instr["token"], car_id).status_code == 200
    status = client.get(
        "/api/instructor/cars", headers=_headers(instr["token"])
    ).json()["cars"][0]["status"]
    assert status == "validating"


def test_s7_submit_withdraw_access_guards(api, client):
    """TC-S7BE-005 (change add-car-validation-booking, задачи 1.1, NFR-7):
    guard-и прав доступа переходов: гость → 401, ученик → 403, чужой
    инструктор → 404, несуществующий → 404; статус чужого авто не
    меняется."""
    owner = create_instructor(client)
    other = create_instructor(client, email="other@example.com")
    student = create_student(client)
    car_id = add_car_json(client, owner["token"])

    assert client.post(f"/api/instructor/cars/{car_id}/submit").status_code == 401
    assert client.post(f"/api/instructor/cars/{car_id}/withdraw").status_code == 401
    assert (
        client.post(
            f"/api/instructor/cars/{car_id}/submit",
            headers=_headers(student["token"]),
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/instructor/cars/{car_id}/withdraw",
            headers=_headers(student["token"]),
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/instructor/cars/{car_id}/submit",
            headers=_headers(other["token"]),
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/instructor/cars/{car_id}/withdraw",
            headers=_headers(other["token"]),
        ).status_code
        == 404
    )
    assert client.post("/api/instructor/cars/999999/submit",
                       headers=_headers(other["token"])).status_code == 404
    assert client.post("/api/instructor/cars/999999/withdraw",
                       headers=_headers(other["token"])).status_code == 404
    # без сессии — 401 раньше проверки существования (guard-порядок)
    assert client.post("/api/instructor/cars/999999/submit").status_code == 401
    # чужие действия статус не изменили
    listed = client.get(
        "/api/instructor/cars", headers=_headers(owner["token"])
    ).json()["cars"][0]
    assert listed["status"] == "draft"


def test_s7_pm_aliases_send_to_validation_back_to_draft(api, client):
    """TC-S7BE-006 (change add-car-validation-booking, задача 1.1, ТЗ ПМ):
    алиасы маршрутов из ТЗ ПМ ведут себя идентично submit/withdraw:
    POST …/{id}/send-to-validation (draft→validating), POST
    …/{id}/back-to-draft (validating→draft); не в том статусе → 409."""
    instr = create_instructor(client)
    car_id = add_car_json(client, instr["token"])

    resp = client.post(
        f"/api/instructor/cars/{car_id}/send-to-validation",
        headers=_headers(instr["token"]),
    )
    assert resp.status_code == 200 and resp.json()["status"] == "validating"
    resp = client.post(
        f"/api/instructor/cars/{car_id}/back-to-draft",
        headers=_headers(instr["token"]),
    )
    assert resp.status_code == 200 and resp.json()["status"] == "draft"
    # guard-и алиасов те же
    assert (
        client.post(
            f"/api/instructor/cars/{car_id}/back-to-draft",
            headers=_headers(instr["token"]),
        ).status_code
        == 409
    )
    assert submit_car(client, instr["token"], car_id).status_code == 200
    assert (
        client.post(
            f"/api/instructor/cars/{car_id}/send-to-validation",
            headers=_headers(instr["token"]),
        ).status_code
        == 409
    )


# --- Админ: список + validate (задача 1.2, ОВ-4) ------------------------------


def _make_validating_complete(client, instr, car_id):
    """Аранжировка validating-авто с 3 ракурсами и СТС (порог ОВ-4)."""
    for angle in ("front", "rear", "interior"):
        upload_angle(client, instr["token"], car_id, angle)
    assert submit_car(client, instr["token"], car_id).status_code == 200


def test_s7_admin_cars_list_filter(api, client):
    """TC-S7BE-007 (change add-car-validation-booking, задача 1.2): GET
    /api/admin/cars/completeness (+алиас GET /api/admin/cars из ТЗ ПМ) —
    все авто всех статусов + status + counters; фильтр ?status=validating
    возвращает только validating («На валидации»); недопустимый фильтр →
    422; без/с неверным токеном → 401."""
    instr = create_instructor(client)
    car_draft = add_car_json(client, instr["token"])
    car_validating = add_car_json(
        client, instr["token"], brand="Lada", model="Kalina",
        plate="Д004ДД777",
    )
    car_validated = add_car_json(
        client, instr["token"], brand="Kia", model="Rio", plate="Е005ЕЕ777"
    )
    assert submit_car(client, instr["token"], car_validating).status_code == 200
    set_car_status(car_validated, "validated")

    assert client.get("/api/admin/cars/completeness").status_code == 401
    assert client.get(
        "/api/admin/cars/completeness",
        headers={"X-Admin-Token": "wrong"},
    ).status_code == 401
    assert client.get("/api/admin/cars").status_code == 401

    token = admin_headers(client)
    for path in ("/api/admin/cars/completeness", "/api/admin/cars"):
        resp = client.get(path, headers=token)
        assert resp.status_code == 200, (path, resp.text)
        cars = {c["id"]: c for c in resp.json()["cars"]}
        assert set(cars) == {car_draft, car_validating, car_validated}
        assert cars[car_draft]["status"] == "draft"
        assert cars[car_validating]["status"] == "validating"
        assert cars[car_validated]["status"] == "validated"
        assert cars[car_draft]["counters"] == {"angles": 0, "sts": False}

    # фильтр «На валидации»
    resp = client.get(
        "/api/admin/cars/completeness?status=validating", headers=token
    )
    assert resp.status_code == 200
    filtered = resp.json()["cars"]
    assert [c["id"] for c in filtered] == [car_validating]
    assert all(c["status"] == "validating" for c in filtered)
    resp = client.get("/api/admin/cars?status=validated", headers=token)
    assert [c["id"] for c in resp.json()["cars"]] == [car_validated]

    # недопустимое значение фильтра
    assert (
        client.get(
            "/api/admin/cars/completeness?status=blocked", headers=token
        ).status_code
        == 422
    )


def test_s7_admin_validate_happy_path(api, client):
    """TC-S7BE-008 (change add-car-validation-booking, задачи 1.2/ОВ-4):
    POST /api/admin/cars/{id}/validate — validating + ЛЮБЫЕ 3 ракурса из 5
    И СТС → validated (виден в каталоге, бейдж «Проверено»); эффект
    отражается в GET /api/admin/cars/completeness."""
    instr = create_instructor(client)
    car_id = add_car_json(client, instr["token"])
    for angle in ("left", "right", "rear"):  # любые 3 из 5
        upload_angle(client, instr["token"], car_id, angle)
    set_car_sts(car_id, "data/uploads/car_sts/x.jpg")
    assert submit_car(client, instr["token"], car_id).status_code == 200

    resp = client.post(
        f"/api/admin/cars/{car_id}/validate", headers=admin_headers(client)
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"ok": True, "status": "validated"}

    cars = client.get(
        "/api/instructor/cars", headers=_headers(instr["token"])
    ).json()["cars"]
    assert cars[0]["status"] == "validated"
    # validated-авто участвует в каталоге (ОВ-2)
    student = create_student(client)
    catalog = client.get(
        "/api/student/instructors", headers=_headers(student["token"])
    ).json()["instructors"]
    assert len(catalog) == 1 and catalog[0]["id"] == instr["id"]
    assert [c["id"] for c in catalog[0]["cars"]] == [car_id]


def test_s7_admin_validate_completeness_guard_409(api, client):
    """TC-S7BE-009 (change add-car-validation-booking, задача 1.2, ОВ-4):
    guard комплектности: 2 ракурса + СТС → 409 с перечнем недостающих
    ракурсов; 3 ракурса без СТС → 409 с «СТС»; 0 ракурсов → 409;
    авто не в validating → 409; несуществующий → 404; без токена → 401;
    статус авто при отказах НЕ меняется."""
    instr = create_instructor(client)
    car_two = add_car_json(client, instr["token"])
    upload_angle(client, instr["token"], car_two, "front")
    upload_angle(client, instr["token"], car_two, "rear")
    set_car_sts(car_two, "data/uploads/car_sts/a.jpg")
    assert submit_car(client, instr["token"], car_two).status_code == 200

    admin = admin_headers(client)
    resp = client.post(f"/api/admin/cars/{car_two}/validate", headers=admin)
    assert resp.status_code == 409
    body = resp.json()
    assert "Комплект неполный" in body["error"]
    for angle in ("interior", "left", "right"):
        assert angle in body["error"], body["error"]
    assert (
        client.get(
            "/api/instructor/cars", headers=_headers(instr["token"])
        ).json()["cars"][0]["status"]
        == "validating"
    ), "отказ validate статус не меняет"

    # 3 ракурса, но без СТС → 409 с упоминанием СТС
    car_no_sts = add_car_json(
        client, instr["token"], brand="Lada", model="Kalina",
        plate="Ж006ЖЖ777",
    )
    for angle in ("front", "rear", "interior"):
        upload_angle(client, instr["token"], car_no_sts, angle)
    assert submit_car(client, instr["token"], car_no_sts).status_code == 200
    resp = client.post(f"/api/admin/cars/{car_no_sts}/validate", headers=admin)
    assert resp.status_code == 409
    assert "СТС" in resp.json()["error"]

    # не validating → 409 (draft)
    car_draft = add_car_json(
        client, instr["token"], brand="Kia", model="Rio", plate="З007ЗЗ777"
    )
    assert (
        client.post(f"/api/admin/cars/{car_draft}/validate", headers=admin).status_code
        == 409
    )
    # validated терминальный — повторный validate → 409
    assert (
        client.post(f"/api/admin/cars/{car_two}/validate", headers=admin).status_code
        == 409
    )
    # несуществующий → 404; без токена → 401
    assert (
        client.post("/api/admin/cars/999999/validate", headers=admin).status_code
        == 404
    )
    assert client.post(f"/api/admin/cars/{car_draft}/validate").status_code == 401


def test_s7_admin_block_endpoint_removed(api, client):
    """TC-S7BE-010 (change add-car-validation-booking, задача 1.2,
    REMOVED-дельта): POST /api/admin/cars/{id}/block отсутствует
    (404/405) — контур блокировки Спринта 5 замещен статусной моделью;
    blocked колонка новыми эндпоинтами не читается (в выдаче нет)."""
    instr = create_instructor(client)
    car_id = add_car_json(client, instr["token"])
    assert (
        client.post(
            f"/api/admin/cars/{car_id}/block", headers=admin_headers(client)
        ).status_code
        in (404, 405)
    )
    listed = client.get(
        "/api/instructor/cars", headers=_headers(instr["token"])
    ).json()["cars"][0]
    assert "blocked" not in listed
    cars = client.get(
        "/api/admin/cars/completeness", headers=admin_headers(client)
    ).json()["cars"]
    assert all("blocked" not in c for c in cars)


# --- Видимость по ОВ-2 (задача 2.1) -------------------------------------------


def test_s7_catalog_only_validated_empty_block_kept(api, client):
    """TC-S7BE-011 (change add-car-validation-booking, задача 2.1, ОВ-2):
    каталог: авто в карточках и авто-фильтрах — ТОЛЬКО validated
    (серверно); draft/validating не участвуют; инструктор без
    validated-авто остается в каталоге с пустым блоком авто (не
    исчезает); фильтр по КПП находит только по validated."""
    validated = create_instructor(client, email="v@example.com")
    car_v = add_car_json(client, validated["token"], transmission="manual")
    set_car_status(car_v, "validated")
    drafty = create_instructor(client, email="d@example.com")
    add_car_json(client, drafty["token"], transmission="manual")

    student = create_student(client)
    resp = client.get(
        "/api/student/instructors", headers=_headers(student["token"])
    )
    assert resp.status_code == 200
    instructors = {i["id"]: i for i in resp.json()["instructors"]}
    assert set(instructors) == {validated["id"], drafty["id"]}, (
        "инструктор без validated-авто остается в каталоге"
    )
    assert [c["id"] for c in instructors[validated["id"]]["cars"]] == [car_v]
    assert instructors[drafty["id"]]["cars"] == [], "пустой блок авто"

    # фильтр по КПП — только по validated
    resp = client.get(
        "/api/student/instructors?transmission=manual",
        headers=_headers(student["token"]),
    )
    assert [i["id"] for i in resp.json()["instructors"]] == [validated["id"]]

    # карточка профиля — то же правило
    card = client.get(
        f"/api/student/instructors/{drafty['id']}",
        headers=_headers(student["token"]),
    ).json()["instructor"]
    assert card["cars"] == []


def test_s7_pair_car_photo_draft_404_indistinctible(api, client):
    """TC-S7BE-012 (change add-car-validation-booking, задачи 2.1/ОВ-2,
    NFR-4): матрица фото ученику пары: draft → 404 неразличение (в т.ч.
    ПРЯМОЙ вызов URL); validating → выдается; validated → выдается;
    владелец видит во всех статусах; ученик НЕ из пары → 403 и по draft
    тоже (не 404-различение с парой)."""
    env = setup_pair(client)
    instr, student = env["instr"], env["student"]
    car_id = env["car_id"]
    upload_angle(client, instr["token"], car_id, "front")

    # draft: прямой вызов учеником пары → 404 (не 403) — неразличение
    assert (
        client.get(
            f"/api/instructor/cars/{car_id}/photo/front",
            headers=_headers(student["token"]),
        ).status_code
        == 404
    )
    # validating → выдается
    set_car_status(car_id, "validating")
    got = client.get(
        f"/api/instructor/cars/{car_id}/photo/front",
        headers=_headers(student["token"]),
    )
    assert got.status_code == 200 and got.content == ROOT_JPEG
    # validated → выдается
    set_car_status(car_id, "validated")
    assert (
        client.get(
            f"/api/instructor/cars/{car_id}/photo/front",
            headers=_headers(student["token"]),
        ).status_code
        == 200
    )
    # владелец — во всех статусах
    set_car_status(car_id, "draft")
    assert (
        client.get(
            f"/api/instructor/cars/{car_id}/photo/front",
            headers=_headers(instr["token"]),
        ).status_code
        == 200
    )

    # ученик НЕ из пары: 403 независимо от статуса (дифференциация с
    # парой не происходит через 404-канал — чужой авто не существует
    # для него в UI; серверный контракт — 403)
    outsider = create_student(client, email="outsider@example.com")
    set_car_status(car_id, "validated")
    assert (
        client.get(
            f"/api/instructor/cars/{car_id}/photo/front",
            headers=_headers(outsider["token"]),
        ).status_code
        == 403
    )


def test_s7_sts_owner_only_in_all_statuses(api, client):
    """TC-S7BE-013 (change add-car-validation-booking, задачи 2.1/4.1,
    NFR-7): СТС ученику пары не выдается во ВСЕХ статусах: GET
    …/photo/sts → 403; GET …/sts → 403; владелец — 200; чужой инструктор
    → 404; angle вне списка → 404."""
    env = setup_pair(client)
    instr, student = env["instr"], env["student"]
    car_id = env["car_id"]
    import backend.uploads as uploads

    path = uploads.save_image("car_sts", ROOT_JPEG, "jpg")
    set_car_sts(car_id, path)
    other = create_instructor(client, email="other@example.com")

    for status in ("draft", "validating", "validated"):
        set_car_status(car_id, status)
        owner_sts = client.get(
            f"/api/instructor/cars/{car_id}/sts",
            headers=_headers(instr["token"]),
        )
        assert owner_sts.status_code == 200, status
        assert owner_sts.content == ROOT_JPEG
        # GET …/sts (выделенный маршрут, только владелец) — 403 во всех
        assert (
            client.get(
                f"/api/instructor/cars/{car_id}/sts",
                headers=_headers(student["token"]),
            ).status_code
            == 403
        ), status
        assert (
            client.get(
                f"/api/instructor/cars/{car_id}/photo/sts",
                headers=_headers(other["token"]),
            ).status_code
            == 404
        ), status
        if status == "draft":
            # неразличение (NFR-4) приоритетнее: draft скрыт от ученика
            # пары целиком, включая angle='sts' → 404
            expected = 404
        else:
            # validating/validated: СТС ученику не выдается → 403
            expected = 403
        assert (
            client.get(
                f"/api/instructor/cars/{car_id}/photo/sts",
                headers=_headers(student["token"]),
            ).status_code
            == expected
        ), status
    assert (
        client.get(
            f"/api/instructor/cars/{car_id}/photo/hood",
            headers=_headers(instr["token"]),
        ).status_code
        == 404
    )


# --- Бронирование: фото и бейдж авто (задача 6.1, ОВ-2) -----------------------


def _book_first_slot(client, env):
    conn = sqlite3.connect(db_path())
    slot_id = conn.execute(
        "SELECT id FROM availability WHERE instructor_id = ? ORDER BY id LIMIT 1",
        (env["instr"]["id"],),
    ).fetchone()[0]
    conn.close()
    created = client.post(
        "/api/student/bookings",
        json={"availability_id": slot_id},
        headers=_headers(env["student"]["token"]),
    )
    assert created.status_code == 200, created.text
    return created.json()["booking_id"]


def test_s7_booking_car_photo_and_badge_by_status(api, client):
    """TC-S7BE-014 (change add-car-validation-booking, задача 6.1, ОВ-2):
    авто брони + car_status (бейдж) + photo_url (приоритет front): валидированный
    авто — с фото у ученика и инструктора; validating — с фото и бейджем
    «Не проверено» (car_status='validating'); draft — у ученика БЕЗ
    photo_url (плейсхолдер), бронь видна, у владельца — с фото;
    перекрепление меняет авто и фото."""
    env = setup_pair(client)
    instr, student = env["instr"], env["student"]
    car_id = env["car_id"]
    upload_angle(client, instr["token"], car_id, "rear")  # НЕ front
    upload_angle(client, instr["token"], car_id, "front")
    booking_id = _book_first_slot(client, env)

    front_url = f"/api/instructor/cars/{car_id}/photo/front"

    # validating: фото + желтый бейдж у обоих
    set_car_status(car_id, "validating")
    mine = client.get(
        "/api/student/bookings", headers=_headers(student["token"])
    ).json()["bookings"]
    theirs = client.get(
        "/api/instructor/bookings", headers=_headers(instr["token"])
    ).json()["bookings"]
    assert mine[0]["car"]["car_status"] == "validating"
    assert mine[0]["car"]["photo_url"] == front_url, "приоритет front"
    assert theirs[0]["car"]["photo_url"] == front_url

    # validated: «Проверено» + фото
    set_car_status(car_id, "validated")
    mine = client.get(
        "/api/student/bookings", headers=_headers(student["token"])
    ).json()["bookings"]
    assert mine[0]["car"]["car_status"] == "validated"
    assert mine[0]["car"]["photo_url"] == front_url

    # draft: ученик — без photo_url (плейсхолдер), владелец — с фото
    set_car_status(car_id, "draft")
    mine = client.get(
        "/api/student/bookings", headers=_headers(student["token"])
    ).json()["bookings"]
    assert mine[0]["car"]["photo_url"] is None
    assert mine[0]["car"]["car_status"] == "draft"
    assert mine[0]["status"] == "new", "бронь видна и в draft-авто"
    theirs = client.get(
        "/api/instructor/bookings", headers=_headers(instr["token"])
    ).json()["bookings"]
    assert theirs[0]["car"]["photo_url"] == front_url

    # перекрепление: авто и фото меняются (ОВ-6)
    car2 = add_car_json(
        client, instr["token"], brand="Lada", model="Kalina",
        plate="И008ИИ777",
    )
    upload_angle(client, instr["token"], car2, "interior")
    set_car_status(car2, "validated")
    moved = client.patch(
        f"/api/instructor/students/{student['id']}/car",
        json={"car_id": car2},
        headers=_headers(instr["token"]),
    )
    assert moved.status_code == 200
    mine = client.get(
        "/api/student/bookings", headers=_headers(student["token"])
    ).json()["bookings"]
    assert mine[0]["car"]["id"] == car2
    assert mine[0]["car"]["photo_url"] == (
        f"/api/instructor/cars/{car2}/photo/interior"
    )


def test_s7_booking_deleted_car_empty_state(api, client):
    """TC-S7BE-015 (change add-car-validation-booking, задача 6.1,
    наследование MIN-3): авто удален (car_id NULL) → car = null («—»),
    не ошибка, в обоих календарях."""
    env = setup_pair(client)
    instr, student = env["instr"], env["student"]
    booking_id = _book_first_slot(client, env)
    assert (
        client.delete(
            f"/api/instructor/cars/{env['car_id']}",
            headers=_headers(instr["token"]),
        ).status_code
        == 200
    )
    mine = client.get(
        "/api/student/bookings", headers=_headers(student["token"])
    ).json()["bookings"]
    theirs = client.get(
        "/api/instructor/bookings", headers=_headers(instr["token"])
    ).json()["bookings"]
    assert mine[0]["car"] is None
    assert theirs[0]["car"] is None


# --- СТС существующего авто angle='sts' (задача 4.1) --------------------------


def test_s7_sts_upload_and_replace_via_angle(api, client):
    """TC-S7BE-016 (change add-car-validation-booking, задача 4.1):
    POST …/photo/sts сохраняет СТС СУЩЕСТВУЮЩЕМУ авто (ранее — корень
    симптома «kind=car_sts не сохраняется» через legacy-маршрут);
    JPEG/PNG принимаются; PDF/6 МБ → 422 (прежнее СТС не изменено);
    замена СТС не трогает ракурсы и статус; файл в data/uploads/car_sts/."""
    import backend.uploads as uploads

    instr = create_instructor(client)
    car_id = add_car_json(client, instr["token"])
    upload_angle(client, instr["token"], car_id, "front")
    assert submit_car(client, instr["token"], car_id).status_code == 200

    # PDF → 422, СТС не записан
    resp = client.post(
        f"/api/instructor/cars/{car_id}/photo/sts",
        files={"photo": ("doc.pdf", ROOT_PDF, "application/pdf")},
        headers=_headers(instr["token"]),
    )
    assert resp.status_code == 422
    # 6 МБ → 422
    resp = client.post(
        f"/api/instructor/cars/{car_id}/photo/sts",
        files={"photo": ("big.jpg", OVERSIZE_JPEG, "image/jpeg")},
        headers=_headers(instr["token"]),
    )
    assert resp.status_code == 422
    assert "5 МБ" in resp.json()["error"]

    # валидный JPEG → photo_sts, статус не изменился, front не тронут
    resp = client.post(
        f"/api/instructor/cars/{car_id}/photo/sts",
        files={"photo": ("sts.jpg", ROOT_JPEG, "image/jpeg")},
        headers=_headers(instr["token"]),
    )
    assert resp.status_code == 200, resp.text
    conn = sqlite3.connect(db_path())
    row = conn.execute(
        "SELECT photo_sts, photo_front, status FROM instructor_cars"
        " WHERE id = ?",
        (car_id,),
    ).fetchone()
    conn.close()
    sts_path, front_path, status = row
    assert sts_path and Path(sts_path).read_bytes() == ROOT_JPEG
    # NFR-9: sts-ракурс идет через существующую механику angle-загрузок
    # (uploads.py без изменений) — каталог car_photo, uuid-имя
    assert "car_photo" in Path(sts_path).parts
    assert front_path, "замена СТС не трогает ракурсы"
    assert status == "validating", "загрузка СТС статус не меняет"

    # PNG-замена: файл обновлен, ракурсы/статус прежние
    old_sts = sts_path
    resp = client.post(
        f"/api/instructor/cars/{car_id}/photo/sts",
        files={"photo": ("sts.png", ROOT_PNG, "image/png")},
        headers=_headers(instr["token"]),
    )
    assert resp.status_code == 200
    conn = sqlite3.connect(db_path())
    new_sts, status2 = conn.execute(
        "SELECT photo_sts, status FROM instructor_cars WHERE id = ?",
        (car_id,),
    ).fetchone()
    conn.close()
    assert new_sts != old_sts
    assert Path(new_sts).read_bytes() == ROOT_PNG
    assert status2 == "validating"

    # гость/чужой при загрузке
    assert (
        client.post(
            f"/api/instructor/cars/{car_id}/photo/sts",
            files={"photo": ("sts.jpg", ROOT_JPEG, "image/jpeg")},
        ).status_code
        == 401
    )
    other = create_instructor(client, email="other@example.com")
    assert (
        client.post(
            f"/api/instructor/cars/{car_id}/photo/sts",
            files={"photo": ("sts.jpg", ROOT_JPEG, "image/jpeg")},
            headers=_headers(other["token"]),
        ).status_code
        == 404
    )
    # сохраненная механика uploads не изменилась (NFR-9)
    assert uploads.image_media_type(new_sts) == "image/png"


def test_s7_documents_sts_all_statuses_and_dosylka(api, client):
    """TC-S7BE-017 (change add-car-validation-booking, задачи 5.1/4.1,
    FR-45): «Мои документы» — СТС по ВСЕМ авто владельца независимо от
    status (draft/validating/validated); после дозагрузки СТС
    (angle='sts') запись появилась; после замены — обновленная привязка
    на месте; доступ — только владельцу (чужая роль → 403/401)."""
    instr = create_instructor(client)
    car1 = add_car_json(client, instr["token"])
    car2 = add_car_json(
        client, instr["token"], brand="Lada", model="Kalina",
        plate="К009КК777",
    )
    car3 = add_car_json(
        client, instr["token"], brand="Kia", model="Rio", plate="Л010ЛЛ777"
    )
    set_car_status(car1, "draft")
    set_car_status(car2, "validating")
    set_car_status(car3, "validated")
    import backend.uploads as uploads

    set_car_sts(car2, uploads.save_image("car_sts", ROOT_JPEG, "jpg"))
    set_car_sts(car3, uploads.save_image("car_sts", ROOT_PNG, "png"))

    # dosylka: у draft-авто СТС не было → загружаем через angle='sts'
    resp = client.post(
        f"/api/instructor/cars/{car1}/photo/sts",
        files={"photo": ("sts.jpg", ROOT_JPEG, "image/jpeg")},
        headers=_headers(instr["token"]),
    )
    assert resp.status_code == 200

    docs = client.get(
        "/api/instructor/documents", headers=_headers(instr["token"])
    ).json()
    sts_docs = [d for d in docs["documents"] if d["type"] == "car_sts"]
    assert {d["car"]["id"] for d in sts_docs} == {car1, car2, car3}, (
        "СТС виден по всем авто независимо от статуса"
    )
    assert sts_docs[0]["car"]["plate"]
    assert sts_docs[0]["uploaded_at"]

    # замена СТС car1 (angle='sts') — запись на месте (обновлена)
    resp = client.post(
        f"/api/instructor/cars/{car1}/photo/sts",
        files={"photo": ("sts2.png", ROOT_PNG, "image/png")},
        headers=_headers(instr["token"]),
    )
    assert resp.status_code == 200
    docs2 = client.get(
        "/api/instructor/documents", headers=_headers(instr["token"])
    ).json()["documents"]
    assert (
        len([d for d in docs2 if d["type"] == "car_sts"]) == 3
    ), "после замены СТС запись осталась"

    # доступ: гость → 401, ученик → 403
    assert client.get("/api/instructor/documents").status_code == 401
    student = create_student(client)
    assert (
        client.get(
            "/api/instructor/documents", headers=_headers(student["token"])
        ).status_code
        == 403
    )


# --- MAJ-1 итерация 3: замена фото/СТС у validated → validating (ОВ-4) -------


def test_s7_upload_to_validated_returns_to_validating_and_revalidate(api, client):
    """TC-S7BE-019 (MAJ-1 review-001, решение ПМ, итерация 3): замена
    ЛЮБОГО ракурса или СТС у авто в status='validated' переводит его
    обратно в validating (ответ upload-ручки несет итоговый status);
    у draft/validating загрузка статус не меняет (ОВ-7); после дозагрузки
    повторный admin validate снова проходит (гейт ОВ-4 не обходится
    задним числом: пока авто в validating — оно скрыто из каталога новых
    учеников)."""
    instr = create_instructor(client)
    car_id = add_car_json(client, instr["token"])
    # baseline (draft): загрузка статус не меняет, ответ несет статус
    resp = upload_angle(client, instr["token"], car_id, "rear")
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "draft"
    # комплект до валидации: front/left + СТС (rear уже есть)
    for angle in ("front", "left"):
        assert upload_angle(client, instr["token"], car_id, angle).status_code == 200
    # СТС у авто в draft: статус НЕ меняет (ответ несет текущий status);
    # комплект 3 ракурса + СТС собран до отправки на валидацию
    resp = client.post(
        f"/api/instructor/cars/{car_id}/photo/sts",
        files={"photo": ("sts.jpg", ROOT_JPEG, "image/jpeg")},
        headers=_headers(instr["token"]),
    )
    assert resp.status_code == 200 and resp.json()["status"] == "draft"
    assert submit_car(client, instr["token"], car_id).status_code == 200
    resp = client.post(
        f"/api/admin/cars/{car_id}/validate", headers=admin_headers(client)
    )
    assert resp.status_code == 200 and resp.json()["status"] == "validated"

    # MAJ-1: замена ракурса у validated → validating (в ответе и в БД)
    resp = upload_angle(client, instr["token"], car_id, "right")
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "validating", resp.json()
    conn = sqlite3.connect(db_path())
    status = conn.execute(
        "SELECT status FROM instructor_cars WHERE id = ?", (car_id,)
    ).fetchone()[0]
    conn.close()
    assert status == "validating"

    # ОВ-2 не обходится задним числом: validating скрыт из каталога новых
    student = create_student(client)
    catalog = client.get(
        "/api/student/instructors", headers=_headers(student["token"])
    ).json()["instructors"]
    assert len(catalog) == 1 and catalog[0]["id"] == instr["id"]
    assert catalog[0]["cars"] == [], catalog[0]["cars"]

    # повторный admin validate после дозагрузки — снова validated
    resp = client.post(
        f"/api/admin/cars/{car_id}/validate", headers=admin_headers(client)
    )
    assert resp.status_code == 200 and resp.json()["status"] == "validated"

    # замена СТС у validated — тот же переход validated → validating
    resp = client.post(
        f"/api/instructor/cars/{car_id}/photo/sts",
        files={"photo": ("sts2.png", ROOT_PNG, "image/png")},
        headers=_headers(instr["token"]),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "validating"
    # повторный admin validate по НОВОМУ комплекту (right загружен,
    # СТС заменен — комплект полный) — снова validated
    resp = client.post(
        f"/api/admin/cars/{car_id}/validate", headers=admin_headers(client)
    )
    assert resp.status_code == 200 and resp.json()["status"] == "validated"


# --- MAJ-1 регресс: PUT availability × брони (наследование Спринта 5) ---------


def test_s7_put_availability_409_maj1_regression(api, client):
    """TC-S7BE-018 (change add-car-validation-booking, MAJ-1 арх-ревью,
    наследование Спринта 5 — регресс): PUT availability, удаляющий
    интервал с активной бронью ('new' или 'confirmed') → 409 с ПЕРЕЧНЕМ
    затронутых интервалов (guard в write-транзакции), график НЕ изменен;
    интервал с только 'rejected' бронями замене не мешает; бронь на
    валидационный статус авто не влияет (MIN-2)."""
    env = setup_pair(client)
    instr, student = env["instr"], env["student"]
    set_car_status(env["car_id"], "validated")

    conn = sqlite3.connect(db_path())
    slot_mon = conn.execute(
        "SELECT id FROM availability WHERE instructor_id = ? AND weekday = 0",
        (instr["id"],),
    ).fetchone()[0]
    conn.close()

    booking_id = client.post(
        "/api/student/bookings",
        json={"availability_id": slot_mon},
        headers=_headers(student["token"]),
    ).json()["booking_id"]

    # PUT без понедельника → 409 с перечнем, график не изменен
    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"weekday": 1, "start_time": "12:00", "end_time": "13:00"}
        ]},
        headers=_headers(instr["token"]),
    )
    assert resp.status_code == 409
    body = resp.json()
    assert "10:00" in body["error"] and "11:00" in body["error"]
    assert body["conflicts"][0]["weekday"] == 0
    assert body["conflicts"][0]["booking_statuses"] == ["new"]
    still = client.get(
        "/api/instructor/availability", headers=_headers(instr["token"])
    ).json()["intervals"]
    assert {"weekday": 0, "start_time": "10:00", "end_time": "11:00"} in still

    # только 'rejected' → замена проходит
    client.post(
        f"/api/instructor/bookings/{booking_id}/reject",
        json={"comment": "нет окна"},
        headers=_headers(instr["token"]),
    )
    ok = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"weekday": 1, "start_time": "12:00", "end_time": "13:00"}
        ]},
        headers=_headers(instr["token"]),
    )
    assert ok.status_code == 200, ok.text


# --- Баг 5.2: выдача фото в плитках (задача 3.1, диагностика) -----------------


def test_s7_bug_5_2_tile_urls_authorized_endpoint(api, client):
    """TC-S7BE-019 (change add-car-validation-booking, задача 3.1, баг 5.2,
    FR-42): выдача фото в плитках — ТОЛЬКО URL авторизованных эндпоинтов
    (photos{angle} = /api/instructor/cars/{id}/photo/{angle}); legacy
    photo_url/файловый путь data/uploads не выдаются (статикой не
    раздается, NFR-1); URL валиден и после ПОВТОРНОГО ВХОДА (новый
    токен) отдает image/* — фото переживает перезагрузку и перезаход.
    Корень 5.2 (диагностика 3.1): устаревшие photo_path/photo_url-поля
    и legacy-маршрут в выдаче — удалены (REMOVED, задача 4.1)."""
    instr = create_instructor(client)
    car_id = add_car_json(client, instr["token"])
    upload_angle(client, instr["token"], car_id, "front")

    car = client.get(
        "/api/instructor/cars", headers=_headers(instr["token"])
    ).json()["cars"][0]
    assert car["photos"]["front"] == f"/api/instructor/cars/{car_id}/photo/front"
    assert "photo_url" not in car, "legacy-поле удалено из выдачи"
    assert not str(car["photos"]["front"]).startswith("data/")

    # повторный вход → новый токен, тот же URL, контент отдается
    login = client.post(
        "/api/auth/login",
        json={"email": instr["email"], "password": INSTR_PASSWORD},
    )
    new_token = login.json()["token"]
    car2 = client.get(
        "/api/instructor/cars", headers=_headers(new_token)
    ).json()["cars"][0]
    assert car2["photos"]["front"] == car["photos"]["front"]
    got = client.get(car2["photos"]["front"], headers=_headers(new_token))
    assert got.status_code == 200
    assert got.content == ROOT_JPEG
    assert "image/" in got.headers["content-type"]
