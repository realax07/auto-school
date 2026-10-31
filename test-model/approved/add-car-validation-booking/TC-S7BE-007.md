# TC-S7BE-007 — GET /api/admin/cars/completeness (+алиас /api/admin/cars): все статусы + counters + фильтр ?status=validating

- Автотест: `tests/test_s7_backend.py::test_s7_admin_cars_list_filter`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Подтверждение автомобилей администратором (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Админ видит комплектность и статус каждого автомобиля (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Фильтр «На валидации» показывает только validating (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN авто во всех трех статусах; админ-токен
- WHEN GET /api/admin/cars/completeness; GET с ?status=validating; ?status=invalid; запрос без/с неверным токеном
- THEN выдача — все авто всех статусов + status + counters; фильтр возвращает только validating («На валидации»); недопустимый фильтр → 422; без/с неверным токеном → 401

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
