"""Спринт 10 — BACKEND-тесты (change add-calendar-weeks-availability;
задачи 1.1/2.1/3.1, волна D-1 backend). Пишутся ПРОТИВ контрактов
design.md пакета (модель recurring/one_off D1–D4, «Контракт availability»,
«Контракт booking», MAJ-1 арх-ревью Спринта 10 — политика (б):
кросс-строчная проверка экземпляра в create_booking ВНУТРИ
BEGIN IMMEDIATE + дедупликация GET slots).

Покрывают (TC-S10BE-001…008, tasks.md 1.1/2.1/3.1):
- TC-S10BE-001 — миграция recurring/one_off: legacy-график становится
  recurring (slot_date='', id/created_at сохранены, брони не теряют
  availability_id), повторный запуск — no-op; домен UNIQUE/CHECK
  (one_off на другую дату вставляется, recurring-дубликат —
  IntegrityError); индекс занятости экземпляра: две активные брони
  одной серии с разными датами возможны, одной даты — нет;
- TC-S10BE-002…005 — домен availability (задача 3.1);
- TC-S10BE-004, 006…008 — домен booking (задача 2.1).

Трассировка TC → спека (rule 6): в docstring каждого теста — точные
заголовки «### Requirement:/#### Scenario:» дельт
openspec/changes/add-calendar-weeks-availability/specs/{booking,
instructor-availability}/spec.md. Граница времени — с фиктивным NOW
(monkeypatch backend.booking.now_moscow — design «Решения по НФТ»,
NFR-31/MIN-2). time.sleep запрещен (спека qa-pipeline).
"""
import datetime
import sqlite3

import pytest

from conftest import admin_headers, db_path, register

from backend import booking as booking_domain
import backend.db as db

# Точные заголовки Requirement дельт (трассировка rule 6)
REQ_MIGRATION = "Существующий график становится повторяющимся (миграция)"
REQ_SAVE = "Сохранение и восстановление графика"
REQ_TYPES = "Типы слотов: повторяющиеся и разовые"
REQ_PAST = "Запрет правки прошлого"
REQ_BOOKING = "Запрос брони на слот"
REQ_BUSY = "Занятый слот недоступен другим ученикам"
REQ_STUDENT_CAL = "Календарь ученика: недели, реальные даты и разворот повторений"

INSTR_PASSWORD = "Instr1234"

# Старый (до Спринта 10) DDL availability/booking — предсозданная БД
# для миграции (NFR-30: контроль на предсозданных данных).
_LEGACY_SCHEMA = """
CREATE TABLE availability (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  instructor_id INTEGER NOT NULL,
  weekday INTEGER NOT NULL CHECK (weekday BETWEEN 0 AND 6),
  start_time TEXT NOT NULL,
  end_time TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (instructor_id, weekday, start_time, end_time)
);
CREATE INDEX idx_availability_instructor ON availability(instructor_id);
CREATE TABLE booking (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL,
  instructor_id INTEGER NOT NULL,
  availability_id INTEGER NOT NULL,
  lesson_date TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'new'
    CHECK (status IN ('new','confirmed','rejected')),
  reject_comment TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  decided_at TEXT
);
CREATE INDEX idx_booking_instructor ON booking(instructor_id, status);
CREATE UNIQUE INDEX uq_booking_active_slot
  ON booking(availability_id) WHERE status IN ('new','confirmed');
"""


def make_db(path):
    """Создать ПУСТУЮ БД по пути (без init_db)."""
    conn = sqlite3.connect(path)
    conn.close()
    return path


def make_legacy_db(path):
    """Предсозданная БД со СТАРОЙ схемой availability/booking и данными
    (интервалы + активные брони на конкретных датах) — контроль NFR-30."""
    conn = sqlite3.connect(path)
    conn.executescript(_LEGACY_SCHEMA)
    conn.execute(
        "INSERT INTO availability"
        " (id, instructor_id, weekday, start_time, end_time, created_at)"
        " VALUES (1, 7, 0, '10:00', '14:00', '2026-01-05 10:00:00')"
    )
    conn.execute(
        "INSERT INTO availability"
        " (id, instructor_id, weekday, start_time, end_time, created_at)"
        " VALUES (2, 7, 3, '16:00', '18:00', '2026-01-06 11:30:00')"
    )
    conn.execute(
        "INSERT INTO booking (id, student_id, instructor_id,"
        " availability_id, lesson_date, status)"
        " VALUES (101, 5, 7, 1, '2026-01-12', 'confirmed')"
    )
    conn.execute(
        "INSERT INTO booking (id, student_id, instructor_id,"
        " availability_id, lesson_date, status)"
        " VALUES (102, 6, 7, 2, '2026-01-15', 'new')"
    )
    conn.commit()
    conn.close()
    return path


