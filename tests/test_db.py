"""TC-REG-001, TC-REG-012, TC-NFR-002 — слой БД (задача 1.2, sdd.md §4).
# Change: add-registration-admin

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
    "role": "TEXT",
    # Спринт 3 (add-instructor-student-loop, MAJ-3): стаж числом
    "experience_years": "INTEGER",
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
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN"
            " ('users', 'instructor_applications')"
        ).fetchall()
    ]
    conn.close()
    assert sorted(names) == ["instructor_applications", "users"]


# --- add-instructor-flow, задача 1.2 (sdd.md §16) ---


@pytest.fixture()
def legacy_db(tmp_path, monkeypatch):
    """Унаследованная база Спринтов 0–1: только users БЕЗ role,
    с существующей записью ученика."""
    path = tmp_path / "legacy.db"
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(path))
    conn = sqlite3.connect(str(path))
    conn.executescript(
        """
        CREATE TABLE users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          surname TEXT NOT NULL,
          name TEXT NOT NULL,
          patronymic TEXT NOT NULL,
          email TEXT NOT NULL UNIQUE,
          phone TEXT NOT NULL,
          password_hash TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        INSERT INTO users (surname, name, patronymic, email, phone, password_hash)
        VALUES ('Иванов', 'Иван', 'Иванович', 'legacy@example.com', '+79001234567', 'x' * 60);
        """
    )
    conn.commit()
    conn.close()
    yield path


APPLICATION_COLUMNS = {
    "id": "INTEGER",
    "surname": "TEXT",
    "name": "TEXT",
    "patronymic": "TEXT",
    "email": "TEXT",
    "phone": "TEXT",
    "address": "TEXT",
    "work_format": "TEXT",
    "plate": "TEXT",
    "license_number": "TEXT",
    "license_date": "TEXT",
    "license_category": "TEXT",
    "experience": "TEXT",
    "password_hash": "TEXT",
    "status": "TEXT",
    "review_comment": "TEXT",
    # Спринт 3 (add-instructor-student-loop): стаж числом (MAJ-3) и
    # сохраненный файл ВУ анкеты (FR-23, NULL = заявка без ВУ)
    "experience_years": "INTEGER",
    "license_photo_path": "TEXT",
    "created_at": "TEXT",
}


def _columns(path, table):
    conn = sqlite3.connect(str(path))
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    conn.close()
    return {name: ctype for (_, name, ctype, *_rest) in rows}


def test_s2_instructor_applications_table_schema(tmp_db):
    """1.2: instructor_applications — ровно колонки из design.md / sdd §16
    (email UNIQUE проверяется отдельным тестом)."""
    assert _columns(tmp_db, "instructor_applications") == APPLICATION_COLUMNS


def test_s2_users_role_column_added_on_empty_db(tmp_db):
    """1.2: init_db на пустой базе — users получает role TEXT NOT NULL
    DEFAULT 'student'; новая запись без role — student."""
    columns = _columns(tmp_db, "users")
    assert columns["role"] == "TEXT"
    conn = sqlite3.connect(str(tmp_db))
    conn.execute(
        "INSERT INTO users (surname, name, patronymic, email, phone, password_hash)"
        " VALUES ('А', 'Б', 'В', 'new@example.com', '+79001234567', 'x' * 60)"
    )
    conn.commit()
    role = conn.execute(
        "SELECT role FROM users WHERE email = 'new@example.com'"
    ).fetchone()[0]
    conn.close()
    assert role == "student"


def test_s2_users_role_migration_on_legacy_db(legacy_db):
    """1.2: init_db на унаследованной базе (Спринты 0–1, users без role)
    поднимается без пересоздания: колонка role добавлена, существующая
    запись остается учеником (role='student')."""
    db.init_db()
    columns = _columns(legacy_db, "users")
    assert columns["role"] == "TEXT"
    conn = sqlite3.connect(str(legacy_db))
    row = conn.execute(
        "SELECT surname, role FROM users WHERE email = 'legacy@example.com'"
    ).fetchone()
    conn.close()
    assert row == ("Иванов", "student")


def test_s2_role_migration_idempotent(tmp_db):
    """1.2: повторный init_db не падает и не плодит колонки role."""
    db.init_db()
    db.init_db()
    roles = [
        name
        for (_, name, *_rest) in sqlite3.connect(str(tmp_db))
        .execute("PRAGMA table_info(users)")
        .fetchall()
        if name == "role"
    ]
    assert roles == ["role"]


def test_s2_users_email_unique_preserved(tmp_db):
    """1.2: UNIQUE users.email сохранен после миграции (FR-16)."""
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


def test_s2_instructor_applications_email_unique(tmp_db):
    """1.2 (MAJ-1): UNIQUE instructor_applications.email — вторая линия
    защиты apply: второй INSERT того же email → sqlite3.IntegrityError."""
    conn = db.get_conn()
    row = (
        "Иванов",
        "Иван",
        "Иванович",
        "dup@example.com",
        "+79001234567",
        "Москва, Тверская 1",
        "own",
        "А123АА 777",
        "1234 567890",
        "2020-05-01",
        "B",
        "хэш",
    )
    conn.execute(
        "INSERT INTO instructor_applications (surname, name, patronymic, email,"
        " phone, address, work_format, plate, license_number, license_date,"
        " license_category, password_hash)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        row,
    )
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO instructor_applications (surname, name, patronymic, email,"
            " phone, address, work_format, plate, license_number, license_date,"
            " license_category, password_hash)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            row,
        )
    conn.close()


def test_s2_instructor_applications_defaults(tmp_db):
    """1.2: дефолты новой таблицы — status='waiting', review_comment='',
    created_at = UTC-момент (±60 с)."""
    conn = db.get_conn()
    conn.execute(
        "INSERT INTO instructor_applications (surname, name, patronymic, email,"
        " phone, address, work_format, plate, license_number, license_date,"
        " license_category, password_hash)"
        " VALUES ('А', 'Б', 'В', 'def@example.com', '+79001234567', 'Москва',"
        " 'sber', '', '1234 567890', '', 'B', 'хэш')"
    )
    conn.commit()
    row = conn.execute(
        "SELECT status, review_comment, created_at FROM instructor_applications"
        " WHERE email = 'def@example.com'"
    ).fetchone()
    conn.close()
    assert row["status"] == "waiting"
    assert row["review_comment"] == ""
    import re
    from datetime import datetime, timezone

    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", row["created_at"])
    parsed = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    delta = abs((datetime.now(timezone.utc) - parsed).total_seconds())
    assert delta < 60


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
