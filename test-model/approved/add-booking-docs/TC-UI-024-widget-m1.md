# TC-UI-024-widget-m1 — Виджет «Занятия на сегодня» рендерит реальный шейп (M-1 review-001)

- Автотест: `tests/test_ui_playwright.py::test_instructor_summary_today_lessons_widget_renders_real_shape`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Подтвержденная бронь в календарях обоих (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Виджет «Занятия на сегодня» показывает реальные брони (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Нет броней на сегодня — прежнее пустое состояние (openspec/changes/add-booking-docs/specs/booking/spec.md)

## GIVEN / WHEN / THEN
- GIVEN мок /api/instructor/summary строго по шейпу бэка (student_full_name, start_time/end_time «ЧЧ:ММ:СС»)
- WHEN открыть /instructor/dashboard с непустым today_lessons
- THEN список отрисован, пустое состояние скрыто; строка «Ольга Нечаева» + «10:00–11:30»; на старом коде (l.student/l.time) тест падает — M-1 закрыт

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