def _availability_rows():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM availability ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def _snapshot():
    """Полный снимок графика/броней/схемы — контроль no-op миграции."""
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    snap = {
        "availability": [
            dict(r) for r in conn.execute(
                "SELECT * FROM availability ORDER BY id").fetchall()
        ],
        "booking": [
            dict(r) for r in conn.execute(
                "SELECT * FROM booking ORDER BY id").fetchall()
        ],
        "schema": [
            (r[0], r[1]) for r in conn.execute(
                "SELECT type, name FROM sqlite_master ORDER BY type, name")
        ],
        "sequence": [
            tuple(r) for r in conn.execute(
                "SELECT name, seq FROM sqlite_sequence ORDER BY name")
        ],
    }
    conn.close()
    return snap


@pytest.fixture()
def legacy_db(client, monkeypatch, tmp_path):
    """client (поднимает приложение на чистой tmp-БД) + предсозданная
    legacy-БД как AUTOSCHOOL_DB_PATH — миграция гоняется прямой
    db.init_db() поверх старых данных (механика conftest)."""
    path = str(tmp_path / "legacy.db")
    make_legacy_db(path)
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", path)
    return path


# --- Задача 1.1: миграция recurring/one_off (TC-S10BE-001) -------------------


def test_s10_migration_legacy_becomes_recurring(legacy_db):
    """TC-S10BE-001 (change add-calendar-weeks-availability, задача 1.1).
    Спека: «### Requirement: Существующий график становится повторяющимся
    (миграция)» — сценарии «Существующий интервал после релиза виден как
    повторяющийся без действий» и «Существующие брони остаются на своих
    слотах и видны на конкретных датах».
    init_db на предсозданной БД со старыми интервалами и бронями: каждая
    строка availability становится recurring (slot_date=''), id и
    created_at СОХРАНЕНЫ, ни одна бронь не потеряла availability_id;
    таблица имеет новые колонки slot_type/slot_date и новый индекс
    занятости (availability_id, lesson_date)."""
    db.init_db()

    rows = _availability_rows()
    assert [r["id"] for r in rows] == [1, 2]
    assert all(r["slot_type"] == "recurring" for r in rows)
    assert all(r["slot_date"] == "" for r in rows)
    assert [r["weekday"] for r in rows] == [0, 3]
    assert [r["start_time"] for r in rows] == ["10:00", "16:00"]
    assert [r["end_time"] for r in rows] == ["14:00", "18:00"]
    assert [r["created_at"] for r in rows] == [
        "2026-01-05 10:00:00", "2026-01-06 11:30:00",
    ]

    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    bookings = conn.execute(
        "SELECT id, availability_id, lesson_date, status FROM booking"
        " ORDER BY id"
    ).fetchall()
    columns = {r[1] for r in conn.execute("PRAGMA table_info(availability)")}
    indexes = {
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'")
    }
    conn.close()
    assert [(b["id"], b["availability_id"], b["lesson_date"], b["status"])
            for b in bookings] == [
        (101, 1, "2026-01-12", "confirmed"),
        (102, 2, "2026-01-15", "new"),
    ]
    assert {"slot_type", "slot_date"} <= columns
    assert {"idx_availability_instructor", "uq_booking_active_slot"} <= indexes


def test_s10_migration_idempotent_noop(legacy_db):
    """TC-S10BE-001 (задача 1.1, NFR-30). Спека: сценарий «Повторный
    запуск миграции не создает дублей».
    Первый init_db выполняет перестройку; повторный (и третий) запуск —
    no-op: строки availability/booking, схема и sqlite_sequence
    не меняются (0 изменений)."""
    db.init_db()
    snap = _snapshot()
    db.init_db()
    db.init_db()
    assert _snapshot() == snap
    assert len(snap["availability"]) == 2  # дублей нет


