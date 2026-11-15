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

import pytest

ROOT = Path(__file__).resolve().parents[2]
CABINET = ROOT / "frontend" / "vue" / "cabinet.html"
APP = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "App.vue"
SIGNS = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "sections" / "PddSigns.vue"
RULES = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "sections" / "PddRules.vue"
TICKETS = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "sections" / "PddTickets.vue"
FINES = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "sections" / "PddFines.vue"
LOGIC = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "sections" / "pdd-logic.mjs"
STYLES = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "styles.css"
MOCKUP_SIGNS = ROOT / "design" / "mocks" / "pdd-znaki-student.html"
MOCKUP_RULES = ROOT / "design" / "mocks" / "pdd-pravila-student.html"
MOCKUP_TICKETS = ROOT / "design" / "mocks" / "pdd-bilety-trenazher.html"
MOCKUP_FINES = ROOT / "design" / "mocks" / "pdd-shtrafi-student.html"
CORPUS_ZNAKI = ROOT / "content" / "pdd" / "znaki"
CORPUS_PRAVILA = ROOT / "content" / "pdd" / "pravila"
CORPUS_SHTRAFI = ROOT / "content" / "pdd" / "shtrafi" / "shtrafi-gibdd.md"
CORPUS_BILETY_INDEX = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "pdd-data" / "pdd-bilety-index.json"


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


# --- 17.5: секция «Билеты» — тренажёр по мокапу pdd-bilety-trenazher.html ----


def tickets_source() -> str:
    return TICKETS.read_text(encoding="utf-8")


def corpus_tickets_per_category() -> dict[str, int]:
    """Число билетов в категории по сгенерированному индексу (корпус:
    2 категории × 40 билетов × 20 вопросов; генератор 17.2.1)."""
    import json

    index = json.loads(CORPUS_BILETY_INDEX.read_text(encoding="utf-8"))
    counts = {c["id"]: len(c["tickets"]) for c in index["categories"]}
    return counts


def test_pdd_tickets_skeleton_sync_in_both_carriers():
    """Скелет sec-pdd-tickets (page-head «Обучение · ПДД» / «Билеты ПДД —
    тренажер», подпись мокапа) синхронен в cabinet.html и App.vue."""
    fragment = (
        '<div id="sec-pdd-tickets" style="display:none">\n'
        '  <div class="page-head">\n'
        '    <div>\n'
        '      <div class="kicker">Обучение · ПДД</div>\n'
        '      <h1>Билеты ПДД — тренажер</h1>\n'
        '      <p>Режим экзамена: 20 вопросов, 20 минут. Картинки вопросов — как на реальном экзамене ГИБДД.</p>\n'
        '    </div>\n'
        '  </div>'
    )
    assert fragment in cabinet_html()
    assert fragment in app_source()


def test_pdd_tickets_mockup_fragments_in_component():
    """Фрагменты мокапа (экзамен-бар/timer/score, q-card/q-num/q-text/q-img/
    answers/ans/tag/tip, q-nav/qn со статусами done-g/done-r/cur) — в
    носителе PddTickets.vue; картинка вопроса — native lazy."""
    src = tickets_source()
    fragments = [
        'class="exam-bar"',
        'class="exam-meta"',
        'class="timer"',
        'class="score"',
        'class="q-card"',
        'class="q-num"',
        'class="q-text"',
        'class="q-img"',
        'alt="ситуация вопроса"',
        'loading="lazy"',
        'class="answers"',
        'class="ans"',
        'class="tag">Верный</span>',
        'class="tip"',
        '<b>Пояснение:</b>',
        'class="q-nav"',
        'class="qn"',
        ':class="[st, { cur: i === cur }]"',
        '{{ i + 1 }}',
    ]
    for fragment in fragments:
        assert fragment in src, fragment


def test_pdd_tickets_mockup_css_verbatim_in_styles():
    """CSS-строки секции мокапа — дословно в styles.css (новые правила —
    только в конце файла)."""
    page_css = STYLES.read_text(encoding="utf-8")
    for line in mockup_css(MOCKUP_TICKETS):
        assert line in page_css, f"CSS-строка мокапа изменена/удалена: {line[:60]}"


def test_pdd_tickets_lazy_component_and_visited():
    """PddTickets — lazy-чанк: defineAsyncComponent + visited-загрузка
    (NFR-26); выбор/тренировка/результат — внутри чанка."""
    src = app_source()
    assert "import('./sections/PddTickets.vue')" in src
    assert '<pdd-tickets v-if="pddTicketsVisited"></pdd-tickets>' in src
    assert "if (isTickets) pddTicketsVisited.value = true;" in src


