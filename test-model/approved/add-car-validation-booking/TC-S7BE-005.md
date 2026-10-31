# TC-S7BE-005 — Guard-и прав доступа переходов: 401/403/404-матрица (NFR-7)

- Автотест: `tests/test_s7_backend.py::test_s7_submit_withdraw_access_guards`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Статусы валидации автомобиля (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Чужой автомобиль не переводится между статусами (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN авто инструктора; отдельные токены гостя, ученика, админа и чужого инструктора
- WHEN transition-запросы (submit/withdraw) по чужим/несуществующим авто под каждым токеном
- THEN гость → 401, ученик → 403, чужой инструктор → 404, несуществующий → 404; статус чужого авто не меняется

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
