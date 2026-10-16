# TC-MOD-013 — Вход одобренного инструктора с паролем из анкеты

- ID кейса: TC-MOD-013
- ID чеклиста: CHK-34
- Источник: CHK-34 → Requirement «Одобрение заявки создает пользователя» (домен admin-moderation) → FR-16, FR-13; Scenario «Вход одобренного инструктора с паролем из анкеты» (покрытие REQ хэша: CHK-21, CHK-34, CHK-35)
- Тип: позитивный
- Приоритет: Must
- Статус: automated — tests/test_auth_route.py::test_login_instructor_approved_route_cabinet (вход с Instr1234 после approve → 200, route=cabinet, /api/auth/me отвечает). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN заявка одобрена; в users создан пользователь с хэшем, перенесенным из заявки
- WHEN вход по email и паролю, указанному в анкете, через /api/auth/login
- THEN вход успешен (проверка пароля против перенесенного хэша): 200, сессия выдана

## Предусловия
- Сервис собран через create_app() (все роутеры); TestClient без сети; чистая БД в tmp, init_db; анти-брутфорс-состояние чистое (auth._bf cleared — механика test_auth_route.py).

## Шаги
1. POST /api/instructors/apply с паролем P → 200.
2. approve через админ-API → 200.
3. POST /api/auth/login {"email": E, "password": P} → зафиксировать.
4. GET /api/auth/me с выданным X-Session-Token.

## Ожидаемый результат
3. 200 {"ok": true, "token": <строка>, "route": "cabinet"}.
4. 200; user.email == E — сессия действительна, пароль сверялся против хэша из заявки.

## Тестовые данные
Заявка — набор test_auth_route.py::_apply: instr@example.com / Instr1234 (work_format sber). Админ: admin / admin-pass-2026.

## Трассировка

### Requirement: Одобрение заявки создает пользователя
#### Scenario: Вход одобренного инструктора с паролем из анкеты

