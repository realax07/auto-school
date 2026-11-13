"""TC-AUTH/CAB (Спринт 1, задача 2.1) — кабинет ученика /cabinet: статика и wiring
# Change: add-auth-cabinet
(задача 2.1, sdd.md §10.2–§10.4, §13; design.md, поток 2).

Спринт 15 (change add-vue-s15-final-migration, задача 5.1): перенос
носителей — легаси frontend/cabinet.html удален (замена монолита целиком,
ADR-008), кабинет обслуживается входом каркаса Vue. Носители — прецедент
2.3 пилота / 3.1 С11 / 4.1 С12/С14 (право правки — перенос носителя, БЕЗ
ослаблений: фрагменты/маркеры/CSS-строки дословно):
- CABINET = frontend/vue/cabinet.html (вход каркаса; дословная разметка
  легаси + вербатим-комментарий wiring);
- APP = src/pages/cabinet/App.vue (wiring — плоский JS в onMounted,
  реактивные списки — design.md «Границы правок тестов»);
- UTILS = src/shared/utils.js (fioOf/fmtDate — дословный перенос
  js/shared/utils.js, задача 4.2; аналогично frontend_source, который
  следовал импортам легаси-модуля транзитивно: единица wiring включала
  js/shared/utils.js);
- CSS-сверка → src/pages/cabinet/styles.css (дословный перенос <style>
  легаси, построчно — прецедент С14 test_instructor_dashboard);
- MOCKUP = design/mocks/cabinet-student.html — БЕЗ ПРАВОК (мокапы не
  синхронизируются: разметка страницы не меняется — design.md «Стратегия
  вербатим-мокапов»).

Покрытие браузерных сценариев 401-редиректа, подстановки ФИО и
logout-редиректа — контролями wiring-фрагментов (по паттерну
test_static.py: тест TC-REG-018, шаг 3, контроль wiring).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CABINET = ROOT / "frontend" / "vue" / "cabinet.html"
APP = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "App.vue"
UTILS = ROOT / "frontend" / "vue" / "src" / "shared" / "utils.js"
STYLES = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "styles.css"
MOCKUP = ROOT / "design" / "mocks" / "cabinet-student.html"


def cabinet_html() -> str:
    return CABINET.read_text(encoding="utf-8")


def cabinet_source() -> str:
    """Единица wiring страницы: вход + компонент + общие хелперы
    (аналог frontend_source("cabinet.html"), который включал подключенные
    ES-модули легаси транзитивно — js/shared/utils.js был в единице)."""
    return "\n".join([
        cabinet_html(),
        APP.read_text(encoding="utf-8"),
        UTILS.read_text(encoding="utf-8"),
    ])


# --- FR-9: перенос мокапа дословно -------------------------------------------


def test_cab_page_exists_and_marker_texts():
    """Готовность 2.1: файл существует; дословные тексты мокапа присутствуют
    (бренд, крошка, приветствие-пример, чат-бар, плитки, футер)."""
    html = cabinet_source()
    for marker in (
        "СберАвтошкола",
        "<em>Сбер</em>Автошкола",
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
    # BUG-059/060 (решение Заказчика 2026-11-06): дубль логотипа в шапке
    # контента убран (логотип — только в сайдбаре), крошки нет, тегов
    # «В КАБИНЕТЕ» на плитках нет.
    for absent in (
        '<div class="brand">',
        "Личный кабинет · Ученик",
        "В КАБИНЕТЕ",
    ):
        assert absent not in html, absent


def test_cab_page_structure_matches_mockup_verbatim():
    """FR-9: структурные фрагменты мокапа перенесены дословно — заголовок,
    разметка hero/frame, крошка, футер (посимвольно); все строки стилей
    мокапа — дословно (носитель — styles.css страницы каркаса, прецедент
    С14 §TC-FR19D-007); плитки — дословно (три <button class="tile">)."""
    html = cabinet_source()
    mockup = MOCKUP.read_text(encoding="utf-8")
    fragments = [
        "<!doctype html>",
        '<html lang="ru">',
        "<title>СберАвтошкола — Кабинет ученика (мокап)</title>",
        '<div class="hero"><div class="frame">',
        '<header>',
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

    # все CSS-правила мокапа — дословно (блочные строки <style>;
    # носитель — styles.css страницы каркаса, перенос 1:1 из легаси)
    mockup_css = mockup.split("<style>", 1)[1].split("</style>", 1)[0]
    page_css = STYLES.read_text(encoding="utf-8")
    for line in mockup_css.splitlines():
        if not line.strip():
            continue
        assert line in page_css, f"CSS-строка мокапа изменена/удалена: {line[:60]}"

    # плитки — дословно (три <button class="tile"> из мокапа)
    mockup_tiles = mockup.split('<div class="tiles">', 1)[1].split("</div>", 1)[0]
    assert mockup_tiles in html, "разметка плиток отличается от мокапа"


def test_cab_page_keeps_mockup_stub_alert():
    """FR-6: плитки/чат — заглушки без сервисных действий; alert из мокапа
    сохранен (поведение клика — как в мокапе, design.md поток 2).
    Спринт 15: JS — плоский wiring в App.vue (см. cabinet_source)."""
    html = cabinet_source()
    assert ".tile" in html and ".quick button" in html and ".send" in html
    assert "Заглушка: сервис появится в следующем спринте" in cabinet_source()


# --- Wiring (единственные отличия от мокапа) ---------------------------------


def test_cab_wiring_auth_me_with_session_token_header():
    """FR-5/FR-7: wiring /api/auth/me с заголовком X-Session-Token из
    sessionStorage (sdd §10.3). Спринт 15: wiring — в App.vue (проверяем
    вход + компонент + хелперы, см. cabinet_source)."""
    src = cabinet_source()
    assert "/api/auth/me" in src
    assert "X-Session-Token" in src
    assert "sessionStorage" in src
    assert "session_token" in src


def test_cab_wiring_401_redirect_to_landing():
    """FR-7: 401 / нет токена → редирект на главную (к модалке входа m-login).
    Спринт 15: wiring — в App.vue."""
    src = cabinet_source()
    assert "toLogin" in src
    assert "location.href = '/'" in src


def test_cab_wiring_fio_substitution():
    """FR-5: 200 → подстановка ФИО: uname = «{surname} {name} {patronymic}»,
    greet = «Добро пожаловать, {name}!» (sdd §10.3). Спринт 15: wiring — в
    App.vue (fioOf — из vue/src/shared/utils.js, дословный перенос)."""
    src = cabinet_source()
    assert "surname" in src and "name" in src and "patronymic" in src
    assert "Добро пожаловать, " in src
    assert "querySelector('.uname')" in src
    assert "querySelector('.greet b')" in src


def test_cab_wiring_logout_flow():
    """FR-8: «Выйти» → POST /api/auth/logout → очистка sessionStorage →
    редирект на главную (sdd §10.2, design поток 3: после любого ответа).
    Спринт 15: wiring — в App.vue."""
    src = cabinet_source()
    assert "/api/auth/logout" in src
    assert "method: 'POST'" in src
    assert "removeItem" in src
    assert "location.href = '/'" in src
