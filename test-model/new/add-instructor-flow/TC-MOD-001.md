# TC-MOD-001 — GET-список заявок: все статусы, данные анкеты, сортировка

- ID кейса: TC-MOD-001
- ID чеклиста: CHK-22
- Источник: CHK-22 → Requirement «Раздел заявок инструкторов в админке» (домен admin-moderation) → FR-14; Scenario «Администратор видит все заявки»; sdd §15.2
- Тип: позитивный
- Приоритет: Must
- Статус: automated — tests/test_instructor_admin.py::test_list_sorted_created_desc_id_desc (сортировка created_at DESC, id DESC) + ::test_list_without_hash_key (состав полей ответа §15.2); статусы waiting/approved/deny в одном списке — toBeAutomated расширением test_list_sorted (прямые UPDATE статусов). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN администратор вошел (валидный X-Admin-Token) и в системе есть заявки со статусами waiting, approved и deny
- WHEN GET /api/admin/instructor-applications
- THEN 200; ответ содержит ВСЕ заявки (все три статуса) с полными данными анкеты; сортировка created_at DESC, id DESC

## Предусловия
- Сервис собран через create_app() с роутерами instructors + admin + instructor_admin; TestClient без сети; чистая БД в tmp, init_db.
- Токен получен через POST /api/admin/login (admin / admin-pass-2026).
- Три заявки созданы публичным POST /api/instructors/apply (email a@example.com, b@example.com, c@example.com); статусы b → approved, c → deny — прямым UPDATE (детерминизм).

## Шаги
1. Создать три заявки; сменить статусы на approved и deny прямым UPDATE.
2. GET /api/admin/instructor-applications с X-Admin-Token.
3. Зафиксировать count, список id и статусов.
4. Проверить состав полей каждого элемента.

## Ожидаемый результат
2. 200 {"count": 3, "applications": [...]}.
3. Присутствуют все 3 заявки со статусами waiting/approved/deny; порядок id — по убыванию (последняя созданная первой).
4. Каждый элемент содержит: id, surname, name, patronymic, email, phone, address, work_format, plate, license_number, license_date, license_category, experience, status, review_comment, created_at.

## Тестовые данные
Заявки: базовый валидный набор (TC-APP-005) с email a@example.com (waiting), b@example.com (approved), c@example.com (deny). Админ: admin / admin-pass-2026.

## Трассировка

### Requirement: Раздел заявок инструкторов в админке
#### Scenario: Администратор видит все заявки

