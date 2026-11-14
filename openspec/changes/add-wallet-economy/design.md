# Design: add-wallet-economy

Источники решений: Заказчик 2026-11-14 (дословные цитаты — proposal.md
«Источник требования»; решения-проекции СА — docs/ba/requirements-sprint16.md
«Открытые вопросы»); BACKLOG п.4 (MinIO закрывается в 16.0, PR#134);
прецеденты — add-booking-docs (транзакции бронирования, BEGIN IMMEDIATE,
частичные UNIQUE-индексы против гонок NFR-8), add-calendar-weeks-availability
(пересоздание таблицы при расширении CHECK — availability_new/ADR-010),
add-code-domain-folders (доменные пакеты backend/), add-s8-cars-docs-booking
(пакет СА + мокапы одним коммитом — 1d40a46), add-containerization (контракт
compose, F-1 ${VAR:?}), s15 (границы правок e2e — NFR-27, носители).
Дизайн-система мокапов: design/mocks/{dashboard-instructor,admin-dashboard,
my-requests}.html (сайдбары, бренд ✓-круг — ОДИН, темный фон #071015/#020b13,
зеленый акцент #35d879/#49ec9a, Inter).

## Примечание по instructor-management

Кейпабилити instructor-management в openspec/specs НЕ существует (сверено
ls openspec/specs). По правилам архива openspec для новой кейпабилити
допускаются только ADDED-требования — дельта оформлена ADDED и СОЗДАЕТ
кейпабилити (сверка с фактом — proposal «Сверка состава с фактом»).

## Baseline (что есть, без этого пакета не меняется)

- Бронирование (backend/student/booking.py, 805 строк): статусы
  new/confirmed/rejected (CHECK в db.py:122–133); POST /api/student/bookings
  — проверки в BEGIN IMMEDIATE (пара → 403, слот → 404, дата → 422, будущее
  FR-96 → 422, кросс-строчная занятость MAJ-1 → 409) + частичный UNIQUE
  uq_booking_active_slot (availability_id, lesson_date) WHERE new/confirmed;
  решения инструктора confirm/reject (guard AND status + rowcount → 409),
  cancel — BUG-049 (confirmed → rejected); _ACTIVE_STATUSES = (new,
  confirmed) — PUT availability против активных броней (MAJ-1); слот
  бронируется ЦЕЛИКОМ (интервал 2–4 ч — длительность для холда берется
  отсюда); money-полей и споров НЕТ.
- БД (backend/core/db.py): users (+role с миграции), instructor_applications
  (анкета; одобрение меняет users.role — таблицы instructors НЕТ),
  availability (slot_type recurring/one_off — прецедент пересоздания
  availability_new), booking, student_requests (прецедент частичного UNIQUE
  uq_student_requests_active), reviews, instructor_cars, document_versions;
  миграции — idempotent (CREATE IF NOT EXISTS + _COLUMN_MIGRATIONS ALTER +
  пересоздание с переносом строк).
- Админка (frontend/vue/src/pages/admin-dashboard/): ОДНА страница, разделы
  Пользователи/Заявки инструкторов/Автомобили/Документы + заглушки
  «Отношения», «Расписания», «₽ Платежи», «✎ Настройки» (soon()); e2e-якоря
  TC-UI-006/011/013/014 — не содержат «Платежи» (grep tests/web — 0);
  password_hash в исходниках UI отсутствует (test_qa_instructor_flow).
- Кабинет ученика (cabinet/): .snav data-tab Главная/Мои заявки/Мои брони,
  #sec-home/#sec-requests/#sec-bookings, хеши #/my-requests#/my-bookings;
  попап #m-book → POST /api/student/bookings, 409 «Слот уже занят»; TC-UI-059/060
  (один логотип, плитки без тегов) — behavioral, правок не требуют.
- Кабинет инструктора (instructor-dashboard/): нав Календарь/Мои ученики/
  Профиль и документы/Мои автомобили; негативы BUG-047-кластера
  («Мои документы», «Бронирования», «Мой автомобиль», «Запросы учеников» —
  отсутствуют); статистические карточки — визуал-заглушки (мокап
  dashboard-instructor «Заработано за месяц» — цифры демо).
- Контейнерный контур: compose services app+nginx+minio(minio под профилем,
  «MinIO отключен» комментарий), volumes db/uploads/minio-data, сети
  frontend/backend; CI flow.yml — dummy .env c MINIO_ROOT_* перед compose
  (F-1); scripts/container_test.sh — MINIO_ROOT_* локально; .env.example —
  ДВА минio-блока (18–21 «Креды MinIO…»; 28–30 дубль «CHANGE_ME_*»);
  test_container_contract.py — 4 минio-точки (см. «Инвентарь ссылок: MinIO»).
- Спеки: openspec/specs/{booking,containerization,…}; кейпабилити
  wallet/payouts/admin-transactions/instructor-management НЕ существуют
  (проверено ls) — создаются дельтами этого пакета; CLI 1.14.1: MODIFIED/
  RENAMED по несуществующей спеке валиден, но НЕ архиваем («only ADDED
  requirements are allowed for new specs» — проверено пробной дельтой) →
  instructor-management оформляется ADDED.

## Сверка контрактов решения (расхождения зафиксированы)

- «База эквайринга наверное отдельно должна быть» → таблица
  acquiring_topups ОТДЕЛЬНО от журнала (провайдер/статус/идемпотентность),
  журнал — только факт денег (transactions topup со ссылкой topup_id).
- «деньги блокируются, но еще у инструктора» → заморозка у ученика;
  двусмысленность дословной цитаты трактуется «еще НЕ у инструктора».
- «статистика сколько он заработал на учениках за месяц и всего за месяц» →
  разбивка по ученикам за месяц + итог месяца; суммы NET (после комиссии —
  «все что получил на руки»); gross/fee видны инструктору в карточках
  release-истории как справка.
- «вывести деньги по сбп, на сбер или другие банки рф» → канал один (СБП),
  поле «банк» — целевой банк получателя (Сбер/ВТБ/Т-Банк/…), телефон —
  идентификатор СБП; мок — заявка хранится в payouts, деньги списываются
  журналом при подтверждении оператора.
- «оператор видит транзакции все» → журнал БЕЗ пагинации-урезания домена:
  выдаются все с фильтрами (тип/роль/юзер/период); сортировка — свежие
  сверху; ограничение размера страницы — инфраструктурное (лимит вывода
  строк, не урезание домена).
- «в админке ставится каждому инструктору» → поле комиссии в разделе
  «Транзакции» (карточка инструктора/таблица инструкторов) — оператор
  редактирует; PUT-эндпоинт с валидацией 0–100.

## Модель данных (волна 16.1 — миграции db.py)

Новые таблицы (CREATE IF NOT EXISTS, idempotent):

    transactions — append-only журнал денег (NFR-34):
      id, type CHECK IN ('topup','hold','release','refund','payout'),
      user_id NOT NULL              -- владелец кошелька-движения
      amount_kop INTEGER NOT NULL CHECK (amount_kop > 0),
      booking_id, payout_id, topup_id  -- ссылки-источники (nullable)
      student_id, instructor_id        -- release: стороны сделки
      amount_gross_kop, fee_kop, amount_net_kop  -- release (нет у прочих)
      note TEXT, created_at DEFAULT (datetime('now'))
      Частичные UNIQUE (гонки NFR-35 — механика uq_booking_active_slot):
        uq_tx_hold_per_booking     ON transactions(booking_id) WHERE type='hold'
        uq_tx_release_per_booking  ON transactions(booking_id) WHERE type='release'
        uq_tx_refund_per_booking   ON transactions(booking_id) WHERE type='refund'
        uq_tx_payout_per_request   ON transactions(payout_id) WHERE type='payout'
      UPDATE/DELETE по журналу запрещены (гард test_qa_s16_money — grep
      исходников; NFR-34).

    acquiring_topups — мок-эквайринг (NFR-36; отдельно от журнала):
      id, student_id NOT NULL,
      amount_kop INTEGER NOT NULL CHECK (amount_kop > 0),
      provider TEXT NOT NULL DEFAULT 'mock',
      idempotency_key TEXT
        -- клиентский X-Idempotency-Key — идемпотентность пополнения:
        -- частичный UNIQUE uq_topups_idem ON (idempotency_key)
        -- WHERE idempotency_key IS NOT NULL (повтор с тем же ключом
        -- возвращает существующую запись, дубль-транзакции нет)
      provider_payment_id TEXT
        -- поле БУДУЩЕГО провайдера: мок не заполняет; UNIQUE при
        -- интеграции реального эквайринга — отдельный объем (NFR-36)
      status CHECK IN ('pending','succeeded','failed') DEFAULT 'succeeded'
        -- мок: мгновенный успех; pending/failed — машинерия будущего
        -- реального провайдера, сейчас не используется
      created_at

    payouts — заявки вывода СБП (NFR-36):
      id, instructor_id NOT NULL,
      amount_kop INTEGER NOT NULL CHECK (amount_kop > 0),
      channel TEXT NOT NULL DEFAULT 'sbp',
      bank TEXT NOT NULL, phone TEXT NOT NULL,
      status CHECK IN ('requested','paid') DEFAULT 'requested',
      operator_comment TEXT,
      requested_at DEFAULT (datetime('now')), paid_at TEXT
      Частичный UNIQUE: не более одной активной заявки на инструктора
        uq_payouts_one_pending ON payouts(instructor_id) WHERE status='requested'

    instructors — экономические атрибуты инструктора (дословно термину
    Заказчика «в админке ставится каждому инструктору»; факта таблицы не
    было — proposal «Сверка»):
      user_id INTEGER PRIMARY KEY  -- = users.id, role='instructor'
      commission_percent INTEGER NOT NULL DEFAULT 10
        CHECK (commission_percent BETWEEN 0 AND 100),
      price_per_hour_rub INTEGER   -- NULL = цена не задана (FR-100)
      updated_at TEXT
      Бэкфилл-миграция (идемпотентно): INSERT OR IGNORE … SELECT id FROM
      users WHERE role='instructor'; точка создания строки — одобрение
      заявки (backend/auth/instructor_admin.py, approve-ветка).

    booking_disputes — споры (механика НОВАЯ — proposal «Сверка»):
      id, booking_id NOT NULL, student_id NOT NULL,
      comment TEXT NOT NULL,
      resolution CHECK (resolution IN ('release','refund')),  -- NULL = открыт
      operator_comment TEXT,
      created_at, resolved_at TEXT
      Частичный UNIQUE: один открытый спор на бронь
        uq_disputes_open ON booking_disputes(booking_id) WHERE resolution IS NULL

Изменение booking (CHECK-статусы расширить ALTER'ом нельзя — прецедент
availability_new, пересоздание с переносом строк):

    booking + колонки (ALTER, _COLUMN_MIGRATIONS):
      price_per_hour_rub INTEGER      -- СНАПШОТ цены на момент брони (FR-101)
      hold_amount_kop INTEGER NOT NULL DEFAULT 0
      completed_at TEXT               -- отметка «проведено» (FR-105)
    booking_new: status CHECK IN ('new','confirmed','rejected','completed')
      -- пересоздание таблицы + перенос строк + индексы
      -- (uq_booking_active_slot пересоздается на new/confirmed — БЕЗ
      -- completed: проведенный экземпляр в прошлом, слот не занят)

Балансы — ЕДИСТВЕННЫЙ источник истины, SUM по журналу (вьюхи/запросы,
никаких колонок-счетчиков):

    ученик: available_kop = Σtopup(user) − Σhold(user)
                          − Σrelease.gross(student_id=я) + Σrefund(user)
            frozen_kop    = Σhold(user) − Σrelease.gross(student_id=я)
                          − Σrefund(user)
            total_kop     = available_kop + frozen_kop
    инструктор: earned_net_kop = Σrelease.net(instructor_id=я)
                balance_kop    = earned_net_kop − Σpayout(user=я)
    платформа:  company_balance_kop = Σrelease.fee   (FR-114; комиссия 0
                вносит 0 фактом — предложение не меняет SUM)

## Конечные автоматы

Бронь (расширение существующего):

    new ──confirm──▶ confirmed ──cancel(BUG-049)──▶ rejected ─┐
     │                    │                                   │
     └──reject──────────▶ rejected (refund: полный размороз)◀──┘
                              │   ▲ cancel/reject ПОСЛЕ старта ЗАПРЕЩЕНЫ:
                              │     409 «Занятие началось» (МАЖ-1)
                              ▼ complete (инструктор; экземпляр начался:
                                начало ≤ NOW МСК — правило instance_start)
                          completed ──(24ч, нет спора)──▶ [releasejournal]
                              │
                              └── dispute ученика (≤24ч от completed_at,
                                  комментарий обязателен; ТОЛЬКО при живом
                                  холде — МАЖ-2) ──▶ [спор открыт]
                                    ──решение оператора──▶ release ИЛИ refund

    Денежные гварды переходов (МАЖ-1/МАЖ-2):
    - cancel/reject допустимы СТРОГО ДО СТАРТА занятия (guard now <
      start_time экземпляра); refund ПОСЛЕ старта не выполняется ни в
      какой ветке. После старта исходы холда: «проведена» (авто-релиз),
      решение спора оператором или timeout-defrost — деньги не теряются.
    - спор открывается ТОЛЬКО из состояния «холд жив и заморожен»
      (held_awaiting): hold-транзакция существует и не исполнена;
      брони с price NULL (hold_amount=0) спора не открывают (422).

Холд (журнал):

    [нет] ──создание брони с ценой──▶ HOLD (available−, frozen+)
    HOLD ──reject/cancel СТРОГО ДО СТАРТА (now < start_time)──▶ REFUND
      (frozen−, available+); при start_time ≤ NOW — отказ 409 «Занятие
      началось», холд не меняется (МАЖ-1: refund после старта невозможен)
    HOLD ──авто-релиз (24ч после completed, спора нет)──▶ RELEASE
    HOLD ──timeout-defrost (экземпляр начался ≥72ч назад, complete НЕ
      было; статусы new/confirmed; спора нет)──▶ REFUND (авто-разморозка
      ученику — холд не висит вечно)
    HOLD ──спор (ТОЛЬКО живой холд: hold_amount_kop>0 и не исполнен —
      held_awaiting; price NULL без спора)──▶ (заморожен)
      ──оператор──▶ RELEASE или REFUND
    RELEASE/REFUND — терминальные; повтор невозможен (частичные UNIQUE).

Спор:

    [нет] ──POST /api/student/bookings/{id}/dispute (≤24ч, комментарий;
           ЖИВОЙ холд обязателен: hold-транзакция существует и не исполнена
           — hold_amount_kop>0 и нет release/refund по брони; иначе 422
           «спор только по тарифицированным броням»)──▶ open
    open ──POST /api/admin/disputes/{id}/resolve {resolution, comment}──▶
      release → RELEASE (gross→net инструктору, fee платформе)
      refund  → REFUND  (полный возврат в available ученику)
    Решение необратимо (resolution NOT NULL закрывает запись; новый спор по
    решенной брони запрещен — открытие спора только при открытом окне).

Пополнение (мок):

    POST /api/wallet/topup {amount_kop} (+ опциональный заголовок
      X-Idempotency-Key)
      → acquiring_topups(provider=mock, idempotency_key=значение ключа,
        provider_payment_id=NULL — поле будущего провайдера, мок не
        заполняет, status='succeeded')  -- мгновенный успех
      → transactions topup (available+)
    Идемпотентность: повтор с тем же X-Idempotency-Key → существующая
    запись (частичный UNIQUE uq_topups_idem), дубль-транзакции нет;
    без ключа каждый вызов — новая операция (клиент посылает ключ при
    повторе после сетевой неопределенности).

Выплата:

    [нет] ──POST /api/instructor/payouts {amount_kop ≤ balance, bank, phone}──▶
      requested (guard: другой requested → 409; частичный UNIQUE страхует гонку)
    requested ──оператор: POST /api/admin/payouts/{id}/confirm──▶
      paid + transactions payout (balance−)
      guard: balance_kop ≥ amount_kop на момент подтверждения, иначе 409 и
      заявка ОСТАЕТСЯ requested (деньги не списаны — журнал правды)
    Заявка НЕ замораживает баланс (СА-решение MVP: списание — факт выплаты,
    журнал = истина; риск «недостачи» к моменту confirm закрыт guard'ом 409).

Авто-релиз — ЛЕНИВЫЙ СВИП (single-worker, без фоновых потоков/кронов):

    wallet_sweep(conn): BEGIN IMMEDIATE; два SELECT'а:
      (1) авто-релиз: брони status='completed' AND hold_amount_kop>0 AND
          completed_at ≤ NOW−24ч AND нет открытого спора AND нет
          release-транзакции → RELEASE;
      (2) timeout-defrost (холд не висит вечно): брони status IN ('new',
          'confirmed') AND hold_amount_kop>0 AND экземпляр начался ≥72ч
          назад (start_time ≤ NOW−72ч) AND «проведена» не отмечена AND
          нет refund-транзакции → REFUND (полный возврат ученику:
          инструктор за 72ч не отметил «проведена» и не отменил до
          старта).
    Точки вызова (внутри write-транзакции): GET /api/wallet,
    GET /api/instructor/economy|earnings, GET /api/admin/transactions,
    GET /api/admin/disputes. Детерминизм: релиз ровно один на бронь
    (частичный UNIQUE) — повторный свип безобиден.

## Денежные правила

- ВСЕ суммы — целые копейки (INTEGER) от границы API до БД (NFR-33);
  цена часа — целые РУБЛИ в UI/API инструктора (FR-100), хранится в рублях,
  в копейки конвертируется при расчете холда (×100 — точная целочисленная).
- hold_amount_kop = price_per_hour_rub_снапшот × 100 × часы_слота;
  часы_слота = (end_time − start_time) целыми минутами / 60 — только если
  интервал кратен часу, иначе floor до целого часа (СА-решение: слоты
  2–4 ч кратны; нецелые интервалы — floor, хвост не тарифицируется).
- Релиз (FR-106): instructor_net = floor(gross × (100 − c) / 100);
  fee = gross − net (хвост платформе; при c=0 fee=0 — «учитывает факт 0»,
  FR-114). ОДНА транзакция release с gross/fee/net — восстанавливаемость
  (NFR-34). Комиссия c берется НА МОМЕНТ РЕЛИЗА (текущее значение
  instructors.commission_percent); историческое значение восстанавливается
  из release-строки (fee/gross) — пере-пересчет не требуется.
- 402 «Недостаточно средств» (FR-103): {ok:false, error, need_kop,
  available_kop}; бронь и холд НЕ создаются (откат транзакции).
- Арифметика: только INTEGER (+, −, ×, //); floor — целочисленное деление;
  float/Decimal/round( в денежном коде запрещены (гард test_qa_s16_money —
  grep исходников backend/wallet/**, booking.py, db.py).

## Инвентарь ссылок: booking / кабинет / админка (полный список)

| Носитель | Что читает/делает сегодня | Судьба в пакете |
|---|---|---|
| backend/student/booking.py::create_booking | INSERT booking в BEGIN IMMEDIATE | 16.3: после кросс-строчной проверки — чтение instructors.price_per_hour_rub, расчет холда, INSERT транзакции hold + снапшот-колонок в ОДНОЙ транзакции; 402 при недостатке. Легаси-путь (цена NULL) — поведение 1:1 |
| booking.py::reject_booking / cancel_booking | UPDATE status → rejected | 16.3: в той же транзакции — refund-транзакция журнала (если холд был; guard hold_amount_kop>0 и нет refund) |
| booking.py::confirm_booking | UPDATE → confirmed | 16.3: БЕЗ ИЗМЕНЕНИЙ (холд создается при создании брони, не при confirm — дословно «При бронировании… блокируются») |
| booking.py::_ACTIVE_STATUSES, blocking_bookings | new/confirmed против PUT availability | БЕЗ ИЗМЕНЕНИЙ: completed не активный статус; прошедшие экземпляры не блокируют (D8) и так |
| booking.py::instructor_slots / my_bookings / instructor_bookings | легаси-ответы | 16.3: state/статусы дополняются completed (отображение); легаси-поля не удаляются (обратная совместимость ответов) |
| tests/api/test_s5_backend.py (27 тестов) | весь контур бронирования | БЕЗ ПРАВОК: цены инструкторов в фикстурах не заданы → холда нет → контракты прежние; КОНТРОЛЬ — полный прогон в 16.3 (обязательный критерий готовности) |
| tests/web/test_ui_playwright.py кабинет-кластер (TC-UI-019/025/026/027, BUG-049/052, С10) | брони без цен | БЕЗ ПРАВОК: тот же аргумент (цены NULL); NFR-27; КОНТРОЛЬ прогоном в 16.3/16.6 |
| frontend/vue/src/pages/cabinet/ (App.vue/styles) | snav, секции | 16.4: + data-tab «Кошелек», #sec-wallet, хеш #/wallet; попап #m-book — обработка 402 (текст + кнопка «Пополнить кошелек»); существующие якоря не удаляются (TC-UI-019 — позитивные assertions) |
| frontend/vue/src/pages/instructor-dashboard/ | нав-разделы, карточки-заглушки | 16.4: + «Доходы» (#sec-earnings: цена часа, статистика, «Вывести»), «Отметить проведенным» в брони; негативы BUG-047-кластера не задеты («Доходы» вне негативного списка) |
| frontend/vue/src/pages/admin-dashboard/ | 4 раздела + soon-заглушки | 16.4: «₽ Платежи» → «Транзакции» (soon() снят) + #sec-transactions (журнал/фильтры/выплаты/споры/комиссия/баланс компании/комиссии за год); e2e-якорей на «Платежи» нет (grep — 0) |
| backend/app.py | include_router | 16.2: + wallet_router (ученик), instructor-economy-роуты, admin-роуты — файл только строкой подключения (прецедент доменных пакетов С13) |
| tests/web/test_static.py, check_tag_balance.py, check-budgets.mjs | 14 входов, PAGES | БЕЗ ИЗМЕНЕНИЙ: новых страниц/входов нет (BUG-047); бюджеты — контроль 16.6 (чанки растут, пороги не меняются) |

## Инвентарь ссылок: MinIO (16.0 — ПОЛНЫЙ, не «2 теста»)

| Носитель | Минio-точки | Судьба |
|---|---|---|
| docker-compose.yml | сервис minio (profiles, image, env ${MINIO_*:?}, volume, сеть backend) + volume minio-data + комментарии MIN-1/«MinIO отключен» | УДАЛЕНИЕ сервиса+volume; сеть backend удаляется (одна сеть frontend; app по-прежнему без публикуемых портов); комментарии переписаны |
| tests/test_container_contract.py | (1) test_compose_yaml_valid_and_has_services — set ≥ {app,nginx,minio}; (2) test_compose_minio_credentials_required_interpolation — ${MINIO_*:?}; (3) test_dockerfile_non_root_healthcheck_pinned — regex minio/minio-пина; (4) test_ci_docker_build_job_and_dummy_env_step — dummy .env MINIO_ROOT_USER | (1) → services == {app,nginx} (ровно; minio запрещен); (2) → заменен негативным тестом «minio в compose отсутствует»; (3) → minio-часть удалена (nginx-пин остается); (4) → dummy-шаг удален из flow.yml, тест проверяет compose-команды без dummy-env условия |
| .github/workflows/flow.yml | комментарий + шаг printf MINIO_ROOT_* > .env | Шаг удален (compose больше не требует переменных; ${POLICY_DIR/TLS_DIR} — с дефолтами) |
| scripts/container_test.sh | MINIO_ROOT_USER/PASSWORD | Удалены |
| .env.example | ДВА минio-блока: 18–21 «Креды MinIO (сервис minio читает из этого же env_file)… MINIO_ROOT_USER/PASSWORD» и 28–30 дубль «MinIO (обязательно при docker compose up…)… CHANGE_ME_*» | ОБА блока УДАЛЕНЫ (попутно закрывается pre-existing дубль MINIO_ROOT_* в одном файле); секция «Контейнерный контур» оставляет только TLS_DIR — compose после 16.0.1 теряет ${MINIO_*:?}, мертвые инструктирующие цепочки в репо недопустимы |
| deploy/container-README.md | сервис minio, креды MINIO_*, volume minio-data | Вычищены (описание стека app+nginx) |
| architecture/map.md | строка 16 (контейнеризация), диаграмма «сеть backend (app ↔ MinIO)», строка ADR-006, MIN-1/MIN-2 примечания | Вычищено/помечено: карта — живой документ (прецедент С10 «карта дополняется»); строка 16 — факт удаления с датой решения; диаграмма — два сервиса |
| architecture/adr/006-containerization.md | MinIO в заголовке/решениях/альтернативах | ТОЛЬКО статусная приписка «2026-11-14 — MinIO удален из стека (решение Заказчика «Закрой minio», add-wallet-economy 16.0)»; ИСТОРИЯ НЕ ПЕРЕПИСЫВАЕТСЯ (заголовок/текст решений — как есть) |
| docs/ba/requirements-containerization.md | MinIO в FR-52/NFR-14/16 описаниях, задача 6.3 | Вычищено (актуальное состояние — app+nginx; S3-контур отмечен отложенным решением BACKLOG) |
| BACKLOG.md | «add-wallet-economics» (п.4) | Опечатка id → add-wallet-economy (одна строка, ветка пакета) |
| openspec/specs/containerization/spec.md | Purpose, «Compose-стек app + nginx + MinIO», «Секреты…» (ключи MinIO, сеть app↔MinIO, сценарий «MinIO готов…»), «Версии зафиксированы» (nginx/MinIO) | ПРАВКА ТОЛЬКО ЧЕРЕЗ ДЕЛЬТУ пакета (REMOVED/ADDED/MODIFIED) — до архива файл не трогается |
| code-reviews/, test-model/ (add-containerization) | исторические записи | НЕ ПРАВЯТСЯ (исторические носители — прецедент s15) |

## Мокапы (создаются в коммите пакета — прецедент 1d40a46)

- design/mocks/wallet-student.html — «Кабинет ученика · Кошелек»: язык
  my-requests.html (шапка бренд ✓-круг ОДИН + crumb + user; page-head;
  карточки статусов Доступно/Заморожено/Всего; кнопка «Пополнить» + модал
  суммы (пресеты ₽); таблица истории: дата, тип, описание, сумма ±);
  плитки-сервисы НЕ вводятся (плиткам взяться неоткуда — инвариант
  TC-UI-060 не затрагивается), тегов «В КАБИНЕТЕ» нет (TC-UI-059/060,
  BUG-059/060).
- design/mocks/instructor-earnings.html — «Кабинет инструктора · Доходы»:
  язык dashboard-instructor.html (сайдбар 236px, бренд с small «Кабинет
  инструктора», nav с «Доходы» active); stat-карты: Заработано за месяц
  (net)/Всего за месяц/Доступно к выводу/Комиссия; таблица «по ученикам за
  месяц»; блок «Цена часа» (input, «Сохранить»); кнопка «Вывести деньги» +
  модал СБП (банк/телефон/сумма); список выплат (статус-бейджи заявка/
  выплачено).
- design/mocks/admin-transactions.html — «Админка · Транзакции»: язык
  admin-dashboard.html (сайдбар 250px, nav — «Транзакции» active);
  карточка «Баланс компании»; фильтры (тип/роль/юзер/даты); таблица
  журнала (id, дата, тип-бейдж, роль, пользователь, источник, сумма);
  блок «Выплаты — заявки» (Подтвердить); блок «Споры» (Выплатить
  инструктору / Вернуть ученику); таблица «Комиссии инструкторов за год» +
  селектор года.
- Все три — статические демо-данные, шапка-комментарий с доменом (прецедент
  my-requests.html); один логотип на страницу; id-якоря разделов
  #sec-wallet/#sec-earnings/#sec-transactions ПРИСУТСТВУЮТ в мокапах
  (прецедент anchor-стиля — admin-dashboard.html:88 id="sec-applications")
  и совпадают с будущей версткой (носители будущих вербатим-сверок и
  контрольного grep — задача 16.5.1).

## API-контур (волна 16.2 — контракты дельт)

    Ученик:   GET  /api/wallet                       → available/frozen/total + transactions
              POST /api/wallet/topup {amount_kop}    → мок-пополнение (мгновенно)
    Инструктор: GET  /api/instructor/economy          → цена, earned, balance, комиссия
                PUT  /api/instructor/price {price_per_hour_rub}
                GET  /api/instructor/earnings         → месяц по ученикам + итог
                POST /api/instructor/payouts {amount_kop, bank, phone}
                GET  /api/instructor/payouts
                POST /api/instructor/bookings/{id}/complete
    Ученик:   POST /api/student/bookings/{id}/dispute {comment}   (окно 24ч)
    Админ:    GET  /api/admin/transactions?type&role&user_id&date_from&date_to
              GET  /api/admin/payouts?status=requested
              POST /api/admin/payouts/{id}/confirm
              GET  /api/admin/disputes?status=open
              POST /api/admin/disputes/{id}/resolve {resolution, comment}
              PUT  /api/admin/instructors/{id}/commission {commission_percent}
              GET  /api/admin/commissions?year=YYYY               (+ баланс компании
                    в ответе /api/admin/transactions — company_balance_kop)
    Гварды: require_role (ученик/инструктор/админ — механика guards.py);
    402/409/422-коды по design «Конечные автоматы»; SQL параметризованный
    (NFR-10←NFR-3); ПД: телефоны СБП не логируются (наследование NFR-логов).

## Волновой план (16.0 → 16.6; задача = сессия, [P] — параллелится)

- **16.0 Гигиена MinIO** [infra]: compose/README/map/ADR-приписка/BA-доки/
  CI/container_test.sh/контрактные тесты; BACKLOG-опечатка. Независима от
  экономики — старт немедленно (решение Заказчика; BACKLOG п.4 «🔨 С16»).
- **16.1 Домен экономики и миграция БД** [code]: db.py (5 новых таблиц +
  booking_new-пересоздание + бэкфилл instructors), backend/wallet/ (журнал,
  балансы, свип),approve-ветка создает строку instructors. [P] с 16.0.
- **16.2 API кошелька/цен/статистики/выплат** [code]: эндпоинты контура
  (список выше), мок-пополнение, комиссия-PUT; test_s16_backend.py.
  Зависит от 16.1.
- **16.3 Холд-интеграция в бронирование** [code]: create_booking (холд в
  BEGIN IMMEDIATE, 402, снапшот), reject/cancel→refund СТРОГО ДО СТАРТА
  (после старта — 409 «Занятие началось», МАЖ-1), complete, dispute
  (ТОЛЬКО живой холд, МАЖ-2); свип в точках чтения (+ timeout-defrost
  72ч — холд не висит вечно); test_s16_hold_booking.py; КОНТРОЛЬНЫЙ
  полный прогон test_s5_backend + кабинет-кластера e2e (зелен без правок —
  критерий обратной совместимости). Зависит от 16.1 (16.2 не блокирует —
  холд-ядро в 16.1).
- **16.4 UI ученик/инструктор/админ** [code][P]: разделы cabinet/
  instructor-dashboard/admin-dashboard по мокапам; 402-обработка попапа
  брони. Зависит от 16.2 (API) — по контракту может стартовать параллельно
  16.3 (пишет против контрактов design, не против кода).
- **16.5 Мокапы — приемка и вербатим-фиксация** [docs]: мокапы созданы в
  пакете СА (этот коммит); задача: сверка инвариантов TC-UI-059/060
  (один логотип, без тегов), приемка Заказчиком, правки по замечаниям,
  фиксация носителей для будущих вербатим-сверок UI (прецедент FR-9).
  Зависит от 16.4 (сверка разметки с реализацией).
- **16.6 Бюджеты/гарды и гейт** [tests][infra]: check:budgets (14 входов,
  пороги без изменений), tag-balance, полный pytest + e2e, гард
  test_qa_s16_money (float-запрет, append-only), openspec validate --all
  --strict 0 ✗. Последняя волна.

## Решения по НФТ

- **NFR-33 (копейки)**: гард читает исходники backend/wallet/**,
  backend/student/booking.py, backend/core/db.py: запрет `float(`,
  `Decimal`, `round(`, деления `/` над денежными переменными; допустимо
  только `//` (floor) и `×100` константами. Тест добавляется в QA-контур
  (прецедент test_qa_sprint1 NFR-002 «SQL параметризован» — source-inspection).
- **NFR-34 (append-only)**: grep-гард: в backend/** нет `UPDATE transactions`
  / `DELETE FROM transactions`; комментарий-обязательство в шапке db.py.
- **NFR-35 (гонки)**: все денежные мутации — в BEGIN IMMEDIATE; частичные
  UNIQUE (список в модели) роняют проигравшего → IntegrityError → честный
  409 (прецедент uq_booking_active_slot/ученических заявок).
- **NFR-36 (моки)**: провайдер=mock захардкожен; внешних вызовов нет
  (гард: в backend/wallet/** нет httpx/requests/urlopen).
- **NFR-37 (UI-габариты)**: новых входов vite нет; check:budgets PAGES=14;
  рост чанков страниц в рамках 150/200 КБ gzip — замеры в отчете 16.6.
- **NFR-26/27 (наследование)**: бюджеты и «e2e без правок сценариев» —
  правок существующих e2e НЕТ; новые сценарии — только ДОБАВЛЕНИЕ
  (wallet/earnings/transactions-кластеры).

## Сознательные ограничения (задокументированы)

- Цена NULL = бесплатное занятие без холда — обратная совместимость
  (test_s5_backend/e2e без правок); инструктор, не выставивший цену, не
  участвует в экономике (осознанный MVP; смена дефолта — решение Заказчика
  отдельным объемом).
- Отмена/отклонение ПОСЛЕ СТАРТА занятия невозможны (МАЖ-1, решение СА):
  refund выполняется СТРОГО до start_time (guard now < start_time в
  cancel/reject — код-гвард задачи 16.3.1, booking.py:737/772); попытка
  после старта — 409 «Занятие началось», статус и холд не меняются.
  После старта исходы холда — «проведена» (авто-релиз), спор оператора
  или timeout-defrost: деньги не теряются ни в одной ветке.
- Спор — ТОЛЬКО по брони с живым холдом (МАЖ-2): hold-транзакция
  существует и не исполнена (hold_amount_kop>0, нет release/refund);
  price NULL (hold_amount=0) спора не создает (422) — иначе решение
  оператора ронялось бы на CHECK amount_kop>0 журнала (release/refund
  нулевой суммы невозможны). Жалоба на бесплатное занятие — вне денежного
  контура (канал жалоб в MVP не вводится).
- Холд не висит вечно (MIN-1): если инструктор за 72ч после старта не
  отметил «проведена» (и не отменил/не отклонил до старта), свип
  возвращает холд ученику (timeout-defrost — REFUND по брони new/
  confirmed с прошедшим экземпляром, задача 16.3.1); 72ч — константа
  MVP (время на отметку после занятия и разбор инцидента).
- Заявка выплаты не замораживает баланс (guard на confirm — design
  «Конечные автоматы»).
- Окно спора — ровно 24ч от completed_at; продление/перенос — вне объема.
- Журнал не хранит курс/валюту: одна валюта (RUB), MVP.
- Свип авто-релиза ленивый: релиз материализуется при первом чтении
  кошелька/админ-раздела ПОСЛЕ дедлайна (не в момент ровно 24ч) —
  статистика инструктора читается через тот же свип, расхождение —
  секунды-минуты, детерминизм сумм не страдает.
- Мокапы — статические артефакты; их синхронизация с разметкой страниц —
  16.5 (прецедент BUG-059/060: синхронизация при ИЗМЕНЕНИИ разметки).
- sdd.md/code-reviews/test-model — исторические носители не правятся.

## Соответствие ADR

ADR-001 (статика тем же сервисом) — не затронуто; ADR-006 (контейнеризация)
— сокращение стека до app+nginx по решению Заказчика (приписка, не отмена);
ADR-008 (Vue, финал миграции) — новые разделы ВНУТРИ существующих Vue-страниц,
без новых входов; ADR-009/ПД — телефоны СБП в payouts: выдаются только
владельцу и оператору (админ-раздел), в логи не пишутся (наследование NFR
логирования); ADR-010 (availability slot_type) — прецедент пересоздания
таблицы для booking_new.
