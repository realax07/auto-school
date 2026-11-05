<!-- reviewer: code_reviewer (изолированная сессия) | дифф: 894ab15 (git diff 035986a..HEAD, задача 1.1, ветка feat/s10-calendar-package) | дата: 2026-11-04 -->

# Code review: задача 1.1 (change add-calendar-weeks-availability)

Дифф `894ab15` — backend/db.py (новый DDL availability + миграция
_migrate_availability_slots) и tests/test_s10_backend.py (TC-S10BE-001,
4 теста миграции/домена). Ревью по трем кругам: (1) design.md «Модель
данных» (D1/D2/D4, NFR-30) + tasks.md 1.1 как закон, (2) практики
(idempotency, транзакционность, SQL), (3) смок ревьюера на TestClient
(свежее дерево HEAD 5f7607f): create_app() поднимает init_db через
lifespan на чистой БД — приложение стартует, домен availability работает
(бронь/409/слоты из проб ревьюера 2.1/3.1 идут через мигрированную
таблицу). Полный регресс НЕ запускался ревьюером (ПМ: полный сьют
365 passed — ПМ-верификация); прогон S10-сьюта — зона приемки.

## Вердикт: approve

Reviewer-Delegation: deleg-cr-20261104-s10-external

## Замечания

|| # | Серьезность | Файл:строка | Замечание | Рекомендация |
||---|---|---|---|---|
|| 1 | minor | backend/db.py:267–269 (_migrate_availability_slots: guard) | Чтение PRAGMA table_info (проверка guard) выполняется ВНЕ транзакции BEGIN IMMEDIATE — теоретическое окно между проверкой и перестройкой. Практически недостижимо: init_db — одноразовый запуск через lifespan при старте single-worker (наследованный инвариант), второй конкурентный init_db в процессе не возникает | Не требуется; при желании перенести BEGIN IMMEDIATE перед чтением PRAGMA — стоимость нулевая |
|| 2 | minor | backend/db.py:271 (conn.isolation_level = None) | Миграция переключает isolation_level в autocommit и НЕ восстанавливает значение; последующие шаги init_db (executescript _TOKEN_INDEXES, _seed_document_versions, conn.commit()) идут в autocommit-режиме. Поведение корректно (каждый шаг самодостаточен, финальный commit — no-op), но семантика соединения меняется неявно | Восстановить isolation_level после COMMIT/ROLLBACK или прокомментировать сознательность; не блокер |

Не является замечанием (соответствует контракту/решениям):
- Idempotency по построению: guard по отсутствию колонки slot_type; на
  свежей БД _SCHEMA уже содержит новые колонки → миграция — no-op.
  Повторный запуск: тест test_s10_migration_idempotent_noop гонит
  init_db трижды и сверяет ПОЛНЫЙ снимок (availability, booking,
  sqlite_master, sqlite_sequence) — 0 изменений, дублей нет (NFR-30).
- Перестройка выполняется ПОШАГОВО conn.execute, а не executescript —
  executescript сделал бы неявный COMMIT и разорвал BEGIN IMMEDIATE
  (комментарий в коде фиксирует причину). Одна транзакция:
  CREATE availability_new → INSERT..SELECT → DROP → RENAME → индексы.
- Совместимость легаси (FR-97, без backfill): существующие строки
  получают slot_type='recurring', slot_date='' через DEFAULT колонки —
  данные не перезаписываются; INSERT..SELECT переносит id и created_at
  (ссылки booking.availability_id остаются валидны). Тест
  test_s10_migration_legacy_becomes_recurring проверяет построчно:
  id [1,2], created_at дословно, брони 101/102 на своих availability_id.
- Индексы по выбранной политике (б): uq_booking_active_slot →
  (availability_id, lesson_date) WHERE status IN ('new','confirmed') —
  ровно design D4; существующие данные совместимы (старый индекс
  строже — две активные брони одного availability_id были невозможны).
  Пересоздание idx_availability_instructor после RENAME. Уровень
  хранилища покрыт test_s10_instance_index_two_dates_ok_same_date_409_domain
  (две даты одной серии — ок, одна дата — IntegrityError, rejected
  вне частичного индекса — ОВ-5).
- CHECK-домен (recurring ⇒ '', one_off ⇒ непустая; недопустимый тип;
  UNIQUE с slot_date: one_off на другую дату вставляется, recurring-
  дубликат и дубль one_off на дату+время — IntegrityError) — покрыт
  test_s10_slot_type_unique_and_check_domain (6 негативов).
- AUTOINCREMENT-последовательность availability сохраняется (sqlite_sequence
  переносится rename'ом; контроль — sqlite_sequence в снимке no-op-теста).
- SQL миграции — статические константы без интерполяций (NFR-10).

## Проверенные Scenario (спека)

- «Существующий интервал после релиза виден как повторяющийся без
  действий» + «Существующие брони остаются на своих слотах и видны на
  конкретных датах» (REQ_MIGRATION) — тестами TC-S10BE-001 на
  предсозданной legacy-БД (построчные assertions id/created_at/брони);
  смок ревьюера: приложение на мигрированной схеме исполняет полный
  контур броней/слотов (пробы задач 2.1/3.1 — 200/409/422 контрактно).
- «Повторный запуск миграции не создает дублей» — тройной init_db,
  полный снимок равен (включая sqlite_sequence — свидетельство
  сохраненной последовательности id).
- Домен уникальности FR-90 (совпадение one_off с экземпляром серии —
  две строки) и D4-индекс — тестами уровня хранилища (см. выше).

## Что НЕ проверено (честно)

- Миграция на РЕАЛЬНОМ контейнерном volume с боевыми данными — зона
  задачи 4.1 (контейнерный стенд); ревьюер проверял на тестовых БД.
- Поведение под конкурентной записью во время миграции (единственный
  writer — lifespan при старте; многопоточный прогон не строился).
- Полный регресс Спринтов 0–9 — прогон 3 плана тестов (приемка 7.1);
  ПМ заявил 365 passed — ревьюером не воспроизводился.
