# Tasks: add-vue-s14-instructor-loop

Правила: задача атомарна (одна сессия = одна задача); `[P]` — независимая
задача (параллелится, каждая в своем worktree; пишут против контрактов
design.md, не против кода друг друга). Типы работ: `[code]`/`[tests]`/
`[docs]`/`[infra]`. Каркас — `frontend/vue/` (существует: пилот С9 +
status-forms С11 + лендинг/анкета С12); правила сборки, сплита и
бюджетов — ADR-008 (architecture/adr/008-vue3-vite-migration.md), свод
С11/С12 по NFR-26 (бюджеты КАЖДОЙ мигрированной страницы; в этой партии
входов становится 8 — design.md «Сверка контрактов решения»);
прецеденты — архивы add-vue-framework-pilot, add-vue-s11-status-forms,
add-vue-s12-landing-apply. Новых npm-зависимостей нет; зависимостей от
параллельных change-пакетов нет. Коммиты не входят в задачи (решает
ПМ/приемка).

## 1. Stub-чистка (мертвая страница /instructor/cabinet-stub)

- [ ] 1.1 [P][code] удалить frontend/instructor-cabinet-stub.html и
      frontend/js/instructor/instructor-cabinet-stub.js; backend/app.py —
      исключить "/instructor/cabinet-stub" из `_PAGE_ROUTES` (строка
      удаляется; остальные маршруты не трогаются). Подтверждение
      недостижимости: grep по frontend/, backend/, tests/ — ссылок на
      "/instructor/cabinet-stub" нет (кроме строки карты и исторических
      носителей sdd.md/code-reviews/test-model — design.md
      «Stub-чистка»). tests/web/test_instructor_pages.py §4.4 — удалить
      2 теста страницы (прецедент «судьба legacy-тестов удаленной
      страницы» — arch-review-002 MAJ-1 пилота); tests/api/
      test_auth_route.py::test_new_static_routes_served — убрать
      "/instructor/cabinet-stub" из списка маршрутов. Spec-дельты
      instructor-auth — в пакете (REMOVED «Заглушка кабинета
      инструктора»; MODIFIED «Роутинг после входа по статусу» —
      approved → /instructor/dashboard, фактическое поведение с 2.2).
      Готовность: файлов и маршрута нет; `pytest tests/web/
      test_instructor_pages.py tests/api/test_auth_route.py` зелен;
      `git grep -n "cabinet-stub" frontend backend tests` — пусто.
      FR: — (решение п.4). NFR: NFR-27. Зависит от: — (параллелится со
      всеми задачами партии).

## 2. Сборка: точки входа партии

- [ ] 2.1 [code] vite.config.mjs — входы: `instructors`
      (frontend/vue/instructors.html), `instructor-dashboard`
      (frontend/vue/instructor-dashboard.html), `documents`
      (frontend/vue/documents.html) — статическая разметка страниц
      (эквивалент legacy 1:1 для instructors/instructor-dashboard;
      documents — оболочка новой страницы, design.md «Страница
      /instructor/documents на Vue») + модуль-скрипты
      /src/pages/<page>/main.js; manualChunks/base '/vue/'/outDir —
      без изменений; scripts/check-budgets.mjs — page-чанки: 8
      (instructors-pending, instructors-rejected, review-form, index,
      instructor-apply, instructors, instructor-dashboard, documents —
      design.md «Сверка контрактов решения»: в решении «7», фактически
      8), замыкание первого захода и «чужие page-чанки» — по каждой
      (бюджеты NFR-26 не меняются). Модуль-скрипты — с МИНИМАЛЬНЫМИ
      App.vue-заглушками страниц (полная разметка и wiring — 3.1/3.2/
      3.3): без заглушек вход не собирается и готовность 2.1
      (build + check:budgets зелен) недостижима (прецедент arch-
      review-001 MIN-2, задача 2.1 С12).
      Готовность: `npm ci && npm run build` — dist содержит три новых
      входа instructors.html/instructor-dashboard.html/documents.html +
      ассеты с хэшами; `npm run check:budgets` зелен (8 page-чанков);
      `npm run dev` поднимает все страницы; вендорного кода в чанках
      страниц нет.
      FR: FR-84. NFR: NFR-26. Зависит от: —.

