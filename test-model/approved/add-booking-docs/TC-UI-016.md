# TC-UI-016 — Слоты ракурсов: клик → файл → превью, пересчет комплектности

- Автотест: `tests/test_ui_playwright.py::test_s4_my_cars_photo_upload_progress_and_preview`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Фото автомобиля доступно владельцу (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Загруженное фото привязано к автомобилю и отображается (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Ракурсы хранятся и заменяются независимо (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN живой сервер + инструктор с авто (пустые слоты)
- WHEN клик по пустому слоту → выбор файла → POST /api/instructor/cars/{{id}}/photo/{{angle}}; замена «спереди»
- THEN миниатюра в слоте (баг 5.2), комплектность пересчитана; на бэке photos.front выдан, остальные ракурсы не тронуты; выдача фото только по сессии (FR-43)

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
