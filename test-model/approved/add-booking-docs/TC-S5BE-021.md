# TC-S5BE-021 — Авто пары удален → календари с car: null (MIN-3)

- Автотест: `tests/test_s5_backend.py::test_s5_calendars_survive_car_deletion`
- Приоритет: Should
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Подтвержденная бронь в календарях обоих (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Календарь ученика показывает занятие (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Календарь инструктора показывает ученика и автомобиль (openspec/changes/add-booking-docs/specs/booking/spec.md) — после удаления авто car = null, не ошибка

## GIVEN / WHEN / THEN
- GIVEN пара с подтвержденной бронью
- WHEN DELETE /api/instructor/cars/{{id}}, затем оба календаря
- THEN 200 у удаления; оба календаря 200 с bookings[0].car = null (MIN-3)

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
