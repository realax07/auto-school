# TC-S5BE-008 — Баг 5.2: фото переживает перезагрузку и повторный вход

- Автотест: `tests/test_s5_backend.py::test_s5_bug_5_2_photo_survives_relogin`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Фото автомобиля доступно владельцу (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Фото владельца отображается после перезагрузки и повторного входа (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN инструктор, авто с загруженным ракурсом front
- WHEN повторный запрос списка и повторный вход (новый токен), чтение фото по URL из плитки
- THEN photos.front — URL авторизованного эндпоинта (не data/uploads), фото отдается после перезахода без повторной загрузки (NFR-1)

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