## 3. Страницы на Vue (после 2.1; порядок: лендинг → кабинет → документы)

- [ ] 3.1 [code] frontend/vue/src/pages/instructors/ — полный перенос
      лендинга инструкторов + КОНСОЛИДАЦИЯ контура входа (последний
      дубль модалок; детали — design.md «Страница /instructors на Vue»
      и «Судьба контура модалок входа»): разметка/стили 1:1 без
      редизайна (бренд с .brand em «Сбер», hero, форматы own/sber,
      возможности, нижний CTA #open-form, футер, медиазапросы 850/560);
      src/shared/loginWiring.js — НОВОЕ: композабл doLogin с дословными
      фрагментами контракта (postJSON('/api/auth/login',
      setToken(res.data.token), route-маппинг §15.5,
      sessionStorage 'instructor_rejected_reason' ДО редиректа
      /instructors/rejected — КОНТРАКТ POLLING/REJECTED НЕ СЛОМАТЬ);
      src/pages/landing/App.vue — переключение на композабл (фрагменты
      переезжают дословно, register-wiring остается);
      src/shared/LoginModal.vue — проп variant ('instructors' —
      разметка варианта из instructors.html дословно: без .sub/label/
      alt-строки; 'landing' — дефолт без изменений, носитель
      LOGIN_MODAL_TEXTS не трогается); wiring js/instructors.js 1:1 в
      App.vue: data-open-login → локальное открытие БЕЗ флагов
      (BUG-055), закрытие крестик/«Отмена»/Esc, фон НЕ закрывает
      (BUG-056), #open-form → /instructors/apply; ошибка — #login-error
      (проп error, эквивалент err.textContent=). tests/web/
      test_login_modal.py — перенос носителя: vue_landing_source()
      дополняется src/shared/loginWiring.js (фрагменты дословны в
      композабле). Id-якоря e2e дословно (TC-UI-003/010/052,
      TC-S9UI-003).
      Готовность: TC-UI-003/052 зеленые на прогоне 6.1 без правок;
      `git grep -l 'id="m-login"' frontend -- '*.html'` — только
      frontend/vue/*; скриншот-сверка визуальной эквивалентности;
      test_login_modal зелен.
      FR: FR-10, FR-13. NFR: NFR-27. Зависит от: 2.1.

- [ ] 3.2 [code] frontend/vue/src/pages/instructor-dashboard/ — полный
      перенос кабинета (крупнейший монолит партии; детали — design.md
      «Страница /instructor/dashboard на Vue»): разметка/стили 1:1 без
      редизайна (каркас .app = aside+main grid 2 колонки, topbar,
      hello, виджеты «Мой день», панели-демо, секции #sec-calendar
      (С10)/#sec-students (С8)/#sec-cars (С5/С7)/#sec-docs (С8),
      demo-tag «демо», сайдбар РОВНО текущий перечень BUG-051);
      wiring dashboard-instructor.js 1:1 в App.vue — плоский JS,
      фрагменты контракта дословно: гвард fetch('/api/auth/me') +
      fetch('/api/instructor/dashboard') 401/403 → '/', ФИО/инициалы
      (FR-20), дата Europe/Moscow, navTo (секции + хеш #/my-cars +
      BUG-058), loadSummary/loadRequests/openStudents (реальные данные
      «Мой день»/«Мои ученики» — FR-39…41), календарь С10, автомобили
      С7, документы С8 (openDocs/docCardNode/версии FR-70/71/72/
      mcValidatePhoto/mcUpload), toast, logout (POST /api/auth/logout
      → clearSession → /instructors); DOM-фрагменты legacy
      (textContent=/style.display=/innerHTML) — эквиваленты Vue на
      реактивных списках (design.md «Границы правок тестов»);
      inline onclick-разметки → @click с теми же действиями/текстами;
      демо-данные Спринта 2.2 сохраняются (решение). Id-якоря e2e
      дословно (TC-UI-005/008/009/010/015/016/023/024/025…028/030/
      033/034/040/042, accept-flow, xss).
      Готовность: якоря партии зеленые на прогоне 6.1 без правок
      сценариев; скриншот-сверка визуальной эквивалентности (мокап
      dashboard-instructor); гварды/редиректы — без изменений.
      FR: FR-18…22, FR-39…41. NFR: NFR-27. Зависит от: 2.1.

- [ ] 3.3 [P][code] frontend/vue/src/pages/documents/ — НОВАЯ страница
      «Мои документы» (детали — design.md «Страница /instructor/
      documents на Vue»): оболочка в стиле кабинета (бренд →
      /instructor/dashboard, «← В кабинет», «Выйти» — механика
      dashboard-logout → /instructors); контент — перенос карточной
      модели раздела С8 1:1: ВУ + СТС по каждому авто (включая «нет
      СТС» с дозагрузкой — merge как openDocs), версии/статусы
      («Действует» / «Ожидает проверки замены» / «Отклонено» с
      причиной — ОВ-1/ОВ-7, docVersionLine), просмотр #m-view
      (BUG-054), диалог замены #m-replace с предупреждением FR-71 и
      явной кнопкой, клиентская валидация JPEG/PNG ≤5 МБ (mcValidatePhoto),
      тосты legacy дословно, перезагрузка списка после загрузки.
      Гвард как в кабинете: fetch('/api/auth/me') → 401 → '/'
      (GET /api/instructor/me НЕ существует — сверка design.md);
      контракты GET /api/instructor/documents, POST
      /api/instructor/documents/license ('file'), POST
      /api/instructor/cars/{id}/photo/sts ('photo'), GET
      …/{doc_id}/file — БЕЗ ИЗМЕНЕНИЙ. Legacy-монолит documents.html
      НЕ создается (инвариант BUG-047 остается без правок); раздел
      «Профиль и документы» кабинета — не трогается; ссылки из
      сайдбара НЕ добавляются (TC-UI-028).
      Готовность: `npm run build` собирает вход; инвариант BUG-047
      (negativный список standalone) зелен без правок; сценарии
      функциональности раздела кабинета (TC-UI-033/034/040/042)
      зеленые — функциональность та же.
      FR: FR-45, FR-69…73. NFR: NFR-26/27. Зависит от: 2.1.

## 4. Переключение маршрутов и удаление легаси (одна сессия)

- [ ] 4.1 [code] удаление легаси + переводы тестов-потребителей:
      удалить frontend/instructors.html, frontend/js/instructors.js,
      frontend/instructor-dashboard.html,
      frontend/js/instructor/dashboard-instructor.js. Переносы
      источников чтения — ТОЛЬКО носители + задокументированные
      подстановки (design.md «Границы правок тестов»):
      tests/web/test_instructor_pages.py §4.1 (4 теста → вход
      vue/instructors.html + App.vue + styles.css; CSS-сверка мокапа →
      styles.css; `location.href='/instructors/apply'`,
      `data-open-login`, `postJSON('/api/auth/login'`,
      отсутствие `location.href='/';` — дословны);
      tests/api/test_instructor_dashboard.py (PAGE → вход
      vue/instructor-dashboard.html; frontend_source → вход + App.vue;
      фрагменты fetch/'X-Session-Token'/401/403/location.href='/'/navTo/
      demo-tag — дословны); tests/api/test_s3_backend.py
      (test_s4_pages_wired_to_real_api_shapes: носитель дашборда →
      вход + App.vue; needles дословны, конкатенация строк сохранена —
      MIN-2 С11); tests/web/test_ui_playwright.py — ТОЛЬКО design-
      guard: tag-balance (−instructor-dashboard.html, +vue/
      instructor-dashboard.html, +vue/instructors.html, +vue/
      documents.html — прецедент vue/index.html С12) и BUG-047-guard
      test_back_links_lead_to_role_home (чтение dash → вход + App.vue;
      негативный список standalone — БЕЗ ПРАВОК). Сценарии e2e не
      тронуты. scripts/check_tag_balance.py — DEFAULT:
      frontend/instructor-dashboard.html → frontend/vue/
      instructor-dashboard.html.
      Готовность: grep по репо — ссылок на 4 легаси-файла нет (кроме
      исторических носителей: sdd.md, openspec/changes/archive/,
      code-reviews/, test-model/, design/mocks, комментарии
      cabinet.html); `git diff tests/web/test_ui_playwright.py` —
      только два design-guard носителя; переведенные файлы тестов
      зеленые.
      FR: FR-84, FR-85. NFR: NFR-27. Зависит от: 3.1, 3.2 (носители
      существуют).

- [ ] 4.2 [code] backend/app.py — регистрация страниц в
      `_PAGE_ROUTES`: "/instructors" → "vue:instructors.html",
      "/instructor/dashboard" → "vue:instructor-dashboard.html",
      НОВАЯ строка "/instructor/documents" → "vue:documents.html"
      (значения с маркером "vue:" — цикл отдачи БЕЗ ИЗМЕНЕНИЙ: читает
      VUE_DIST_DIR, 404 при отсутствии dist); пилотный хендлер
      /instructors/pending НЕ трогается; статика /vue/assets/*,
      _PAGE_REDIRECTS и /api/* — БЕЗ ИЗМЕНЕНИЙ. tests/api/
      test_auth_route.py::test_new_static_routes_served — добавить
      "/instructor/documents" в список (200 text/html; изъятие
      cabinet-stub — в 1.1). Выполняется в одной сессии с 4.1 (без
      промежуточного пуша — design.md «Роуты и статика»).
      Готовность: GET /instructors и GET /instructor/dashboard отдают
      входы dist (html со ссылками на /vue/assets); GET
      /instructor/documents — 200 вход documents; tests/web/
      test_static.py (GET / — без правок) и tests/api/
      test_auth_route.py зеленые (после сборки dist); остальные
      маршруты карты — как прежде.
      FR: FR-84. NFR: NFR-27. Зависит от: 4.1.

## 5. Бюджеты чанков NFR-26 на артефактах сборки

- [ ] 5.1 [tests] прогон сборки + замер gzip: `npm ci && npm run
      build && npm run check:budgets` (скрипт 2.1): (а) каждый
      vendor-чанк ≤150 КБ gzip; (б) JS первого захода КАЖДОЙ страницы
      (page-чанк + static-import graph: shared + vue) ≤200 КБ gzip —
      отдельно для instructors-pending, instructors-rejected,
      review-form, index, instructor-apply, instructors,
      instructor-dashboard, documents (8 — design.md «Сверка
      контрактов решения»); (в) в бандле страницы нет чужих page-
      чанков (multi-entry). Фактические размеры всех чанков — в
      отчете задачи. Кабинет — крупнейший перенос: стили в styles.css
      (CSS вне JS-бюджета), wiring без библиотек.
      Готовность: оба бюджета соблюдены на восьми страницах; при
      превышении — сокращение зависимостей (без новых библиотек), не
      ослабление проверки.
      FR: FR-84. NFR: NFR-26. Зависит от: 2.1, 3.1, 3.2, 3.3
      (финальные чанки).

## 6. e2e-совместимость и приемка партии

- [ ] 6.1 [tests] полный прогон Playwright-набора БЕЗ правок сценариев:
      `npm ci && npm run build` → `pytest tests/web/test_ui_playwright.py`
      (фикстура server поднимает uvicorn backend.app:app; маршруты
      /instructors, /instructor/dashboard, /instructor/documents
      отдают dist). Правки test_ui_playwright.py в этом пакете —
      только два переноса носителя design-guard (4.1): `git diff`
      контроль; селекторы/маршруты/ожидания сценариев не тронуты.
      Якоря партии: TC-UI-003 (лендинг инструкторов), TC-UI-005
      (вход → layout кабинета), TC-UI-008/024 (календарь, виджет),
      TC-UI-009 (запросы), TC-UI-010 (выход → /instructors, .brand em
      «Сбер»), TC-UI-015/016/023/028 (авто, BUG-051 сайдбар ровно),
      TC-UI-030/033/034/040/042 (авто-флоу, документы раздела),
      TC-UI-052 (модалка входа instructors), TC-S9UI-003 (rejected-
      редирект), accept-flow/xss. Регресс смежных доменов: `pytest
      tests/web/test_instructor_pages.py tests/api/
      test_instructor_dashboard.py tests/api/test_s3_backend.py
      tests/web/test_login_modal.py tests/web/test_static.py
      tests/api/test_auth_route.py tests/web/test_bug001.py` зеленый;
      полный `pytest tests/` — зеленый (после сборки dist).
      Валидации: `openspec validate add-vue-s14-instructor-loop
      --strict` и `openspec validate --all --strict` зеленые.
      Готовность: полный набор e2e passed, 0 правок сценариев (кроме
      двух задокументированных переносов design-guard); маршруты и
      /api/* — без ломающих изменений; сессия rejected-причины жива
      (TC-S9UI-003); `pytest tests/web/test_instructor_pages.py` —
      §4.4 отсутствует, §4.1 зелен на новых носителях.
      FR: FR-85. NFR: NFR-27. Зависит от: 1.1, 4.2, 5.1.

## Зависимости (волны)

- Волна 0: 1.1 stub-чистка — [P], независима от всего пакета (легаси
  stub + строка карты + §4.4 + список test_auth_route + дельта
  instructor-auth; файловых пересечений с миграцией нет).
- Волна 1: 2.1 (входы + бюджет-скрипт + заглушки) → { 3.1 → 3.2,
  3.3 [P] } — утвержденный порядок решения: лендинг инструкторов →
  кабинет → документы. 3.1 до 3.2: консолидация wiring входа меняет
  носители test_login_modal — интегрируется первым; 3.3 зависит
  только от 2.1 (файлы с 3.2 не пересекаются — допускается параллель
  при свободных руннерах).
- Волна 2: 3.1 и 3.2 → 4.1 (переводы требуют готовых носителей);
  4.1 → 4.2 (подряд в одной сессии, без промежуточного пуша).
- Волна 3: 5.1 — после 3.1/3.2/3.3 (финальные чанки); 6.1 — последняя
  (после 4.2, 5.1 и 1.1 — общий e2e-гейт).

## Рекомендации к нарезке

- Швы: (а) stub-чистка (1.1) — независимая задача, любой момент;
  (б) лендинг + консолидация (3.1) — после 2.1; (в) кабинет (3.2) —
  после 3.1; (г) документы (3.3) — [P] после 2.1; интеграция
  (4.1+4.2) — одна сессия.
- НЕЛЬЗЯ делить: 4.1 и 4.2 (удаление легаси без немедленной
  регистрации маршрутов оставляет маршрут без отдачи); 5.1 нельзя
  выполнять до финала 3.1/3.2/3.3 (бюджеты по финальным чанкам);
  6.1 — после всех (включая 1.1).
- Общая зона файлов (не делить между задачами): frontend/vue/
  vite.config.mjs и scripts/check-budgets.mjs — только 2.1;
  src/shared/loginWiring.js и LoginModal.vue — 2.1 (пустые входы не
  трогают) / 3.1 (создание и подключение); src/pages/landing/App.vue —
  только 3.1; backend/app.py — 1.1 (строка stub) и 4.1/4.2 (маршруты
  партии) — не параллелить 1.1 с 4.x; tests/web/test_ui_playwright.py —
  только 4.1 (оба design-guard носителя); tests/web/
  test_instructor_pages.py — 1.1 (§4.4) и 4.1 (§4.1) — разные секции
  одного файла: не параллелить 1.1 и 4.1 в разных worktrees;
  tests/api/test_auth_route.py — 1.1 (изъятие stub) и 4.2 (добавление
  documents) — не параллелить; src/pages/instructors/ — только 3.1;
  src/pages/instructor-dashboard/ — только 3.2; src/pages/documents/ —
  только 3.3.

## План тестовых прогонов (наборы — отдельные делегации-раннеры)

1. **API/регресс**: `pytest tests/` (кроме playwright) — после сборки
   dist (маршруты партии отдают 404 без нее; /instructor/documents —
   новый маршрут); стенд: репо, env-заглушки conftest; ~5–10 мин.
2. **e2e полный**: `pytest tests/web/test_ui_playwright.py` — стенд:
   собранный dist (`npm ci && npm run build` ДО прогона — обязательный
   шаг), uvicorn на эфемерном порту, Chromium headless; ~15–30 мин
   (кабинет на Vue — самый долгий контур).
3. **Валидации**: `openspec validate --all --strict` +
   `npm run check:budgets` — секунды, локально без стенда.
Прогоны 1 и 2 НЕ объединять в один сабагент-раннер (разные стенды и
длительности); сборка dist выполняется один раз до прогонов 2, 5.1 и
регресса 6.1.
