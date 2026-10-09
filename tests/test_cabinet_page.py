"""TC-AUTH/CAB (Спринт 1, задача 2.1) — frontend/cabinet.html: статика и wiring
# Change: add-auth-cabinet
(задача 2.1, sdd.md §10.2–§10.4, §13; design.md, поток 2).

Маршрут /cabinet появится в задаче 3.1 — здесь TestClient не участвует:
файл frontend/cabinet.html читается напрямую и сверяется посимвольно с
утвержденным мокапом design/mocks/cabinet-student.html (кроме wiring и
подстановки ФИО — design.md «Тексты и стили — дословно из мокапа;
отличия ТОЛЬКО: wiring»). Покрытие браузерных сценариев 401-редиректа,
подстановки ФИО и logout-редиректа — контролями wiring-фрагментов
(по паттерну test_static.py: тест TC-REG-018, шаг 3, контроль wiring).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CABINET = ROOT / "frontend" / "cabinet.html"
MOCKUP = ROOT / "design" / "mocks" / "cabinet-student.html"


def cabinet_html() -> str:
    return CABINET.read_text(encoding="utf-8")


# --- FR-9: перенос мокапа дословно -------------------------------------------


def test_cab_page_exists_and_marker_texts():
    """Готовность 2.1: файл существует; дословные тексты мокапа присутствуют
    (бренд, крошка, приветствие-пример, чат-бар, плитки, футер)."""
    html = cabinet_html()
    for marker in (
        "СберАвтошкола",
        "<em>Сбер</em>Автошкола",
        "Личный кабинет · Ученик",
        "ЛИЧНЫЙ КАБИНЕТ",
        "Гига ГАИшник",
        "Твой AI-помощник в обучении и на дороге",
        "Спроси что угодно про обучение, экзамен или ПДД...",
        "Когда экзамен?",
        "Мой прогресс",
        "Готов ли я<br>к экзамену?",
        "СЕРВИСЫ",
        "Обучение ПДД",
        "Онлайн экзамен",
        "Найти водителя",
        "СКОРО",
        "СберАвтошкола · кабинет ученика",
        "Выйти",
    ):
        assert marker in html, marker


def test_cab_page_structure_matches_mockup_verbatim():
    """FR-9: структурные фрагменты мокапа перенесены дословно — заголовок,
    все строки стилей, разметка hero/frame, крошка, футер (посимвольно)."""
    html = cabinet_html()
    mockup = MOCKUP.read_text(encoding="utf-8")
    fragments = [
        "<!doctype html>",
        '<html lang="ru">',
        "<title>СберАвтошкола — Кабинет ученика (мокап)</title>",
        '<div class="hero"><div class="frame">',
        '<header>',
        '<div class="crumb">Личный кабинет · Ученик</div>',
        '<div class="user"><span class="uname">Иван Иванов</span><button class="logout">Выйти</button></div>',
        '<div class="greet">ЛИЧНЫЙ КАБИНЕТ<b>Добро пожаловать, Иван!</b></div>',
        '<section class="assistant">',
        '<div class="ai-head"><div class="avatar"></div><div><b>Гига ГАИшник</b><span>Твой AI-помощник в обучении и на дороге</span></div></div>',
        '<div class="prompt"><span>Спроси что угодно про обучение, экзамен или ПДД...</span><button class="send" title="Открыть чат с AI">↑</button></div>',
        '<footer><span>СберАвтошкола · кабинет ученика</span><span>Спринт 1 · визуал</span></footer>',
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

    # плитки — дословно (три <button class="tile"> из мокапа)
    mockup_tiles = mockup.split('<div class="tiles">', 1)[1].split("</div>", 1)[0]
    assert mockup_tiles in html, "разметка плиток отличается от мокапа"


def test_cab_page_keeps_mockup_stub_alert():
    """FR-6: плитки/чат — заглушки без сервисных действий; alert из мокапа
    сохранен (поведение клика — как в мокапе, design.md поток 2)."""
    html = cabinet_html()
    assert "Заглушка: сервис появится в следующем спринте" in html
    assert ".tile" in html and ".quick button" in html and ".send" in html


# --- Wiring (единственные отличия от мокапа) ---------------------------------


def test_cab_wiring_auth_me_with_session_token_header():
    """FR-5/FR-7: wiring /api/auth/me с заголовком X-Session-Token из
    sessionStorage (sdd §10.3)."""
    html = cabinet_html()
    assert "/api/auth/me" in html
    assert "X-Session-Token" in html
    assert "sessionStorage" in html
    assert "session_token" in html


def test_cab_wiring_401_redirect_to_landing():
    """FR-7: 401 / нет токена → редирект на главную (к модалке входа m-login)."""
    html = cabinet_html()
    assert "toLogin" in html
    assert "location.href = '/'" in html


def test_cab_wiring_fio_substitution():
    """FR-5: 200 → подстановка ФИО: uname = «{surname} {name} {patronymic}»,
    greet = «Добро пожаловать, {name}!» (sdd §10.3)."""
    html = cabinet_html()
    assert "surname" in html and "name" in html and "patronymic" in html
    assert "Добро пожаловать, " in html
    assert "querySelector('.uname')" in html
    assert "querySelector('.greet b')" in html


def test_cab_wiring_logout_flow():
    """FR-8: «Выйти» → POST /api/auth/logout → очистка sessionStorage →
    редирект на главную (sdd §10.2, design поток 3: после любого ответа)."""
    html = cabinet_html()
    assert "/api/auth/logout" in html
    assert "method: 'POST'" in html
    assert "removeItem" in html
    assert "location.href = '/'" in html
