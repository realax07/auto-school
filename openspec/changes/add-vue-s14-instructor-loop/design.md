# Design: add-vue-s14-instructor-loop

Источники решений: ADR-008 (architecture/adr/008-vue3-vite-migration.md —
стек, multi-entry, замена монолита целиком, бюджеты, план «кабинеты»);
решение Заказчика 2026-11-09 (decisions/2026-11-09-sprint14-go.md —
состав С14: instructors + dashboard + documents + чистка stub; вне
состава: instructor-bookings, admin-контур); прецеденты —
add-vue-framework-pilot (задачи 2.1/2.3/4.1; arch-review-002 MAJ-1 —
«судьба legacy-тестов удаленной страницы»), add-vue-s11-status-forms
(vue:-маркеры, переносы источников чтения, MIN-2 «строковая
конкатенация сохраняется»), add-vue-s12-landing-apply (архив —
структура пакета, shared/LoginModal.vue, консолидация wiring «на живом
втором потребителе», переносы 4.1); sdd.md §15.5/§15.6 (route/reason,
маршруты); BUG-047 (standalone-страницы запрещены), BUG-055/056
(семантика модалки входа).

## Baseline (что есть, без этого пакета не меняется)

- Каркас Vue 3 + Vite — frontend/vue/: multi-entry (входы
  instructors-pending, instructors-rejected, review-form, index,
  instructor-apply), manualChunks (vue → 'vue', сторонние пакеты →
  чанки по пакетам, /src/shared/ → 'shared'), base '/vue/', dist не в
  git, pinned-версии (vue 3.5.44, vite 8.3.5, @vitejs/plugin-vue
  6.0.10), dev-proxy /api/* → 127.0.0.1:8390, npm run check:budgets
  (5 page-чанков).
- backend/app.py: `_PAGE_ROUTES` — карта маршрутов страниц ("/instructors"
  → instructors.html, "/instructor/dashboard" → instructor-dashboard.html,
  "/instructor/cabinet-stub" → instructor-cabinet-stub.html); значения с
  маркером `vue:<вход dist>` читаются из VUE_DIST_DIR (404 при
  отсутствии dist; media_type text/html; charset=utf-8) — механика
  С11/С12; пилотный хендлер /instructors/pending — вне карты;
  статика `GET /vue/assets/{path}` (.js/.css) существует.
  `_PAGE_REDIRECTS` (/my-cars → /instructor/dashboard#/my-cars и др.) —
  без изменений.
- Контур: Dockerfile содержит node builder-этап; CI flow.yml собирает
  dist ПЕРЕД pytest; compose/nginx — без сборки; bare-metal (FR-57) —
  `npm ci && npm run build` перед деплоем.
- Легаси в объеме: `frontend/instructors.html` (19 КБ) +
  `frontend/js/instructors.js` (лендинг инструкторов: hero, форматы,
  возможности, нижний CTA #open-form, модалка m-login — ПОСЛЕДНИЙ
  дубль контура входа; wiring — postJSON через js/shared/api.js) и
  `frontend/instructor-dashboard.html` (85 КБ) +
  `frontend/js/instructor/dashboard-instructor.js` (кабинет: гвард,
  «Мой день», Календарь С10, Мои ученики С8, Мои автомобили С5/С7,
  «Профиль и документы» С8, модалки mc*/m-view/m-replace; onclick-инлайны
  в разметке — toast/navTo/logout).
- Контур модалок входа: shared/LoginModal.vue + RegisterModal.vue (С12)
  используются лендингом «/» (wiring — src/pages/landing/App.vue);
  легаси-дубль m-login в instructors.html (id — те же
  login-email/login-password/login-error/login-submit/login-close;
  отличия разметки: p без .sub, span вместо label, btn primary/ghost,
  БЕЗ строки «Нет аккаунта? #to-register») + wiring js/instructors.js
  (data-open-login; закрытие НЕ снимает open_login-флаги — на этой
  странице их никто не ставит, BUG-055).
- Маршрут входа инструктора: approved (users, role='instructor') →
  route='cabinet' → клиент → /instructor/dashboard (backend/auth/auth.py:
  `route = "cabinet" if role == "instructor" else "student-cabinet"`);
  waiting → route='pending' без токена; deny → route='rejected' + reason
  без токена. GET /api/instructor/me НЕ СУЩЕСТВУЕТ (сверка
  backend/auth, backend/instructor) — гвард страниц: GET /api/auth/me
  (X-Session-Token; 401 → «/») + 401/403 инструкторских данных
  (FR-18).
- Данные кабинета: GET /api/instructor/dashboard (демо-флаг), GET
  /api/instructor/summary (students, today_lessons — «Мой день»),
  GET /api/instructor/requests (запросы, accept/deny), GET
  /api/instructor/students (пары, С8), GET /api/instructor/cars;
  выход — POST /api/auth/logout → clearSession → /instructors
  (dashboard-instructor.js:1679).
- Документы (С8): GET /api/instructor/documents (ВУ + СТС по каждому
  авто; active_version/pending/last_rejected), GET
  /api/instructor/documents/{doc_id}/file (только владелец), POST
  /api/instructor/documents/license, POST
  /api/instructor/cars/{id}/photo/sts; клиентская валидация JPEG/PNG
  ≤5 МБ (mcValidatePhoto); замена — диалог #m-replace с явной кнопкой
  (FR-71); просмотр — модалка #m-view (BUG-054: стрелки над фото,
  Esc); дозагрузка СТС авто без документа (FR-69).
