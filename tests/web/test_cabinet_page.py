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
- SIDEBAR = src/components/StudentSidebar.vue — единый модуль сайдбара
  (замечание Заказчика 2026-11-16): разметка side/snav/side-user и wiring
  ФИО/«Выйти» переехали сюда; единица wiring страницы = вход + компонент
  + utils (фрагменты мокапа сайдбара проверяются по совокупности);
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

Спринт 19 (change add-ai-chat-home, задача 19.3.4/19.4 — «Главная» = ИИ-чат):
гарды «Главной» ПЕРЕВЕДЕНЫ на новые макеты-эталоны (аппрув Заказчика
2026-11-18 «Вот теперь отлично. Так и делай»):
- MOCKUP_MOBILE = design/mocks/mobile/mobile-home-chat.html (≤760px) и
  MOCKUP_WEB = design/mocks/home-chat-web.html (>760px) — фрагменты
  разметки/CSS/текстов «Главной» сверяются с ними ДОСЛОВНО (дизайн.md
  «Решение 4»: «фрагменты дословно; сами мокапы не синхронизируются»).
  Реализация переносит тексты/SVG макетов дословно (App.vue), а CSS —
  адаптированно (классы ai-*: .spark→.ai-spark и т.п., база веб-макета +
  @media ≤760px переопределения мобилки), поэтому CSS-строки сверяются
  ПАРАМИ «фрагмент макета ↔ фрагмент styles.css» с дословными значениями
  (прецедент side_fragments: мокап-фрагмент в макете, компонентный — в
  модуле); отброшенные при переносе классы .greet/.assistant/.quick/
  .services-title/.tiles — носители absence (решение Заказчика 2026-11-18
  «Да, убираем все кнопки с этого экрана и оставь только гигагаишника.
  Не только в могилке, но и на веб версии тоже»);
- MOCKUP = design/mocks/cabinet-student.html — ОСТАЕТСЯ эталоном разделов
  ВНЕ «Главной» (прецедент CHK-29: «Мои заявки», «Мои брони», «Кошелек»,
  ПДД; футер/hero-оболочка) — whole-line CSS-гард мокапа сохранен без
  ослаблений (строки легаси-стилей в styles.css не изменялись).
Осознанное отступление (вопрос Заказчику, waves 19.3): на вебе композер
стоит над футером с зазором 40px — не 48px padding-bottom макета (футер
мокапа Спринта 1 остается на всех разделах; styles.css, шапка блока S19).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CABINET = ROOT / "frontend" / "vue" / "cabinet.html"
APP = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "App.vue"
SIDEBAR = ROOT / "frontend" / "vue" / "src" / "components" / "StudentSidebar.vue"
UTILS = ROOT / "frontend" / "vue" / "src" / "shared" / "utils.js"
STYLES = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "styles.css"
MOCKUP = ROOT / "design" / "mocks" / "cabinet-student.html"
# Спринт 19: макеты-эталоны «Главной» (ИИ-чат) — БЕЗ ПРАВОК
MOCKUP_MOBILE = ROOT / "design" / "mocks" / "mobile" / "mobile-home-chat.html"
MOCKUP_WEB = ROOT / "design" / "mocks" / "home-chat-web.html"


def cabinet_html() -> str:
    return CABINET.read_text(encoding="utf-8")


def cabinet_source() -> str:
    """Единица wiring страницы: вход + КОМПОНЕНТ сайдбара + общие хелперы
    (аналог frontend_source("cabinet.html"), который включал подключенные
    ES-модули легаси транзитивно — js/shared/utils.js был в единице).
    Замечание Заказчика 2026-11-16: сайдбар — отдельный модуль
    StudentSidebar.vue, ФИО/«Выйти» — wiring внутри компонента."""
    return "\n".join([
        cabinet_html(),
        APP.read_text(encoding="utf-8"),
        SIDEBAR.read_text(encoding="utf-8"),
        UTILS.read_text(encoding="utf-8"),
    ])


# --- FR-19.1: «Главная» = ИИ-чат по новым макетам (перевод гардов 19.3.4) ----


