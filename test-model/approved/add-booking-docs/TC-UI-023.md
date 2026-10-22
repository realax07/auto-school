# TC-UI-023 — Миниатюра СТС до отправки + ошибки файла (BUG-048)

- Автотест: `tests/test_ui_playwright.py::test_bug048_mycars_photo_thumbnail_before_send_and_errors`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Обязательное фото СТС при создании автомобиля (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Создание без СТС блокировано (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Недопустимый файл фото отклоняется (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN живой сервер + инструктор; модалка нового авто
- WHEN выбор СТС-файла (миниатюра до отправки); неверный формат; битый .png; валидный PNG
- THEN миниатюра видна до отправки; неверный формат отсечен клиентом (тост, кнопка заблокирована); битый .png → серверная 422, авто НЕ создан; валидный PNG → авто создан с СТС (FR-44, NFR-9)

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
