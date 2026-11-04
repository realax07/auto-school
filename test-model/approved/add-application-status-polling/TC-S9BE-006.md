# TC-S9BE-006 — Миграция idempotent на legacy-БД: колонки токенов, частичные UNIQUE, backfill НЕТ (FR-80, NFR-11…24)

- Автотест: `tests/test_s9_backend.py::test_tc_s9be_006_migration_idempotent_no_backfill`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-application-status-polling (Спринт 9)
- Трассировка:
  - Requirement: Автоопределение статуса заявки на экране ожидания
  - Scenario: Экран без сохраненного идентификатора — статичный режим без запросов

## GIVEN / WHEN / THEN
- GIVEN предсозданная legacy-БД (tmp_path + AUTOSCHOOL_DB_PATH): таблица instructor_applications в схеме Спринтов 2–8 — БЕЗ колонок токенов, 2 старые строки заявок
- WHEN db.init_db(); проверка PRAGMA table_info, sqlite_master по индексам uq_instructor_applications_%, SELECT старых строк; контрольная попытка двух INSERT с одним poll_token; ПОВТОРНЫЙ запуск init_db с повторной проверкой
- THEN колонки poll_token/exchange_token добавлены как TEXT; частичные UNIQUE-индексы на месте с «WHERE … IS NOT NULL» (uq_instructor_applications_poll_token, uq_instructor_applications_exchange_token); backfill НЕТ — старые строки остались (NULL, NULL): историческим заявкам токен некому выдать, их экран — статичный режим по построению; индексы РЕАЛЬНО уникальны — второй INSERT с тем же poll_token → IntegrityError; повторный init_db ничего не меняет: колонки не задвоены (count == 2), NULL по-прежнему на месте (idempotent)

## Примечание
- Партия change add-application-status-polling (Спринт 9, блок 2 — FR-80…FR-83 + NFR-28); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6).
- Фактический статус: backend реализован (задача 2.1 смержена в ветке);
  backend-матрица tests/test_s9_backend.py — 13 passed (лог ПМ). Полный
  регресс — в работе, светофор не присваивался.
