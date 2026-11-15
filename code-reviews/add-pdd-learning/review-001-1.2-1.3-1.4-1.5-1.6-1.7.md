<!-- Reviewer-Delegation: deleg-s17-dev-external | независимый код-ревьюер (не автор диффа) | дифф: 6dabdee..HEAD (17 коммитов, волны 17.2–17.7) | ветка: feat/s17-pdd-learning | дата: 2026-11-15 -->

# Code review: партия add-pdd-learning — задачи 1.2, 1.3, 1.4, 1.5, 1.6, 1.7 (генератор/статика/секции/бюджеты/носители/приемка)

Периметр: dev-дифф 6dabdee..HEAD (23 файла, +2827/−39): build-time генератор
`generate-pdd-json.mjs` + шаг `npm run build` (1.2), роут `/pdd-assets` +
Dockerfile COPY content/ (1.3), amendment check-budgets (1.4)/README корпуса
(1.5), секции «Знаки»/«Правила»/«Билеты»/«Штрафы» с ленивыми чанками и
гард/e2e-тестами (1.6), приемка 17.7: карта/BUG-064/гейты (1.7). Мокапы
design/mocks/pdd-*.html СОГЛАСОВАНЫ Заказчиком — в диффе НЕ тронуты
(последнее касание 70a45b2, до базы ревью); znaki-details.json не менялся
после 15649d4 (проверено `git diff 15649d4..HEAD`). СА+арх approve в истории
(9f104dd, 6dabdee) — дизайн-уровень не ре-ревьюится.

## Вердикт: return (MAJ-1)

Пункт 1.3 закрыт наполовину: COPY content/ корректен в runtime-стейдже, но
сборка образа СЛОМАНА — frontend-builder выполняет `npm run build`, который
теперь начинается с генератора, требующего content/pdd, а corpus в builder-стейдж
не копируется. `docker build` (и CI job `docker-build`, flow.yml:141–156,
`docker compose build app`) падает на `RUN npm run build` — воспроизведено
локально на точной копии layout стейджа (ниже). Это роняет приемку 17.7.4 и
связку BUG-064 («CI docker-build — действующий гейт» — гейт будет красным).
Остальные приоритеты (генератор-гейты, статика-гварды, тренажер, мокапы,
бюджеты, носители) — проверены по коду и прогонами, замечаний уровня MAJ нет;
три MIN и один process-note.

## 1. Генератор (1.2) — гейты/join/whitelist/детерминизм: зелен

- Join-правило сверено с кодом: номер парсится из title
  (`/^Знак\s+(\d+(?:\.\d+)*)\b/`, generate-pdd-json.mjs:200), группа — ТОЛЬКО
  из group-md (long/img записей details игнорируются, :219), биекция номеров
  в ОБЕ стороны (:221–226). Unit: test_znaki_join_by_title_number_bijective,
  test_znaki_8_groups_and_321_signs (47/13/38/24/63/37/22/77 = 321) — зеленые.
- Гейты-допуски: desc пуст ТОЛЬКО 5.33.1/5.34.1 — гейт генератора
  (:49, :213–215) + тест test_znaki_desc_empty_only_allowed_numbers; fine
  опционален (166/321, пустой → null → блок не рендерится)
  test_znaki_fine_optional_166. Whitelist картинок: инвентарь строится ТОЛЬКО
  по ссылкам `../images/bilety/*` из .md (:254–287); crawl-артефакт
  `none_gray.jpg?` (файл реально есть на диске, ссылок в .md нет — проверено
  grep по корпусу) в выдачу НЕ попадает:
  test_bilety_image_links_exist_whitelist (`"?" not in image`,
  `not any("none_gray" …)` + unreferenced больше referenced) — зелен.
- Детерминизм: сортировки глав по числовому префиксу (:88–92), вопросов по
  _qn (:306), порядок тикетов — цикл abm/cd×1..40; Set/Map-итерации с
  фиксированным порядком вставки. test_rerun_is_byte_identical (sha256
  всех 86 файлов двух прогонов) — зелен.
- pdd-data в git НЕ коммитится: .gitignore:240
  `frontend/vue/src/pages/cabinet/pdd-data/` (git check-ignore подтверждает).
- Ручных правок контента нет: README корпуса (1.5) факт-точен
  (8 групп/321, details 321/166 fine/2 пустых desc, 58 строк штрафов,
  1292+198 images), расходится с фактом ни в одном проверенном числе.

