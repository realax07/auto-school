# TC-S5BE-017 — Гонка: два параллельных POST на слот — [200, 409] (NFR-8)

- Автотест: `tests/test_s5_backend.py::test_s5_booking_race_two_students_one_409`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Занятый слот недоступен другим ученикам (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Параллельные запросы на один слот — максимум одна бронь (openspec/changes/add-booking-docs/specs/booking/spec.md)

## GIVEN / WHEN / THEN
- GIVEN пара + второй принятый ученик, общий слот
- WHEN два потока через threading.Barrier одновременно POST /api/student/bookings
- THEN ровно [200, 409]; в БД максимум одна активная бронь (BEGIN IMMEDIATE + частичный UNIQUE)

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