- Stub: frontend/instructor-cabinet-stub.html (5 КБ) +
  js/instructor/instructor-cabinet-stub.js; маршрут "/instructor/
  cabinet-stub" в `_PAGE_ROUTES`; переходов на маршрут из frontend/
  нет (grep — только сама карта, исторические sdd.md/code-reviews и
  тесты) — недостижима с Спринта 2.2.
- NFR-26 свод С11/С12: бюджеты проверяются для КАЖДОЙ мигрированной
  страницы (сейчас 5 входов, с партией — 8).

## Сверка контрактов решения (расхождения зафиксированы)

- **Бюджеты «7 страниц» → фактически 8 входов.** Состав решения:
  instructors + instructor-dashboard + documents — новые/мигрируемые;
  существующие входы каркаса: instructors-pending, instructors-rejected,
  review-form, index, instructor-apply (5). 5 + 3 = 8 page-чанков.
  Указанные в решении «станет 7 страниц» и «бюджеты 7 чанков» —
  арифметическая неточность состава (сверено с задачей СА: «фактически
  8 входов; сверяй»); check:budgets расширяется до 8. Правка решения
  не делается — расхождение фиксируется здесь и в tasks 2.1/5.1.
- **GET /api/instructor/me не существует.** В задаче решения указан
  «GET /api/instructor/me (гвард)» — такого эндпоинта в backend нет
  (сверка роутера); фактический гвард кабинета/документов: GET
  /api/auth/me (X-Session-Token) → 401 → «/», роль гарантируют
  401/403 инструкторских эндпоинтов (FR-18). Контракты не вводятся и
  не меняются — гвард переносится как в legacy.
- **documents.html — только вход каркаса.** В решении страница названа
  «frontend/documents.html» (легаси-конвенция именования); создание
  legacy-монолита запрещено design-guard BUG-047 (test_ui_playwright:
  `not (frontend/documents.html).exists()` — «разделы ВНУТРИ кабинетов,
  standalone-страницы запрещены») и правила ADR-008 «параллельное
  существование версий не допускается». Страница создается СРАЗУ
  входом каркаса: frontend/vue/documents.html; критерий решения
  «documents.html — в archive легаси» выполняется тривиально —
  легаси-версии страницы не существует ни до, ни после партии.
  Негативный инвариант BUG-047 остается БЕЗ ПРАВОК (проверяет
  frontend/ корень — vue-входы его не нарушают).

## Потребители легаси-файлов (полный список, судьба каждого)

