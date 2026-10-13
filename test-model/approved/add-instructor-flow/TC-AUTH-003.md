# TC-AUTH-003 — Негатив: верный email инструктора, неверный пароль → 401

- ID кейса: TC-AUTH-003
- ID чеклиста: CHK-37
- Источник: CHK-37 → Requirement «Вход инструктора через общий механизм авторизации» (домен instructor-auth) → FR-13; Scenario «Неверный пароль отклоняется единым сообщением»
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_auth.py::test_login_failures_identical_message (users-путь) + tests/test_auth_route.py::test_login_wrong_password_against_application_401 (TC-FR13-005 — против заявки; users-вариант инструктора — тот же контракт). До утверждения кейсов (rule 6)

## GIVEN / WHEN / THEN
- GIVEN одобренный инструктор с email E и паролем P существует в users
- WHEN POST /api/auth/login {"email": E, "password": <неверный>}
- THEN 401 единое сообщение (AUTH_FAIL_MESSAGE); сессия не выдается

## Предусловия
- Сервис собран через create_app(); TestClient без сети; чистая БД в tmp, init_db; состояние анти-брутфорса чистое; одобренный инструктор instr@example.com / Instr1234 (apply + approve).

## Шаги
1. Создать инструктора: apply + approve → 200.
2. POST /api/auth/login {"email": "instr@example.com", "password": "WrongPass1"}.
3. Зафиксировать статус/тело; сравнить с телом отказа из TC-AUTH-002.

## Ожидаемый результат
2. 401 {"ok": false, "error": "Неверный email или пароль"}; ключа token нет.
3. Код и текст идентичны единым отказам учеников и несуществующих email.

## Тестовые данные
instr@example.com: верный пароль Instr1234, неверный WrongPass1. Админ: admin / admin-pass-2026.
