# Покрытие: add-wallet-economy — TC-S16-001…008

Дельта: `openspec/changes/add-wallet-economy/specs/` — NEW
wallet (3 требования, 9 сценариев), payouts (2/7),
admin-transactions (5/10), instructor-management (4/10); AMENDED
booking (MODIFIED «Запрос брони на слот» — 11 сценариев, из них 4
эконом-сценария холда; ADDED 4 требования — размороз/refund+409+defrost
72ч (5), авто-релиз 24ч (3), спор (5), статус «проведена» (2)) и
containerization (REMOVED 2 — MinIO-стек и MinIO-сегментация; ADDED 2 —
стек app+nginx, секреты/порты; MODIFIED 1 — образ приложения). Всего
70 сценариев дельты. Покрытие полное: 70/70 — кейс либо группа кейсов на
каждый сценарий; сценарии, уже автоматизированные дословно, — через
существующие API/e2e-тесты без дублирования (NFR-27).

Принцип партии (Н5): вся поведенческая автоматизация уже существует —
экономика API: tests/api/test_s16_backend.py (22 теста, плановые ID
TC-S16-001…023), tests/api/test_s16_hold_booking.py (12, TC-S16-030…041,
полный FSM холда), tests/api/test_qa_s16_money.py (4 гварда исходников
TC-S16-M-001…003 + files-present); e2e: +3 кейса кластера экономики
TC-UI-061 (кошелек)/062 (транзакции)/063 (цена) — полный e2e 76;
контракт containerization — tests/test_container_contract.py (5,
ред. 16.0). Полный набор: 501 = 425 не-браузерных + 76 e2e; подтверждено
на HEAD 4ba66b1: эконом-подмножество 43 passed (22+12+4+5 контракт),
test_s8_backend 9 passed (вкл. [test-adapted] МАЖ-1). Адаптация s8
(TC-S8BE-009: отклоняемая бронь — будущего экземпляра, reject прошлой
брони 409) легитимна по МАЖ-1 — коммит 79e6ee7. Кейсы трассируют
«сценарий спеки → автоматизация/ручной остаток» и НЕ заводят новых
тестов. Именование: финальные approved-ID TC-S16-001…008; плановые
docstring-ID dev-волн (TC-S16-001…041, TC-S16-M-001…003) действовали до
утверждения (rule 6, прецедент add-instructor-flow TC-FR13→TC-AUTH) —
правок docstring не требуется, соответствие — в колонке «Автоматизация»
кейсов.

Обозначения: Wal = specs/wallet; Bkm-M = specs/booking MODIFIED «Запрос
брони на слот» (эконом-сценарии); Bkm-A = specs/booking ADDED (размороз,
авто-релиз, спор, «проведена»); Pay = specs/payouts; Adm =
specs/admin-transactions; Ins = specs/instructor-management; Cnt =
specs/containerization.

