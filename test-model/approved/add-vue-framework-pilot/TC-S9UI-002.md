# TC-S9UI-002 — waiting→approved: обмен exchange_token на сессию, бесшовный переход в кабинет, чистка токенов

- Автотест: `tests/test_ui_playwright.py::test_s9_pilot_approved_exchange_redirects_cabinet_and_cleanup`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-vue-framework-pilot (Спринт 9)
- Трассировка:
  - Requirement: Пилотная страница «Ожидание модерации» на Vue (FR-86, ОВ-4) (openspec/changes/add-vue-framework-pilot/specs/Frontend/spec.md)
  - Scenario: Функциональность блока 2 выполняется на Vue-версии

## GIVEN / WHEN / THEN
- GIVEN в localStorage сохранены application_poll_token и application_exchange_token; GET /api/instructors/application-status замокан 200 {"ok":true,"status":"approved","reason":null} с capture; POST /api/instructors/application-exchange замокан 200 {"ok":true,"token":"ui-session-token-cabinet","route":"cabinet"} с capture; сессионный контур кабинета заглушен (/api/auth/me → ok, /api/instructor/** → ok — без 401-редиректа на «/»)
- WHEN страница /instructors/pending загружена (первый тик статуса сразу); после редиректа выполнен возврат page.goto /instructors/pending
- THEN редирект на /instructor/dashboard; статус-запросов ровно 1, обменов ровно 1; sessionStorage session_token = «ui-session-token-cabinet», application_poll_token и application_exchange_token удалены из localStorage ДО редиректа; возврат на экран ожидания после чистки — статический режим: h1 «Заявка на рассмотрении» и 0 новых запросов статуса (счетчик стабилен = 1 при settle 3 с)

## Примечание
- Партия change add-vue-framework-pilot (Спринт 9, задача 5.1 — пилотная страница
  Vue /instructors/pending; контракт опроса — change add-application-status-polling);
  кейсы живут трассировкой TC-ID в docstring автотеста (rule 6).
- Ссылочные прогоны: полный прогон ветки — 380 passed (факт ПМ).
