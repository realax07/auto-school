# TC-UI-032 — MAJ-1 итерация 3: замена фото у validated через UI → «На валидации»; повторное подтверждение

- Автотест: `tests/test_ui_playwright.py::test_s7_validated_car_photo_replace_returns_to_validating`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (MAJ-1 review-001, решение ПМ)
- Трассировка:
  - Requirement: Фото автомобиля доступно владельцу (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Ракурсы хранятся и заменяются независимо (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Requirement: Видимость автомобиля ученикам по статусу валидации (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Автомобиль на проверке виден паре с желтым бейджем (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Проверенный автомобиль — бейдж и зеленая галочка (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Requirement: Подтверждение автомобилей администратором (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Подтверждение при полном пороге переводит авто в validated (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN живой сервер: авто в validated у пары с учеником; модалка-галерея инструктора
- WHEN замена фото через UI модалки; осмотр бейджа карточки/модалки и брони ученика; повторное подтверждение админом в validating-фильтре после дозагрузки
- THEN тост «Фото заменены — авто отправлено на повторную валидацию»; бейджи карточки и модалки — желтый «На валидации» (честная копия в модалке); у ученика пары бейдж «Не проверено»; после повторного подтверждения — «Проверено» (и ученику тоже) — гейт ОВ-4 не обходится задним числом

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
