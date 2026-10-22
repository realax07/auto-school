# TC-S5BE-014 — Состояния слотов: free → pending/busy → free после отказа (ОВ-5)

- Автотест: `tests/test_s5_backend.py::test_s5_slots_states`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Занятый слот недоступен другим ученикам (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Занятость видна без раскрытия, кем занято (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Requirement: Запрос брони на слот (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Повторный запрос после отклонения допустим (openspec/changes/add-booking-docs/specs/booking/spec.md)

## GIVEN / WHEN / THEN
- GIVEN пара + второй принятый ученик того же инструктора
- WHEN бронь слота первым учеником; чтение слотов вторым; reject брони; чтение слотов
- THEN свой запрос → pending; другому ученику — busy без деталей; после отклонения слот снова free

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
