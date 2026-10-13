# TC-AUTH-008 — Граница: регресс роутинга ученика → student-cabinet

- ID кейса: TC-AUTH-008
- ID чеклиста: CHK-42
- Источник: CHK-42 → Requirement «Роутинг после входа по статусу» (домен instructor-auth) → FR-13; sdd §15.5 (регресс Спринта 1: role='student' → route=student-cabinet → /cabinet, поведение без изменений)
- Тип: граничный
- Приоритет: Must
- Статус: automated — tests/test_auth_route.py::test_login_student_route_student_cabinet (плановый ID TC-FR13-006-смежный; route=student-cabinet, token выдан). До утверждения кейсов (rule 6)

## GIVEN / WHEN / THEN
- GIVEN зарегистрирован ученик (role='student', Спринт 0)
- WHEN POST /api/auth/login с верными кредами ученика
- THEN 200 {"ok": true, "token": <строка>, "route": "student-cabinet"}; сессия выдается; фронт ведет на /cabinet — поведение ученического входа без изменений

## Предусловия
- Сервис собран через create_app(); TestClient без сети; чистая БД в tmp, init_db; состояние анти-брутфорса чистое.

## Шаги
1. POST /api/register — базовый ученик petrova@example.com / Qwerty123 → 200.
2. POST /api/auth/login {"email": "petrova@example.com", "password": "Qwerty123"}.
3. Зафиксировать статус/тело; проверить наличие token.

## Ожидаемый результат
2. 200 {"ok": true, "token": <непустая строка>, "route": "student-cabinet"}.
(Фронт: редирект на /cabinet — механика Спринта 1 без изменений.)

## Тестовые данные
Ученик — базовый набор (TC-AUTH-001 Спринта 1): petrova@example.com / Qwerty123.
