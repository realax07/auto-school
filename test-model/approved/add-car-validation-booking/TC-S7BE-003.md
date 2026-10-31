# TC-S7BE-003 — Новое авто создается в draft (ЯВНО в INSERT); GET /cars выдает status и counters

- Автотест: `tests/test_s7_backend.py::test_s7_new_car_created_in_draft_with_counters`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Статусы валидации автомобиля (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Новый автомобиль создается в черновике (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN авторизованный инструктор
- WHEN создание нового авто (JSON-путь совместимости); GET /api/instructor/cars
- THEN авто в status='draft' (явно в INSERT — DEFAULT не используется, защита от «молчаливого validated»); выдача несет status и counters (ракурсов из 5, СТС да/нет) во всех статусах владельца

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
