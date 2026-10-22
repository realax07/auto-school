# TC-S5BE-022 — «Занятия на сегодня»: confirmed на сегодня (FR-49, ОВ-6)

- Автотест: `tests/test_s5_backend.py::test_s5_summary_today_lessons`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Подтвержденная бронь в календарях обоих (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Виджет «Занятия на сегодня» показывает реальные брони (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Нет броней на сегодня — прежнее пустое состояние (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Перекрепление авто меняет авто в отображении брони (openspec/changes/add-booking-docs/specs/booking/spec.md)

## GIVEN / WHEN / THEN
- GIVEN пара; слоты today/tomorrow weekday
- WHEN GET /api/instructor/summary пустой; две брони + confirm; summary; PATCH перекрепление авто; удаление авто; summary
- THEN [] → ровно бронь на today (lesson_date/start_time/ФИО/авто); перекрепление видно; после удаления авто запись остается с car = null (MIN-3, ОВ-6)

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
