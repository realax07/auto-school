"""Матрица Спринта 9 add-personal-data-policy (задача 7.1, волна 3).

Трассировка (rule 6, flow_check): каждый тест — TC-PD-NNN в docstring,
кейсы партии — test-model/new/add-personal-data-policy/TC-PD-NNN.md
(формат партии add-s8-cars-docs-booking). Плановые ID волны 2
(TC-FR77-901…, TC-FR78-901…, TC-FR79-901…) перемаплены на финальные
TC-PD-001…017 с трассировкой ПО ТОЧНЫМ ЗАГОЛОВКАМ
openspec/changes/add-personal-data-policy/specs/PersonalData/spec.md
(названия Requirement/Scenario менять нельзя):

  Req «Публичная страница политики персональных данных (/policy)»:
    TC-PD-001 ← «Страница открывается без входа и показывает текст и версию»
    TC-PD-002 ← «Подмена артефакта меняет текст и версию без правки кода»
                (+ Req «Заменяемость артефакта политики» ← «Подмена одного
                   файла — без пересборки и правки кода»)
    TC-PD-003 ← «Артефакт поврежден — честная ошибка страницы»
    TC-PD-004 ← «Текст политики отсутствует в исходниках страниц»
    TC-PD-005 ← «Ссылка на политику видна из обоих мест согласия»
    TC-PD-006 ← «Политика охватывает данные существующих форм»
  Req «Обязательное согласие при регистрации инструктора»:
    TC-PD-007 ← «Прямой POST без согласия отклоняется сервером»
    TC-PD-008 ← «Согласие установлено — заявка создана»
                (+ Req «Фиксация…» ← «Заявка инструктора содержит дату
                   и версию политики»)
  Req «Обязательное согласие при регистрации ученика»:
    TC-PD-011 ← «Прямой POST /api/register без согласия отклоняется
                 сервером» (в т.ч. порядок 1 → 1a — TC-PD-013)
    TC-PD-012 ← «Согласие установлено — пользователь создан»
                (+ Req «Фиксация…» ← «Запись ученика содержит дату
                   и версию политики»)
  Req «Фиксация согласия в данных заявки и регистрации»:
    TC-PD-009/014 ← «Новая версия политики — новые записи фиксируют ее,
                     прежние сохраняют свою» (apply/register)
                (+ Req «Заменяемость…» ← «Версия для фиксации берется из
                   артефакта на момент сабмита»)
    TC-PD-016/017 ← «Записи до введения фиксации не переписываются»
  Req «Заменяемость артефакта политики»:
    TC-PD-010/015 ← «Поврежденный артефакт — записи не создаются»
  Клиентские сценарии (чекбокс/кнопка disabled/рендер /policy/ссылки) —
  e2e TC-UI-002/043/044/045 в tests/test_ui_playwright.py (задача 7.2).

Клиент (гость, без авторизации) + чистая БД в tmp_path — фикстуры
tests/conftest.py; артефакт по умолчанию deploy/policy/policy.md,
подмена — через POLICY_FILE (env, читается НА КАЖДЫЙ запрос).
"""
import re
import sqlite3
from pathlib import Path

import pytest

from conftest import (  # noqa: F401
    client,
    count_users,
    db_path,
    fetch_user,
    frontend_source,
    register,
)
from conftest import valid_body

ROOT = Path(__file__).resolve().parent.parent

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

# Битые артефакты для матрицы «Поврежденный артефакт» (формат design.md):
# имя варианта → содержимое (или None — файл не создается вовсе).
_BROKEN_ARTIFACTS = {
    "отсутствует": None,
    "нет-разделителя": (
        "policy-version: 1.0\npolicy-date: 2026-11-10\nТекст без шапки.\n"
    ),
    "пустой-текст": "policy-version: 1.0\npolicy-date: 2026-11-10\n---\n\n",
    "нет-версии": "policy-date: 2026-11-10\n---\nКакой-то текст.\n",
    "битая-дата": "policy-version: 1.0\npolicy-date: ноябрь\n---\nТекст.\n",
    "строка-без-ключа": "policy-version: 1.0\nслучайная строка\n---\nТ.\n",
}

_POLICY_UNAVAILABLE = {"ok": False, "error": "Политика: временно недоступна"}
_RECORD_UNAVAILABLE = (
    "Сервис: политика персональных данных временно недоступна"
)


