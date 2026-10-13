<!-- factory-version: a12da342e542 -->

# Code Review: задача 5.3 (MIN-3) change add-instructor-cabinet

## Вердикт: approve

| Параметр | Значение |
|---|---|
| Ревьюер | Код-ревьюер (изолированная сессия, Reviewer-Delegation: deleg-cr-20261013-external) |
| Дата | 2026-10-13 |
| Ревьюемый дифф | 2aa7c2c (feature/s2c-dashboard) — tests/test_instructor_dashboard.py (+18: test_dashboard_401_expired_session_ttl); tasks.md 5.3 [x] |
| Основание | Покрывающее ревью по выводам review-002-3.1.md (раздел «MIN-3 — ЗАКРЫТО (approve)»); исходное замечание — review-001-3.1.md MIN-3 |
| Арбитры | specs/instructor-dashboard/spec.md (сценарий «Сессия истекла → 401»), design.md, sdd.md §20, tasks.md, requirements-instructor-cabinet.md (FR-18) |
| Прогоны при ревью | `pytest tests/test_instructor_dashboard.py` → 12 passed (11 в rev-001 + 1 новый TTL-тест); `pytest tests/` (регресс) → 201 passed (200 → 201: добавлен ровно один тест) |
| Blocker | 0 |
| Major | 0 |
| Minor | 0 |

Вердикт **approve**. Формулировка rev-001 (MIN-3): сценарий «Сессия истекла
(TTL 12 ч)» не покрыт отдельным тестом (TC-FR18D-002 — только неверный токен);
рекомендация — тест, кладущий запись с истекшим expires в auth._sessions
напрямую. Проверка по диффу 2aa7c2c (подтверждена review-002-3.1):

- Добавлен test_dashboard_401_expired_session_ttl: monkeypatch.setitem кладет
  в auth._sessions запись `(time.time() - 1, user_id)` (expires в прошлом,
  без sleep), затем GET → 401 `{"ok": false}` + проверка ленивой чистки
  (токен отсутствует в _sessions после вызова).
- Формат записи соответствует `dict[str, tuple[float, int]]` (auth.py:46),
  механике `_session_user_id` (expires < now → pop → None).
- Тест изолирован через monkeypatch.setitem — после теста словарь
  восстанавливается, конфликтов с logout-тестами нет; не flaky-зависим от
  порядка (подтверждено прогоном 12 passed).
- Тест реально выполнялся в review-002-3.1 — закрыто по первому (основному)
  варианту рекомендации.

Сценарий спек-дельты «Сессия истекла → 401» теперь покрыт отдельным тестом
(в rev-001 — «частично»).

---
Reviewer-Delegation: deleg-cr-20261013-external
