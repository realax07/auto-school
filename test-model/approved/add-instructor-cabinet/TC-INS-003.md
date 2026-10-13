# TC-INS-003 — Запрос с подделанным/неверным токеном → 401

- ID кейса: TC-INS-003
- ID чеклиста: CHK-3
- Источник: CHK-3 → Requirement «Доступ к кабинету инструктора» → FR-18; Scenario «Сессия истекла — редирект на вход» (ветвь «неверный токен»; механика require_session, sdd §10.3)
- Тип: негативный
- Приоритет: Must
- Статус: automated — API-часть (tests/test_instructor_dashboard.py::test_dashboard_401_invalid_token, плановый ID TC-FR18D-002); браузерная часть (редирект на главную) — manual/toBeAutomated (Playwright)

## GIVEN / WHEN / THEN
- GIVEN успешного входа не было; у клиента произвольная строка в sessionStorage.session_token (подделанный/несуществующий токен)
- WHEN страница /instructor/dashboard запрашивает данные кабинета (GET /api/instructor/dashboard с X-Session-Token: <подделка>)
- THEN бэкенд отвечает 401 {"ok": false}; выполнен клиентский редирект на главную

## Предусловия
- Сервис собран (create_app(), чистая БД); токен «not-a-real-token» не входит в реестр сессий (auth._sessions).
- Для UI-части: браузер/Playwright; в sessionStorage вручную положить фейковый session_token.

## Шаги
1. GET /api/instructor/dashboard с заголовком X-Session-Token: not-a-real-token.
2. (UI) Положить в sessionStorage.session_token = "not-a-real-token", открыть /instructor/dashboard, наблюдать поведение.

## Ожидаемый результат
1. 401, тело точно {"ok": false}; код отличим от 403 (сессии нет — не «чужая роль»).
2. Контент не отрисован; редирект на `/`.

## Тестовые данные
Невалидный токен: not-a-real-token.
