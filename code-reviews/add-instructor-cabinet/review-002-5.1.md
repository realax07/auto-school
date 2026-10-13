<!-- factory-version: a12da342e542 -->

# Code Review: задача 5.1 (MIN-1) change add-instructor-cabinet

## Вердикт: approve

| Параметр | Значение |
|---|---|
| Ревьюер | Код-ревьюер (изолированная сессия, Reviewer-Delegation: deleg-cr-20261013-external) |
| Дата | 2026-10-13 |
| Ревьюемый дифф | 2aa7c2c (feature/s2c-dashboard) — backend/auth.py (+8: публичный `session_user_id(token)`, auth.py:97–102), backend/dashboard.py (замена `auth._session_user_id` → `auth.session_user_id`); tasks.md 5.1 [x] |
| Основание | Покрывающее ревью по выводам review-002-3.1.md (раздел «MIN-1 — ЗАКРЫТО (approve)»); исходное замечание — review-001-3.1.md MIN-1 |
| Арбитры | specs/instructor-dashboard/spec.md, design.md, sdd.md §20.1, tasks.md, requirements-instructor-cabinet.md (FR-18, NFR-2, NFR-3) |
| Прогоны при ревью | `pytest tests/test_instructor_dashboard.py` → 12 passed; `pytest tests/` (регресс) → 201 passed |
| Blocker | 0 |
| Major | 0 |
| Minor | 0 |

Вердикт **approve**. Формулировка rev-001 (MIN-1): dashboard.py:101 обращался
к приватному `auth._session_user_id` ради контрактного тела `{"ok": false}`;
рекомендация — expose-нуть публичный helper в auth.py. Проверка по диффу
2aa7c2c (подтверждена review-002-3.1):

- auth.py: добавлен публичный `session_user_id(token)` — тонкая обертка, тело
  целиком `return _session_user_id(token)`; семантика не дублирована и не
  изменена (ленивая чистка истекших auth.py:91–93, None на неверном токене).
- dashboard.py: обращений к underscore-символу больше нет (grep — только
  упоминание в комментарии).
- Контрактное тело 401 `{"ok": false}` сохранено (тесты
  test_dashboard_401_without_token / _invalid_token / _after_logout — зеленые).
- Сделано ровно по рекомендации, без расширения объема; область диффа
  минимальна (5 файлов, +35/−8 в коммите).

FR-18 затронут положительно (семантика 401 идентична — та же функция под
оберткой), NFR-2/NFR-3 не затронуты (обертка без SQL и логирования).

---
Reviewer-Delegation: deleg-cr-20261013-external
