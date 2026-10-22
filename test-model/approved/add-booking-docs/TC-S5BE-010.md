# TC-S5BE-010 — Блокировка авто: идемпотентна, 404, не ретроактивна (MIN-2)

- Автотест: `tests/test_s5_backend.py::test_s5_admin_block_car_min2`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Комплектность фото автомобиля проверяет администратор (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Автомобиль с неполным комплектом блокируется (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Заблокированный автомобиль недоступен ученикам (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md) — скрытие фото; брони решаются по MIN-2 вне спеки блокировки

## GIVEN / WHEN / THEN
- GIVEN пара с авто; админ-токен
- WHEN двойной POST /api/admin/cars/{{id}}/block, block 999999, block без токена; затем новая бронь + confirm
- THEN 200/200/404/401; новая бронь создается и подтверждается (блокировка не ретроактивна, MIN-2), подтвержденная бронь видна ученику с авто

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
