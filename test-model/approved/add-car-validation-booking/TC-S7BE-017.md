# TC-S7BE-017 — «Мои документы»: СТС по всем авто во всех статусах + дозагрузка/замена (FR-45)

- Автотест: `tests/test_s7_backend.py::test_s7_documents_sts_all_statuses_and_dosylka`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Раздел «Мои документы» инструктора (openspec/changes/add-car-validation-booking/specs/instructor-documents/spec.md)
  - Scenario: Список включает ВУ и СТС всех автомобилей (openspec/changes/add-car-validation-booking/specs/instructor-documents/spec.md)
  - Scenario: СТС отображается независимо от статуса валидации авто (openspec/changes/add-car-validation-booking/specs/instructor-documents/spec.md)
  - Scenario: Дозагрузка СТС существующему авто обновляет раздел (openspec/changes/add-car-validation-booking/specs/instructor-documents/spec.md)
  - Scenario: Документы доступны только владельцу (openspec/changes/add-car-validation-booking/specs/instructor-documents/spec.md)
  - Requirement: Загрузка СТС существующего автомобиля (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: СТС существующего авто появляется в «Моих документах» (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN инструктор с авто в draft/validating/validated, у части СТС нет
- WHEN GET /api/instructor/documents; дозагрузка СТС (angle='sts'); замена СТС; запрос под чужой ролью
- THEN СТС по ВСЕМ авто владельца независимо от status; после дозагрузки запись появилась; после замены — обновленная привязка на месте; доступ — только владельцу (чужая роль → 403/401)

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
