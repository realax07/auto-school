# TC-INT-001 — Интеграция сборки: mount auth, /cabinet, регресс Спринта 0

- ID кейса: TC-INT-001
- ID чеклиста: CHK-30
- Источник: CHK-30 → tasks.md 3.1 (трассировка FR-4); Requirement «Вход ученика» Scenario «После входа открыт кабинет» + cabinet / Доступ к кабинету; регресс — approved-кейсы Спринта 0 (TC-REG-001, TC-REG-013, TC-ADM-005)
- Тип: позитивный (интеграционный)
- Приоритет: Must
- Статус: automated — tests/test_integration_sprint1.py (test_health_ok, test_login_via_create_app, test_cabinet_page_served, test_cabinet_page_is_cabinet_html_file, test_regression_register_flow, test_regression_admin_flow, test_regression_static_pages); негатив админ-логина (сигнал review-001-3.1 #2) — tests/test_admin.py (TC-ADM-трассировка Спринта 0)

## GIVEN / WHEN / THEN
- GIVEN change add-auth-cabinet собран (все задачи 1.1–3.1 в ветке)
- WHEN поднимается приложение через create_app() и выполняется срез: /api/health, вход, /cabinet, регресс /api/register и /api/admin/*, полный pytest-прогон
- THEN /api/health зелен; роутер /api/auth/* примонтирован (login работает без самоподключения); GET /cabinet → 200 HTML кабинета; /api/register и /api/admin/* работают как в Спринте 0 (включая негативы); pytest зеленый

## Предусловия
- Чистая БД (tmp), env как в tests/conftest.py; код change в рабочей копии.

## Шаги
1. GET /api/health → зафиксировать ответ.
2. POST /api/register (базовый пользователь) → 200; POST /api/auth/login через create_app() без локального монтирования роутера → зафиксировать токен; GET /api/auth/me с токеном → 200.
3. GET /cabinet → зафиксировать статус, content-type, совпадение тела с frontend/cabinet.html.
4. Регресс Спринта 0: повтор той же регистрации → 422 «Email: уже зарегистрирован»; POST /api/admin/login (админ-креды) → токен; GET /api/admin/users с X-Admin-Token → список; GET /api/admin/users/export.csv → CSV; без токена → 401; POST /api/admin/login с неверным паролем → 401.
5. Выполнить полный прогон pytest (вся tests/).

## Ожидаемый результат
1. 200 {"ok": true}.
2. Регистрация 200; login 200 с токеном (43 симв. base64url); /me 200 {"ok": true, ...} — роутер примонтирован в create_app().
3. 200, text/html; тело == frontend/cabinet.html; маркеры мокапа и wiring присутствуют.
4. Все регрессные ответы идентичны Спринту 0: 422 дубликат; админ-токен 200; список 200 count==1; CSV 200; без токена 401; неверный админ-пароль 401.
5. pytest: 0 failed, 0 error.

## Тестовые данные
- Базовый пользователь TC-AUTH-001; админ: ADMIN_USER/пароль из env (conftest: admin / admin-pass-2026).
