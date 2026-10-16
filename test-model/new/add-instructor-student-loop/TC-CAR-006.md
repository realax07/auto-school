# TC-CAR-006 — Фото автомобиля: недопустимый тип и превышение лимита

- ID кейса: TC-CAR-006
- ID чеклиста: CHK-19
- Источник: CHK-19 → Requirement «Фото автомобиля доступно владельцу» (instructor-cars) → FR-27, NFR-6, ОВ-5; Scenario «Недопустимый файл фото отклоняется»
- Тип: негативный + граничный
- Приоритет: Must
- Статус: ручной (не исполнялся; автоматизация — после утверждения кейсов, контракт 6; плановые TC-ID в docstring автотестов действуют до утверждения, rule 6)

## GIVEN / WHEN / THEN
- GIVEN автомобиль принадлежит инструктору А ({car_id})
- WHEN POST /api/instructor/cars/{car_id}/photo с PDF (A, подмена Content-Type на image/jpeg не помогает — magic bytes) или изображением 6 МБ (B); граница ровно 5 МБ (C)
- THEN A/B → 422 {ok:false}, фото не привязано; C → принимается

## Предусловия
- Сервис собран через create_app() (uvicorn, single-worker); допускается TestClient без сети (паттерн tests/conftest.py). Чистая БД (AUTOSCHOOL_DB_PATH в tmp), init_db при старте. Контроль живости: GET /api/health → 200 {"ok": true}.
- Сессии/данные фикстур: одобренные инструкторы А и Б (approved-заявка, Спринт 2; users.role='instructor'), ученик с валидной сессией (role='student'), X-Admin-Token администратора (Спринт 0). Сессии получены через /api/auth/login.
- Все запросы к API передают токены в заголовках X-Session-Token / X-Admin-Token (механика Спринтов 0–2).

## Шаги
1. POST photo file=document.pdf (Content-Type: image/jpeg) → код/ответ.
2. POST photo file=big.jpg (6 МБ) → код/ответ.
3. POST photo file=exact5mb.jpg (ровно 5 МБ) → код/ответ.
4. GET photo — что привязано?

## Ожидаемый результат
1. 422 {ok:false} (проверка magic bytes).
2. 422 {ok:false}.
3. 200 {ok:true}.
4. Привязан только файл из шага 3.

## Тестовые данные
Тестовые данные: см. Предусловия; учетные записи фикстур (admin-token, инструкторы, ученик).

## Трассировка

### Requirement: Фото автомобиля доступно владельцу
#### Scenario: Недопустимый файл фото отклоняется

