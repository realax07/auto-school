# TC-S7BE-018 — MAJ-1 регресс: PUT availability × активные брони → 409 с перечнем, график не изменен

- Автотест: `tests/test_s7_backend.py::test_s7_put_availability_409_maj1_regression`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (MAJ-1 арх-ревью, наследование Спринта 5)
- Трассировка:
  - Requirement: Сохранение и восстановление графика (openspec/changes/add-car-validation-booking/specs/instructor-availability/spec.md)
  - Scenario: PUT с удалением интервала с активной бронью отклоняется (MAJ-1) (openspec/changes/add-car-validation-booking/specs/instructor-availability/spec.md)
  - Scenario: Интервалы с только отклоненными бронями замене не мешают (openspec/changes/add-car-validation-booking/specs/instructor-availability/spec.md)

## GIVEN / WHEN / THEN
- GIVEN инструктор с сохраненным графиком и бронями 'new'/'confirmed'/'rejected' на интервалах
- WHEN PUT /api/instructor/availability, удаляющий интервал с активной бронью; затем с только 'rejected'; смена статуса авто при наличии брони
- THEN удаление интервала с 'new'/'confirmed' → 409 с ПЕРЕЧНЕМ затронутых интервалов (conflicts с booking_statuses), график НЕ изменен (guard в write-транзакции); интервал с только 'rejected' замене не мешает; бронь на валидационный статус авто не влияет (MIN-2)

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
