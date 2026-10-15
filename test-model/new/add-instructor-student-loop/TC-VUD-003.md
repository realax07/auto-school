# TC-VUD-003 — Изображение ВУ выдается админу с валидным токеном

- ID кейса: TC-VUD-003
- ID чеклиста: CHK-5
- Источник: CHK-5 → Requirement «Выдача изображения ВУ только по админ-токену» (instructor-documents) → FR-24; Scenario «Админ с валидным токеном получает изображение»
- Тип: позитивный
- Приоритет: Must
- Статус: ручной (не исполнялся; автоматизация — после утверждения кейсов, контракт 6; плановые TC-ID в docstring автотестов действуют до утверждения, rule 6)

## GIVEN / WHEN / THEN
- GIVEN существует заявка с загруженным ВУ (см. TC-VUD-001); валидный админ-токен (механизм Спринта 0)
- WHEN выполняется GET /api/admin/instructor-applications/{id}/license-image с заголовком X-Admin-Token
- THEN 200, тело — изображение (Content-Type image/jpeg или image/png), байты совпадают с сохраненным файлом

## Предусловия
- Сервис собран через create_app() (uvicorn, single-worker); допускается TestClient без сети (паттерн tests/conftest.py). Чистая БД (AUTOSCHOOL_DB_PATH в tmp), init_db при старте. Контроль живости: GET /api/health → 200 {"ok": true}.
- Сессии/данные фикстур: одобренные инструкторы А и Б (approved-заявка, Спринт 2; users.role='instructor'), ученик с валидной сессией (role='student'), X-Admin-Token администратора (Спринт 0). Сессии получены через /api/auth/login.
- Все запросы к API передают токены в заголовках X-Session-Token / X-Admin-Token (механика Спринтов 0–2).

## Шаги
1. Создать заявку с ВУ (шаги TC-VUD-001), получить {id}.
2. GET /api/admin/instructor-applications/{id}/license-image с X-Admin-Token.
3. Зафиксировать статус, Content-Type, первые байты тела (magic bytes).

## Ожидаемый результат
2. 200, Content-Type image/jpeg или image/png.
3. Тело начинается с magic bytes JPEG (FF D8) или PNG (89 50 4E 47); содержимое идентично сохраненному файлу.

## Тестовые данные
Тестовые данные: см. Предусловия; учетные записи фикстур (admin-token, инструкторы, ученик).
