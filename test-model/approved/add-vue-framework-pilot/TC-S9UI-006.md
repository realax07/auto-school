# TC-S9UI-006 — Статический режим без сохраненного идентификатора заявки: разметка на месте, 0 запросов статуса и обмена

- Автотест: `tests/test_ui_playwright.py::test_s9_pilot_without_tokens_static_mode_zero_requests`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-vue-framework-pilot (Спринт 9)
- Трассировка:
  - Requirement: Пилотная страница «Ожидание модерации» на Vue (FR-86, ОВ-4) (openspec/changes/add-vue-framework-pilot/specs/Frontend/spec.md)
  - Scenario: Статический режим без идентификатора сохраняется

## GIVEN / WHEN / THEN
- GIVEN экран /instructors/pending открыт прямой ссылкой БЕЗ сохраненных идентификаторов: application_poll_token и application_exchange_token в localStorage отсутствуют (seed-скрипт токенов не применялся); GET /api/instructors/application-status (200 waiting) и POST /api/instructors/application-exchange (200 ok) замоканы с capture-счетчиками; таймеры страницы — виртуальные (page.clock)
- WHEN страница загружена (гидрация Vue); затем прокручено 60 000 мс виртуального времени
- THEN статический текст экрана на месте: h1 «Заявка на рассмотрении», .kicker «Заявка инструктора», блока подсказки .login-hint нет; за 60 с виртуального времени 0 запросов статуса и 0 запросов обмена — статический режим без запросов статуса и без ошибок (FR-80)

## Примечание
- Партия change add-vue-framework-pilot (Спринт 9, задача 5.1 — пилотная страница
  Vue /instructors/pending; контракт опроса — change add-application-status-polling);
  кейсы живут трассировкой TC-ID в docstring автотеста (rule 6).
- Ссылочные прогоны: полный прогон ветки — 380 passed (факт ПМ).
