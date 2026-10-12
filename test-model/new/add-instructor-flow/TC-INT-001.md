# TC-INT-001 — Сборка change: health, монтирование роутеров, статика, регресс, pytest

- ID кейса: TC-INT-001
- ID чеклиста: CHK-49
- Источник: CHK-49 → tasks.md задача 5.1 (сборка) → FR-10, FR-12, FR-13; sdd §15.6
- Тип: позитивный
- Приоритет: Must
- Статус: automated — tests/test_auth_route.py::test_health_ok_after_mount (плановый ID TC-FR13-006-смежный) + ::test_regression_sprint0_1 (/api/register, /api/auth/login, /api/admin/users) + ::test_new_static_routes_served (5 маршрутов 200 text/html) + полный pytest-прогон. До утверждения кейсов (rule 6)

## GIVEN / WHEN / THEN
- GIVEN приложение собрано через create_app()
- WHEN выполняются health-проверка, обращения к новым и унаследованным маршрутам, полный pytest-прогон
- THEN /api/health зелен; роутеры instructors и instructor_admin примонтированы; статика /instructors, /instructors/apply, /instructors/pending, /instructors/rejected, /instructor/cabinet-stub отдается (200); регресс Спринтов 0–1 (/api/register, /api/auth/*, /api/admin/users) работает; полный pytest-прогон зеленый

## Предусловия
- Репозиторий в рабочем состоянии; зависимости установлены; чистая БД для TestClient (conftest).

## Шаги
1. GET /api/health → зафиксировать.
2. GET /instructors, /instructors/apply, /instructors/pending, /instructors/rejected, /instructor/cabinet-stub → статусы/content-type.
3. Регресс: POST /api/register (petrova) → 200; POST /api/auth/login (petrova) → 200; GET /api/admin/users с админ-токеном → 200.
4. Монтирование: POST /api/instructors/apply → 200; GET /api/admin/instructor-applications с админ-токеном → 200.
5. Выполнить полный прогон: python -m pytest tests/ -q.

## Ожидаемый результат
1. 200 {"ok": true}.
2. Все 5 маршрутов — 200, text/html.
3. Все унаследованные операции работают как в Спринте 1.
4. Роутеры отвечают (примонтированы).
5. pytest: 0 failed, 0 error.

## Тестовые данные
Ученик petrova@example.com / Qwerty123; анкета — набор _apply (instr@example.com / Instr1234); админ admin / admin-pass-2026.
