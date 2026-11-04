# TC-PD-017 — Повторный init_db idempotent: ничего не меняет

- Автотест: `tests/test_policy.py::test_s9_migration_repeated_init_db_is_idempotent`
- Приоритет: Must (FR-79, NFR-27)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-personal-data-policy (Спринт 9)
- Трассировка:
  - Requirement: Фиксация согласия в данных заявки и регистрации
  - Scenario: Записи до введения фиксации не переписываются

## GIVEN / WHEN / THEN
- GIVEN БД после первой миграции с легаси-строкой (NULL фиксации)
- WHEN db.init_db() выполняется второй раз
- THEN схема и данные идентичны состоянию до повторного запуска (строки и набор колонок равны, COUNT=1) — миграция idempotent на существующем volume

## Примечание
- Партия change add-personal-data-policy (Спринт 9, задача 7.1); кейсы
  живут трассировкой TC-ID в docstring автотеста (rule 6); заголовки
  Requirement/Scenario — дословно specs/PersonalData/spec.md.
