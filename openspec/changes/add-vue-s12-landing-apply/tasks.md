# Tasks: add-vue-s12-landing-apply

Правила: задача атомарна (одна сессия = одна задача); `[P]` — независимая
задача (параллелится, каждая в своем worktree; пишут против контрактов
design.md, не против кода друг друга). Типы работ: `[code]`/`[tests]`/
`[docs]`/`[infra]`. Каркас — `frontend/vue/` (существует: пилот С9 +
status-forms С11); правила сборки, сплита и бюджетов — ADR-008
(architecture/adr/008-vue3-vite-migration.md), свод С11 по NFR-26
(бюджеты КАЖДОЙ мигрированной страницы); прецеденты — архивы
add-vue-framework-pilot и add-vue-s11-status-forms. Новых
npm-зависимостей нет; зависимостей от параллельных change-пакетов нет.
Коммиты не входят в задачи (решает ПМ/приемка).

## 1. BUG-062 (отдельная задача пакета — независима от миграции)

- [x] 1.1 [P][code] BUG-062 (реестр test-model/bugs/BUG-062.md, решение
      Заказчика 2026-11-07): убрать плитку-аватар из шапки «Выбора
      инструктора» — frontend/instructor-choice.html: удалить
      `<span class="avatar" id="avatar">—</span>` из блока .user и
      правило `.avatar{width:34px;…}`; frontend/js/instructor-choice.js:
      удалить заполнение `document.getElementById('avatar')` (чтение ФИО
      #uname — без изменений); дизайн-мокапы СИНХРОННО (прецедент
      «мокапы choice-a/b синхронно» BUG-059/060/061):
      design/mocks/choice-instructor-a.html и choice-instructor-b.html —
      убрать ту же плитку и то же правило; tests/web/test_ui_playwright.py
      TC-UI-059 (test_tc_ui_059_student_cabinet_single_logo_no_crumbs) —
      в секцию /instructor-choice добавить негативный инвариант «в шапке
      нет .avatar» (дополнение сценария прямо предписано планом фикса —
      design.md «Границы правок тестов»); остальное тело сценария и
      прочие сценарии не трогаются. Сверка плана BUG-062 «инициалы
      нигде больше в контуре ученика»: шапка /cabinet — уже без
      аватара; .avatar в cabinet.html — декоративный круг ассистента
      (не трогается); инициалы ученика на /review (С11) — вне решения
      BUG-062 (зафиксировано в design.md).
      Готовность: на /instructor-choice шапка = ФИО + «Выйти» (без
      .avatar, вёрстка BUG-061 не поехала); мокапы choice-a/b без
      плитки и правила; расширенный TC-UI-059 зелен в прогоне 6.1;
      `git grep -n "id=\"avatar\"" frontend/instructor-choice.html` —
      пусто.
      FR: — (BUG-062). NFR: NFR-27. Зависит от: — (параллелится со
      всеми задачами партии).

## 2. Сборка: точки входа партии

- [x] 2.1 [code] vite.config.mjs — входы: `index`
      (frontend/vue/index.html) и `instructor-apply`
      (frontend/vue/instructor-apply.html) — статическая разметка
      страниц (эквивалент legacy 1:1: лендинг с модалками из
      index.html; анкета с формой из instructor-apply.html; тексты/CSS
      дословно) + модуль-скрипты /src/pages/<page>/main.js;
      manualChunks/base '/vue/'/outDir — без изменений;
      scripts/check-budgets.mjs — page-чанки: 5 страниц
      (instructors-pending, instructors-rejected, review-form, index,
      instructor-apply), замыкание первого захода и «чужие page-чанки»
      — по каждой (бюджеты NFR-26 не меняются). src/shared/ — НОВОЕ:
      LoginModal.vue и RegisterModal.vue (разметка модалок — дословный
      перенос из index.html, включая комментарии-маркеры
      «Модалка: Вход/Регистрация» — носитель LOGIN_MODAL_TEXTS;
      api.js/utils.js — без изменений). Модуль-скрипты входов
      /src/pages/<page>/main.js — с МИНИМАЛЬНЫМИ App.vue-заглушками
      страниц (полную разметку-копию и wiring — 3.1/3.2): без заглушек
      вход не собирается и готовность 2.1 (build + check:budgets зелен)
      недостижима (arch-review-001 MIN-2).
      Готовность: `npm ci && npm run build` — dist содержит оба входа
      index.html/instructor-apply.html + ассеты с хэшами;
      `npm run check:budgets` зелен (5 page-чанков); `npm run dev`
      поднимает обе страницы; вендорного кода в чанках страниц нет.
      FR: FR-84. NFR: NFR-26. Зависит от: —.

