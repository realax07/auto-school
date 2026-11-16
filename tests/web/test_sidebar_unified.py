"""Замечание Заказчика 2026-11-15 №1 + 2026-11-16: сайдбар ученика — единый
элемент при переходах по разделам/страницам (пропадали новые разделы ПДД
на instructor-choice; затем разметка дублировалась в каждом носителе — на
страницах вне «активного» переноса терялись ФИО и «Выйти», BUG-065).

Носитель канонического списка — ОТДЕЛЬНЫЙ МОДУЛЬ
src/components/StudentSidebar.vue (9 пунктов: 8 data-tab + data-goto
«Выбрать инструктора»; ФИО из GET /api/auth/me и «Выйти» POST
/api/auth/logout — wiring внутри компонента, на любой странице).
Страницы-носители ПОДКЛЮЧАЮТ компонент и НЕ дублируют разметку:

- src/pages/cabinet/App.vue — <student-sidebar :active-tab="curTab"
  @tab="navTo" @me="onMe"> (SPA-кабинет: клик таба — событие компонента);
- src/pages/instructor-choice/App.vue — <student-sidebar
  active-tab="Выбрать инструктора">;
- cabinet.html / instructor-choice.html — pre-boot: ПУСТОЙ
  <aside class="side" aria-hidden="true"></aside> (грид-колонка
  резервируется до гидрации, вспышки/дублей нет).

ПДД-хеши (#/pdd-*) и разделы кабинета (#/my-requests, #/my-bookings,
#/wallet) роутятся App.vue кабинета при загрузке (bootstrap-проверки хешей,
test_pdd_sections.py::test_pdd_four_hashes_bootstrap_in_app, e2e TC-UI-070a).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VUE = ROOT / "frontend" / "vue"
SRC = VUE / "src" / "pages"
SIDEBAR = VUE / "src" / "components" / "StudentSidebar.vue"

# канонический список ученика: (текст, иконка, data-tab / data-goto)
ITEMS = [
    ("Главная", "⌂", "Главная"),
    ("Мои заявки", "✉", "Мои заявки"),
    ("Выбрать инструктора", "▤", "/instructor-choice"),
    ("Мои брони", "◷", "Мои брони"),
    ("Кошелек", "₽", "Кошелек"),
    ("Знаки", "◈", "Знаки"),
    ("Правила", "☰", "Правила"),
    ("Билеты", "◉", "Билеты"),
    ("Штрафы", "⚠", "Штрафы"),
]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_snav_nine_items_canonical_in_component():
    """Канонический список — 9 пунктов в модуле StudentSidebar.vue: порядок
    data-tab/data-goto, иконки, состав (8 кнопок + data-goto)."""
    nav = read(SIDEBAR).split('<nav class="snav">', 1)[1].split("</nav>", 1)[0]
    attrs = re.findall(r'data-(?:tab|goto)="([^"]+)"', nav)
    assert attrs == [value for _, _, value in ITEMS], attrs
    icons = re.findall(r'<span class="ico">([^<]+)</span>', nav)
    assert icons == [ico for _, ico, _ in ITEMS], icons
    assert nav.count("<button") == 9


def test_sidebar_wiring_self_contained():
    """ФИО и «Выйти» — wiring внутри компонента (независимо от страницы):
    GET /api/auth/me с X-Session-Token (FR-5, fioOf; токен — getToken из
    shared/api.js, ключ session_token), 401/403/!ok → toLogin (FR-7);
    «Выйти» — POST /api/auth/logout → clearSession → главная (FR-8)."""
    src = read(SIDEBAR)
    api_js = read(VUE / "src" / "shared" / "api.js")
    assert "/api/auth/me" in src and "/api/auth/logout" in src
    assert "X-Session-Token" in src and "getToken" in src
    assert "session_token" in api_js and "clearSession" in api_js
    assert "toLogin" in src
    assert "fioOf" in src and "uname.value = fio" in src
    assert "clearSession" in src


def test_cabinet_uses_component_without_duplicate():
    """Кабинет: <student-sidebar> с актив-табом и @tab (SPA); pre-boot
    cabinet.html — пустой aside без дублированной разметки .snav."""
    app = read(SRC / "cabinet" / "App.vue")
    assert '<student-sidebar :active-tab="curTab" @tab="navTo" @me="onMe">' in app
    preboot = read(VUE / "cabinet.html")
    assert '<aside class="side" aria-hidden="true"></aside>' in preboot
    assert '<nav class="snav">' not in preboot
    assert "data-tab=" not in preboot


def test_instructor_choice_uses_component_without_duplicate():
    """«Выбрать инструктора»: <student-sidebar active-tab=…>; pre-boot —
    пустой aside, ссылок-дублей нет; активный пункт передан пропом."""
    app = read(SRC / "instructor-choice" / "App.vue")
    assert '<student-sidebar active-tab="Выбрать инструктора">' in app
    preboot = read(VUE / "instructor-choice.html")
    assert '<aside class="side" aria-hidden="true"></aside>' in preboot
    assert '<nav class="snav">' not in preboot
    assert 'href="/cabinet' not in preboot


def test_sidebar_single_source_across_repo():
    """Разметка сайдбара физически в одном модуле: класс-маркер .side-brand
    и список .snav встречаются в vue-носителях только в StudentSidebar.vue."""
    carriers = list(VUE.glob("*.html")) + list((VUE / "src").rglob("*.vue")) \
        + list((VUE / "src").rglob("*.html"))
    hits = sorted(str(p.relative_to(ROOT)) for p in carriers if '.side-brand' in read(p))
    assert hits == ["frontend/vue/src/components/StudentSidebar.vue"], hits
