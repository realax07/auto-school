# TC-AUTH-004 — Негатив: waiting-заявка → route=pending БЕЗ сессии

- ID кейса: TC-AUTH-004
- ID чеклиста: CHK-38
- Источник: CHK-38 → Requirement «Роутинг после входа по статусу» (домен instructor-auth) → FR-13; Scenario «Заявка waiting — экран ожидания»; sdd §15.5
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_auth_route.py::test_login_waiting_application_pending_no_session (плановый ID TC-FR13-002): 200 {ok, route:'pending'}, ключа token нет. До утверждения кейсов (rule 6)

## GIVEN / WHEN / THEN
- GIVEN существует заявка в статусе waiting (записи users НЕТ); пароль из анкеты верный
- WHEN POST /api/auth/login {"email": E, "password": P}
- THEN 200 {"ok": true, "route": "pending"} и ТОКЕН/СЕССИЯ НЕ ВЫДАЮТСЯ (ключа token в ответе нет); фронт ведет на экран ожидания /instructors/pending («заявка на рассмотрении»)

## Предусловия
- Сервис собран через create_app(); TestClient без сети; чистая БД в tmp, init_db; состояние анти-брутфорса чистое.

## Шаги
1. POST /api/instructors/apply (instr@example.com / Instr1234) → 200.
2. POST /api/auth/login {"email": "instr@example.com", "password": "Instr1234"}.
3. Зафиксировать статус/тело; проверить отсутствие ключа token.
4. (браузерная часть, manual) Проверить редирект фронта на /instructors/pending.

## Ожидаемый результат
2. 200 {"ok": true, "route": "pending"}; ключа token НЕТ.
4. Экран /instructors/pending открыт («Заявка на рассмотрении»).

## Тестовые данные
Анкета: instr@example.com / Instr1234 (набор test_auth_route.py::_apply).