def test_s10_slot_type_unique_and_check_domain(client):
    """TC-S10BE-001 (задача 1.1, FR-90). Спека: «### Requirement: Типы
    слотов: повторяющиеся и разовые» — сценарий «Совпадение разового с
    экземпляром повторяющегося отображается одним слотом» (домен
    уникальности design.md «Модель данных»).
    На свежей БД: one_off допускает ту же пару «день недели + время» на
    ДРУГУЮ дату и совпадение с экземпляром серии (обе строки);
    recurring-дубликат и одна one_off на дату+время дважды —
    IntegrityError; CHECK: recurring ⇒ без даты, one_off ⇒ с датой."""
    db.init_db()
    conn = sqlite3.connect(db_path())
    # серия: чт 16:00–18:00
    conn.execute(
        "INSERT INTO availability (instructor_id, weekday, start_time,"
        " end_time) VALUES (7, 3, '16:00', '18:00')"
    )
    conn.commit()
    # one_off на ДРУГУЮ дату того же дня недели — вставляется
    conn.execute(
        "INSERT INTO availability (instructor_id, weekday, start_time,"
        " end_time, slot_type, slot_date)"
        " VALUES (7, 3, '16:00', '18:00', 'one_off', '2026-11-12')"
    )
    # one_off ПОВЕРХ экземпляра серии (та же дата+время) — обе строки (FR-90)
    conn.execute(
        "INSERT INTO availability (instructor_id, weekday, start_time,"
        " end_time, slot_type, slot_date)"
        " VALUES (7, 3, '16:00', '18:00', 'one_off', '2026-11-19')"
    )
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        # recurring-дубликат (старое правило сохранено)
        conn.execute(
            "INSERT INTO availability (instructor_id, weekday, start_time,"
            " end_time) VALUES (7, 3, '16:00', '18:00')"
        )
    conn.rollback()
    with pytest.raises(sqlite3.IntegrityError):
        # одна one_off на дату+время — ровно одна строка
        conn.execute(
            "INSERT INTO availability (instructor_id, weekday, start_time,"
            " end_time, slot_type, slot_date)"
            " VALUES (7, 3, '16:00', '18:00', 'one_off', '2026-11-12')"
        )
    conn.rollback()
    with pytest.raises(sqlite3.IntegrityError):
        # recurring ⇒ slot_date=''
        conn.execute(
            "INSERT INTO availability (instructor_id, weekday, start_time,"
            " end_time, slot_type, slot_date)"
            " VALUES (7, 1, '09:00', '10:00', 'recurring', '2026-11-16')"
        )
    conn.rollback()
    with pytest.raises(sqlite3.IntegrityError):
        # one_off ⇒ slot_date непустая
        conn.execute(
            "INSERT INTO availability (instructor_id, weekday, start_time,"
            " end_time, slot_type, slot_date)"
            " VALUES (7, 1, '09:00', '10:00', 'one_off', '')"
        )
    conn.rollback()
    with pytest.raises(sqlite3.IntegrityError):
        # недопустимый тип
        conn.execute(
            "INSERT INTO availability (instructor_id, weekday, start_time,"
            " end_time, slot_type, slot_date)"
            " VALUES (7, 1, '09:00', '10:00', 'weekly', '2026-11-16')"
        )
    conn.rollback()
    conn.close()


def test_s10_instance_index_two_dates_ok_same_date_409_domain(client):
    """TC-S10BE-001 (задача 1.1, D4, NFR-8). Спека: «### Requirement:
    Занятый слот недоступен другим ученикам» — сценарий «Другие даты
    повторяющейся серии остаются доступными» (уровень хранилища).
    Частичный UNIQUE (availability_id, lesson_date) WHERE active: две
    активные брони ОДНОЙ серии с РАЗНЫМИ датами возможны, одной даты —
    нет; rejected не считается (повторный запрос после отклонения — ОВ-5)."""
    db.init_db()
    conn = sqlite3.connect(db_path())
    conn.execute(
        "INSERT INTO availability (id, instructor_id, weekday, start_time,"
        " end_time) VALUES (1, 7, 3, '16:00', '18:00')"
    )
    conn.execute(
        "INSERT INTO booking (id, student_id, instructor_id,"
        " availability_id, lesson_date, status)"
        " VALUES (1, 5, 7, 1, '2026-11-12', 'new')"
    )
    conn.commit()
    # другая дата той же серии — свободна
    conn.execute(
        "INSERT INTO booking (student_id, instructor_id,"
        " availability_id, lesson_date, status)"
        " VALUES (6, 7, 1, '2026-11-19', 'confirmed')"
    )
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        # тот же ЭКЗЕМПЛЯР (та же дата) — вторая активная бронь невозможна
        conn.execute(
            "INSERT INTO booking (student_id, instructor_id,"
            " availability_id, lesson_date, status)"
            " VALUES (7, 7, 1, '2026-11-12', 'confirmed')"
        )
    conn.rollback()
    # rejected выпадает из частичного индекса (ОВ-5)
    conn.execute(
        "INSERT INTO booking (student_id, instructor_id,"
        " availability_id, lesson_date, status)"
        " VALUES (8, 7, 1, '2026-11-12', 'rejected')"
    )
    conn.commit()
    conn.close()


