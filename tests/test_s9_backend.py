"""Спринт 9 — BACKEND-тесты (change add-application-status-polling; задача
5.1, волна P-1; снятие skipif и финальный живой прогон — волна P-2,
задачи 2.1/6.1). Пишутся ПРОТИВ контрактов design.md пакета (таблицы
эндпоинтов, «Решение СА», «Модель данных»).

Покрывают (TC-S9BE-001…007, tasks.md 5.1):
- TC-S9BE-001 — apply выдает ОБА токена, сохраняет в заявку, токены двух
  заявок не совпадают, длина/энтропия secrets.token_urlsafe(32)
  (неперебираемость NFR-28); 422 apply токенов НЕ выдает; MIN-2 (оба
  исхода IntegrityError, ветки разведены по сообщению/имени индекса —
  классификация сверена с РЕАЛЬНЫМИ сообщениями SQLite): гонка дубля
  email → 422 (заявка одна, цикла регенерации нет), коллизия токена →
  регенерация, заявка создана БЕЗ 422;
- TC-S9BE-002 — статус waiting по X-Poll-Token, чтение без побочных
  эффектов (заявка неизменна после N чтений);
- TC-S9BE-003 — approved в статусе + бесшовный обмен на рабочую сессию
  по строке users (роль instructor — БД-проверка, контракт /api/auth/me
  без ключа role, sdd.md §20.1); переходный отказ обмена (409,
  вырожденное «approved без users») — токен НЕ потреблен, повтор
  возможен;
- TC-S9BE-004 — rejected с причиной и без (историческая пустая причина →
  нейтральный текст на экране);
- TC-S9BE-005 — 404-неразличение чужой/несуществующий poll_token и
  exchange_token (тела ответов идентичны), 422 на пустые заголовок/токен;
- TC-S9BE-006 — миграция idempotent на legacy-БД (колонки есть, старые
  строки NULL — backfill НЕТ, повторный запуск ничего не меняет;
  частичные UNIQUE-индексы реально уникальны);
- TC-S9BE-007 — потребление exchange_token: повторный обмен → 404
  (триггер терминального состояния экрана, MAJ-1), статус остается
  approved; обмен при waiting → 409 (токен сохранен); MIN-1 — два
  ПАРАЛЛЕЛЬНЫХ обмена одним валидным токеном: ровно один 200, второй 404.

Трассировка TC → спека (rule 6, контракт 4): в docstring каждого теста —
точные заголовки «### Requirement:/#### Scenario:» дельты
openspec/changes/add-application-status-polling/specs/StudentFlow/spec.md.
time.sleep запрещен (спека qa-pipeline); синхронизация параллельного
обмена — threading.Barrier. Фикстуры — общий client из conftest.
"""
import re
import secrets
import sqlite3
import threading

import pytest

from conftest import admin_headers, db_path, fetch_user

import backend.instructors as instructors

# Точный заголовок Requirement дельты (трассировка rule 6)
REQ_TITLE = "Автоопределение статуса заявки на экране ожидания"

_STATUS_PATH = "/api/instructors/application-status"
_EXCHANGE_PATH = "/api/instructors/application-exchange"

PASSWORD = "Instr1234"


# --- helpers -----------------------------------------------------------------


def valid_application(**overrides):
    """Базовый валидный набор анкеты (контракт apply, sdd §15.1)."""
    body = {
        "surname": "Иванов",
        "name": "Иван",
        "patronymic": "Иванович",
        "phone": "+7 (912) 345-67-89",
        "email": "instructor@example.com",
        "address": "Москва, Тверская 1, кв. 2",
        "work_format": "any",
        "plate": "",
        "license_number": "1234 567890",
        "license_date": "2020-05-01",
        "license_category": "B",
        "experience": "5–9 лет",
        "password": PASSWORD,
        "password_confirm": PASSWORD,
        "consent": True,
    }
    body.update(overrides)
    return body


def apply_post(client, **overrides):
    return client.post("/api/instructors/apply", json=valid_application(**overrides))


