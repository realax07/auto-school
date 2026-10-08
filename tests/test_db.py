"""Тесты слоя БД (задача 1.2, sdd.md §4).

БД создается во временном пути (AUTOSCHOOL_DB_PATH); схема users — все
колонки из sdd.md; SQL — только параметризованный (NFR-2).
"""
import os
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

import backend.db as db  # noqa: E402


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


def test_db_created_in_tmp_path(tmp_db):
    assert tmp_db.exists()


def test_users_table_has_all_schema_columns(tmp_db):
    conn = sqlite3.connect(str(tmp_db))
    rows = conn.execute("PRAGMA table_info(users)").fetchall()
    conn.close()
    columns = {name: ctype for (_, name, ctype, *_rest) in rows}
    assert columns == EXPECTED_COLUMNS


def test_email_unique(tmp_db):
    conn = db.get_conn()
    params = ("Иванов", "Иван", "Иванович", "a@b.ru", "+79001234567", "x" * 60)
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


def test_created_at_defaults_to_utc_now(tmp_db):
    conn = db.get_conn()
    conn.execute(
        "INSERT INTO users (surname, name, patronymic, email, phone, password_hash)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        ("Иванов", "Иван", "Иванович", "a@b.ru", "+79001234567", "x" * 60),
    )
    conn.commit()
    created_at = conn.execute("SELECT created_at FROM users").fetchone()[0]
    conn.close()
    # datetime('now') пишет UTC в формате YYYY-MM-DD HH:MM:SS
    import re

    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", created_at)
    from datetime import datetime, timezone

    parsed = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    delta = abs((datetime.now(timezone.utc) - parsed).total_seconds())
    assert delta < 60


def test_wal_mode(tmp_db):
    conn = db.get_conn()
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    conn.close()
    assert mode.lower() == "wal"


def test_row_factory_is_row(tmp_db):
    conn = db.get_conn()
    row = conn.execute("SELECT 1 AS one").fetchone()
    conn.close()
    assert isinstance(row, sqlite3.Row)


def test_init_db_idempotent(tmp_db):
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


def test_no_sql_concatenation_in_db_module():
    source = Path(db.__file__).read_text(encoding="utf-8")
    # NFR-2: SQL — литеральные строки с ?-плейсхолдерами;
    # f-строки с SQL и конкатенация SQL-запросов не допускаются
    import re

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

