"""Спринт 18 (change add-mobile-adaptive) — QA-automation J66: носители
медиа-компоновки ≤760px (кейсы партии TC-S18-001…008, approved 8/8 —
test-model/approved/add-mobile-adaptive/, review-001-cases.md; конвенция
S16 — TC-ID в docstring каждого теста, образец
tests/api/test_qa_s16_money.py).

Принцип «не дублировать носители»: кликовые сценарии уже покрыты
носителями волн 18.1–18.4 — TC-S18-ID разметка внесена в docstring
tests/web/test_mobile_tabbar.py и мобильных тестов
tests/web/test_ui_playwright.py (TC-UI-077/078/079 + top-bar initials +
geometry). МАШИННО НЕ ПОКРЫТЫМИ остались факты media-компоновки
cabinet/styles.css (≤760px), названные в coverage.md якорями, но не
имеющие pytest-носителя: «История кошелька» — одноколоночные карточки
вместо таблиц (TC-S18-002), «Слоты недели» — полоса дней со слотами
списком (TC-S18-003), ПДД-разделы 18.3.1 — chips/знаки 2 колонки/штрафы-
карточки (TC-S18-006). Этот файл закрывает дельту: source-гварды
дословных CSS-фактов (прецедент test_mobile_tabbar.py) + живая
компоновка 390×844 (фикстуры из test_ui_playwright.py).

Карта «кейс → носитель» (сверка с coverage.md / review-001-cases.md):
- TC-S18-001: test_mobile_tabbar.py (8 тестов, TC-S18-ID в docstring),
  TC-UI-077, test_mobile_topbar_initials_visible, geometry-тест,
  test_sidebar_unified.py (5) — покрыт, нового носителя не требует;
- TC-S18-002: geometry (.wal-btn/.act ≥44 на данных), TC-UI-077
  (#sec-wallet, пополнение) + НОВОЕ ЗДЕСЬ: карточки плиток/заявок/истории
  кошелька (source-гвард + live 390 на данных);
- TC-S18-003: TC-UI-077 (#sec-bookings + хеш), TC-UI-079 (desktop-инвариант)
  + НОВОЕ ЗДЕСЬ: неделя-полоса source-гвард, вкл. гарант bk-act ≥44px
  (styles.css, формулировка замечания 3 review-001 — live-замер bk-act
  «при наличии данных», ручной остаток приемки);
- TC-S18-004: TC-UI-077 (вход/пополнение/профиль — bottom-sheet, регресс
  BUG-069) + test_mobile_tabbar::sheets_edu_profile_and_wiring — покрыт;
- TC-S18-005: test_mobile_tabbar::cabinet_integrates (.frame 84px),
  geometry (choice pad 20..30, sticky mtop MAJ-3), TC-UI-079 — покрыт;
- TC-S18-006: TC-UI-078 (тренажер live 390), test_pdd_sections (31),
  unit test_pdd_tickets_logic/test_pdd_generator + НОВОЕ ЗДЕСЬ:
  знаки 2 колонки / штрафы-карточки / chips-лента (source-гвард + live 390 —
  мобайл-сторона инварианта TC-UI-079);
- TC-S18-007: geometry (scrollWidth choice ≤390 с изоляцией storage+reload,
  pad 20..30), test_mobile_tabbar (интеграция choice, single source) —
  покрыт; scrollWidth-инвариант админки — ручной остаток приемки
  (coverage.md, кандидат следующего мобайл-носителя админ-партии);
- TC-S18-008: TC-UI-079, медиа-носители «дифф = 0» (test_cabinet_page (7),
  test_pdd_sections (31), test_sidebar_unified (5)),
  test_mobile_tabbar::mobile_only_matchmedia_and_css_guard — покрыт.

Ручные остатки приемки (coverage.md) — визуальная сверка с мокапами,
живые данные полосы дней, блюр фона, 20-минутный таймер, скрин-сравнение
desktop «до/после» — здесь не автоматизируются.

Запуск live-части требует LD_LIBRARY_PATH с каталогом системных
библиотек браузера Playwright (см. шапку test_ui_playwright.py).
"""
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect  # noqa: E402

