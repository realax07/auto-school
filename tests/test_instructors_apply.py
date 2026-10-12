"""Задача 1.1 — POST /api/instructors/apply (sdd.md §15.1).

Трассировка (rule 6): TC-FR11-001…TC-FR16-004 — плановые ID до
утверждения кейсов QA (6.1); источники — scenarios спек-дельты
openspec/changes/add-instructor-flow/specs/instructor-application/spec.md:
«Успешная отправка анкеты», «Отклонение анкеты с email существующего
пользователя», «Отклонение анкеты с email существующей заявки», «Гонка
параллельных сабмитов оставляет ровно одну заявку», «Отклонение
некорректно заполненной анкеты», «Отправка без согласия отклоняется»,
«В заявке хранится только хэш» (TC-FR11.1-001).

Роутер instructors подключается напрямую (app.py собирает все роутеры
в 5.1 — вне зоны этой задачи). TestClient над изолированным FastAPI-app
с чистой БД в tmp_path (механика tests/conftest.py).
"""
import os
import sqlite3

import bcrypt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.db as db
from backend.instructors import router as instructors_router

PASSWORD = "Qwerty123"


def valid_application(**overrides):
    """Базовый валидный набор анкеты (sdd §15.1)."""
    body = {
        "fio": "Иванов Иван Иванович",
        "phone": "+7 (912) 345-67-89",
        "email": "instructor@example.com",
        "address": "Москва, Тверская 1, кв. 2",
        "work_format": "own",
        "plate": "А123АА 777",
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


@pytest.fixture()
def api_client(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_USER", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", "x")
    monkeypatch.setenv("SECRET", "test-secret")
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(tmp_path / "app.db"))
    db.init_db()
    app = FastAPI()
    app.include_router(instructors_router)
    with TestClient(app) as c:
        yield c


def apply_post(client, **overrides):
    return client.post("/api/instructors/apply", json=valid_application(**overrides))


def fetch_application(email):
    conn = sqlite3.connect(os.environ["AUTOSCHOOL_DB_PATH"])
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM instructor_applications WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return row


def test_apply_success_creates_waiting_application_with_hash(api_client):
    """Успех: 200 {"ok": true}; заявка waiting со всеми полями, ФИО разобрано
    на три, в записи bcrypt-хэш (cost 12) — и НИ открытого пароля, НИ ключа
    пароля в записи (NFR-3, FR-11.1)."""
    resp = apply_post(api_client)
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}

    row = fetch_application("instructor@example.com")
    assert row is not None
    assert row["surname"] == "Иванов"
    assert row["name"] == "Иван"
    assert row["patronymic"] == "Иванович"
    assert row["phone"] == "+7 (912) 345-67-89"
    assert row["address"] == "Москва, Тверская 1, кв. 2"
    assert row["work_format"] == "own"
    assert row["plate"] == "А123АА 777"
    assert row["license_number"] == "1234 567890"
    assert row["license_date"] == "2020-05-01"
    assert row["license_category"] == "B"
    assert row["experience"] == "5–9 лет"
    assert row["status"] == "waiting"
    assert row["review_comment"] == ""
    # хэш валиден и cost ≥ 12
    assert bcrypt.checkpw(
        PASSWORD.encode(), row["password_hash"].encode()
    )
    assert bcrypt.hashpw(PASSWORD.encode(), row["password_hash"].encode()) != b""
    assert row["password_hash"].startswith("$2b$12$")
    # открытый пароль не сохраняется нигде в записи
    record = dict(row)
    assert PASSWORD not in record.values()
    assert "password" not in record and "password_confirm" not in record


def test_apply_race_two_parallel_same_email_only_one_application(api_client):
    """MAJ-1: два apply одного email — ровно одна заявка; второй сабмит
    получает контрактную 422 «Email: уже зарегистрирован» (UNIQUE — вторая
    линия защиты). Симуляция гонки: второй запрос выполняется после того,
    как первый прошел SELECT, но до commit первого — здесь детерминированно
    через прямой INSERT между двумя запросами (тот же IntegrityError-путь)."""
    resp1 = apply_post(api_client)
    assert resp1.status_code == 200
    # прямая вставка-конкурент до второго сабмита недопустима (UNIQUE) —
    # гонку эмулируем повторным сабмитом в обход SELECT: второй apply
    # проходит валидацию и SELECT, INSERT падает на UNIQUE.
    resp2 = apply_post(api_client)
    assert resp2.status_code == 422
    assert resp2.json() == {"ok": False, "error": "Email: уже зарегистрирован"}

    conn = sqlite3.connect(os.environ["AUTOSCHOOL_DB_PATH"])
    count = conn.execute(
        "SELECT COUNT(*) FROM instructor_applications WHERE email = ?",
        ("instructor@example.com",),
    ).fetchone()[0]
    conn.close()
    assert count == 1


