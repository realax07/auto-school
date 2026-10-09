# TC-CAB-001 — Открытие кабинета с действующим токеном

- ID кейса: TC-CAB-001
- ID чеклиста: CHK-18
- Источник: CHK-18 → Requirement «Доступ к кабинету по сессионному токену» (домен cabinet) → FR-7; Scenario «Переход в кабинет после входа»
- Тип: позитивный
- Приоритет: Must
- Статус: manual/toBeAutomated (браузерный сценарий: исполнение JS, sessionStorage; сигнал риска review-001-2.1 #3 — выполнять в браузере, не строковыми тестами; серверная часть косвенно автоматизирована — tests/test_integration_sprint1.py::test_cabinet_page_served)

## GIVEN / WHEN / THEN
- GIVEN ученик успешно вошел и получил действующий сессионный токен (sessionStorage.session_token)
- WHEN он открывает /cabinet (GET /cabinet; страница выполняет GET /api/auth/me с заголовком X-Session-Token)
- THEN кабинет открывается: GET /cabinet → 200 (HTML кабинета); GET /api/auth/me с токеном → 200 {"ok": true, "user": {...}}; содержимое кабинета отрисовано с данными пользователя

## Предусловия
- Сервис собран через create_app() (маршрут /cabinet примонтирован, задача 3.1); /api/health → 200.
- Браузер/Playwright для фронт-части (sessionStorage, fetch исполняются реально).

## Шаги
1. Через UI: открыть /, в модалке m-login ввести email/пароль базового пользователя, сабмит.
2. Убедиться, что выполнен редирект на /cabinet и в sessionStorage есть ключ session_token.
3. Зафиксировать: GET /cabinet → 200, content-type text/html.
4. Перехватить сетевые запросы: GET /api/auth/me с заголовком X-Session-Token.

## Ожидаемый результат
1–2. Редирект на /cabinet выполнен; sessionStorage.session_token — токен из ответа login (43 симв. base64url).
3. 200, text/html; HTML содержит маркеры кабинета («ЛИЧНЫЙ КАБИНЕТ», «Гига ГАИшник»).
4. GET /api/auth/me → 200 {"ok": true, "user": {...}} с email пользователя.

## Тестовые данные
Базовый пользователь TC-AUTH-001 (petrova@example.com / Qwerty123).
