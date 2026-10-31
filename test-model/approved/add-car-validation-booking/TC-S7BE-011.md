# TC-S7BE-011 — Каталог/авто-фильтры — только validated серверно; инструктор без validated остается (ОВ-2)

- Автотест: `tests/test_s7_backend.py::test_s7_catalog_only_validated_empty_block_kept`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Видимость автомобиля ученикам по статусу валидации (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: В каталог новых учеников попадают только проверенные авто (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Requirement: Каталог одобренных инструкторов для ученика (openspec/changes/add-car-validation-booking/specs/student-instructor-choice/spec.md)
  - Scenario: В каталоге участвуют только проверенные автомобили (openspec/changes/add-car-validation-booking/specs/student-instructor-choice/spec.md)
  - Scenario: Авто-фильтры каталога учитывают только validated (openspec/changes/add-car-validation-booking/specs/student-instructor-choice/spec.md)
  - Scenario: Инструктор без validated-авто остается в каталоге (openspec/changes/add-car-validation-booking/specs/student-instructor-choice/spec.md)

## GIVEN / WHEN / THEN
- GIVEN инструкторы с авто в draft/validating/validated и без validated-авто
- WHEN GET каталога новых учеников и авто-фильтров (в т.ч. по КПП)
- THEN авто в карточках и фильтрах — ТОЛЬКО validated (серверно), draft/validating не участвуют; инструктор без validated-авто остается в каталоге с пустым блоком авто (не исчезает); фильтр по КПП находит только по validated

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