## 3. Страницы на Vue (параллель после 2.1; лендинг — последняя)

- [x] 3.1 [P][code] frontend/vue/src/pages/instructor-apply/ — полный
      перенос анкеты, wiring js/apply.js 1:1 (детали — design.md
      «Страница /instructors/apply на Vue»): разметка/стили 1:1 без
      редизайна (тексты/CSS мокапа registration-instructor дословно);
      формат own/sber — реактивная связь (госномер disabled/очистка/
      приглушение — эквивалент updateFormat, design.md «Границы правок
      тестов»); выбор ВУ → миниатюра objectURL / клиентская ошибка
      (JPEG/PNG ≤5 МБ, тексты = серверным); consent-гейт кнопки
      (FR-77); сабмит — FormData построчно как legacy (15
      fd.append-строк: 14 полей + consent, + условный license_photo —
      arch-review-001 MIN-1; тест-кортеж §4.2 покрывает 13
      append-фрагментов), fetch('/api/instructors/apply',
      method:'POST') — СТРОКОВО как в legacy; 200 → localStorage
      application_poll_token/application_exchange_token ДО редиректа
      /instructors/pending; 413/415/422-файловые → #license-error +
      #notice; согласие — 422 позиция 1a (сервер) → #notice; сеть →
      #notice «Ошибка сети»; sessionStorage на странице НЕ используется.
      Id-якоря e2e дословно (#registration, #license-file,
      .checkline, #notice и др. — TC-UI-004-серия).
      Готовность: TC-UI-004 и upload-сценарии зеленые на прогоне 6.1
      без правок; скриншот-сверка визуальной эквивалентности;
      контракты вызовов — без изменений.
      FR: FR-10, FR-11, FR-12, FR-77. NFR: NFR-27. Зависит от: 2.1.

- [x] 3.2 [code] frontend/vue/src/pages/landing/ — полный перенос
      лендинга + подключение shared-модалок (ПОСЛЕДНЯЯ задача партии —
      самая рискованная: вход в кабинеты идет через модалки лендинга,
      около половины e2e; детали — design.md «Страница / на Vue» и
      «Судьба общего контура модалок»): разметка/стили 1:1 без
      редизайна (hero, шаги 01–04, чат-бар «Гига ГАИшник» —
      визуальная заглушка с alert-текстами дословно, плитки футера,
      медиазапросы включая порог nav 1200); модалки —
      src/shared/LoginModal.vue/RegisterModal.vue поверх статической
      разметки входа (комментарии-маркеры и разметка m-login/m-register
      1:1 — носитель LOGIN_MODAL_TEXTS); wiring js/landing.js 1:1 в
      App.vue: data-open/data-close, Esc, фон НЕ закрывает #m-login
      (BUG-055/056), снятие open_login/open_login_from при закрытии;
      consent-гейт #reg-submit (FR-78); сабмиты через shared/api.js
      (postJSON/setToken); login route-маппинг §15.5 дословно —
      route=rejected → sessionStorage «instructor_rejected_reason» ДО
      редиректа /instructors/rejected (КОНТРАКТ POLLING/REJECTED НЕ
      СЛОМАТЬ), approved → /instructor/dashboard, waiting →
      /instructors/pending, ученик → /cabinet; ошибки — тексты сервера
      в #login-error/#reg-error. Id/класс-якоря e2e дословно
      (TC-UI-001/002/043…045/053, TC-S9UI-003, TC-UI-005/059/060).
      Готовность: якоря партии зеленые на прогоне 6.1 без правок
      сценариев; модалка входа отцентрована (TC-UI-001); скриншот-
      сверка визуальной эквивалентности; ключи sessionStorage — те же.
      FR: FR-1, FR-2, FR-13, FR-17, FR-78. NFR: NFR-27. Зависит от:
      2.1, 3.1 (анкета готова раньше — лендинг интегрируется последним).

## 4. Переключение маршрутов и удаление легаси (одна сессия)

- [ ] 4.1 [code] удаление легаси + переводы тестов-потребителей:
      удалить frontend/index.html, frontend/js/landing.js,
      frontend/instructor-apply.html, frontend/js/apply.js; исключить
      "/" и "/instructors/apply" из легаси-отдачи `_PAGE_ROUTES`.
      Переводы источников чтения — ТОЛЬКО носители + задокументированные
      подстановки (design.md «Границы правок тестов»): tests/web/
      test_login_modal.py (LOGIN_MODAL_TEXTS → frontend/vue/index.html;
      WIRING_FRAGMENTS и route-маппинг → вход + App.vue +
      shared/api.js, фрагменты контракта дословны, `err.textContent=`
      → эквивалент #login-error/#reg-error; GET /js/landing.js →
      носитель из репо); tests/web/test_bug001.py (TC-AUTH-019 → тот же
      носитель, фрагменты дословны); tests/api/test_policy.py
      (TC-PD-005 → носители обоих страниц, `regSubmit.disabled=…` и
      `consent:regConsent.checked` → эквиваленты Vue, `fd.append('consent'`
      дословно); tests/web/test_instructor_pages.py §4.2 (5 тестов →
      вход + App.vue; CSS-сверка → styles.css; `updateFormat`/
      `plate.disabled`/`notice.classList` → эквиваленты Vue, остальные
      фрагменты дословны); tests/web/test_ui_playwright.py — ТОЛЬКО
      test_s4_pages_tag_balance (+ `vue/index.html`,
      `vue/instructor-apply.html` — прецедент vue/review-form.html
      С11). Сценарии e2e не тронуты.
      Готовность: grep по репо — ссылок на 4 легаси-файла нет (кроме
      исторических носителей: docstring, openspec/changes/archive/,
      code-reviews/, design/mocks/, sdd.md — sdd.md в пакетах миграции
      не ведется); `git diff tests/web/test_ui_playwright.py` — только
      две строки параметризации tag-balance (инвариант BUG-062 — в 1.1);
      переведенные файлы тестов зеленые.
      FR: FR-84, FR-85. NFR: NFR-27. Зависит от: 3.1, 3.2 (носители
      существуют).

- [ ] 4.2 [code] backend/app.py — регистрация двух страниц в
      `_PAGE_ROUTES`: значения с маркером каркаса "vue:index.html" и
      "vue:instructor-apply.html" (цикл отдачи при префиксе "vue:" —
      БЕЗ ИЗМЕНЕНИЙ: читает VUE_DIST_DIR, 404 при отсутствии dist);
      пилотный хендлер /instructors/pending НЕ трогается; статика
      /vue/assets/* — БЕЗ ИЗМЕНЕНИЙ; _PAGE_REDIRECTS и /api/* — БЕЗ
      ИЗМЕНЕНИЙ. Выполняется в одной сессии с 4.1 (без промежуточного
      пуша — design.md «Роуты и статика»).
      Готовность: GET / и GET /instructors/apply отдают входы dist
      (html со ссылками на /vue/assets); tests/web/test_static.py
      (GET / → 200 «СберАвтошкола», reg-password wiring) и tests/api/
      test_auth_route.py::test_new_static_routes_served зеленые
      (после сборки dist); остальные маршруты карты — как прежде.
      FR: FR-84. NFR: NFR-27. Зависит от: 4.1.

## 5. Бюджеты чанков NFR-26 на артефактах сборки

- [ ] 5.1 [tests] прогон сборки + замер gzip: `npm ci && npm run
      build && npm run check:budgets` (скрипт 2.1): (а) каждый
      vendor-чанк ≤150 КБ gzip; (б) JS первого захода КАЖДОЙ страницы
      (page-чанк + static-import graph: shared + vue) ≤200 КБ gzip —
      отдельно для instructors-pending, instructors-rejected,
      review-form, index, instructor-apply; (в) в бандле страницы нет
      чужих page-чанков (multi-entry). Фактические размеры всех
      чанков — в отчете задачи.
      Готовность: оба бюджета соблюдены на пяти страницах (лендинг —
      крупнейший перенос стилей: стили в styles.css-чанке страницы);
      при превышении — сокращение зависимостей (без новых библиотек),
      не ослабление проверки.
      FR: FR-84. NFR: NFR-26. Зависит от: 2.1, 3.1, 3.2 (финальные
      чанки).

## 6. e2e-совместимость и приемка партии

- [ ] 6.1 [tests] полный прогон Playwright-набора БЕЗ правок сценариев:
      `npm ci && npm run build` → `pytest tests/web/test_ui_playwright.py`
      (62 сценария; фикстура server поднимает uvicorn backend.app:app,
      маршруты / и /instructors/apply отдают dist). Правки
      test_ui_playwright.py в этом пакете — только две строки
      параметризации tag-balance (4.1) и негативный инвариант BUG-062
      (1.1): `git diff` контроль; селекторы/маршруты/ожидания сценариев
      не тронуты. Якоря партии: TC-UI-001/002 (лендинг, регистрация),
      TC-UI-004 + upload-серия (анкета), TC-UI-043…045 (consent +
      policy), TC-UI-053 (семантика модалки входа), TC-S9UI-003 и
      TC-UI-005 (route-редиректы входа), TC-UI-059/060 (вход ученика,
      негативный инвариант BUG-062). Регресс смежных доменов:
      `pytest tests/web/test_login_modal.py tests/web/test_bug001.py
      tests/web/test_instructor_pages.py tests/web/test_static.py
      tests/api/test_policy.py tests/api/test_auth_route.py` зеленый;
      полный `pytest tests/` — зеленый (после сборки dist).
      Валидации: `openspec validate add-vue-s12-landing-apply --strict`
      и `openspec validate --all --strict` зеленые.
      Готовность: полный набор e2e passed, 0 правок сценариев (кроме
      двух задокументированных исключений); маршруты и /api/* — без
      ломающих изменений; сессия rejected-причины жива
      (TC-S9UI-003).
      FR: FR-85. NFR: NFR-27. Зависит от: 4.2, 5.1, 1.1.

## Зависимости (волны)

- Волна 0: 1.1 BUG-062 — [P], независима от всего пакета (легаси
  instructor-choice + мокапы + TC-UI-059; файловых пересечений с
  миграцией нет).
- Волна 1: 2.1 (входы + бюджет-скрипт + shared-модалки) → { 3.1 [P],
  3.2 } — страницы параллятся по замыслу, НО 3.2 (лендинг) —
  ПОСЛЕДНЯЯ задача партии по приоритету интеграции: 3.1 → 3.2
  (последовательность; самая рискованная страница — последней).
- Волна 2: 3.1 и 3.2 → 4.1 (переводы требуют готовых носителей);
  4.1 → 4.2 (подряд в одной сессии, без промежуточного пуша).
- Волна 3: 5.1 — после 3.1/3.2 (финальные чанки); 6.1 — последняя
  (после 4.2, 5.1 и 1.1).

## Рекомендации к нарезке

- Швы: (а) BUG-062 (1.1) — независимая задача, любой момент; (б) анкета
  (3.1) — после 2.1, параллелится; (в) лендинг (3.2) — после 3.1;
  интеграция (4.1+4.2) — одна сессия.
- НЕЛЬЗЯ делить: 4.1 и 4.2 (удаление легаси без немедленной регистрации
  маршрутов оставляет маршрут без отдачи); 5.1 нельзя выполнять до
  финала 3.1/3.2 (бюджеты по финальным чанкам); 6.1 — после всех
  (включая 1.1 — общий e2e-гейт).
- Общая зона файлов (не делить между задачами): frontend/vue/
  vite.config.mjs и scripts/check-budgets.mjs — только 2.1;
  src/shared/LoginModal.vue/RegisterModal.vue — только 2.1 (создание) /
  3.2 (подключение); backend/app.py — только 4.1/4.2;
  tests/web/test_ui_playwright.py — 1.1 (TC-UI-059) и 4.1
  (tag-balance) — разные тесты, но в одном файле: не параллелить 1.1 и
  4.1 в разных worktrees; frontend/instructor-choice.html + мокапы
  choice-a/b — только 1.1; src/pages/landing/ — только 3.2;
  src/pages/instructor-apply/ — только 3.1.

## План тестовых прогонов (наборы — отдельные делегации-раннеры)

1. **API/регресс**: `pytest tests/` (кроме playwright) — после сборки
   dist (маршруты / и /instructors/apply отдают 404 без нее); стенд:
   репо, env-заглушки conftest; ~5–10 мин.
2. **e2e полный**: `pytest tests/web/test_ui_playwright.py` (62
   сценария) — стенд: собранный dist (`npm ci && npm run build` ДО
   прогона — обязательный шаг), uvicorn на эфемерном порту, Chromium
   headless; ~15–30 мин.
3. **Валидации**: `openspec validate --all --strict` +
   `npm run check:budgets` — секунды, локально без стенда.
Прогоны 1 и 2 НЕ объединять в один сабагент-раннер (разные стенды и
длительности); сборка dist выполняется один раз до прогонов 2, 5.1 и
регресса 6.1.
