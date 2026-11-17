# Change: add-vue-s14-instructor-loop

## Why (Зачем)

Спринт 14, пункт 1 бэклога «Фронтенд-фреймворк — продолжение миграции»
(BACKLOG.md #1): решение Заказчика 2026-11-09 — состав Спринта 14
(decisions/2026-11-09-sprint14-go.md, «давай дальше»). Каркас Vue 3 +
Vite — в проде: пилот /instructors/pending (С9, PR#107), статусные формы
(С11), лендинг ученика + анкета инструктора (С12, PR#128). По плану
ADR-008 (п.4, ступень «лендинги, анкета с multipart, кабинеты») остаются
три страницы инструкторского контура: лендинг /instructors — носитель
ПОСЛЕДНЕГО легаси-дубля модалки входа (та же пара оверлеев m-login, что
на каркасе с С12; после партии легаси-копий модалок не остается — все
входы в инструкторский контур идут через Vue), кабинет инструктора
/instructor/dashboard (крупнейший монолит: 85 КБ html + wiring, через
него проходит более трети e2e-сценариев) и новая страница «Мои
документы» /instructor/documents (вынос функциональности раздела
«Мои документы», Спринт 8). Вместе с партией закрывается мертвая
страница-заглушка /instructor/cabinet-stub — недостижима с Спринта 2.2
(approved-вход ведет в /instructor/dashboard; переходов на заглушку
нет — grep подтвержден, задача 1.1).

Источники требований: ADR-008 (architecture/adr/008-vue3-vite-migration.md —
multi-entry, замена монолита целиком, бюджеты NFR-26, план миграции);
решение Заказчика 2026-11-09 (decisions/2026-11-09-sprint14-go.md —
состав С14, вне состава: instructor-bookings + admin-контур); FR-10/
FR-13 (лендинг, вход route/reason §15.5); FR-18…FR-22, FR-39…FR-41
(кабинет: гвард, макет, ФИО, выход, виджеты, запросы); FR-45,
FR-69…FR-73 (документы: версии, загрузка/замена с предупреждением,
просмотр действующей); FR-84…FR-86; NFR-26/27.

## What Changes (Что меняет)

- **Лендинг инструкторов `/instructors` на Vue**: новая страница
  `frontend/vue/src/pages/instructors/` + вход
  `frontend/vue/instructors.html`; разметка/CSS/тексты legacy
  (frontend/instructors.html) воспроизводятся 1:1 — hero «Учи водить.
  Меняй подход.», форматы own/sber, возможности, нижний CTA, футер;
  wiring js/instructors.js переносится 1:1: CTA #open-form →
  /instructors/apply, «Войти» (data-open-login) открывает модалку
  ЛОКАЛЬНО без sessionStorage-флагов (BUG-055), закрытие —
  крестик/«Отмена»/Esc, клик по фону не закрывает (BUG-056); сабмит —
  POST /api/auth/login, route/reason §15.5 без изменений (approved
  route='cabinet' → /instructor/dashboard, pending →
  /instructors/pending, rejected → sessionStorage
  «instructor_rejected_reason» ДО редиректа /instructors/rejected,
  ученик → /cabinet). Модалка входа — ПОСЛЕДНИЙ ДУБЛЬ: используется
  shared/LoginModal.vue (с С12) с вариантом разметки лендинга
  инструкторов; wiring входа консолидируется в shared-композабл на
  живом втором потребителе (обещание design С12 «Судьба общего контура
  модалок») — легаси-копий модалок после партии не остается. Контракт
  НЕ МЕНЯЕТСЯ.
- **Кабинет инструктора `/instructor/dashboard` на Vue**: новая страница
  `frontend/vue/src/pages/instructor-dashboard/` + вход
  `frontend/vue/instructor-dashboard.html`; перенос 1:1 legacy
  instructor-dashboard.html + js/instructor/dashboard-instructor.js
  (крупнейший монолит партии): гвард без изменений (GET /api/auth/me с
  X-Session-Token → 401 → «/»; данные — GET /api/instructor/dashboard,
  401/403 → «/»), ФИО из /api/auth/me (FR-20), демо-данные Спринта 2.2
  сохраняются, разделы «Мой день» (виджеты из GET /api/instructor/
  summary + /api/instructor/requests) и «Мои ученики» (GET
  /api/instructor/students, подраздел «Запросы учеников» с
  accept/deny) — реальные данные API 1:1; «Календарь» (С10),
  «Мои автомобили» (С5/С7), «Профиль и документы» (С8) — перенос как
  есть; «Выйти» — POST /api/auth/logout → /instructors. Контракты,
  гвард, редиректы — НЕ МЕНЯЮТСЯ.
- **«Мои документы» `/instructor/documents` на Vue — НОВАЯ страница**:
  вход `frontend/vue/documents.html` + страница
  `frontend/vue/src/pages/documents/`; воспроизводит функциональность
  раздела «Мои документы» (Спринт 8): ВУ и СТС по каждому авто с
  версиями (действует / «Ожидает проверки замены» / отклонено с
  причиной — ОВ-1/ОВ-7), просмотр действующей
  (GET /api/instructor/documents/{doc_id}/file), кнопки
  загрузки/замены с предупреждением FR-71 и явной кнопкой «Заменить»,
  дозагрузка СТС авто без документа. Контракты НЕ МЕНЯЮТСЯ: GET
  /api/instructor/documents, POST /api/instructor/documents/license,
  POST /api/instructor/cars/{id}/photo/sts, авторизованный файл.
  Legacy-монолит documents.html НЕ создается (design-guard BUG-047
  «standalone-страницы запрещены» сохраняется — новая страница сразу
  на каркасе, замены монолита нет). Раздел «Профиль и документы»
  внутри кабинета ОСТАЕТСЯ (e2e не переписываются).
- **Чистка мертвой страницы**: frontend/instructor-cabinet-stub.html +
  frontend/js/instructor/instructor-cabinet-stub.js удаляются, маршрут
  "/instructor/cabinet-stub" исключается из `_PAGE_ROUTES` (задача 1.1;
  grep переходов — пусто, кроме самой карты маршрутов и исторических
  носителей); тесты страницы (§4.4 test_instructor_pages) удаляются
  вместе со страницей; spec-дельта instructor-auth: REMOVED «Заглушка
  кабинета инструктора», MODIFIED «Роутинг после входа по статусу»
  (approved → /instructor/dashboard — фиксация фактического поведения
  с Спринта 2.2).
- **Сборка**: vite.config.mjs — три новых входа (instructors,
  instructor-dashboard, documents — multi-entry MPA, ОВ-3;
  SPA/vue-router/pinia ЗАПРЕЩЕНЫ); scripts/check-budgets.mjs —
  page-чанки расширяются до ВОСЬМИ (сверка состава: 5 существующих +
  3 страницы партии; в решении указано «7 страниц» — арифметическая
  неточность, сверено с задачей СА: фактических входов 8; NFR-26
  «каждая мигрированная страница» выполняется). Dockerfile, compose,
  nginx, CI — БЕЗ ИЗМЕНЕНИЙ: builder-этап собирает dist из всех
  входов.
- **backend/app.py**: маршруты "/instructors",
  "/instructor/dashboard" переключаются на отдачу входов dist (маркер
  `vue:` — механика С11/С12); добавляется маршрут "/instructor/documents"
  → "vue:documents.html"; удаляется "/instructor/cabinet-stub". Все
  /api/*, редиректы, пилотный хендлер /instructors/pending — БЕЗ
  ИЗМЕНЕНИЙ. Legacy instructors.html, js/instructors.js,
  instructor-dashboard.html, js/instructor/dashboard-instructor.js
  удаляются (замена монолита целиком, ADR-008 п.4).
- **Тесты-потребители** переводятся на новые носители — ТОЛЬКО переносы
  источников чтения (прецедент 2.3 пилота, 3.1 С11, 4.1 С12):
  tests/web/test_instructor_pages.py (§4.1 → вход+App.vue+styles.css;
  §4.4 — удаление вместе со страницей), tests/api/test_instructor_
  dashboard.py (PAGE + frontend_source → вход + App.vue + shared),
  tests/api/test_s3_backend.py (needle-носитель дашборда), tests/web/
  test_login_modal.py (консолидация wiring — +shared/loginWiring.js),
  tests/api/test_auth_route.py (список маршрутов: −cabinet-stub,
  +/instructor/documents); в tests/web/test_ui_playwright.py — ТОЛЬКО
  переносы носителей design-guard (tag-balance: +3 vue-входа, −легаси
  дашборда; BUG-047-guard: чтение dash → новые носители; негативный
  список standalone с documents.html — БЕЗ ПРАВОК). Сценарии e2e не
  переписываются (NFR-27): якоря TC-UI-003/005/008/009/010/015/016/
  023/024/025…028/030/033/034/040/042/052, TC-S9UI-003 зеленые без
  правок.
- **Проверка бюджетов NFR-26** на артефактах сборки (npm run
  check:budgets — 8 page-чанков): каждый vendor-чанк ≤150 КБ gzip;
  JS первого захода КАЖДОЙ страницы ≤200 КБ gzip — приемочный шаг
  партии.

## Impact (Последствия)

- Код: `frontend/vue/vite.config.mjs` (+3 входа),
  `frontend/vue/instructors.html`, `frontend/vue/instructor-dashboard.html`,
  `frontend/vue/documents.html` (новые входы),
  `frontend/vue/src/pages/instructors/`,
  `frontend/vue/src/pages/instructor-dashboard/`,
  `frontend/vue/src/pages/documents/` (новые страницы),
  `frontend/vue/src/shared/LoginModal.vue` (вариант разметки),
  `frontend/vue/src/shared/loginWiring.js` (НОВОЕ: консолидация wiring
  входа), `frontend/vue/src/pages/landing/App.vue` (переключение на
  композабл), `frontend/vue/scripts/check-budgets.mjs` (+3 page-чанка);
  `backend/app.py` (три строки карты `_PAGE_ROUTES`).
- Чистка: `frontend/instructor-cabinet-stub.html`,
  `frontend/js/instructor/instructor-cabinet-stub.js` (1.1).
- Удаление: `frontend/instructors.html`, `frontend/js/instructors.js`,
  `frontend/instructor-dashboard.html`,
  `frontend/js/instructor/dashboard-instructor.js` (после переключения
  маршрутов; остальные монолиты — registered/admin-*/cabinet/
  instructor-choice/policy и instructor-bookings — не трогаются).
- Тесты: переносы источников чтения — test_instructor_pages.py,
  test_instructor_dashboard.py, test_s3_backend.py, test_login_modal.py,
  test_auth_route.py, test_ui_playwright.py (только design-guard),
  scripts/check_tag_balance.py (границы — design.md «Границы правок
  тестов»).
- Master-spec: ADDED домен Frontend — «Лендинг инструкторов на Vue
  (/instructors)», «Кабинет инструктора на Vue (/instructor/dashboard)»,
  «Мои документы на Vue (/instructor/documents)»; домен instructor-auth —
  MODIFIED «Роутинг после входа по статусу», REMOVED «Заглушка кабинета
  инструктора».
- Кейпабилити БЕЗ дельт (проверено по openspec/specs/):
  instructor-dashboard (гвард/макет/разделы — поведение сохранено,
  перенос носителя), instructor-documents (раздел, статусная модель,
  загрузка/замена, верификация админом — контракты не меняются;
  новая страница — тот же контракт), instructor-availability,
  instructor-cars, navigation (переходы logout → /instructors, ссылки
  pending/rejected/apply → /instructors сохранены), auth (route/reason
  API — без изменений), PersonalData (без изменений), StudentFlow
  (не затрагивается).
- Зависимости: нет новых пакетов npm (только vue — уже в каркасе);
  зависимостей от параллельных change-пакетов нет.

## Out of scope / допущения

- `instructor-bookings.html` — календарь инструктора (Спринт 10) и
  ученический booking.html/instructor-choice.html — отдельная тяжелая
  партия (решение Заказчика: «следующие партии»).
- admin-контур (admin-login/admin-dashboard/admin-cars/admin-documents) —
  финальная партия миграции.
- Раздел «Профиль и документы» внутри кабинета сохраняется как есть
  (параллельная точка входа к той же функциональности — сознательное
  состояние, design.md «Сознательные ограничения»); ссылки на
  /instructor/documents из сайдбара кабинета НЕ добавляются (сайдбар
  «ровно перечень» — TC-UI-028 без правок); страница достижима прямым
  URL.
- Реальные данные вместо демо в кабинете (доходы, материалы,
  расписание-заглушки) — будущие функциональные партии (решение:
  «демо-данные Спринта 2.2 сохраняются»).
- Редизайн, перенос текстов иными словами, замена бренда — вне объема:
  визуальная эквивалентность текущим экранам (директива «без большого
  переписывания» ADR-008).
- Изменения контрактов: POST /api/auth/login (route/reason),
  GET /api/instructor/{dashboard,summary,requests,students,cars,
  documents}, POST /api/instructor/documents/license,
  POST /api/instructor/cars/{id}/photo/sts, POST /api/auth/logout,
  sessionStorage-ключи (session_token, instructor_rejected_reason,
  open_login*) — НЕ меняются; /api/* каркасом не затрагиваются
  (NFR-27).
- GET /api/instructor/me НЕ СУЩЕСТВУЕТ (сверка backend): гвард
  кабинета/документов — GET /api/auth/me + роль по 401/403
  инструкторских эндпоинтов (design.md «Сверка контрактов»).

## Отслеживание

- FR-10 (лендинг инструкторов, CTA на анкету) → specs/Frontend/spec.md
  «Лендинг инструкторов на Vue (/instructors)»; tasks 3.1.
- FR-13 (вход route/reason, sessionStorage «instructor_rejected_reason»)
  → specs/Frontend/spec.md «Лендинг инструкторов…»; specs/instructor-
  auth/spec.md MODIFIED «Роутинг после входа по статусу»; tasks 3.1.
- FR-18…FR-22 (гвард, макет, ФИО, разделы, выход) → specs/Frontend/
  spec.md «Кабинет инструктора на Vue (/instructor/dashboard)»; tasks 3.2.
- FR-39…FR-41 (запросы, виджеты «Мой день») → там же; tasks 3.2.
- FR-45, FR-69…FR-73 (документы: версии, загрузка/замена FR-71,
  просмотр действующей, без виджетов FR-73) → specs/Frontend/spec.md
  «Мои документы на Vue (/instructor/documents)»; tasks 3.3.
- FR-84 (multi-entry, постраничная миграция, ADR-008) → все дельты
  Frontend; tasks 2.1.
- FR-85 + NFR-27 (e2e без правок сценариев) → дельты (якоря TC-UI-003/
  005/008/009/010/024/028/033/034/052, TC-S9UI-003); tasks 4.1, 6.1.
- NFR-26 (бюджеты 150/200 КБ gzip на артефактах, каждая страница —
  8 входов) → tasks 2.1, 5.1.
- Решение Заказчика п.4 (чистка stub) → specs/instructor-auth/spec.md
  REMOVED; task 1.1.
