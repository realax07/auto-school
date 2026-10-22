# TC-UI-025 — Интеграция «бронирование»: слоты → запрос → confirm, 409 (FR-46…FR-50)

- Автотест: `tests/test_ui_playwright.py::test_s5_booking_flow_slots_request_confirm_and_409`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Запрос брони на слот (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Запрос создается со статусом «новая» и виден инструктору (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Requirement: Решение инструктора по запросу брони (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Подтверждение без комментария (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Занятый слот не бронируется повторно (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Requirement: Подтвержденная бронь в календарях обоих (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Календарь ученика показывает занятие (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Календарь инструктора показывает ученика и автомобиль (openspec/changes/add-booking-docs/specs/booking/spec.md)

## GIVEN / WHEN / THEN
- GIVEN живой сервер: инструктор с авто и графиком, принятый ученик
- WHEN ученик: «Мои брони» → слоты → запрос; инструктор: «Бронирования» → confirm; повторная бронь занятого слота
- THEN слот «запрос отправлен»/желтый статус; confirm → «Подтверждена» в календарях ОБОИХ, слот помечен учеником; повтор → 409 без записи (NFR-8)

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
