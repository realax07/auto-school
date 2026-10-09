# TC-AUTH-009 — Logout аннулирует токен

- ID кейса: TC-AUTH-009
- ID чеклиста: CHK-4, CHK-12
- Источник: CHK-4/CHK-12 → Requirement «Выход ученика» (домен auth) → FR-8; Scenarios «Успешный выход», «Токен не принимается после выхода»
- Тип: позитивный
- Приоритет: Must
- Статус: automated — tests/test_auth.py::test_logout_invalidates_token

Примечание: CHK-4 (аннулирование) и CHK-12 (отклонение аннулированного) — одна сессия «успех → использование после», один кейс.

## GIVEN / WHEN / THEN
- GIVEN ученик вошел в систему и находится в кабинете; его токен действующий
- WHEN POST /api/auth/logout с заголовком X-Session-Token: <token>, затем GET /api/auth/me с тем же токеном
- THEN logout: 200 {"ok": true} — токен удален из реестра; повторный /me: 401 {"ok": false} — токен отклонен как неавторизованный; фронт: очистка sessionStorage и редирект на главную (браузерная часть — TC-AUTH-018)

## Предусловия
- Как в TC-AUTH-001.

## Шаги
1. POST /api/register → 200; POST /api/auth/login → 200, извлечь token.
2. POST /api/auth/logout с заголовком X-Session-Token: <token> → зафиксировать ответ.
3. GET /api/auth/me с тем же заголовком → зафиксировать ответ.

## Ожидаемый результат
2. 200 {"ok": true}.
3. 401 {"ok": false}; поле token в теле отсутствует.

## Тестовые данные
Базовый пользователь TC-AUTH-001; заголовок X-Session-Token: <token из шага 1>.
