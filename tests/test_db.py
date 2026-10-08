"""TC-REG-001, TC-REG-012, TC-NFR-002 — слой БД (задача 1.2, sdd.md §4).

БД создается во временном пути (AUTOSCHOOL_DB_PATH); схема users — все
колонки из sdd.md; SQL — только параметризованный (NFR-2).
"""
import re
import sqlite3
from pathlib import Path

import pytest

import backend.db as db

EXPECTED_COLUMNS = {
    "id": "INTEGER",
    "surname": "TEXT",
    "name": "TEXT",
    "patronymic": "TEXT",
    "email": "TEXT",
    "phone": "TEXT",
    "password_hash": "TEXT",
    "created_at": "TEXT",
}


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    path = tmp_path / "app.db"
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(path))
    db.init_db()
    yield path


def test_tc_reg_001_db_created_in_tmp_path(tmp_db):
    """TC-REG-001 (инфраструктура): БД создается во временном пути
    (AUTOSCHOOL_DB_PATH) — тестовое окружение с чистой таблицей users,
    как требуют предусловия approved-кейсов."""
    assert tmp_db.exists()


def test_tc_reg_001_users_table_has_all_schema_columns(tmp_db):
    """TC-REG-001 (схема хранилища): таблица users содержит ровно колонки
    из sdd.md §4 — id, surname, name, patronymic, email, phone,
    password_hash, created_at (хранение всех 7 полей регистрации)."""
    conn = sqlite3.connect(str(tmp_db))
    rows = conn.execute("PRAGMA table_info(users)").fetchall()
    conn.close()
    columns = {name: ctype for (_, name, ctype, *_rest) in rows}
    assert columns == EXPECTED_COLUMNS


def test_tc_reg_012_email_unique_at_db_level(tmp_db):
    """TC-REG-012 (вторая линия защиты): уникальность email на уровне БД
    (UNIQUE в схеме, sdd §4) — повторный INSERT того же email →
    sqlite3.IntegrityError, даже если SELECT-проверка в хендлере
    пропустит."""
    conn = db.get_conn()
    params = ("Иванов", "Иван", "Иванович", "a@b.ru", "+790****4567", "x" * 60)
    conn.execute(
        "INSERT INTO users (surname, name, patronymic, email, phone, password_hash)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        params,
    )
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO users (surname, name, patronymic, email, phone, password_hash)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            params,
        )
    conn.close()


def test_tc_reg_001_created_at_defaults_to_utc_now(tmp_db):
    """TC-REG-001 (created_at): DEFAULT (datetime('now')) пишет UTC в
    формате YYYY-MM-DD HH:MM:SS, значение — текущий момент (±60 с);
    основа для MIN-4 (UTC→локаль в CSV)."""
    conn = db.get_conn()
    conn.execute(
        "INSERT INTO users (surname, name, patronymic, email, phone, password_hash)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        ("Иванов", "Иван", "Иванович", "a@b.ru", "+790****4567", "x" * 60),
    )
    conn.commit()
    created_at = conn.execute("SELECT created_at FROM users").fetchone()[0]
    conn.close()

    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", created_at)
    from datetime import datetime, timezone

    parsed = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    delta = abs((datetime.now(timezone.utc) - parsed).total_seconds())
    assert delta < 60


def test_tc_reg_001_wal_mode(tmp_db):
    """TC-REG-001 (инфраструктура): SQLite работает в режиме WAL (sdd §4:
    файл data/app.db, режим WAL)."""
    conn = db.get_conn()
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    conn.close()
    assert mode.lower() == "wal"


def test_tc_reg_001_row_factory_is_row(tmp_db):
    """TC-REG-001 (инфраструктура): row_factory=Row — доступ к колонкам
    записи по именам (используется хендлерами и CSV-экспортом)."""
    conn = db.get_conn()
    row = conn.execute("SELECT 1 AS one").fetchone()
    conn.close()
    assert isinstance(row, sqlite3.Row)


def test_tc_reg_001_init_db_idempotent(tmp_db):
    """TC-REG-001 (инфраструктура): init_db идемпотентен (CREATE TABLE IF
    NOT EXISTS) — повторный вызов не падает и не плодит таблиц."""
    db.init_db()  # повторный вызов не должен падать
    conn = sqlite3.connect(str(tmp_db))
    names = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchall()
    ]
    conn.close()
    assert names == ["users"]


def test_tc_nfr_002_no_sql_concatenation_in_db_module():
    """TC-NFR-002 (статическая часть, db-слой): каждый SQL — литеральная
    строка с «?»-плейсхолдерами; f-строки с SQL и конкатенация
    SQL-запросов не допускаются (NFR-2, sdd §4)."""
    source = Path(db.__file__).read_text(encoding="utf-8")
    fstrings = re.findall(r'f"[^"]*"|f\'[^\']*\'', source)
    sql_fstrings = [
        s
        for s in fstrings
        if any(
            w in s.upper()
            for w in ("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE")
        )
    ]
    assert sql_fstrings == []