## 2. Статика /pdd-assets (1.3) — гварды: зелен; Dockerfile: MAJ-1

- backend/app.py:204–227: группа whitelist (znaki|bilety — остальное 404),
  гварды `"/" in file or ".." in file or file.startswith(".")` — прецедент
  С13 (/js-матрица: ../, %2e%2e, absolute, dot, hidden → 404) выдержан:
  `%2e%2e` декодируется Starlette ДО матчинга → ловится проверкой `..`;
  absolute/`%2f` не матчатся в один сегмент → 404; явная карта media-types
  (.png/.gif/.jpg/.jpeg), неизвестный суффикс — 404; финальный `is_file()`.
  Live-проверка: e2e TC-UI-073 (200+content-type на реальных файлах, 404 на
  traversal/чужой группе/суффиксе) — зелен; unit test_pdd_assets_route_404_guards.
- content-path: `CONTENT_DIR = ROOT_DIR / "content"` (app.py:41) — тот же
  паттерн, что FRONTEND_DIR/VUE_DIST_DIR (конфиг-константы модуля app.py,
  nginx не участвует) — соответствует решению.
- **MAJ-1 (блокер): Dockerfile:18–26 — frontend-builder не имеет corpus.**
  `npm run build` = `node scripts/generate-pdd-json.mjs && vite build`
  (package.json:8); генератор по умолчанию читает
  `REPO_ROOT/content/pdd` (generate-pdd-json.mjs:43–46), а в builder-стейдж
  копируется только `frontend/vue/` (Dockerfile:23–25). `COPY content/
  content/` добавлен только в RUNTIME-стейдж (Dockerfile:54). Воспроизведение
  на точной копии layout стейджа (`/app/frontend/vue` без content/):
  `node scripts/generate-pdd-json.mjs` →
  `ENOENT: scandir '…/app/content/pdd/pravila'`, EXIT=1 → `RUN npm run build`
  падает → `docker build` сломан на этой ветке; CI `docker compose build app`
  (flow.yml:156) будет красным. Фикс (не применяю — ревью): в
  frontend-builder перед `RUN npm run build` добавить `COPY content/
  /app/content/` (или `content/pdd/` + `ENV PDD_CONTENT_DIR=/app/content/pdd`).
  Отметить: build-контекст content/ не исключен .dockerignore — runtime-COPY
  корректен, сломан именно builder.

## 3. Тренажер (1.6, PddTickets.vue + pdd-logic.mjs) — зелен

- Таймер 20:00: EXAM_SECONDS=1200, setInterval 1с, decClock не уходит ниже
  нуля, timeUp → stopTimer+finished (авто-финиш, :171–182); все выходы
  (other/finish/beforeUnmount/startTicket→restartRun) гасят интервал —
  утечек нет. e2e TC-UI-074: формат MM:SS и тик −1с — зелен; unit harness
  (fmtClock/decClock/timeUp сценарий 2→1→0) — зелен.
- Однократная фиксация: `pick` гвардит `isAnswered(picked[cur])` (:191–194) +
  чистая fixAnswer (pdd-logic.mjs:41–43; индекс 0 ≠ «не отвечено» — harness
  покрывает); e2e: повторный клик по другому варианту не меняет подсветку/счет.
- Подсветка good/wrong + tag «Верный» + блок пояснения после ответа
  (ansClass/revealed), q-nav 1–20 со статусами done-g/done-r/cur,
  счёт good/wrong из отвеченных (scoreOf), итог «X из 20» + «Не отвечено»,
  «Пройти снова»/«Выбрать другой билет» — по мокапу; данные из
  pdd-data/bilety/<ticket>.json через import.meta.glob-чанк (:88, :141).
