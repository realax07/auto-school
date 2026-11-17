"""Спринт 18 (change add-mobile-adaptive) — носитель «mobile-tabbar».

Мокапы design/mocks/mobile/*.html (v3, согласованы Заказчиком 2026-11-17 —
«Давай реализуем»): фиксированный таб-бар снизу с пятью разделами (Главная,
Записи, Обучение, Кошелек, Профиль; высота 54px ≤ 64px спеки
mobile-adaptive) ТОЛЬКО на мобильных ширинах ≤760px — двойная защита:
JS matchMedia('(max-width:760px)') в MobileTabBar.vue + CSS-страховка
@media(min-width:761px){.mtabs{display:none!important}}. Desktop-сайдбар
ученика на ≤760px скрыт (media в styles.css кабинета, задача 18.1.2) —
заменяется таб-баром; ширины >760px не меняются (носители e2e 84 защищают).

Канонический модуль — src/components/MobileTabBar.vue (паттерн
StudentSidebar): SVG-иконки дословно из мокапов (mobile-home.html,
строка .tabs), шиты «Обучение» (4 раздела ПДД)/«Профиль» (ФИО + «Выйти») —
bottom-sheet с grab-хендлом; wiring учетки самодостаточен внутри
компонента (GET /api/auth/me с X-Session-Token, POST /api/auth/logout —
FR-5/FR-7/FR-8). Страницы-носители ПОДКЛЮЧАЮТ компонент и НЕ дублируют
разметку:
- src/pages/cabinet/App.vue — <mobile-tab-bar :active-tab="curTab"
  @tab="navTo"> (SPA-механика кабинета без изменений);
- src/pages/instructor-choice/App.vue — <mobile-tab-bar
  active-tab="Выбрать инструктора">;
- cabinet.html / instructor-choice.html — pre-boot БЕЗ таб-бара
  (компонент появляется после гидрации; matchMedia гасит его на desktop).

Трассировка (rule 6): функциональные кликовые сценарии — e2e
TC-UI-077 (вход→кабинет→табы→модалки, 390×844) и desktop-инвариант
TC-UI-079 (1440×900, регресс BUG-070) — кейсы
test-model/new/add-mobile-adaptive/; этот носитель закрепляет структуру
и wiring компонента для тех же требований дельты
specs/mobile-adaptive/spec.md.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VUE = ROOT / "frontend" / "vue"
SRC = VUE / "src" / "pages"
TABBAR = VUE / "src" / "components" / "MobileTabBar.vue"
MOCK_HOME = ROOT / "design" / "mocks" / "mobile" / "mobile-home.html"

# канонические 5 разделов спеки mobile-adaptive (мокапы v3: .tab/.tab.on)
TABS = ["Главная", "Записи", "Обучение", "Кошелек", "Профиль"]
# шит «Обучение» — все разделы ПДД С17 доступны с одной кнопки
EDU_ITEMS = ["Знаки", "Правила", "Билеты", "Штрафы"]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def tabbar_template() -> str:
    return read(TABBAR).split("<template>", 1)[1].split("</template>", 1)[0]


def mock_tab_paths() -> list[str]:
    """d="…" пути SVG-иконок из .tabs мокапа mobile-home.html (источник
    дизайна; в компоненте мокап-разметка повторена дословно, кроме
    stroke="None" → stroke="currentColor")."""
    mock = read(MOCK_HOME)
    tabs_html = mock.split('<div class="tabs">', 1)[1].split("</div>", 1)[0]
    return re.findall(r'<path d="([^"]+)"', tabs_html)


def test_mtabs_five_tabs_canonical_in_component():
    """Таб-бар — ровно 5 кнопок с подписями спеки (порядок мокапа v3);
    у каждой — SVG-иконка; шиты «Обучение»/«Профиль» открывает
    таб-бар (отдельные страниц-дублей нет)."""
    nav = tabbar_template().split('<nav v-if="visible"', 1)[1].split("</nav>", 1)[0]
    labels = re.findall(r"<span>([^<]+)</span>", nav)
    assert labels == TABS, labels
    assert nav.count("<button") == 5
    assert nav.count("<svg") == 5


def test_mtabs_icons_verbatim_from_mobile_mock():
    """SVG-иконки — дословно из мокапа mobile-home.html (каждый path d="…"
    мокапа присутствует в компоненте, порядок сохранен)."""
    src = read(TABBAR)
    component_paths = re.findall(r'<path d="([^"]+)"', src)
    mock_paths = mock_tab_paths()
    assert len(mock_paths) == 7  # 5 иконок: 2+1+2+1+1 (rect/circle — не path)
    pos = -1
    for d in mock_paths:
        pos = component_paths.index(d, pos + 1)  # порядок как в мокапе
    assert pos >= 0


def test_mtabs_mobile_only_matchmedia_and_css_guard():
    """Показ ТОЛЬКО ≤760px — двойная защита: matchMedia('(max-width:760px)')
    (задача 18.1.1) + CSS-страховка @media(min-width:761px){.mtabs
    {display:none!important}}; высота таб-бара 54px ≤ 64px спеки."""
    src = read(TABBAR)
    assert "matchMedia('(max-width:760px)')" in src
    assert "@media(min-width:761px){.mtabs{display:none!important}}" in src
    assert ".mtabs{position:fixed;left:0;right:0;bottom:0;z-index:60;height:54px" in src


def test_mtabs_setup_bindings_exposed():
    """BUG-068-регресс: все вызываемые из шаблона функции (`openTab` на 4
    табах, `openProfile`, `closeSheet`, `pickEdu`, `logout`) — в возвращаемом
    объекте setup (иначе клики падают TypeError в рантайме, сборка это не
    ловит)."""
    src = read(TABBAR)
    ret = src.split("return {", 1)[1].split("};", 1)[0]
    for fn in ("openTab", "openProfile", "closeSheet", "pickEdu", "logout"):
        assert f"{fn}: {fn}" in ret, fn


def test_mtabs_sheets_edu_profile_and_wiring_self_contained():
    """Шиты — bottom-sheet с grab-хендлом: «Обучение» — 4 раздела ПДД
    (сохранение действий desktop-сайдбара), «Профиль» — ФИО + «Выйти»;
    wiring учетки внутри компонента (GET /api/auth/me с X-Session-Token —
    FR-5, лениво при первом открытии; 401/403/!ok → toLogin — FR-7;
    «Выйти» — POST /api/auth/logout → clearSession → главная — FR-8)."""
    src = read(TABBAR)
    assert "sheet = 'edu'" in src and "'profile'" in src
    assert '.grab{width:38px;height:4px' in src
    assert ".mtab-backdrop{position:fixed;inset:0" in src
    for name in EDU_ITEMS:
        assert f"tab: '{name}'" in src, name
    assert "/api/auth/me" in src and "/api/auth/logout" in src
    assert "X-Session-Token" in src and "getToken" in src
    assert "toLogin" in src and "clearSession" in src
    assert "location.href = '/'" in src


def test_cabinet_integrates_tabbar_sidebar_hidden_le760():
    """Кабинет: <mobile-tab-bar :active-tab="curTab" @tab="navTo"> (SPA-emit —
    механика разделов/хешей не меняется); pre-boot cabinet.html БЕЗ
    .mtabs; media ≤760px в styles.css прячет desktop-сайдбар (aside.side)
    и резервирует место под таб-баром (.frame снизу 88px ≥ 54px)."""
    app = read(SRC / "cabinet" / "App.vue")
    assert '<mobile-tab-bar :active-tab="curTab" @tab="navTo">' in app
    assert app.count("<mobile-tab-bar") == 1
    preboot = read(VUE / "cabinet.html")
    assert "mtabs" not in preboot and "mtab" not in preboot
    css = read(SRC / "cabinet" / "styles.css")
    assert "@media(max-width:760px){\n  aside.side{display:none}" in css
    assert ".frame{padding:26px 16px 88px}" in css


def test_instructor_choice_integrates_tabbar_without_duplicate():
    """«Выбрать инструктора»: <mobile-tab-bar active-tab="Выбрать
    инструктора"> — активен домик (мокап mobile-choice.html .tab on);
    pre-boot instructor-choice.html БЕЗ таб-бара."""
    app = read(SRC / "instructor-choice" / "App.vue")
    assert '<mobile-tab-bar active-tab="Выбрать инструктора">' in app
    assert app.count("<mobile-tab-bar") == 1
    preboot = read(VUE / "instructor-choice.html")
    assert "mtabs" not in preboot and "mtab" not in preboot


def test_mtabs_single_source_across_repo():
    """Разметка таб-бара физически в одном модуле: класс-маркер .mtabs
    встречается в vue-носителях только в MobileTabBar.vue (стили — scoped
    в компоненте; styles.css кабинета таб-бар не дублирует)."""
    carriers = list(VUE.glob("*.html")) + list((VUE / "src").rglob("*.vue")) \
        + list((VUE / "src").rglob("*.css"))
    hits = sorted(str(p.relative_to(ROOT)) for p in carriers
                  if ".mtabs" in read(p))
    assert hits == ["frontend/vue/src/components/MobileTabBar.vue"], hits