def test_cab_page_exists_and_marker_texts():
    """Готовность 19.3.4 (FR-19.1, TC-S19-WEB-001 статическая нога): файл
    существует; дословные тексты/маркеры «Главной»-чата из утвержденных
    макетов присутствуют (приветствие, подсказка, плейсхолдер, «Скоро»,
    футер, бренд сайдбара); удаленные по решению Заказчика 2026-11-18
    элементы (.greet/.assistant/.quick/.services-title/.tiles, тег
    «В КАБИНЕТЕ») — носители absence (в разметке страницы их НЕТ)."""
    html = cabinet_source()
    for marker in (
        "<title>СберАвтошкола — Кабинет ученика (мокап)</title>",
        "<em>Сбер</em>Автошкола",  # бренд — только в сайдбаре (BUG-059)
        '<div class="ai-hello">Добрый день!</div>',
        '<div class="ai-hello-sub">Спроси что угодно про обучение, экзамен или ПДД — помогу подготовиться</div>',
        'placeholder="Спроси что угодно про обучение, экзамен или ПДД..."',
        '<span class="ai-soon">Скоро</span>',  # FR-19.7
        'aria-label="Вложения — скоро"',
        'aria-label="Ассистент печатает"',  # NFR: ожидание не молча
        '<footer><span>СберАвтошкола · кабинет ученика</span><span>Спринт 1 · визуал</span></footer>',
        "Выйти",
    ):
        assert marker in html, marker
    # удаленные элементы «Главной» (решение Заказчика 2026-11-18) — absence:
    # фрагменты РАЗМЕТКИ не встречаются нигде в единице страницы
    # (включая wiring-модули; комментарии без этих дословных фрагментов)
    for absent in (
        '<div class="greet">ЛИЧНЫЙ КАБИНЕТ',
        '<section class="assistant">',
        '<div class="ai-head"><div class="avatar">',
        '<div class="quick">',
        '<div class="services-title">',
        '<div class="tiles">',
        'id="tile-instructor"',
        'id="tile-requests"',
        "В КАБИНЕТЕ",
        "Когда экзамен?",
        "Мой прогресс",
        "Готов ли я",
        "Гига ГАИшник",
        "Твой AI-помощник в обучении и на дороге",
        "Заглушка: сервис появится в следующем спринте",
        # BUG-059/060 (решение Заказчика 2026-11-06): инвариант сохраняется —
        # дубля логотипа в шапке контента нет, крошки нет
        '<div class="brand">',
        "Личный кабинет · Ученик",
    ):
        assert absent not in html, absent


