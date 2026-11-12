# Покрытие: add-vue-s14-instructor-loop — TC-S14-001…007

Дельта: `openspec/changes/add-vue-s14-instructor-loop/specs/` —
Frontend: 3 ADDED-требования — «Лендинг инструкторов на Vue (/instructors)»
(4 сценария), «Кабинет инструктора на Vue (/instructor/dashboard)» (4),
«Мои документы на Vue (/instructor/documents)» (4); instructor-auth:
MODIFIED «Роутинг после входа по статусу» (4 сценария) + REMOVED
«Заглушка кабинета инструктора». Всего 12 сценариев дельты. Покрытие
полное: 12/12 (кейс либо группа кейсов на каждый сценарий; сценарии, уже
автоматизированные дословно, — через существующие e2e/API без
дублирования, NFR-27) + REMOVED-инвариант и NFR-26 (источник требований).

Обозначения: Lan = Requirement «Лендинг инструкторов на Vue
(/instructors)»; Dash = «Кабинет инструктора на Vue
(/instructor/dashboard)»; Doc = «Мои документы на Vue
(/instructor/documents)» (все — specs/Frontend/spec.md); Route =
«Роутинг после входа по статусу» (specs/instructor-auth/spec.md,
MODIFIED).

| Кейс | Сценарий спеки | Автоматизация |
|---|---|---|
| TC-S14-001 | Lan: «Лендинг обслуживается каркасом Vue» + Lan: «Визуальная эквивалентность и CTA анкеты» | частично: `tests/web/test_instructor_pages.py` §4.1 (4 теста: exists/texts_verbatim/cta_wiring/footer — носитель → vue-вход, задача 4.1); `tests/web/test_ui_playwright.py::test_instructors_landing_brand_and_cta` (TC-UI-003 — без правок); `tests/api/test_auth_route.py::test_new_static_routes_served` (/instructors 200); /vue/-вход, отсутствие легаси-файлов, 404 без dist, поблочное сопоставление — ручные шаги |
| TC-S14-002 | Lan: «Вход — модалка на месте, контракт не меняется» + Route: все 4 сценария (approved/waiting/deny/без пароля) | `tests/web/test_ui_playwright.py::test_bug056_instructor_login_modal_close_semantics` (TC-UI-052), `::test_s9_pilot_rejected_redirects_with_reason` (TC-S9UI-003), `::test_instructor_apply_valid_form_goes_pending` (TC-UI-004), `::test_instructor_login_approved_dashboard_layout` (TC-UI-005); `tests/web/test_login_modal.py` (5 тестов, носитель +shared/loginWiring.js); `tests/api/test_auth_route.py` (5 route-тестов логина); `tests/web/test_instructor_pages.py` §4.3 (pending/rejected); модалка локально без флагов (BUG-055), rejected без входа — ручные шаги |
| TC-S14-003 | Lan: «Последний дубль модалок устранен» + REMOVED «Заглушка кабинета инструктора» + клаузы «legacy MUST быть удалены» (Lan + Dash, монолит целиком) | `tests/web/test_login_modal.py::test_tc_auth_login_wiring_fragments_present`, `::test_login_route_mapping_wiring` (носитель shared/loginWiring.js + LoginModal.vue); `tests/api/test_auth_route.py::test_new_static_routes_served` (реестр 5 маршрутов, cabinet-stub отсутствует); `tests/web/test_ui_playwright.py::test_s4_pages_tag_balance` (design-guard +3 vue-входа), `::test_back_links_lead_to_role_home` (BUG-047-guard), `::test_bug047_mycars_route_redirects_into_dashboard`; grep дерева frontend/, чтение `_PAGE_ROUTES`, контроль диффа тестов — ручные шаги |
| TC-S14-004 | Dash: «Кабинет обслуживается каркасом Vue» + Dash: «Гвард и данные кабинета — контракты не меняются» | частично: `tests/web/test_ui_playwright.py` TC-UI-005 (вход → layout, ФИО), TC-UI-024 (виджет summary), TC-UI-009 (запросы deny/accept); `tests/api/test_instructor_dashboard.py` (гвард 401×4/403, 200+ФИО, demo payload, page_served, mockup_texts_verbatim, nav_sections_fr19, wiring_fr18_fr20_fr22 — носитель → вход + App.vue + shared); `tests/api/test_s3_backend.py::test_summary_widgets`, `::test_instructor_requests_contract_shape`; /vue/-вход, 404 без dist — ручные шаги |
| TC-S14-005 | Dash: «Разделы и выход сохранены» + Dash: «Визуальная эквивалентность кабинету» | `tests/web/test_ui_playwright.py::test_bug051_sidebar_exact_items_students_subtabs_profile_docs` (TC-UI-028 — сайдбар РОВНО перечень), TC-UI-008 (календарь), TC-UI-010 (выход → /instructors), TC-UI-015/016/023 (автомобили #/my-cars), TC-UI-030/033/034/040/042 (раздел документов кабинета), `::test_back_links_lead_to_role_home`; grid 2 колонки — частично в TC-UI-005; поблочное сопоставление макета (topbar/hello/demo-tag/панели) — ручной шаг |
| TC-S14-006 | Doc: «Новая страница обслуживается каркасом Vue» + Doc: «Список и версии — контракт не меняется» + Doc: «Доступ только владельцу» | частично: `tests/api/test_auth_route.py::test_new_static_routes_served` (/instructor/documents 200); `tests/api/test_s8_backend.py` — версии/статусы ОВ-1/ОВ-7, пустой СТС, access_matrix (401/403/чужой 404, file только владельцу); тот же контракт в e2e TC-UI-033/034 (раздел кабинета); html-вход /vue/assets, прямой URL, негативный список BUG-047 (без правок), smoke dist 3.3 (список/просмотр/замена-диалог/гвард/logout) — ручные шаги |
| TC-S14-007 | Doc: «Загрузка и замена — предупреждение и явная кнопка (FR-71)» + источник NFR-26 (бюджеты на артефактах, 8 страниц) | `tests/web/test_ui_playwright.py::test_s8_my_documents_statuses_versions_and_license_replace` (TC-UI-033 — FR-70/71/72, тот же контракт); `tests/api/test_s8_backend.py` (замена СТС/ВУ, дозагрузка СТС, статусы до верификации, 401/403 multipart); предупреждение FR-71/явная кнопка/отмена/клиентская валидация/tосты дословно на новой странице и `npm run check:budgets` (8 страниц, 150/200 КБ gzip) — ручные шаги приемки (гейт 5.1) |

Свод по автоматизации партии: поведенческие якоря TC-UI-003/004/005/008/
009/010/015/016/023/024/028/030/033/034/040/042/052, TC-S9UI-003 и API
test_auth_route.py / test_instructor_dashboard.py / test_s3_backend.py /
test_s8_backend.py / test_instructor_pages.py / test_login_modal.py —
прогон без правок СЦЕНАРИЕВ (NFR-27). Допустимый дифф
test_ui_playwright.py — только два переноса носителя design-guard
(список tag-balance +3 vue-входа, чтение dash в BUG-047-guard; design.md
«Границы правок тестов»). §4.4 test_instructor_pages (2 теста заглушки)
удален вместе со страницей — REMOVED-дельта instructor-auth (прецедент
arch-review-002 MAJ-1). Новых автотестов партия не добавляет — ручные
шаги кейсов выполняются на приемке (гейты 5.1/6.1) и регрессе; полный
e2e 69 passed — прогон 6.1 партии. Специфика НОВОЙ страницы
/instructor/documents: поведенческая автоматизация — контракты API и
e2e раздела кабинета (тот же функционал С8), экран новой страницы —
ручной smoke задачи 3.3.
