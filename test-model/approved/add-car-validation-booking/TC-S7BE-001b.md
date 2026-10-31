# TC-S7BE-001b — CHECK-ограничение колонки status: значение вне статусной машины отвергается

- Автотест: `tests/test_s7_backend.py::test_s7_migration_rejects_status_outside_domain`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Статусы валидации автомобиля (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN мигрированная БД с CHECK-доменом status (draft/validating/validated)
- WHEN INSERT строки instructor_cars со статусом вне домена
- THEN IntegrityError на уровне БД — недопустимый статус не сохраняется

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