def test_pdd_tickets_auto_states_from_logic_module():
    """Чистая арифметика тренажёра — в pdd-logic.mjs (unit-носитель
    tests/unit/test_pdd_tickets_logic.py), НЕ дублируется в компоненте:
    часы fmtClock/decClock/timeUp, фиксация isAnswered/fixAnswer,
    статусы/счёт statusesOf/scoreOf."""
    logic = LOGIC.read_text(encoding="utf-8")
    for fragment in (
        "export function fmtClock",
        "export function decClock",
        "export function timeUp",
        "export function isAnswered",
        "export function fixAnswer",
        "export function answerStatus",
        "export function statusesOf",
        "export function scoreOf",
    ):
        assert fragment in logic, fragment
    src = tickets_source()
    for fragment in (
        "from './pdd-logic.mjs'",
        "if (isAnswered(this.picked[this.cur])) return;",
        "fixAnswer(this.picked[this.cur], choice)",
        "decClock(self.clock)",
        "timeUp(self.clock)",
        "statusesOf(this.questions, this.picked)",
        "scoreOf(this.statuses)",
    ):
        assert fragment in src, fragment


def test_pdd_tickets_data_sharded_per_ticket_chunk():
    """Шардинг ПО БИЛЕТУ (design «Бюджеты», правило (г)): JSON билета —
    lazy-чанк на билет (import.meta.glob), индекс — static import;
    категории/билеты — по корпусу (2 × 40)."""
    assert "import.meta.glob('../pdd-data/pdd-bilety-*.json')" in tickets_source()
    assert "'../pdd-data/pdd-bilety-' + id + '.json'" in tickets_source()
    assert "pdd-data/pdd-bilety-index.json" in tickets_source()
    counts = corpus_tickets_per_category()
    assert counts == {"abm": 40, "cd": 40}


# --- 17.6: секция «Штрафы» по мокапу pdd-shtrafi-student.html ---------------


def fines_source() -> str:
    return FINES.read_text(encoding="utf-8")


def corpus_shtrafi_rows() -> int:
    """Число строк таблицы корпуса (tab-строки после заголовка «Пункт
    КоАП»; факт: 58 — мокап-63 иллюстративен, proposal «Сверка»)."""
    lines = [
        ln for ln in CORPUS_SHTRAFI.read_text(encoding="utf-8").splitlines()
        if ln.count("\t") >= 2
    ]
    return len(lines) - 1  # минус строка заголовка


def test_pdd_fines_skeleton_sync_in_both_carriers():
    """Скелет sec-pdd-fines (page-head «Обучение · ПДД» / «Штрафы ГИБДД»)
    синхронен в cabinet.html и App.vue."""
    fragment = (
        '<div id="sec-pdd-fines" style="display:none">\n'
        '  <div class="page-head">\n'
        '    <div>\n'
        '      <div class="kicker">Обучение · ПДД</div>\n'
        '      <h1>Штрафы ГИБДД</h1>\n'
        '      <p>Таблица нарушений главы 12 КоАП: статья, нарушение, наказание. Поиск — по любой колонке, без перезагрузки.</p>\n'
        '    </div>\n'
        '  </div>'
    )
    assert fragment in cabinet_html()
    assert fragment in app_source()


def test_pdd_fines_mockup_fragments_in_component():
    """Фрагменты мокапа (search + fines-таблица) — в носителе PddFines.vue;
    поиск — клиентский (v-model), без перезагрузки; пустой результат —
    строка-заглушка. Заголовок первого столбца — «Пункт КоАП» (tasks.md
    17.6.1 / design «Решение 6», как в источнике; «Статья» мокапа —
    иллюстрация)."""
    src = fines_source()
    fragments = [
        'class="search"',
        'v-model="query"',
        'placeholder="Поиск по статье или нарушению… (например: скорость, переезд, пешеход)"',
        'class="fines"',
        '<th>Пункт КоАП</th>',
        '<th>Нарушение</th>',
        '<th>Наказание</th>',
        'Ничего не найдено по запросу',
    ]
    for fragment in fragments:
        assert fragment in src, fragment


def test_pdd_fines_mockup_css_verbatim_in_styles():
    """CSS-строки секции мокапа — дословно в styles.css (новые правила —
    только в конце файла)."""
    page_css = STYLES.read_text(encoding="utf-8")
    for line in mockup_css(MOCKUP_FINES):
        assert line in page_css, f"CSS-строка мокапа изменена/удалена: {line[:60]}"


def test_pdd_fines_lazy_component_and_visited():
    """PddFines — lazy-чанк: defineAsyncComponent + visited-загрузка."""
    src = app_source()
    assert "import('./sections/PddFines.vue')" in src
    assert '<pdd-fines v-if="pddFinesVisited"></pdd-fines>' in src
    assert "if (isFines) pddFinesVisited.value = true;" in src


def test_pdd_fines_table_renders_all_corpus_rows():
    """Таблица — ВСЕ строки pdd-shtrafi.json (число = строкам tab-таблицы
    корпуса; сейчас 58); фильтр — чистая функция filterFines из
    pdd-logic.mjs (поиск по трем колонкам, без учета регистра)."""
    import json

    data = json.loads(
        (ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "pdd-data" / "pdd-shtrafi.json")
        .read_text(encoding="utf-8")
    )
    assert len(data) == corpus_shtrafi_rows() == 58
    for row in data:
        assert set(row) == {"article", "violation", "penalty"}
    src = fines_source()
    assert "pdd-data/pdd-shtrafi.json" in src
    assert "filterFines(this.rows, this.query)" in src
    logic = LOGIC.read_text(encoding="utf-8")
    assert "export function filterFines" in logic


