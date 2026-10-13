<!-- factory-version: a12da342e542 -->

# Code Review: задача 1.1 change add-instructor-cabinet

## Вердикт: approve

| Параметр | Значение |
|---|---|
| Ревьюер | Код-ревьюер (изолированная сессия, Reviewer-Delegation: deleg-cr-20261013-external) |
| Дата | 2026-10-13 |
| Ревьюемый дифф | 018baae (feature/s2c-dashboard) — backend/dashboard.py (новый, GET /api/instructor/dashboard), backend/app.py (include роутера); tasks.md 1.1 [x] |
| Основание | Покрывающее ревью по выводам review-001-3.1.md (verdict: return по 3.1, функциональная часть подтверждена) и review-002-3.1.md (approve, MIN-1 закрыт); MAJ-1 (синхронизация контрактов sdd.md §20.1 / design.md / tasks.md 1.1) закрыт документально в 533e03e — предке 2aa7c2c |
| Арбитры | openspec/changes/add-instructor-cabinet/specs/instructor-dashboard/spec.md, design.md, sdd.md §20.1 (синхронизирован), tasks.md, requirements-instructor-cabinet.md (FR-18, FR-20, NFR-2, NFR-3) |
| Прогоны при ревью | `pytest tests/test_instructor_dashboard.py` → 11 passed (rev-001) / 12 passed (rev-002, +TTL); `pytest tests/` (регресс) → 200 → 201 passed |
| Blocker | 0 |
| Major | 0 |
| Minor | 0 (MIN-1 — единственное замечание, затрагивавшее файл задачи, закрыто в 2aa7c2c, подтверждено review-002-3.1) |

Вердикт **approve**. Задача 1.1 (backend/dashboard.py, эндпоинт
GET /api/instructor/dashboard) выполнена в объеме коммита 018baae и
полностью подтверждена ревью-циклом 3.1:

- Серверная проверка роли: сессия → 401 (`{"ok": false}`) без/с неверным/
  истекшим/аннулированным токеном; `role != 'instructor'` → 403; distinct
  401/403 как в design.md. Подтверждено кодом (dashboard.py:100–131) и
  тестами (TC-001/003/004/005 — зеленые).
- **demo:true** в ответе присутствует и тестируется (assert data["demo"] is True).
- NFR-2: единственный SQL — `SELECT … WHERE id = ?`, параметризован
  (test_dashboard_sql_parameterized, 0 конкатенаций).
- NFR-3: ответ и заголовки не логируются.
- MIN-1 (rev-001, приватный `auth._session_user_id`): закрыто в 2aa7c2c —
  добавлен публичный `auth.session_user_id(token)` (тонкая обертка, семантика
  401 идентична: ленивая чистка истекших, None на неверном токене);
  обращений к underscore-символу в dashboard.py больше нет. Подтверждено
  review-002-3.1 (MIN-1 — ЗАКРЫТО, approve).
- Контрактная синхронизация (MAJ-1 rev-001): sdd.md §20.1 / design.md /
  tasks.md 1.1 приведены к реализации в 533e03e (путь /api/instructor/dashboard,
  ключ `instructor`, состав §10.3 без id, демо-полезная нагрузка); задачи 1.1
  в tasks.md отмечена [x] с отсылкой к объему коммита 018baae. Расхождение
  устранено.

## Сценарии спек-дельты (серверная часть), покрытие

| Scenario | Проверка |
|---|---|
| Без сессии → 401 | тест TC-001 зеленый |
| Сессия истекла → 401 | TTL-тест добавлен (5.3/2aa7c2c), зеленый в прогоне 12 passed |
| Сессия student → доступ запрещен | тест TC-004 зеленый (403) |
| Одобренный инструктор с сессией видит кабинет | тест TC-005 зеленый (200 + ФИО/email + demo:true) |
| После выхода повторный доступ отклоняется | тест TC-003 зеленый |

Не проверено данным ревью: браузерный рендеринг (фронтовая часть — в
review-001-2.1), TTL-истечение в реальном времени (только через
monkeypatch-тест).

Provenance: функциональные доказательства привязаны к 018baae (rev-001) и
2aa7c2c (rev-002, MIN-1); approve действителен для этой цепочки SHA.

---
Reviewer-Delegation: deleg-cr-20261013-external
