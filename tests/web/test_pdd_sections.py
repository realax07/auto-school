"""Гард-тесты обучающих секций кабинета ПДД (Спринт 17, change
add-pdd-learning, задачи 17.3.2/17.4.2 — прецедент test_cabinet_page.py).

Секции «Знаки» (#/pdd-signs) и «Правила» (#/pdd-rules) переносят
классы/структуру/стили СОГЛАСОВАННЫХ мокапов design/mocks/pdd-znaki-
student.html и pdd-pravila-student.html (источник дизайна). Носители:
- CABINET = frontend/vue/cabinet.html (скелет sec-pdd-* + 4 кнопки .snav);
- APP = src/pages/cabinet/App.vue (navTo/hash/visited, разметка синхронна);
- SIGNS/RULES = sections/PddSigns.vue, PddRules.vue (динамические списки);
- STYLES = src/pages/cabinet/styles.css (стили мокапов — дословно,
  новые правила только добавлены в конце — design-guard);
- МОКАПЫ — БЕЗ ПРАВОК (design.md «Стратегия вербатим-мокапов»).

Иллюстративные данные мокапов НЕ переносятся как данные: toc правил —
26 пунктов по корпусу (мокап-29 — иллюстрация, proposal «Сверка»),
счетчики групп знаков — из корпуса (совпадают с мокапом: 47/13/38/24/
63/37/22/77 = 321).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CABINET = ROOT / "frontend" / "vue" / "cabinet.html"
APP = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "App.vue"
SIGNS = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "sections" / "PddSigns.vue"
RULES = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "sections" / "PddRules.vue"
STYLES = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "styles.css"
MOCKUP_SIGNS = ROOT / "design" / "mocks" / "pdd-znaki-student.html"
MOCKUP_RULES = ROOT / "design" / "mocks" / "pdd-pravila-student.html"
CORPUS_ZNAKI = ROOT / "content" / "pdd" / "znaki"
CORPUS_PRAVILA = ROOT / "content" / "pdd" / "pravila"


def cabinet_html() -> str:
    return CABINET.read_text(encoding="utf-8")


def app_source() -> str:
    return APP.read_text(encoding="utf-8")


def signs_source() -> str:
    return SIGNS.read_text(encoding="utf-8")


def mockup_css(mockup: Path) -> list[str]:
    text = mockup.read_text(encoding="utf-8")
    block = text.rsplit("<style>", 1)[1].split("</style>", 1)[0]
    return [line for line in block.splitlines() if line.strip()]


def corpus_group_counts() -> list[int]:
    """Число знаков в группах t1…t8 по корпусу (оба формата заголовков
    `## N.N` и `## | N.N` — t8)."""
    counts = []
    for i in range(1, 9):
        md = next((CORPUS_ZNAKI).glob(f"t{i}_*.md"))
        headings = re.findall(r"^##\s+\|?\s*\d+(?:\.\d+)*\s*$", md.read_text(encoding="utf-8"), re.M)
        counts.append(len(headings))
    return counts


def corpus_chapter_count() -> int:
    return len(list(CORPUS_PRAVILA.glob("*.md")))


# --- 17.3: сайдбар/хеши/скелеты (общий блок интеграции) ----------------------


def test_pdd_sidebar_buttons_after_wallet_in_both_carriers():
    """4 кнопки .snav после «Кошелек» (без перегруппировки существующих) —
    в обоих носителях разметки."""
    buttons = [
        '<button data-tab="Знаки" type="button"><span class="ico">◈</span>Знаки</button>',
        '<button data-tab="Правила" type="button"><span class="ico">☰</span>Правила</button>',
        '<button data-tab="Билеты" type="button"><span class="ico">◉</span>Билеты</button>',
        '<button data-tab="Штрафы" type="button"><span class="ico">⚠</span>Штрафы</button>',
    ]
    for carrier in (cabinet_html(), app_source()):
        wallet_pos = carrier.index('<button data-tab="Кошелек"')
        for b in buttons:
            pos = carrier.index(b)
            assert pos > wallet_pos, f"кнопка не после «Кошелек»: {b}"


def test_pdd_hashes_and_navto_wiring():
    """navTo/hash-паттерн design «Интеграция»: is-цепочка, wantHash-тернарник,
    начальные проверки хешей (прецедент #/my-requests/#/wallet)."""
    src = app_source()
    for tab, hash_ in (
        ("Знаки", "#/pdd-signs"),
        ("Правила", "#/pdd-rules"),
        ("Билеты", "#/pdd-tickets"),
        ("Штрафы", "#/pdd-fines"),
    ):
        assert f"(name === '{tab}')" in src, tab
        assert hash_ in src, hash_
        assert f"if (location.hash === '{hash_}') navTo('{tab}')" in src, hash_
    assert "history.replaceState" in src


def test_pdd_signs_skeleton_sync_in_both_carriers():
    """Скелет sec-pdd-signs (page-head «Обучение · ПДД» / «Дорожные знаки»)
    синхронен в cabinet.html и App.vue; div#sec-pdd-signs display:none
    (динамический <pdd-signs> — только в App.vue, прецедент sec-requests)."""
    fragment = (
        '<div id="sec-pdd-signs" style="display:none">\n'
        '  <div class="page-head">\n'
        '    <div>\n'
        '      <div class="kicker">Обучение · ПДД</div>\n'
        '      <h1>Дорожные знаки</h1>\n'
        '      <p>8 групп · 321 знак с описаниями. Выбери группу — внутри карточки знаков и их значение.</p>\n'
        '    </div>\n'
        '  </div>'
    )
    assert fragment in cabinet_html()
    assert fragment in app_source()


def test_pdd_signs_visited_async_component():
    """defineAsyncComponent + visited-загрузка (NFR-26): чанк грузится при
    первом открытии, остается смонтированным."""
    src = app_source()
    assert "defineAsyncComponent" in src
    assert "import('./sections/PddSigns.vue')" in src
    assert '<pdd-signs v-if="pddSignsVisited"></pdd-signs>' in src


# --- 17.3: секция «Знаки» по мокапу pdd-znaki-student.html -------------------


def test_pdd_signs_mockup_fragments_in_component():
    """Фрагменты мокапа (chips/zn-grid/zn-detail классы, структура карточки
    и детали) — в носителе PddSigns.vue."""
    src = signs_source()
    fragments = [
        '<div class="chips"',
        'class="chip"',
        '<div class="zn-grid"',
        'class="zn"',
        'loading="lazy"',
        '<figcaption><b>{{ s.number }}</b> {{ s.name }}</figcaption>',
        '<div v-if="selected" class="zn-detail"',
        '<div class="zd-head">',
        '<div class="kicker">Знак {{ selected.number }}</div>',
    ]
    for fragment in fragments:
        assert fragment in src, fragment


def test_pdd_signs_fine_conditional_render():
    """Блок штрафа — УСЛОВНЫЙ рендер по корпусу (fine 166/321): при
    отсутствии записи блок не рендерится (design «Решение 4»); desc пуст
    у 5.33.1/5.34.1 — блок описания тоже условный."""
    src = signs_source()
    assert '<div v-if="selected.fine" class="fine"' in src
    assert '<p v-if="selected.desc"' in src
    assert '← назад к группе' in src  # возврат к группе


def test_pdd_signs_counters_match_corpus_and_mockup():
    """Счётчики чипов — из корпуса: 8 групп, 47/13/38/24/63/37/22/77 = 321
    (совпадают с мокапом; spec «Группы и счётчики соответствуют корпусу»)."""
    counts = corpus_group_counts()
    assert counts == [47, 13, 38, 24, 63, 37, 22, 77]
    assert sum(counts) == 321
    mockup = MOCKUP_SIGNS.read_text(encoding="utf-8")
    for i, n in enumerate(counts, start=1):
        # мокап-чип: «Предупреждающие <b>47</b>» и т.д. (иллюстрация тех же фактов)
        assert re.search(rf"<b>{n}</b>", mockup), f"группа t{i}: {n} нет в мокапе"


def test_pdd_signs_mockup_css_verbatim_in_styles():
    """CSS-строки секции мокапа — дословно в styles.css (прецедент
    test_cabinet_page: вербатим CSS, новые правила только в конце)."""
    page_css = STYLES.read_text(encoding="utf-8")
    for line in mockup_css(MOCKUP_SIGNS):
        assert line in page_css, f"CSS-строка мокапа изменена/удалена: {line[:60]}"


def test_pdd_signs_images_via_pdd_assets():
    """Изображения — /pdd-assets/znaki/<номер>small.png (вне бандла,
    задача 17.2.2): путь приходит из pdd-znaki.json генератора — компонент
    НЕ ссылается на content/ и не импортирует ассеты изображений."""
    src = signs_source()
    assert 'content/pdd' not in src.replace('content/pdd/правится', '')
    assert ':src="s.image"' in src
    assert '<img :src="selected.image"' in src
    # 48 МБ не в бандле: данные — из pdd-data (генератор), не из content/
    assert "pdd-data/pdd-znaki.json" in src


# --- 17.4: секция «Правила» по мокапу pdd-pravila-student.html ---------------


def rules_source() -> str:
    return RULES.read_text(encoding="utf-8")


def test_pdd_rules_skeleton_sync_in_both_carriers():
    """Скелет sec-pdd-rules (page-head «Обучение · ПДД» / «Правила дорожного
    движения») синхронен в cabinet.html и App.vue."""
    fragment = (
        '<div id="sec-pdd-rules" style="display:none">\n'
        '  <div class="page-head">\n'
        '    <div>\n'
        '      <div class="kicker">Обучение · ПДД</div>\n'
        '      <h1>Правила дорожного движения</h1>\n'
        '      <p>26 глав действующей редакции. Глава раскрывается по клику; пункты — полный текст.</p>\n'
        '    </div>\n'
        '  </div>'
    )
    assert fragment in cabinet_html()
    assert fragment in app_source()


def test_pdd_rules_mockup_fragments_in_component():
    """Фрагменты мокапа (two-column prav-wrap: toc/toc-item/chapter) — в
    носителе PddRules.vue; переход по toc — клиентский (без перезагрузки),
    активный toc-item подсвечен."""
    src = rules_source()
    fragments = [
        'class="prav-wrap"',
        'class="toc"',
        'class="toc-item"',
        ':class="{ on: c.id === activeId }"',
        '@click="openChapter(c.id)"',
        'class="chapter"',
        '<h2>{{ activeChapter.title }}</h2>',
    ]
    for fragment in fragments:
        assert fragment in src, fragment


def test_pdd_rules_toc_count_is_corpus_26():
    """Число глав toc = 26 ПО КОРПУСУ (мокап-29 — иллюстрация, proposal
    «Сверка»); рендер — v-for по pdd-pravila.json генератора."""
    assert corpus_chapter_count() == 26
    src = rules_source()
    assert 'v-for="c in chapters"' in src
    assert "pdd-data/pdd-pravila.json" in src
    # первая глава рендерится по умолчанию (мокап начинает с активной главы)
    assert "activeId: pravilaData.length ? pravilaData[0].id : 1" in src


def test_pdd_rules_v_html_only_for_generated_blocks():
    """v-html — ТОЛЬКО для сгенерированных полей корпуса (экранирование на
    этапе генерации); сырых md-строк и пользовательского ввода нет."""
    src = rules_source()
    assert 'v-html="activeHtml"' in src
    # activeHtml — join сгенерированных <p>-блоков JSON, не сырой текст md
    assert "activeChapter.html.join" in src


def test_pdd_rules_mockup_css_verbatim_in_styles():
    """CSS-строки секции мокапа — дословно в styles.css (новые правила —
    только в конце файла)."""
    page_css = STYLES.read_text(encoding="utf-8")
    for line in mockup_css(MOCKUP_RULES):
        assert line in page_css, f"CSS-строка мокапа изменена/удалена: {line[:60]}"


def test_pdd_rules_visited_async_component():
    """PddRules — lazy-чанк: defineAsyncComponent + visited-загрузка."""
    src = app_source()
    assert "import('./sections/PddRules.vue')" in src
    assert '<pdd-rules v-if="pddRulesVisited"></pdd-rules>' in src
