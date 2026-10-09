# TC-AUTH-005 — GET /api/auth/me возвращает данные записи ученика

- ID кейса: TC-AUTH-005
- ID чеклиста: CHK-2
- Источник: CHK-2 → Requirement «Вход ученика» (домен auth) → FR-1; контракт sdd.md §10.3; Scenario «Успешный вход ученика» (токен принимается защищенным ресурсом)
- Тип: позитивный
- Приоритет: Must
- Статус: automated — tests/test_auth.py::test_me_returns_user_record

## GIVEN / WHEN / THEN
- GIVEN ученик успешно вошел и получил сессионный токен
- WHEN GET /api/auth/me с заголовком X-Session-Token: <token>
- THEN 200 {"ok": true, "user": {"id": int, "surname": "...", "name": "...", "patronymic": "...", "email": "..."}} — данные записи из users, значения совпадают с зарегистрированными

## Предусловия
- Как в TC-AUTH-001.

## Шаги
1. POST /api/register с базовым пользователем → 200.
2. POST /api/auth/login → 200, извлечь token.
3. GET /api/auth/me с заголовком X-Session-Token: <token>.
4. Сравнить тело user с зарегистрированными значениями.

## Ожидаемый результат
3. 200; тело:
```json
{"ok": true, "user": {"id": 1, "surname": "Петрова-Водкина", "name": "Анна", "patronymic": "Оттовна", "email": "petrova@example.com"}}
```
4. user == зарегистрированным значениям (посимвольно); лишних полей в user нет.

## Тестовые данные
Базовый валидный пользователь TC-AUTH-001 (email petrova@example.com, пароль Qwerty123).
