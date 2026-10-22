# TC-S5BE-018 — Confirm: confirmed + decided_at, виден в обоих календарях

- Автотест: `tests/test_s5_backend.py::test_s5_confirm_flow`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Решение инструктора по запросу брони (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Подтверждение без комментария (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Чужую бронь решить нельзя (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Requirement: Подтвержденная бронь в календарях обоих (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Календарь инструктора показывает ученика и автомобиль (openspec/changes/add-booking-docs/specs/booking/spec.md)

## GIVEN / WHEN / THEN
- GIVEN пара с бронью 'new'; чужой инструктор
- WHEN confirm чужим; confirm своим; повторный confirm; чтение обоих календарей
- THEN чужой 404; свой 200 → status='confirmed', decided_at; повтор 409; в календарях статус/авто/ФИО инструктора

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