def apply_tokens(client, **overrides):
    """apply 200 → (poll_token, exchange_token)."""
    resp = apply_post(client, **overrides)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    return body["poll_token"], body["exchange_token"]


def fetch_application(email):
    """Полная строка заявки по email (тот же файл БД, что использует app)."""
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM instructor_applications WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return row


def application_id(email):
    row = fetch_application(email)
    assert row is not None
    return row["id"]


def approve(client, email):
    """Модерация: approve заявки (контур Спринта 2, без изменений)."""
    resp = client.post(
        f"/api/admin/instructor-applications/{application_id(email)}/approve",
        headers=admin_headers(client),
    )
    assert resp.status_code == 200, resp.text


def deny(client, email, comment):
    resp = client.post(
        f"/api/admin/instructor-applications/{application_id(email)}/deny",
        json={"comment": comment},
        headers=admin_headers(client),
    )
    assert resp.status_code == 200, resp.text


def force_status(email, status, review_comment=None):
    """Прямой UPDATE статуса (вырожденные/исторические состояния вне
    контракта модерации — design.md «Обработка ошибок»)."""
    conn = sqlite3.connect(db_path())
    if review_comment is None:
        conn.execute(
            "UPDATE instructor_applications SET status = ? WHERE email = ?",
            (status, email),
        )
    else:
        conn.execute(
            "UPDATE instructor_applications SET status = ?, review_comment = ?"
            " WHERE email = ?",
            (status, review_comment, email),
        )
    conn.commit()
    conn.close()


def insert_raw_application(conn, email, poll_token=None, exchange_token=None):
    """Сырая строка заявки (для веток IntegrityError и legacy-кейсов)."""
    conn.execute(
        "INSERT INTO instructor_applications (surname, name, patronymic,"
        " email, phone, address, work_format, license_number,"
        " license_category, password_hash, poll_token, exchange_token)"
        " VALUES ('А', 'Б', 'В', ?, '+7 900 000-00-00', 'адрес', 'any',"
        " '123', 'B', 'hash', ?, ?)",
        (email, poll_token, exchange_token),
    )


def insert_legacy_application(conn, email):
    """Сырая строка заявки в LEGACY-таблицу (до миграции — без колонок
    токенов; состав колонок как в Спринтах 2–8)."""
    conn.execute(
        "INSERT INTO instructor_applications (surname, name, patronymic,"
        " email, phone, address, work_format, license_number,"
        " license_category, password_hash)"
        " VALUES ('А', 'Б', 'В', ?, '+7 900 000-00-00', 'адрес', 'any',"
        " '123', 'B', 'hash')",
        (email,),
    )


# --- TC-S9BE-001: apply выдает токены (задача 1.1, выполняется в P-1) -------


