# TC-S5BE-009 — Админская комплектность: GET /api/admin/cars/completeness

- Автотест: `tests/test_s5_backend.py::test_s5_admin_cars_completeness`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Комплектность фото автомобиля проверяет администратор (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Админ видит комплектность каждого автомобиля (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN инструктор с полным (2 ракурса+СТС) и пустым авто
- WHEN GET /api/admin/cars/completeness без токена / с неверным токеном / с админ-токеном
- THEN 401/401/200; по каждому авто владелец, флаги 5 ракурсов + СТС + blocked, отражают фактические наборы (ОВ-1)

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
