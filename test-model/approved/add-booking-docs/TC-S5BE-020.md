# TC-S5BE-020 — PUT графика при активных бронях → 409 с перечнем (MAJ-1)

- Автотест: `tests/test_s5_backend.py::test_s5_put_availability_blocked_by_active_bookings`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Замена графика при активных бронях отклоняется (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Сохранение графика без слота с активной бронью отклоняется (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: После решения броней график сохраняется (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Слоты с только отклоненными бронями замене не мешают (openspec/changes/add-booking-docs/specs/booking/spec.md)

## GIVEN / WHEN / THEN
- GIVEN пара; на слоте Пн бронь 'new' (затем 'confirmed')
- WHEN PUT графика без Пн до и после решения брони
- THEN 409 с conflicts (weekday, booking_statuses ['new']/['confirmed']) и прежним графиком; после reject/confirm сохранение проходит; только 'rejected' не мешает

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
