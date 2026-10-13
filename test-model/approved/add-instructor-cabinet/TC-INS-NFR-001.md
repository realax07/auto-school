# TC-INS-NFR-001 — SQL в dashboard.py параметризован (NFR-2)

- ID кейса: TC-INS-NFR-001
- ID чеклиста: CHK-17
- Источник: CHK-17 → requirements-instructor-cabinet.md NFR-2 (трассировка чеклиста «Нефункциональные требования»); контроль sdd §20.1 п.2 (SELECT users по user_id с `?`-плейсхолдером)
- Тип: НФТ
- Приоритет: Must
- Статус: automated — tests/test_instructor_dashboard.py::test_dashboard_sql_parameterized (инспекция: 'WHERE id = ?' присутствует, конкатенации/f-строки SELECT отсутствуют) + тест-проба исполнения (успешный 200-запрос с реальным SELECT)

## GIVEN / WHEN / THEN
- GIVEN модуль backend/dashboard.py содержит единственный новый SQL-запрос
- WHEN выполняется инспекция исходного кода + тест-проба (успешный вызов GET /api/instructor/dashboard валидным инструктором)
- THEN единственный SELECT имеет форму … WHERE id = ? с `?`-плейсхолдером; конкатенаций SQL в модуле 0 (нет `id = ' +`, `id = " +`, f"SELECT, format(SELECT…); тест-проба проходит — запрос исполняется корректно

## Предусловия
- backend/dashboard.py присутствует; тестовое окружение собрано (create_app(), чистая БД).

## Шаги
1. Прочитать исходник backend/dashboard.py.
2. Инспекция: убедиться, что встречается `WHERE id = ?"`; убедиться в отсутствии each паттернов: `id = ' +`, `id = " +`, `f"SELECT`, `format(SELECT`.
3. Тест-проба: создать инструктора (apply → approve → login), выполнить GET /api/instructor/dashboard с валидным токеном.

## Ожидаемый результат
2. Единственный SELECT — с `?`-плейсхолдером; 0 конкатенаций SQL.
3. 200 с instructor.* — параметризованный запрос исполняется корректно (SQL-инъекция через параметры невозможна по построению).

## Тестовые данные
Инструктор: instr@example.com / Instr1234 (id подставляется параметром, не конкатенацией).