def _columns(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _artifact_version():
    from backend.policy import read_policy

    return read_policy()["version"]


def _apply_count():
    conn = sqlite3.connect(db_path())
    n = conn.execute(
        "SELECT COUNT(*) FROM instructor_applications"
    ).fetchone()[0]
    conn.close()
    return n


# === Req «Публичная страница политики персональных данных (/policy)» =====


def test_s9_policy_api_and_page_guest(client):
    """TC-PD-001: GET /api/policy отдает текст+метаданные из артефакта;
    страница /policy открыта гостю (без входа) и является оболочкой БЕЗ
    текста политики.

    Трассировка: Requirement «Публичная страница политики персональных
    данных (/policy)» / Scenario «Страница открывается без входа и
    показывает текст и версию» (API-часть + исходник страницы; полный
    рендер — e2e TC-UI-044, задача 7.2).
    """
    from backend.policy import read_policy

    artifact = read_policy()  # дефолтный deploy/policy/policy.md

    resp = client.get("/api/policy")  # клиент-фикстура — гость, без сессии
    assert resp.status_code == 200, resp.text
    assert resp.json() == {
        "ok": True,
        "version": artifact["version"],
        "date": artifact["date"],
        "text": artifact["text"],
    }

    page = client.get("/policy")
    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]
    assert 'id="policy-meta"' in page.text
    assert 'id="policy-text"' in page.text
    assert '/js/policy.js' in page.text
    # в исходнике страницы текста политики нет (он приходит из API)
    assert artifact["version"] not in page.text
    assert artifact["text"][:60] not in page.text


def test_s9_policy_artifact_swap_new_version_without_code_change(
    client, tmp_path, monkeypatch
):
    """TC-PD-002: подмена артефакта (временный файл с новым version/text)
    → /api/policy и /policy отдают НОВЫЕ версию и текст БЕЗ правки кода
    (правится только файл); страница остается оболочкой без текста.

    Трассировка: Requirement «Публичная страница политики персональных
    данных (/policy)» / Scenario «Подмена артефакта меняет текст и версию
    без правки кода»; Requirement «Заменяемость артефакта политики» /
    Scenario «Подмена одного файла — без пересборки и правки кода»
    (файловая часть — до/после без правки исходников).
    """
    before = client.get("/api/policy").json()
    assert before["version"] == "1.0"

    artifact_v2 = tmp_path / "policy-v2.md"
    new_text = (
        "ПОЛИТИКА ПЕРСОНАЛЬНЫХ ДАННЫХ (РЕДАКЦИЯ 2.0)\n\n"
        "Новый текст политики для проверки подмены артефакта.\n"
    )
    artifact_v2.write_text(
        "policy-version: 2.0\npolicy-date: 2026-12-01\n---\n" + new_text,
        encoding="utf-8",
    )
    monkeypatch.setenv("POLICY_FILE", str(artifact_v2))

    resp = client.get("/api/policy")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {
        "ok": True,
        "version": "2.0",
        "date": "2026-12-01",
        "text": new_text.strip(),
    }

    page = client.get("/policy")
    assert page.status_code == 200
    assert "РЕДАКЦИЯ 2.0" not in page.text  # текст по-прежнему не в HTML


@pytest.mark.parametrize("variant", sorted(_BROKEN_ARTIFACTS))
def test_s9_policy_broken_or_missing_artifact_500_no_leak(
    client, tmp_path, monkeypatch, variant
):
    """TC-PD-003: отсутствующий/битый артефакт (нет разделителя, пустой
    текст, нет обязательного ключа, битая дата, строка шапки без ключа)
    → 500 {ok:false, error:"Политика: временно недоступна"}; содержимое
    артефакта в ответе НЕ раскрывается; сервис не падает.

    Трассировка: Requirement «Публичная страница политики персональных
    данных (/policy)» / Scenario «Артефакт поврежден — честная ошибка
    страницы» (API-часть; честное сообщение UI — e2e TC-UI-044).
    """
    content = _BROKEN_ARTIFACTS[variant]
    path = tmp_path / f"broken-{variant}.md"
    if content is None:
        path = tmp_path / "no-such-policy.md"  # файл не создан
    else:
        path.write_text(content, encoding="utf-8")
    monkeypatch.setenv("POLICY_FILE", str(path))

    resp = client.get("/api/policy")
    assert resp.status_code == 500, (variant, resp.text)
    assert resp.json() == _POLICY_UNAVAILABLE
    # содержимое битого артефакта не раскрывается (NFR-10)
    if content:
        assert "Какой-то текст" not in resp.text
        assert "случайная строка" not in resp.text


