# TC-NFR-001 — NFR-2: SQL параметризован; SQL-инъекция в apply/login не срабатывает

- ID кейса: TC-NFR-001
- ID чеклиста: CHK-50
- Источник: CHK-50 → NFR-2 (сквозное); sdd §17 (все новые запросы §15.1–15.4, §15.5 — ?-плейсхолдеры через db-слой)
- Тип: НФТ
- Приоритет: Must
- Статус: automated (динамическая проба) — tests/test_instructors_apply.py::test_apply_validation_contract_422 (email с метасимволами обрабатывается валидатором как «неверный формат» → 422) + единая проверка login test_auth_route.py::test_login_unknown_credentials_unified_401; инспекция исходников (только ?-плейсхолдеры, 0 конкатенаций в INSERT заявки, SELECT заявок, UPDATE статусов, INSERT users при approve) — manual/toBeAutomated (статическая инспекция backend/instructors.py, backend/instructor_admin.py, ветки auth.py)

## GIVEN / WHEN / THEN
- GIVEN сервис собран; новые модули (instructors.py, instructor_admin.py, новые ветки auth.py)
- WHEN (1) инспектируется SQL-код; (2) в поля email apply и login подставляется `' OR 1=1 --`
- THEN (1) только ?-плейсхолдеры через db-слой, 0 конкатенаций строк SQL; (2) инъекция обрабатывается как литерал: apply → 422 («Email: неверный формат» — литерал не проходит валидацию формата), login → 401 единое сообщение; обход авторизации невозможен, заявок/сессий не создается

## Предусловия
- Сервис собран через create_app(); TestClient без сети; чистая БД в tmp; состояние анти-брутфорса чистое.

## Шаги
1. Инспекция backend/instructors.py, backend/instructor_admin.py: каждый SQL (INSERT заявки, SELECT заявок, UPDATE статусов, INSERT users при approve) — с ?-плейсхолдерами, параметры кортежем; конкатенации/f-строки SQL отсутствуют.
2. POST /api/instructors/apply с email `' OR 1=1 --` (остальное — валидный набор).
3. POST /api/auth/login {"email": "' OR 1=1 --", "password": "x"}.
4. После проб: SELECT COUNT(*) FROM instructor_applications; попытка GET защищенных ресурсов.

## Ожидаемый результат
1. 0 конкатенаций; все запросы параметризованы.
2. 422 {"ok": false, "error": "Email: неверный формат"} (литерал); заявка НЕ создана.
3. 401 {"ok": false, "error": "Неверный email или пароль"} — обхода нет.
4. COUNT = 0; авторизация не обходится.

## Тестовые данные
Инъекция: `' OR 1=1 --`. Остальные поля apply — базовый валидный набор (TC-APP-005).
