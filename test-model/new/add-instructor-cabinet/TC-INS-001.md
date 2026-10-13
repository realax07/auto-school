# TC-INS-001 — Доступ одобренного инструктора к кабинету

- ID кейса: TC-INS-001
- ID чеклиста: CHK-1
- Источник: CHK-1 → Requirement «Доступ к кабинету инструктора» (дельта instructor-dashboard) → FR-18; Scenario «Одобренный инструктор с сессией видит кабинет»
- Тип: позитивный
- Приоритет: Must
- Статус: automated — API-часть (tests/test_instructor_dashboard.py::test_dashboard_200_for_instructor_with_fio, плановый ID TC-FR18D-005; фикс. instructor: apply → approve → login, route='cabinet'); UI-часть (отрисовка кабинета по макету с подстановкой данных учетки) — manual/toBeAutomated (браузер/Playwright: сигнал риска review-001-3.1 — редиректы/ФИО требуют исполнения JS)

## GIVEN / WHEN / THEN
- GIVEN одобренный инструктор (role='instructor') выполнил вход, валидная сессия выдана (sessionStorage.session_token)
- WHEN он открывает /instructor/dashboard (страница выполняет GET /api/instructor/dashboard с заголовком X-Session-Token)
- THEN GET → 200 {"ok": true, "instructor": {"surname", "name", "patronymic", "email"}, "demo": true, ...}; кабинет отображается по макету, данные учетной записи подставлены

## Предусловия
- Сервис собран через create_app() поверх чистой БД; маршруты /instructor/dashboard и /api/instructor/dashboard примонтированы (задача 3.1).
- Учетка инструктора создана реальным флоу: POST /api/instructors/apply → approve администратором → POST /api/auth/login (ответ содержит route='cabinet').
- Для UI-части: браузер/Playwright (fetch, sessionStorage исполняются реально).

## Шаги
1. Создать инструктора флоу Спринта 2.1 (apply → approve), войти, зафиксировать токен.
2. GET /api/instructor/dashboard с X-Session-Token: <токен>.
3. (UI) Открыть /instructor/dashboard в браузере, перехватить сетевые запросы; убедиться, что кабинет отрисован по макету и ФИО/email учетки подставлены.

## Ожидаемый результат
2. 200; тело: ok=true, demo=true, instructor.surname/name/patronymic/email = данные записи users (ключ `instructor`, не `user`; поля id нет — sdd §20.1).
3. Кабинет отображается по макету; шапка содержит ФИО учетки (не демо-«Михаил Самойлов»); демо-блоки отрисованы (контроль D4 — по фактическому контракту sdd §20.1).

## Тестовые данные
Инструктор: instr@example.com / Instr1234 (ФИО «Иванов Иван Иванович»); админ для approve — admin_headers conftest.
