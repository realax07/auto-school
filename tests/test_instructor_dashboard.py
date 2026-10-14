"""Задача change add-instructor-cabinet — кабинет инструктора
(correlation_id 467fcb39a3234f33b54b95567f4ce656).

Трассировка (по паттерну tests/test_auth_route.py, rule 6): плановые ID
TC-FR18D-001…TC-FR18D-009 (до утверждения кейсов QA-циклом) — сценарии
спек-дельты openspec/changes/add-instructor-cabinet/specs/instructor-dashboard/spec.md:
- TC-FR18D-001 «Обращение к данным кабинета без сессии отклоняется»
  (401 без токена);
- TC-FR18D-002 «Сессия истекла» / неверный токен (401);
- TC-FR18D-003 «После выхода повторный доступ к кабинету отклоняется»
  (logout → 401);
- TC-FR18D-004 «Сессия ученика не дает доступ к кабинету инструктора»
  (403, FR-18);
- TC-FR18D-005 «Одобренный инструктор с сессией видит кабинет»
  (200 + ФИО/email, demo-флаг, FR-18/FR-20);
- TC-FR19D-006 «Данные кабинета — демо» (состав демо-блоков, FR-19/FR-21);
- TC-FR19D-007 «Структура кабинета соответствует макету» (дословные
  тексты/CSS макета, FR-19);
- TC-FR21D-008 «Все разделы сайдбара переключаются» / пометка «демо»
  (FR-19/FR-21, wiring-контроль по паттерну test_instructor_pages.py);
- TC-FR22D-009 «Выход через профиль» / «Выход прямой кнопкой» (wiring);
- сборка: /instructor/dashboard отдаётся (задача 3.1).

Готовность 1.1: logout → повторный вызов 401; SQL параметризован
(NFR-2 — единственный SELECT с `?`-плейсхолдером), ответ не логируется
(NFR-3). Фикстуры — общий client из conftest (create_app() поверх чистой БД).

Инструкторская учетка создается реальным флоу Спринта 2.1: apply →
approve → login (по паттерну test_auth_route.py).
"""
import sqlite3
import time
from pathlib import Path

import pytest

import backend.auth as auth
from conftest import admin_headers, db_path, register

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
MOCKS = ROOT / "design" / "mocks"

DASH = "/api/instructor/dashboard"
PAGE = FRONTEND / "instructor-dashboard.html"


@pytest.fixture()
def instructor(client):
    """Одобренный инструктор (users, role='instructor') + его сессия."""
    resp = client.post(
        "/api/instructors/apply",
        json={
            "surname": "Иванов",
            "name": "Иван",
            "patronymic": "Иванович",
            "phone": "+7 (911) 222-33-44",
            "email": "instr@example.com",
            "address": "г. Тест, ул. Полевая, 1",
            "work_format": "sber",
            "license_number": "9911223344",
            "license_category": "B",
            "password": "Instr1234",
            "password_confirm": "Instr1234",
            "consent": True,
        },
    )
    assert resp.status_code == 200, resp.text
    conn = sqlite3.connect(db_path())
    app_id = conn.execute(
        "SELECT id FROM instructor_applications WHERE email = ?",
        ("instr@example.com",),
    ).fetchone()[0]
    conn.close()
    resp = client.post(
        f"/api/admin/instructor-applications/{app_id}/approve",
        headers=admin_headers(client),
    )
    assert resp.status_code == 200, resp.text
    login = client.post(
        "/api/auth/login",
        json={"email": "instr@example.com", "password": "Instr1234"},
    )
    assert login.status_code == 200, login.text
    assert login.json()["route"] == "cabinet"
    return {"token": login.json()["token"], "email": "instr@example.com"}


def _headers(token):
    return {"X-Session-Token": token}


# --- FR-18: доступ (401 без/с неверным/аннулированным токеном) -------------------


def test_dashboard_401_without_token(client):
    """Сценарий «Обращение к данным кабинета без сессии отклоняется»:
    без X-Session-Token → 401 {"ok": false}."""
    resp = client.get(DASH)
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}


def test_dashboard_401_invalid_token(client):
    """Неверный/чужой токен — 401 (механика require_session, §10.3)."""
    resp = client.get(DASH, headers=_headers("not-a-real-token"))
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}


