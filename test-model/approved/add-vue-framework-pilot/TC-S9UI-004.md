# TC-S9UI-004 — Терминальная ошибка обмена 404: подсказка «войдите с email и паролем», токены удалены, опрос остановлен

- Автотест: `tests/test_ui_playwright.py::test_s9_pilot_exchange_404_terminal_login_hint_no_polling`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-vue-framework-pilot (Спринт 9)
- Трассировка:
  - Requirement: Пилотная страница «Ожидание модерации» на Vue (FR-86, ОВ-4) (openspec/changes/add-vue-framework-pilot/specs/Frontend/spec.md)
  - Scenario: Функциональность блока 2 выполняется на Vue-версии

## GIVEN / WHEN / THEN
- GIVEN в localStorage сохранены application_poll_token и application_exchange_token; GET /api/instructors/application-status замокан 200 {"ok":true,"status":"approved","reason":null} с capture; POST /api/instructors/application-exchange замокан 404 {"ok":false,"error":"Заявка не найдена"} с capture (токен потреблен/чужой — терминальная ветка контракта опроса); таймеры страницы — виртуальные (page.clock)
- WHEN страница /instructors/pending загружена (тик статуса → обмен → 404); затем прокручено 60 000 мс виртуального времени
- THEN показана подсказка .login-hint «Войдите с email и паролем.» при h1 «Заявка на рассмотрении» (страница не ушла с экрана ожидания); статус-запросов ровно 1, обменов ровно 1; application_poll_token и application_exchange_token удалены из localStorage; дальше 0 запросов — счетчики стабильны (= 1) при 60 с виртуального времени: терминальная ветка, таймер опроса снят (arch-review-002 MAJ-1)

## Примечание
- Партия change add-vue-framework-pilot (Спринт 9, задача 5.1 — пилотная страница
  Vue /instructors/pending; контракт опроса — change add-application-status-polling);
  кейсы живут трассировкой TC-ID в docstring автотеста (rule 6).
- Ссылочные прогоны: полный прогон ветки — 380 passed (факт ПМ).
