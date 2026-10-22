# TC-S5BE-005 — 5 ракурсов: загрузка/замена независимы, выдача отдельно

- Автотест: `tests/test_s5_backend.py::test_s5_car_photo_angles_upload_replace`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Фото автомобиля доступно владельцу (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Ракурсы хранятся и заменяются независимо (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Загруженное фото привязано к автомобилю и отображается (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN авто создано (multipart с СТС)
- WHEN загрузка всех 5 ракурсов (JPEG/PNG), затем замена «спереди»
- THEN каждый ракурс выдан отдельно с image/*; замена front не меняет rear (FR-43)

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