| Потребитель | Что читает | Судьба в пакете |
|---|---|---|
| backend/app.py `_PAGE_ROUTES` ("/instructors", "/instructor/dashboard", "/instructor/cabinet-stub") | отдача файлов | 1.1 — исключение cabinet-stub из карты; 4.1/4.2 — "/instructors" → "vue:instructors.html", "/instructor/dashboard" → "vue:instructor-dashboard.html", NEW "/instructor/documents" → "vue:documents.html" (одна сессия 4.1+4.2) |
| tests/web/test_instructor_pages.py §4.1 (4 теста: существование/тексты мокапа landing-instructors, CTA-wiring, футер) | page("instructors.html"), frontend_source("instructors.html"), split("<style>") | 4.1 — перенос носителей: page() → вход frontend/vue/instructors.html; frontend_source → вход + src/pages/instructors/App.vue; CSS-сверка → src/pages/instructors/styles.css (перенос дословный); фрагменты контракта (`location.href='/instructors/apply'`, `data-open-login`, `postJSON('/api/auth/login'`, отсутствие `location.href='/'`) — дословно в App.vue/loginWiring.js |
| tests/web/test_instructor_pages.py §4.4 (2 теста stub: тексты, guard-wiring) | page("instructor-cabinet-stub.html"), frontend_source(...) | 1.1 — УДАЛЕНИЕ вместе со страницей (прецедент «судьба legacy-тестов удаленной страницы» — arch-review-002 MAJ-1 пилота); §4.2/§4.3 (анкета, pending/rejected — уже Vue С9/С11/С12) — БЕЗ ПРАВОК |
| tests/api/test_instructor_dashboard.py (12 тестов: PAGE + frontend_source — тексты/CSS мокапа dashboard-instructor, сайдбар data-tab, wiring FR-18/20/22) | FRONTEND/"instructor-dashboard.html", frontend_source("instructor-dashboard.html") | 4.1 — перенос носителей: PAGE → вход frontend/vue/instructor-dashboard.html; frontend_source → вход + App.vue (+shared при импортах); фрагменты wiring (`fetch('/api/instructor/dashboard'`, `'X-Session-Token'`, `res.status===401||res.status===403`, `location.href='/'`, `navTo`, `document.querySelectorAll('.nav button')`, `class="demo-tag">демо<`) — дословно в плоском JS App.vue |
| tests/api/test_s3_backend.py::test_s4_pages_wired_to_real_api_shapes | frontend_source("instructor-dashboard.html") (needles: api/instructor/cars, "cars/'+t.carId+'/photo/'+t.angle", "c.sts_url") | 4.1 — перенос носителя: вход + App.vue; needles дословны — строковая конкатенация URL в Vue-коде сохраняется (прецедент MIN-2 С11) |
| tests/web/test_ui_playwright.py ( behavioral: TC-UI-003 лендинг, TC-UI-005 вход→layout дашборда, TC-UI-008/024 календарь/виджет, TC-UI-009 запросы, TC-UI-010 выход→/instructors, TC-UI-015/016/023/028 my-cars/BUG-051, TC-UI-025/026/027 брони/пустые, TC-UI-030 авто-флоу, TC-UI-033/034/040/042 документы (раздел кабинета), accept-flow, xss, TC-UI-052 модалка instructors, TC-S9UI-003 rejected-редирект) | селекторы/маршруты/ожидания | БЕЗ ПРАВОК — id/классы/тексты/хеши сохраняются в Vue-версиях (NFR-27): .app>aside/main (grid 2 колонки), .user b, .icon-btn[title='Выйти'], data-tab="…", #sec-*/#stu-*/#rq-*/#lic-docs/#sts-docs/#m-view/#m-replace, .brand em «Сбер», #m-login/#login-* |
| tests/web/test_ui_playwright.py (test_s4_pages_tag_balance, список файлов) | frontend/<filename> | 4.1 — перенос носителя design-guard: instructor-dashboard.html → vue/instructor-dashboard.html; + vue/instructors.html, + vue/documents.html (прецедент vue/index.html С12; инструктор-choice/cabinet/review-form/index остаются) |
| tests/web/test_ui_playwright.py (test_back_links_lead_to_role_home, BUG-047 design-guard) | frontend/instructor-dashboard.html (data-tab перечень, «Профиль и документы», отсутствие «Бронирования»/sec-bookings) + негативный список standalone (в т.ч. documents.html ЗАПРЕЩЕН) | 4.1 — перенос носителя чтения dash → вход + App.vue; НЕГАТИВНЫЙ СПИСОК STANDALONE — БЕЗ ПРАВОК (vue/documents.html его не нарушает); instructor-choice.html/cabinet.html/review-form носители не меняются |
| tests/api/test_auth_route.py::test_new_static_routes_served | список маршрутов (200 text/html): "/instructors", …, "/instructor/cabinet-stub" | 1.1 — из списка УДАЛЯЕТСЯ "/instructor/cabinet-stub" (маршрут снят); 4.2 — ДОБАВЛЯЕТСЯ "/instructor/documents"; остальные пункты и инвариант 200 text/html — без правок логики |
| tests/web/test_login_modal.py (vue_landing_source: вход + App.vue + shared/api.js + LoginModal + RegisterModal; WIRING_FRAGMENTS route-маппинга) | носители wiring входа лендинга | 3.1 — перенос носителя: + src/shared/loginWiring.js (wiring doLogin вынесен из App.vue в композабл — консолидация на живом втором потребителе /instructors); фрагменты контракта дословны в композабле; REGISTER-wiring и LOGIN_MODAL_TEXTS — остаются на текущих носителях |
| scripts/check_tag_balance.py (DEFAULT) | frontend/instructor-dashboard.html | 4.1 — перенос: frontend/vue/instructor-dashboard.html (+ новые входы по потребности); скрипт — инфра-инструмент приемки, вне NFR-27 |
| frontend/cabinet.html, design/mocks/*.html, sdd.md, code-reviews/, test-model/ | комментарии-референсы, исторические носители | БЕЗ ПРАВОК (не потребители кода; исторические носители не считаются — прецедент 4.1 С12) |

## Границы правок тестов (NFR-27 — разграничение)

- «0 правок сценариев» по-прежнему означает: селекторы, маршруты,
  ожидания и логика сценариев tests/web/test_ui_playwright.py не
  переписываются. Допустимый дифф по этому файлу — ТОЛЬКО переносы
  носителей design-guard: (а) список параметризации tag-balance
  (−легаси instructor-dashboard.html, +3 vue-входа — прецедент С11/С12);
  (б) чтение dash в test_back_links_lead_to_role_home (BUG-047) → вход
  + App.vue. НЕ трогаются: негативный список standalone (documents.html
  и др.), все поведенческие сценарии (включая TC-UI-028 «сайдбар РОВНО
  перечень»). Контроль: `git diff tests/web/test_ui_playwright.py`
  содержит только эти правки (задача 4.1, проверка в 6.1).
- tests/web/test_instructor_pages.py, tests/api/test_instructor_
  dashboard.py, tests/api/test_s3_backend.py, tests/web/
  test_login_modal.py, tests/api/test_auth_route.py — легаси-тесты-
  потребители: правки разрешены (вне test_ui_playwright.py; прецедент
  2.3 пилота, 3.1 С11, 4.1 С12). Право правки НЕ означает право
  ослаблять: проверяемые тексты, контракты, wiring-фрагменты —
  дословно; меняется носитель источника. Удаление §4.4 (2 теста) —
  прецедент «судьба legacy-тестов удаленной страницы» (arch-review-002
  MAJ-1 пилота: тесты удаленной страницы удаляются без замены).
- Подстановки «стековых фрагментов legacy» (задокументированные
  эквиваленты Vue — прецеденты С11/С12):
  - test_instructor_pages §4.1 / test_login_modal / test_bug001:
    `err.style.display='block'`/`err.textContent=` → эквивалент — текст
    сервера рендерится в #login-error из реактивного состояния (проп
    error, интерполяция {{ }}); `postJSON('/api/auth/login'`,
    `setToken(res.data.token)`, `location.href='/instructors/apply'`,
    `sessionStorage.setItem('instructor_rejected_reason'`, весь
    route-маппинг (`route==='cabinet'`→/instructor/dashboard,
    `route==='pending'`→/instructors/pending, `route==='rejected'`+
    sessionStorage ДО редиректа, `route||'student-cabinet'`) и порядок
    `res.status===200&&res.data.ok` — СОХРАНЯЮТСЯ дословно в
    shared/loginWiring.js (плоский JS) — правки носителя минимальны;
    `location.href='/';` отсутствует (BUG-055) — инвариант сохранен.
  - test_instructor_dashboard / test_s3_backend: wiring-фрагменты
    (`fetch('/api/instructor/dashboard'`, `'X-Session-Token'`,
    `res.status===401||res.status===403`, `location.href='/'`,
    `cars/'+t.carId+'/photo/'+t.angle`, `c.sts_url`, `navTo`,
    `document.querySelectorAll('.nav button')`) — дословно (плоский
    fetch-JS в App.vue; конкатенация строк сохранена — MIN-2 С11);
    `document.getElementById(...).textContent=` / `style.display=` /
    `innerHTML=''` (отрисовка списков) → эквиваленты Vue — интерполяция,
    v-show, реактивные списки (design.md «Страницы на Vue»);
    inline `onclick="toast(...)"`/`navTo('…')` разметки → эквивалент —
    @click-обработчики App.vue с теми же действиями и текстами (фрагмент
    `class="demo-tag">демо<` — дословно в разметке входа/App.vue).

## Точки входа Vite (решение)

- vite.config.mjs, `rollupOptions.input` дополняется тремя входами
  (правила пилота — без изменений):
  - `instructors` → frontend/vue/instructors.html (dist/instructors.html;
    имя по маршруту /instructors — паттерн С11/С12);
  - `instructor-dashboard` → frontend/vue/instructor-dashboard.html;
  - `documents` → frontend/vue/documents.html (имя по сегменту маршрута
    /instructor/documents).
- Вход = статическая разметка страницы (эквивалент legacy 1:1) +
  модуль-скрипт /src/pages/<page>/main.js; до гидрации видна та же
  разметка (паттерн пилота/С11/С12; «Разметку держать синхронной с
  App.vue»).
- Страницы: src/pages/instructors/ (main.js, App.vue, styles.css),
  src/pages/instructor-dashboard/ (main.js, App.vue, styles.css),
  src/pages/documents/ (main.js, App.vue, styles.css). Стили — дословный
  перенос из legacy html (без редизайна): у лендинга — сверка с мокапом
  landing-instructors (TC §4.1), у кабинета — с макетом
  dashboard-instructor (test_instructor_dashboard), у документов — с
  разделом «Профиль и документы» кабинета.
- scripts/check-budgets.mjs: карта page-чанков расширяется до восьми
  (instructors-pending, instructors-rejected, review-form, index,
  instructor-apply, instructors, instructor-dashboard, documents);
  замыкание первого захода и «чужие page-чанки» — по КАЖДОЙ странице;
  бюджеты не меняются (NFR-26).
- Новых npm-зависимостей НЕТ; pinia/vue-router НЕ вводятся (ОВ-3).

## Судьба контура модалок входа (решение — последний дубль)

- **Консолидация wiring (обещание С12 выполнено)**: сабмит входа
  (doLogin: payload email/password → postJSON('/api/auth/login') →
  setToken → route-маппинг §15.5 с sessionStorage
  «instructor_rejected_reason» ДО редиректа) выносится в
  `src/shared/loginWiring.js` — композабл с плоским JS и дословными
  фрагментами контракта. Потребители: App.vue лендинга «/»
  (переключение с локальной doLogin — фрагменты переезжают дословно) и
  App.vue инструкторского лендинга (перенос js/instructors.js 1:1).
  Open/close-семантика остается ПОСТРАНИЧНО (различаются по legacy):
  лендинг «/» — data-open/data-close + снятие open_login/open_login_from
  при закрытии (BUG-056); /instructors — data-open-login, открытие
  локально БЕЗ флагов, закрытие без работы с флагами (BUG-055).
- **shared/LoginModal.vue — вариант разметки**: добавляется проп
  `variant` ('landing' — дефолт, текущая разметка С12 дословно;
  'instructors' — разметка варианта из instructors.html дословно: p
  без .sub, span вместо label, btn primary/ghost, БЕЗ alt-строки
  «Нет аккаунта?» и #to-register). Носитель текстов лендинга
  (LOGIN_MODAL_TEXTS в vue/index.html между комментариями-маркерами) —
  БЕЗ ИЗМЕНЕНИЙ. Дефолтный рендер компонента не меняется — e2e лендинга
  (TC-UI-001/053) и test_login_modal зеленые без правок.
- **Легаси-дубль умирает**: instructors.html удаляется в 4.1 — после
  партии копий m-login вне каркаса нет (проверка 4.1: `git grep -l
  'id="m-login"' frontend -- '*.html'` — только frontend/vue/*);
  конфликтов id нет: разные страницы = разные бандлы (multi-entry),
  модалки никогда не оказываются в одном DOM.
- Сверка контракта ключей: Vue-версия пишет те же ключи
  (session_token, instructor_rejected_reason; open_login* — только
  лендинг, как в legacy) — поведение polling/rejected (экран С11 читает
  причину) не зависит от точки входа.

## Роуты и статика (backend/app.py)

- 1.1: "/instructor/cabinet-stub" исключается из карты (маршрут снят —
  страница мертва; удаляется одновременно с файлами и тестами §4.4).
- 4.1/4.2 (одна сессия): "/instructors" и "/instructor/dashboard"
  исключаются из легаси-отдачи и регистрируются с маркером каркаса
  ("vue:instructors.html" / "vue:instructor-dashboard.html"); добавляется
  "/instructor/documents" → "vue:documents.html" (одна строка карты —
  «следующие партии миграции добавляют страницу одной строкой»);
  легаси-файлы удаляются тем же коммитом. Цикл отдачи при префиксе
  `vue:` — без изменений (VUE_DIST_DIR, 404 без dist).
- Статика `/vue/assets/{path}` — БЕЗ ИЗМЕНЕНИЙ (покрывает новые чанки);
  шрифты/картинки страницам не нужны (системные шрифты, эмодзи-глифы).
- `_PAGE_REDIRECTS` (/my-cars → /instructor/dashboard#/my-cars — хеш
  раздела «Мои автомобили» сохраняется в Vue-версии), пилотный хендлер
  /instructors/pending, `/api/*` — БЕЗ ИЗМЕНЕНИЙ (NFR-27).
- Между 4.1 и 4.2 переходное состояние (маршрут без отдачи) существует
  только внутри одной сессии; промежуточный пуш/PR не делается; гейт
  партии — 6.1.

## Страница /instructors на Vue (3.1)

- Перенос 1:1 (без редизайна): шапка (бренд «СберАвтошкола — Платформа
  для инструкторов» с .brand em «Сбер» — якорь TC-UI-010; nav-якоря
  #format/#benefits/#start; кнопки: «Войти» header-cta с
  data-open-login href="/", «Стать инструктором ↗» → /instructors/apply),
  hero (eyebrow «Новая система обучения вождению», h1 «Учи водить.
  Меняй подход.», lead, actions, subnote, декоративная .visual — glass-
  карточки «Профиль инструктора/Автомобиль/Ваше расписание»; svg-блок
  «Ваш следующий маршрут» отсутствует — navigation spec), секции
  «Два формата подключения» (choice own/sber → /instructors/apply),
  «Работа в новом формате» (3 feature), нижний CTA («Готов
  подключиться?» + #open-form), футер; фоновые градиенты и медиазапросы
  (850/560) — дословно.
- Поведение js/instructors.js — в App.vue (1:1): #open-form →
  location.href='/instructors/apply'; data-open-login → открытие
  #m-login локально (body overflow hidden, фокус #login-email) БЕЗ
  sessionStorage-флагов; закрытие — #login-close/[data-close]/Esc
  (клик по фону НЕ закрывает — обработчика нет); сабмит —
  shared/loginWiring.js (route/reason §15.5).
- Якоря e2e дословно: .header-cta[href="/instructors/apply"], .btn
  primary[href="/instructors/apply"], .choice[data-type=own|sber],
  #open-form, .brand em («Сбер»), #m-login (.overlay.open),
  #login-close, #login-email/#login-password/#login-submit/
  #login-error (TC-UI-003/010/052).

## Страница /instructor/dashboard на Vue (3.2 — крупнейший перенос)

- Перенос 1:1 (без редизайна; мокап design/mocks/dashboard-instructor
  — носитель test_instructor_dashboard): каркас .app (aside сайдбар +
  main — прямые дети, grid 2 колонки — якоря TC-UI-005), topbar (crumb,
  #page-title, .date-chip, .user с #avatar/#user-fio, «Выйти»
  .icon-btn[title='Выйти']), hello-панель (#hello-name, .kicker),
  разделы: «Мой день» (виджеты w-students/w-requests/w-today — данные
  GET /api/instructor/summary + /api/instructor/requests; stats,
  панели «Ближайшее занятие», «Последние операции», «Быстрые
  действия» — демо как в legacy), «Календарь» (С10: недели,
  availability, попап слота — перенос как есть), «Мои ученики» (С8:
  вкладки Ученики/Запросы учеников, accept/deny), «Мои автомобили»
  (С5/С7: галерея ракурсов, валидация, СТС, hash #/my-cars), «Профиль
  и документы» (С8: lic-docs/sts-docs, m-view, m-replace, doc-file);
  demo-tag «демо» у нереализованных разделов — дословно; сайдбар —
  РОВНО текущий перечень (BUG-051: без «Бронирования», «Мой автомобиль»,
  «Запросы учеников»; «Мои документы» носит имя «Профиль и документы»).
- Поведение dashboard-instructor.js — в App.vue (плоский JS, фрагменты
  контракта дословно): гвард (fetch('/api/auth/me', X-Session-Token) →
  401 → '/'; fetch('/api/instructor/dashboard') → 401/403 → '/'; ФИО/
  инициалы из ответа — FR-20), текущая дата Europe/Moscow, navTo
  (переключение секций + хеш-синхронизация #/my-cars + BUG-058
  закрытие модалок), loadSummary/loadRequests/openStudents (текст
  stu-error дословно), календарь С10, авто С7, документы С8
  (openDocs/docCardNode/версии/mcValidatePhoto/mcUpload), toast, logout
  (POST /api/auth/logout → clearSession → /instructors). DOM-хелперы
  node()/textContent (XSS-гигиена review-001) — эквиваленты Vue на
  реактивных списках; DOM-структура и классы разметки — 1:1.
- Якоря e2e дословно (сценарии не правятся): .app>aside/main, .user b,
  .icon-btn[title='Выйти'], #sec-calendar/#sec-students/#sec-cars/
  #sec-docs, #stu-tabs/#stu-cards/#rq-list/#rq-filters, #week/#cal-*/
  #w-students*/#w-requests*/#w-today*, #lic-docs/#sts-docs/#lic-n/
  #sts-count/#no-license*, #m-view/#view-*/#m-replace/#rep-*/#doc-file,
  data-tab="…", .demo-tag, #page-title/#crumb, hash #/my-cars
  (TC-UI-005/008/009/010/015/016/023/024/025…028/030/033/034/040/042,
  accept-flow, xss).

