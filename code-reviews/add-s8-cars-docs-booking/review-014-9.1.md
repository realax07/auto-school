<!-- reviewer: code_reviewer (изолированная сессия) | РЕ-ревью, итерация 002 | диффы: 8ca8880 (GET /api/instructor/students + TC-S8BE-009) | дата: 2026-11-02 -->

# Code review: задача 9.1 (change add-s8-cars-docs-booking) — РЕ-ревью (итерация 002)

Чек-лист итерации 001 (review-009): blocker #1 (GET /api/instructor/students
не реализован), major #2 (критерии готовности не покрыты тестами).
Проверен дифф 8ca8880 и соответствие контракту design.md блок A
(строка GET /api/instructor/students), tasks.md 9.1, ОВ-5, NFR-22/10.

Проверено:
- BLOCKER #1 ЗАКРЫТ: эндпоинт реализован (backend/student_requests.py:385–460,
  my_students): пары student_requests.status='accepted' ТОЛЬКО этого
  инструктора (instructor_id из сессии серверно — чужие пары невыдаемы
  по построению, адресации «чужого инструктора» в API нет — NFR-22;
  гость → 401, ученик → 403 через require_role); по каждой паре:
  student_id, full_name (ФИО из users — ADR-004), next_lesson —
  ближайшая confirmed бронь с lesson_date ≥ сегодня {date, time[, end_time]}
  или None → «нет», planned_count — confirmed после следующей
  (len(upcoming)-1), completed_count — confirmed с датой < сегодня;
  ТОЛЬКО confirmed (ОВ-5: new и rejected не входят); локальная дата
  сервера — local_today() из booking.py (правило MIN-1, таймзона клиента
  не участвует); чтение поверх booking/student_requests — новые сущности
  не заводятся (ADR-005); SQL параметризован (?-плейсхолдеры — NFR-10);
  сортировка детерминирована (lesson_date, start_time, id).
  Соответствие contracts design.md блок A — полное (end_time в
  next_lesson — аддитивное поле, потребители контракта не ломает).
- MAJOR #2 ЗАКРЫТ: TC-S8BE-009 (tests/test_s8_backend.py:1033+) покрывает
  все критерии готовности: сценарий дельты — 1 бронь на завтра, 2 на
  следующей неделе, 3 в прошлом → next_lesson «завтра» (дата/время
  слота), planned_count 2, completed_count 3; пара без броней (только
  new-запрос) → None/0/0; rejected-бронь и new-запрос вне «следующего»
  и счетчиков; состав — только принятые пары этого инструктора
  (второй инструктор видит только свою пару — «чужие пары не выдаются»);
  гость → 401, неверный токен → 401, ученик → 403. В прогоне ПМ
  358 passed (лог s8-int-fullpytest2.log).
- Зависимость 9.2 (данные раздела) — закрыта одновременно (см.
  review-015: фронт потребляет этот контракт).

## Вердикт: approve

Reviewer-Delegation: deleg-cr-20261102-111748-external

## Замечания

Блокирующих и мажорных замечаний нет. Статус закрытия чек-листа
итерации 001:

| # (review-009) | Серьезность | Статус | Доказательство |
|---|---|---|---|
| 1 | blocker | ЗАКРЫТ | my_students по контракту design.md блок A (пар/счетчики/доступ/SQL); TC-S8BE-009 |
| 2 | major | ЗАКРЫТ | TC-S8BE-009: дельта 1/2/3 → «завтра»/2/3, пустые состояния, new/rejected вне счетчиков, чужие пары, 401/403; 358 passed |

Не является замечанием: сравнение дат строковое (ISO lesson_date ≥
today) — корректно для ISO-формата; empty-состояние «нет пар» →
students: [] — пустое состояние раздела обрабатывается фронтом
(review-015).
