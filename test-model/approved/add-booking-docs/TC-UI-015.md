# TC-UI-015 — «Мои автомобили» на живом бэкенде: CRUD + обязательный СТС (BUG-047)

- Автотест: `tests/test_ui_playwright.py::test_s4_my_cars_add_edit_delete_car`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Обязательное фото СТС при создании автомобиля (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Создание без СТС блокировано (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Создание с СТС — автомобиль создан, СТС в «Моих документах» (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Отсутствие фото — плейсхолдер (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md) — 5 пустых слотов-плейсхолдеров новой карточки

## GIVEN / WHEN / THEN
- GIVEN живой сервер + одобренный инструктор (сессия)
- WHEN раздел «Мои автомобили» внутри дашборда; модалка создания без/с СТС; PATCH-правка; удаление с отменой и подтверждением
- THEN сайдбар/активный таб/заголовок на месте (BUG-047); без СТС кнопка заблокирована; с СТС карточка с 5 пустыми слотами + «Не хватает: …»; правка отражается; после подтверждения авто нет в UI и API

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
