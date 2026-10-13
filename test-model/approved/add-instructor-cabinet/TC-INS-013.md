# TC-INS-013 — Выход через «Профиль и документы»

- ID кейса: TC-INS-013
- ID чеклиста: CHK-13
- Источник: CHK-13 → Requirement «Выход из кабинета» → FR-22; Scenario «Выход через профиль»
- Тип: позитивный
- Приоритет: Must
- Статус: automated — API/wiring-часть (tests/test_instructor_dashboard.py::test_dashboard_page_wiring_fr18_fr20_fr22 — wiring logout: fetch('/api/auth/logout'), method POST, sessionStorage.clear(), редирект; test_dashboard_401_after_logout — logout аннулирует токен); браузерная часть (клик по элементу в профиле, очистка sessionStorage, редирект) — manual/toBeAutomated (Playwright)

## GIVEN / WHEN / THEN
- GIVEN инструктор с валидной сессией открыл кабинет
- WHEN он выполняет выход через «Профиль и документы»
- THEN вызван POST /api/auth/logout с текущим токеном, после ответа sessionStorage очищен, выполнен редирект на главную

## Предусловия
- Инструктор вошел, кабинет открыт; браузер/Playwright с перехватом network и доступом к sessionStorage.

## Шаги
1. Войти инструктором, открыть кабинет; зафиксировать sessionStorage.session_token.
2. Открыть раздел «Профиль и документы», кликнуть элемент выхода внутри него.
3. Зафиксировать сетевые запросы, состояние sessionStorage и URL после завершения.
4. Дополнительно (серверная часть): повторить GET /api/instructor/dashboard со старым токеном.

## Ожидаемый результат
2. Отправлен POST /api/auth/logout с заголовком X-Session-Token: <токен>; ответ 200.
3. После получения ответа: sessionStorage пуст (sessionStorage.clear()), выполнен редирект на `/`.
4. Повторный вызов со старым токеном → 401 {"ok": false} — сессия аннулирована.

## Тестовые данные
Инструктор: instr@example.com / Instr1234.
