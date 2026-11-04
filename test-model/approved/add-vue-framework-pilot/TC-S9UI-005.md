# TC-S9UI-005 — Переходная ошибка обмена 409: экран остается в waiting, опрос продолжается, повтор обмена на следующем тике

- Автотест: `tests/test_ui_playwright.py::test_s9_pilot_exchange_409_stays_waiting_and_retries`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-vue-framework-pilot (Спринт 9)
- Трассировка:
  - Requirement: Пилотная страница «Ожидание модерации» на Vue (FR-86, ОВ-4) (openspec/changes/add-vue-framework-pilot/specs/Frontend/spec.md)
  - Scenario: Функциональность блока 2 выполняется на Vue-версии (openspec/changes/add-vue-framework-pilot/specs/Frontend/spec.md)

## GIVEN / WHEN / THEN
- GIVEN в localStorage сохранены application_poll_token и application_exchange_token; мок GET /api/instructors/application-status детерминирован по счетчику тиков: тик 1 → 200 waiting, тик 2 и далее → 200 approved (capture); POST /api/instructors/application-exchange замокан 409 {"ok":false,"error":"Обмен недоступен: заявка не одобрена"} (переходная ветка FR-81) с capture; таймеры страницы — виртуальные (page.clock)
- WHEN страница загружена (тик 1 → waiting); прокручено окно 12 100 мс (тик 2 → approved → обмен → 409); затем прокручено следующее окно 12 100 мс
- THEN после 409 редиректа НЕТ — URL остался /instructors/pending (экран в waiting); опрос не прерван: тик №3 приходит в следующем окне и повтор обмена уходит (status-запросов = 3, обменов = 2); URL по-прежнему /instructors/pending — переходная ошибка не завершает цикл (FR-81: ошибка обмена — остаться в waiting, опрос продолжается)

## Примечание
- Партия change add-vue-framework-pilot (Спринт 9, задача 5.1 — пилотная страница
  Vue /instructors/pending; контракт опроса — change add-application-status-polling);
  кейсы живут трассировкой TC-ID в docstring автотеста (rule 6).
- Ссылочные прогоны: полный прогон ветки — 380 passed (факт ПМ).
