# TC-UI-031 — Админка «Автомобили»: validating-фильтр, заблокированное «Подтвердить» с перечнем; сайдбар без заглушек (FR-58)

- Автотест: `tests/test_ui_playwright.py::test_s7_admin_cars_filter_and_incomplete_approve_locked`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking (Спринт 7, Партия A)
- Трассировка:
  - Requirement: Подтверждение автомобилей администратором (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Фильтр «На валидации» показывает только validating (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Кнопка подтверждения заблокирована при неполном комплекте (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Requirement: Единая навигация по ролям без демо-заглушек (openspec/changes/add-car-validation-booking/specs/navigation/spec.md)
  - Scenario: В админке нет пунктов «Расписание» и «Отношения» (openspec/changes/add-car-validation-booking/specs/navigation/spec.md)

## GIVEN / WHEN / THEN
- GIVEN живой сервер: авто в validating с 2 ракурсами и СТС, авто в draft и validated
- WHEN админ открывает раздел «Автомобили», применяет фильтр «На валидации», открывает модалку ОВ-4; осматривает сайдбар админки
- THEN фильтр показывает только validating-авто (черновики и «Проверено» скрыты, счетчик фильтра верный); «Подтвердить» ЗАБЛОКИРОВАНО с перечнем недостающего; сайдбар без заглушек «Отношения»/«Расписания»

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