def test_dashboard_401_expired_session_ttl(client, instructor, monkeypatch):
    """Сценарий «Сессия истекла (TTL 12 ч)» (TC-FR18D-002, MIN-3):
    запись с истекшим expires кладется в auth._sessions напрямую — 401
    {"ok": false}, ленивая чистка удаляет запись (без sleep)."""
    monkeypatch.setitem(
        auth._sessions, instructor["token"], (time.time() - 1, 1)
    )
    assert instructor["token"] in auth._sessions

    resp = client.get(DASH, headers=_headers(instructor["token"]))
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}
    # ленивая чистка: истекшая запись вычищена при проверке
    assert instructor["token"] not in auth._sessions


def test_dashboard_401_after_logout(client, instructor):
    """Готовность 1.1: logout аннулирует токен → повторный вызов 401."""
    login = client.post(
        "/api/auth/login",
        json={"email": "instr@example.com", "password": "Instr1234"},
    )
    token = login.json()["token"]
    assert client.get(DASH, headers=_headers(token)).status_code == 200

    out = client.post("/api/auth/logout", headers=_headers(token))
    assert out.status_code == 200

    resp = client.get(DASH, headers=_headers(token))
    assert resp.status_code == 401
    assert resp.json() == {"ok": False}


# --- FR-18: роль (403 для student при валидной сессии) ----------------------------


def test_dashboard_403_for_student_session(client):
    """Сценарий «Сессия ученика не дает доступ к кабинету инструктора»:
    валидная сессия role='student' → 403 {"ok": false} (distinct от 401)."""
    assert register(client).status_code == 200
    login = client.post(
        "/api/auth/login",
        json={"email": "petrova@example.com", "password": "Qwerty123"},
    )
    assert login.status_code == 200
    resp = client.get(DASH, headers=_headers(login.json()["token"]))
    assert resp.status_code == 403
    assert resp.json() == {"ok": False}


# --- FR-18/FR-20: 200 для instructor с ФИО и демо-флагом --------------------------


def test_dashboard_200_for_instructor_with_fio(client, instructor):
    """Сценарий «Одобренный инструктор с сессией видит кабинет»: 200;
    ФИО/email из записи users (§20.1: состав полей instructor); demo: true."""
    resp = client.get(DASH, headers=_headers(instructor["token"]))
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["demo"] is True
    assert data["instructor"]["surname"] == "Иванов"
    assert data["instructor"]["name"] == "Иван"
    assert data["instructor"]["patronymic"] == "Иванович"
    assert data["instructor"]["email"] == "instr@example.com"


def test_dashboard_contains_demo_payload(client, instructor):
    """Демо-данные макета в ответе (stats, schedule, appointments,
    next_lesson, vehicle, operations) — реальные данные БД не выводятся."""
    data = client.get(DASH, headers=_headers(instructor["token"])).json()
    for key in ("stats", "schedule", "appointments", "next_lesson", "vehicle", "operations"):
        assert key in data, key
    assert len(data["stats"]) == 4
    assert len(data["appointments"]) == 4
    assert data["next_lesson"]["student"] == "Александр Иванов"


# --- FR-19/FR-21: статика отдаётся, тексты макета дословно ------------------------


