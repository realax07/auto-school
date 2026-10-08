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
"""


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


def init_db() -> None:
    """Создание схемы users (CREATE TABLE IF NOT EXISTS)."""
    conn = get_conn()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()
