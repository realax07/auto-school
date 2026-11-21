<!-- Reviewer-Delegation: deleg-s19-cr192rr3 — spawned hermes chat session (role=code_reviewer); ре-ревью тем же ревьюером | объект: фикс RR-1/RR-2 (HEAD) | дата: 2026-11-19 | session: 20261119_153124_706b6f -->

# Ре-ревью 19.2 (review-19.2-003) — фикс RR-1/RR-2 review-19.2-002

Роль: code_reviewer, ре-ревью тем же ревьюером (автор review-19.2-002).
Объект: commit 025572a «ПМ: фикс RR-1/RR-2 review-19.2-002 — убран
time.sleep (флейм keep-строки), докстринг по конвенции файла» — точечный
дифф по findings RR-1/RR-2 моего review-19.2-002. Ревью выполняется вне
flowctl: провениенс — эта шапка + sidecar-запись gate_runner record-review
(делает ПМ). Дерево: worktree wt-s19-ai-chat, ветка feature/add-ai-chat-home,
HEAD = 025572a (фикс поверх 9c63dba review-19.2-002).

## Периметр: только RR-1/RR-2 review-19.2-002

Проверяется исключительно закрытие двух находок review-19.2-002:

- RR-1 — time.sleep(1.2) в носителе TC-S19-011 (конвенция файла и
  conftest: sleep запрещен) + флейм keep-строки: после снятия сна
  выживание keep-строки должно быть детерминированным — floored
  T0−14d+1с, delete-строка (floored T0−14d−1с) удаляется всегда;
- RR-2 — докстринг носителя: без обоснования сна; детерминизм описан
  как прямой контроль БД («старые записи — прямым INSERT с created_at»).

MIN-1 (f-string SQL) закрыт и подтвержден в review-19.2-002 — не
ре-ревьюится. Нового сверх фикса не ищу; код/тесты не правятся, push
нет; зона записи — только этот файл.

## Машинные проверки (команды + результат)

1. Состав фикса: `git show HEAD --stat` → ровно 1 файл,
   tests/unit/test_s19_ai_chat.py (+5/−6); вне его коммит ничего не
   трогает. HEAD = 025572ad8c2755c4375d5bf1f47e2b69176d9f11.
2. Флейм-проба носителя: 5 одиночных прогонов
   `…/.venv/bin/python -m pytest
   tests/unit/test_s19_ai_chat.py::test_tc_s19_011_retention_exact_boundary -q`
   → все green: 1 passed (3.72s / 2.85s / 3.13s / 3.28s / 2.91s).
3. Полный файл: `…/.venv/bin/python -m pytest tests/unit/test_s19_ai_chat.py -v`
   → 13 passed, 1 warning in 13.43s (warning — StarletteDeprecationWarning
   из fastapi/testclient, к фиксу не относится).
4. Конвенция sleep: `grep -n "sleep\|import time" tests/unit/test_s19_ai_chat.py`
   → вызовов time.sleep и import time нет (совпадения — только
   докстринги, декларирующие «time.sleep запрещен»).
5. Спеки: `openspec validate --all --strict` → Totals: 28 passed,
   0 failed (28 items).

## Закрытие находок

RR-1 (sleep + флейм) — закрыто.

- time.sleep(1.2) удален, вместе с ним удален и `import time`;
  конвенция файла/conftest соблюдена.
- Детерминизм — формулами ровно как предписано (floored-секундная
  точка SQLite datetime):
  - delete-строка: `datetime('now','-14 days','-1 seconds')` =
    floored T0−14d−1с. Условие удаления created_at < T_q−14d
    сводится к floor(T_q) ≥ floor(T1) — истинно всегда (запрос
    выполняется после INSERT), строка удаляется безусловно, при
    любой латентности.
  - keep-строка: `datetime('now','-13 days','-23 hours','-59 minutes',
    '-59 seconds')` = floored T0−14d+1с. Выживание created_at ≥ T_q−14d
    сводится к floor(T_q) ≤ floor(T2)+1 — гарантировано при латентности
    запроса после сева < ~1с (локальный TestClient — единицы мс);
    допущение честно заявлено в докстринге. Двух отдельных вызовов
    datetime('now') (T1≠T2) это не ломает: margin ±1с у каждой строки
    свой, исход обеих проверок от взаимного сдвига на ≤1с не зависит.
- 5/5 одиночных прогонов + полный файл green (проверки 2–3 выше) —
  флейм-проба чистая.

RR-2 (докстринг) — закрыто.

- Обоснование сна убрано; сон больше не упоминается как механизм.
- Детерминизм описан соответственно реализации: «прямым контролем БД
  (конвенция файла: без time.sleep)» с явными floored-формулами
  T0−14d±1с — эквивалент «старые записи — прямым INSERT с created_at»
  (оба INSERT в теле теста идут с created_at = datetime('now', …)).

## Вердикт: approve
