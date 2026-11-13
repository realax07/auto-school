# Design: add-vue-s15-final-migration

Источники решений: ADR-008 (architecture/adr/008-vue3-vite-migration.md —
стек, multi-entry, замена монолита целиком, бюджеты, критерий e2e);
решение Заказчика 2026-11-12 (decisions/2026-11-12-sprint15-go.md —
«добей до конца»; СОСТАВ СВЕРЕН С ФАКТОМ: booking/instructor-bookings/
admin-cars/admin-documents как отдельные файлы и маршруты НЕ существуют —
разделы внутри cabinet.html и admin-dashboard.html, календарь инструктора
уже на Vue с С14); прецеденты — add-vue-framework-pilot (задачи 2.1/2.3,
arch-review-002 MAJ-1 «судьба legacy-тестов удаленной страницы»),
add-vue-s11-status-forms (vue:-маркеры, переносы носителей, MIN-2
«строковая конкатенация сохраняется»), add-vue-s12-landing-apply
(структура пакета, tag-balance переносы, BUG-062-дельта), add-vue-s14-
instructor-loop (кабинет-перенос: static-вход + App.vue поверх #app +
styles.css; verbatim-мокап dashboard-instructor через перенос носителей;
s14 design.md «Границы правок тестов»); BUG-047 (standalone-страницы
запрещены), BUG-055/056 (семантика модалок — контур входа ученика уже
Vue), BUG-059/060/062 (кабинет/choice: один логотип, без крошек/тегов,
без плитки-аватара).

## Baseline (что есть, без этого пакета не меняется)

