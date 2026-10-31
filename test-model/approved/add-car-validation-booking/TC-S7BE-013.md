# TC-S7BE-013 — СТС ученику пары не выдается во ВСЕХ статусах (NFR-7)

- Автотест: `tests/test_s7_backend.py::test_s7_sts_owner_only_in_all_statuses`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Загрузка СТС существующего автомобиля (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: СТС существующего авто не выдается ученику (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN пара с авто, у владельца загружен СТС
- WHEN GET …/photo/sts и GET …/sts учеником пары во всех статусах; владельцем; чужим инструктором; с angle вне списка
- THEN ученику пары → 403 в каждом статусе; владелец → 200; чужой инструктор → 404; angle вне списка → 404

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
