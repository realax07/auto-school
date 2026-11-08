# Покрытие: add-vue-s12-landing-apply — TC-S12UI-001…010

Дельта: `openspec/changes/add-vue-s12-landing-apply/specs/` —
Frontend: 2 ADDED-требования, «Лендинг ученика на Vue (/)» — 5 сценариев
(в дельте, включая «Визуальная эквивалентность текущему лендингу»),
«Анкета инструктора на Vue (/instructors/apply)» — 5; student-instructor-choice:
«Шапка „Выбора инструктора“ без плитки-аватара (BUG-062)» — 3. Всего 13
сценариев. Покрытие полное: 13/13 (кейс либо группа кейсов на каждый
сценарий; сценарии, уже автоматизированные дословно, — через существующие
e2e/API без дублирования, NFR-27).

Обозначения: Lan = Requirement «Лендинг ученика на Vue (/)»; App =
Requirement «Анкета инструктора на Vue (/instructors/apply)» (оба —
specs/Frontend/spec.md); Bug62 = Requirement «Шапка „Выбора инструктора“
без плитки-аватара (BUG-062)» (specs/student-instructor-choice/spec.md).

| Кейс | Сценарий спеки | Автоматизация |
|---|---|---|
| TC-S12UI-001 | Lan: «Лендинг обслуживается каркасом Vue» + Lan: «Визуальная эквивалентность текущему лендингу» | частично: `tests/web/test_login_modal.py::test_tc_auth_landing_page_served_with_wiring` (GET /, бренд, wiring — без правок); `tests/web/test_static.py::test_tc_reg_018_static_pages_return_200_with_mock_texts`; `scripts/check_hero_overlap.py` (5 ширин, dist); /vue/-вход, поблочное сопоставление текстов, 404 без dist — ручные шаги |
| TC-S12UI-002 | Lan: «Семантика модалок и заглушки сохранены» | `tests/web/test_ui_playwright.py::test_bug056_landing_login_modal_close_semantics` (TC-UI-053 — дословно); `tests/web/test_login_modal.py::test_tc_auth_login_modal_texts_verbatim`, `::test_tc_auth_login_modal_no_stub_submit`; «Отмена», снятие open_login-флагов (BUG-056), alert-заглушки #ai-open/.quick/#to-teachers — ручные шаги |
| TC-S12UI-003 | Lan: «Вход — route/reason контракт не меняется, включая rejected» | `tests/web/test_ui_playwright.py::test_s9_pilot_rejected_redirects_with_reason` (TC-S9UI-003 — дословно: rejected → sessionStorage «instructor_rejected_reason» ДО редиректа), `::test_instructor_login_approved_dashboard_layout` (TC-UI-005); `tests/web/test_login_modal.py::test_login_route_mapping_wiring`; `tests/api/test_auth_route.py` (4 route-теста логина); ученик → /cabinet — ручной шаг |
| TC-S12UI-004 | Lan: «Регистрация — согласие обязательно (FR-78)» | `tests/web/test_ui_playwright.py::test_student_register_redirects_to_cabinet` (TC-UI-002 — дословно), `::test_register_modal_consent_gates_submit_and_links_policy` (TC-UI-043); `tests/api/test_register.py::test_s9_register_consent_missing_or_false_422_in_regression`, `::test_tc_reg_008_no_record_created_on_any_rejection`; `tests/api/test_policy.py::test_s9_policy_link_visible_in_both_consent_blocks` (TC-PD-005) |
| TC-S12UI-005 | App: «Анкета обслуживается каркасом Vue» + App: «Валидная анкета — экран ожидания, контракт не меняется» | частично: `tests/api/test_auth_route.py::test_new_static_routes_served` (/instructors/apply 200 text/html — без правок); `tests/web/test_ui_playwright.py::test_instructor_apply_valid_form_goes_pending` (TC-UI-004 — дословно); `tests/api/test_instructors_apply.py::test_apply_success_creates_waiting_application_with_hash`; `tests/web/test_instructor_pages.py::test_apply_submit_wiring` (носитель); /vue/-вход, localStorage-токены до редиректа, 404 без dist — ручные шаги |
| TC-S12UI-006 | App: «Согласие обязательно — 422 позиция 1a (FR-77)» + App: «Ошибки файла ВУ — видимое сообщение у поля загрузки» | `tests/web/test_ui_playwright.py::test_instructor_apply_consent_gates_submit_and_links_policy` (TC-UI-045 — дословно); `tests/api/test_instructors_apply.py::test_apply_order_consent_checked_before_email_format` (1a), `::test_apply_validation_contract_422` (контрактные 422-тексты полей), `::test_apply_fio_three_required_fields`; клиентская валидация ВУ (≤5 МБ, JPEG/PNG, #license-error, 413/415 → notice), BUG-048 миниатюра — ручные шаги |
| TC-S12UI-007 | App: «Визуальная эквивалентность текущей анкете» | `tests/web/test_instructor_pages.py` §4.2: test_apply_page_texts_verbatim, test_apply_password_fields_added, test_apply_links_to_landing, test_apply_work_format_toggles_plate, test_apply_submit_wiring (носители: вход vue/instructor-apply.html + styles.css); `tests/web/test_ui_playwright.py::test_instructor_apply_upload_icon_centered` (6px); поблочное сопоставление с мокапом registration-instructor — ручной шаг |
| TC-S12UI-008 | Bug62: «В шапке нет плитки-аватара» + Bug62: «ФИО и „Выйти“ не пострадали» + Bug62: «Мокапы синхронизированы» | `tests/web/test_ui_playwright.py::test_tc_ui_059_student_cabinet_single_logo_no_crumbs` (TC-UI-059 — негативный инвариант «header .avatar count==0», дополнение предписано планом BUG-062; «Выйти»/BUG-059/060/061 — без ослабления, ФИО в #uname — ручной шаг), `::test_tc_ui_060_cabinet_tiles_no_v_kabinete_tag` (TC-UI-060); grep носителей (instructor-choice.html/.js) и мокапов choice-a/b — ручные шаги |
| TC-S12UI-009 | Lan + App: источник NFR-26 (бюджеты на артефактах сборки; 5 page-чанков) | `npm run check:budgets` (frontend/vue, scripts/check-budgets.mjs — PAGES: instructors-pending, instructors-rejected, review-form, index, instructor-apply — приемочный ручной шаг, отчет 5.1); контрольный gzip-замер и замыкание первого захода по каждой странице — ручные шаги |
| TC-S12UI-010 | Lan: клауза «legacy index.html и js/landing.js MUST быть удалены» + App: клауза «legacy instructor-apply.html и js/apply.js MUST быть удалены» (монолит целиком) | `tests/web/test_ui_playwright.py::test_s4_pages_tag_balance` (NIT-4 design-guard: +vue/index.html, +vue/instructor-apply.html); `tests/web/test_login_modal.py::test_tc_auth_landing_page_served_with_wiring` (носитель /js/landing.js); `tests/web/test_bug001.py::test_tc_auth_019_register_wiring_fragments`; `tests/api/test_policy.py::test_s9_policy_link_visible_in_both_consent_blocks`; `tests/web/test_ui_playwright.py::test_bug056_instructor_login_modal_close_semantics` (легаси-дубль /instructors жив); git/grep дерева, чтение `_PAGE_ROUTES` — ручные шаги |

Свод по автоматизации партии: поведенческие якоря TC-UI-001/002/004/043…045/053,
TC-UI-059/060, TC-S9UI-003 и API test_register.py / test_instructors_apply.py /
test_auth_route.py — прогон без правок СЦЕНАРИЕВ (NFR-27). Допустимый дифф
test_ui_playwright.py — только два переноса носителя design-guard (NIT-4) и
негативный инвариант BUG-062 в TC-UI-059 (design.md «Границы правок тестов»).
Новых автотестов партия не добавляет — ручные шаги кейсов выполняются на
приемке (гейт 5.1/6.1) и регрессе; полный e2e 67 passed — прогон 6.1 партии.
