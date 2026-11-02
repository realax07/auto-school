# TC-S8BE-004 — ОВ-6: замена СТС у validated не сбрасывает валидацию; ракурсы сохраняют MAJ-1 (ОВ-6)

- Автотест: `tests/test_s8_backend.py::test_s8_sts_replacement_keeps_validated_ov6`
- Приоритет: Must (FR-69/FR-70, решение ОВ-6)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-s8-cars-docs-booking (Спринт 8)
- Трассировка:
  - Requirement: Замена СТС не влияет на статус валидации автомобиля
  - Scenario: Замена СТС у validated-авто не сбрасывает валидацию

## GIVEN / WHEN / THEN
- GIVEN approved-инструктор; авто с первичным СТС (verified v1), ракурсами front/rear/left и статусом validated (аранжировка — прямой UPDATE instructor_cars в БД)
- WHEN владелец загружает замену СТС (PNG); затем загружает замену ракурса right (JPEG2)
- THEN замена СТС: 200, document {status: pending, version: 2}, итоговый статус авто в ответе и в БД остается validated (ОВ-6 — сброса нет), photo_sts не перезаписан (FR-70), ракурсы не тронуты (photo_front на месте), версии [(1, verified), (2, pending)]; замена ракурса right: 200, статус авто → validating (в ответе и в БД) — MAJ-1: правило Спринта 7 для 5 ракурсов сохранено без изменений

## Примечание
- Партия change add-s8-cars-docs-booking (Спринт 8); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); полный прогон
  359 passed (integration, лог ПМ).