def test_cab_page_structure_matches_mockup_verbatim():
    """FR-19.1/FR-19.2 (TC-S19-WEB-001): фрагменты «Главной» перенесены
    дословно из утвержденных макетов — разметка приветствия/композера
    (тексты и SVG — посимвольно, ПАРАМИ «макет ↔ страница»: классы чата
    ai-* против макетных hello/spark), CSS-значения — парами «фрагмент
    макета ↔ фрагмент styles.css» (база = home-chat-web.html >760px,
    переопределения ≤760px = mobile-home-chat.html; перенос адаптированный,
    значения сверяются дословно — design.md «Решение 4»: «фрагменты
    дословно»). Разделы ВНЕ «Главной» и оболочка страницы (hero/frame,
    футер, сайдбар) остались на мокапе cabinet-student.html — их вербатим-
    фрагменты и whole-line CSS-гард сохранены БЕЗ ослаблений; вербатим-
    фрагмент плиток ЗАМЕНЕН носителем absence (решение Заказчика
    2026-11-18, дословно: «Да, убираем все кнопки с этого экрана и оставь
    только гигагаишника. Не только в могилке, но и на веб версии тоже»)."""
    html = cabinet_source()
    sidebar = SIDEBAR.read_text(encoding="utf-8")
    mockup = MOCKUP.read_text(encoding="utf-8")
    mockup_mobile = MOCKUP_MOBILE.read_text(encoding="utf-8")
    mockup_web = MOCKUP_WEB.read_text(encoding="utf-8")

    # оболочка страницы и футер — как в мокапе кабинета (вне «Главной»)
    fragments = [
        "<!doctype html>",
        '<html lang="ru">',
        "<title>СберАвтошкола — Кабинет ученика (мокап)</title>",
        '<div class="hero"><div class="frame">',
        '<footer><span>СберАвтошкола · кабинет ученика</span><span>Спринт 1 · визуал</span></footer>',
    ]
    for fragment in fragments:
        assert fragment in html, fragment
        assert fragment in mockup, f"фрагмент не из мокапа: {fragment}"

    # --- «Главная»: разметка чата дословно из ОБОИХ новых макетов ----------
    # общие фрагменты SVG (посимвольно в мобильном и веб-макетах и на
    # странице — классы у контейнеров отличаются, содержимое дословно)
    chat_common = [
        'viewBox="0 0 24 24" fill="none" stroke="#3ddc84" stroke-width="1.6" stroke-linecap="round">',
        '<path d="M12 2v6M12 16v6M2 12h6M16 12h6"/>',
        '<path d="M4.9 4.9l4.2 4.2M14.9 14.9l4.2 4.2M19.1 4.9l-4.2 4.2M9.1 14.9l-4.2 4.2"/>',
        '<path d="M12 5v14M5 12h14"/>',
        'stroke="#9aa39d" stroke-width="2"',
        '<path d="M12 19V5"/>',
        '<path d="M5 12l7-7 7 7"/>',
        'stroke="#0a130e" stroke-width="2.4"',
    ]
    for fragment in chat_common:
        assert fragment in mockup_mobile, f"фрагмент не из мокапа (мобилка): {fragment}"
        assert fragment in mockup_web, f"фрагмент не из мокапа (веб): {fragment}"
        assert fragment in html, fragment

    # тексты — дословно (пары: класс макета ↔ класс чата страницы)
    chat_pairs = [
        ('<div class="hello">Добрый день!</div>',
         '<div class="ai-hello">Добрый день!</div>'),
        ('<div class="hello-sub">Спроси что угодно про обучение, экзамен или ПДД — помогу подготовиться</div>',
         '<div class="ai-hello-sub">Спроси что угодно про обучение, экзамен или ПДД — помогу подготовиться</div>'),
        ('<div class="placeholder">Спроси что угодно про обучение, экзамен или ПДД...</div>',
         'placeholder="Спроси что угодно про обучение, экзамен или ПДД..."'),
    ]
    for mock_frag, page_frag in chat_pairs:
        for mockup_text in (mockup_mobile, mockup_web):
            assert mock_frag in mockup_text, mock_frag
        assert page_frag in html, page_frag

    # --- «Главная»: CSS-значения дословно (пары «макет ↔ styles.css») ------
    page_css = STYLES.read_text(encoding="utf-8")
    css_pairs = [
        # база (>760px) — home-chat-web.html ↔ корневые правила ai-*
        ("width: 76px; height: 76px;", "width:76px;height:76px"),      # .spark
        ("font-size: 44px;", "font-size:44px;"),                       # .hello
        ("max-width: 480px;", "max-width:480px"),                      # .hello-sub
        ("width: 760px;", "width:760px"),                              # .composer
        ("max-width: calc(100% - 96px);", "max-width:calc(100% - 96px)"),
        ("border-radius: 32px;", "border-radius:32px;"),               # .input-box
        ("padding: 22px 14px 14px 26px;", "padding:22px 14px 14px 26px;"),
        ("gap: 18px;", "gap:18px;"),
        ("box-shadow: 0 24px 60px", "box-shadow:0 24px 60px"),
        ("width: 48px; height: 48px;", "width:48px;height:48px"),      # .plus-btn
        ("width: 54px; height: 54px;", "width:54px;height:54px"),      # .send
        ("--green: #3ddc84;", "background:#3ddc84;"),
        # мобилка (≤760px) — mobile-home-chat.html ↔ @media-переопределения
        ("width: 64px; height: 64px;", "width:64px;height:64px"),      # .spark
        ("font-size: 30px;", "font-size:30px;"),                       # .hello
        ("max-width: 280px;", "max-width:280px"),                      # .hello-sub
        ("border-radius: 28px;", "border-radius:28px;"),               # .input-box
        ("padding: 18px 10px 12px 20px;", "padding:18px 10px 12px 20px;"),
        ("width: 44px; height: 44px;", "width:44px;height:44px"),      # .plus-btn
    ]
    for mock_frag, css_frag in css_pairs:
        source = mockup_mobile if mock_frag in mockup_mobile else mockup_web
        assert mock_frag in source, f"CSS-фрагмент не из макета: {mock_frag}"
        assert mock_frag in mockup_mobile or mock_frag in mockup_web, mock_frag
        assert css_frag in page_css, f"CSS-значение макета изменено/удалено: {css_frag}"

    # сайдбар: мокап-фрагменты — в мокапе, компонентные — в модуле 1:1
    side_fragments = [
        ('<aside class="side">', '<aside class="side">'),
        ('<div class="side-brand"><span class="check">✓</span><div><em>Сбер</em>Автошкола<small>Кабинет ученика</small></div></div>',
         '<div class="side-brand"><span class="check">✓</span><div><em>Сбер</em>Автошкола<small>Кабинет ученика</small></div></div>'),
        ('<div class="side-user"><span class="uname">Иван Иванов</span><button class="logout">Выйти</button></div>',
         '<div class="side-user"><span class="uname">{{ uname }}</span><button class="logout" type="button" @click="logout">Выйти</button></div>'),
    ]
    for mock_frag, comp_frag in side_fragments:
        assert mock_frag in mockup, mock_frag
        assert comp_frag in sidebar, comp_frag

    # все CSS-правила мокапа кабинета — дословно (разделы ВНЕ «Главной»;
    # носитель — styles.css страницы каркаса, перенос 1:1 из легаси).
    # Замечание Заказчика 2026-11-16: CSS-строки САЙДБАРА (.side*/.snav*)
    # переехали в модуль StudentSidebar.vue (scoped, 1:1) — сверяются с ним.
    mockup_css = mockup.split("<style>", 1)[1].split("</style>", 1)[0]
    for line in mockup_css.splitlines():
        if not line.strip():
            continue
        if line.lstrip().startswith((".side", ".snav")):
            assert line in sidebar, f"CSS-строка мокапа (сайдбар) изменена/удалена в StudentSidebar.vue: {line[:60]}"
        else:
            assert line in page_css, f"CSS-строка мокапа изменена/удалена: {line[:60]}"


