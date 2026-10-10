# BUG-001: успешная регистрация не вела в кабинет

> Автор: PM (main) · Дата: 2026-10-10 · Статус: ИСПРАВЛЕНО

## Симптом

После успешной регистрации пользователь попадал на страницу-заглушку
/registered («Регистрация завершена»), в кабинет ученика не попадал —
требовался отдельный вход через модалку.

## Ожидаемое поведение (решение Заказчика, 2026-10-10)

Успешная регистрация → пользователь сразу в кабинете /cabinet, сессия
выдается при регистрации (отдельный вход не нужен).

## Причина

- backend/register.py возвращал только {ok:true} — сессия не выдавалась.
- frontend/index.html редиректил на /registered.

## Исправление

- backend/auth.py: + _session_issue(user_id) — выдача сессии единым
  механизмом с login (secrets.token_urlsafe(32), TTL 12ч).
- backend/register.py: после INSERT — SELECT id, ответ {ok:true, token}.
- frontend/index.html: сабмит регистрации → sessionStorage['session_token']
  → location.href='/cabinet'.

## Проверка

- E2E: register 200 {ok, token} → GET /api/auth/me по токену 200 {ok, user}.
- pytest tests/: 97 passed (в т.ч. регресс Спринта 0; assert-правки
  test_register/test_static под расширенное тело ответа).
- openspec validate --all --strict: 2/2; flow_check: OK.

## Трассировка

- FR-4 (кабинет после входа), FR-1/FR-7 (сессия/доступ по токену).
