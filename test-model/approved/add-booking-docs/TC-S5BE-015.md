# TC-S5BE-015 — Бронь status='new' + границы lesson_date (MIN-1)

- Автотест: `tests/test_s5_backend.py::test_s5_booking_create_and_lesson_date_boundary`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Запрос брони на слот (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Запрос создается со статусом «новая» и виден инструктору (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Слот бронируется целиком (openspec/changes/add-booking-docs/specs/booking/spec.md) — lesson_date = ближайшая будущая дата weekday по локальной дате сервера

## GIVEN / WHEN / THEN
- GIVEN пара; слоты today-weekday и tomorrow-weekday
- WHEN POST /api/student/bookings по обоим слотам + чужой/несуществующий слот + вызов без пары
- THEN 200 status='new', lesson_date = сегодня/завтра; бронь видна инструктору (ФИО ученика); чужой слот 404, без пары 403 (MIN-1)

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
