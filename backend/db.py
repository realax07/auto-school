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
"""

_USERS_ROLE_MIGRATION = (
    "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'student'"
)


def init_db() -> None:
    """Создание схемы (users, instructor_applications) + idempotent-миграция
    users.role (add-instructor-flow, задача 1.2, sdd.md §16): существующие
    базы Спринтов 0–1 поднимаются без пересоздания, записи остаются
    учениками (role='student')."""
    conn = get_conn()
    try:
        conn.executescript(_SCHEMA)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        if "role" not in columns:
            conn.execute(_USERS_ROLE_MIGRATION)
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