def test_dashboard_page_served(client):
    """Задача 3.1: GET /instructor/dashboard отдаётся, text/html."""
    resp = client.get("/instructor/dashboard")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_dashboard_page_mockup_texts_verbatim():
    """FR-19: дословные тексты ключевых блоков макета (шапка, приветствие,
    4 карточки статистики, расписание, занятия, ближайшее, автомобиль,
    операции, быстрые действия, футер «Все данные вымышлены») + все CSS-
    строки мокапа."""
    html = PAGE.read_text(encoding="utf-8")
    mockup = (MOCKS / "dashboard-instructor.html").read_text(encoding="utf-8")
    fragments = [
        "<title>СберАвтошкола — кабинет инструктора</title>",
        '<div class="brand"><div class="check">✓</div><div>СберАвтошкола<small>Кабинет инструктора</small></div></div>',
        'Рабочее пространство / <span id="crumb">Мой день</span>',
        '<h1 id="page-title">Мой день</h1>',
        "Пн, 12 октября 2026",
        "<small>Инструктор · Категория B</small>",
        "<h2>Добрый день, Михаил</h2>",
        "Вот что у тебя сегодня. Всё под контролем.",
        "Профиль активен",
        "Заработано за месяц",
        "84 600",
        "к прошлому месяцу",
        "Отработано часов",
        "из 80 ч",
        "план на месяц",
        "Мои ученики",
        "+3",
        "новых за неделю",
        "Занятия сегодня",
        "Первое в 10:00",
        "Расписание занятий",
        "Загруженность и свободные окна на неделе",
        "Эта неделя",
        "Занятие подтверждено",
        "Ожидает подтверждения",
        "Свободное окно",
        "Сегодня · 4 занятия",
        "Весь календарь ↗",
        "Александр Иванов",
        "Практика · Городской маршрут",
        "Екатерина Смирнова",
        "Практика · Манёвры и парковка",
        "Дмитрий Волков",
        "Можно открыть запись для ученика",
        "Ближайшее занятие",
        "Сегодня, через 30 минут",
        "Škoda Rapid · А123АА",
        "Согласованная локация",
        "Движение в потоке",
        "Открыть занятие ↗",
        "Мой автомобиль",
        "Данные подключённого авто",
        "2020 · Автомат",
        "А123АА 777",
        "Свой автомобиль",
        "Проверка документов",
        "Последние операции",
        "Начисления и выплаты",
        "Занятие · Мария Петрова",
        "Расходы на автомобиль",
        "+2 000 ₽",
        "−1 450 ₽",
        "Быстрые действия",
        "Самое нужное — в один клик",
        "Открыть время<br>для записи",
        "Посмотреть<br>учеников",
        "Мои доходы<br>и выплаты",
        "СберАвтошкола · Кабинет инструктора",
        "Демонстрационный интерфейс · Все данные вымышлены",
    ]
    for fragment in fragments:
        assert fragment in html, fragment
        assert fragment in mockup, f"фрагмент не из мокапа: {fragment}"

    # все CSS-правила мокапа — дословно (блочные строки <style>)
    mockup_css = mockup.split("<style>", 1)[1].split("</style>", 1)[0]
    page_css = html.split("<style>", 1)[1].split("</style>", 1)[0]
    for line in mockup_css.splitlines():
        if not line.strip():
            continue
        assert line in page_css, f"CSS-строка мокапа изменена/удалена: {line[:60]}"


def test_dashboard_page_nav_sections_fr19():
    """FR-19/FR-21: сайдбар достроен nav-кнопками разделов (полный перечень
    FR-19), у разделов кроме «Мой день» — пометка «демо»; на готовых
    .nav-стилях и механике navTo мокапа."""
    html = PAGE.read_text(encoding="utf-8")
    for section in (
        "Мой день",
        "Расписание",
        "Мои ученики",
        "Доходы и выплаты",
        "Мой автомобиль",
        "Материалы и обучение",
        "Профиль и документы",
    ):
        assert f'data-tab="{section}"' in html, section
    js = html.split("<script>", 1)[1]
    assert "navTo" in js
    assert "document.querySelectorAll('.nav button')" in js
    # пометка «демо» у разделов (кроме «Мой день»)
    assert 'class="demo-tag">демо<' in html
    active = html.split('<button class="active" data-tab="', 1)[1].split('"', 1)[0]
    assert active == "Мой день"


def test_dashboard_page_wiring_fr18_fr20_fr22():
    """Wiring (единственные отличия от мокапа): GET /api/instructor/dashboard
    с X-Session-Token до отрисовки, 401/403 → редирект `/`; ФИО шапки из
    ответа (инициалы — первые буквы фамилии и имени); демо-ФИО заменяется;
    выход → POST /api/auth/logout → sessionStorage.clear() → `/`."""
    html = PAGE.read_text(encoding="utf-8")
    js = html.split("<script>", 1)[1]
    assert "fetch('/api/instructor/dashboard'" in js
    assert "'X-Session-Token'" in js
    assert "sessionStorage" in js
    assert "session_token" in js
    # 401/403 -> редирект на главную (к модалке входа)
    assert "res.status===401||res.status===403" in js
    assert "location.href='/'" in js
    # ФИО шапки = "{surname} {name} {patronymic}" (демо заменяется)
    assert "[i.surname,i.name,i.patronymic].filter(Boolean).join(' ')" in js
    assert "document.querySelector('.user b').textContent=fio" in js
    # инициалы аватара — первые буквы фамилии и имени
    assert "document.querySelector('.avatar').textContent=initials" in js
    # выход: logout -> очистка sessionStorage -> редирект
    assert "fetch('/api/auth/logout'" in js
    assert "method:'POST'" in js
    assert "sessionStorage.clear()" in js
    assert "function logout()" in js


def test_dashboard_sql_parameterized():
    """NFR-2: единственный новый запрос — SELECT users по id с
    `?`-плейсхолдером; 0 конкатенаций SQL в новом модуле."""
    src = (ROOT / "backend" / "dashboard.py").read_text(encoding="utf-8")
    assert 'WHERE id = ?"' in src
    for bad in ('id = \' +', "id = \" +", 'f"SELECT', "format(SELECT"):
        assert bad not in src, bad
