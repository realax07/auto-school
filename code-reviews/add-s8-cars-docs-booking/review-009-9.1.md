<!-- reviewer: code_reviewer (изолированная сессия) | дифф: 1d40a46..HEAD, обе волны проверены на наличие реализации | дата: 2026-11-02 -->

# Code review: задача 9.1 (change add-s8-cars-docs-booking)

Проверен дифф `1d40a46..HEAD` на предмет реализации GET
/api/instructor/students (tasks.md 9.1, FR-75, ОВ-5). Backend-волна b473703
меняла только db.py, instructor_cars.py, instructor_documents.py (плюс
тесты); backend/student_requests.py в диффе отсутствует. Поиск по кодовой
базе: единственный маршрут /api/instructor/students — PATCH
…/students/{student_id}/car (Спринт 3, student_requests.py:335); GET-эндпоинта
с карточками принятых учеников нет нигде (grep по backend/*.py). Счетчики
(next_lesson по confirmed с lesson_date ≥ сегодня, planned_count,
completed_count — только confirmed, ОВ-5), чтение поверх
booking/student_requests, проверка «только свои пары» (NFR-22) — не
реализованы; тестов на сценарий дельты (1 завтра / 2 на неделе / 3 в
прошлом) в диффе нет. Задача целиком не выполнена.

## Вердикт: return

Reviewer-Delegation: deleg-cr-20261102-094136-external

## Замечания

| # | Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|---|
| 1 | blocker | backend/student_requests.py (файл не входит в дифф) | GET /api/instructor/students не реализован: ни эндпоинта, ни вычисления next_lesson/planned_count/completed_count, ни проверки «только свои пары». Контракт design.md блок A (строка GET /api/instructor/students) не покрыт | Реализовать по contracts design.md блок A: пары student_requests.status='accepted', next_lesson — ближайшая confirmed бронь с lesson_date ≥ сегодня (ЛОКАЛЬНАЯ дата сервера, правило MIN-1) / null; planned_count — confirmed после следующей; completed_count — confirmed с датой < сегодня; ТОЛЬКО confirmed (ОВ-5); владелец вычисляется серверно, чужие пары не выдаются (404-неразличение); параметризованный SQL (NFR-10) |
| 2 | major | tests/test_s8_backend.py (дифф) | Критерии готовности 9.1 не покрыты тестами: сценарий дельты (1 завтра, 2 на следующей неделе, 3 в прошлом → «завтра», 2, 3), «без броней → нет/0/0», «запрос (new) не входит в счетчики», «чужие пары не выдаются» — тестов нет | Добавить тесты по критериям готовности вместе с реализацией; таймзону клиента не использовать (локальная дата сервера) |

Примечание: невыполнение 9.1 блокирует и фронтовую 9.2 (см. review-010);
«Мои ученики» в текущем UI — демо-заглушка (navTo показывает тост
«демо-данные»), без вызова API.
