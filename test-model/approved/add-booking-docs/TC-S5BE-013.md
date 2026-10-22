# TC-S5BE-013 — Слоты: доступ только принятому ученику (FR-46, NFR-7)

- Автотест: `tests/test_s5_backend.py::test_s5_slots_access_guard`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Расписание инструктора доступно только принятым ученикам (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Не принятому ученику расписание недоступно при прямом вызове API (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Гость и иная роль не получают расписание (openspec/changes/add-booking-docs/specs/booking/spec.md)

## GIVEN / WHEN / THEN
- GIVEN инструктор с графиком; ученик без пары; гость
- WHEN GET /api/student/instructors/{{id}}/slots от ученика без пары / по 999999 / без токена / от инструктора
- THEN 403 / 404 / 401 / 403 — расписание не возвращается

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
