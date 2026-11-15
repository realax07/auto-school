# Покрытие: add-pdd-learning — TC-S17-001…008

Дельта: `openspec/changes/add-pdd-learning/specs/` — NEW-кейпабилити
learning (8 требований). Сверка состава партии: в директиве QA-партии
дельта названа «8 Requirements / 26 сценариев»; ФАКТ по spec.md —
**29 сценариев** (`#### Scenario:` = 29: сайдбар 4, знаки 6, правила 2,
билеты 5, штрафы 3, доставка 3, целостность 3, бюджеты 3). «26/26» в
tasks.md 17.1.1/17.7.4 — это `openspec validate --all --strict`
(26 items; подтверждено прогоном на ветке: 26 passed, 0 failed), а не
счёт сценариев. Покрытие полное: **29/29** — кейс либо группа кейсов на
каждый сценарий; вся поведенческая автоматизация уже существует (принцип
Н5) — кейсы фиксируют трассировку «сценарий спеки → автоматизация /
ручной остаток», НОВЫХ тестов партия QA не заводит.

Якоря автоматизации партии (владельцы S17-сценариев):

- unit ПДД 15: `tests/unit/test_pdd_generator.py` (14 — прогон
  генератора как subprocess на реальном корпусе: 80×20/один ✅/2–5
  вариантов, whitelist изображений 1094, 8 групп/321/small.png, join
  по title биективен 321/321, допуски desc 5.33.1/5.34.1 и fine 166,
  26 глав с одним H1, shtrafi 58×3 поля, идемпотентность байт-в-байт,
  манифест, НЕГАТИВ — сборка падает на недостающей картинке) +
  `tests/unit/test_pdd_tickets_logic.py` (1 — чистая логика тренажёра:
  таймер 20:00/авто-финиш timeUp, фиксация однократная fixAnswer,
  статусы/счёт);
- web 67: в т.ч. `tests/web/test_pdd_sections.py` (31 гард-тест по
  СОГЛАСОВАННЫМ мокапам design/mocks/pdd-*.html — прецедент
  test_cabinet_page.py: фрагменты/CSS-строки дословно, скелеты синхронно
  в обоих носителях, 9 пунктов .snav, 4 хеша, счётчики = корпус, toc =
  корпус-26, штрафы 58 = корпус, conditional fine/desc, lazy-visited,
  роут /pdd-assets 200/404-гварды на endpoint);
- e2e 84 (`tests/web/test_ui_playwright.py`): +8 сценариев S17 —
  TC-UI-070 (сайдбар/хеши/reload), TC-UI-070a (хеш напрямую), TC-UI-071
  (знаки группа→деталь→назад, допуски 1.18/5.33.1, t8), TC-UI-072
  (правила toc→глава без reload), TC-UI-073 (статика live:
  200/media-type, 404 группа/суффикс/traversal), TC-UI-074 (тренажёр:
  таймер тикает, фиксация однократная, подсветка+пояснение, q-nav,
  счёт, итог), TC-UI-075 (штрафы 58 строк/поиск/пустой результат),
  TC-UI-076 (Билеты/Штрафы табы, 9 пунктов); существующие 76 e2e не
  переписывались (NFR-27);
- контракт 5 (`tests/test_container_contract.py`) — зеленые на
  Dockerfile с `COPY content/` (builder-стейдж для npm run build —
  CR MAJ-1; рантайм-стейдж рядом с frontend/); гейт сборки образа —
  CI job docker-build на PR (локальный docker build невыполним в среде
  агента — BUG-064, OPEN);
