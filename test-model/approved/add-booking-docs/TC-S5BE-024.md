# TC-S5BE-024 — Легаси-JSON путь create_car: клиентский ввод → 422, не 500 (M-2)

- Автотест: `tests/test_s5_backend.py::test_s5_create_car_json_invalid_body_422_not_500`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Добавление автомобиля инструктором (openspec/specs/instructor-cars/spec.md, мастер — перенесен из архивного пакета) — невалидные данные отклоняются с ошибкой валидации; регресс M-2 review-001

## GIVEN / WHEN / THEN
- GIVEN одобренный инструктор с сессией
- WHEN POST /api/instructor/cars json={{year: "abc"}} и json=[1, 2]
- THEN оба → 422 (метка «Год…»/не-объект), записей в instructor_cars нет — 500 на клиентский ввод недостижим

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
