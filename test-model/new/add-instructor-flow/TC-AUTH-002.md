# TC-AUTH-002 — Негатив: email отсутствует и в users, и в заявках → 401 единое сообщение

- ID кейса: TC-AUTH-002
- ID чеклиста: CHK-36
- Источник: CHK-36 → Requirement «Вход инструктора через общий механизм авторизации» (домен instructor-auth) → FR-13; Scenario «Единое сообщение при отсутствии и пользователя, и заявки»
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_auth_route.py::test_login_unknown_credentials_unified_401 (плановый ID TC-FR13-004; AUTH_FAIL_MESSAGE идентичен ученическому отказу — эталон tests/test_auth.py::test_login_failures_identical_message). До утверждения кейсов (rule 6)

## GIVEN / WHEN / THEN
- GIVEN email X отсутствует и в users, и в заявках
- WHEN POST /api/auth/login {"email": X, "password": <любой>}
- THEN 401 с тем же ЕДИНЫМ сообщением об отказе, что у учеников (код и текст идентичны AUTH_FAIL_MESSAGE «Неверный email или пароль»); сессия не выдается (ключа token нет)

## Предусловия
- Сервис собран через create_app(); TestClient без сети; чистая БД в tmp, init_db; состояние анти-брутфорса чистое.

## Шаги
1. POST /api/auth/login {"email": "ghost@example.com", "password": "Whatever123"}.
2. Зафиксировать статус и тело.
3. (эталон) POST /api/auth/login с неверным паролем ученика (petrova@example.com / WrongPass) — сравнить тело.

## Ожидаемый результат
2. 401 {"ok": false, "error": "Неверный email или пароль"}; ключа token нет.
3. Тело и код совпадают с ученическим отказом байт-в-байт.

## Тестовые данные
ghost@example.com / Whatever123 (пользователь не существует). Эталон ученика: petrova@example.com / Qwerty123 (регистрация) с неверным паролем.

## Трассировка

### Requirement: Вход инструктора через общий механизм авторизации
#### Scenario: Единое сообщение при отсутствии и пользователя, и заявки