# --- Общие помощники API-кейсов (домены booking/availability) -----------------


def _headers(token):
    return {"X-Session-Token": token}


def apply_body(email):
    return {
        "surname": "Иванов", "name": "Иван", "patronymic": "Иванович",
        "phone": "+7 (911) 222-33-44", "email": email,
        "address": "г. Тест, ул. Полевая, 1", "work_format": "sber",
        "license_number": "9911223344", "license_category": "B",
        "experience_years": 5, "password": INSTR_PASSWORD,
        "password_confirm": INSTR_PASSWORD, "consent": True,
    }


def create_instructor(client, email="instr10@example.com"):
    resp = client.post("/api/instructors/apply", json=apply_body(email))
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
    login = client.post(
        "/api/auth/login", json={"email": email, "password": INSTR_PASSWORD}
    )
    assert login.status_code == 200, login.text
    return {"token": login.json()["token"], "id": approved.json()["user_id"]}


def create_student(client, email="student10@example.com"):
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
    return {"token": login.json()["token"], "id": user_id}


def add_car(client, instructor):
    resp = client.post(
        "/api/instructor/cars",
        json={"brand": "Lada", "model": "Vesta", "year": 2021,
              "plate": "В456ВВ777", "transmission": "manual"},
        headers=_headers(instructor["token"]),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["car_id"]


def accept_pair(client, instructor, student):
    """Пара accepted (заявка ученика → accept инструктором, контур С3)."""
    req = client.post(
        "/api/student/requests",
        json={"instructor_id": instructor["id"]},
        headers=_headers(student["token"]),
    )
    assert req.status_code == 200, req.text
    car_id = add_car(client, instructor)
    acc = client.post(
        f"/api/instructor/requests/{req.json()['request_id']}/accept",
        json={"car_id": car_id},
        headers=_headers(instructor["token"]),
    )
    assert acc.status_code == 200, acc.text


def put_availability(client, instructor, intervals):
    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": intervals},
        headers=_headers(instructor["token"]),
    )
    return resp


def slot_ids(client, student, instructor_id):
    """{weekday: [id, ...]} строк графика (легаси-выдача слотов)."""
    resp = client.get(
        f"/api/student/instructors/{instructor_id}/slots",
        headers=_headers(student["token"]),
    )
    assert resp.status_code == 200, resp.text
    by_weekday: dict[int, list[int]] = {}
    for slot in resp.json()["slots"]:
        by_weekday.setdefault(slot["weekday"], []).append(slot["id"])
    return by_weekday


def book(client, student, availability_id, date=None):
    payload = {"availability_id": availability_id}
    if date is not None:
        payload["date"] = date
    return client.post(
        "/api/student/bookings", json=payload, headers=_headers(student["token"])
    )


def fake_now(monkeypatch, hour=8, minute=0):
    """Фиктивный NOW (МСК) — сегодня в hour:minute (design «Решения по
    НФТ»: тесты границы с фиктивным NOW, monkeypatch хелпера)."""
    fixed = datetime.datetime.combine(
        datetime.date.today(), datetime.time(hour, minute),
        tzinfo=booking_domain._MOSCOW_TZ,
    )
    monkeypatch.setattr(booking_domain, "now_moscow", lambda: fixed)
    return fixed


def next_weekday(weekday, weeks_ahead=1):
    """Ближайшая дата weekday НЕ РАНЬШЕ следующей недели (детерминированно
    будущее относительно любого момента текущей недели)."""
    today = datetime.date.today()
    days_ahead = (weekday - today.weekday()) % 7 + 7 * weeks_ahead
    return today + datetime.timedelta(days=days_ahead)


# --- Задача 2.1: POST bookings +date, будущее, кросс-строчность ---------------