class TestTCS9BE001ApplyIssuesTokens:
    """TC-S9BE-001 (задача 5.1; FR-80, NFR-27, NFR-28, MIN-2).

    Requirement: Автоопределение статуса заявки на экране ожидания
    Scenario: Экран опрашивает статус по неперебираемому идентификатору
    (apply 200 с poll_token/exchange_token — источник идентификатора;
    неперебираемость; MIN-2 — оба исхода IntegrityError разведены).
    """

    def test_apply_200_contains_both_tokens_and_saves_them(self, client):
        poll, exchange = apply_tokens(client)
        # неперебираемость: token_urlsafe(32) → 43 символа base64url
        # (256 бит энтропии — NFR-28); перебор невозможен
        for token in (poll, exchange):
            assert isinstance(token, str) and len(token) == 43
            assert re.fullmatch(r"[A-Za-z0-9_-]{43}", token)
        assert poll != exchange
        # оба токена сохранены в заявке той же транзакцией
        row = fetch_application("instructor@example.com")
        assert row["poll_token"] == poll
        assert row["exchange_token"] == exchange
        # обратно-совместимость (NFR-27): заявка waiting, старый контракт
        # apply не сломан
        assert row["status"] == "waiting"
        assert row["review_comment"] == ""

    def test_tokens_of_two_applications_differ(self, client):
        poll_a, exchange_a = apply_tokens(client)
        poll_b, exchange_b = apply_tokens(client, email="second@example.com")
        assert {poll_a, exchange_a}.isdisjoint({poll_b, exchange_b})
        # и внутри пары каждого заявителя токены различны
        assert poll_a != exchange_a and poll_b != exchange_b

    def test_apply_422_issues_no_tokens_and_creates_nothing(self, client):
        resp = apply_post(client, surname="")  # первое обязательное поле пусто
        assert resp.status_code == 422
        body = resp.json()
        assert body["ok"] is False
        # токены НЕ выдаются (design.md: при 422 заявка не создается)
        assert "poll_token" not in body
        assert "exchange_token" not in body
        assert fetch_application("instructor@example.com") is None

    def test_email_race_contract_422_single_application_no_regen_loop(self, client):
        """MIN-2, ветка email: дубль email → контрактная 422, заявка одна,
        цикла регенерации нет (IntegrityError-линия — тот же исход)."""
        first = apply_post(client)
        assert first.status_code == 200
        second = apply_post(client)  # тот же email
        assert second.status_code == 422
        assert second.json() == {"ok": False, "error": "Email: уже зарегистрирован"}
        # токены НЕ выданы в 422 и вторая заявка НЕ создана
        assert "poll_token" not in second.json()
        rows = sqlite3.connect(db_path()).execute(
            "SELECT COUNT(*) FROM instructor_applications"
        ).fetchone()[0]
        assert rows == 1

    def test_token_collision_regenerated_application_created_no_422(
        self, client, monkeypatch
    ):
        """MIN-2, ветка token: коллизия частичного UNIQUE → регенерация +
        повторная вставка БЕЗ 422 (design.md «Модель данных»)."""
        poll_a, _ = apply_tokens(client)  # в БД уже есть poll_token
        real_token_urlsafe = secrets.token_urlsafe
        calls = {"n": 0}

        def colliding_once(length=None):
            # первый вызов — заведомая коллизия poll_token, далее — честные
            calls["n"] += 1
            if calls["n"] == 1:
                return poll_a
            return real_token_urlsafe(32)

        monkeypatch.setattr(
            instructors.secrets, "token_urlsafe", colliding_once
        )
        resp = apply_post(client, email="collision@example.com")
        # НЕ 422: коллизия токена не превращается в ложный «дубль email»
        assert resp.status_code == 200, resp.text
        assert calls["n"] >= 2  # регенерация реально произошла
        body = resp.json()
        assert body["poll_token"] != poll_a
        row = fetch_application("collision@example.com")
        assert row is not None
        assert row["poll_token"] == body["poll_token"]

    def test_integrity_branches_classified_by_real_sqlite_messages(self, client):
        """MIN-2: классификатор веток сверен с РЕАЛЬНЫМИ сообщениями
        IntegrityError SQLite — и колоночного UNIQUE (email), и частичных
        UNIQUE-индексов токенов (по имени индекса/колонки)."""
        conn = sqlite3.connect(db_path())
        insert_raw_application(
            conn, "raw1@example.com", poll_token="P" * 43, exchange_token="E" * 43
        )
        conn.commit()
        messages = {}
        # гонка дубля email (UNIQUE instructor_applications.email)
        try:
            insert_raw_application(conn, "raw1@example.com")
        except sqlite3.IntegrityError as exc:
            messages["email"] = str(exc)
        # коллизия poll_token (частичный UNIQUE)
        try:
            insert_raw_application(
                conn, "raw2@example.com", poll_token="P" * 43
            )
        except sqlite3.IntegrityError as exc:
            messages["poll"] = str(exc)
        # коллизия exchange_token (частичный UNIQUE)
        try:
            insert_raw_application(
                conn, "raw3@example.com", exchange_token="E" * 43
            )
        except sqlite3.IntegrityError as exc:
            messages["exchange"] = str(exc)
        conn.close()
        assert instructors._integrity_kind(messages["email"]) == "email"
        assert instructors._integrity_kind(messages["poll"]) == "token"
        assert instructors._integrity_kind(messages["exchange"]) == "token"


