<!-- reviewer: code_reviewer (изолированная сессия) | дифф: adf1a23 (feature/s2-integration) | дата: 2026-10-12 -->

# Code review: задача 5.1 (change add-instructor-flow)

Файл: backend/app.py (единственная правка существующего кода в части
сборки), интеграционные тесты tests/test_auth_route.py (раздел 5.1).
Provenance: HEAD `adf1a236bf9b7516d78b081d4da1853e3d481d1b`.

## Вердикт: approve

Reviewer-Delegation: deleg-cr-20261012-external

create_app() подключает роутеры instructors (1.1) и instructor_admin (2.1);
статические маршруты §15.6 добавлены рядом с /cabinet: /instructors,
/instructors/apply, /instructors/pending, /instructors/rejected,
/instructor/cabinet-stub; init_db через lifespan вызывает обновленную схему
(1.2). Границы задачи соблюдены: дифф спринта по существующим модулям —
только app.py (+11 строк) и auth.py (оговоренное расширение 3.1);
register.py, admin.py, config.py — без изменений (git diff против
origin/main — пусто).

## Таблица замечаний

| # | Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|---|
| — | — | — | Blocker/major отсутствуют | — |

Не является замечанием: порядок include_router не влияет (уникальные пути);
_page-фабрика с default-аргументом filename — корректное замыкание
(наследованный паттерн); маршруты /instructors/apply и /instructors/pending
не конфликтуют с /instructors (FastAPI точное совпадение путей).

## Проверено по чек-листу

| Проверка | Результат |
|---|---|
| /api/health зеленый | OK: `test_health_ok_after_mount` — {"ok": true} |
| Регресс Спринтов 0–1 | OK: `test_regression_sprint0_1` (/api/register, /api/auth/login, /api/admin/users) + полный набор 169 passed (включая test_register, test_admin, test_admin_users, test_auth, test_qa_sprint1, test_integration_sprint1, test_bug001 — без правок) |
| Новые маршруты отдаются | OK: `test_new_static_routes_served` — все 5 путей, 200 + text/html |
| Роутеры заявки/модерации смонтированы | OK: apply-контракт работает на собранном app (тесты test_auth_route через общий client из conftest), модерация — admin_headers + approve в тех же тестах |
| app.py — единственная точка правки (кроме auth.py 3.1) | OK: git diff против origin/main по backend: app.py, auth.py, db.py (1.2), instructors.py/instructor_admin.py (новые); register.py/admin.py/config.py не тронуты |
| init_db обновленной схемы | OK: миграция 1.2 исполняется в lifespan; тесты схемы (test_db.py) на той же init_db |

## Проверенные Scenario (готовность 5.1)

- Сборка: оба новых роутера отвечают на собранном приложении.
- Статика §15.6: пять маршрутов → 200 text/html.
- Регресс: здоровье, регистрация, вход, админ-список — как до спринта.

## Что НЕ проверено (честно)

- Запуск под реальным uvicorn (все прогоны через TestClient/create_app) и
  прод-файл data/app.db (тесты на изолированной БД conftest).
- openspec validate --all --strict — ворота задачи 6.1 (полная приемка).