- гейт сборки/бюджетов (Node, не pytest): `npm run build &&
  npm run check:budgets` — green (а)–(д) на ветке: vendor 0.4/4.0 КБ;
  первый заход cabinet = 42.3 КБ gzip ≤ 200 (все 14 страниц — по
  СТАТИЧЕСКОМУ замыканию); чужих page-чанков нет; lazy-чанки ≤ 150 КБ
  каждый (PddSigns 46.0, PddRules 45.6, PddTickets 3.4, PddFines 3.5,
  pdd-bilety-<cat>-<nn> 4.1–5.2, index 0.5, logic 0.4); lazy-чанки вне
  статических замыканий 14 страниц; генератор: «OK — 26 глав,
  8 групп / 321 знаков (fine: 166), 58 строк штрафов, 80×20».

Прогоны на HEAD 49663a9 (feat/s17-pdd-learning) при утверждении партии:
не-браузерный набор (unit 37 + web 67 + api 362 + контракт 5) —
**471 passed** (539.8s); `npm run build && npm run check:budgets` —
green (а)–(д), лог в Партии; `openspec validate --all --strict` —
26 passed / 0 failed; полный e2e 84 — см. свод прогонов ниже.

Обозначения: Spe = specs/learning (единственная дельта партии; другие
спеки не правятся — Frontend/NFR-26 остается истинным, containerization
COPY content/ не нарушает «Образ приложения»).

