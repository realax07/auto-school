# TC-S5BE-025 — Гонка PUT availability × создание брони — сироты нет (M-3)

- Автотест: `tests/test_s5_backend.py::test_s5_put_availability_vs_booking_race_no_orphan`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Замена графика при активных бронях отклоняется (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Сохранение графика без слота с активной бронью отклоняется (openspec/changes/add-booking-docs/specs/booking/spec.md) — окно M-3 review-001 закрыто BEGIN IMMEDIATE

## GIVEN / WHEN / THEN
- GIVEN пара; monkeypatch blocking_bookings вставляет бронь отдельным соединением сразу после проверки конфликтов
- WHEN PUT графика без слота Пн в окне гонки
- THEN инвариант: либо 409 + слот жив + бронь жива, либо 200 + записей 0; комбинация «бронь жива + слот удален» невозможна (NFR-8)

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
