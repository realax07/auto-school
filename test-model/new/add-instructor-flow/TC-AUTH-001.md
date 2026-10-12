# TC-AUTH-001 — Вход одобренного инструктора: 200, сессия, route=cabinet

- ID кейса: TC-AUTH-001
- ID чеклиста: CHK-35
- Источник: CHK-35 → Requirement «Вход инструктора через общий механизм авторизации» (домен instructor-auth) → FR-13; Scenario «Вход одобренного инструктора» + «Пользователь найден — заглушка кабинета»; sdd §15.5
- Тип: позитивный
- Приоритет: Must
- Статус: automated — tests/test_auth_route.py::test_login_instructor_approved_route_cabinet (плановый ID TC-FR13-001 в docstring — до утверждения кейсов, rule 6). Ответ /api/auth/me — тот же тест

## GIVEN / WHEN / THEN
- GIVEN заявка одобрена; пользователь с email E и хэшем пароля P существует в users (role='instructor')
- WHEN POST /api/auth/login с телом {"email": E, "password": P}
- THEN 200 {"ok": true, "token": "<строка>", "route": "cabinet"}; сессия (токен) выдана как §10.1; фронт направляет на /instructor/cabinet-stub

## Предусловия
- Сервис собран через create_app() (все роутеры); TestClient без сети; чистая БД в tmp, init_db.
- Анти-брутфорс-состояние чистое (auth._bf.clear() до/после теста — механика test_auth_route.py).

## Шаги
1. POST /api/instructors/apply (валидная анкета) → 200.
2. approve через админ-API → 200.
3. POST /api/auth/login {"email": "instr@example.com", "password": "Instr1234"} → зафиксировать статус/тело.
4. GET /api/auth/me с X-Session-Token из ответа.

## Ожидаемый результат
3. 200; ok=true, route="cabinet", token — непустая строка.
4. 200; user.email == instr@example.com — сессия действительна.

## Тестовые данные
Анкета (набор test_auth_route.py::_apply): instr@example.com / Instr1234, work_format sber. Админ: admin / admin-pass-2026.
