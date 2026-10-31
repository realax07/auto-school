# TC-S7BE-008 — POST validate happy path: validating + любые 3 ракурса из 5 И СТС → validated (ОВ-4)

- Автотест: `tests/test_s7_backend.py::test_s7_admin_validate_happy_path`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Подтверждение автомобилей администратором (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Подтверждение при полном пороге переводит авто в validated (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Requirement: Видимость автомобиля ученикам по статусу валидации (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Проверенный автомобиль — бейдж и зеленая галочка (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN авто в validating с любыми 3 ракурсами из 5 и СТС
- WHEN POST /api/admin/cars/{id}/validate
- THEN авто → validated (виден в каталоге, бейдж «Проверено»); эффект отражается в GET /api/admin/cars/completeness

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
