# TC-S5BE-011 — «Мои документы»: ВУ + СТС двух авто = 3 записи (FR-45)

- Автотест: `tests/test_s5_backend.py::test_s5_documents_list_with_license_and_two_cars`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Раздел «Мои документы» инструктора (openspec/changes/add-booking-docs/specs/instructor-documents/spec.md)
  - Scenario: Список включает ВУ и СТС всех автомобилей (openspec/changes/add-booking-docs/specs/instructor-documents/spec.md)

## GIVEN / WHEN / THEN
- GIVEN инструктор с ВУ в анкете и двумя авто со СТС
- WHEN GET /api/instructor/documents
- THEN 200; 3 записи: license + 2 car_sts, тип/привязка (марка/модель/госномер)/дата загрузки; license_hint пуст

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
