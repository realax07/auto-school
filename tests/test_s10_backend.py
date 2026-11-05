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
