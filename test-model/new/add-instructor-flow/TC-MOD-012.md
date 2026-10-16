# TC-MOD-012 — Роль одобренного инструктора отличима от роли ученика

- ID кейса: TC-MOD-012
- ID чеклиста: CHK-33
- Источник: CHK-33 → Requirement «Созданный пользователь получает роль инструктора» (домен admin-moderation) → FR-16; Scenario «Роль одобренного инструктора отличима от роли ученика»; миграция role='student' у существующих записей (sdd §16)
- Тип: позитивный
- Приоритет: Must
- Статус: automated — tests/test_instructor_admin.py::test_approve_creates_user_with_instructor_role_and_same_hash (role='instructor') + tests/test_db.py::test_s2_users_role_column_added_on_empty_db, ::test_s2_users_role_migration_on_legacy_db (дефолт student, миграция) + test_auth_route.py::test_login_student_route_student_cabinet (ученик — student). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN одобрена заявка с email E И существует ученик, зарегистрированный через /api/register (Спринт 0)
- WHEN сравниваются записи users обоих
- THEN запись инструктора помечена role='instructor', запись ученика — role='student' (дефолт миграции для существующих записей); записи различимы по role

## Предусловия
- Сервис собран через create_app() с роутерами instructors + admin + instructor_admin; TestClient без сети; чистая БД в tmp, init_db.

## Шаги
1. POST /api/register — ученик petrova@example.com → 200.
2. Создать заявку instructor@example.com публичным apply; approve через админ-API → 200.
3. SELECT role из users для обоих email.

## Ожидаемый результат
3. users[petrova@example.com].role = 'student'; users[instructor@example.com].role = 'instructor' — роли различимы.

## Тестовые данные
Ученик — базовый набор регистрации (TC-AUTH-001): petrova@example.com / Qwerty123. Заявка — базовый валидный набор (TC-APP-005): instructor@example.com. Админ: admin / admin-pass-2026.

## Трассировка

### Requirement: Созданный пользователь получает роль инструктора
#### Scenario: Роль одобренного инструктора отличима от роли ученика

