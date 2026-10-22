# TC-S5BE-012 — Файл документа только владельцу (NFR-7)

- Автотест: `tests/test_s5_backend.py::test_s5_documents_file_access`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Раздел «Мои документы» инструктора (openspec/changes/add-booking-docs/specs/instructor-documents/spec.md)
  - Scenario: Документы доступны только владельцу (openspec/changes/add-booking-docs/specs/instructor-documents/spec.md)
  - Scenario: Просмотр и скачивание документа (openspec/changes/add-booking-docs/specs/instructor-documents/spec.md)

## GIVEN / WHEN / THEN
- GIVEN инструктор с ВУ; чужой инструктор, ученик, гость
- WHEN GET /api/instructor/documents/{{doc_id}}/file от всех ролей + несуществующие doc_id
- THEN владелец 200 image/* с исходными байтами; чужой инструктор 404; ученик 403; гость 401; неизвестный doc_id 404

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
