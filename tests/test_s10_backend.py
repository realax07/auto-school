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
    """TC-S10BE-002 (задача 1.1, NFR-30). Спека: сценарий «Повторный
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
    """TC-S10BE-003 (задача 1.1, FR-90). Спека: «### Requirement: Типы
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
    """TC-S10BE-004 (задача 1.1, D4, NFR-8). Спека: «### Requirement:
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
    """TC-S10BE-005 (change add-calendar-weeks-availability, задача 2.1).
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
    """TC-S10BE-007 (задача 2.1). Спека: «### Requirement: Запрос брони на
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
    """TC-S10BE-008 (задача 2.1, MAJ-1 арх-ревью Спринта 10 — политика (б)).
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
    """TC-S10BE-009 (задача 2.1, FR-95, NFR-8). Спека: «### Requirement:
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
    """TC-S10BE-010 (задача 2.1, D7; FR-94/FR-95, MAJ-1 (б) — дедупликация).
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
    """TC-S10BE-011/008 (задача 2.1; MIN-4 арх-ревью, NFR-7 наследование).
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


# --- Задача 3.1: availability GET/PUT типы/даты, запрет прошлого, дифф --------


def availability_rows():
    """Строки availability последнего инструктора (полный ключ + id)."""
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM availability ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def test_s10_availability_types_save_and_readback(client, monkeypatch):
    """TC-S10BE-012 (change add-calendar-weeks-availability, задача 3.1).
    Спека: «### Requirement: Типы слотов: повторяющиеся и разовые» —
    сценарии «В одной неделе сочетаются оба типа», «Совпадение разового с
    экземпляром повторяющегося отображается одним слотом» (серверно: обе
    строки, FR-90); «### Requirement: Сохранение и восстановление
    графика» — «График восстанавливается после перезахода» (с типами).
    PUT со смешанным графиком (recurring + one_off на одну дату)
    сохраняется и восстанавливается GET-ом: recurring — date null,
    one_off — date своя; совпадение one_off с экземпляром серии — ОБЕ
    строки в БД допускаются; замена полным графиком другого типа
    убирает/добавляет строки."""
    fake_now(monkeypatch)
    instructor = create_instructor(client)
    one_off_date = next_weekday(3).isoformat()
    put = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"weekday": 3, "start_time": "16:00", "end_time": "18:00",
             "slot_type": "recurring"},
            {"weekday": 3, "start_time": "16:00", "end_time": "18:00",
             "slot_type": "one_off", "date": one_off_date},
            {"weekday": 1, "start_time": "09:00", "end_time": "10:00"},
        ]},
        headers=_headers(instructor["token"]),
    )
    assert put.status_code == 200, put.text
    intervals = put.json()["intervals"]
    assert {"weekday": 3, "start_time": "16:00", "end_time": "18:00",
            "slot_type": "recurring", "date": None} in intervals
    assert {"weekday": 3, "start_time": "16:00", "end_time": "18:00",
            "slot_type": "one_off", "date": one_off_date} in intervals
    assert {"weekday": 1, "start_time": "09:00", "end_time": "10:00",
            "slot_type": "recurring", "date": None} in intervals

    # перезаход: тот же график с теми же типами
    login = client.post(
        "/api/auth/login",
        json={"email": "instr10@example.com", "password": INSTR_PASSWORD},
    )
    fresh = client.get(
        "/api/instructor/availability",
        headers=_headers(login.json()["token"]),
    ).json()["intervals"]
    assert len(fresh) == 3
    assert sum(1 for i in fresh if i["slot_type"] == "one_off") == 1

    # совпадение one_off с экземпляром серии — ОБЕ строки в БД (FR-90)
    assert len(availability_rows()) == 3

    # полная замена: убрали серию и one_off, добавили другой разовый
    other_date = next_weekday(5).isoformat()
    replace = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"weekday": 5, "start_time": "12:00", "end_time": "13:00",
             "slot_type": "one_off", "date": other_date},
        ]},
        headers=_headers(instructor["token"]),
    )
    assert replace.status_code == 200, replace.text
    assert replace.json()["intervals"] == [
        {"weekday": 5, "start_time": "12:00", "end_time": "13:00",
         "slot_type": "one_off", "date": other_date}
    ]
    assert len(availability_rows()) == 1


def test_s10_availability_validation_types(client):
    """TC-S10BE-013 (задача 3.1, FR-90/D5). Спека: «### Requirement:
    Сохранение и восстановление графика» (валидации нового контракта,
    design «Обработка ошибок»).
    one_off без date → 422; one_off с несуществующей датой (2026-02-30)
    → 422; one_off с чужим weekday → 422; recurring с date → 422;
    неизвестный slot_type → 422; график при отказе не изменен."""
    instructor = create_instructor(client)
    ok_date = next_weekday(2).isoformat()
    bad_payloads = [
        {"weekday": 2, "start_time": "10:00", "end_time": "12:00",
         "slot_type": "one_off"},                                    # без date
        {"weekday": 2, "start_time": "10:00", "end_time": "12:00",
         "slot_type": "one_off", "date": "2026-02-30"},              # не существует
        {"weekday": 4, "start_time": "10:00", "end_time": "12:00",
         "slot_type": "one_off", "date": ok_date},                   # weekday ≠ дате
        {"weekday": 2, "start_time": "10:00", "end_time": "12:00",
         "slot_type": "recurring", "date": ok_date},                 # recurring+date
        {"weekday": 2, "start_time": "10:00", "end_time": "12:00",
         "slot_type": "weekly"},                                     # неизвестный тип
    ]
    for payload in bad_payloads:
        resp = client.put(
            "/api/instructor/availability",
            json={"intervals": [payload]},
            headers=_headers(instructor["token"]),
        )
        assert resp.status_code == 422, (payload, resp.text)
        assert resp.json()["ok"] is False
    assert availability_rows() == []


def test_s10_availability_409_instances_with_date(client, monkeypatch):
    """TC-S10BE-014 (задача 3.1, MAJ-1 на уровне ЭКЗЕМПЛЯРОВ, FR-92).
    Спека: «### Requirement: Сохранение и восстановление графика» —
    сценарии «PUT, убирающий экземпляр с активной бронью, отклоняется с
    409 (MAJ-1, уровень экземпляров)», «Экземпляры с только отклоненными
    бронями замене не мешают», «Прошедшие экземпляры не блокируют
    замену и не изменяются».
    PUT, убирающий one_off с активной бронью → 409 с ДАТОЙ в перечне
    (conflicts[0]['date']), график не изменен; убирающий серию с бронью
    на конкретный экземпляр → 409, но при СОХРАНЕНИИ серии → 200
    (экземпляр покрыт); только rejected-брони замене не мешают;
    прошедший экземпляр (lesson_date в прошлом) не блокирует."""
    fake_now(monkeypatch)
    instructor = create_instructor(client)
    student = create_student(client)
    one_off_date = next_weekday(3).isoformat()
    put = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"weekday": 3, "start_time": "16:00", "end_time": "18:00",
             "slot_type": "one_off", "date": one_off_date},
        ]},
        headers=_headers(instructor["token"]),
    )
    assert put.status_code == 200, put.text
    accept_pair(client, instructor, student)
    one_off_id = availability_rows()[0]["id"]
    booked = book(client, student, one_off_id, one_off_date)
    assert booked.status_code == 200, booked.text

    # убираем one_off с активной бронью → 409, дата в перечне
    # (тело НОВОГО формата — легаси-тело one_off убрать не может, MAJ-2)
    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"weekday": 1, "start_time": "09:00", "end_time": "10:00",
             "slot_type": "recurring"},
        ]},
        headers=_headers(instructor["token"]),
    )
    assert resp.status_code == 409, resp.text
    conflict = resp.json()["conflicts"][0]
    assert conflict["date"] == one_off_date
    assert conflict["weekday"] == 3
    assert conflict["booking_statuses"] == ["new"]
    assert "16:00" in resp.json()["error"] and "18:00" in resp.json()["error"]
    # график не изменен
    assert len(availability_rows()) == 1

    # только rejected-брони → замена проходит («…отклоненными не мешают»)
    client.post(
        f"/api/instructor/bookings/{booked.json()['booking_id']}/reject",
        json={"comment": "не могу"},
        headers=_headers(instructor["token"]),
    )
    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"weekday": 1, "start_time": "09:00", "end_time": "10:00",
             "slot_type": "recurring"},
        ]},
        headers=_headers(instructor["token"]),
    )
    assert resp.status_code == 200, resp.text

    # серия с активной бронью на конкретный экземпляр: убрали серию →
    # 409 с датой экземпляра; СОХРАНИЛИ серию → 200 (экземпляр покрыт)
    instructor2 = create_instructor(client, email="instr10b@example.com")
    student2 = create_student(client, email="student10d@example.com")
    put_availability(client, instructor2, [
        {"weekday": 3, "start_time": "16:00", "end_time": "18:00"},
    ])
    accept_pair(client, instructor2, student2)
    series_id = availability_rows()[-1]["id"]
    d1 = next_weekday(3).isoformat()
    assert book(client, student2, series_id, d1).status_code == 200
    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"weekday": 1, "start_time": "09:00", "end_time": "10:00"},
        ]},
        headers=_headers(instructor2["token"]),
    )
    assert resp.status_code == 409
    assert resp.json()["conflicts"][0]["date"] == d1
    keep = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"weekday": 3, "start_time": "16:00", "end_time": "18:00"},
            {"weekday": 1, "start_time": "09:00", "end_time": "10:00"},
        ]},
        headers=_headers(instructor2["token"]),
    )
    assert keep.status_code == 200, keep.text

    # прошедший экземпляр (lesson_date в прошлом) не блокирует замену,
    # запись брони остается как история («Прошедшие экземпляры…»)
    conn = sqlite3.connect(db_path())
    conn.execute(
        "UPDATE booking SET lesson_date = '2026-01-08' WHERE id = ("
        " SELECT MAX(id) FROM booking)"
    )
    conn.commit()
    conn.close()
    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"weekday": 1, "start_time": "09:00", "end_time": "10:00"},
        ]},
        headers=_headers(instructor2["token"]),
    )
    assert resp.status_code == 200, resp.text
    conn = sqlite3.connect(db_path())
    kept = conn.execute(
        "SELECT lesson_date, status FROM booking ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    assert kept == ("2026-01-08", "new")


def test_s10_availability_past_ban_new_format(client, monkeypatch):
    """TC-S10BE-015 (задача 3.1, FR-93/NFR-31/D6, MIN-1). Спека: «###
    Requirement: Запрет правки прошлого» — сценарий «Сервер отклоняет
    сохранение, меняющее прошедший экземпляр, в обход UI»; «###
    Requirement: Сохранение и восстановление графика» — «Попытка
    изменения прошедшего слота отклоняется сервером».
    Прямой PUT нового формата: убирает прошедший one_off → 422;
    меняет прошедший one_off (другое время) → 422; создает one_off с
    прошедшей датой → 422; прошедшая one_off, возвращенная БЕЗ
    изменений, сохраняется (клиент возвращает прошедшие one_off без
    изменений); прошедшая по времени В МОМЕНТ сохранения (была будущей)
    и убранная из payload → 422; граница MIN-1: начало ровно NOW —
    правится (проходит)."""
    fake_now(monkeypatch)
    instructor = create_instructor(client)
    yesterday = (datetime.date.today() - datetime.timedelta(days=1))
    conn = sqlite3.connect(db_path())
    cur = conn.execute(
        "INSERT INTO availability (instructor_id, weekday, start_time,"
        " end_time, slot_type, slot_date) VALUES (?, ?, '10:00', '12:00',"
        " 'one_off', ?)",
        (instructor["id"], yesterday.weekday(), yesterday.isoformat()),
    )
    past_one_off_id = cur.lastrowid
    conn.commit()
    conn.close()
    base_key = {"weekday": yesterday.weekday(), "start_time": "10:00",
                "end_time": "12:00", "slot_type": "one_off",
                "date": yesterday.isoformat()}

    # (б) убирает прошедший one_off → 422, график не изменен
    # (тело НОВОГО формата: легаси-тело one_off убрать не может — MAJ-2)
    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"weekday": 1, "start_time": "09:00", "end_time": "10:00",
             "slot_type": "recurring"},
        ]},
        headers=_headers(instructor["token"]),
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["error"] == "Прошедшие слоты не подлежат изменению"
    assert len(availability_rows()) == 1

    # меняет прошедший one_off (другое время) → 422
    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {**base_key, "start_time": "10:00", "end_time": "13:00"},
        ]},
        headers=_headers(instructor["token"]),
    )
    assert resp.status_code == 422, resp.text

    # (а) создает one_off с прошедшей датой → 422
    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            base_key,
            {"weekday": yesterday.weekday(), "start_time": "14:00",
             "end_time": "15:00", "slot_type": "one_off",
             "date": yesterday.isoformat()},
        ]},
        headers=_headers(instructor["token"]),
    )
    assert resp.status_code == 422, resp.text

    # прошедшая one_off возвращенная БЕЗ изменений → 200 (клиентский
    # контракт: прошедшие one_off возвращаются в payload без изменений)
    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            base_key,
            {"weekday": 1, "start_time": "09:00", "end_time": "10:00"},
        ]},
        headers=_headers(instructor["token"]),
    )
    assert resp.status_code == 200, resp.text
    conn = sqlite3.connect(db_path())
    still = conn.execute(
        "SELECT COUNT(*) FROM availability WHERE id = ?",
        (past_one_off_id,),
    ).fetchone()[0]
    conn.close()
    assert still == 1

    # прошла по времени В МОМЕНТ сохранения (была будущей при создании),
    # убрана из payload → 422 (immutable-история — design D6)
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    conn = sqlite3.connect(db_path())
    conn.execute(
        "INSERT INTO availability (instructor_id, weekday, start_time,"
        " end_time, slot_type, slot_date) VALUES (?, ?, '08:00', '09:00',"
        " 'one_off', ?)",
        (instructor["id"],
         datetime.date.fromisoformat(tomorrow).weekday(), tomorrow),
    )
    conn.commit()
    conn.close()
    # NOW переведен на послезавтра 10:00 — «завтрашний» слот стал прошлым
    future_now = datetime.datetime.combine(
        datetime.date.today() + datetime.timedelta(days=2),
        datetime.time(10, 0), tzinfo=booking_domain._MOSCOW_TZ,
    )
    monkeypatch.setattr(booking_domain, "now_moscow", lambda: future_now)
    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            base_key,
            {"weekday": 1, "start_time": "09:00", "end_time": "10:00"},
        ]},
        headers=_headers(instructor["token"]),
    )
    assert resp.status_code == 422, resp.text

    # граница MIN-1: начало РОВНО NOW — правится (≥ NOW), проходит;
    # прошедшие one_off БД возвращены в payload БЕЗ изменений
    # (клиентский контракт), поэтому правило (б) не нарушено
    fake_now(monkeypatch, 16, 0)
    today = datetime.date.today()
    tomorrow_key = {"weekday": datetime.date.fromisoformat(tomorrow).weekday(),
                    "start_time": "08:00", "end_time": "09:00",
                    "slot_type": "one_off", "date": tomorrow}
    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            base_key,
            tomorrow_key,
            {"weekday": 1, "start_time": "09:00", "end_time": "10:00"},
            {"weekday": today.weekday(), "start_time": "16:00",
             "end_time": "18:00", "slot_type": "one_off",
             "date": today.isoformat()},
        ]},
        headers=_headers(instructor["token"]),
    )
    assert resp.status_code == 200, resp.text


def test_s10_availability_legacy_body_maj2(client, monkeypatch):
    """TC-S10BE-016 (задача 3.1, NFR-29/MAJ-2 арх-ревью). Спека: «###
    Requirement: Сохранение и восстановление графика» — сценарий «Запрос
    в старом формате продолжает приниматься (MAJ-2)».
    PUT легаси-тела {intervals:[{weekday,start_time,end_time}]} при
    наличии в БД прошедшей И будущей one_off → 200: recurring-интервалы
    тела заменяют серию, ОБЕ one_off (прошедшая и будущая) сохранены БЕЗ
    изменений (легаси-клиент не может ни убрать, ни изменить разовый
    слот — запрет прошлого выполняется конструктивно)."""
    fake_now(monkeypatch)
    instructor = create_instructor(client)
    yesterday = (datetime.date.today() - datetime.timedelta(days=1))
    future = next_weekday(3)
    conn = sqlite3.connect(db_path())
    conn.executemany(
        "INSERT INTO availability (instructor_id, weekday, start_time,"
        " end_time, slot_type, slot_date) VALUES (?, ?, '10:00', '12:00',"
        " 'one_off', ?)",
        [
            (instructor["id"], yesterday.weekday(), yesterday.isoformat()),
            (instructor["id"], future.weekday(), future.isoformat()),
        ],
    )
    conn.commit()
    conn.close()

    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"weekday": 1, "start_time": "09:00", "end_time": "11:00"},
        ]},
        headers=_headers(instructor["token"]),
    )
    assert resp.status_code == 200, resp.text
    intervals = resp.json()["intervals"]
    assert {"weekday": 1, "start_time": "09:00", "end_time": "11:00",
            "slot_type": "recurring", "date": None} in intervals
    assert {"weekday": yesterday.weekday(), "start_time": "10:00",
            "end_time": "12:00", "slot_type": "one_off",
            "date": yesterday.isoformat()} in intervals
    assert {"weekday": future.weekday(), "start_time": "10:00",
            "end_time": "12:00", "slot_type": "one_off",
            "date": future.isoformat()} in intervals

    # и GET возвращает тот же полный график
    got = client.get(
        "/api/instructor/availability",
        headers=_headers(instructor["token"]),
    ).json()["intervals"]
    assert len(got) == 3


def test_s10_availability_diff_write_and_rebind(client, monkeypatch):
    """TC-S10BE-017 (задача 3.1, дифф-запись MAJ-1 — design «Экземпляр и
    разворот серий»). Спека: «### Requirement: Сохранение и
    восстановление графика» (дифф-запись: id сохраненных строк не
    меняются; перепривязка брони при покрытой замене носителя).
    Сохранение без правок сохраняет id строки (бронь видна в выдаче);
    удаление разового слота с активной бронью при СОХРАНЯЮЩЕЙСЯ серии
    того же экземпляра → 200 и бронь ПЕРЕПРИВЯЗАНА на серию (видна,
    дата/статус прежние)."""
    fake_now(monkeypatch)
    instructor = create_instructor(client)
    student = create_student(client)
    one_off_date = next_weekday(3).isoformat()
    client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"weekday": 3, "start_time": "16:00", "end_time": "18:00",
             "slot_type": "recurring"},
            {"weekday": 3, "start_time": "16:00", "end_time": "18:00",
             "slot_type": "one_off", "date": one_off_date},
        ]},
        headers=_headers(instructor["token"]),
    )
    accept_pair(client, instructor, student)
    before = availability_rows()
    one_off = next(r for r in before if r["slot_type"] == "one_off")
    series = next(r for r in before if r["slot_type"] == "recurring")
    booked = book(client, student, one_off["id"], one_off_date)
    assert booked.status_code == 200, booked.text
    booking_id = booked.json()["booking_id"]

    # сохранение без правок → id обеих строк сохранены (дифф, не
    # DELETE+INSERT), бронь продолжает ссылаться на ту же строку
    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"weekday": 3, "start_time": "16:00", "end_time": "18:00",
             "slot_type": "recurring"},
            {"weekday": 3, "start_time": "16:00", "end_time": "18:00",
             "slot_type": "one_off", "date": one_off_date},
        ]},
        headers=_headers(instructor["token"]),
    )
    assert resp.status_code == 200, resp.text
    after = availability_rows()
    assert {r["id"] for r in after} == {r["id"] for r in before}
    conn = sqlite3.connect(db_path())
    row = conn.execute(
        "SELECT availability_id, lesson_date, status FROM booking"
        " WHERE id = ?", (booking_id,)
    ).fetchone()
    conn.close()
    assert row == (one_off["id"], one_off_date, "new")

    # удаление разового слота с бронью при сохраняющейся серии → 200,
    # бронь перепривязана на строку-носитель (серию того же экземпляра)
    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"weekday": 3, "start_time": "16:00", "end_time": "18:00",
             "slot_type": "recurring"},
        ]},
        headers=_headers(instructor["token"]),
    )
    assert resp.status_code == 200, resp.text
    remaining = availability_rows()
    assert [r["id"] for r in remaining] == [series["id"]]
    conn = sqlite3.connect(db_path())
    row = conn.execute(
        "SELECT availability_id, lesson_date, status FROM booking"
        " WHERE id = ?", (booking_id,)
    ).fetchone()
    visible = conn.execute(
        "SELECT COUNT(*) FROM booking AS b"
        " JOIN availability AS a ON a.id = b.availability_id"
        " WHERE b.id = ?", (booking_id,)
    ).fetchone()[0]
    conn.close()
    assert row == (series["id"], one_off_date, "new")
    assert visible == 1  # JOIN выдач не разорван (бронь-сирота невозможна)


def _join_visible_booking_id(booking_id):
    """(availability_id, lesson_date, статус, видимость через JOIN) брони."""
    conn = sqlite3.connect(db_path())
    row = conn.execute(
        "SELECT b.availability_id, b.lesson_date, b.status,"
        " (SELECT COUNT(*) FROM booking AS bj"
        "  JOIN availability AS aj ON aj.id = bj.availability_id"
        "  WHERE bj.id = b.id)"
        " FROM booking AS b WHERE b.id = ?",
        (booking_id,),
    ).fetchone()
    conn.close()
    return row


def test_s10_availability_rebind_series_to_oneoff_new_carrier(
    client, monkeypatch
):
    """TC-S10BE-018 (задача 3.1, дифф-запись MAJ-1; review-003-3.1 major-1 —
    носитель ДОБАВЛЯЕТСЯ этим же PUT). Спека: «### Requirement:
    Сохранение и восстановление графика» — сценарий «Изменение графика
    перезаписывает сохраненный» (серия снята, разовый на дату брони
    добавлен); «### Requirement: Типы слотов: повторяющиеся и разовые» —
    смена типа (FR-91) + design «Экземпляр и разворот серий»
    (перепривязка на строку-носитель ОБЯЗАТЕЛЬНА при покрытой замене).
    Смена типа серия→one_off одним PUT: активная бронь на экземпляре
    серии, новый график = one_off на дату этой брони (серий больше нет) →
    200; бронь перепривязана на НОВУЮ строку (id ≠ удаленной серии),
    видна через JOIN booking JOIN availability, lesson_date/статус
    прежние (бронь-сирота невозможна)."""
    fake_now(monkeypatch)
    instructor = create_instructor(client)
    student = create_student(client)
    put_availability(client, instructor, [
        {"weekday": 3, "start_time": "16:00", "end_time": "18:00",
         "slot_type": "recurring"},
    ])
    accept_pair(client, instructor, student)
    series = availability_rows()[0]
    instance_date = next_weekday(3).isoformat()
    booked = book(client, student, series["id"], instance_date)
    assert booked.status_code == 200, booked.text
    booking_id = booked.json()["booking_id"]

    # «Смена типа»: серия удалена, one_off на дату брони добавлен —
    # экземпляр покрыт новой строкой (409 нет), носитель ДОБАВЛЯЕТСЯ
    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"weekday": 3, "start_time": "16:00", "end_time": "18:00",
             "slot_type": "one_off", "date": instance_date},
        ]},
        headers=_headers(instructor["token"]),
    )
    assert resp.status_code == 200, resp.text

    rows = availability_rows()
    # осталась ровно одна строка — НОВАЯ (one_off), серия удалена
    assert len(rows) == 1
    carrier = rows[0]
    assert carrier["id"] != series["id"]
    assert (carrier["slot_type"], carrier["slot_date"]) == \
        ("one_off", instance_date)
    # бронь перепривязана на новую строку; lesson_date/статус прежние;
    # JOIN booking JOIN availability не разорван (сирота невозможна)
    assert _join_visible_booking_id(booking_id) == \
        (carrier["id"], instance_date, "new", 1)


def test_s10_availability_rebind_oneoff_to_series_new_carrier(
    client, monkeypatch
):
    """TC-S10BE-019 (задача 3.1, дифф-запись MAJ-1; review-003-3.1 major-1 —
    симметричный one_off→серия). Спека: «### Requirement: Сохранение и
    восстановление графика» — сценарий «Изменение графика перезаписывает
    сохраненный»; «### Requirement: Типы слотов: повторяющиеся и
    разовые» — смена типа разового в повторяющийся (FR-91) + design
    «Экземпляр и разворот серий» (перепривязка обязательна).
    Смена типа one_off→серия одним PUT: активная бронь на разовом слоте,
    новый график = recurring-серия того же дня/времени (one_off больше
    нет) → 200; бронь перепривязана на НОВУЮ строку-серию, видна через
    JOIN, lesson_date/статус прежние."""
    fake_now(monkeypatch)
    instructor = create_instructor(client)
    student = create_student(client)
    instance_date = next_weekday(3).isoformat()
    put_availability(client, instructor, [
        {"weekday": 3, "start_time": "16:00", "end_time": "18:00",
         "slot_type": "one_off", "date": instance_date},
    ])
    accept_pair(client, instructor, student)
    one_off = availability_rows()[0]
    booked = book(client, student, one_off["id"], instance_date)
    assert booked.status_code == 200, booked.text
    booking_id = booked.json()["booking_id"]

    # «Смена типа»: разовый удален, серия того же экземпляра добавлена
    resp = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"weekday": 3, "start_time": "16:00", "end_time": "18:00",
             "slot_type": "recurring"},
        ]},
        headers=_headers(instructor["token"]),
    )
    assert resp.status_code == 200, resp.text

    rows = availability_rows()
    assert len(rows) == 1
    carrier = rows[0]
    assert carrier["id"] != one_off["id"]
    assert (carrier["slot_type"], carrier["slot_date"]) == ("recurring", "")
    # бронь перепривязана на новую строку-серию; дата/статус прежние;
    # JOIN не разорван (бронь-сирота невозможна)
    assert _join_visible_booking_id(booking_id) == \
        (carrier["id"], instance_date, "new", 1)
