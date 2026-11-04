# TC-S9UI-001 — Опрос статуса на Vue-странице ожидания: первый тик сразу, интервал ~12 с, остановка при уходе со страницы

- Автотест: `tests/test_ui_playwright.py::test_s9_pilot_polling_interval_and_stops_on_leave`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-vue-framework-pilot (Спринт 9)
- Трассировка:
  - Requirement: Пилотная страница «Ожидание модерации» на Vue (FR-86, ОВ-4) (openspec/changes/add-vue-framework-pilot/specs/Frontend/spec.md)
  - Scenario: Функциональность блока 2 выполняется на Vue-версии (openspec/changes/add-vue-framework-pilot/specs/Frontend/spec.md)

## GIVEN / WHEN / THEN
- GIVEN пилотная страница /instructors/pending обслуживается каркасом Vue; в localStorage сохранены идентификаторы заявки application_poll_token = ui-poll-token-0f1e2d3c4b5a6978 и application_exchange_token (как оставляет apply.js после сабмита анкеты); GET /api/instructors/application-status замокан 200 {"ok":true,"status":"waiting","reason":null} с capture-счетчиком запросов; таймеры страницы — виртуальные (page.clock, CLOCK_BASE)
- WHEN страница загружена (гидрация Vue, h1 виден); виртуальное время доведено до 11-й секунды и проверена стабильность счетчика; затем прокручено окно 12 100 мс; затем уход со страницы (goto «/») и прокручено еще 60 000 мс виртуального времени
- THEN первый тик статуса приходит СРАЗУ при загрузке (ровно 1 запрос к application-status); между 0 и 12 с второго тика нет (счетчик стабилен = 1); тик №2 приходит ровно в окне ~12 с (счетчик = 2); после ухода со страницы новых запросов нет — счетчик стабилен = 2 при 60 с виртуального времени (onUnmounted снял таймер, интервал 12 с — в границах блока 2, 10–15 с)

## Примечание
- Партия change add-vue-framework-pilot (Спринт 9, задача 5.1 — пилотная страница
  Vue /instructors/pending; контракт опроса — change add-application-status-polling);
  кейсы живут трассировкой TC-ID в docstring автотеста (rule 6).
- Ссылочные прогоны: полный прогон ветки — 380 passed (факт ПМ).
