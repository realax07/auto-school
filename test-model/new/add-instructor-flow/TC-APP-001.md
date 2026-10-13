# TC-APP-001 — Лендинг инструкторов по прямой ссылке без авторизации

- ID кейса: TC-APP-001
- ID чеклиста: CHK-1
- Источник: CHK-1 → Requirement «Лендинг инструкторов по прямой ссылке» (домен instructor-application) → FR-10; Scenario «Прямой переход по ссылке»
- Тип: позитивный
- Приоритет: Must
- Статус: automated — tests/test_auth_route.py::test_new_static_routes_served (маршрут /instructors → 200, text/html) + tests/test_instructor_pages.py::test_instructors_landing_texts_verbatim (тексты и CSS дословно vs design/mocks/landing-instructors.html). Плановые ID в docstring автотестов (TC-FR13-…, TC-CAB-…) действуют до утверждения кейсов (rule 6)

## GIVEN / WHEN / THEN
- GIVEN сервис запущен; пользователь НЕ авторизован (нет сессионного токена)
- WHEN выполняется GET /instructors по прямой ссылке без заголовков авторизации
- THEN 200, content-type text/html; отдана страница frontend/instructors.html, соответствующая макету landing-instructors.html: тексты (title, hero, форматы, возможности, нижний CTA, футер) и CSS-строки мокапа перенесены дословно; допустимые отличия — только wiring (CTA → /instructors/apply), модалка сбора контактов мокапа не используется

## Предусловия
- Сервис собран через create_app() (uvicorn, single-worker); допускается TestClient без сети (паттерн tests/conftest.py).
- Чистая БД (AUTOSCHOOL_DB_PATH в tmp), init_db при старте.
- Контроль живости: GET /api/health → 200 {"ok": true}.

## Шаги
1. GET http://127.0.0.1:8000/instructors (без cookie/token-заголовков).
2. Зафиксировать статус-код и content-type.
3. Сверить текст и CSS страницы с design/mocks/landing-instructors.html: каждый текстовый фрагмент мокапа присутствует дословно; каждая непустая строка CSS-блока мокапа присутствует в странице.
4. Убедиться, что модалка мокапа (id="lead-form"/id="modal") в странице отсутствует.

## Ожидаемый результат
1–2. 200, text/html.
3. Все фрагменты мокапа найдены дословно; ни один фрагмент не отсутствует и не изменен.
4. Модалки нет — единственное допустимое удаление относительно мокапа.

## Тестовые данные
Тестовые данные не требуются (анонимный GET).
