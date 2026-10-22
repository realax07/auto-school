# TC-UI-024-integration — Интеграция «авто»: полный комплект = комплектность админа; ученик видит авто, СТС — нет

- Автотест: `tests/test_ui_playwright.py::test_s5_car_full_kit_completeness_and_student_sees_car`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Комплектность фото автомобиля проверяет администратор (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Админ видит комплектность каждого автомобиля (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Requirement: Фото автомобиля доступно владельцу (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Фото ракурсов доступно ученику пары (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: СТС не выдается ученику (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN живой сервер: инструктор, авто через UI (СТС обязателен), 5 ракурсов; ученик принятой пары
- WHEN загрузка 5 фото по слотам; сверка с GET /api/admin/cars/completeness; каталог ученика + прямые запросы фото/СТС
- THEN UI «Комплект полный» совпадает с админской комплектностью; ученик видит авто в каталоге, фото ракурсов выдаются, СТС — 403 (FR-42/FR-44)

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
