# TC-S5BE-001 — Миграции: таблица booking с индексами и колонки instructor_cars

- Автотест: `tests/test_s5_backend.py::test_s5_migration_booking_table_and_indexes`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Занятый слот недоступен другим ученикам (openspec/changes/add-booking-docs/specs/booking/spec.md) — гарантия на уровне хранилища (частичный UNIQUE uq_booking_active_slot)
  - Scenario: Параллельные запросы на один слот — максимум одна бронь (openspec/changes/add-booking-docs/specs/booking/spec.md)

## GIVEN / WHEN / THEN
- GIVEN чистая БД после init_db
- WHEN открыть схему sqlite (sqlite_master, PRAGMA table_info)
- THEN есть таблица booking (student_id, instructor_id, availability_id, lesson_date, status, reject_comment, created_at, decided_at), индексы idx_booking_instructor/idx_booking_student/uq_booking_active_slot; в instructor_cars — колонки 5 ракурсов, photo_sts, blocked

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
