# TC-REV-004 — Некорректная оценка/текст отзыва отклоняются

- ID кейса: TC-REV-004
- ID чеклиста: CHK-42
- Источник: CHK-42 → Requirement «Отзыв только реальным учеником» (reviews) → FR-34, NFR-5; Scenario «Некорректная оценка отклоняется»
- Тип: негативный
- Приоритет: Must
- Статус: ручной (не исполнялся; автоматизация — после утверждения кейсов, контракт 6; плановые TC-ID в docstring автотестов действуют до утверждения, rule 6)

## GIVEN / WHEN / THEN
- GIVEN ученик с принятой заявкой заполняет форму отзыва
- WHEN POST reviews с rating=0 (A), rating=6 (B), пустым text (C), text > 1000 символов (D), дробным rating (E)
- THEN каждый вариант → 422 {ok:false} (rating int 1..5, text непустой ≤1000), отзыв не создается

## Предусловия
- Сервис собран через create_app() (uvicorn, single-worker); допускается TestClient без сети (паттерн tests/conftest.py). Чистая БД (AUTOSCHOOL_DB_PATH в tmp), init_db при старте. Контроль живости: GET /api/health → 200 {"ok": true}.
- Сессии/данные фикстур: одобренные инструкторы А и Б (approved-заявка, Спринт 2; users.role='instructor'), ученик с валидной сессией (role='student'), X-Admin-Token администратора (Спринт 0). Сессии получены через /api/auth/login.
- Все запросы к API передают токены в заголовках X-Session-Token / X-Admin-Token (механика Спринтов 0–2).

## Шаги
1. Подготовка связи: ученик подал заявку одобренному инструктору А (POST /api/student/requests), А принял с автомобилем (POST .../accept {car_id}) — см. TC-REQ-008.
2. POST reviews {rating:0, text:"..."} → код.
3. POST reviews {rating:6, text:"..."} → код.
4. POST reviews {rating:5, text:""} → код.
5. POST reviews {rating:5, text:"x"*1001} → код.
6. POST reviews {rating:4.5, text:"..."} → код.
7. GET /api/student/instructors/{A} — агрегат.

## Ожидаемый результат
2–6. Каждый POST → 422 {ok:false}.
7. Агрегат не изменился (отзывов нет).

## Тестовые данные
Тестовые данные: см. Предусловия; учетные записи фикстур (admin-token, инструкторы, ученик).
