# TC-S8BE-009 — «Мои ученики» (API): состав пар, счетчики только confirmed, доступ (ОВ-5)

- Автотест: `tests/test_s8_backend.py::test_s8_my_students_list_counters_and_access`
- Приоритет: Must (FR-75, NFR-22)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-s8-cars-docs-booking (Спринт 8)
- Трассировка:
  - Requirement: Раздел «Мои ученики» со счетчиками занятий (openspec/changes/add-s8-cars-docs-booking/specs/student-requests/spec.md)
  - Scenario: Карточка ученика с занятями показывает счетчики (openspec/changes/add-s8-cars-docs-booking/specs/student-requests/spec.md)
  - Scenario: Пара без броней — корректное пустое состояние (openspec/changes/add-s8-cars-docs-booking/specs/student-requests/spec.md)
  - Scenario: Запросы не входят в счетчики (только confirmed) — ОВ-5 (openspec/changes/add-s8-cars-docs-booking/specs/student-requests/spec.md)
  - Scenario: Раздел доступен только владельцу (openspec/changes/add-s8-cars-docs-booking/specs/student-requests/spec.md)

## GIVEN / WHEN / THEN
- GIVEN два инструктора (A и B) и три ученика; принятые пары: A—s1, A—s2, B—s3 (accept с авто, контур Спринта 3); у s1 брони: завтра (слот 09:00), +7 и +8 дней, вчера/-2/-3 дня — все confirmed; плюс rejected-бронь в прошлом и new-запрос s2 на послезавтра (confirm=False); lesson_date задается явно (материализация MIN-1 — локальная дата сервера)
- WHEN GET /api/instructor/students у A и у B; GET без сессии (гость), с bogus-токеном, с сессией ученика
- THEN у A: students = [s1, s2] — только принятые пары ЭТОГО инструктора, s3 отсутствует; карточка s1: full_name с ФИО ученика, next_lesson {date: завтра, time: 09:00, end_time: 23:00}, planned_count = 2, completed_count = 3; карточка s2 (пара без confirmed-броней): next_lesson = None, planned_count = 0, completed_count = 0 — new-запрос и rejected в «следующее»/счетчики не входят (ОВ-5); у B: только [s3] — чужие пары не выдаются; гость и bogus-токен → 401, ученик → 403

## Примечание
- Партия change add-s8-cars-docs-booking (Спринт 8); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); полный прогон
  359 passed (integration, лог ПМ).
