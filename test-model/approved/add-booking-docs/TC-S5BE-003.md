# TC-S5BE-003 — Создание авто: СТС обязателен (multipart), photo_sts сохранен

- Автотест: `tests/test_s5_backend.py::test_s5_car_creation_requires_sts`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Обязательное фото СТС при создании автомобиля (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Создание с СТС — автомобиль создан, СТС в «Моих документах» (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Создание без СТС блокировано (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN одобренный инструктор с сессией
- WHEN POST /api/instructor/cars multipart с sts_photo и без него
- THEN с файлом — 200, photo_sts в data/uploads/car_sts/, has_sts/sts_url в списке; без файла — 422 «СТС», авто не создан (FR-44)

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