## Страница /instructor/documents на Vue (3.3 — новая)

- НОВАЯ страница (нет legacy-предка): функциональность — вынос раздела
  «Мои документы» кабинета (С8) на отдельный маршрут по решению
  Заказчика. Оболочка страницы — минимальная, в стиле кабинета: шапка
  (бренд → /instructor/dashboard, заголовок «Мои документы», «← В
  кабинет», «Выйти» с механикой dashboard-logout → /instructors);
  контент — перенос карточной модели раздела 1:1: ВУ + СТС по каждому
  авто, карточки (thumb + mcLoadImg авторизованного файла, бейдж
  «Действует»/«нет СТС», блок «Ожидает проверки замены», «Отклонено»
  с причиной — ОВ-1/ОВ-7, docVersionLine «версия N · загружено …»),
  просмотр — модалка #m-view (BUG-054: стрелки над фото, Esc, клик по
  фону закрывает), кнопки Загрузить/Заменить (диалог #m-replace с
  предупреждением FR-71 и явной кнопкой; первая загрузка — без
  предупреждения), дозагрузка СТС авто без документа (GET
  /api/instructor/cars + merge как openDocs), клиентская валидация
  JPEG/PNG ≤5 МБ (mcValidatePhoto — тексты = серверным), тосты
  (тексты legacy дословно: «Замена ВУ отправлена на проверку
  администратору…» и др.), перезагрузка списка после успешной
  загрузки.
