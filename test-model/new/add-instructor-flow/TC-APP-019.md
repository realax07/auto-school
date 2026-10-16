# TC-APP-019 — В заявке bcrypt-хэш cost ≥ 12; при approve хэш переносится без повторного хэширования

- ID кейса: TC-APP-019
- ID чеклиста: CHK-19
- Источник: CHK-19 → Requirement «Хранение пароля заявки только в виде bcrypt-хэша» (домен instructor-application) → FR-11.1; Scenario «В заявке хранится только хэш» + «Одобренная заявка переносит хэш без повторного хэширования»
- Тип: позитивный
- Приоритет: Must
- Статус: automated — tests/test_instructors_apply.py::test_apply_success_creates_waiting_application_with_hash (префикс $2b$12$, bcrypt.checkpw(P, hash)=true) + tests/test_instructor_admin.py::test_approve_creates_user_with_instructor_role_and_same_hash (users.password_hash == заявочный хэш — перенос без повторного хэширования). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN анкета отправлена с паролем P
- WHEN инспектируется запись заявки, затем заявка одобряется и инспектируется запись users
- THEN password_hash заявки — bcrypt-хэш (префикс $2b$/$2a$, cost ≥ 12, тот же механизм, что register.py), bcrypt.checkpw(P, hash)=true; после approve значение хэша в users СОВПАДАЕТ со значением в заявке (без повторного хэширования)

## Предусловия
- Сервис собран через create_app() с роутерами instructors + admin + instructor_admin; TestClient без сети; чистая БД в tmp, init_db; env админа (ADMIN_USER, ADMIN_PASSWORD_HASH, SECRET).

## Шаги
1. POST /api/instructors/apply с базовым набором (P = «Qwerty123») → 200.
2. Прочитать instructor_applications.password_hash по email.
3. Проверить: префикс $2b$12$ (или $2a$, cost ≥ 12); bcrypt.checkpw(b"Qwerty123", hash) = true.
4. POST /api/admin/instructor-applications/{id}/approve с X-Admin-Token → 200.
5. Прочитать users.password_hash того же email; сравнить со значением из шага 2.

## Ожидаемый результат
2–3. Хэш начинается с «$2b$12$»; checkpw = true.
4. 200 {"ok": true, "user_id": <int>}.
5. users.password_hash == заявочный hash (строгое равенство — повторного хэширования не было).

## Тестовые данные
Базовый валидный набор (TC-APP-005): instructor@example.com / Qwerty123. Админ: admin / admin-pass-2026 (POST /api/admin/login).

## Трассировка

### Requirement: Хранение пароля заявки только в виде bcrypt-хэша
#### Scenario: В заявке хранится только хэш
#### Scenario: Одобренная заявка переносит хэш без повторного хэширования

