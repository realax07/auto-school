# TC-S5BE-007 — Матрица доступа к фото + СТС ученику не выдается (MIN-2)

- Автотест: `tests/test_s5_backend.py::test_s5_car_photo_access_matrix_and_sts`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Фото автомобиля доступно владельцу (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Фото ракурсов доступно ученику пары (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Ученик без принятой заявки фото не получает (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: СТС не выдается ученику (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)
  - Scenario: Заблокированный автомобиль недоступен ученикам (openspec/changes/add-booking-docs/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN пара инструктор+ученик с авто и загруженным front; посторонний ученик и чужой инструктор
- WHEN GET фото и СТС от владельца/ученика пары/постороннего/гостя; затем block авто админом
- THEN ученик пары 200; без пары 403; чужой инструктор 404; гость 401; СТС ученику 403; после блокировки ученику 404, владельцу 200 (FR-42, NFR-7, ОВ-1/MIN-2)

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
