# TC-AUTH-010 — Logout без валидного токена: 401, аннулировать нечего

- ID кейса: TC-AUTH-010
- ID чеклиста: CHK-11
- Источник: CHK-11 → Requirement «Сессии с ограниченным сроком действия» (домен auth) → FR-1, FR-7 («токен выдается только после успешного входа»); контракт sdd.md §10.2
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_auth.py::test_logout_without_valid_token_401

## GIVEN / WHEN / THEN
- GIVEN успешный вход не выполнялся (или токен неверный/истекший)
- WHEN POST /api/auth/logout с заголовком X-Session-Token: "<произвольная строка>"
- THEN 401 {"ok": false} — аннулировать нечего; поле token в теле отсутствует

## Предусловия
- Как в TC-AUTH-001; реестр сессий пуст.

## Шаги
1. POST /api/auth/logout с заголовком X-Session-Token: "no-such-token" → зафиксировать ответ.

## Ожидаемый результат
1. 401 {"ok": false}; токен не выдан.

## Тестовые данные
Заголовок X-Session-Token: "no-such-token".
