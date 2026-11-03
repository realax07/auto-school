"""Минимальные самопроверки задач 3.1/4.1 (Спринт 9, add-personal-data-policy).

Трассировка (rule 6): TC-FR77-901…902, TC-FR78-901…904, TC-FR79-901…905 —
ПЛАНОВЫЕ ID до утверждения кейсов QA (прецедент: tests/test_instructors_apply.py
Спринта 1). Полная TC-матрица с финальными ID и кейсами в
test-model/new/add-personal-data-policy/ — задача 7.1 (волна 3); эти ID
плановые и могут быть перемаплены при утверждении кейсов.

НЕ полная матрица: здесь — проверка пунктов «Готовности» 3.1/4.1 из tasks.md:
- миграция 4 колонок idempotent, легаси-строки NULL, без seed/backfill;
- apply: фиксация consent_at (UTC сервера) + consent_policy_version
  (артефакт на момент сабмита), 422 без consent, 500 при недоступном
  артефакте (заявка НЕ создается), подмена версии (FR-79);
- register: 200 с фиксацией, 422 без consent/false, порядок проверок
  1 → 1a, 500 при недоступном артефакте (пользователь НЕ создается).
"""
import re
import sqlite3

import pytest

from conftest import (  # noqa: F401
    client,
    count_users,
    db_path,
    fetch_user,
    register,
)
from conftest import valid_body

_CONSENT_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

