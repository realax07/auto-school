# TC-S7BE-001 — Миграция существующих авто → validated на предсозданной БД, идемпотентность (ОВ-1)

- Автотест: `tests/test_s7_backend.py::test_s7_migration_existing_cars_become_validated`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Статусы валидации автомобиля (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Существующие автомобили мигрируют в validated (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Брони сохраняются при переходе на статусную модель (в т.ч. заблокированных авто) (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN предсозданная «легаси»-БД (схема до статусной модели, 2 строки авто)
- WHEN выполняется init_db ДВАЖДЫ; проверяется DDL колонки status
- THEN обе строки получают 'validated' через DEFAULT (не исчезают из каталога и пар); columns.count("status") == 1 — колонка не дублируется; в DDL есть CHECK (draft/validating/validated)

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