def test_s9_policy_text_absent_from_frontend_sources():
    """TC-PD-004: grep по исходникам страниц (frontend/**.html, **.js —
    включая все подключаемые ES-модули; собранных бандлов нет) не находит
    НИ ОДНОЙ строки текста политики — текст поступает только из артефакта
    через API.

    Трассировка: Requirement «Публичная страница политики персональных
    данных (/policy)» / Scenario «Текст политики отсутствует в исходниках
    страниц».
    """
    from backend.policy import read_policy

    text = read_policy()["text"]
    needles = ["152-ФЗ", "privacy@sberavtoshkola.example"]
    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if len(paragraph) >= 60:
            needles.append(paragraph[20:60])  # фрагмент середины абзаца

    sources = []
    for path in sorted((ROOT / "frontend").rglob("*")):
        if path.suffix in (".html", ".js"):
            sources.append((path, path.read_text(encoding="utf-8")))
    assert sources, "frontend-исходники не найдены"

    for path, source in sources:
        for needle in needles:
            assert needle not in source, (path.name, needle)


def test_s9_policy_link_visible_in_both_consent_blocks():
    """TC-PD-005: ссылка на /policy видна из ОБОИХ мест согласия — блок
    согласия анкеты инструктора (checkline) и модалка регистрации ученика
    (reg-check перед кнопками); target="_blank"; из анкеты отправляется
    consent в multipart, из модалки — consent в payload при активном
    чекбоксе (wiring по объединенному источнику HTML + ES-модулей).

    Трассировка: Requirement «Публичная страница политики персональных
    данных (/policy)» / Scenario «Ссылка на политику видна из обоих мест
    согласия» (клики и видимость — e2e TC-UI-043/045).
    """
    instructor = frontend_source("instructor-apply.html")
    assert 'href="/policy" target="_blank"' in instructor
    assert ".checkline" in instructor  # блок согласия анкеты
    assert "fd.append('consent'" in instructor  # apply.js

    student = frontend_source("index.html")  # включает js/landing.js
    assert 'id="reg-consent"' in student
    assert 'href="/policy" target="_blank"' in student
    assert "regSubmit.disabled=!regConsent.checked" in student
    assert "consent:regConsent.checked" in student


def test_s9_policy_artifact_covers_existing_form_data():
    """TC-PD-006: политика описывает данные, собираемые СУЩЕСТВУЮЩИМИ
    формами сервиса: ФИО, телефон, email, адрес, реквизиты ВУ (номер/
    категория/дата выдачи), фото ВУ, госномер, фото СТС, фото авто;
    структура шаблона (оператор, цели, основания, перечень, сроки, права
    субъекта, контакты) присутствует.

    Трассировка: Requirement «Публичная страница политики персональных
    данных (/policy)» / Scenario «Политика охватывает данные существующих
    форм».
    """
    from backend.policy import read_policy

    text = read_policy()["text"].lower()
    for needle in (
        "фамилия",
        "номер телефона",
        "адрес электронной почты",
        "адрес фактического проживания",
        "водительского удостоверения",
        "категория, дата выдачи",
        "государственный регистрационный номер",
        "свидетельства о регистрации транспортного средства",
        "фотография автомобиля",
        "оператор персональных данных",
        "цели обработки",
        "правовые основания",
        "сроки обработки",
        "права субъекта",
        "контакты",
    ):
        assert needle in text, needle


# === Req «Обязательное согласие при регистрации инструктора» =============


def test_s9_apply_without_consent_422_no_application(client):
    """TC-PD-007: прямой POST /api/instructors/apply без согласия
    (consent не true) → 422 {ok:false, error:"Согласие: поле обязательно"};
    заявка не создана (регресс MIN-2, позиция 1a).

    Трассировка: Requirement «Обязательное согласие при регистрации
    инструктора» / Scenario «Прямой POST без согласия отклоняется
    сервером».
    """
    body = {k: v for k, v in _APPLY_BODY.items() if k != "consent"}
    resp = client.post("/api/instructors/apply", json=body)
    assert resp.status_code == 422
    assert resp.json() == {"ok": False, "error": "Согласие: поле обязательно"}
    assert _apply_count() == 0