def test_s10_booking_exact_instance_date(client, monkeypatch):
    """TC-S10BE-006 (change add-calendar-weeks-availability, задача 2.1).
    Спека: «### Requirement: Запрос брони на слот» — сценарий «Бронь
    фиксируется на конкретной дате экземпляра».
    Повторяющийся слот «Чт 16:00–18:00»: POST с датой экземпляра → бронь
    именно на эту дату; дата не на weekday серии → 422; другой экземпляр
    серии (другой ученик пары) бронируется на свою дату."""
    fake_now(monkeypatch)
    instructor = create_instructor(client)
    student = create_student(client)
    put_availability(client, instructor, [
        {"weekday": 3, "start_time": "16:00", "end_time": "18:00"},
    ])
    accept_pair(client, instructor, student)
    slot = slot_ids(client, student, instructor["id"])[3][0]

    dec10 = next_weekday(3).isoformat()  # четверг следующей недели
    resp = book(client, student, slot, dec10)
    assert resp.status_code == 200, resp.text
    assert resp.json()["lesson_date"] == dec10
    conn = sqlite3.connect(db_path())
    row = conn.execute(
        "SELECT lesson_date, status FROM booking WHERE availability_id = ?",
        (slot,),
    ).fetchone()
    conn.close()
    assert row == (dec10, "new")

    # дата не на weekday серии (пятница) → 422, записи нет
    friday = (datetime.date.fromisoformat(dec10)
              + datetime.timedelta(days=1)).isoformat()
    bad = book(client, student, slot, friday)
    assert bad.status_code == 422, bad.text
    assert bad.json()["ok"] is False

    # другой экземпляр серии (через неделю) — бронируется другим учеником
    student2 = create_student(client, email="student10b@example.com")
    accept_pair(client, instructor, student2)
    other = book(client, student2, slot,
                 (datetime.date.fromisoformat(dec10)
                  + datetime.timedelta(days=7)).isoformat())
    assert other.status_code == 200, other.text


def test_s10_booking_future_boundary_min1(client, monkeypatch):
    """TC-S10BE-006 (задача 2.1, FR-96/NFR-31, MIN-1). Спека: «###
    Requirement: Запрос брони на слот» — сценарий «Запрос брони на
    прошедший или начавшийся слот отклоняется сервером» (прямой вызов
    API в обход UI). ЕДИНОЕ правило границы: прошедший = начало < NOW
    (МСК) — начало ровно NOW → 422 «Слот уже начался или прошел»,
    начало NOW+1мин → 200; прошедшая дата → 422."""
    instructor = create_instructor(client)
    student = create_student(client)
    put_availability(client, instructor, [
        {"weekday": 3, "start_time": "16:00", "end_time": "18:00"},
    ])
    accept_pair(client, instructor, student)
    slot = slot_ids(client, student, instructor["id"])[3][0]

    thursday = next_weekday(3).isoformat()
    past_thursday = (datetime.date.fromisoformat(thursday)
                     - datetime.timedelta(days=7)).isoformat()

    # граница: начало ровно NOW → 422 (строгое «>»); NOW — МСК того же дня
    now_fixed = datetime.datetime.combine(
        datetime.date.fromisoformat(thursday), datetime.time(16, 0),
        tzinfo=booking_domain._MOSCOW_TZ,
    )
    monkeypatch.setattr(booking_domain, "now_moscow", lambda: now_fixed)
    rejected = book(client, student, slot, thursday)
    assert rejected.status_code == 422, rejected.text
    assert rejected.json()["error"] == "Слот уже начался или прошел"
    conn = sqlite3.connect(db_path())
    assert conn.execute("SELECT COUNT(*) FROM booking").fetchone()[0] == 0
    conn.close()

    # начало NOW+1мин → 200
    now_fixed = datetime.datetime.combine(
        datetime.date.fromisoformat(thursday), datetime.time(15, 59),
        tzinfo=booking_domain._MOSCOW_TZ,
    )
    ok = book(client, student, slot, thursday)
    assert ok.status_code == 200, ok.text

    # слот сегодняшнего дня, начало уже прошло (NOW того же дня позже
    # начала — сценарий «сегодня 16:00–18:00 при текущем времени 17:00»)
    fake_now(monkeypatch, 17, 0)
    past = book(client, student, slot, past_thursday)
    assert past.status_code == 422, past.text


