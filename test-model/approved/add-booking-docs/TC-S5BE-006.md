# TC-S5BE-006 — Ошибки ракурсов: вне списка/чужой авто/незагруженный → 404

- Автотест: `tests/test_s5_backend.py::test_s5_car_photo_angle_errors`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Фото автомобиля доступно владельцу (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Фото не выдается другому пользователю (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Отсутствие фото — плейсхолдер (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md) — незагруженный ракурс не возвращает байт, клиент рисует плейсхолдер

## GIVEN / WHEN / THEN
- GIVEN два инструктора; у первого авто с ракурсом front
- WHEN загрузка/чтение ракурса trunk, чужая загрузка front, чтение незагруженного interior
- THEN все три запроса 404, файлы не создаются/не выдаются

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
