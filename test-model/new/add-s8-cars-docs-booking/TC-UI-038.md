# TC-UI-038 — «Бронирования» удалены без остатков, запросы на слотах, отклонение с комментарием (FR-74)

- Автотест: `tests/test_ui_playwright.py::test_s8_bookings_section_removed_redirect_and_slot_reject`
- Приоритет: Must (FR-74)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-s8-cars-docs-booking (Спринт 8)
- Трассировка:
  - Requirement: Запросы и брони учеников на слотах календаря (openspec/changes/add-s8-cars-docs-booking/specs/instructor-availability/spec.md)
  - Scenario: Раздел «Бронирования» удален без остатков (openspec/changes/add-s8-cars-docs-booking/specs/instructor-availability/spec.md)
  - Scenario: Запрос виден именно на выбранном слоте (openspec/changes/add-s8-cars-docs-booking/specs/instructor-availability/spec.md)
  - Scenario: Решения по брони — немедленно, мимо кнопок графика (openspec/changes/add-s8-cars-docs-booking/specs/instructor-availability/spec.md)

## GIVEN / WHEN / THEN
- GIVEN дашборд инструктора с замоканным API: availability — Ср(2) 14:00–16:00 и 16:00–18:00; bookings — new-запрос Крыловой Дарьи Игоревны на слот 14:00–16:00 (weekday 2); reject 91 → 200 и очищает список
- WHEN открыта старая ссылка /instructor/dashboard#/bookings; проверяются слот запроса и соседний; клик по слоту запроса → модалка → «Отклонить»: пустая причина / пробелы / причина «В это время пересдача экзамена в ГИБДД» → подтверждение
- THEN редирект в календарь: #sec-calendar виден, #sec-bookings в DOM НЕТ, пункта меню «Бронирования» НЕТ, «Календарь» active, заголовок «Календарь», хеш #/bookings очищен из URL (механика BUG-047); запрос РОВНО на своем слоте: единственная ячейка .reqslot с data-k="2-14" и ФИО ученика, соседний слот 2-16 — чистый слот графика («cal-slot on», без чужой метки); отклонение: кнопка disabled без причины и с пробелами, с причиной enabled; POST /api/instructor/bookings/91/reject {comment: «В это время пересдача экзамена в ГИБДД»} — решение немедленно, мимо PUT графика, toast «Запрос отклонён»; календарь перезагружен: .reqslot нет, слот 2-14 снова в графике

## Примечание
- Партия change add-s8-cars-docs-booking (Спринт 8); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); полный прогон
  359 passed (integration, лог ПМ).