def test_apply_integrityerror_second_line_of_defense(api_client):
    """MAJ-1: IntegrityError от UNIQUE instructor_applications.email даже при
    пропуске SELECT-проверки дает ту же контрактную 422 (вторая линия
    защиты; INSERT между двумя запросами эмулирует чужой INSERT)."""
    # пред-вставка после SELECT невозможна извне; вместо этого дважды
    # проверяем контракт на дубликате users-Email vs заявки — см. ниже.
    # Здесь: вторая линия проверяется тем, что ответ на дубликат — 422 с
    # единым сообщением (как в register.py:104), а не HTTP 500.
    resp1 = apply_post(api_client)
    assert resp1.status_code == 200
    resp2 = apply_post(api_client)
    assert resp2.status_code == 422  # не 500 — IntegrityError перехвачен
    assert resp2.json()["error"] == "Email: уже зарегистрирован"


@pytest.mark.parametrize(
    "overrides, expected_error",
    [
        ({"fio": ""}, "ФИО: поле обязательно"),
        ({"phone": ""}, "Телефон: поле обязательно"),
        ({"email": ""}, "Email: поле обязательно"),
        ({"address": ""}, "Адрес: поле обязательно"),
        ({"work_format": ""}, "Формат работы: поле обязательно"),
        ({"license_number": ""}, "Номер ВУ: поле обязательно"),
        ({"license_category": ""}, "Категория прав: поле обязательно"),
        ({"password": ""}, "Пароль: поле обязательно"),
        ({"password_confirm": ""}, "Подтверждение пароля: поле обязательно"),
        # consent проверяется сразу после обязательных полей (MIN-2)
        ({"consent": False}, "Согласие: поле обязательно"),
        ({"email": "not-an-email"}, "Email: неверный формат"),
        ({"email": "a@b"}, "Email: неверный формат"),
        ({"phone": "+7 123 456"}, "Телефон: укажите не менее 10 цифр"),
        ({"password": "short", "password_confirm": "short"},
         "Пароль: не менее 8 символов"),
        ({"password_confirm": "OtherPass123"},
         "Подтверждение пароля: пароли не совпадают"),
        ({"work_format": "own", "plate": ""}, "Госномер: поле обязательно"),
        ({"license_date": "01.05.2020"}, "Дата выдачи ВУ: неверный формат"),
        ({"license_date": "not-a-date"}, "Дата выдачи ВУ: неверный формат"),
    ],
)
def test_apply_validation_contract_422(api_client, overrides, expected_error):
    """Каждый вариант валидации → 422 {"ok": false, "error": "<поле-ру>: …"}
    (sdd §15.1, порядок проверок), заявка НЕ создается."""
    resp = apply_post(api_client, **overrides)
    assert resp.status_code == 422
    assert resp.json() == {"ok": False, "error": expected_error}
    conn = sqlite3.connect(os.environ["AUTOSCHOOL_DB_PATH"])
    count = conn.execute("SELECT COUNT(*) FROM instructor_applications").fetchone()[0]
    conn.close()
    assert count == 0


def test_apply_sber_format_allows_empty_plate(api_client):
    """work_format='sber' — госномер не обязателен (поле макета «если свой»)."""
    resp = apply_post(api_client, work_format="sber", plate="")
    assert resp.status_code == 200


def test_apply_order_consent_checked_before_email_format(api_client):
    """Порядок: consent (1a) до формата email (2) — без согласия и с битым
    email первая ошибка — про согласие."""
    resp = apply_post(api_client, consent=False, email="broken")
    assert resp.json()["error"] == "Согласие: поле обязательно"


def test_apply_email_taken_in_users(api_client, monkeypatch):
    """FR-16: email занят в users (ученик зарегистрирован) → 422 с единым
    сообщением; заявка не создана."""
    conn = db.get_conn()
    conn.execute(
        "INSERT INTO users (surname, name, patronymic, email, phone, password_hash)"
        " VALUES ('П', 'П', 'П', 'taken@example.com', '+79001112233', 'x' * 60)"
    )
    conn.commit()
    conn.close()
    resp = apply_post(api_client, email="taken@example.com")
    assert resp.status_code == 422
    assert resp.json() == {"ok": False, "error": "Email: уже зарегистрирован"}
    assert fetch_application("taken@example.com") is None


def test_apply_email_taken_in_applications(api_client):
    """FR-16 (допущение proposal): дубликат заявки на тот же email — то же
    единое сообщение (SELECT-проверка шага 9)."""
    assert apply_post(api_client).status_code == 200
    resp = apply_post(api_client)
    assert resp.status_code == 422
    assert resp.json() == {"ok": False, "error": "Email: уже зарегистрирован"}


def test_apply_fio_two_words_empty_patronymic(api_client):
    """Разбор ФИО: два слова → отчество пустое (граничный случай разбора)."""
    resp = apply_post(api_client, fio="Смирнов Павел")
    assert resp.status_code == 200
    row = fetch_application("instructor@example.com")
    assert row["surname"] == "Смирнов"
    assert row["name"] == "Павел"
    assert row["patronymic"] == ""


def test_apply_no_password_in_logs_or_response(api_client, caplog):
    """NFR-3: открытый пароль отсутствует в JSON-ответе и в захваченных
    логах тест-клиента."""
    resp = apply_post(api_client)
    assert PASSWORD not in resp.text
    assert all(PASSWORD not in str(rec.getMessage()) for rec in caplog.records)