# --- TC-S9BE-002: статус waiting, чтение без побочных эффектов (P-2) --------


def test_tc_s9be_002_status_waiting_read_only_no_side_effects(client):
    """TC-S9BE-002 (задача 5.1; FR-80, NFR-28 — только чтение).

    Requirement: Автоопределение статуса заявки на экране ожидания
    Scenario: Экран опрашивает статус по неперебираемому идентификатору
    (запрос только чтения, без записи и побочных эффектов).
    """
    poll, exchange = apply_tokens(client)
    row_before = dict(fetch_application("instructor@example.com"))
    for _ in range(3):  # многократные тики опроса
        resp = client.get(_STATUS_PATH, headers={"X-Poll-Token": poll})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["ok"] is True
        assert body["status"] == "waiting"
        assert body["reason"] is None  # reason только при rejected
    # N чтений НЕ меняют заявку: статус/created_at/токены/комментарий
    row_after = dict(fetch_application("instructor@example.com"))
    assert row_after == row_before
    assert row_after["exchange_token"] == exchange  # не потреблен чтением


# --- TC-S9BE-003: approved + бесшовный обмен на сессию (P-2) ----------------


def test_tc_s9be_003_approved_status_and_seamless_exchange(client):
    """TC-S9BE-003 (задача 5.1; FR-81).

    Requirement: Автоопределение статуса заявки на экране ожидания
    Scenario: waiting → approved: бесшовный переход в кабинет без ввода пароля
    Scenario: Ошибка обмена оставляет экран в waiting
    (обмен одноразового токена на существующую сессию users, роль
    instructor; переходный отказ 409 вырожденного «approved без users» —
    токен НЕ потреблен, повтор возможен).
    """
    poll, exchange = apply_tokens(client)
    approve(client, "instructor@example.com")

    resp = client.get(_STATUS_PATH, headers={"X-Poll-Token": poll})
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"
    assert resp.json()["reason"] is None

    # обмен токена на сессию — форма ответа логина (design.md «Порядок
    # обмена» п.5): {ok, token, route:'cabinet'}
    resp = client.post(_EXCHANGE_PATH, json={"exchange_token": exchange})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["route"] == "cabinet"
    assert isinstance(body["token"], str) and body["token"]
    # сессия рабочая и привязана к строке users инструктора (FR-81).
    # [test-adapted] P-2 (задача 6.1): было me["user"]["role"] — контракт
    # /api/auth/me БЕЗ ключа role не меняется (sdd.md §20.1, регресс
    # Спринтов 1–2.1: test_auth.py проверяет точный состав user), поэтому
    # роль instructor верифицируется по строке users в БД (семантика
    # сохранена: сессия → users с role='instructor')
    me = client.get(
        "/api/auth/me", headers={"X-Session-Token": body["token"]}
    )
    assert me.status_code == 200, me.text
    me_body = me.json()
    assert me_body["ok"] is True
    assert me_body["user"]["email"] == "instructor@example.com"
    assert fetch_user("instructor@example.com")["role"] == "instructor"

    # Сценарий «Ошибка обмена оставляет экран в waiting»: переходный отказ
    # 409 (вырожденное «approved без users» — вне контракта модерации) —
    # токен НЕ потреблен, повторный обмен возможен на следующем тике.
    apply_tokens(client, email="degenerate@example.com")
    force_status("degenerate@example.com", "approved")  # без INSERT users
    poll_d, exchange_d = _poll_exchange_of("degenerate@example.com")
    resp = client.post(_EXCHANGE_PATH, json={"exchange_token": exchange_d})
    assert resp.status_code == 409
    assert resp.json()["ok"] is False
    row = fetch_application("degenerate@example.com")
    assert row["exchange_token"] == exchange_d  # токен сохранен


