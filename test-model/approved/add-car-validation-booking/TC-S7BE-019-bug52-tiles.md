# TC-S7BE-019-bug52-tiles — Баг 5.2 (задача 3.1): плитки строятся от авторизованного photos{angle}, legacy-пути удалены (FR-42)

- Автотест: `tests/test_s7_backend.py::test_s7_bug_5_2_tile_urls_authorized_endpoint`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-car-validation-booking; ID-коллизия с тестом MAJ-1 (тот же TC-S7BE-019) — разнесены в два файла (прецедент TC-UI-024, решение ПМ/ретро)
- Трассировка:
  - Requirement: Фото автомобиля доступно владельцу (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Фото отображается в плитке инструктора (выдача бага 5.2) (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Scenario: Фото владельца отображается после перезагрузки и повторного входа (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)
  - Requirement: Одиночное фото автомобиля без ракурса (фото-контракт Спринта 3) (openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN инструктор с авто и загруженными ракурсами; REMOVED-дельта legacy-маршрута и photo_path/photo_url-полей
- WHEN GET /api/instructor/cars (выдача плиток); повторный вход с новым токеном; GET фото по выданному URL
- THEN в выдаче ТОЛЬКО URL авторизованных эндпоинтов (photos{angle}); legacy photo_url/файловые пути data/uploads не выдаются (статикой не раздается, NFR-1); URL валиден и после ПОВТОРНОГО ВХОДА — отдает image/* (фото переживает перезагрузку и перезаход)

## Примечание
- Партия change add-car-validation-booking (Спринт 7, Партия A); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); свод —
  test-model/impact/add-car-validation-booking.md.
- Ссылочные прогоны: полный сьют 340 passed (review-001, итерация 3,
  2026-10-30); e2e 34/34 (review-002-design, финал); приемка — ACCEPT
  (test-model/reviews/add-car-validation-booking/review-acceptance.md).