_OLD_SCHEMA = """
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
CREATE TABLE instructor_applications (
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

_APPLY_BODY = {
    "surname": "Иванов",
    "name": "Иван",
    "patronymic": "Иванович",
    "phone": "+7 (912) 345-67-89",
    "email": "instructor@example.com",
    "address": "Москва, Тверская 1, кв. 2",
    "work_format": "studio",
    "license_number": "1234 567890",
    "license_category": "B",
    "password": "Qwerty123",
    "password_confirm": "Qwerty123",
    "consent": True,
}


def _columns(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _artifact_version():
    from backend.policy import read_policy

    return read_policy()["version"]


# --- 3.1: миграция -----------------------------------------------------------


def test_s9_migration_adds_consent_columns_legacy_null(tmp_path, monkeypatch):
    """TC-FR79-901 (плановый): миграция — предсозданная БД со старыми
    строками: 4 колонки добавлены, легаси-строки остаются NULL (без
    seed/backfill)."""
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(tmp_path / "app.db"))
    conn = sqlite3.connect(tmp_path / "app.db")
    conn.executescript(_OLD_SCHEMA)
    conn.execute(
        "INSERT INTO users (surname, name, patronymic, email, phone,"
        " password_hash) VALUES ('Легаси', 'Юзер', 'О.', 'legacy@x.io',"
        " '+7 900 000-00-00', 'hash')"
    )
    conn.execute(
        "INSERT INTO instructor_applications (surname, name, patronymic,"
        " email, phone, address, work_format, license_number,"
        " license_category, password_hash)"
        " VALUES ('Легаси', 'Заявка', 'О.', 'legacy-apply@x.io',"
        " '+7 900 000-00-01', 'Адрес', 'studio', '99 001002', 'B', 'hash')"
    )
    conn.commit()
    assert "consent_at" not in _columns(conn, "users")
    conn.close()

    import backend.db as db

    db.init_db()
    conn = sqlite3.connect(tmp_path / "app.db")
    for table in ("users", "instructor_applications"):
        cols = _columns(conn, table)
        assert "consent_at" in cols, table
        assert "consent_policy_version" in cols, table
    for email in ("legacy@x.io", "legacy-apply@x.io"):
        table = "users" if email == "legacy@x.io" else "instructor_applications"
        row = conn.execute(
            f"SELECT consent_at, consent_policy_version FROM {table}"
            " WHERE email = ?",
            (email,),
        ).fetchone()
        assert row == (None, None), email
    conn.close()


def test_s9_migration_repeated_init_db_is_idempotent(tmp_path, monkeypatch):
    """TC-FR79-902 (плановый): повторный init_db ничего не меняет
    (легаси-значения на месте, схема не растет)."""
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(tmp_path / "app.db"))
    conn = sqlite3.connect(tmp_path / "app.db")
    conn.executescript(_OLD_SCHEMA)
    conn.execute(
        "INSERT INTO users (surname, name, patronymic, email, phone,"
        " password_hash) VALUES ('Легаси', 'Юзер', 'О.', 'legacy@x.io',"
        " '+7 900 000-00-00', 'hash')"
    )
    conn.commit()
    conn.close()

    import backend.db as db

    db.init_db()
    conn = sqlite3.connect(tmp_path / "app.db")
    before = conn.execute("SELECT * FROM users").fetchall()
    cols_before = _columns(conn, "users")
    conn.close()

    db.init_db()  # второй запуск — не должен упасть и что-то переписать
    conn = sqlite3.connect(tmp_path / "app.db")
    assert conn.execute("SELECT * FROM users").fetchall() == before
    assert _columns(conn, "users") == cols_before
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
    conn.close()


# --- 3.1: apply ---------------------------------------------------------------


def test_s9_apply_success_fixes_consent_at_and_policy_version(client):
    """TC-FR77-901 (плановый): валидный POST → заявка создана, оба поля
    непустые и равны метаданным артефакта (версия) / моменту сабмита
    (формат created_at)."""
    resp = client.post("/api/instructors/apply", json=_APPLY_BODY)
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"ok": True}

    conn = sqlite3.connect(db_path())
    row = conn.execute(
        "SELECT consent_at, consent_policy_version FROM"
        " instructor_applications WHERE email = ?",
        (_APPLY_BODY["email"],),
    ).fetchone()
    conn.close()
    assert row is not None
    consent_at, version = row
    assert consent_at and _CONSENT_AT_RE.match(consent_at)
    assert version == _artifact_version() == "1.0"


def test_s9_apply_without_consent_422_no_application(client):
    """TC-FR77-902 (плановый, регресс MIN-2): POST без consent → 422
    «Согласие: поле обязательно», заявки нет."""
    body = {k: v for k, v in _APPLY_BODY.items() if k != "consent"}
    resp = client.post("/api/instructors/apply", json=body)
    assert resp.status_code == 422
    assert resp.json() == {"ok": False, "error": "Согласие: поле обязательно"}
    conn = sqlite3.connect(db_path())
    count = conn.execute(
        "SELECT COUNT(*) FROM instructor_applications"
    ).fetchone()[0]
    conn.close()
    assert count == 0


def test_s9_apply_artifact_unavailable_500_no_application(
    client, tmp_path, monkeypatch
):
    """TC-FR79-903 (плановый): артефакт недоступен в момент сабмита →
    500 {ok:false}, заявка НЕ создается (FR-79)."""
    missing = tmp_path / "no-such-policy.md"
    monkeypatch.setenv("POLICY_FILE", str(missing))
    resp = client.post("/api/instructors/apply", json=_APPLY_BODY)
    assert resp.status_code == 500
    data = resp.json()
    assert data["ok"] is False
    assert data["error"] == (
        "Сервис: политика персональных данных временно недоступна"
    )
    conn = sqlite3.connect(db_path())
    count = conn.execute(
        "SELECT COUNT(*) FROM instructor_applications"
    ).fetchone()[0]
    conn.close()
    assert count == 0


def test_s9_policy_version_swap_new_application_records_new_version(
    client, tmp_path, monkeypatch
):
    """TC-FR79-904 (плановый, FR-79): подмена артефакта → новая заявка
    фиксирует новую версию, прежняя — свою."""
    resp = client.post("/api/instructors/apply", json=_APPLY_BODY)
    assert resp.status_code == 200

    artifact_v2 = tmp_path / "policy-v2.md"
    artifact_v2.write_text(
        "policy-version: 2.0\npolicy-date: 2026-12-01\n---\nНОВЫЙ ТЕКСТ\n\n"
        "Второй абзац.\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("POLICY_FILE", str(artifact_v2))
    body2 = dict(_APPLY_BODY, email="instructor2@example.com")
    resp2 = client.post("/api/instructors/apply", json=body2)
    assert resp2.status_code == 200, resp2.text

    conn = sqlite3.connect(db_path())
    versions = dict(
        conn.execute(
            "SELECT email, consent_policy_version FROM instructor_applications"
        ).fetchall()
    )
    conn.close()
    assert versions[_APPLY_BODY["email"]] == "1.0"
    assert versions[body2["email"]] == "2.0"


# --- 4.1: register ------------------------------------------------------------


def test_s9_register_success_fixes_consent_at_and_policy_version(client):
    """TC-FR78-901 (плановый): POST со всеми полями + consent:true → 200,
    в users consent_at и версия непустые и равны метаданным артефакта."""
    resp = register(client)
    assert resp.status_code == 200, resp.text
    row = fetch_user("petrova@example.com")
    assert row["consent_at"] and _CONSENT_AT_RE.match(row["consent_at"])
    assert row["consent_policy_version"] == _artifact_version() == "1.0"


@pytest.mark.parametrize("consent", [None, False])
def test_s9_register_consent_required_422_no_user(client, consent):
    """TC-FR78-902 (плановый): POST без consent и с consent:false → 422
    «Согласие: поле обязательно», пользователя нет."""
    overrides = {} if consent is None else {"consent": consent}
    body = valid_body(**overrides)
    if consent is None:
        body.pop("consent")
    resp = client.post("/api/register", json=body)
    assert resp.status_code == 422
    assert resp.json() == {"ok": False, "error": "Согласие: поле обязательно"}
    assert count_users() == 0


def test_s9_register_empty_surname_checked_before_consent(client):
    """TC-FR78-903 (плановый): порядок проверок 1 → 1a сохранен — пустая
    фамилия при consent:true → «Фамилия: поле обязательно»
    (не «Согласие: …»)."""
    resp = register(client, surname="", consent=True)
    assert resp.status_code == 422
    assert resp.json() == {"ok": False, "error": "Фамилия: поле обязательно"}
    assert count_users() == 0


def test_s9_register_duplicate_email_regression(client):
    """TC-FR78-904 (плановый, регресс): повторная регистрация email → 422
    «Email: уже зарегистрирован»."""
    assert register(client).status_code == 200
    dup = register(client)
    assert dup.status_code == 422
    assert dup.json() == {"ok": False, "error": "Email: уже зарегистрирован"}


def test_s9_register_artifact_unavailable_500_no_user(
    client, tmp_path, monkeypatch
):
    """TC-FR79-905 (плановый): артефакт недоступен → 500 {ok:false},
    пользователь НЕ создается."""
    monkeypatch.setenv("POLICY_FILE", str(tmp_path / "absent.md"))
    resp = register(client)
    assert resp.status_code == 500
    data = resp.json()
    assert data["ok"] is False
    assert data["error"] == (
        "Сервис: политика персональных данных временно недоступна"
    )
    assert count_users() == 0
