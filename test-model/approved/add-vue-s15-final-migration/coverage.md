# Покрытие: add-vue-s15-final-migration — TC-S15-001…006

Дельта: `openspec/changes/add-vue-s15-final-migration/specs/` —
Frontend: 7 ADDED-требований — «Кабинет ученика на Vue (/cabinet)» (4
сценария), «Выбор инструктора на Vue (/instructor-choice)» (2), «Вход
администратора на Vue (/admin-login)» (1), «Админ-панель на Vue
(/admin-dashboard)» (3), «Страница „Регистрация завершена" на Vue
(/registered)» (1), «Политика на Vue (/policy)» (1), «Финал миграции —
frontend/ без легаси-HTML» (2); MODIFIED «Постраничная миграция —
страница заменяет HTML-монолит целиком» (2 сценария). Всего 16 сценариев
дельты. Покрытие полное: 16/16 (кейс либо группа кейсов на каждый
сценарий; сценарии, уже автоматизированные дословно, — через
существующие e2e/API без дублирования, NFR-27).

Обозначения: Cab = «Кабинет ученика на Vue (/cabinet)»; Cho = «Выбор
инструктора на Vue (/instructor-choice)»; AL = «Вход администратора на
Vue (/admin-login)»; AD = «Админ-панель на Vue (/admin-dashboard)»; Reg
= «Страница „Регистрация завершена" на Vue (/registered)»; Pol =
«Политика на Vue (/policy)»; Fin = «Финал миграции — frontend/ без
легаси-HTML»; Mig = «Постраничная миграция — страница заменяет
HTML-монолит целиком» (MODIFIED) (все — specs/Frontend/spec.md).

