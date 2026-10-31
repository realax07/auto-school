# TC-S7BE-015 — Удаленный авто брони (car_id NULL) → «—», не ошибка (наследование MIN-3)

- Автотест: `tests/test_s7_backend.py::test_s7_booking_deleted_car_empty_state`
- Приоритет: Should
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Подтвержденная бронь в календарях обоих (openspec/changes/add-car-validation-booking/specs/booking/spec.md)
  - Scenario: Автомобиль пары удален — пустое состояние без ошибки (openspec/changes/add-car-validation-booking/specs/booking/spec.md)

## GIVEN / WHEN / THEN
- GIVEN пара с бронью, авто удален (car_id NULL)
- WHEN GET брони/календаря ученика и инструктора
- THEN car = null («—»), не ошибка, в обоих календарях

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