def _poll_exchange_of(email):
    row = fetch_application(email)
    return row["poll_token"], row["exchange_token"]


# --- TC-S9BE-004: rejected с причиной/без (P-2) -----------------------------


def test_tc_s9be_004_rejected_with_reason_and_without(client):
    """TC-S9BE-004 (задача 5.1; FR-82).

    Requirement: Автоопределение статуса заявки на экране ожидания
    Scenario: waiting → rejected: причина отказа без входа
    (текст причины виден без входа; пустой/исторический комментарий —
    нейтральный текст).
    """
    # с причиной: deny обязателен непустой комментарий (Спринт 2)
    poll_a, _ = apply_tokens(client)
    deny(client, "instructor@example.com", "нечитаемое фото ВУ")
    resp = client.get(_STATUS_PATH, headers={"X-Poll-Token": poll_a})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "rejected"  # внутренний 'deny' маппится
    assert body["reason"] == "нечитаемое фото ВУ"

    # без причины (историческая заявка): комментарий пуст → нейтральный
    # текст на экране; backend отдает reason = review_comment ('')
    poll_b, _ = apply_tokens(client, email="historic@example.com")
    deny(client, "historic@example.com", "временный комментарий")
    force_status(
        "historic@example.com", "deny", review_comment=""
    )  # симуляция исторической строки
    resp = client.get(_STATUS_PATH, headers={"X-Poll-Token": poll_b})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "rejected"
    assert body["reason"] == ""


# --- TC-S9BE-005: 404-неразличение, 422 на пустые (P-2) ---------------------


def test_tc_s9be_005_404_indistinguishable_and_422_on_empty(client):
    """TC-S9BE-005 (задача 5.1; NFR-28, NFR-7).

    Requirement: Автоопределение статуса заявки на экране ожидания
    Scenario: Чужой или несуществующий идентификатор — 404-неразличение
    (чужая и несуществующая заявка неотличимы; сессия не выдается).
    """
    poll, exchange = apply_tokens(client)
    foreign_poll = secrets.token_urlsafe(32)
    foreign_poll2 = secrets.token_urlsafe(32)
    foreign_exchange = secrets.token_urlsafe(32)
    foreign_exchange2 = secrets.token_urlsafe(32)

    # чужой и несуществующий poll_token — одинаковый 404-ответ
    resp_foreign = client.get(
        _STATUS_PATH, headers={"X-Poll-Token": foreign_poll}
    )
    resp_missing = client.get(
        _STATUS_PATH, headers={"X-Poll-Token": foreign_poll2}
    )
    assert resp_foreign.status_code == 404
    assert resp_missing.status_code == 404
    assert resp_foreign.json() == resp_missing.json()
    assert resp_foreign.json()["ok"] is False

    # чужой и несуществующий exchange_token — одинаковый 404-ответ
    resp_foreign = client.post(_EXCHANGE_PATH, json={"exchange_token": foreign_exchange})
    resp_missing = client.post(_EXCHANGE_PATH, json={"exchange_token": foreign_exchange2})
    assert resp_foreign.status_code == 404
    assert resp_missing.status_code == 404
    assert resp_foreign.json() == resp_missing.json()
    assert resp_foreign.json()["ok"] is False

    # пустые заголовок/токен → 422 (контракт формата запроса)
    assert client.get(_STATUS_PATH).status_code == 422
    assert client.get(_STATUS_PATH, headers={"X-Poll-Token": ""}).status_code == 422
    assert client.post(_EXCHANGE_PATH, json={}).status_code == 422
    assert client.post(_EXCHANGE_PATH, json={"exchange_token": ""}).status_code == 422

    # зондирующие запросы без побочных эффектов: валидные токены живы
    assert client.get(
        _STATUS_PATH, headers={"X-Poll-Token": poll}
    ).status_code == 200
    assert fetch_application("instructor@example.com")["exchange_token"] == exchange