def test_s10_booking_legacy_without_date(client, monkeypatch):
    """TC-S10BE-006 (задача 2.1). Спека: «### Requirement: Запрос брони на
    слот» — сценарий «Запрос в старом формате (без даты) продолжает
    приниматься»: POST {availability_id} без даты → ближайшая будущая
    дата экземпляра серии (materialize, MIN-1); для разового слота
    lesson_date = slot_date; невалидный формат date → 422."""
    fake_now(monkeypatch)
    instructor = create_instructor(client)
    student = create_student(client)
    put_availability(client, instructor, [
        {"weekday": 3, "start_time": "16:00", "end_time": "18:00"},
    ])
    accept_pair(client, instructor, student)
    slot = slot_ids(client, student, instructor["id"])[3][0]

    legacy = book(client, student, slot)
    assert legacy.status_code == 200, legacy.text
    assert legacy.json()["lesson_date"] == \
        booking_domain.materialize_lesson_date(3)

    # one_off без date → lesson_date = slot_date
    one_off_date = next_weekday(3).isoformat()
    conn = sqlite3.connect(db_path())
    cur = conn.execute(
        "INSERT INTO availability (instructor_id, weekday, start_time,"
        " end_time, slot_type, slot_date) VALUES (?, 3, '16:00', '18:00',"
        " 'one_off', ?)",
        (instructor["id"], one_off_date),
    )
    one_off_id = cur.lastrowid
    conn.commit()
    conn.close()
    resp = book(client, student, one_off_id)
    assert resp.status_code == 200, resp.text
    assert resp.json()["lesson_date"] == one_off_date

    # date не ISO/несуществующая → 422
    assert book(client, student, slot, "12.11.2026").status_code == 422
    assert book(client, student, slot, "2026-02-30").status_code == 422


def test_s10_booking_cross_row_same_instance_409(client, monkeypatch):
    """TC-S10BE-004 (задача 2.1, MAJ-1 арх-ревью Спринта 10 — политика (б)).
    Спека: «### Requirement: Занятый слот недоступен другим ученикам» —
    сценарий «Бронь через вторую строку того же экземпляра отклоняется
    (MAJ-1)».
    Обе строки одного экземпляра (серия Чт 16:00–18:00 + разовый слот на
    дату экземпляра): бронь ученика А через разовый слот → бронь ученика
    Б через ПОВТОРЯЮЩИЙСЯ слот (вторую строку того же экземпляра) →
    409 «Слот уже занят», записи нет."""
    fake_now(monkeypatch)
    instructor = create_instructor(client)
    student_a = create_student(client)
    student_b = create_student(client, email="student10b@example.com")
    put_availability(client, instructor, [
        {"weekday": 3, "start_time": "16:00", "end_time": "18:00"},
    ])
    accept_pair(client, instructor, student_a)
    accept_pair(client, instructor, student_b)
    conn = sqlite3.connect(db_path())
    rows = {
        row[1]: row[0]
        for row in conn.execute(
            "SELECT id, slot_type FROM availability"
            " WHERE instructor_id = ?", (instructor["id"],)
        ).fetchall()
    }
    instance_date = next_weekday(3).isoformat()
    # вторая строка экземпляра: one_off на ту же дату+время
    cur = conn.execute(
        "INSERT INTO availability (instructor_id, weekday, start_time,"
        " end_time, slot_type, slot_date) VALUES (?, 3, '16:00', '18:00',"
        " 'one_off', ?)",
        (instructor["id"], instance_date),
    )
    one_off_id = cur.lastrowid
    conn.commit()
    conn.close()

    first = book(client, student_a, one_off_id, instance_date)
    assert first.status_code == 200, first.text

    # бронь через ВТОРУЮ строку того же экземпляра → 409, записи нет
    second = book(client, student_b, rows["recurring"], instance_date)
    assert second.status_code == 409, second.text
    assert second.json()["error"] == "Слот уже занят"
    conn = sqlite3.connect(db_path())
    assert conn.execute(
        "SELECT COUNT(*) FROM booking WHERE instructor_id = ?",
        (instructor["id"],),
    ).fetchone()[0] == 1
    conn.close()