- Каркас Vue 3 + Vite — frontend/vue/: multi-entry (8 входов:
  instructors-pending, instructors-rejected, review-form, index,
  instructor-apply, instructors, instructor-dashboard, documents),
  manualChunks (vue → 'vue', сторонние → чанки по пакетам,
  /src/shared/ → 'shared'), base '/vue/', dist не в git, pinned-версии,
  dev-proxy /api/* → 127.0.0.1:8390, npm run check:budgets (8
  page-чанков).
- backend/app.py: `_PAGE_ROUTES` — 13 маршрутов (8 «vue:», 5 легаси:
  /registered, /admin-login, /admin-dashboard, /cabinet,
  /instructor-choice, /policy — 6); цикл отдачи `vue:` читает
  VUE_DIST_DIR (404 без dist); хендлер GET /js/{filepath:path} —
  отдача frontend/js/ (application/javascript); статика
  GET /vue/assets/{path} (.js/.css); `_PAGE_REDIRECTS` (/my-cars →
  /instructor/dashboard#/my-cars, /my-requests → /cabinet#/my-requests);
  пилотный хендлер /instructors/pending вне карты.
- Легаси (фактический остаток, 6 страниц + 7 модулей js/):
  - cabinet.html (384 строки; 33.7 КБ) + js/student/cabinet.js (626
    строк; импортирует toast/el/fmtDate/nowMoscow/fioOf из
    ../shared/utils.js): гвард session_token + GET /api/auth/me
    (X-Session-Token; 401/!ok → toLogin → «/»), ФИО (fioOf) в .uname и
    «Добро пожаловать, {name}!» в .greet b, logout POST /api/auth/logout
    → removeItem → «/» после любого ответа; navTo по .snav
    (data-tab Главная/Мои заявки/Мои брони, data-goto →
    /instructor-choice) с хеш-синхронизацией #/my-requests #/my-bookings;
    «Мои заявки»: GET/повтор POST /api/student/requests, фильтры
    data-f all/new/accepted/denied (n-new/n-accepted/n-denied),
    instructor_id:r.instructor_id, бейджи st-new/st-acc/st-den,
    комментарии отказов, «Оставить отзыв» → /review?instructor=…;
    «Мои брони» С10 (bk-*): пара bk-pair (без пары — bk-nopair),
    календарь bk-grid с навигацией bk-prev/bk-this/bk-next (#bk-range,
    горизонт ±12 месяцев, запрет прошлого .past), карточка авто С7
    (bk-car-*, photo_url, бейдж ОВ-2), легенда, попап #m-book
    (data-close-book, bk-instr/bk-day/bk-time/bk-car, POST
    /api/student/bookings {availability_id, date}; 409 → «Слот уже
    занят»), «Мои брони» bk-list/bk-count (статусы bk-st-*, retry);
    чат-бар (.assistant, .send, .quick — alert-заглушки), плитки
    (#tile-instructor → /instructor-choice, #tile-requests → раздел,
    «СКОРО»-заглушки alert); #toast вне контента.
  - instructor-choice.html (200 строк) + js/student/instructor-choice.js
    (162 строки; импортирует api/toLogin/clearSession/getToken из
    ../shared/api.js + toast/el из ../shared/utils.js): гвард без токена
    → toLogin; ФИО (api /api/auth/me → #uname); каталог GET
    /api/student/instructors + buildQuery (transmission/min_rating/
    min_experience/free_weekday/free_from/free_to), fetchSeq-гонка
    фильтров; сортировка sort (rating/exp/name, localeCompare 'ru');
    карточки article.card[data-id] (icard-инициалы, Стаж + expWord,
    рейтинг {average,count} / «☆ Нет отзывов», meta pill'ы авто,
    slotrow часов, apply-кнопка: sent-кэш, 409 без кэширования —
    review-001 #14, тосты дословно); empty-состояние (#empty,
    empty-reset); reset; logout (POST /api/auth/logout → clearSession →
    «/»); сайдбар ученика (a.snav на /cabinet, /cabinet#/my-requests,
    /cabinet#/my-bookings — TC-UI-019: href="/cabinet" в разметке).
  - admin-login.html (30 строк) + js/admin/admin-login.js (postJSON из
    ../shared/api.js): POST /api/admin/login {login,password} → 200 +
    ok + token → sessionStorage admin_token → location.href=
    '/admin-dashboard'; иначе/сеть → #err.classList.add('show').
  - admin-dashboard.html (373 строки; 30.5 КБ) + js/admin/
    admin-dashboard.js (665 строк; БЕЗ импортов shared — свой fetch):
    гвард admin_token (нет → /admin-login; 401 → /admin-login); разделы
    showSection (users/applications/cars/documents; inline onclick в
    навигации): Пользователи (GET /api/admin/users → #rows
    textContent-only, «Записей: N», «↓ Выгрузить CSV» exportCsv: fetch
    /api/admin/users/export.csv → blob → a.download='users.csv'),
    Заявки (GET /api/admin/instructor-applications → #app-rows; модалка
    #ic-backdrop: карточка #ic-*, license-image fetch → objectURL,
    approve с confirm('Одобрить заявку?…'), deny #ic-deny-box с
    обязательным комментарием (#ic-deny-confirm disabled до текста) —
    BUG-046/045-паттерн), Автомобили С7 (#ac-*: GET
    /api/admin/cars/completeness +status, фильтры data-f, модалка
    чек-листа, POST /api/admin/cars/{id}/validate, тост #ac-toast),
    Документы С8 (#dc-*: GET /api/admin/documents?status=, вкладки
    pending/history, фильтры, предпросмотр blob objectURL, verify POST,
    reject POST с причиной #dc-reason — кнопка disabled до текста).
  - registered.html (28 строк; заглушка С0): «Регистрация завершена»,
    note «демонстрационная страница спринта-0», кнопки «На главную» (/)
    и «Личный кабинет» — href="landing-students.html" ПОД onclick
    alert('Заглушка: личный кабинет появится в следующем спринте');
    return false (переход никогда не выполняется — файла
    landing-students.html давно нет).
  - policy.html (35 строк) + js/policy.js (44 строки; БЕЗ импортов):
    оболочка БЕЗ текста (NFR-25); fetch /api/policy → 200
    {ok,version,date,text} → metaEl.textContent = 'Версия: '+version+'
    от '+date; абзацы split(/\n\s*\n/) → createTextNode/textContent
    (НЕ innerHTML); 500/не-JSON/сеть → showError(): #policy-meta
    пустой, #policy-text → p.policy-error «Политика временно
    недоступна. Попробуйте позже».
  - js/shared/api.js — ДОСЛОВНО равен vue/src/shared/api.js (С9-перенос:
    TOKEN_KEY, getToken/setToken/clearSession/toLogin, api,
    handleAuthFail, apiGet, apiSend, postJSON — функции совпадают
    1:1, сверено diff'ом семантики); js/shared/utils.js — надмножество
    vue/src/shared/utils.js: в Vue-версии есть toast/nowMoscow/expWord,
    НЕТ el/fioOf/initials/fmtDate.
- Контур входа ученика: модалки shared/LoginModal.vue + RegisterModal.vue
  на лендинге «/» (С12; wiring loginWiring.js — route/reason §15.5,
  ученик → location.href='/cabinet'); cabinet легаси СВОИХ модалок НЕ
  содержит (вход только через гвард-редирект на «/») — дублировать не
  требуется (BUG-055/056 затрагивают лендинг/инструкторов — не кабинет).
- Вербатим-мокапы (design/mocks/): cabinet-student.html — носитель
  test_cabinet_page.py (FR-9: посимвольные фрагменты + все CSS-строки
  мокапа — подмножество CSS страницы; плитки-фрагмент дословно);
  admin-dashboard.html — носитель design-guard'а BUG-046
  (test_admin_dashboard_bug046_mock_sync_fragments: 4 фрагмента в обе
  стороны). Мокапы СИНХРОНИЗИРОВАНЫ с легаси-разметкой (BUG-059/062 —
  синхронизация мокапов выполнялась при ИЗМЕНЕНИИ разметки; сейчас
  разметка не меняется).
- Бюджеты NFR-26: свод С11/С12/С14 — бюджеты на КАЖДОЙ мигрированной
  странице (сейчас 8 входов, с партией — 14).
- CI flow.yml собирает dist ПЕРЕД pytest; API-тесты (TestClient) уже
  зависят от dist для «/» (маркер test_static) — зависимость для
  /cabinet и др. после переключения маршрутов не новая.

## Сверка контрактов решения (расхождения зафиксированы)

- **Состав п.1–3 назван по несуществующим файлам.** booking.html,
  instructor-bookings.html, admin-cars.html, admin-documents.html в
  frontend/ отсутствуют; маршрутов /booking, /instructor/bookings,
  /admin/cars, /admin/documents в _PAGE_ROUTES нет. Календарный контур
  ученика (С10) — раздел #sec-bookings внутри cabinet.html; админ-авто и
  админ-документы — #sec-cars-admin/#sec-documents внутри
  admin-dashboard.html; календарь инструктора — уже Vue (С14).
  Следствие: 6 страниц партии, 6 новых входов, 14 page-чанков (в решении
  «~17» — счет по фантомным страницам). Отдельный вывод: «изъятие
  больше-не-существующих маршрутов» — изымать нечего, контроль grep'ом
  в 5.1 (все легаси-значения карты указывают на существующие файлы).
- **«booking/admin-cars отдельно не существуют» — разделы мигрируют в
  составе носителей.** Никаких новых страниц «booking»/«admin-cars» не
  создается (BUG-047: standalone-разделы запрещены — негативный список
  test_back_links_lead_to_role_home сохраняется БЕЗ ПРАВОК; vue-входы
  живут в frontend/vue/, корень frontend/ не нарушают — прецедент
  vue/documents.html С14).
- **policy.js в решении не назван** — фактический единственный модуль
  policy.html; удаляется вместе с js/ (переносится в App.vue policy).
- **Бюджеты «gzip-замеры»** — без изменения порогов (150/200 КБ gzip);
  расширяется только список PAGES в check-budgets (8 → 14).

## Дерево входов Vite (решение)

- vite.config.mjs, rollupOptions.input дополняется ШЕСТЬЮ входами
  (правила пилота — без изменений; имена = имена артефактов маршрутов,
  паттерн С11/С12/С14): `cabinet` → frontend/vue/cabinet.html;
  `instructor-choice` → frontend/vue/instructor-choice.html;
  `admin-login` → frontend/vue/admin-login.html; `admin-dashboard` →
  frontend/vue/admin-dashboard.html; `registered` →
  frontend/vue/registered.html; `policy` → frontend/vue/policy.html.
- Вход = статическая разметка страницы (эквивалент legacy 1:1, включая
  дословные HTML-комментарии wiring) + <link rel="stylesheet"
  href="/src/pages/<page>/styles.css"> + <script type="module"
  src="/src/pages/<page>/main.js">; #app оборачивает контент, #toast —
  вне #app (переживает гидрацию); до гидрации видна та же разметка
  (паттерн пилота/С11/С12/С14; «Разметку держать синхронной с App.vue» —
  App.vue повторяет разметку входа как template).
- Страницы: src/pages/{cabinet, instructor-choice, admin-login,
  admin-dashboard, registered, policy}/ (main.js, App.vue, styles.css).
  Стили — дословный перенос <style> легаси (без редизайна); у cabinet —
  сверка с мокапом cabinet-student (FR-9 через test_cabinet_page), у
  admin-dashboard — с мокапом admin-dashboard (BUG-046-гвард), у choice
  — классы 1:1 (мокапы choice-a/b тестами не читаются — поведение
  TC-UI-007/059).
- scripts/check-budgets.mjs: PAGES расширяется до 14 (…, cabinet,
  instructor-choice, admin-login, admin-dashboard, registered, policy);
  замыкание первого захода и «чужие page-чанки» — по КАЖДОЙ странице;
  пороги НЕ меняются (NFR-26).
- Новых npm-зависимостей НЕТ; pinia/vue-router НЕ вводятся (ОВ-3).

## Судьба каталога js/ и shared-логики (полный список)

| Легаси-файл | Потребители | Судьба в пакете |
|---|---|---|
| js/student/cabinet.js | только cabinet.html | 4.2 — wiring 1:1 в src/pages/cabinet/App.vue (плоский JS; фрагменты контракта дословно); хелперы — из vue/src/shared/ |
| js/student/instructor-choice.js | только instructor-choice.html | 4.1 — wiring 1:1 в src/pages/instructor-choice/App.vue |
| js/admin/admin-login.js | только admin-login.html | 2.1 — wiring 1:1 в src/pages/admin-login/App.vue; postJSON — из vue/src/shared/api.js (существует с С9) |
| js/admin/admin-dashboard.js | только admin-dashboard.html | 2.2 — wiring 1:1 в src/pages/admin-dashboard/App.vue |
| js/policy.js | только policy.html | 3.1 — логика 1:1 в src/pages/policy/App.vue (fetch + split абзацев + текстовые узлы) |
| js/shared/api.js | cabinet.js, instructor-choice.js, admin-login.js | ПЕРЕНОС НЕ ТРЕБУЕТСЯ: vue/src/shared/api.js уже содержит все функции дословно (С9-перенос, сверено) — легаси-копия удаляется с каталогом |
| js/shared/utils.js | cabinet.js, instructor-choice.js | vue/src/shared/utils.js ДОПОЛНЯЕТСЯ по потребностям (дословный перенос): fioOf, fmtDate (cabinet: ФИО FR-5, даты заявок); el/initials НЕ переносятся (DOM-хелпер не нужен на Vue — интерполяция/реактивные списки; choice считает инициалы инлайн — переносится как есть); toast/nowMoscow/expWord уже там |
| каталог js/ целиком + хендлер GET /js/{path} | — | 5.1 — удаление всех 7 модулей + rmdir; хендлер удаляется (потребителей нет: grep frontend_source-носителей и /js/ ссылок — пусто после переносов; test_policy-носитель '/js/policy.js' переведен в 3.1-волне) |

## Стратегия вербатим-мокапов (решение — мокапы НЕ синхронизируются)

- FR-9 дословность (test_cabinet_page.py) и BUG-046-фрагменты
  (test_ui_playwright) переносятся на новые носители БЕЗ правки мокапов:
  сравниваемые фрагменты/CSS-строки мокапа проверяются против входа
  frontend/vue/<page>.html + App.vue + styles.css (прецедент С14:
  test_instructor_dashboard §TC-FR19D-007 — «все CSS-правила мокапа —
  дословно (носитель — styles.css страницы)» + фрагменты во входе/компоненте).
- Обоснование: прецедент BUG-055/059/062 — мокапы синхронизируются, когда
  МЕНЯЕТСЯ разметка страницы (фиксы по решению Заказчика). Здесь
  семантика и разметка не меняются (перенос 1:1) — синхронизировать
  нечего; правка мокапов создала бы дифф в design-носителях без
  содержательной причины. Мокапы остаются зафиксированными артефактами
  (исторические носители не правятся).
- Технические следствия (в задачи 4.2/2.2): (а) комментарий wiring
  cabinet.html («Wiring (единственные отличия от мокапа)…») переносится
  во вход ДОСЛОВНО — им же держатся wiring-маркеры
  test_integration_sprint1 (CABINET_WIRING_MARKERS: «/api/auth/me»,
  «X-Session-Token», «/api/auth/logout» в resp.text маршрута);
  (б) CSS-строки мокапа — в styles.css страницы без переформатирования
  (проверка построчная); (в) плитки-фрагмент и структурные фрагменты
  (hero/frame, user, greet, assistant, footer) — во входе и App.vue
  дословно; (г) BUG-046-фрагменты admin (badge.wait CSS, thead без
  «Действия», rowhint, ic-deny-confirm disabled) — CSS в styles.css,
  разметка во входе/App.vue дословно; негативный инвариант
  «<th>Действия</th>» отсутствует — сохранен.

## Переносы тестов ПОЛНЫМ списком (потребители легаси → носители)

| Тест | Что читает сегодня | Судьба в пакете |
|---|---|---|
| tests/web/test_cabinet_page.py (7 тестов) | CABINET = frontend/cabinet.html; frontend_source("cabinet.html"); MOCKUP | 4.2 (в волне чистки 5.1) — перенос носителей: CABINET → frontend/vue/cabinet.html; frontend_source → вход + App.vue; CSS-сверка → src/pages/cabinet/styles.css (построчно); фрагменты — дословно; MOCKUP — БЕЗ ПРАВОК. Право правки — прецедент 2.3 пилота/4.1 С12; ослаблений нет (тексты/структура/CSS — те же) |
| tests/api/test_integration_sprint1.py::test_cabinet_page_served | resp.text /cabinet: CABINET_MARKERS + CABINET_WIRING_MARKERS | 5.1 — БЕЗ ПРАВОК: маркеры держатся статической разметкой и дословным комментарием wiring во входе (см. «Стратегия вербатим-мокапов») |
| tests/api/test_integration_sprint1.py::test_cabinet_page_is_cabinet_html_file | resp.text == frontend/cabinet.html (byte-equality легаси) | 5.1 — АДАПТАЦИЯ носителя: легаси-файл удален — byte-equality заменяется на признак входа каркаса (200 + "/vue/assets/" в resp.text; прецедент сценария «обслуживается каркасом Vue»); «судьба legacy-теста удаленного носителя» — arch-review-002 MAJ-1 |
| tests/web/test_static.py (PAGES) | маршруты /, /registered, /admin-login, /admin-dashboard — маркеры («СберАвтошкола», «Регистрация завершена», «Админка», «Пользователи») | БЕЗ ПРАВОК: маркеры — в статических входах (h1/бренд); маршруты отдают dist (TestClient — dist собран, уже так для «/» с С12) |
| tests/api/test_policy.py::test_s9_policy_api_and_page_guest | page.text: 'id="policy-meta"', 'id="policy-text"', '/js/policy.js'; текста политики в исходнике нет | 5.1 — перенос носителя ОДНОЙ строки: '/js/policy.js' → признак входа каркаса ('/vue/assets/'); id-якоря и grep-контроль текста — БЕЗ ПРАВОК |
| tests/api/test_policy.py::test_s9_policy_text_absent_from_frontend_sources | rglob frontend/** (*.html, *.js) — текста политики нет нигде | БЕЗ ПРАВОК: зелен после чистки (источников меньше; .vue не сканируется — см. «Сознательные ограничения»); текст политики в .vue отсутствует по построению (оболочка рендерит из API) |
| tests/api/test_qa_instructor_flow.py::test_tcmod002_…no_hash_in_logs_or_ui | frontend/admin-dashboard.html: «password_hash» нет в UI | 5.1 — перенос носителя: вход frontend/vue/admin-dashboard.html + src/pages/admin-dashboard/App.vue (инвариант тот же) |
| tests/api/test_s3_backend.py::test_s4_pages_wired_to_real_api_shapes (checks["cabinet.html"]) | frontend_source("cabinet.html"): needles «api/student/requests», «instructor_id:r.instructor_id» | 5.1 — перенос носителя: вход + App.vue; needles ДОСЛОВНЫ (сокращенная запись свойства объекта сохраняется в плоском JS App.vue — прецедент MIN-2 С11) |
| tests/web/test_ui_playwright.py::test_admin_dashboard_bug046_mock_sync_fragments | frontend/admin-dashboard.html + design/mocks/admin-dashboard.html | 5.1 — перенос носителя: page_html → вход + App.vue; MOCKUP — БЕЗ ПРАВОК (фрагменты дословно; негативный инвариант «Действия» сохранен) |
| tests/web/test_ui_playwright.py::test_student_choice_filters_narrow_and_apply_request (TC-UI-007) | _serve_frontend: route.fulfill /instructor-choice телом frontend/instructor-choice.html | 5.1 — перенос носителя: перехват СНИМАЕТСЯ — страница читается живым маршрутом (он существует с С3-7.1; вход из dist; ассеты /vue/assets — тем же сервером; API-моки _route_json и _seed_session — БЕЗ ПРАВОК). Альтернатива «fulfill собранным dist/instructor-choice.html» отклонена: скрытая зависимость e2e от артефактов сборки с хэш-именами ассетов; селекторы/ожидания сценария — БЕЗ ПРАВОК |
| tests/web/test_ui_playwright.py::test_back_links_lead_to_role_home (TC-UI-019, BUG-047-guard) | cab = frontend/cabinet.html; choice = frontend/instructor-choice.html (data-tab/sec-bookings/href) | 5.1 — перенос носителя design-guard: cab → вход + App.vue; choice → вход + App.vue; НЕГАТИВНЫЙ СПИСОК standalone (my-cars/my-requests/documents/booking/instructor-bookings/admin-cars) — БЕЗ ПРАВОК (vue-входы его не нарушают) |
| tests/web/test_ui_playwright.py::test_s4_pages_tag_balance | параметризация: «cabinet.html», «instructor-choice.html», 6 vue-входов | 5.1 — перенос носителя design-guard: −2 легаси, +6 vue-входов (cabinet, instructor-choice, admin-login, admin-dashboard, registered, policy) — прецедент С12/С14 |
| tests/web/test_ui_playwright.py — ВСЕ ОСТАЛЬНЫЕ сценарии | маршруты/селекторы/ожидания (гвард 401, хеши #/my-requests#/my-bookings, bk-* календарь С10, #m-book, #tile-*, admin #ic-/#ac-/#dc- + page.on("dialog"), TC-UI-044 policy, TC-UI-059/060) | БЕЗ ПРАВОК (NFR-27): якоря, классы, тексты, хеши, confirm()-диалоги сохраняются в Vue-версиях дословно |
| tests/web/test_bug001.py, test_login_modal.py, test_instructor_pages.py | контур входа лендинга/инструкторов (Vue с С12/С14) | БЕЗ ПРАВОК (партия их носители не трогает; редирект логина → /cabinet сохранен) |
| tests/api/test_register.py, test_admin.py, test_admin_users.py (CSV BOM/санитизация), test_auth_route.py | API-контракты | БЕЗ ПРАВОК: /api/* не меняются; список маршрутов test_auth_route партию не содержит (легаси-маршруты там не перечислены) |
| scripts/check_tag_balance.py (DEFAULT) | frontend/instructor-choice.html, frontend/admin-dashboard.html, frontend/cabinet.html | 5.1 — перенос: −3 легаси, +6 vue-входов (инфра-инструмент приемки, вне NFR-27) |

Контроль полноты: grep по frontend/{cabinet,instructor-choice,admin-
login,admin-dashboard,registered,policy}.html и frontend/js в tests/
и scripts/ после 5.1 — пусто (задача 5.1, готовность).

## Границы правок тестов (NFR-27 — разграничение)

- «0 правок сценариев»: селекторы, маршруты, ожидания и логика
  behavioral-сценариев tests/web/test_ui_playwright.py не переписываются.
  Допустимый дифф по файлу — РОВНО четыре точки: (а) BUG-046-носитель,
  (б) TC-UI-007 снятие route.fulfill, (в) TC-UI-019 носители cab/choice,
  (г) список параметризации tag-balance (−2/+6). Контроль:
  `git diff tests/web/test_ui_playwright.py` содержит только эти правки
  (задача 5.1, проверка в 7.1).
- Легаси-тесты-потребители (test_cabinet_page, test_integration_sprint1,
  test_policy, test_qa_instructor_flow, test_s3_backend) — правки
  разрешены (прецедент 2.3 пилота, 3.1 С11, 4.1 С12/С14). Право правки
  НЕ означает право ослаблять: фрагменты, needles, маркеры и инварианты
  — дословно; меняется носитель источника. Удаление byte-equality —
  прецедент «судьба legacy-тестов удаленной страницы».
- Подстановки «стековых фрагментов legacy» (задокументированные
  эквиваленты Vue — прецеденты С11/С12/С14):
  - `document.getElementById(...).textContent=`/`style.display=`/
    `innerHTML=''`/`appendChild(el(...))` (отрисовка списков/карточек) →
    эквиваленты Vue — интерполяция {{ }}, v-show/v-if, реактивные
    списки; XSS-правило «только textContent» выполняется построением
    (интерполяция создает текстовые узлы).
  - `err.classList.add('show')` (admin-login) → эквивалент — класс
    .show из реактивного состояния ошибки; текст «Неверный логин или
    пароль» — дословно в разметке.
  - inline `onclick="showSection(...)"`/`exportCsv()`/`soon()` разметки
    → эквивалент — @click-обработчики App.vue с теми же действиями;
    window.confirm('Одобрить заявку?…') — СОХРАНЯЕТСЯ (e2e
    page.on("dialog") без правок).
  - строковая конкатенация URL/строк (`'Версия: '+v+' от '+d`,
    `'Записей: '+data.count`, `api/admin/instructor-applications/'+id+…`)
    — СОХРАНЯЕТСЯ дословно (MIN-2 С11; e2e to_have_text exact).
- НЕ трогаются: мокапы design/mocks/, негативный список standalone,
  все /api/*, _PAGE_REDIRECTS, sessionStorage-ключи (session_token,
  admin_token).

## Роуты и статика (backend/app.py)

- 5.1 (одна сессия с удалением файлов): «/registered» →
  «vue:registered.html», «/admin-login» → «vue:admin-login.html»,
  «/admin-dashboard» → «vue:admin-dashboard.html», «/cabinet» →
  «vue:cabinet.html», «/instructor-choice» →
  «vue:instructor-choice.html», «/policy» → «vue:policy.html»; легаси
  6 html + js/ удаляются тем же коммитом; хендлер GET /js/{path}
  удаляется. Цикл отдачи `vue:` — без изменений (VUE_DIST_DIR, 404 без
  dist). Между задачами 1.1–4.2 переходного состояния «маршрут без
  отдачи» НЕТ — легаси обслуживается до 5.1 (переключение всех шести
  строк одним коммитом после готовности всех входов; промежуточные
  пуш/PR безопасны: e2e зелен на легаси).
- Статика /vue/assets/{path} — БЕЗ ИЗМЕНЕНИЙ (покрывает новые чанки);
  шрифты/картинки страницам не нужны (системные шрифты, эмодзи-глифы).
- _PAGE_REDIRECTS (/my-cars → /instructor/dashboard#/my-cars,
  /my-requests → /cabinet#/my-requests) — БЕЗ ИЗМЕНЕНИЙ: хеш-синхронизация
  воспроизводится в App.vue cabinet (navTo пишет #/my-requests —
  TC-UI-019/BUG-047-редиректы живут). Пилотный хендлер
  /instructors/pending — без изменений (наследование С11/С12/С14).

## Страницы партии (перенос 1:1 — свод)

- **/cabinet (4.2 — крупнейший перенос)**: гвард/ФИО/logout, хеш-навигация
  и разделы sec-home/sec-requests/sec-bookings, «Мои заявки» (фильтры,
  бейджи, retry, /review-ссылка), календарь С10 (навигация недель,
  #bk-range, запрет прошлого, bk-nopair, пара+авто С7, попап #m-book,
  POST {availability_id, date}, 409 «Слот уже занят», bk-list статусы/
  retry) — логика выверена в С10/С13 и уже переносилась 1:1 в С14 для
  дашборда; тот же подход (плоский JS в App.vue, реактивные списки).
  Якоря e2e дословно: .side-brand, header .logout, #tile-instructor/
  #tile-requests, .snav [data-tab], #sec-*, #/my-requests, #/my-bookings,
  #list/#noreq/#go-catalog, #bk-*, #m-book/[data-close-book], #toast,
  .uname/.greet b (TC-UI-002/019/025/026/027/059/060, BUG-049/052).
