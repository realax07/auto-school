# TC-APP-021 — Одобренная заявка: хэш в users совпадает, вход с паролем P успешен

- ID кейса: TC-APP-021
- ID чеклиста: CHK-21
- Источник: CHK-21 → Requirement «Хранение пароля заявки только в виде bcrypt-хэша» (домен instructor-application) → FR-11.1; Scenario «Одобренная заявка переносит хэш без повторного хэширования»
- Тип: позитивный
- Приоритет: Must
- Статус: automated — tests/test_instructor_admin.py::test_approve_creates_user_with_instructor_role_and_same_hash (users.password_hash == заявочный) + tests/test_auth_route.py::test_login_instructor_approved_route_cabinet (вход с Instr1234 после approve → 200, route=cabinet). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN заявка с паролем P одобрена (users создан)
- WHEN сравниваются хэши и выполняется вход с паролем P
- THEN значение хэша в users СОВПАДАЕТ со значением в заявке; вход с паролем P по /api/auth/login успешен

## Предусловия
- Сервис собран через create_app() с роутерами instructors + admin + instructor_admin + auth; TestClient без сети; чистая БД в tmp, init_db.

## Шаги
1. POST /api/instructors/apply с базовым набором (P) → 200; зафиксировать password_hash заявки H1.
2. POST /api/admin/instructor-applications/{id}/approve с админ-токеном → 200.
3. Прочитать users.password_hash (H2) по email; сравнить H1 == H2.
4. POST /api/auth/login {"email": E, "password": P} → зафиксировать статус/тело.

## Ожидаемый результат
3. H2 == H1 (без повторного хэширования).
4. 200 {"ok": true, "token": <строка>, "route": "cabinet"} — пароль проверен против перенесенного хэша.

## Тестовые данные
Базовый валидный набор (TC-APP-005): instructor@example.com / Qwerty123. Админ: admin / admin-pass-2026.