def test_s9_apply_success_fixes_consent_at_and_policy_version(client):
    """TC-PD-008: чекбокс установлен, анкета валидна → заявка создана
    (status waiting) с фиксацией: consent_at — момент сабмита (UTC сервера,
    формат created_at 'YYYY-MM-DD HH:MM:SS'), consent_policy_version —
    версия артефакта «1.0».

    Трассировка: Requirement «Обязательное согласие при регистрации
    инструктора» / Scenario «Согласие установлено — заявка создана»;
    Requirement «Фиксация согласия в данных заявки и регистрации» /
    Scenario «Заявка инструктора содержит дату и версию политики».
    """
    resp = client.post("/api/instructors/apply", json=_APPLY_BODY)
    assert resp.status_code == 200, resp.text
    # Спринт 9 (merge с add-application-status-polling): ответ РАСШИРЕН
    # токенами заявки (обратно-совместимо, NFR-27) — проверяем надмножество.
    body = resp.json()
    assert body["ok"] is True
    assert body["poll_token"] and body["exchange_token"]

    conn = sqlite3.connect(db_path())
    row = conn.execute(
        "SELECT status, consent_at, consent_policy_version FROM"
        " instructor_applications WHERE email = ?",
        (_APPLY_BODY["email"],),
    ).fetchone()
    conn.close()
    assert row is not None
    status, consent_at, version = row
    assert status == "waiting"
    assert consent_at and _CONSENT_AT_RE.match(consent_at)
    assert version == _artifact_version() == "1.0"


def test_s9_apply_version_swap_new_application_records_new_version(
    client, tmp_path, monkeypatch
):
    """TC-PD-009: подмена артефакта (1.0 → 2.0) → новая заявка фиксирует
    «2.0», прежняя сохраняет «1.0» (не переписывается); версия прочитана
    СЕРВЕРОМ из метаданных артефакта на момент сабмита (клиент версию
    не присылает).

    Трассировка: Requirement «Фиксация согласия в данных заявки и
    регистрации» / Scenario «Новая версия политики — новые записи
    фиксируют ее, прежние сохраняют свою»; Requirement «Заменяемость
    артефакта политики» / Scenario «Версия для фиксации берется из
    артефакта на момент сабмита».
    """
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


def test_s9_apply_broken_artifact_500_no_application(
    client, tmp_path, monkeypatch
):
    """TC-PD-010: артефакт отсутствует/поврежден в момент сабмита →
    500 {ok:false, error:"Сервис: политика персональных данных временно
    недоступна"}; заявка НЕ создана (фиксация версии невозможна — сервис
    не создает запись без согласия на конкретную версию).

    Трассировка: Requirement «Заменяемость артефакта политики» /
    Scenario «Поврежденный артефакт — записи не создаются».
    """
    missing = tmp_path / "no-such-policy.md"
    monkeypatch.setenv("POLICY_FILE", str(missing))
    resp = client.post("/api/instructors/apply", json=_APPLY_BODY)
    assert resp.status_code == 500
    data = resp.json()
    assert data["ok"] is False
    assert data["error"] == _RECORD_UNAVAILABLE
    assert _apply_count() == 0


# === Req «Обязательное согласие при регистрации ученика» =================


@pytest.mark.parametrize("consent", [None, False])
def test_s9_register_consent_required_422_no_user(client, consent):
    """TC-PD-011: прямой POST /api/register без consent и с consent:false
    → 422 {ok:false, error:"Согласие: поле обязательно"}; пользователь
    не создан.

    Трассировка: Requirement «Обязательное согласие при регистрации
    ученика» / Scenario «Прямой POST /api/register без согласия
    отклоняется сервером».
    """
    overrides = {} if consent is None else {"consent": consent}
    body = valid_body(**overrides)
    if consent is None:
        body.pop("consent")
    resp = client.post("/api/register", json=body)
    assert resp.status_code == 422
    assert resp.json() == {"ok": False, "error": "Согласие: поле обязательно"}
    assert count_users() == 0


def test_s9_register_success_fixes_consent_at_and_policy_version(client):
    """TC-PD-012: чекбокс установлен, форма валидна → пользователь создан
    (роль student) с фиксацией: consent_at (UTC сервера, момент сабмита) и
    версия артефакта «1.0»; ответ содержит сессию как прежде
    ({ok:true, token}).

    Трассировка: Requirement «Обязательное согласие при регистрации
    ученика» / Scenario «Согласие установлено — пользователь создан»;
    Requirement «Фиксация согласия в данных заявки и регистрации» /
    Scenario «Запись ученика содержит дату и версию политики».
    """
    resp = register(client)
    assert resp.status_code == 200, resp.text
    assert resp.json()["ok"] is True and resp.json()["token"]

    row = fetch_user("petrova@example.com")
    assert row["role"] == "student"
    assert row["consent_at"] and _CONSENT_AT_RE.match(row["consent_at"])
    assert row["consent_policy_version"] == _artifact_version() == "1.0"


