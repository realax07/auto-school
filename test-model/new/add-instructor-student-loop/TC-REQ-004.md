# TC-REQ-004 — Заявка неодобренному/несуществующему инструктору отклоняется

- ID кейса: TC-REQ-004
- ID чеклиста: CHK-49
- Источник: CHK-49 → Requirement «Подача заявки инструктору» (student-requests) → FR-36; Scenario «Заявка неодобренному инструктору отклоняется»
- Тип: негативный
- Приоритет: Must
- Статус: ручной (не исполнялся; автоматизация — после утверждения кейсов, контракт 6; плановые TC-ID в docstring автотестов действуют до утверждения, rule 6)

## GIVEN / WHEN / THEN
- GIVEN инструктор В с заявкой в статусе waiting, инструктор Г с deny; несуществующий instructor_id
- WHEN POST /api/student/requests на каждого
- THEN каждый вариант → 404 {ok:false}, заявка не создается

## Предусловия
- Сервис собран через create_app() (uvicorn, single-worker); допускается TestClient без сети (паттерн tests/conftest.py). Чистая БД (AUTOSCHOOL_DB_PATH в tmp), init_db при старте. Контроль живости: GET /api/health → 200 {"ok": true}.
- Сессии/данные фикстур: одобренные инструкторы А и Б (approved-заявка, Спринт 2; users.role='instructor'), ученик с валидной сессией (role='student'), X-Admin-Token администратора (Спринт 0). Сессии получены через /api/auth/login.
- Все запросы к API передают токены в заголовках X-Session-Token / X-Admin-Token (механика Спринтов 0–2).

## Шаги
1. POST requests {instructor_id:В(waiting)} → код.
2. POST requests {instructor_id:Г(deny)} → код.
3. POST requests {instructor_id:999999} → код.
4. Проверить student_requests ученика.

## Ожидаемый результат
1–3. Каждый → 404 {ok:false}.
4. Новых записей нет.

## Тестовые данные
Тестовые данные: см. Предусловия; учетные записи фикстур (admin-token, инструкторы, ученик).

## Трассировка

### Requirement: Подача заявки инструктору
#### Scenario: Заявка неодобренному инструктору отклоняется