def test_cab_page_removes_stub_tiles_and_dead_wiring():
    """FR-19.1 (негатив, CHK-3; решение Заказчика 2026-11-18 — замена
    носителя test_cab_page_keeps_mockup_stub_alert): быстрые кнопки и блок
    «СЕРВИСЫ» удалены ВМЕСТЕ со ставшим мертвым wiring заглушек
    (arch-review 002 MIN-3 — alert-обработчики .tile/.quick button/.send
    удалены, чтобы вербатим-гарды не считали его живым). Живой wiring
    «Главной» — только чат: #ai-input/#ai-send/#ai-plus."""
    html = cabinet_source()
    assert "Заглушка: сервис появится в следующем спринте" not in html
    assert "alert(" not in html  # заглушечного JS больше нет
    for dead in ('<div class="tiles">', '<div class="quick">', '<section class="assistant">'):
        assert dead not in html, dead
    # живые якоря композера на месте (wiring отправки — e2e TC-S19-WEB-002)
    for anchor in ('id="ai-input"', 'id="ai-send"', 'id="ai-plus"'):
        assert anchor in html, anchor


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
    """FR-5: 200 → подстановка ФИО: uname = «{surname} {name} {patronymic}»
    (wiring ВНУТРИ StudentSidebar.vue: fioOf из vue/src/shared/utils.js,
    реактивный uname), greet = «Добро пожаловать, {name}!» — App.vue по
    событию @me сайдбара (sdd §10.3)."""
    src = cabinet_source()
    assert "surname" in src and "name" in src and "patronymic" in src
    assert "Добро пожаловать, " in src
    assert "uname.value = fio" in src
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
