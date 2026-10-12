<!-- reviewer: code_reviewer (изолированная сессия) | дифф: adf1a23 (feature/s2-integration) | дата: 2026-10-12 -->

# Code review: задача 1.2 (change add-instructor-flow)

Файл: backend/db.py (расширение _SCHEMA + миграция users.role), тесты
tests/test_db.py (раздел «add-instructor-flow, задача 1.2»).
Provenance: HEAD `adf1a236bf9b7516d78b081d4da1853e3d481d1b`.

## Вердикт: approve

Reviewer-Delegation: deleg-cr-20261012-external

Схема instructor_applications — ровно состав design.md / sdd §16 (16 колонок,
email TEXT NOT NULL UNIQUE — вторая линия защиты apply, MAJ-1); миграция
users.role idempotent (PRAGMA table_info → условный ALTER), унаследованные
базы Спринтов 0–1 поднимаются без пересоздания, существующие записи остаются
учениками. UNIQUE users.email сохранен (таблица users в _SCHEMA не менялась).
Регрессионный набор — 169 passed.

## Таблица замечаний

| # | Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|---|
| 1 | minor | backend/db.py:52–57 | executescript(_SCHEMA) неявно коммитит открытую транзакцию перед выполнением; ALTER выполняется отдельным execute с явным commit — при падении процесса между executescript и ALTER схема уже частично применена. Для заявленной idempotent-миграции это безопасно (повторный init_db доводит до консистентного состояния: таблица создана, ALTER повторится), поэтому не major — рассинхрон невозможен по построению | Ничего не требуется для приема; при будущем расширении схемы — держать каждый шаг самодостаточным (текущий паттерн уже таков) |

Не является замечанием: WAL/row_factory/путь через AUTOSCHOOL_DB_PATH —
наследованная механика get_conn без изменений; проверка существования
колонки через PRAGMA — заявленный в sdd §16 способ; индексов сверх UNIQUE
контракт не требует.

## Проверено по чек-листу

| Проверка | Результат |
|---|---|
| Состав колонок instructor_applications = design.md (NFR-4) | OK: тест `test_s2_instructor_applications_table_schema` сверяет полный список, включая DEFAULT-политики |
| email UNIQUE — вторая линия (MAJ-1) | OK: UNIQUE в схеме; поведение проверено на уровне задачи 1.1 (повторный INSERT → контрактная 422), тест схемы 1.2 проверяет структуру |
| Миграция legacy-базы без пересоздания | OK: `test_s2_users_role_migration_on_legacy_db` — база users без role, init_db добавляет колонку, существующая запись role='student', данные целы |
| Idempotent повторного init_db | OK: `test_s2_role_migration_idempotent` — колонка role одна |
| Дефолт учеников | OK: пустая база → новая запись без role получает 'student' (`test_s2_users_role_column_added_on_empty_db`) |
| UNIQUE users.email сохранен | OK: users-часть _SCHEMA дословна со Спринта 0, регресс-тесты register (дубль email → 422) зеленые |

## Проверенные Scenario (готовность 1.2 + спека)

- init_db на пустой базе: обе таблицы + users.role.
- init_db на унаследованной базе: ALTER без пересоздания, записи остаются
  учениками.
- Повторный init_db — без ошибок и дублей колонок.
- Список таблиц — ровно users + instructor_applications.

## Что НЕ проверено (честно)

- Миграция на реальном производственном файле data/app.db (тесты на
  tmp_path-фикстурах); механика идентична, файл прод-базы в репо не входит.
