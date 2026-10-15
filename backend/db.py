"""SQLite-слой (sdd.md §4): файл data/app.db, WAL, только параметризованные
запросы (?-плейсхолдеры, NFR-2). В БД только хранение, без логики."""
import os
import sqlite3
from pathlib import Path

_DEFAULT_DB_PATH = os.path.join("data", "app.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  surname TEXT NOT NULL,
  name TEXT NOT NULL,
  patronymic TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  phone TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS instructor_applications (
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
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS instructor_cars (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  instructor_id INTEGER NOT NULL,
  brand TEXT NOT NULL,
  model TEXT NOT NULL,
  year INTEGER NOT NULL,
  plate TEXT NOT NULL,
  transmission TEXT NOT NULL CHECK (transmission IN ('manual','automatic')),
  photo_path TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_instructor_cars_instructor
  ON instructor_cars(instructor_id);

CREATE TABLE IF NOT EXISTS availability (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  instructor_id INTEGER NOT NULL,
  weekday INTEGER NOT NULL CHECK (weekday BETWEEN 0 AND 6),
  start_time TEXT NOT NULL,
  end_time TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (instructor_id, weekday, start_time, end_time)
);
CREATE INDEX IF NOT EXISTS idx_availability_instructor
  ON availability(instructor_id);

CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  instructor_id INTEGER NOT NULL,
  student_id INTEGER NOT NULL,
  rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
  text TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (instructor_id, student_id)
);
CREATE INDEX IF NOT EXISTS idx_reviews_instructor
  ON reviews(instructor_id);

CREATE TABLE IF NOT EXISTS student_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL,
  instructor_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'new'
    CHECK (status IN ('new','accepted','denied')),
  deny_comment TEXT,
  car_id INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  decided_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_student_requests_instructor
  ON student_requests(instructor_id, status);
CREATE INDEX IF NOT EXISTS idx_student_requests_student
  ON student_requests(student_id, status);

-- Спринт 3, фикс-ветка (code-review review-001 #6, гонка дубликата):
-- частичный UNIQUE-индекс гарантирует «не более одной АКТИВНОЙ
-- (new/accepted) заявки ученика этому инструктору» на уровне БД —
-- check-then-insert в create_request не защищает от параллельных POST
-- (sync-эндпоинты FastAPI выполняются в threadpool). Отказы (denied)
-- индекс не учитывает — повторная заявка после отказа допустима (ОВ-2).
CREATE UNIQUE INDEX IF NOT EXISTS uq_student_requests_active
  ON student_requests(student_id, instructor_id)
  WHERE status IN ('new','accepted');
"""

# Спринт 0–1: users.role (add-instructor-flow, задача 1.2, sdd.md §16).
_USERS_ROLE_MIGRATION = (
    "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'student'"
)

# Спринт 3 (add-instructor-student-loop): idempotent-миграции по образцу
# users.role. experience_years — стаж числом (arch-review итерация 2,
# MAJ-3: users NOT NULL DEFAULT 0, заявка — NULL); license_photo_path —
# файл ВУ анкеты (NULL = заявка без ВУ).
_COLUMN_MIGRATIONS = (
    ("users", "experience_years",
     "ALTER TABLE users ADD COLUMN experience_years INTEGER NOT NULL DEFAULT 0"),
    ("instructor_applications", "experience_years",
     "ALTER TABLE instructor_applications ADD COLUMN experience_years INTEGER"),
    ("instructor_applications", "license_photo_path",
     "ALTER TABLE instructor_applications ADD COLUMN license_photo_path TEXT"),
)


def init_db() -> None:
    """Создание схемы (users, instructor_applications + 4 таблицы контура
    «инструктор ↔ ученик»: instructor_cars, availability, reviews,
    student_requests) + idempotent-миграции: существующие базы Спринтов
    0–2 поднимаются без пересоздания, записи остаются учениками
    (role='student', experience_years=0)."""
    conn = get_conn()
    try:
        conn.executescript(_SCHEMA)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        if "role" not in columns:
            conn.execute(_USERS_ROLE_MIGRATION)
        for table, column, ddl in _COLUMN_MIGRATIONS:
            columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
            if column not in columns:
                conn.execute(ddl)
        conn.commit()
    finally:
        conn.close()


def _db_path() -> str:
    return os.environ.get("AUTOSCHOOL_DB_PATH", _DEFAULT_DB_PATH)


def get_conn() -> sqlite3.Connection:
    """Соединение с SQLite (data/app.db, WAL, row_factory=Row)."""
    path = Path(_db_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn
