# Impact-анализ — change add-vue-s14-instructor-loop (Спринт 14)

- Роль: qa_impact_analyst (H5); составлено ПМ по фактическим дельтам
- Дата: 2026-11-12
- Вход: дельты `openspec/changes/add-vue-s14-instructor-loop/specs/`
  (instructor-auth — MODIFIED, Frontend — ADDED, student-instructor-choice —
  ADDED по факту диффа; instructor-cabinet-stub — REMOVED страницы);
  тестовый набор `tests/`; трассировка TC-S14-001…007.

## 1. MODIFIED / REMOVED дельты

### MODIFIED `instructor-auth` — маршрут входа инструктора и судьба stub

- База: мастер-спека Спринтов 2–2.2 (модалка входа инструктора,
  route/reason, stub-кабинет как отдельная страница).
- Семантика С14: лендинг /instructors и модалка входа — Vue (variant
  'instructors', wiring консолидирован в shared/loginWiring.js);
  route/reason §15.5 и sessionStorage instructor_rejected_reason —
  ДО редиректа, дословно; pending/rejected — существующие Vue-страницы
  (С9/С11), связка без дублирования; stub-страница удалена (REMOVED,
  недостижима с 2.2), дельта instructor-auth REMOVED-сценарий stub
  снят, MODIFIED-заголовки сценариев сохранены дословно (инвариант
  openspec).
- Воздействие на эндпоинты: НЕТ (POST /api/auth/login,
  /api/instructors/apply, /api/instructor/me-гвард → фактический
  /api/auth/me + 401/403 инструкторских, /api/instructor/documents —
  контракты 1:1).
- Регресс-зона: test_instructor_pages (перенос источника чтения —
  вход vue/instructors.html + App.vue + styles.css),
  test_instructor_dashboard (12 тестов — вход + App.vue),
  test_auth_route (−stub, +documents), test_ui_playwright (ровно 2
  design-guard правки: tag-balance +3 vue-входа, BUG-047 чтение dash),
  test_login_modal (+shared/loginWiring.js), test_s3_backend (needles
  дословно, конкатенация — MIN-2 С11). Полный e2e: 69 passed.

## 2. REMOVED страницы

- instructor-cabinet-stub.html + js + маршрут — недостижима с 2.2
  (grep переходов пуст); тесты §4.4 удалены вместе со страницей
  (прецедент arch-review-002 MAJ-1).
- instructors.html, instructor-dashboard.html, documents.html, js —
  легаси удалены ЦЕЛИКОМ (замена монолита, ADR-008); единственный
  легаси-дубль модалки входа умер — вход инструктора теперь только
  Vue (shared/LoginModal variant 'instructors').

## 3. Итог

- Полный e2e ветки: 69 passed, 0 failed (сценарии не переписывались —
  ровно 2 design-guard правки); наборы носителей/гвардов: 152 passed.
- regress-final change: PASS (failed_tests: []).
- Ломающих изменений контрактов нет (все API 1:1); admin-контур и
  календарь instructor-bookings — вне объема (следующие партии).
