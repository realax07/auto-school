# TC-NFR-003 — NFR-4: схема instructor_applications, миграция idempotent, наследие

- ID кейса: TC-NFR-003
- ID чеклиста: CHK-52
- Источник: CHK-52 → NFR-4; sdd §16 (состав таблицы, email TEXT NOT NULL UNIQUE, миграция idempotent); сигнал review-001-1.2 #1 (executescript неявно коммитит — доводка повторным init_db)
- Тип: НФТ
- Приоритет: Must
- Статус: automated — tests/test_db.py::test_s2_instructor_applications_table_schema (ровно колонки §16) + ::test_s2_instructor_applications_email_unique (UNIQUE на уровне БД) + ::test_s2_users_role_migration_on_legacy_db + ::test_s2_role_migration_idempotent + ::test_s2_users_email_unique_preserved + ::test_s2_instructor_applications_defaults (дефолты статуса/created_at). До утверждения кейсов (rule 6)

## GIVEN / WHEN / THEN
- GIVEN унаследованная база Спринтов 0–1 (users без role, с существующей записью ученика)
- WHEN выполняется init_db (миграция) и инспектируется схема
- THEN таблица instructor_applications хранит полный состав полей анкеты + статус (waiting/approved/deny) + review_comment + created_at; email TEXT NOT NULL UNIQUE; миграция idempotent — база поднимается без пересоздания, существующие ученики остаются role='student', UNIQUE users.email сохранен

## Предусловия
- AUTOSCHOOL_DB_PATH в tmp; для legacy-прогона — БД, созданная схемой Спринтов 0–1 (users без role + запись ученика), без instructor_applications.

## Шаги
1. init_db на пустой базе; PRAGMA table_info(instructor_applications) — сверить состав колонок: id, surname, name, patronymic, email, phone, address, work_format, plate, license_number, license_date, license_category, experience, password_hash, status, review_comment, created_at.
2. Двойной INSERT одной записи (тот же email) → второй падает sqlite3.IntegrityError (UNIQUE на уровне БД).
3. init_db на legacy-базе → users получил колонку role; запись legacy@example.com сохранилась с role='student'; таблица не пересоздавалась (данные целы).
4. Повторный init_db (×2) → без ошибок, без дублей колонок.
5. INSERT в users без role → дефолт student; попытка дубликата users.email → IntegrityError (UNIQUE сохранен).

## Ожидаемый результат
1. Состав колонок точно по §16 (лишних/недостающих нет).
2. IntegrityError на втором INSERT.
3. Миграция аддитивна: роль добавлена, ученик остался student, данные целы.
4. init_db идемпотентен (idempotent-доводка повторным вызовом — review-001-1.2 #1).
5. Дефолт student; UNIQUE users.email сохранен.

## Тестовые данные
Legacy-запись: (Иванов, Иван, Иванович, legacy@example.com, телефон, password_hash-заглушка). Проба UNIQUE: dup@example.com.
