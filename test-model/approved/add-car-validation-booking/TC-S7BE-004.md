# TC-S7BE-004 — Переходы submit/withdraw и guard недопустимых переходов (409), validated терминальный (ОВ-3)

- Автотест: `tests/test_s7_backend.py::test_s7_submit_withdraw_transitions`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Статусы валидации автомобиля (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Инструктор отправляет автомобиль на проверку (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Повторная отправка не в draft отклоняется (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Инструктор отзывает автомобиль с проверки (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN авто владельца в статусе draft
- WHEN submit → withdraw → повторный submit → попытки недопустимых переходов → validate (TC-S7BE-009) — полный цикл draft→validating→draft→validating→validated
- THEN submit переводит draft→validating, withdraw validating→draft; submit по validated → 409 (validated терминальный); submit по validating → 409 «не в статусе черновика»; withdraw по draft → 409

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