def test_s10_booking_instance_occupancy_and_race(client, monkeypatch):
    """TC-S10BE-006 (задача 2.1, FR-95, NFR-8). Спека: «### Requirement:
    Занятый слот недоступен другим ученикам» — сценарии «Другие даты
    повторяющейся серии остаются доступными», «Параллельные запросы на
    один слот — максимум одна бронь», «Занятый слот не бронируется
    повторно».
    Экземпляр занят → тот же экземпляр другим учеником → 409 (и
    повторный запрос своим «на рассмотрении» → 409); экземпляр через
    неделю той же серии свободен; два ПАРАЛЛЕЛЬНЫХ POST на один
    экземпляр — ровно один 200, второй 409."""
    fake_now(monkeypatch)
    import threading

    instructor = create_instructor(client)
    student = create_student(client)
    student2 = create_student(client, email="student10b@example.com")
    put_availability(client, instructor, [
        {"weekday": 3, "start_time": "16:00", "end_time": "18:00"},
    ])
    accept_pair(client, instructor, student)
    accept_pair(client, instructor, student2)
    slot = slot_ids(client, student, instructor["id"])[3][0]

    d1 = next_weekday(3).isoformat()
    d2 = (datetime.date.fromisoformat(d1)
          + datetime.timedelta(days=7)).isoformat()

    first = book(client, student, slot, d1)
    assert first.status_code == 200, first.text

    # тот же экземпляр другим учеником → 409 без записи
    conflict = book(client, student2, slot, d1)
    assert conflict.status_code == 409, conflict.text
    # повторный запрос СВОЙ «на рассмотрении» → 409
    assert book(client, student, slot, d1).status_code == 409
    conn = sqlite3.connect(db_path())
    assert conn.execute(
        "SELECT COUNT(*) FROM booking WHERE availability_id = ?", (slot,)
    ).fetchone()[0] == 1
    conn.close()

    # другая дата серии — свободна
    other = book(client, student2, slot, d2)
    assert other.status_code == 200, other.text

    # гонка: два параллельных POST на один свободный экземпляр
    d3 = (datetime.date.fromisoformat(d1)
          + datetime.timedelta(days=14)).isoformat()
    barrier = threading.Barrier(2)
    results: list[int] = []

    def worker(token):
        barrier.wait()
        results.append(book(client, {"token": token}, slot, d3).status_code)

    t1 = threading.Thread(target=worker, args=(student["token"],))
    t2 = threading.Thread(target=worker, args=(student2["token"],))
    t1.start()
    t2.start()
    t1.join(30)
    t2.join(30)
    assert sorted(results) == [200, 409], results
    conn = sqlite3.connect(db_path())
    active = conn.execute(
        "SELECT COUNT(*) FROM booking WHERE availability_id = ?"
        " AND lesson_date = ? AND status IN ('new','confirmed')",
        (slot, d3),
    ).fetchone()[0]
    conn.close()
    assert active == 1


# --- Задача 2.1: GET slots?date= — экземпляры недели --------------------------