# --- TC-S9BE-006: миграция idempotent, backfill нет (P-1) -------------------

_LEGACY_APP_DDL = """
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


def test_tc_s9be_006_migration_idempotent_no_backfill(monkeypatch, tmp_path):
    """TC-S9BE-006 (задача 5.1; FR-80, NFR-11…24, design.md «Модель
    данных»: backfill НЕТ).

    Requirement: Автоопределение статуса заявки на экране ожидания
    Scenario: Экран без сохраненного идентификатора — статичный режим без запросов
    (историческая заявка: токенов нет — NULL, опрос невозможен по
    построению; миграция idempotent).
    """
    import backend.db as db

    legacy = tmp_path / "legacy.db"
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(legacy))
    conn = sqlite3.connect(str(legacy))
    conn.executescript(_LEGACY_APP_DDL)
    insert_legacy_application(conn, "old1@example.com")  # старые заявки БЕЗ токенов
    insert_legacy_application(conn, "old2@example.com")
    conn.commit()
    conn.close()

    db.init_db()

    conn = sqlite3.connect(str(legacy))
    columns = {name: ctype for (_, name, ctype, *_r) in conn.execute(
        "PRAGMA table_info(instructor_applications)"
    ).fetchall()}
    assert columns["poll_token"] == "TEXT"
    assert columns["exchange_token"] == "TEXT"
    # частичные UNIQUE-индексы на месте, SQL с WHERE … IS NOT NULL
    indexes = {row[0]: row[1] for row in conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type = 'index' AND name LIKE"
        " 'uq_instructor_applications_%'"
    ).fetchall()}
    assert "uq_instructor_applications_poll_token" in indexes
    assert "uq_instructor_applications_exchange_token" in indexes
    assert "WHERE poll_token IS NOT NULL" in indexes[
        "uq_instructor_applications_poll_token"
    ]
    # backfill НЕТ: старые строки остались NULL (статичный режим экрана)
    rows = conn.execute(
        "SELECT email, poll_token, exchange_token FROM instructor_applications"
        " ORDER BY email"
    ).fetchall()
    assert rows == [
        ("old1@example.com", None, None),
        ("old2@example.com", None, None),
    ]
    # индексы реально уникальны: дубль poll_token невозможен
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO instructor_applications (surname, name, patronymic,"
            " email, phone, address, work_format, license_number,"
            " license_category, password_hash, poll_token)"
            " VALUES ('Г', 'Д', 'Е', 'new@example.com', '+7 900 000-00-09',"
            " 'адрес', 'any', '123', 'B', 'hash', 'DUP-token')"
        )
        conn.execute(
            "INSERT INTO instructor_applications (surname, name, patronymic,"
            " email, phone, address, work_format, license_number,"
            " license_category, password_hash, poll_token)"
            " VALUES ('Ж', 'З', 'И', 'new2@example.com', '+7 900 000-00-08',"
            " 'адрес', 'any', '123', 'B', 'hash', 'DUP-token')"
        )
    conn.close()

    # повторный запуск init_db — ничего не меняет (idempotent)
    db.init_db()
    conn = sqlite3.connect(str(legacy))
    n_columns = conn.execute(
        "SELECT COUNT(*) FROM pragma_table_info('instructor_applications')"
        " WHERE name IN ('poll_token', 'exchange_token')"
    ).fetchone()[0]
    rows = conn.execute(
        "SELECT poll_token, exchange_token FROM instructor_applications"
        " WHERE email = 'old1@example.com'"
    ).fetchone()
    conn.close()
    assert n_columns == 2  # колонки не задвоены
    assert rows == (None, None)  # backfill по-прежнему нет


# --- TC-S9BE-007: потребление exchange_token, 409 waiting, MIN-1 (P-2) ------


def test_tc_s9be_007_consumed_exchange_repeat_404_and_waiting_409(client):
    """TC-S9BE-007 (задача 5.1; FR-81, MAJ-1 arch-review-002, MIN-1).

    Requirement: Автоопределение статуса заявки на экране ожидания
    Scenario: Обмен вернул 404 (токен потреблен или чужой) — терминальное состояние с подсказкой входа
    Scenario: Ошибка обмена оставляет экран в waiting
    (повторный обмен 404 — триггер терминального состояния экрана;
    обмен при waiting → 409 — переходная ветка, токен сохранен).
    """
    # 1) потребление: первый обмен 200 → токен NULL → повторный обмен 404
    poll, exchange = apply_tokens(client)
    approve(client, "instructor@example.com")
    first = client.post(_EXCHANGE_PATH, json={"exchange_token": exchange})
    assert first.status_code == 200
    assert fetch_application("instructor@example.com")["exchange_token"] is None
    repeat = client.post(_EXCHANGE_PATH, json={"exchange_token": exchange})
    assert repeat.status_code == 404  # терминальное состояние экрана (MAJ-1)
    assert repeat.json()["ok"] is False
    # approved — терминальный: статус после выдачи сессии НЕ меняется
    status = client.get(_STATUS_PATH, headers={"X-Poll-Token": poll})
    assert status.status_code == 200
    assert status.json()["status"] == "approved"

    # 2) обмен при waiting → 409 (guard, симметричен модерации), токен
    #    сохранен — повтор возможен на следующем тике
    apply_tokens(client, email="waiting@example.com")
    _, exchange_w = _poll_exchange_of("waiting@example.com")
    resp = client.post(_EXCHANGE_PATH, json={"exchange_token": exchange_w})
    assert resp.status_code == 409
    assert resp.json()["ok"] is False
    assert fetch_application("waiting@example.com")["exchange_token"] == exchange_w


def test_tc_s9be_007_parallel_exchanges_exactly_one_200(client):
    """TC-S9BE-007, часть MIN-1 (design.md «Порядок обмена» п.4): два
    ПАРАЛЛЕЛЬНЫХ обмена одним валидным токеном — ровно один 200, второй
    404; условный UPDATE … WHERE exchange_token = ? + rowcount
    (SQLite сериализует запись). Сессия выдана ровно одна.

    Requirement: Автоопределение статуса заявки на экране ожидания
    Scenario: waiting → approved: бесшовный переход в кабинет без ввода пароля
    (одноразовость токена обмена — анти-replay).
    """
    _, exchange = apply_tokens(client, email="parallel@example.com")
    approve(client, "parallel@example.com")

    results = []
    barrier = threading.Barrier(2)

    def exchange_worker():
        from backend.app import create_app
        from fastapi.testclient import TestClient

        with TestClient(create_app()) as worker_client:
            barrier.wait(timeout=30)  # синхронизация старта запросов
            resp = worker_client.post(
                _EXCHANGE_PATH, json={"exchange_token": exchange}
            )
            results.append((resp.status_code, resp.json()))

    threads = [
        threading.Thread(target=exchange_worker, daemon=True) for _ in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert len(results) == 2, "оба воркера должны завершиться"

    # ровно один 200, второй — 404-неразличение (MIN-1)
    statuses = sorted(status for status, _body in results)
    assert statuses == [200, 404]
    ok_bodies = [body for status, body in results if status == 200]
    assert len(ok_bodies) == 1
    assert ok_bodies[0]["ok"] is True
    assert ok_bodies[0]["route"] == "cabinet"
    # сессия выдана ровно одна и привязана к строке users инструктора
    # ([test-adapted] P-2: роль по строке users — контракт /me без ключа
    # role, sdd.md §20.1; см. TC-S9BE-003)
    me = client.get(
        "/api/auth/me", headers={"X-Session-Token": ok_bodies[0]["token"]}
    )
    assert me.status_code == 200
    assert me.json()["user"]["email"] == "parallel@example.com"
    assert fetch_user("parallel@example.com")["role"] == "instructor"
    # токен потреблен ровно один раз
    assert fetch_application("parallel@example.com")["exchange_token"] is None
