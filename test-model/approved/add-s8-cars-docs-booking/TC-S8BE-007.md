# TC-S8BE-007 — Баг 5.2 (регресс): список авто выдает URL авторизованных фото-эндпоинтов, без файловых путей (баг 5.2)

- Автотест: `tests/test_s8_backend.py::test_s8_car_tiles_use_photo_endpoints_bug52`
- Приоритет: Must (FR-42 — плитки; регресс бага 5.2 задания Спринта 8)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-s8-cars-docs-booking (Спринт 8)
- Трассировка:
  - Requirement: Замена СТС не влияет на статус валидации автомобиля (openspec/changes/add-s8-cars-docs-booking/specs/instructor-cars/spec.md)
  - Scenario: Диагностика СТС-симптома предшествует фиксу — после фикса СТС/фото на созданном авто выдаются рабочими авторизованными эндпоинтами (openspec/changes/add-s8-cars-docs-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN approved-инструктор с авто (JSON-создание); загружены ракурс front и первичный СТС (verified v1)
- WHEN GET /api/instructor/cars владельцем; затем GET выданных URL фото (front и sts) с сессией владельца; повторный GET списка
- THEN photos.front = /api/instructor/cars/{id}/photo/front, photos.rear = None, sts_url = /api/instructor/cars/{id}/sts, has_sts = true; в сериализации списка нет подстроки «data/» (файловые пути клиенту не выдаются) и ключа photo_path (устаревшая колонка не выдается); фото-эндпоинты отвечают 200 с содержимым загруженных файлов (плитки переживают повторный вход); повторный GET списка выдает те же photos

## Примечание
- Партия change add-s8-cars-docs-booking (Спринт 8); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); полный прогон
  359 passed (integration, лог ПМ).
- Отдельного Scenario под выдачу плиток в specs/*/spec.md нет —
  трассировка ближайшая (Scenario «Диагностика СТС-симптома
  предшествует фиксу» + исторический FR-42 Спринта 4); гэп зафиксирован
  для ПМ.
