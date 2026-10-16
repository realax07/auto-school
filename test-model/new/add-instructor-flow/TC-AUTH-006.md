# TC-AUTH-006 — Негатив: неверный пароль против заявки → 401 без route/reason

- ID кейса: TC-AUTH-006
- ID чеклиста: CHK-40
- Источник: CHK-40 → Requirement «Роутинг после входа по статусу» (домен instructor-auth) → FR-13; Scenario «Статусный экран недоступен без проверки пароля» (фиктивная проверка — та же схема тайминга, что §10.1)
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_auth_route.py::test_login_wrong_password_against_application_401 (плановый ID TC-FR13-005). До утверждения кейсов (rule 6)

## GIVEN / WHEN / THEN
- GIVEN существует заявка в статусе waiting (или deny) с email E
- WHEN POST /api/auth/login {"email": E, "password": <неверный>}
- THEN 401 единое сообщение; route и reason НЕ выдаются — проверка пароля обязательна и для статусных маршрутов

## Предусловия
- Сервис собран через create_app(); TestClient без сети; чистая БД в tmp, init_db; состояние анти-брутфорса чистое.

## Шаги
1. POST /api/instructors/apply (instr@example.com / Instr1234) → 200.
2. POST /api/auth/login {"email": "instr@example.com", "password": "WrongPass1"}.
3. Зафиксировать статус/тело; проверить отсутствие ключей route и reason.
4. (deny-вариант) Перевести заявку в deny с комментарием C; повторить шаги 2–3.

## Ожидаемый результат
2, 4. 401 {"ok": false, "error": "Неверный email или пароль"}; ключей route и reason в ответе НЕТ (причина не утекает без верного пароля).

## Тестовые данные
Анкета: instr@example.com / Instr1234, неверный WrongPass1. C: «Не подтверждена квалификация».

## Трассировка

### Requirement: Роутинг после входа по статусу
#### Scenario: Статусный экран недоступен без проверки пароля

