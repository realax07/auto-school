# TC-INS-016 — Вход инструктора через модалку лендинга ведет в кабинет

- ID кейса: TC-INS-016
- ID чеклиста: CHK-16
- Источник: CHK-16 → Requirement «Выход из кабинета» → FR-22; Scenario «Переход после входа ведет в кабинет» (сквозной: login-модалка лендинга → кабинет)
- Тип: позитивный (сквозной)
- Приоритет: Must
- Статус: automated — API-часть (фикстура instructor в tests/test_instructor_dashboard.py: POST /api/auth/login инструктора → route='cabinet'; также tests/test_auth_route.py); UI-часть (модалка m-login, sessionStorage, переход) — manual/toBeAutomated (Playwright)

## GIVEN / WHEN / THEN
- GIVEN одобренный инструктор (role='instructor') выполняет вход через модалку входа лендинга с верными учетными данными
- WHEN вход успешен (POST /api/auth/login → 200, ответ содержит route='cabinet')
- THEN пользователь попадает на /instructor/dashboard (переход выполнен автоматически, токен сохранен в sessionStorage)

## Предусловия
- Одобренная учетка инструктора создана флоу apply → approve; лендинг `/` обслуживается с модалкой входа (m-login).
- Для UI-части: браузер/Playwright.

## Шаги
1. Создать инструктора (apply → approve администратором).
2. (UI) Открыть `/`, открыть модалку входа, ввести email/пароль инструктора, сабмит.
3. Зафиксировать ответ POST /api/auth/login (route), содержимое sessionStorage, итоговый URL.

## Ожидаемый результат
2. POST /api/auth/login → 200 {"ok": true, "token": "...", "route": "cabinet"}.
3. Токен сохранен в sessionStorage.session_token; выполнен переход на /instructor/dashboard; кабинет отрисован (см. TC-INS-001).

## Тестовые данные
Инструктор: instr@example.com / Instr1234 (пароль ≥8 симв., есть буква и цифра — правила пароля регистрации).
