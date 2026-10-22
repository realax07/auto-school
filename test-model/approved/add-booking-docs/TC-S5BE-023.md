# TC-S5BE-023 — NFR-10: в новых модулях нет SQL-конкатенаций

- Автотест: `tests/test_s5_backend.py::test_s5_new_modules_no_sql_concatenation`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Занятый слот недоступен другим ученикам (openspec/changes/add-booking-docs/specs/booking/spec.md) — сквозной NFR-10←NFR-3 по всем модулям дельты (booking, instructor_documents, instructor_cars, instructor_availability, instructor_summary): параметризованный SQL без f-строк/конкатенаций/format()

## GIVEN / WHEN / THEN
- GIVEN исходники backend/ (статический контроль)
- WHEN grep-контроль пяти модулей на f"SELECT/INSERT/UPDATE/DELETE, конкатенации и format(
- THEN ни одного совпадения — все запросы параметризованы

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
