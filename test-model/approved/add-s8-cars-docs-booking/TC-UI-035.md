# TC-UI-035 — Экраны «Мои автомобили»/«Мои документы» без виджетов (FR-73)

- Автотест: `tests/test_ui_playwright.py::test_s8_cars_and_docs_screens_have_no_widgets`
- Приоритет: Must (FR-73)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-s8-cars-docs-booking (Спринт 8)
- Трассировка:
  - Requirement: Виджет «Привязанные ученики» (openspec/changes/add-s8-cars-docs-booking/specs/student-requests/spec.md)
  - Scenario: Экраны «Мои автомобили» и «Мои документы» — без виджета (openspec/changes/add-s8-cars-docs-booking/specs/student-requests/spec.md)
  - Requirement: Виджет «Занятия на сегодня» — честная заглушка (openspec/changes/add-s8-cars-docs-booking/specs/student-requests/spec.md)
  - Scenario: Экраны «Мои автомобили» и «Мои документы» — без виджета (openspec/changes/add-s8-cars-docs-booking/specs/student-requests/spec.md)

## GIVEN / WHEN / THEN
- GIVEN дашборд инструктора с замоканным API (cars [], documents []); открыт /instructor/dashboard
- WHEN открываются по очереди разделы: «Мой день» → «Мои автомобили» → «Профиль и документы» → снова «Мой день»
- THEN на главной все три виджета (#w-students, #w-requests, #w-today) видимы; на «Мои автомобили» и на «Профиль и документы» контейнер .widgets имеет display:none — ни один из трех виджетов (привязанные ученики, запросы учеников, занятия на сегодня) не отображен (FR-73); возврат на главную — виджеты снова видимы (явные исключения Заказчика: место виджетам — главная кабинета)

## Примечание
- Партия change add-s8-cars-docs-booking (Спринт 8); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); полный прогон
  359 passed (integration, лог ПМ).
