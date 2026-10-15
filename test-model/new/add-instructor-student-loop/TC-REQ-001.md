# TC-REQ-001 — Подача заявки: появляется у инструктора со статусом «новая»

- ID кейса: TC-REQ-001
- ID чеклиста: CHK-45
- Источник: CHK-45 → Requirement «Подача заявки инструктору» (student-requests) → FR-36; Scenario «Заявка появляется у инструктора со статусом «новая»»
- Тип: позитивный
- Приоритет: Must
- Статус: ручной (не исполнялся; автоматизация — после утверждения кейсов, контракт 6; плановые TC-ID в docstring автотестов действуют до утверждения, rule 6)

## GIVEN / WHEN / THEN
- GIVEN ученик открыл карточку одобренного инструктора А
- WHEN POST /api/student/requests {instructor_id:A}
- THEN заявка создана со статусом 'new' и появляется у А в GET /api/instructor/requests

## Предусловия
- Сервис собран через create_app() (uvicorn, single-worker); допускается TestClient без сети (паттерн tests/conftest.py). Чистая БД (AUTOSCHOOL_DB_PATH в tmp), init_db при старте. Контроль живости: GET /api/health → 200 {"ok": true}.
- Сессии/данные фикстур: одобренные инструкторы А и Б (approved-заявка, Спринт 2; users.role='instructor'), ученик с валидной сессией (role='student'), X-Admin-Token администратора (Спринт 0). Сессии получены через /api/auth/login.
- Все запросы к API передают токены в заголовках X-Session-Token / X-Admin-Token (механика Спринтов 0–2).

## Шаги
1. POST /api/student/requests {instructor_id:A} с X-Session-Token ученика.
2. GET /api/student/requests учеником.
3. GET /api/instructor/requests инструктором А.

## Ожидаемый результат
1. 200 {ok:true, id}, статус 'new'.
2. В списке заявок ученика — заявка к А со статусом «новая».
3. У А заявка видна: ученик (ФИО, стаж), дата, статус 'new'.

## Тестовые данные
Тестовые данные: см. Предусловия; учетные записи фикстур (admin-token, инструкторы, ученик).
