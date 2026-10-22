# TC-S5BE-016 — Занятый слот → 409 без записи; повтор после отклонения (ОВ-5)

- Автотест: `tests/test_s5_backend.py::test_s5_booking_conflict_409_no_record`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Занятый слот недоступен другим ученикам (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Занятый слот не бронируется повторно (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Повторный запрос после отклонения допустим (openspec/changes/add-booking-docs/specs/booking/spec.md)

## GIVEN / WHEN / THEN
- GIVEN пара + второй принятый ученик; слот занят первой бронью
- WHEN повторная бронь чужим учеником и своим; подсчет записей; reject; повторная бронь
- THEN оба повтора 409 («занят»), в БД ровно 1 запись; после reject новая бронь создается

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
