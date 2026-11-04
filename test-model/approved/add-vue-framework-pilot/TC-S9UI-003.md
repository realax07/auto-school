# TC-S9UI-003 — waiting→rejected: переход на существующий экран отказа с причиной, без входа и перелогина

- Автотест: `tests/test_ui_playwright.py::test_s9_pilot_rejected_redirects_with_reason`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-vue-framework-pilot (Спринт 9)
- Трассировка:
  - Requirement: Пилотная страница «Ожидание модерации» на Vue (FR-86, ОВ-4) (openspec/changes/add-vue-framework-pilot/specs/Frontend/spec.md)
  - Scenario: Функциональность блока 2 выполняется на Vue-версии

## GIVEN / WHEN / THEN
- GIVEN в localStorage сохранены application_poll_token и application_exchange_token; GET /api/instructors/application-status замокан 200 {"ok":true,"status":"rejected","reason":"Документы не подтверждены"} с capture
- WHEN страница /instructors/pending загружена (первый тик статуса сразу)
- THEN выполнен переход на СУЩЕСТВУЮЩИЙ экран /instructors/rejected (тот же, что после логина route «rejected», Спринт 2) БЕЗ входа и перелогина; причина показана: #reason-text = «Документы не подтверждены»; причина передана через sessionStorage-ключ «instructor_rejected_reason»; опрос остановлен — ровно 1 тик статуса, повторных запросов нет

## Примечание
- Партия change add-vue-framework-pilot (Спринт 9, задача 5.1 — пилотная страница
  Vue /instructors/pending; контракт опроса — change add-application-status-polling);
  кейсы живут трассировкой TC-ID в docstring автотеста (rule 6).
- Ссылочные прогоны: полный прогон ветки — 380 passed (факт ПМ).