- **/instructor-choice (4.1)**: фильтры/каталог/сортировка/заявка 1:1;
  dataset.id карточек, ratingNode-эквиваленты («☆ Нет отзывов»,
  «★ X.Y», «N отзывов»), sent-состояние кнопки («✓ Заявка отправлена»),
  409-тост, empty-состояние. Якоря: .card[data-id], .apply, #f-*/,
  #reset/#empty-reset, #sort, #found, #uname, header #logout,
  a.snav[href="/cabinet"] (TC-UI-007/019/059, xss-сценарий).
- **/admin-login (2.1)**: форма (login/pass), postJSON → admin_token →
  /admin-dashboard; #err.show. Якоря: #login/#pass/#err (тестов
  test_static-маркер «Админка»; behavioral-сценариев admin-login в e2e
  нет — вход через _seed_session admin_token).
- **/admin-dashboard (2.2)**: гвард admin_token; nav-разделы
  (onclick → @click showSection-эквивалент; тексты «Пользователи»/
  «Заявки инструкторов»/«Автомобили»/«Документы» — has_text-якоря e2e);
  таблица users (#users-table/#rows/#count/#empty + CSV-кнопка
  .btn-export «↓ Выгрузить CSV» → blob download users.csv); заявки
  (#app-rows, модалка #ic-backdrop/#ic-name/#ic-approve/#ic-deny/
  #ic-deny-box/#ic-deny-confirm disabled/#ic-deny-comment, confirm(),
  license-image blob); авто (#ac-filters/#ac-table/#ac-rows/#ac-backdrop/
  #ac-thumbs/#ac-verdict/#ac-approve/#ac-toast); документы
  (#dc-tabs/#dc-filters/#dc-filters-hist/#dc-list/#dc-count/#dc-view/
  #dc-view-full/#dc-deny/#dc-reason/#dc-deny-go disabled). password_hash
  в исходниках НЕТ (test_qa_instructor_flow). BUG-046-фрагменты дословно.
- **/registered (3.1)**: разметка 1:1 включая note-заглушку и кнопку
  «Личный кабинет» (href="landing-students.html" + alert + return false —
  поведение сохраняется как в legacy; см. «Сознательные ограничения»).
- **/policy (3.1)**: оболочка 1:1 (#policy-meta/#policy-text, .back,
  бренд); логика policy.js в App.vue: fetch → split абзацев →
  интерполяция (текстовые узлы), ошибка → p.policy-error с дословным
  сообщением; NFR-25: текста политики в исходниках нет (grep-контроль
  зелен).

## Обработка ошибок — реакции 1:1 legacy (сводно)

| Ответ | cabinet | choice | admin-login/dashboard | policy |
|---|---|---|---|---|
| 200 | данные разделов; тосты действий | каталог + apply-состояния | таблицы/карточки | текст+версия |
| 401/403 | toLogin → «/» | toLogin → «/» | → /admin-login | n/a (гость) |
| 409/422 | «Слот уже занят»; honest-тосты (текст сервера) | «У вас уже есть активная заявка…»; honest-тост | alert-текст сервера (approve), deny-кнопка disabled без причины | n/a |
| network | остаемся без подстановки / honest-тост | honest-тост списка | err.show / alert «Ошибка» | .policy-error честное сообщение |
| закрытие модалки | data-close-book (фон НЕ закрывает — как legacy) | — | ic-close/ac-close/dc-view-close — как legacy | — |

## Решения по НФТ

- **NFR-26:** npm run check:budgets — 14 page-чанков: каждый vendor-чанк
  ≤150 КБ gzip; JS первого захода КАЖДОЙ страницы ≤200 КБ gzip; в
  замыкании нет чужих page-чанков. Крупнейший перенос — cabinet (~34 КБ
  html + 26 КБ cabinet.js): стили — в styles.css-чанк (вне JS-бюджета),
  wiring — плоский JS без библиотек; запас бюджета сохраняется (vue-чанк
  ~20 КБ gzip + shared ~5 КБ). admin-dashboard: blob/objectURL-логика
  без новых зависимостей. Замеры — в отчете 6.1; при превышении —
  сокращение зависимостей, не ослабление проверки.
- **NFR-27:** полный набор e2e зелен без правок СЦЕНАРИЕВ (допустимый
  дифф — 4 переноса design-guard, см. «Границы правок тестов»);
  маршруты, редиректы, гварды, /api/* — без ломающих изменений.
- Наследуются без изменений: ADR-001 (статика тем же сервисом), FR-57
  (bare-metal npm ci && npm run build), ADR-006 (multi-stage, pinned),
  ADR-009 (ПД: согласия не затрагиваются), NFR-25 (policy), NFR-2/NFR-3
  (параметризация/секреты — backend не трогается).

## Сознательные ограничения (задокументированы)

- **registered — заглушка С0 сохраняется как есть**: alert «Заглушка:
  личный кабинет появится в следующем спринте» и
  href="landing-students.html" (файла нет; onclick+return false —
  переход не выполняется никогда). Перенос 1:1; замена на живой
  редирект в /cabinet — функциональное изменение ВНЕ объема партии
  (правка бы потребовала и мокапа, и сценариев). Легаси-поведение
  воспроизведено честно.
- **NFR-25 grep-контроль не расширяется на .vue**: тест сканирует
  *.html/*.js (входы + main.js); .vue-носители не сканируются (состояние
  с С9). Текст политики в App.vue policy отсутствует по построению
  (оболочка рендерит из API); расширение контроля — будущая партия,
  не правка этой (расширение = правка сценария).
- **frontend_source (tests/conftest.py) не удаляется**: инфра-хелпер
  останется без прямых легаси-потребителей (чистка инфраструктуры —
  вне объема; прецедент: консьерж-функции не переносятся без
  потребностей).
- **el()/initials из js/shared/utils.js не переносятся**: DOM-хелпер на
  Vue не нужен (интерполяция/реактивные списки); choice считает
  инициалы инлайн (перенос инлайна 1:1).
- **Админка остается одной страницей** (4 раздела) — разнос на
  /admin/cars, /admin/documents не выполняется (маршруты не существовали;
  BUG-047; e2e-якоря без правок).
- **Заглушки сохраняются**: чат-бар/quick/плитки «СКОРО», разделы
  «Платежи»/«Настройки» админки (soon() alert), demo-блоки — как в
  legacy.
- **Дубли разметки шапок легаси×Vue исчезают** — финальная партия
  закрывает временное состояние ADR-008 (копий модалки m-login вне
  каркаса нет с С14; легаси-монолитов нет после 5.1).
- dist и node_modules — не в git; входы и компоненты — в git.
- Пилотный хендлер /instructors/pending остается вне карты —
  унификация не делается (наследование С11/С12/С14).
- Контроль бюджетов — приемочный ручной шаг (не CI-гейт) — наследование
  пилота. Сборка dist перед pytest — обязательна (уже так с С12).
- sdd.md в пакетах миграции не ведется; исторические носители
  (sdd.md, code-reviews, test-model, design/mocks) не правятся.
- Порядок задач (утвержден СА): входы-каркас → admin → мелкие → choice →
  cabinet → финальная чистка (/js, _PAGE_ROUTES, носители тестов) →
  бюджеты → полный e2e. Cabinet — последний из переносов: крупнейший,
  интегрируется на готовом shared (fioOf/fmtDate от choice/admin).
- Коммит+пуш после КАЖДОЙ задачи (правило партии С15 — директива СА;
  отменяет наследуемое «коммиты решает ПМ» из С12/С14).

## Соответствие ADR-001/006/008/009

Отступлений нет: multi-entry MPA (страница = точка входа, SPA/
vue-router/pinia запрещены — ОВ-3); замена монолита целиком с удалением
легаси (ADR-008 п.4) — ФИНАЛ: в frontend/ не остается легаси-HTML;
vendor-сплит и бюджеты NFR-26 — правила пилота, свод С11/С12/С14 (теперь
14 входов); статика тем же сервисом (ADR-001) через существующие
/vue/assets + удаление мертвого /js-хендлера; контур доставки без
изменений (ADR-006); критерий приема — зеленый полный e2e (ADR-008 п.6,
FR-85/NFR-27); ПД — согласия/политика-артефакт не затрагиваются
(ADR-009; /policy — тот же контракт, тот же рендер текстовыми узлами).
