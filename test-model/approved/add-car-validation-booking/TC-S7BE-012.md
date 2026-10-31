# TC-S7BE-012 — Матрица фото ученику пары: draft → 404 неразличение (в т.ч. прямой URL), validating/validated → выдача (NFR-4)

- Автотест: `tests/test_s7_backend.py::test_s7_pair_car_photo_draft_404_indistinctible`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Фото автомобиля доступно владельцу (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Фото ракурсов доступно ученику пары (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Ученик без принятой заявки фото не получает (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Requirement: Видимость автомобиля ученикам по статусу валидации (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Черновик скрыт от учеников (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Владелец видит свои автомобили во всех статусах (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN пара инструктор-ученик с авто; отдельный ученик НЕ из пары
- WHEN GET …/photo/{angle} учеником пары по всем статусам (включая прямой вызов URL по draft); тем же запросом — ученик не из пары; владельцем
- THEN draft → 404 неразличение (в т.ч. ПРЯМОЙ вызов); validating → выдается; validated → выдается; владелец видит во всех статусах; ученик не из пары → 403 и по draft тоже (не 404-различение с парой)

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
