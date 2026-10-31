# TC-S7BE-009 — Guard комплектности validate: 409 с перечнем, статус не меняется (ОВ-4)

- Автотест: `tests/test_s7_backend.py::test_s7_admin_validate_completeness_guard_409`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Подтверждение автомобилей администратором (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Сервер отклоняет подтверждение без порога (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN авто в validating с неполными наборами (2 ракурса + СТС; 3 ракурса без СТС; 0 ракурсов), авто не в validating, несуществующий id
- WHEN POST validate по каждому случаю, включая запрос без токена
- THEN 2 ракурса + СТС → 409 с перечнем недостающих ракурсов; 3 без СТС → 409 с «СТС»; 0 ракурсов → 409; не в validating → 409; несуществующий → 404; без токена → 401; статус авто при отказах НЕ меняется

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
