# TC-MOD-004 — Негатив: все три эндпоинта без админ-токена → 401

- ID кейса: TC-MOD-004
- ID чеклиста: CHK-25
- Источник: CHK-25 → Requirement «Раздел заявок инструкторов в админке» (домен admin-moderation) → FR-14; Scenario «Доступ без админ-токена отклоняется»; sdd §15.2–15.4
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_instructor_admin.py::test_list_without_token_401 + ::test_all_endpoints_without_token_401 (GET-список, POST approve, POST deny без токена → 401 {"ok": false}; невалидный токен → 401). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN у клиента нет валидного админ-токена; существует заявка id A
- WHEN выполняются GET-список, POST approve и POST deny: без заголовка X-Admin-Token, с неизвестным токеном, с истекшим токеном (отдельные прогоны)
- THEN каждый запрос → 401 {"ok": false}, данные заявок не выдаются, действия не выполняются

## Предусловия
- Сервис собран через create_app() с роутерами; TestClient без сети; чистая БД в tmp, init_db; существует заявка (публичный apply).
- Истекший токен: инъекция времени/прямой ввод в реестр backend.admin._tokens токена с expires < now (паттерн test_auth.py::test_expired_token_401).

## Шаги
1. Создать заявку → id A.
2. GET /api/admin/instructor-applications без заголовка → зафиксировать.
3. POST /api/admin/instructor-applications/{A}/approve без заголовка → зафиксировать.
4. POST /api/admin/instructor-applications/{A}/deny (с телом-комментарием) без заголовка → зафиксировать.
5. Повторить шаги 2–4 с заголовком X-Admin-Token: «not-a-token» (неизвестный), затем с истекшим токеном.
6. SELECT статуса заявки и COUNT(*) заявок.

## Ожидаемый результат
2–5. Каждый ответ 401 с телом {"ok": false} (без данных заявок, без error-деталей).
6. Заявка осталась waiting; действия не выполнены.

## Тестовые данные
Заявка — базовый валидный набор (TC-APP-005); deny-тело: {"comment": "Не подтверждена квалификация"}. Невалидный токен: not-a-token.