from test_ui_playwright import (  # noqa: E402
    _mobile_page,
    _student_token,
    api,
    browser,
    server,
)

ROOT = Path(__file__).resolve().parents[2]
CAB_CSS = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "styles.css"


# ------------------------------------------------- source-гварды (18.2/18.3)
def test_qa_s18_wallet_requests_tiles_media_guard():
    """TC-S18-002 («История кошелька на 390px» — одноколоночные карточки
    вместо таблиц): дословные факты media-блоков styles.css 18.2.1/18.2.2/
    18.2.4 — плитки «Главной» 1fr (:442), заявки-карточки + .act 44px
    (:465/:469), кошелек — wal-table→grid-карточки: thead скрыт, tbody
    grid, tr — карточка, переупорядочивание td (тип→сумма→описание→дата)
    и .wal-btn 44px (:509-520) — без горизонтального скролла.
    Живая компоновка на данных — test_qa_s18_mobile_cards_live_390."""
    css = CAB_CSS.read_text(encoding="utf-8")
    for fact in (
        ".tiles{grid-template-columns:1fr;gap:13px}",
        ".req{padding:14px;border-radius:15px}",
        ".act{flex:1 1 auto;padding:13px 16px;min-height:44px !important;font-size:12.5px}",
        ".wal-actions .wal-btn{flex:1 1 auto;padding:13px 16px;min-height:44px !important}",
        ".wal-table{display:block}",
        ".wal-table thead{display:none}",
        ".wal-table tbody{display:grid;gap:10px}",
        ".wal-table td.wal-amount{order:2;text-align:right;font-size:14px}",
        ".wal-table td.wal-when{order:4;grid-column:1/-1;white-space:normal;font-size:11px}",
    ):
        assert fact in css, fact


def test_qa_s18_week_slots_strip_media_guard():
    """TC-S18-003 («Слоты недели на 390px» — календарь-полоса недель
    бронирования): дословные факты media-блока 18.2.3 styles.css — bk-nav
    wrap (:479), bk-grid flex-полоса дней (:480), corner/tlabel скрыты
    (:481), слоты вертикальным списком min-height:44px (:486), пустые
    ячейки матрицы скрыты (:487), подпись слота видима (:488), состояния
    «свободно — тап для брони»/«занято»/«ваш запрос» (:490-492), bk-act
    min-height:44px (:499 — гарант ≥44px по замечанию 3 review-001;
    live-замер bk-act — ручной остаток приемки «при наличии данных»)."""
    css = CAB_CSS.read_text(encoding="utf-8")
    for fact in (
        ".bk-nav{flex-wrap:wrap}",
        ".bk-grid{display:flex;flex-wrap:wrap;gap:6px}",
        ".bk-corner,.bk-tlabel{display:none}",
        ".bk-slot{flex:1 1 100%;height:auto;min-height:44px;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 14px;font-size:12px;text-align:left}",
        ".bk-slot.off{display:none}",
        ".bk-slot .bk-slot-lab{display:inline;font-weight:650}",
        '.bk-slot.free:after{content:"свободно — тап для брони"}',
        '.bk-slot.taken:after{content:"занято"}',
        '.bk-slot.mine:after{content:"ваш запрос"}',
        ".bk-actions .bk-act{flex:1 1 auto;padding:13px 16px;min-height:44px !important}",
    ):
        assert fact in css, fact


def test_qa_s18_pdd_sections_media_guard():
    """TC-S18-006 («Тренажер на 390px» — разделы ПДД адаптивны без
    изменения логики): дословные факты media-блока 18.3.1 styles.css —
    лента групп знаков chips nowrap/overflow-x (:558), сетка знаков 2
    колонки (:561), штрафы — карточки вместо таблицы: .fines block,
    thead скрыт, tbody grid (:591-593). Навигатор билетов 10 колонок и
    exam-bar wrap НЕ дублируем — live-носитель TC-UI-078
    (test_ui_playwright.py::test_s18_mobile_tickets_trainer_grid_390),
    desktop-инвариант — TC-UI-079."""
    css = CAB_CSS.read_text(encoding="utf-8")
    for fact in (
        ".chips{flex-wrap:nowrap;overflow-x:auto;gap:7px;padding-bottom:10px;margin-bottom:16px;scrollbar-width:none}",
        ".zn-grid{grid-template-columns:1fr 1fr;gap:10px}",
        ".fines{display:block;max-width:none}",
        ".fines thead{display:none}",
        ".fines tbody{display:grid;gap:10px}",
    ):
        assert fact in css, fact


