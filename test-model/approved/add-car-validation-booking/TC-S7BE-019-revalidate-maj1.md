# TC-S7BE-019-revalidate-maj1 — MAJ-1 review-001 (итерация 3): замена ракурса/СТС у validated → validating; повторный validate (решение ПМ)

- Автотест: `tests/test_s7_backend.py::test_s7_upload_to_validated_returns_to_validating_and_revalidate`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking; ID-коллизия с тестом бага 5.2 (тот же TC-S7BE-019) — разнесены в два файла (прецедент TC-UI-024, решение ПМ/ретро)
- Трассировка:
  - Requirement: Фото автомобиля доступно владельцу (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Ракурсы хранятся и заменяются независимо (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Requirement: Статусы валидации автомобиля (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Загрузка фото не меняет статус (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Requirement: Подтверждение автомобилей администратором (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Подтверждение при полном пороге переводит авто в validated (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Requirement: Видимость автомобиля ученикам по статусу валидации (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: В каталог новых учеников попадают только проверенные авто (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN авто в status='validated' с полным комплектом
- WHEN замена ЛЮБОГО ракурса, затем замена СТС; загрузка у draft/validating; повторный POST validate после каждой дозагрузки; GET каталога пока авто в validating
- THEN замена у validated переводит авто в validating (ответ upload-ручки несет итоговый status); у draft/validating статус не меняется (ОВ-7); повторный admin validate проходит (дважды: гейт ОВ-4 не обходится задним числом — пока авто в validating, оно скрыто из каталога новых учеников: catalog[0]["cars"] == [])

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