| Кейс | Сценарии спеки | Автоматизация |
|---|---|---|
| TC-S16-001 | Wal: все 9 («Кошелек пуст», «Балансы = журнал», «Копейки», «Чужой недоступен», «Пополнение зачисляется», «Идемпотентность», «Некорректная сумма», «Раздел: балансы+история», «Внутри кабинета — якоря») | test_s16_wallet_empty_and_guards (011), topup_and_history (012), topup_idempotency_key_vs_no_key (013), topup_validation_limits (014), wallet_isolation_between_students (017), ledger_balances_hold_refund_cycle (007); гварды: test_qa_s16_money M-001 (NFR-33), M-002 (NFR-34); e2e TC-UI-061 + якоря TC-UI-019/025/026/027, BUG-047 без правок |
| TC-S16-002 | Bkm-M: «Холд и снапшот», «402 — брони нет», «Без цены — без холда», «Дубль — холд не дублируется»; Ins: «Выставить цену», «Смена цены не трогает холды», «Некорректная цена» | test_s16_hold_booking: hold_snapshot_and_frozen_on_create (030), insufficient_funds_402_no_booking (031), race_outcomes_terminal_and_complete_guard (040), legacy_price_null_path_untouched (041); test_s16_backend: ledger_hold_amount_kop_hours_floor (009), instructor_price_save_validate_reset (018); M-001; e2e TC-UI-063 (тост-инвариант «существующие холды не изменились»); легаси-контроль — s5-кластер брони, TC-UI-007 |
| TC-S16-003 | Bkm-A «Размороз»: все 5 («Reject возвращает», «Cancel возвращает», «Повторный невозможен», «409 после старта», «Defrost 72ч») | test_s16_hold_booking: hold_reject_refund_before_start (032), hold_cancel_refund_and_legacy_guards (033), maj1_cancel_reject_after_start_409 (034), timeout_defrost_72h_refund (039), race_outcomes_terminal… (040); test_s16_backend: ledger_balances_hold_refund_cycle (007); [test-adapted] test_s8_backend::test_s8_my_students_list_counters_and_access (МАЖ-1, 79e6ee7); «без холда размороза нет» — BUG-049 e2e (легаси) |
| TC-S16-004 | Bkm-A «Авто-релиз 24ч»: 3 («После окна», «До окна нет», «Спор блокирует»); Bkm-A «Спор»: 5 («В окне», «Вне окна», «Повторный», «Бесплатной 422», «Решение оператора»); Bkm-A «Статус „проведена"»: 2; Ins «Отметить проведенным»: 2 | test_s16_hold_booking: complete_and_lazy_release_after_24h (035), release_commission_zero_fact (036), dispute_blocks_sweep_then_operator_resolves (037), dispute_guards_window_hold_ownership (038), race_outcomes… (040); test_s16_backend: sweep_release_after_24h_dispute_blocks_and_rerun_idempotent (010), migration_booking_completed_and_snapshot_columns (001), domain_tables_constraints (005 — UNIQUE спора); «не занимает будущие экземпляры»/UI-кнопки — ручные пробы приемки (см. кейс) |
| TC-S16-005 | Ins «Комиссия 10/0–100/floor»: 2; Ins «Статистика»: 3 («Сходится с журналом», «Нули», «Чужая недоступна»); Adm «Комиссия редактируется»: 2 | test_s16_backend: instructors_backfill_and_approve_point (006 — дефолт 10), ledger_release_split_and_balances_commissions_0_10_100 (008 — floor 0/10/100), admin_commission_and_yearly_commissions (023 — PUT + границы), instructor_earnings_month_by_student (018b — месяц по ученикам + пустой месяц); test_s16_hold_booking: release_commission_zero_fact (036); M-001; e2e TC-UI-063/TC-UI-062 (факт 0 в таблице комиссий) |
| TC-S16-006 | Pay: все 7 («Заявка создается», «Сумма > баланса», «Вторая активная», «Мок без сети», «Confirm один раз», «Недостача», «Чужую/выплаченную нельзя»); Adm «Операционные блоки»: выплатная половина («Подтверждает выплату из раздела») | test_s16_backend: instructor_payout_request_guards (019), admin_payout_confirm_and_insufficiency (021); test_qa_s16_money M-003 (NFR-36 — мок СБП без httpx/requests/urlopen); e2e TC-UI-062 (#tx-payouts-empty); форма инструктора/confirm()-диалог админа — ручные пробы |
| TC-S16-007 | Adm «Журнал с фильтрами»: 3 («Все без фильтров», «Фильтры сужают», «Доступ только оператора»); Adm «Баланс компании»: 1; Adm «Комиссии за год»: 2; Adm «Операционные блоки»: спорная половина («Оператор решает спор») | test_s16_backend: admin_transactions_filters_and_company_balance (020 — фильтры тип/роль/юзер/период, company_balance_kop, 401 на ученическую сессию), admin_disputes_resolve_release_refund (022 — release/refund, комментарий обязателен, повтор 409), admin_commission_and_yearly_commissions (023 — селектор года, факт 0); M-002 (журнал только читается); e2e TC-UI-062 (раздел вместо «Платежи»-заглушки, журнал по живому API, баланс 0 ₽, пустые состояния); UI-фильтры/диалог спора — ручные пробы |
| TC-S16-008 | Cnt ADDED «Стек app+nginx»: 2; Cnt ADDED «Секреты/порты»: 3; Cnt MODIFIED «Образ»: 3; REMOVED 2 (причины удаления — в дельте) | test_container_contract: compose_yaml_valid_and_services_exactly_app_nginx (services == {app, nginx}), compose_minio_absent (негатив: minio/minio-data/MINIO_* — замена прежнего позитивного теста), dockerfile_non_root_healthcheck_pinned, requirements_fully_pinned, ci_docker_build_job_compose_without_dummy_env; пин nginx tag+digest и «только 80/443» — факт compose (docker-compose.yml:51, 16.0); Docker-стенд (build/up/down-персистентность db+uploads, history/inspect секретов) — ручные шаги гейта |

Свод по автоматизации партии: новых автотестов партия НЕ добавляет.
Якоря: API-экономика 38 тестов (test_s16_backend 22 + test_s16_hold_booking 12 +
test_qa_s16_money 4), контракт 5, e2e TC-UI-061/062/063 в полном e2e 76,
легаси-контроль — s5/s10-кластеры бронирования, BUG-049, TC-UI-019/025/
026/027, BUG-047, TC-UI-006/011/013/014 — все прогоняются без правок
сценариев (NFR-27); допустимый дифф тестов партии — только ДОБАВЛЕНИЕ
новых кластеров + [test-adapted] TC-S8BE-009 (МАЖ-1, reject прошлой
брони 409 → отклоняемая бронь будущего экземпляра — коммит 79e6ee7).
Прогоны на HEAD 4ba66b1: эконом-подмножество 43 passed; test_s8_backend
9 passed; полный набор 501 (425 не-браузерных + 76 e2e, зеркало CI —
гейт 16.6.2). Ручные остатки (свод, выполняются на приемке/гейте):
проба брони с ценой через UI (402-сообщение), UI-кнопка «Проведено» и
форма спора ученика, «проведенная бронь не занимает будущие экземпляры
серии», поле «Комиссия %» и фильтры/диалоги раздела «Транзакции»
(confirm() выплат, disabled-кнопка решения спора — прецедент BUG-046),
форма заявки СБП инструктора, Docker-стенд 16.0 (build/down-up
персистентность, инспекции секретов/портов), визуальные сверки разделов
с мокапами wallet-student/instructor-earnings/admin-transactions
(задача 16.5.1). Двойное именование ID (плановые docstring TC-S16-001…041
vs approved TC-S16-001…008) — осознанное: плановые действовали до
утверждения (rule 6), соответствие зафиксировано в кейсах и таблице.
