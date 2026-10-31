# TC-S7BE-010 — REMOVED: POST /api/admin/cars/{id}/block отсутствует, blocked не читается

- Автотест: `tests/test_s7_backend.py::test_s7_admin_block_endpoint_removed`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Комплектность фото автомобиля проверяет администратор (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN change с REMOVED-дельтой контура блокировки Спринта 5
- WHEN POST /api/admin/cars/{id}/block; GET /api/admin/cars/completeness
- THEN block-эндпоинт отсутствует (404/405) — замещен статусной моделью; колонка blocked новыми эндпоинтами не читается (в выдаче нет)

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