- XSS-гарды: сторонний корпус интерполируется только через `{{ }}`
  (текст/опции/пояснение/строки штрафов/запрос поиска); v-html в партии
  РОВНО один — PddRules.vue:23 для escHtml-блоков генератора (:71–78:
  &<>\"' на этапе сборки, ввода пользователя в секциях нет) — прецедент
  С11/С16 соблюден; img-src — только сгенерированный
  `/pdd-assets/bilety/<файл-по-белому-списку>`.

## 4. Секции vs согласованные мокапы — соответствие зафиксировано

- znaki: чипы 8 групп со счетчиками КОРПУСА (47/13/38/24/63/37/22/77 —
  совпадают с мокапом, test_pdd_signs_counters_match_corpus_and_mockup),
  zn-grid/zn-карточки, zn-detail с kicker/группой; fine-блок — v-if при
  наличии записи (166/321; у 1.18 нет — e2e проверяет отсутствие), desc-блок
  тоже условный (5.33.1 — e2e). CSS мокапа дословно в styles.css
  (гард-тесты всех 4 мокапов) — зелен.
- pravila: two-column prav-wrap (toc слева/глава справа), toc — 26 глав
  КОРПУСА (мокап-29 — иллюстрация; отклонение зафиксировано в шапке
  PddRules.vue:10–12 и tasks.md 17.4.2, гард test_pdd_rules_toc_count_is_corpus_26);
  активный toc-item, переход без перезагрузки (e2e window-маркер).
- shtrafi: поиск-подстрока по 3 колонкам без учета регистра (filterFines,
  unit + e2e) + таблица 58 строк КОРПУСА. Сверка числа: корпус 59
  tab-строк − заголовок = 58 (awk по факту); мокап-63 — иллюстрация
  (5 строк-заглушек источника с «—»; зафиксировано PddFines.vue:7–8,
  test_pdd_fines_table_renders_all_corpus_rows == 58, e2e TC-UI-075 == 58,
  манифест rows:58). Заголовок колонки «Пункт КоАП» (мокап «Статья») —
  решение по tasks.md 17.6.1, зафиксировано в шапке компонента.
- bilety: экзамен-бар/q-card/answers/q-nav/score — фрагменты и CSS дословно;
  отклонений от мокапа кроме задокументированных («данные — из корпуса,
  не иллюстрации») не найдено.

## 5. Ленивые чанки / бюджеты (1.4) — зелен

- defineAsyncComponent + visited ×4 (App.vue:432–448, v-if="pdd*Visited"),
  visited-флаги ставятся в navTo при первом открытии; чанк остается
  смонтированным (NFR-26). Шардинг по билету — import.meta.glob → 80
  чанков ~5 КБ gzip.
- npm run check:budgets на HEAD: green, правила (а)–(д). (г): PddSigns=46.0,
  PddRules=45.6, PddTickets=3.8, PddFines=3.5, pdd-bilety-*=4.1–5.2 — все
  ≤150 КБ; (д): lazy-чанки вне статических замыканий всех 14 страниц.
  Кабинет первый-заход: 42.3 КБ gzip (cabinet+vue+shared) — не распух.
- Amendment честный: (б)/(в) считают СТАТИЧЕСКОЕ замыкание (динамические
  импорты вынесены в отдельную регулярку, check-budgets.mjs:82–92) — для 14
  существующих страниц поведение не меняется (динамических импортов у них нет).

## 6. Носители кабинета / старые e2e — аддитивность подтверждена

- tests/web/test_cabinet_page.py — НЕ тронут (0 строк в диффе);
  test_ui_playwright.py — только добавления в конец (343+, 0 удаленных
  строк, NFR-27 соблюден; TC-UI-070…076 новые).
- TC-UI-059/060 инварианты: правки cabinet.html/App.vue аддитивны —
  4 кнопки после «Кошелек» без перегруппировки (гард
  test_pdd_sidebar_buttons_after_wallet_in_both_carriers), 9 пунктов .snav
  (гард test_pdd_snav_nine_items_order + e2e), хеш-паттерн BUG-047 расширен
  без изменения существующих веток.
- session-токены/хеши не сломаны: session_token sessionStorage,
  X-Session-Token — без изменений в диффе; wallet-раздел/модалка не тронуты.
- Прогон: полный pytest (unit+api+web без playwright) 466 passed; полный
  e2e test_ui_playwright.py 84 passed — существующие сценарии не сломаны.

## 7. BUG-064 — запись корректна, связка с гейтом НЕ работает при MAJ-1

- test-model/bugs/BUG-064.md — структура по прецеденту BUG-063
  (Обнаружено/Природа/Что сделано/Статус); факт среды (нет доступа к
  docker.sock) правдоподобен и не оспаривается. Статус — OPEN (не «закрыт»):
  честно, локальная реплика сборки отсутствует.
- НО: связка «действующий гейт 17.7.4 — CI job docker-build» при MAJ-1 не
  выполняется — CI сборка упадет на frontend-builder. После фикса Dockerfile
  связка становится корректной (CI-гейт зелен) и BUG-064 можно закрывать с
  фактом CI-прогона. До фикса — tasks.md 17.7.4 «docker build → CI green»
  считается НЕ подтвержденным.

## 8. Process-note (не блокер)

Дев-коммиты волн 17.2–17.4.1 помечены «CA:» вместо «dev:»: 65bcda0 (17.2.1),
929efcb (17.2.2), fee05b6 (17.2.3), a6d23e7 (17.2.4), 4cd9e00 (17.3.1),
d9a3047 (17.3.2), 0b071b4 (17.4.1). С волны 17.4.2 (7faa9b7) маркер «dev:» —
как в прецедентах. История не переписывается; учесть в следующих волнах.

## 9. Карта (1.7) — факт-точна

architecture/map.md:315–335: роут/гварды/карта media-types/публичность,
COPY content/ +~48 МБ, build-time генератор, pdd-data gitignored, 4 секции
с хешами, чанк билета отдельным lazy, бюджеты NFR-26(г)/(д) — все факты
сверены с кодом выше; расхождений нет.

## MIN-находки

- **MIN-1** generate-pdd-json.mjs:84–86 и :135–136 — ветка «каталог
  отсутствует» ломает контракт гейта: `fail()` записывается, но выполнение
  продолжается к безусловному `readdirSync(dir)` → сырой ENOENT-стек вместо
  штатного «ГЕЙТ ЦЕЛОСТНОСТИ КОРПУСА ПРОВАЛЕН … Сборка прервана»
  (dieIfFailed для этой ветки не вызывается). Exit-код ненулевой (пропуска
  нет), но диагностика деградировала — проявилось в repro MAJ-1. Фикс:
  `if (!existsSync(dir)) { fail(…); return …; }` (как в buildShtrafi:366–370).
- **MIN-2** PddTickets.vue:79 + :88 — `pdd-bilety-index.json` и статически
  импортируется, и захватывается glob `pdd-bilety-*.json` → vite warning
  INEFFECTIVE_DYNAMIC_IMPORT на каждой сборке + паразитный lazy-чанк
  pdd-bilety-index-*.js (67 Б). Поведения не меняет (динамический путь по
  index недостижим: startTicket строит только `<cat>-<nn>`). Фикс: сузить
  glob до `pdd-bilety-{abm,cd}-*.json`.
- **MIN-3** generate-pdd-json.mjs:408–410 — `out()`: тернарник
  `pretty ? '\\n' : '\\n'` дает одинаковый хвост в обеих ветках (мертвый
  код, намекает на не задуманную разницу). Детерминизму не вредит (хвост
  всегда `\\n`). Фикс: упростить или осознанно развести.

## Прогоны ревьюера (HEAD 2c5f3d8, worktree wt-s17-pdd)

- `npm run build` (генератор на реальном корпусе + vite): OK, 86 pdd-файлов;
  `npm run check:budgets`: OK — (а)–(д) green, «страниц: 14».
- pytest unit+api+web (`pytest tests/unit tests/api tests/web
  --ignore=tests/web/test_ui_playwright.py`): **466 passed**, 1 warning
  (сторонний StarletteDeprecation из testclient, не из диффа).
- e2e полный (`LD_LIBRARY_PATH=/home/hermes-bot/.cache/pw-libs/… pytest
  tests/web/test_ui_playwright.py`): **84 passed** (вкл. новые
  TC-UI-070…076 и старые инварианты кабинета).
- `pytest tests/test_container_contract.py`: 5 passed.
- `openspec validate --all --strict`: 26 passed, 0 failed.
- `python3 scripts/flow_check.py .`: 1 ошибка — J10 (15 закрытых dev-задач
  без approve-ревью) — НОРМА до CR, закрывается этим ревью.
- docker build: НЕ воспроизводим локально (среда без docker.sock — сам факт
  BUG-064 подтвержден), НО layout builder-стейджа воспроизведен в песочнице:
  генератор падает ENOENT/EXIT=1 → MAJ-1 доказан без docker.

## Итог

return: **MAJ-1** — Dockerfile:18–26 (frontend-builder без corpus для
`npm run build`; фикс: COPY content/ в builder-стейдж) — блокер приемки
17.7.4 и CI docker-build. После фикса: MIN-1/2/3 (files: строки выше) —
по желанию партии, не блокеры; process-note §8 — в следующие волны.
Повторное ревью — только дифф фикса + факты CI docker-build (для закрытия
связки BUG-064).