| Кейс | Сценарии спеки | Автоматизация |
|---|---|---|
| TC-S17-001 | Spe «Разделы сайдбара»: все 4 («Открытие раздела из сайдбара», «Хеш открывает раздел напрямую», «Существующие разделы не сломаны», «Сайдбар из 9 пунктов прокручивается») | test_pdd_sections: sidebar_buttons_after_wallet_in_both_carriers, snav_nine_items_order, hashes_and_navto_wiring, four_hashes_bootstrap_in_app, four_section_skeletons_in_both_carriers; e2e TC-UI-070 (клик→секция/on/хеш/взаимоисключающе/reload), TC-UI-070a, TC-UI-076; регресс «не сломаны»: test_cabinet_page.py (7) и сценарии кабинета e2e (регистрация→кабинет, BUG-047, TC-UI-059/060/061) без правок + api test_integration_sprint1 (кабинет маркеры); прокрутка .snav — CSS-факт (cabinet/styles.css:288, конец CSS-блока мокапа, `.snav{overflow-y:auto}`) + ручная проба |
| TC-S17-002 | Spe «Знаки»: все 6 («Группы и счётчики соответствуют корпусу», «Сетка карточек группы», «Деталь знака», «Деталь знака без записи штрафа», «Деталь с пустым описанием (допуск 5.33.1/5.34.1)», «Знак группы «Таблички» (формат t8)») | e2e TC-UI-071 (8 чипов, 47/77, сетка 47 карточек src=/pdd-assets/znaki/1.1small.png, деталь 1.1 desc+fine, назад, 1.18 без fine-блока, 5.33.1 без desc-блока, t8: 77 карточек + 8.1.1small.png); гарды test_pdd_sections: signs_counters_match_corpus_and_mockup (== [47,13,38,24,63,37,22,77]=321 по корпусу и мокапу), signs_fine_conditional_render (v-if fine/desc + «назад»), signs_mockup_fragments/CSS_verbatim, signs_images_via_pdd_assets, signs_skeleton_sync, signs_visited_async; состав данных — unit генератора (см. TC-S17-007) |
| TC-S17-003 | Spe «Правила»: все 2 («Оглавление из 26 глав», «Переход к главе») | e2e TC-UI-072 (toc=26, глава 1 по умолчанию on, клик 13 → «13. Проезд перекрестков» + «13.1» без перезагрузки — window-маркер, подсветка перешла); гарды: rules_toc_count_is_corpus_26 (26 файлов корпуса, v-for по pdd-pravila.json), rules_mockup_fragments (prav-wrap/toc/toc-item/chapter, `:class on`, @click), rules_v_html_only_for_generated_blocks, rules_mockup_css_verbatim, rules_skeleton_sync, rules_visited_async; заголовки — unit test_pravila_26_chapters_with_title_and_html + chapter10_title_from_corpus_h1; мокап-29 — иллюстрация (proposal «Сверка») |
| TC-S17-004 | Spe «Билеты» (тренажёр): все 5 («Старт попытки по билету с картинками», «Фиксация ответа и пояснение», «Навигация со статусами и досрочная сдача», «Авто-финиш по таймеру», «Состояние не переживает перезагрузку (MVP)») | e2e TC-UI-074 (выбор 40+40, exam-bar «Билет 1», таймер MM:SS тикает −1, «Вопрос 1 из 20», верный ответ → ans good + «Верный» + «Пояснение», повторный клик не меняет/счёт не растет, qn done-g cur + 20 точек, q2 картинка /pdd-assets/bilety loading=lazy, «Сдать» → «2 из 20»/«Не отвечено: 18», «Пройти снова» с нуля, «Выбрать другой билет»); unit test_pdd_logic_pure_functions_harness (fmtClock/decClock/timeUp — 20:00 и авто-финиш; isAnswered/fixAnswer — однократная; statusesOf/scoreOf); гард tickets_auto_states_from_logic_module (wiring логики в компоненте) + tickets_data_sharded_per_ticket_chunk (abm=40/cd=40, чанк на билет) + mockup-фрагменты/CSS + skeleton + lazy_visited; «MVP-перезагрузка» — конструктив (нет API/записей) + ручная проба; «00:00» естественный — ручной (тик и timeUp автоматизированы) |
| TC-S17-005 | Spe «Штрафы»: все 3 («Таблица всех строк корпуса», «Поиск фильтрует клиентски», «Пустой результат поиска») | e2e TC-UI-075 (58 tr = строкам pdd-shtrafi.json=корпусу, заголовки «Пункт КоАП/Нарушение/Наказание», поиск «ПЕШЕХОД» → число строк по независимому пересчёту корпуса без учета регистра, без перезагрузки, «запрос-xyz» → заглушка «Ничего не найдено по запросу», очистка → 58, reload сохраняет); гарды: fines_table_renders_all_corpus_rows (len JSON == corpus == 58, поля article/violation/penalty, filterFines из pdd-logic.mjs), fines_mockup_fragments (search/v-model/заголовки/заглушка), fines_mockup_css_verbatim, fines_skeleton_sync, fines_lazy_visited; факт корпуса — unit test_shtrafi_rows_three_fields; «63 vs 58» — зафиксировано в proposal «Сверка» |
| TC-S17-006 | Spe «Доставка контента»: все 3 («Сборка воспроизводит контент без ручных шагов», «Изображения вне бандла», «Раздел грузится лениво») | unit test_rerun_is_byte_identical + manifest_counts_match_outputs + bilety_abm_01_question_texts_from_corpus (генератор идемпотентен, выход = корпусу); роут: test_pdd_assets_route_200_media_types (png/jpeg media-type по явной карте) + test_pdd_assets_route_404_guards (other/.txt/../app.py/.hidden/no-file → 404) на endpoint create_app(); e2e TC-UI-073 — то же на ЖИВОМ сервере; «вне бандла»: signs_images_via_pdd_assets (пути из JSON, ассеты не импортируются) + факт dist/assets (0 изображений); «лениво»: visited_async-гарды ×4 + правило (д) check:budgets (lazy вне замыканий 14 страниц); pdd-data/ в .gitignore (:240); регресс контейнера — контракт 5 на Dockerfile с COPY content/ (builder — CR MAJ-1, рантайм); ручные: docker build (CI job docker-build, BUG-064), сетевая проба «до клика нет pdd-запросов» |
| TC-S17-007 | Spe «Целостность контента»: все 3 («Сборка падает на недостающем изображении», «Сборка падает на неожиданной пустоте desc или номере вне group-md», «Позитивный прогон на текущем корпусе») | unit test_pdd_generator.py: НЕГАТИВ test_build_fails_on_missing_ticket_image (symlink-копия корпуса → exit≠0 с указанием файла/вопроса, dist не собирается); ПОЗИТИВ — полный набор гейтов на реальном корпусе: bilety_80_tickets_20_questions_one_correct, bilety_image_links_exist_whitelist (1094), znaki_8_groups_and_321_signs, znaki_images_exist_whitelist (small.png, t8), znaki_join_by_title_number_bijective (321/321 в обе стороны), znaki_desc_empty_only_allowed_numbers (только 5.33.1/5.34.1), znaki_fine_optional_166, pravila_26_chapters (один H1), shtrafi_rows_three_fields (58×3); fail-гейты desc/join в коде генератора (строки fail()) — негативная проба испорченной znaki-details.json через PDD_CONTENT_DIR — ручная (автоматизирован один негатив — прецедент «минимального негатива» tasks 17.7.2a) |
| TC-S17-008 | Spe «Производительность (NFR-26)»: все 3 («Первый заход кабинета не изменился», «Каждый lazy-чанк в бюджете», «Гард срабатывает при распухании») | командный гейт npm run build && npm run check:budgets (amendment 17.2.3: статическое замыкание, PAGES=14, роль lazy, правила (а)–(д)) — green на ветке: cabinet первый заход 42.3 КБ gzip ≤ 200, vendor ≤ 150, чужих page-чанков нет, lazy ≤ 150 (максимум PddSigns 46.0 КБ), lazy вне замыканий; pytest-гарды паттерна: tickets_data_sharded_per_ticket_chunk (билеты не слипаются — чанк на билет), visited_async ×4; негатив «распухание» — ручная проба на копии dist (exit≠0 с диагностикой чанка/правила; механика asserts — код-факт) |