| Кейс | Сценарий спеки | Автоматизация |
|---|---|---|
| TC-S15-001 | AL: «Вход админа — контракт не меняется» (частично) + AD: «Панель обслуживается каркасом Vue» (частично) | `tests/web/test_static.py` (GET /admin-login → «Админка», /admin-dashboard → «Пользователи» — входы каркаса, без правок); `tests/web/test_ui_playwright.py::test_s4_pages_tag_balance` (входы admin-login/admin-dashboard — design-guard −2/+6), `::test_back_links_lead_to_role_home` (BUG-047: no /admin/cars, /admin/documents); отдача входом /vue/, контракт входа POST→admin_token→/admin-dashboard + #err «Неверный логин или пароль», гвард-редирект — ручные шаги (behavioral e2e admin-login нет — вход через _seed_session) |
| TC-S15-002 | AD: «Пользователи и CSV — контракт не меняется» + AD: «Заявки, авто, документы — якоря и семантика сохранены» | `test_admin_moderation_approve_reflects_status` (confirm() + page.on("dialog") без правок, #ic-*), `test_admin_row_click_opens_card_and_loads_license_image` + `test_bug048_admin_card_license_photo_real_backend` (ВУ с X-Admin-Token), `test_admin_deny_modal_locked_until_comment_and_waiting_badge_yellow` (deny disabled + wait-бейдж), `test_admin_dashboard_bug046_mock_sync_fragments` (носитель → вход+App.vue, MOCKUP без правок), `test_s7_admin_cars_filter_and_incomplete_approve_locked` (#ac-*), `test_s8_admin_documents_verify_reject_preview_history` (#dc-*); API `test_admin_users.py` TC-ADM-005/008…012 (CSV BOM/«;»/санитизация), `test_admin.py` (401 export.csv), `test_qa_instructor_flow.py` TC-MOD-002 (password_hash — носитель вход+App.vue); blob-download users.csv в браузере — ручной шаг (e2e download-сценария нет) |
| TC-S15-003 | Cab: все 4 сценария («Кабинет обслуживается каркасом Vue», «Гвард, ФИО и выход», «Разделы и календарь С10 на месте», «Дословность FR-9 — против существующего мокапа») | `tests/web/test_cabinet_page.py` (7 тестов — носители → вход+App.vue+styles.css, фрагменты/CSS мокапа cabinet-student дословно, MOCKUP без правок); `test_integration_sprint1.py::test_cabinet_page_served` (wiring-маркеры /api/auth/me, X-Session-Token, /api/auth/logout) + `::test_cabinet_page_is_cabinet_html_file` (адаптация: 200 + «/vue/assets/»); `test_s3_backend.py::test_s4_pages_wired_to_real_api_shapes` (needles дословно); e2e без правок: TC-UI-002 (вход → кабинет), TC-UI-018 (заявки: бейджи/фильтры/#noreq/retry/review-link/.uname), BUG-047 (`test_bug047_myrequests_route_redirects_into_cabinet`), TC-UI-019 (носитель cab), С10-кластер (`test_s5_booking_flow…409`, `test_bug052_calendar…`, `test_bug049_*`), TC-UI-059/060 (логотип/крошки/тег, header .logout); «Выйти» клик-сценарий, визуальная эквивалентность, /vue/-вход, 404 без dist — ручные шаги |
| TC-S15-004 | Cho: «Каталог обслуживается каркасом Vue» + «Фильтры и заявка — контракт не меняется» | `test_student_choice_filters_narrow_and_apply_request` (TC-UI-007 — fulfill снят, ЖИВОЙ маршрут из dist; query-фильтры/reset/POST {instructor_id}/sent «✓ Заявка отправлена»/.uname), TC-UI-019 (носитель choice — href="/cabinet"), `test_student_choice_xss_instructor_name_not_executed` (текстовые узлы), tag-balance (вход choice); API `test_s3_backend.py` TC-S3BE-019…022 (каталог/гвард 401·403/фильтры/пустой 200 []/рейтинг FR-35/409 FR-36); 409-тост без кэширования (review-001 #14), empty-состояние UI, logout → «/», сортировка #sort — ручные шаги (e2e-носителей нет, контракты на API) |
| TC-S15-005 | Reg: «Заглушка обслуживается каркасом Vue» + Pol: «Оболочка и рендер из API — контракт не меняется» | `test_static.py` («Регистрация завершена», маркер во входе) + `test_tc_reg_016_health_and_registered_page_available` (TC-REG-016); `tests/api/test_policy.py::test_s9_policy_api_and_page_guest` (id-якоря + перенос носителя одной строки '/js/policy.js' → '/vue/assets/'), `::test_s9_policy_text_absent_from_frontend_sources` (NFR-25 grep); e2e TC-UI-044 `test_policy_page_guest_render_from_api_and_honest_error` (#policy-meta «Версия:», текстовые узлы, .policy-error дословно); tag-balance (входы registered/policy); alert-кнопка «Личный кабинет» (href="landing-students.html" + return false — перехода нет никогда), 404 без dist — ручные шаги (TC-REG-018 браузерная часть вне TestClient) |
| TC-S15-006 | Fin: «Легаси-носители удалены целиком» + Fin: «Карта маршрутов — все значения vue:» + Mig (MODIFIED): «Мигрированная страница не оставляет legacy-версии» + «ADR фиксирует план и правила миграции» | tag-balance 12 vue-входов (e2e design-guard −2/+6) + `scripts/check_tag_balance.py` DEFAULT (−3/+6); `test_back_links_lead_to_role_home` + `test_bug047_mycars…`/`test_bug047_myrequests…` (негативный список + _PAGE_REDIRECTS без правок); `test_s9_policy_text_absent_from_frontend_sources` (grep источников после чистки); `test_integration_sprint1.py` (признак входа); NFR-27: git diff test_ui_playwright = ровно 4 точки (проверено код-ревью d502f98); прогоны: полный e2e 73 passed (61 + 12 параметризация), не-браузерный регресс 387 passed, NFR-инспекции; матрица /js-смерти (git grep /js/ — пусто вне исторических), ls frontend/ → только vue/, все 13 значений карты «vue:», хендлер /js удален, дубли разметки отсутствуют, ADR-008 строка 21 финал, check:budgets 14 page-чанков (макс 50.7 КБ gzip) — ручные шаги |

Свод по автоматизации партии: behavioral-якоря e2e TC-UI-002/006/007/
011/013/014/018/019/025/026/027/044/052/059/060, BUG-046/047/048/049/
052, admin/С7/С8-кластеры (dialog/CSV-API/комплектность/документы),
хеши #/my-requests#/my-bookings, С10-календарь, policy/registered —
прогон БЕЗ ПРАВОК СЦЕНАРИЕВ (NFR-27). Допустимый дифф
test_ui_playwright.py — РОВНО четыре точки design-guard (BUG-046-носитель;
TC-UI-007 снятие route.fulfill → живой маршрут; TC-UI-019 носители
cab/choice; список параметризации tag-balance −2/+6) + комментарий-шапка
раздела — контроль git diff выполнен код-ревью (d502f98). Носители
легаси-тестов перенесены (право правки — прецедент 2.3 пилота/3.1 С11/
4.1 С12/С14): test_cabinet_page.py (7 тестов → вход+App.vue+styles.css,
MOCKUP без правок), test_integration_sprint1.py (byte-equality → признак
входа «/vue/assets/»), test_policy.py (одна строка носителя),
test_qa_instructor_flow.py (password_hash-носитель), test_s3_backend.py
(checks["vue/cabinet.html"], needles дословно), scripts/check_tag_balance.py
(DEFAULT −3/+6). REMOVED-инварианты (6 легаси html, каталог js/ с 7
модулями, хендлер GET /js/{path}) — инспекция grep'ом/чтением дерева
(матрица /js-смерти: git grep "frontend/js\|/js/" — пусто вне
исторических test-model/sdd/code-reviews). Новых автотестов партия не
добавляет — ручные шаги кейсов выполняются на приемке (гейт 7.1) и
регрессе. Прогоны партии: полный e2e 73 passed (61 сценарий + 12
параметризация tag-balance, на собранном dist), не-браузерный регресс
387 passed, NFR-26 check:budgets 14 page-чанков green (макс 50.7 КБ
gzip). Ручные остатки (свод): клик-контракт admin-login (вход/ошибка),
гвард-редиректы admin, blob-download users.csv в браузере, «Выйти» из
кабинета (wiring-маркер автоматизирован), 409-тост/empty/logout
instructor-choice, alert-кнопка /registered, поблочные визуальные
сверки с легаси-видом, /vue/-входы и 404 без dist, grep-инспекции финала
миграции и ADR-008.
