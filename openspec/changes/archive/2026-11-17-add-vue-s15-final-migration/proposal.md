# Change: add-vue-s15-final-migration

## Why (Зачем)

Спринт 15 — ФИНАЛ постраничной миграции на Vue (ADR-008, BACKLOG #1):
решение Заказчика 2026-11-12 — «Раскатил. Давай дальше. Добей до конца»
(decisions/2026-11-12-sprint15-go.md). Каркас Vue 3 + Vite — в проде:
пилот (С9, PR#107), статусные формы (С11), лендинг + анкета (С12,
PR#128), инструкторский контур (С14, PR#131). Легаси-HTML в frontend/
остался ровно в ШЕСТИ файлах (сверено с фактом, см. «Сверка состава с
фактом»): cabinet.html, instructor-choice.html, admin-login.html,
admin-dashboard.html, registered.html, policy.html + каталог js/ (7
модулей). Партия выводит последние страницы на каркас и закрывает
миграцию: frontend/ без легаси-HTML, каталог js/ удален целиком,
_PAGE_ROUTES — все значения «vue:». Дубли шапок/модалок легаси×Vue —
временное состояние ADR-008 — исчезают полностью.

Источники требований: ADR-008 (architecture/adr/008-vue3-vite-migration.md —
multi-entry MPA, замена монолита целиком, бюджеты NFR-26, критерий —
зеленый полный e2e); решение Заказчика 2026-11-12 (состав С15);
FR-5…FR-9 (кабинет ученика, requirements.md); FR-31/32/35/36 (каталог и
заявки, sdd.md); FR-24/FR-25 + admin-контур С0/С7/С8 (админка);
FR-76/NFR-25 (политика); FR-84…FR-86, NFR-26/27 (каркас); BUG-047/055/
056/059/060/062 (design-guard'ы).

## Сверка состава с фактом (решение перечисляет состав частично неверно)

Состав решения п.1–3 назван по легаси-конвенции «отдельный файл на
страницу». Фактическое состояние frontend/ (сверено ls'ом и grep'ом):

- **booking.html и instructor-bookings.html НЕ СУЩЕСТВУЮТ** как файлы и
  как маршруты: календарный контур ученика — раздел «Мои брони» ВНУТРИ
  cabinet.html (#sec-bookings, календарь С10: bk-nav ‹ › «Эта неделя»,
  попап #m-book, запрет прошлого); календарный контур инструктора —
  раздел «Календарь» ВНУТРИ instructor-dashboard.html, который УЖЕ на
  Vue с С14. booking/admin-cars отдельно не существуют — мигрируются
  только их НОСИТЕЛИ (разделы), отдельных входов для них НЕТ.
- **admin-cars.html и admin-documents.html НЕ СУЩЕСТВУЮТ**: разделы
  «Автомобили» (#sec-cars-admin) и «Документы» (#sec-documents) внутри
  одной страницы admin-dashboard.html (4 раздела: Пользователи, Заявки
  инструкторов, Автомобили, Документы). Маршруты /admin/cars и
  /admin/documents никогда не регистрировались в _PAGE_ROUTES.
- **Фактический остаток — 6 страниц** (+ js/: student/cabinet.js,
  student/instructor-choice.js, admin/admin-login.js,
  admin/admin-dashboard.js, policy.js, shared/api.js, shared/utils.js —
  policy.js в решении не назван, но является единственным модулем
  policy.html).
- **«~17 входов» → фактически 14**: 8 существующих входов каркаса
  (instructors-pending, instructors-rejected, review-form, index,
  instructor-apply, instructors, instructor-dashboard, documents) + 6
  страниц партии. Решение считало booking/instructor-bookings/
  admin-cars/admin-documents отдельными входами — их не существует.
- **Изъятие больше-не-существующих маршрутов**: в _PAGE_ROUTES таких
  строк НЕТ (все 6 легаси-значений указывают на существующие файлы;
  фантомных маршрутов /booking, /admin/cars, /admin/documents в карте
  нет) — изымать нечего; контроль grep'ом в задаче 5.1.

Правка решения не делается — расхождения зафиксированы здесь и в
design.md «Сверка контрактов решения».

## What Changes (Что меняет)

- **Кабинет ученика `/cabinet` на Vue**: вход frontend/vue/cabinet.html +
  страница frontend/vue/src/pages/cabinet/ (App.vue, main.js,
  styles.css). Перенос 1:1 cabinet.html + js/student/cabinet.js:
  гвард (sessionStorage session_token → GET /api/auth/me с
  X-Session-Token, 401 → toLogin → «/»), подстановка ФИО (FR-5,
  fioOf), чат-бар «Гига ГАИшник» и плитки СЕРВИСЫ (визуал-заглушки,
  BUG-059/060: логотип один — в сайдбаре, без крошек и тегов «В
  КАБИНЕТЕ»), хеш-навигация #/my-requests / #/my-bookings, разделы
  «Мои заявки» (GET/POST /api/student/requests, фильтры data-f,
  «Повторить заявку», 409) и «Мои брони» (календарь С10 bk-*: недели
  ‹ › «Эта неделя», диапазон #bk-range, запрет прошлого, карточка авто
  С7, попап #m-book, POST {availability_id, date}, гонка «Слот уже
  занят»), «Выйти» → POST /api/auth/logout → очистка → «/». Контракты,
  якоря и хеши — НЕ МЕНЯЮТСЯ (TC-UI-019/025/026/027/059/060, BUG-049/
  052, s8-брони — без правок).
- **Выбор инструктора `/instructor-choice` на Vue**: вход
  frontend/vue/instructor-choice.html + страница src/pages/
  instructor-choice/. Перенос 1:1: каталог одобренных (GET
  /api/student/instructors + query-параметры фильтров FR-31/32),
  фильтры (f-trans/f-rating/f-exp/f-day/f-from/f-to/reset/sort),
  карточки (dataset.id, рейтинг {average,count}/«нет отзывов» FR-35,
  свободные часы, авто), «Подать заявку» → POST /api/student/requests
  (409 — «уже есть активная заявка», FR-36), XSS-гигиена (только
  текстовые узлы), сайдбар ученика, logout. Якоря TC-UI-007/059 — без
  правок.
- **Админ-контур на Vue**: входы frontend/vue/admin-login.html +
  frontend/vue/admin-dashboard.html, страницы src/pages/admin-login/ и
  src/pages/admin-dashboard/. Перенос 1:1: вход (POST /api/admin/login
  → sessionStorage admin_token → /admin-dashboard; ошибка → .err.show)
  и панель — гвард admin_token (нет/401 → /admin-login), сессии
  X-Admin-Token in-memory, 4 раздела одной страницы: Пользователи
  (GET /api/admin/users + «↓ Выгрузить CSV» — fetch blob →
  users.csv; BOM/«;»/санитизация — backend, контракты 1:1), Заявки
  инструкторов (таблица без «Действий» — BUG-046, модалка #ic-*, confirm()
  диалоги, deny с обязательным комментарием, license-image по токену),
  Автомобили (#ac-*, комплектность, validate), Документы (#dc-*,
  верификация ВУ/СТС, предпросмотр blob, reject с причиной). Якоря
  TC-UI-006/011/013/014/024… admin-сценариев — без правок.
- **Мелкие на Vue**: `/registered` — вход frontend/vue/registered.html +
  src/pages/registered/ (заглушка «Регистрация завершена» 1:1, включая
  alert-перехват кнопки «Личный кабинет» — wiring не изобретается);
  `/policy` — вход frontend/vue/policy.html + src/pages/policy/
  (оболочка БЕЗ текста: fetch GET /api/policy, «Версия: X от Y» в
  #policy-meta, абзацы — текстовыми узлами в #policy-text (интерполяция
  Vue = textContent-семантика, NFR-25), отказ API → честное
  .policy-error сообщение). Якоря TC-UI-044, test_policy, test_static —
  без правок (кроме переносов носителей — design.md).
- **Сборка**: vite.config.mjs +6 входов (cabinet, instructor-choice,
  admin-login, admin-dashboard, registered, policy — имена по
  маршрутам, паттерн С11/С12/С14; SPA/vue-router/pinia ЗАПРЕЩЕНЫ —
  ОВ-3); scripts/check-budgets.mjs — PAGES расширяется до 14
  (сверка: в решении «~17» — арифметика фантомных страниц, design.md);
  Dockerfile/compose/nginx/CI — БЕЗ ИЗМЕНЕНИЙ (builder собирает все
  входы).
- **backend/app.py**: 6 строк _PAGE_ROUTES переключаются на «vue:<вход>»
  (одна сессия с удалением файлов — механика С11/С12/С14); хендлер
  GET /js/{path} УДАЛЯЕТСЯ (каталог js/ мертв — потребителей нет);
  /vue/assets/{path}, VUE_DIST_DIR-цикл, _PAGE_REDIRECTS (#/my-requests,
  #/my-cars — хеши живы в Vue-версиях), пилотный хендлер /instructors/
  pending, все /api/* — БЕЗ ИЗМЕНЕНИЙ. Легаси-файлы (6 html + js/
  целиком) удаляются тем же коммитом.
- **Тесты-потребители** — ТОЛЬКО переносы источников чтения (прецедент
  2.3 пилота, 3.1 С11, 4.1 С12/С14): tests/web/test_cabinet_page.py
  (вербатим FR-9 → вход + App.vue + styles.css против СУЩЕСТВУЮЩИХ
  мокапов — мокапы НЕ синхронизируются, design.md), tests/api/
  test_integration_sprint1.py (byte-equality легаси-файла → признак
  входа каркаса; маркеры — зелен без правок за счет дословного
  комментария wiring во входе), tests/api/test_policy.py (носитель
  '/js/policy.js'), tests/api/test_qa_instructor_flow.py (носитель
  password_hash-проверки), tests/api/test_s3_backend.py (носитель
  needle'ов cabinet), tests/web/test_ui_playwright.py — ТОЛЬКО 4
  переноса design-guard (BUG-046-фрагменты, TC-UI-007 снятие
  route.fulfill легаси-файла → живой маршрут, TC-UI-019 чтение cab/
  choice → новые носители, tag-balance: −2 легаси +6 входов) —
  сценарии не переписываются (NFR-27); scripts/check_tag_balance.py
  (DEFAULT-список).

## Impact (Последствия)

- Код: frontend/vue/vite.config.mjs (+6 входов), frontend/vue/{cabinet,
  instructor-choice,admin-login,admin-dashboard,registered,policy}.html
  (новые входы), frontend/vue/src/pages/{шесть страниц}/, frontend/vue/
  src/shared/utils.js (дополнение: fioOf, fmtDate — по потребностям,
  дословно из js/shared/utils.js), frontend/vue/scripts/
  check-budgets.mjs (14 page-чанков); backend/app.py (6 строк карты,
  удаление хендлера /js/{path}).
- Чистка (финал миграции): frontend/cabinet.html,
  frontend/instructor-choice.html, frontend/admin-login.html,
  frontend/admin-dashboard.html, frontend/registered.html,
  frontend/policy.html, каталог frontend/js/ ЦЕЛИКОМ (7 модулей;
  shared/api.js уже 1:1 существует в vue/src/shared/api.js с С9 —
  легаси-копия умирает без переноса).
- Тесты: переносы носителей — test_cabinet_page.py,
  test_integration_sprint1.py, test_policy.py,
  test_qa_instructor_flow.py, test_s3_backend.py, test_ui_playwright.py
  (только 4 design-guard точки), scripts/check_tag_balance.py
  (границы — design.md «Границы правок тестов»).
- Master-spec: ADDED домен Frontend — требования шести страниц;
  «Финал миграции — frontend/ без легаси-HTML»; MODIFIED
  «Постраничная миграция — страница заменяет HTML-монолит целиком»
  (миграция ЗАВЕРШЕНА: legacy-монолитов и каталога js/ больше нет).
  Кейпабилити БЕЗ дельт (поведение сохранено, перенос носителя —
  проверено по openspec/specs/): cabinet, registration, PersonalData,
  admin-moderation, instructor-documents, instructor-cars,
  student-instructor-choice, student-requests, booking, navigation,
  auth (гварды, route/reason, CSV, policy-артефакт — контракты не
  меняются).
- Зависимости: нет новых npm-пакетов; от параллельных change-пакетов
  зависимостей нет.

## Out of scope / допущения

- Функциональные изменения страниц — ВНЕ объема: registered остается
  заглушкой (alert «Личный кабинет появится…» и href=
  «landing-students.html» под onclick-перехватом сохраняются как есть —
  реальная цель кнопки не изобретается); чат-бар/quick/плитки
  «Обучение ПДД»/«Онлайн экзамен» — визуал-заглушки (alert из мокапа);
  разделы «Платежи»/«Настройки» админки — заглушки soon().
- Разнос админки на /admin/cars и /admin/documents — НЕ выполняется
  (маршруты никогда не существовали; BUG-047: разделы внутри одной
  страницы).
- BOM/санитизация CSV, X-Admin-Token сессии, все /api/* — backend, без
  изменений.
- Редизайн, замена текстов, синхронизация мокапов — вне объема
  (mockup-verbatim сохраняется переносом носителей — design.md).
- sdd.md, code-reviews/, test-model/, design/mocks/ — исторические
  носители, не правятся.
- Дистрибутив dist/ и node_modules — не в git; сборка dist —
  обязательный шаг перед прогоном pytest (уже так для «/» с С12).

## Отслеживание

- FR-5…FR-9 (кабинет: ФИО, чат-бар/плитки, гвард, выход, мокап FR-9) →
  specs/Frontend/spec.md «Кабинет ученика на Vue (/cabinet)»; tasks 4.2.
- FR-31/32/35/36 (каталог, фильтры, рейтинг, заявка) → «Выбор
  инструктора на Vue (/instructor-choice)»; tasks 4.1.
- FR-24/FR-25 + админ-контур (вход, CSV, заявки, авто, документы) →
  «Вход администратора на Vue (/admin-login)», «Админ-панель на Vue
  (/admin-dashboard)»; tasks 2.1/2.2.
- FR-76/NFR-25 (политика-оболочка, текст не в HTML) → «Политика на Vue
  (/policy)»; tasks 3.1.
- TC-REG-016/018 («Регистрация завершена») → «Страница «Регистрация
  завершена» на Vue (/registered)»; tasks 3.1.
- FR-84 (multi-entry, постраничная миграция) → все дельты Frontend;
  tasks 1.1.
- FR-85 + NFR-27 (e2e без правок сценариев) → дельты (якоря TC-UI-006/
  007/011/013/014/019/025/026/027/044/052/059/060, BUG-049/052); tasks
  5.1, 7.1.
- NFR-26 (бюджеты 150/200 КБ gzip на артефактах; каждая страница —
  теперь 14 входов) → tasks 1.1, 6.1.
- Финал миграции (frontend/ без легаси, js/ удален, все маршруты vue:) →
  «Финал миграции…» + MODIFIED «Постраничная миграция…»; tasks 5.1.
- Решение Заказчика 2026-11-12 (состав, критерии) → весь пакет.
