# TC-AUTH-014 — Длительность блокировки нарастает и истекает (без sleep)

- ID кейса: TC-AUTH-014
- ID чеклиста: CHK-14
- Источник: CHK-14 → Requirement «Ограничение попыток входа (анти-брутфорс)» (домен auth) → FR-2; Scenario «Длительность блокировки нарастает»; R-BF2 (design: база 30 с, удвоение, верхняя граница 15 мин; значения фактические — backend/auth.py, D2)
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_auth.py::test_bruteforce_block_expires_and_escalates

## GIVEN / WHEN / THEN
- GIVEN блокировка входа с IP уже срабатывала ранее, и порог неудачных попыток превышен снова
- WHEN сравнивается длительность новой блокировки с предыдущей (сдвиг времени напрямую, без sleep)
- THEN новая блокировка длится дольше предыдущей (нарастание: base*2^(level-1), ≤ 15 мин); истекшая блокировка снимается; попытки во время блокировки не меняют level

## Предусловия
- Как в TC-AUTH-001; IP 10.0.0.4.
- Время управляемо: monkeypatch auth.time.time на управляемую переменную now[0] (в in-memory реестре blocked_until хранится как timestamp).

## Шаги
1. POST /api/register → 200; подменить clock: now[0] = реальное время.
2. С IP 10.0.0.4 выполнить _BF_MAX_FAILURES неудачных попыток → зафиксировать blocked_until; first_block = blocked_until - now[0].
3. Проверить: _BF_BASE_BLOCK_SECONDS ≤ first_block ≤ _BF_MAX_BLOCK_SECONDS.
4. Во время блокировки: попытка входа (ghost) → 401; зафиксировать level до/после.
5. Сдвинуть now[0] = blocked_until + 1 → убедиться, что IP не заблокирован (_is_blocked false).
6. Повторить _BF_MAX_FAILURES неудачных попыток → second_block = blocked_until - now[0].

## Ожидаемый результат
2–3. first_block в границах [30 с; 15 мин] (фактические константы из backend/auth.py).
4. 401; level не изменился (попытки во время блокировки не проверяют креды и не наращивают срок).
5. Блокировка истекла — IP разблокирован.
6. second_block > first_block (нарастание) и second_block ≤ _BF_MAX_BLOCK_SECONDS.

## Тестовые данные
IP 10.0.0.4; ghost@example.com; параметры _BF_MAX_FAILURES=5, _BF_BASE_BLOCK_SECONDS=30, _BF_MAX_BLOCK_SECONDS=900 (читать из backend/auth.py).
