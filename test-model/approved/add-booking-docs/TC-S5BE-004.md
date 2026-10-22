# TC-S5BE-004 — СТС: не JPEG/PNG и >5 МБ → 422, авто не создан

- Автотест: `tests/test_s5_backend.py::test_s5_car_sts_file_validation`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Обязательное фото СТС при создании автомобиля (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Недопустимый файл фото отклоняется (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md) — проверка содержимого/размера распространена на СТС (NFR-9)

## GIVEN / WHEN / THEN
- GIVEN одобренный инструктор с сессией
- WHEN POST /api/instructor/cars multipart c sts_photo = PDF и JPEG >5 МБ
- THEN оба запроса 422 («Файл…»), записей instructor_cars нет (NFR-9)

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