def test_s9_register_empty_surname_checked_before_consent(client):
    """TC-PD-013: порядок проверок 1 → 1a сохранен — пустая фамилия при
    consent:true → «Фамилия: поле обязательно» (НЕ «Согласие: …»):
    согласие проверяется после обязательных полей (MIN-2).

    Трассировка: Requirement «Обязательное согласие при регистрации
    ученика» / Scenario «Прямой POST /api/register без согласия
    отклоняется сервером» (порядок проверок 1 → 1a — design.md,
    наследование MIN-2).
    """
    resp = register(client, surname="", consent=True)
    assert resp.status_code == 422
    assert resp.json() == {"ok": False, "error": "Фамилия: поле обязательно"}
    assert count_users() == 0


def test_s9_register_version_swap_new_user_records_new_version(
    client, tmp_path, monkeypatch
):
    """TC-PD-014: подмена артефакта (1.0 → 2.0) → новый пользователь
    фиксирует «2.0», прежний сохраняет «1.0» (включая свой consent_at —
    сохраненные значения не переписываются).

    Трассировка: Requirement «Фиксация согласия в данных заявки и
    регистрации» / Scenario «Новая версия политики — новые записи
    фиксируют ее, прежние сохраняют свою»; Requirement «Заменяемость
    артефакта политики» / Scenario «Версия для фиксации берется из
    артефакта на момент сабмита».
    """
    assert register(client).status_code == 200
    conn = sqlite3.connect(db_path())
    first_before = conn.execute(
        "SELECT consent_at, consent_policy_version FROM users"
        " WHERE email = 'petrova@example.com'"
    ).fetchone()
    conn.close()
    assert first_before[1] == "1.0"

    artifact_v2 = tmp_path / "policy-v2.md"
    artifact_v2.write_text(
        "policy-version: 2.0\npolicy-date: 2026-12-01\n---\nНОВЫЙ ТЕКСТ\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("POLICY_FILE", str(artifact_v2))
    resp = register(client, email="second@example.com")
    assert resp.status_code == 200, resp.text

    conn = sqlite3.connect(db_path())
    first_after = conn.execute(
        "SELECT consent_at, consent_policy_version FROM users"
        " WHERE email = 'petrova@example.com'"
    ).fetchone()
    second = conn.execute(
        "SELECT consent_at, consent_policy_version FROM users"
        " WHERE email = 'second@example.com'"
    ).fetchone()
    conn.close()
    assert first_after == first_before  # прежняя запись не переписана
    assert second[1] == "2.0"
    assert second[0] and _CONSENT_AT_RE.match(second[0])


def test_s9_register_broken_artifact_500_no_user(
    client, tmp_path, monkeypatch
):
    """TC-PD-015: артефакт отсутствует/поврежден в момент сабмита →
    500 {ok:false, error:"Сервис: политика персональных данных временно
    недоступна"}; пользователь НЕ создан.

    Трассировка: Requirement «Заменяемость артефакта политики» /
    Scenario «Поврежденный артефакт — записи не создаются».
    """
    monkeypatch.setenv("POLICY_FILE", str(tmp_path / "absent.md"))
    resp = register(client)
    assert resp.status_code == 500
    data = resp.json()
    assert data["ok"] is False
    assert data["error"] == _RECORD_UNAVAILABLE
    assert count_users() == 0


# === Req «Фиксация согласия…»: легаси-записи и idempotent-миграция =======


def test_s9_migration_adds_consent_columns_legacy_null(tmp_path, monkeypatch):
    """TC-PD-016: миграция — предсозданная БД со старыми строками: 4
    колонки (users/instructor_applications × consent_at/
    consent_policy_version) добавлены; легаси-записи остаются с NULL
    фиксации (без seed/backfill); новые записи получают обе колонки
    непустыми (см. TC-PD-008/012).

    Трассировка: Requirement «Фиксация согласия в данных заявки и
    регистрации» / Scenario «Записи до введения фиксации не
    переписываются».
    """
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
    """TC-PD-017: миграция выполняется повторно (idempotent) — повторный
    init_db ничего не меняет (легаси-значения NULL на месте, схема
    не растет).

    Трассировка: Requirement «Фиксация согласия в данных заявки и
    регистрации» / Scenario «Записи до введения фиксации не
    переписываются» (GIVEN «в том числе повторно — idempotent»).
    """
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


def test_s9_register_duplicate_email_regression(client):
    """TC-REG-012/013 (регресс Спринта 1, tests/test_register.py):
    повторная регистрация email → 422 «Email: уже зарегистрирован» —
    контракт register не сломан добавлением consent (4.1).

    Трассировка: наследуемый контракт (change add-registration-admin,
    TC-REG-012/013); Спринт 9 — регресс-гард в матрице согласия.
    """
    assert register(client).status_code == 200
    dup = register(client)
    assert dup.status_code == 422
    assert dup.json() == {"ok": False, "error": "Email: уже зарегистрирован"}
