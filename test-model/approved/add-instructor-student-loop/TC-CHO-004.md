# TC-CHO-004 — Фильтр по свободному времени (пересечение с availability)

- ID кейса: TC-CHO-004
- ID чеклиста: CHK-35
- Источник: CHK-35 → Requirement «Фильтры каталога» (student-instructor-choice) → FR-32; Scenario «Фильтр по свободному времени»
- Тип: позитивный
- Приоритет: Must
- Статус: ручной (не исполнялся; автоматизация — после утверждения кейсов, контракт 6; плановые TC-ID в docstring автотестов действуют до утверждения, rule 6)

## GIVEN / WHEN / THEN
- GIVEN инструктор А с availability Пн 09:00–13:00; инструктор Б с availability Пн 14:00–18:00
- WHEN ученик запрашивает GET /api/student/instructors?free_weekday=0&free_from=10:00&free_to=12:00
- THEN только А (интервал 09:00–13:00 пересекается с 10:00–12:00); Б отсечен

## Предусловия
- Сервис собран через create_app() (uvicorn, single-worker); допускается TestClient без сети (паттерн tests/conftest.py). Чистая БД (AUTOSCHOOL_DB_PATH в tmp), init_db при старте. Контроль живости: GET /api/health → 200 {"ok": true}.
- Сессии/данные фикстур: одобренные инструкторы А и Б (approved-заявка, Спринт 2; users.role='instructor'), ученик с валидной сессией (role='student'), X-Admin-Token администратора (Спринт 0). Сессии получены через /api/auth/login.
- Все запросы к API передают токены в заголовках X-Session-Token / X-Admin-Token (механика Спринтов 0–2).

## Шаги
1. PUT availability А: Пн 09:00–13:00; Б: Пн 14:00–18:00.
2. GET с free_weekday=0, free_from=10:00, free_to=12:00.

## Ожидаемый результат
2. 200; в списке только А.

## Тестовые данные
Тестовые данные: см. Предусловия; учетные записи фикстур (admin-token, инструкторы, ученик).
