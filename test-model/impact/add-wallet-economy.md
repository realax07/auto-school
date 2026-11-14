# Impact-анализ — change add-wallet-economy (Спринт 16)

- Роль: qa_impact_analyst (H5); составлено по фактическим дельтам
- Дата: 2026-11-14
- Вход: дельты `openspec/changes/add-wallet-economy/specs/`
  (NEW wallet, payouts, admin-transactions, instructor-management;
  AMENDED booking — MODIFIED/ADDED; AMENDED containerization —
  REMOVED/ADDED/MODIFIED); тестовый набор `tests/`; трассировка
  TC-S16-001…008.

## 1. NEW дельты (новые кейпабилити — impact на существующее НЕ требуется)

- wallet / payouts / admin-transactions / instructor-management:
  кейпабилити не существовали (сверено `ls openspec/specs`),
  дельты создают их ADDED-требованиями. Существующие спеки не
  затрагивают: эндпоинты новые (/api/wallet*, /api/instructor/
  economy*, /api/admin/transactions*), таблицы новые (transactions,
  acquiring_topups, payouts, booking_disputes, instructors).

## 2. AMENDED booking (MODIFIED/ADDED) — зона регресса s5/s8/e2e

- MODIFIED «Запрос брони на слот»: при цене инструктора NULL поведение
  легаси 1:1 (холд не создается) — все 27 тестов s5-кластера остались
  БЕЗ правок и зеленые (полный прогон 501 passed); при заданной цене —
  снапшот + HOLD, 402 при нехватке средств.
- ADDED (размороз при отмене; авто-релиз 24ч; спор + решение
  оператора; статус «проведена»): дополнения поверх существующих
  статусов — конфликтов имен нет (сверка MODIFIED-имен с мастером).
- **Единственная правка старого теста**: tests/api/test_s8_backend.py
  TC-S8BE-009 [test-adapted] (79e6ee7) — кейс отклонял бронь в
  ПРОШЕДШЕМ экземпляре; политика МАЖ-1 арх-ревью (refund/отмена
  строго ДО старта) делает такой сценарий недостижимым (409).
  Кейс переведен на будущий экземпляр + усилен негативной проверкой
  409 — семантика кейса (reject-ветка) сохранена, усилен.
- e2e кабинет-кластера: без правок (цена NULL у фикстур) — 73 старых
  сценария green, +3 новых (кошелек/транзакции/цена) = 76 passed.

## 3. AMENDED containerization (REMOVED/ADDED/MODIFIED) — зона 16.0

- REMOVED MinIO: compose-сервис + volume удалены; контракт-тесты
  test_container_contract.py переработаны (4 точки); deploy/container-
  README.md, .env.example (оба блока), architecture/map.md вычищены;
  ADR-006 — только статусная приписка (история не переписывается).
- Прод-поведение: app+nginx не зависели от MinIO (S3-адаптер никогда
  не был реализован) — поведение контейнера не меняется; docker-build
  CI green.

## 4. Итог

- Полный pytest: 501 passed / 0 failed; e2e: 76 passed / 0 failed;
  regress-final change: PASS (failed_tests: []).
- Ломающих изменений контрактов API нет:.booking-эндпоинты расширяются
  (снапшот/холд — при цене NULL поведение идентично легаси); REMOVED —
  только MinIO-инфраструктура, не использовалась приложением.
