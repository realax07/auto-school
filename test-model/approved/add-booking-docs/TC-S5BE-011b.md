# TC-S5BE-011b — «Мои документы»: анкета без ВУ — пустое состояние с подсказкой

- Автотест: `tests/test_s5_backend.py::test_s5_documents_empty_license_state`
- Приоритет: Should
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Раздел «Мои документы» инструктора (openspec/changes/add-booking-docs/specs/instructor-documents/spec.md)
  - Scenario: Анкета без ВУ — корректное пустое состояние (openspec/changes/add-booking-docs/specs/instructor-documents/spec.md)

## GIVEN / WHEN / THEN
- GIVEN инструктор без ВУ, авто со СТС
- WHEN GET /api/instructor/documents
- THEN 200; license = null, license_hint упоминает ВУ, СТС-запись на месте (досыл вне объема)

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