def test_s10_slots_week_instances_and_dedup(client, monkeypatch):
    """TC-S10BE-007 (задача 2.1, D7; FR-94/FR-95, MAJ-1 (б) — дедупликация).
    Спека: «### Requirement: Календарь ученика: недели, реальные даты и
    разворот повторений» — сценарии «Повторяющийся слот развернут в
    экземпляры каждой отображаемой недели», «Разовый слот виден только
    на своей дате», «Свои брони и запросы показаны ровно на своих
    слотах»; «### Requirement: Типы слотов: повторяющиеся и разовые» —
    сценарий «Совпадение разового с экземпляром повторяющегося
    отображается одним слотом» (серверная выдача: один instance,
    availability_id one_off-строки, state агрегирован).
    week {monday, sunday}; one_off вне недели не попадает в instances;
    state: pending (свой 'new') старше busy; занятость видна и по
    второй строке (бронь через one_off делает экземпляр busy)."""
    fake_now(monkeypatch)
    instructor = create_instructor(client)
    student = create_student(client)
    student2 = create_student(client, email="student10b@example.com")
    put_availability(client, instructor, [
        {"weekday": 3, "start_time": "16:00", "end_time": "18:00"},
        {"weekday": 1, "start_time": "09:00", "end_time": "10:00"},
    ])
    accept_pair(client, instructor, student)
    accept_pair(client, instructor, student2)

    monday = next_weekday(0)  # понедельник следующей недели
    thursday = monday + datetime.timedelta(days=3)
    conn = sqlite3.connect(db_path())
    cur = conn.execute(
        "INSERT INTO availability (instructor_id, weekday, start_time,"
        " end_time, slot_type, slot_date) VALUES (?, 3, '16:00', '18:00',"
        " 'one_off', ?)",
        (instructor["id"], thursday.isoformat()),
    )
    one_off_id = cur.lastrowid
    conn.commit()
    conn.close()

    # одинаковый экземпляр: бронь через one_off (вторая строка) —
    # занятость ЕДИНА по обеим строкам (проверка create_booking — MAJ-1)
    assert book(
        client, student2, one_off_id, thursday.isoformat()
    ).status_code == 200
    slots = slot_ids(client, student, instructor["id"])
    recurring_thu = slots[3][0]  # строка-серия того же экземпляра
    resp = client.get(
        f"/api/student/instructors/{instructor['id']}/slots"
        f"?date={monday.isoformat()}",
        headers=_headers(student["token"]),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["week"] == {
        "monday": monday.isoformat(),
        "sunday": (monday + datetime.timedelta(days=6)).isoformat(),
    }
    instances = body["instances"]
    # дедупликация: совпавший экземпляр — ОДИН instance с one_off-носителем
    thu = [i for i in instances if i["date"] == thursday.isoformat()]
    assert len(thu) == 1
    assert thu[0]["availability_id"] == one_off_id
    assert thu[0]["weekday"] == 3
    assert thu[0]["start_time"] == "16:00" and thu[0]["end_time"] == "18:00"
    assert thu[0]["state"] == "busy"  # чужая (student2) активная бронь

    # recurring-серия развернута во ВСЕ недели: соседняя (без совпадения
    # one_off) показывает ту же серию своим availability_id
    prev_monday = monday - datetime.timedelta(days=7)
    resp_prev = client.get(
        f"/api/student/instructors/{instructor['id']}/slots"
        f"?date={prev_monday.isoformat()}",
        headers=_headers(student["token"]),
    ).json()
    prev_thu = [i for i in resp_prev["instances"]
                if i["date"] == (prev_monday
                                 + datetime.timedelta(days=3)).isoformat()]
    assert len(prev_thu) == 1
    assert prev_thu[0]["availability_id"] == recurring_thu
    assert prev_thu[0]["state"] == "free"

    # порядок выдачи — по дате и времени
    assert [i["date"] for i in instances] == sorted(
        i["date"] for i in instances)

    # свой запрос 'new' ровно на своем экземпляре: pending старше busy
    d2 = (thursday + datetime.timedelta(days=7)).isoformat()
    assert book(client, student, recurring_thu, d2).status_code == 200
    resp2 = client.get(
        f"/api/student/instructors/{instructor['id']}/slots"
        f"?date={(monday + datetime.timedelta(days=7)).isoformat()}",
        headers=_headers(student["token"]),
    ).json()
    mine = [i for i in resp2["instances"] if i["date"] == d2]
    assert len(mine) == 1 and mine[0]["state"] == "pending"


def test_s10_slots_date_validation_and_access(client, monkeypatch):
    """TC-S10BE-007/008 (задача 2.1; MIN-4 арх-ревью, NFR-7 наследование).
    Спека: «### Requirement: Календарь ученика: недели, реальные даты и
    разворот повторений» (серверная выдача и доступ).
    date не ISO (12.11.2026) / несуществующий день (2026-02-30) → 422
    {ok:false} ДО приведения к понедельнику; без параметра — легаси-ответ
    {ok, slots:[...]} прежнего контракта; нет принятой пары → 403;
    несуществующий инструктор → 404 (в обеих формах выдачи)."""
    fake_now(monkeypatch)
    instructor = create_instructor(client)
    student = create_student(client)
    put_availability(client, instructor, [
        {"weekday": 3, "start_time": "16:00", "end_time": "18:00"},
    ])
    accept_pair(client, instructor, student)

    base = f"/api/student/instructors/{instructor['id']}/slots"
    for bad in ("12.11.2026", "2026-02-30", "2026-1-5", "not-a-date"):
        resp = client.get(
            f"{base}?date={bad}", headers=_headers(student["token"])
        )
        assert resp.status_code == 422, (bad, resp.text)
        assert resp.json()["ok"] is False

    # легаси-ответ (без date) — прежний контракт
    legacy = client.get(base, headers=_headers(student["token"]))
    assert legacy.status_code == 200, legacy.text
    slots = legacy.json()["slots"]
    assert slots == [{
        "id": slots[0]["id"], "weekday": 3, "start_time": "16:00",
        "end_time": "18:00", "state": "free",
    }]

    # доступ: 403 без пары, 404 несуществующий инструктор — обе формы
    loner = create_student(client, email="student10c@example.com")
    assert client.get(
        base, headers=_headers(loner["token"])
    ).status_code == 403
    assert client.get(
        f"{base}?date={next_weekday(0).isoformat()}",
        headers=_headers(loner["token"]),
    ).status_code == 403
    ghost = "/api/student/instructors/999999/slots"
    assert client.get(
        ghost, headers=_headers(student["token"])
    ).status_code == 404
    assert client.get(
        f"{ghost}?date={next_weekday(0).isoformat()}",
        headers=_headers(student["token"]),
    ).status_code == 404
