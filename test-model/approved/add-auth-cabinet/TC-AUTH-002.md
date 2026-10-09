# TC-AUTH-002 — Пароль проверяется против bcrypt-хэша из users

- ID кейса: TC-AUTH-002
- ID чеклиста: CHK-3
- Источник: CHK-3 → Requirement «Хранение учетных данных» (домен auth) → FR-3; Scenario «Проверка пароля против хэша»
- Тип: позитивный
- Приоритет: Must
- Статус: automated — tests/test_auth.py::test_login_checks_password_against_bcrypt_hash

## GIVEN / WHEN / THEN
- GIVEN ученик зарегистрирован; в таблице users для его email хранится bcrypt-хэш пароля
- WHEN выполняется вход с корректным паролем (POST /api/auth/login) и прямой SELECT из users
- THEN вход разрешен (200); в users для email — bcrypt-хэш (префикс $2b$), bcrypt.checkpw(P, hash) = true; открытый пароль в колонке отсутствует

## Предусловия
- Как в TC-AUTH-001 (create_app, чистая БД, env, health 200).

## Шаги
1. POST /api/register с базовым пользователем → 200.
2. Прямой SELECT password_hash FROM users WHERE email = 'petrova@example.com' (sqlite3).
3. Проверить префикс хэша и что bcrypt.checkpw(b"Qwerty123", hash) = True.
4. POST /api/auth/login с корректным паролем.

## Ожидаемый результат
2. В users ровно одна запись; password_hash содержит "$2b$" и != "Qwerty123".
3. bcrypt.checkpw(b"Qwerty123", password_hash) = True.
4. 200 {"ok": true, "token": "..."} — вход разрешен сравнением с хэшем.

## Тестовые данные
Базовый валидный пользователь TC-AUTH-001; пароль P = "Qwerty123".
