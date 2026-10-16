# TC-REQ-008 — Принятие с выбором своего автомобиля создает связь

- ID кейса: TC-REQ-008
- ID чеклиста: CHK-55
- Источник: CHK-55 → Requirement «Принятие заявки с привязкой к автомобилю» (student-requests) → FR-39; Scenario «Принятие с выбором автомобиля создает связь»
- Тип: позитивный
- Приоритет: Must
- Статус: ручной (не исполнялся; автоматизация — после утверждения кейсов, контракт 6; плановые TC-ID в docstring автотестов действуют до утверждения, rule 6)

## GIVEN / WHEN / THEN
- GIVEN входящая заявка 'new' инструктору А; у А есть ≥1 автомобиль (car_id)
- WHEN А выполняет POST /api/instructor/requests/{id}/accept {car_id}
- THEN 200; заявка 'accepted', car_id проставлен; создана связь ученик↔инструктор↔автомобиль; ученик появляется в «Моих учениках» (GET /api/instructor/summary.students)

## Предусловия
- Сервис собран через create_app() (uvicorn, single-worker); допускается TestClient без сети (паттерн tests/conftest.py). Чистая БД (AUTOSCHOOL_DB_PATH в tmp), init_db при старте. Контроль живости: GET /api/health → 200 {"ok": true}.
- Сессии/данные фикстур: одобренные инструкторы А и Б (approved-заявка, Спринт 2; users.role='instructor'), ученик с валидной сессией (role='student'), X-Admin-Token администратора (Спринт 0). Сессии получены через /api/auth/login.
- Все запросы к API передают токены в заголовках X-Session-Token / X-Admin-Token (механика Спринтов 0–2).

## Шаги
1. Подготовить заявку 'new' и автомобиль А (TC-CAR-001).
2. POST accept {car_id} токеном А.
3. GET /api/student/requests учеником; GET /api/instructor/summary токеном А.
4. Проверить student_requests в БД (status, car_id).

## Ожидаемый результат
2. 200 {ok:true}.
3. Ученик видит «принята»; summary.students содержит ученика.
4. status='accepted', car_id = выбранный автомобиль.

## Тестовые данные
Тестовые данные: см. Предусловия; учетные записи фикстур (admin-token, инструкторы, ученик).

## Трассировка

### Requirement: Принятие заявки с привязкой к автомобилю
#### Scenario: Принятие с выбором автомобиля создает связь

