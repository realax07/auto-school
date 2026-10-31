# TC-S7BE-006 — Алиасы маршрутов ТЗ ПМ: send-to-validation / back-to-draft идентичны submit/withdraw

- Автотест: `tests/test_s7_backend.py::test_s7_pm_aliases_send_to_validation_back_to_draft`
- Приоритет: Should
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Статусы валидации автомобиля (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Инструктор отправляет автомобиль на проверку (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Инструктор отзывает автомобиль с проверки (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN авто в draft, затем в validating
- WHEN POST …/{id}/send-to-validation и POST …/{id}/back-to-draft; повтор в неверном статусе
- THEN алиасы ведут себя идентично submit/withdraw (draft→validating, validating→draft); не в том статусе → 409

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