# --- 17.7: приемка — консолидация носителей + интеграция ---------------------


def test_pdd_four_section_skeletons_in_both_carriers():
    """Консолидация (17.7.1): все 4 обучающих секции — скелеты в ОБОИХ
    носителях (кабинет.html синхронен App.vue), компоненты — только в
    App.vue (прецедент sec-requests)."""
    sections = [
        ("sec-pdd-signs", "Дорожные знаки"),
        ("sec-pdd-rules", "Правила дорожного движения"),
        ("sec-pdd-tickets", "Билеты ПДД — тренажер"),
        ("sec-pdd-fines", "Штрафы ГИБДД"),
    ]
    for sec_id, h1 in sections:
        for carrier in (cabinet_html(), app_source()):
            assert f'<div id="{sec_id}" style="display:none">' in carrier, sec_id
            assert f"<h1>{h1}</h1>" in carrier, sec_id
        assert 'style="display:none">' in app_source()  # статические скелеты


def test_pdd_snav_nine_items_order():
    """Сайдбар — 9 пунктов (design «Решение 3»): 8 data-tab + data-goto;
    обучающие ПДД — после «Кошелек» в порядке Знаки→Правила→Билеты→Штрафы
    (без перегруппировки существующих)."""
    for carrier in (cabinet_html(), app_source()):
        nav = carrier.split('<nav class="snav">')[1].split("</nav>")[0]
        buttons = re.findall(r'data-(?:tab|goto)="([^"]+)"', nav)
        assert buttons == [
            "Главная", "Мои заявки", "/instructor-choice", "Мои брони",
            "Кошелек", "Знаки", "Правила", "Билеты", "Штрафы",
        ], buttons


def test_pdd_four_hashes_bootstrap_in_app():
    """4 хеша открывают разделы напрямую (прецедент BUG-047: хвост старых
    ссылок) — начальные проверки хешей в App.vue (полный список)."""
    src = app_source()
    for hash_, tab in (
        ("#/pdd-signs", "Знаки"),
        ("#/pdd-rules", "Правила"),
        ("#/pdd-tickets", "Билеты"),
        ("#/pdd-fines", "Штрафы"),
    ):
        assert f"if (location.hash === '{hash_}') navTo('{tab}');" in src


@pytest.fixture()
def pdd_asset_endpoint(monkeypatch, tmp_path):
    """Эндпоинт /pdd-assets/{{group}}/{{file}} из create_app() — вызов
    напрямую (без HTTP-стека/lifespan; прецедент env-фикстуры
    test_static.py)."""
    import bcrypt

    monkeypatch.setenv("ADMIN_USER", "admin")
    monkeypatch.setenv(
        "ADMIN_PASSWORD_HASH",
        bcrypt.hashpw(b"x", bcrypt.gensalt()).decode(),
    )
    monkeypatch.setenv("SECRET", "test-secret")
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(tmp_path / "app.db"))
    from fastapi import HTTPException

    from backend.app import create_app

    app = create_app()
    route = next(
        r for r in app.routes
        if getattr(r, "path", "") == "/pdd-assets/{group}/{file}"
    )
    endpoint = route.endpoint
    return endpoint


def test_pdd_assets_route_200_media_types(pdd_asset_endpoint):
    """/pdd-assets: реальные файлы корпуса — 200 с корректным media-type
    по явной карте (.png/.jpg; роут 17.2.2, ADR-001)."""
    resp = pdd_asset_endpoint(group="znaki", file="1.1small.png")
    assert resp.media_type == "image/png"
    from pathlib import Path as _Path

    assert _Path(resp.path).is_file()
    resp = pdd_asset_endpoint(group="bilety", file="6942508s.jpg")
    assert resp.media_type == "image/jpeg"
    assert _Path(resp.path).is_file()


def test_pdd_assets_route_404_guards(pdd_asset_endpoint):
    """/pdd-assets: чужая группа / неизвестный суффикс / traversal /
    отсутствующий файл — 404 (угадывание не вводится; e2e-зеркало
    TC-UI-073)."""
    from fastapi import HTTPException

    for group, file in (
        ("other", "1.1small.png"),      # группа не znaki|bilety
        ("znaki", "1.1small.txt"),      # неизвестный суффикс
        ("znaki", "../app.py"),         # traversal
        ("znaki", ".hidden.png"),       # скрытый файл
        ("znaki", "no-such-file.png"),  # нет файла
    ):
        with pytest.raises(HTTPException) as exc_info:
            pdd_asset_endpoint(group=group, file=file)
        assert exc_info.value.status_code == 404, (group, file)
