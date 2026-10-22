# TC-S5BE-002 — Повторный init_db идемпотентен, данные целы

- Автотест: `tests/test_s5_backend.py::test_s5_migration_idempotent_keeps_rows`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Занятый слот недоступен другим ученикам (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Параллельные запросы на один слот — максимум одна бронь (openspec/changes/add-booking-docs/specs/booking/spec.md) — уровень хранилища сохраняется при повторной миграции

## GIVEN / WHEN / THEN
- GIVEN инструктор с графиком, вручную вставлена бронь status='new'
- WHEN дважды выполняется init_db()
- THEN колонки/таблицы/индексы не дублируются, запись booking и авто сохранены

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