Свод по автоматизации партии: новых автотестов партия QA НЕ добавляет.
Нумерация: approved-ID партии — TC-S17-001…008; e2e-носители носят
плановые ID TC-UI-070…076 в docstring (rule 6; 070a — в имени носителя
test_tc_ui_070a_pdd_hash_opens_section_directly, docstring — прецедент
BUG-047) — соответствие зафиксировано в колонке «Автоматизация» и в
кейсах (прецедент add-wallet-economy TC-S16-001…008 vs TC-S16-011…041).

Ручные остатки (свод; выполняются на приемке/гейте):
- прокрутка .snav в окне низкой высоты (CSS-строка-факт в styles.css);
- естественный 20-минутный таймер тренажёра до 00:00 (тик −1 и
  авто-финиш timeUp автоматизированы) и «reload посреди попытки → экран
  выбора, серверных записей нет» (конструктив: новых API нет);
- негатив целостности «пустой desc вне {5.33.1, 5.34.1} / номер вне
  group-md» (fail-гейты в коде генератора; автоматизирован один
  негатив — недостающее изображение);
- сетевая проба «до первого клика pdd-* чанки не запрашиваются»
  (машинно закрыто правилом (д): lazy вне статических замыканий);
- негатив бюджета «чанк распух» (ручная проба на копии dist);
- docker build/Docker-стенд — CI job docker-build на PR (BUG-064, OPEN),
  контрактные тесты контейнера — статические, зеленые.

Прогоны партии (подтверждение при утверждении): HEAD 49663a9,
не-браузерный набор 471 passed (unit 37 + web 67 + api 362 + контракт 5;
лог Партии, 539.8s); build + check:budgets green (а)–(д) с фактами
чанков выше; openspec validate --all --strict — 26 passed / 0 failed;
полный e2e test_ui_playwright.py — **84 passed** (198.2s; в т.ч. 8 новых
сценариев S17 TC-UI-070/070a/071/072/073/074/075/076 — зелёные на HEAD). Сверка счётчиков корпуса
с дельтой: 8 групп = 47/13/38/24/63/37/22/77 = 321 ✓; toc = 26 ✓;
штрафы = 58 ✓; билеты 2×40×20 ✓; znaki-details: 321 запись, desc
319/321 (пусты 5.33.1/5.34.1 — допуск), fine 166/321 ✓ (генератор
«OK», log Партии).
