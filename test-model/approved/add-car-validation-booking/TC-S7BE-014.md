# TC-S7BE-014 — Брони: car_status-бейдж + photo_url (приоритет front) по статусам и viewer (ОВ-2)

- Автотест: `tests/test_s7_backend.py::test_s7_booking_car_photo_and_badge_by_status`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Подтвержденная бронь в календарях обоих (openspec/changes/add-car-validation-booking/specs/booking/spec.md)
  - Scenario: Календарь ученика показывает фото прикрепленного авто (openspec/changes/add-car-validation-booking/specs/booking/spec.md)
  - Scenario: Draft-автомобиль в брони — без фото (openspec/changes/add-car-validation-booking/specs/booking/spec.md)
  - Scenario: Перекрепление авто меняет авто в отображении брони (openspec/changes/add-car-validation-booking/specs/booking/spec.md)
  - Requirement: Видимость автомобиля ученикам по статусу валидации (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Автомобиль на проверке виден паре с желтым бейджем (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Проверенный автомобиль — бейдж и зеленая галочка (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN пара с подтвержденной бронью; авто поочередно в validated/validating/draft
- WHEN GET броней учеником и инструктором; перекрепление авто
- THEN validated — с фото у ученика и инструктора; validating — с фото и бейджем «Не проверено» (car_status='validating'); draft — у ученика БЕЗ photo_url (плейсхолдер), бронь видна, у владельца — с фото; перекрепление меняет авто и фото

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
