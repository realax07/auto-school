# TC-S7BE-016 — СТС существующего авто через angle='sts': загрузка/замена, PDF/6 МБ → 422 (задача 4.1)

- Автотест: `tests/test_s7_backend.py::test_s7_sts_upload_and_replace_via_angle`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Загрузка СТС существующего автомобиля (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: СТС загружается на существующий автомобиль (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Недопустимый файл СТС отклоняется (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Замена СТС не трогает ракурсы (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Requirement: Фото автомобиля доступно владельцу (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Ракурсы хранятся и заменяются независимо (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Недопустимый файл фото отклоняется (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN существующее авто владельца с загруженными ракурсами
- WHEN POST …/photo/sts с JPEG/PNG, затем с PDF и >6 МБ; повторная замена СТС
- THEN JPEG/PNG сохраняются (файл в data/uploads/car_sts/) — корень симптома «kind=car_sts не сохраняется» закрыт; PDF/6 МБ → 422, прежнее СТС не изменено; замена СТС не трогает ракурсы и статус

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