- Гвард страницы — как в кабинете (сверка «GET /api/instructor/me»):
  fetch('/api/auth/me', X-Session-Token) → 401 → location.href='/';
  данные — GET /api/instructor/documents (401/403 → '/'); контракты
  загрузки — POST /api/instructor/documents/license ('file'),
  POST /api/instructor/cars/{id}/photo/sts ('photo') — БЕЗ ИЗМЕНЕНИЙ.
- Виджетов в разделе нет (FR-73); админ-верификация — вне страницы
  (только чтение статусов, «только чтение контура» решения).
- Ссылки из кабинета НЕ добавляются (сайдбар «ровно перечень» —
  TC-UI-028 без правок); раздел «Профиль и документы» кабинета
  остается (параллельная точка входа — см. «Сознательные ограничения»).
- Якоря: id контента 1:1 с разделом (#lic-docs/#sts-docs/#m-view/
  #m-replace/#doc-file и классы .doc/.thumb/.ds-badge/.subver) —
  будущие e2e страницы пишутся на тех же соглашениях; новых тестов
  пакет не добавляет (покрытие функциональности — существующие
  сценарии раздела кабинета).

## Stub-чистка (1.1)

- Удалить frontend/instructor-cabinet-stub.html и frontend/js/
  instructor/instructor-cabinet-stub.js; исключить "/instructor/
  cabinet-stub" из `_PAGE_ROUTES`.
- Подтверждение недостижимости (grep по репо): ссылок/переходов на
  "/instructor/cabinet-stub" в frontend/, backend/ (кроме строки
  карты), tests/ — нет; исторические носители (sdd.md §15.6, code-
  reviews/, test-model/) не считаются потребителями (прецедент 4.1
  С12).
- Тесты §4.4 test_instructor_pages (2 теста) — удалить (судьба
  legacy-тестов удаленной страницы — MAJ-1 пилота); test_auth_route:
  список статических маршрутов — убрать "/instructor/cabinet-stub".
- Spec-дельта instructor-auth: REMOVED «Заглушка кабинета инструктора»
  (Reason: недостижима с 2.2, удалена решением Заказчика; защита
  кабинета — «Доступ к кабинету инструктора» instructor-dashboard);
  MODIFIED «Роутинг после входа по статусу» (approved →
  /instructor/dashboard — фиксация фактического поведения с Спринта
  2.2, sdd.md; сценарий «Пользователь найден» переведен с заглушки на
  кабинет).
- Спринт-2.2 наследие: FR-13-сценарии waiting/deny/без-пароля — без
  изменений.

## Обработка ошибок — реакции 1:1 legacy (сводно)

| Ответ | Лендинг /instructors | Кабинет | Документы |
|---|---|---|---|
| 200 | login → setToken → route-маппинг §15.5 | данные разделов отрисовываются; toast-подтверждения действий | список отрисовывается; после загрузки — перезагрузка статусов |
| 401/403 | res.data.error → #login-error (единое сообщение) | fetch me/dashboard 401/403 → location.href='/' | то же — на «/» |
| 422 | res.data.error → #login-error | честный тост с текстом сервера (mcUpload/apiSend) | то же + список не меняется до успеха |
| 413/415 | n/a | mcValidatePhoto до отправки (тексты = серверным) | то же |
| network | «Ошибка сети» → #login-error | toast «Не удалось загрузить…» (тексты legacy) | toast «Не удалось загрузить документы» |
| закрытие модалки | крестик/«Отмена»/Esc; фон НЕ закрывает; флаги open_login* не трогаются | BUG-058: смена раздела закрывает все .backdrop.open | m-view — фон закрывает; m-replace — фон НЕ закрывает (как legacy) |

## Решения по НФТ

- **NFR-26:** бюджеты на артефактах сборки (npm run check:budgets —
  расширение 2.1: ВОСЕМЬ page-чанков): каждый vendor-чанк ≤150 КБ
  gzip; JS первого захода КАЖДОЙ страницы ≤200 КБ gzip. Кабинет —
  крупнейший перенос (≈85 КБ html + ~96 КБ JS wiring — фактический
  размер dashboard-instructor.js 98 649 Б, сверено arch-review-001
  MIN-1): стили уходят в
  styles.css-чанк (CSS вне JS-бюджета), wiring — плоский JS без
  библиотек в page-чанке; вендорного кода в чанках страниц нет;
  запас бюджета сохраняется (vue-чанк ~20 КБ gzip + shared). Замеры —
  в отчете 5.1; при превышении — сокращение зависимостей, не
  ослабление проверки.
- **NFR-27:** полный набор tests/web/test_ui_playwright.py зелен без
  правок СЦЕНАРИЕВ (допустимый дифф — только переносы носителей
  design-guard, см. «Границы правок тестов»); маршруты, редиректы,
  гварды и /api/* — без ломающих изменений.
- Наследуются без изменений: ADR-001 (статика тем же сервисом), FR-57
  (bare-metal), ADR-006 (multi-stage, pinned), ADR-009 (ПД: согласия
  анкеты/логина не затрагиваются), NFR-2/NFR-3 (тосты, параметризация
  — не затрагиваются).

## Сознательные ограничения (задокументированы)

- **Демо-данные Спринта 2.2 сохраняются**: панели «Ближайшее занятие»,
  «Последние операции», «Быстрые действия», разделы «Доходы и выплаты»,
  «Материалы и обучение» и приветственные заглушки переносятся как
  есть (с пометками «демо»); реальные данные — будущие функциональные
  партии (решение Заказчика). «Мой день»/«Мои ученики» — реальные
  данные API (как в legacy с С3/С8).
- **instructor-bookings и ученический booking/instructor-choice,
  admin-контур — вне состава** (решение: «следующие партии»);
  остаются легаси на С15+.
- **Двойная точка входа к документам**: раздел «Профиль и документы»
  остается в кабинете (e2e TC-UI-028/033/034/040/042 не переписываются),
  /instructor/documents — отдельная страница к той же функциональности.
  Альтернатива «перенести раздел со страницы кабинета» отклонена:
  потребовала бы правок e2e-сценариев (против NFR-27) и сайдбара
  («ровно перечень»). Ссылку из кабинета на новую страницу НЕ
  добавляем — сайдбар/контент кабинета остаются 1:1; страница
  достижима прямым URL (точки входа — будущие партии по мере
  развития кабинета).
- Дубли стилей/разметки шапки между легаси-монолитами (cabinet,
  instructor-choice, admin-*) и Vue-страницами — временное состояние
  постраничной миграции ADR-008, исчезает на С15+.
- dist и node_modules — не в git; входы и компоненты — в git.
- Пилотный хендлер /instructors/pending остается выделенным вне карты —
  унификация не делается (наследование С11/С12).
- Переходное состояние 4.1→4.2 (маршруты без отдачи) — внутри одной
  сессии; гейт — 6.1.
- Переносы носителей design-guard в test_ui_playwright.py (tag-balance,
  BUG-047-guard) — задокументированные исключения из «0 правок»;
  альтернативы отклонены: сохранение легаси-файлов «мертвыми» (против
  ADR-008 п.4), правка frontend_source/conftest (шире необходимого
  диффа).
- Контроль бюджетов остается приемочным ручным шагом (не CI-гейт) —
  наследование пилота.
- sdd.md в пакетах миграции не ведется (прецедент пилота/С11/С12);
  исторические носители (sdd.md §15.5/15.6, code-reviews, test-model,
  design/mocks) не правятся.
- Порядок задач: stub-чистка → входы+заглушки → лендинг инструкторов →
  кабинет → документы → удаление легаси+маршруты → бюджеты → полный
  e2e (утвержденный порядок решения; кабинет — до документов: крупнейший
  перенос интегрируется раньше, документы зависят только от 2.1).

## Соответствие ADR-001/006/008/009

Отступлений нет: multi-entry MPA (страница = отдельная точка входа,
SPA/vue-router/pinia запрещены — ОВ-3); замена монолита целиком с
удалением легаси (ADR-008 п.4); vendor-сплит и бюджеты NFR-26 — правила
пилота, свод С11/С12 (каждая страница, теперь 8); статика тем же
сервисом (ADR-001) через существующие /vue/assets; контур доставки без
изменений (ADR-006); критерий приема — зеленый полный e2e (ADR-008
п.6, FR-85/NFR-27); ПД — согласия/политика не затрагиваются (ADR-009).