# ------------------------------------------------------------ live 390×844
def test_qa_s18_mobile_cards_live_390(browser, server):
    """TC-S18-002/006 (live 390×844, реальный бэкенд): media-компоновка
    РЕАЛЬНО применяется на данных — 18.2.1: плитки «Главной» одной
    колонкой; 18.2.4: история кошелька карточками вместо таблицы (после
    API-пополнения: thead скрыт, tbody grid, tr — rounded-карточка, сумма
    справа order:2); 18.3.1: сетка знаков ровно 2 колонки (мобайл-сторона
    инварианта TC-UI-079 — на 1440×900 там >2) и таблица штрафов —
    карточки (thead скрыт). Изоляция — свежий контекст _mobile_page на
    тест (паттерн TC-UI-077/078)."""
    token = _student_token(server)
    status, data = api("POST", "/api/wallet/topup", base=server, token=token,
                       body={"amount_kop": 300000})
    assert status == 200 and data and data["ok"], (status, data)

    page, ctx = _mobile_page(browser, token)
    try:
        page.goto(f"{server}/cabinet")
        expect(page.locator(".mtabs")).to_be_visible()
        expect(page.locator("#sec-home")).to_be_visible()

        # 18.2.1: плитки «Главной» — одна колонка на 390px
        assert page.evaluate(
            "getComputedStyle(document.querySelector('.tiles'))"
            ".gridTemplateColumns.split(' ').length") == 1

        # 18.2.4: история кошелька — карточки вместо таблицы (есть 1 topup)
        page.locator(".mtab", has_text="Кошелек").click()
        expect(page.locator("#sec-wallet")).to_be_visible()
        expect(page.locator("#hist .wal-ttype").first).to_have_text("Пополнение")
        assert page.locator("#hist").evaluate(
            "el => getComputedStyle(el.closest('table')"
            ".querySelector('thead')).display") == "none"
        assert page.locator("#hist").evaluate(
            "el => getComputedStyle(el).display") == "grid"
        row = page.locator("#hist tr").first
        assert row.evaluate(
            "el => getComputedStyle(el).display") == "grid"
        radius = row.evaluate("el => getComputedStyle(el).borderTopLeftRadius")
        assert radius not in ("", "0px"), radius  # карточка, не строка таблицы
        assert page.locator("#hist .wal-amount").first.evaluate(
            "el => getComputedStyle(el).order") == "2"

        # 18.3.1: сетка знаков — ровно 2 колонки на мобиле (шит «Обучение»;
        # pickEdu закрывает шит и открывает раздел — повторное открытие чисто)
        page.locator(".mtab", has_text="Обучение").click()
        sheet = page.locator(".mtab-sheet")
        expect(sheet).to_be_visible()
        sheet.locator(".mi", has_text="Знаки").click()
        expect(page.locator("#sec-pdd-signs")).to_be_visible()
        expect(page.locator(".zn-grid")).to_be_visible()
        assert page.evaluate(
            "getComputedStyle(document.querySelector('.zn-grid'))"
            ".gridTemplateColumns.split(' ').length") == 2

        # 18.3.1: штрафы — карточки вместо таблицы (thead скрыт; секция —
        # lazy-чанк: ждём саму таблицу, как в TC-UI-079)
        page.locator(".mtab", has_text="Обучение").click()
        sheet = page.locator(".mtab-sheet")
        expect(sheet).to_be_visible()
        sheet.locator(".mi", has_text="Штрафы").click()
        expect(page.locator("#sec-pdd-fines")).to_be_visible()
        table = page.locator('[data-test="pdd-fines-table"]')
        expect(table).to_be_visible()
        assert table.evaluate(
            "el => getComputedStyle(el.querySelector('thead')).display") == "none"
        assert table.evaluate(
            "el => getComputedStyle(el.querySelector('tbody')).display") == "grid"
    finally:
        ctx.close()
