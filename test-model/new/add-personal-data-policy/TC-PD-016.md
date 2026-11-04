# TC-PD-016 — Миграция 4 колонок: легаси-записи остаются с NULL фиксации (без seed/backfill)

- Автотест: `tests/test_policy.py::test_s9_migration_adds_consent_columns_legacy_null`
- Приоритет: Must (FR-79, NFR-27)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-personal-data-policy (Спринт 9)
- Трассировка:
  - Requirement: Фиксация согласия в данных заявки и регистрации
  - Scenario: Записи до введения фиксации не переписываются

## GIVEN / WHEN / THEN
- GIVEN предсозданная БД со старой схемой (без consent-колонок) и легаси-строкой в users и instructor_applications
- WHEN выполняется db.init_db() (миграция через _COLUMN_MIGRATIONS)
- THEN 4 колонки добавлены (users и instructor_applications × consent_at, consent_policy_version); легаси-строки остаются (NULL, NULL); при последующих регистрация/заявках обе колонки непустые (см. TC-PD-008/012)

## Примечание
- Партия change add-personal-data-policy (Спринт 9, задача 7.1); кейсы
  живут трассировкой TC-ID в docstring автотеста (rule 6); заголовки
  Requirement/Scenario — дословно specs/PersonalData/spec.md.
