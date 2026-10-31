# TC-UI-030 — Сквозной статусный флоу через UI: инструктор → админ → ученик

- Автотест: `tests/test_ui_playwright.py::test_s7_car_status_transitions_admin_validate_student_badge`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Статусы валидации автомобиля (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Инструктор отправляет автомобиль на проверку (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Инструктор отзывает автомобиль с проверки (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Requirement: Подтверждение автомобилей администратором (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Фильтр «На валидации» показывает только validating (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Подтверждение при полном пороге переводит авто в validated (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Requirement: Видимость автомобиля ученикам по статусу валидации (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Проверенный автомобиль — бейдж и зеленая галочка (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Requirement: Подтвержденная бронь в календарях обоих (openspec/changes/add-car-validation-booking/specs/booking/spec.md)
  - Scenario: Календарь ученика показывает фото прикрепленного авто (openspec/changes/add-car-validation-booking/specs/booking/spec.md)

## GIVEN / WHEN / THEN
- GIVEN живой сервер (без page.route): одобренный инструктор, новый авто «Черновик» с СТС, принятая пара с учеником, админ
- WHEN инструктор: 3 ракурса (API) → «Отправить на валидацию» → «Вернуть в черновик» → повторная отправка → перезагрузка; админ: раздел «Автомобили» → фильтр «На валидации» → модалка с чек-листом → «Подтвердить»; ученик принятой пары открывает брони
- THEN бейдж «На валидации» после перезагрузки сохраняется, отзыв возвращает «Черновик»; админ видит авто в validating-фильтре, «Подтвердить» активна (3 ракурса + СТС) → бейдж «Проверено» (+✓); ученик: бейдж «Проверено», карточка авто с фото рядом со слотами

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
