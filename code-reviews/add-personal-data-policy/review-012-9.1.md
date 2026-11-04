<!-- reviewer: ПМ (приемка change add-personal-data-policy, задача 9.1) | дерево: feat/s9-policy-package | дата: 2026-11-03 -->

# Code review: задача 9.1 (change add-personal-data-policy) — приемка

Сводка контрольных точек приемки (факты прогонов на дереве feat/s9-policy-package):

1. Полный прогон `pytest tests/` — 389 passed, 1 failed; failed = TC-NFR-001
   (логин <500мс) — ИЗВЕСТНЫЙ флак под параллельной нагрузкой агентов
   (флакует и на базовых деревьях прежних спринтов); изолированный прогон
   на тихой машине — passed (4.11с; повторно в составе 25 passed вместе с
   матрицей test_policy.py).
2. NFR-25 (заменяемость) — покрыта tests/test_policy.py (подмена артефакта →
   новая версия/текст БЕЗ правки кода; grep по frontend/** — 0 строк текста
   политики; битый артефакт → 500 {ok:false} без раскрытия содержимого).
   Механизм read_policy — чтение на каждый запрос без кэша, поэтому подмена
   видна даже до рестарта; деплой-операция (рестарт) — deploy/RUNBOOK.md,
   контрольные команды исправлены по код-ревью (review-007 → review-011:
   nginx-первичный curl; раскрытие $POLICY_FILE внутри контейнера).
3. NFR-10 — grep параметризованного SQL в измененных модулях: 0
   конкатенаций; текст политики/ПД в логи не пишутся (design/код).
4. openspec validate add-personal-data-policy --strict — valid;
   `--all --strict` — 15 passed, 0 failed (локально).
5. `python3 scripts/flow_check.py .` — OK (J10 указатели review-001..011 +
   review-012-9.1; кейсы approved 20/20 — review-001-cases «одобрить»).
6. sdd.md §32–33 (Спринт 9 ПД: модель артефакта, контракты, трассировка).
7. Design check — test-model/reviews/add-personal-data-policy/
   review-001-design.md: approve; минор (disabled-атрибут #reg-submit)
   применен отдельным коммитом.
8. Согласие фиксируется: consent_at (UTC сервера) + consent_policy_version
   (артефакт на момент сабмита) — в заявке инструктора и записи ученика;
   легаси-строки NULL без переписывания; артефакт недоступен при сабмите →
   500 и запись НЕ создается (тесты матрицы 3.1/4.1).

## Вердикт: approve

Reviewer-Delegation: deleg-acc-20261103-policy-external

## Замечания

Таймерный TC-NFR-001 — предсуществующий флак под нагрузкой; изолированный
прогон зеленый. Не является дефектом change.
