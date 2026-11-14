# Tasks: add-wallet-economy

Правила: задача атомарна (одна сессия = одна задача); `[P]` — независимая
задача (параллелится, каждая в своем worktree; пишут против контрактов
design.md, не против кода друг друга). Типы работ: `[code]`/`[tests]`/
`[docs]`/`[infra]`. Источники контрактов — docs/ba/requirements-sprint16.md
(FR-98…FR-116, NFR-33…NFR-37) и design.md (модель данных, автоматы,
инвентарь ссылок). Домен экономики — backend/wallet/ (прецедент
add-code-domain-folders). Новых pip/npm-зависимостей нет; моки эквайринга/
СБП — без внешних вызовов (NFR-36). Денежная арифметика — только целые
копейки (NFR-33; гард 16.6).

**Правило партии С16 (директива СА): после КАЖДОЙ задачи — коммит
«[s16] CA: <краткое имя задачи>» + push в ветку feat/s16-economy
(прецедент С15).**

## 16.0 Гигиена MinIO (решение Заказчика «Закрой minio»; [P] со всеми волнами)

- [ ] 16.0.1 [infra] docker-compose.yml — сервис minio и volume minio-data
      УДАЛЕНЫ; сеть backend удалена (остается frontend: nginx ↔ app;
      app по-прежнему БЕЗ публикуемых портов); комментарии MIN-1/
      «MinIO отключен» переписаны под фактический стек app+nginx;
      BACKLOG.md п.4 — опечатка «add-wallet-economics» →
      «add-wallet-economy» (одна строка).
      Готовность: `docker compose config` валиден; services = {app,
      nginx}; `git grep -in minio docker-compose.yml` — пусто.
      FR: — (гигиена). NFR: — (MinIO-чистка без собственного NFR —
      решение Заказчика «Закрой minio»; трассировка — REMOVED-дельта
      containerization). Зависит от: —.

- [ ] 16.0.2 [tests][infra] tests/test_container_contract.py — переработка
      РОВНО ЧЕТЫРЕХ минio-точек (полный инвентарь — design.md «Инвентарь
      ссылок: MinIO», решение называло «2 теста» — сверка с фактом):
      (1) test_compose_yaml_valid_and_has_services → services == {app,
      nginx} (ровно; minio запрещен); (2) test_compose_minio_credentials_
      required_interpolation → заменен негативным «minio в compose
      отсутствует»; (3) test_dockerfile_non_root_healthcheck_pinned —
      minio-пин удален из проверок (nginx tag+digest остается); (4)
      test_ci_docker_build_job_and_dummy_env_step → dummy .env-шаг
      удален из flow.yml, тест проверяет docker-build job и compose-
      команды без условия dummy-env. Сопутствующая чистка:
      .github/workflows/flow.yml (шаг printf MINIO_* удален),
      scripts/container_test.sh (MINIO_* env удалены),
      deploy/container-README.md (сервис/креды/volume minio вычищены),
      .env.example (ОБА минio-блока удалены: 18–21 «Креды MinIO…» и
      дубль 28–30 «CHANGE_ME_*»; секция «Контейнерный контур» оставляет
      только TLS_DIR — compose теряет ${MINIO_*:?}, мертвые
      инструктирующие цепочки недопустимы),
      architecture/map.md (строка 16, диаграмма «app ↔ MinIO», MIN-1/MIN-2
      примечания — факт удаления с датой; карта — живой документ),
      docs/ba/requirements-containerization.md (minio-упоминания вычищены),
      ADR-006 — ТОЛЬКО статусная приписка «2026-11-14 — MinIO удален
      (решение «Закрой minio», add-wallet-economy 16.0)», история НЕ
      переписывается.
      Готовность: `pytest tests/test_container_contract.py` зелен;
      `git grep -il minio -- docker-compose.yml deploy/container-README.md
      architecture/map.md docs/ba/requirements-containerization.md
      .github/workflows flow.yml scripts/container_test.sh .env.example`
      — пусто;
      `grep -c MinIO architecture/adr/006-containerization.md` —
      неизменен кроме приписки (исторический текст сохранен).
      FR: —. NFR: — (MinIO-чистка без собственного NFR — см. 16.0.1).
      Зависит от: 16.0.1.

## 16.1 Домен экономики и миграция БД ([P] с 16.0)

- [ ] 16.1.1 [code] backend/core/db.py — миграции (idempotent, прецедент
      availability_new): НОВЫЕ таблицы transactions (append-only журнал;
      частичные UNIQUE uq_tx_hold/release/refund_per_booking,
      uq_tx_payout_per_request — design «Модель данных»),
      acquiring_topups (provider=mock, idempotency_key — клиентский
      X-Idempotency-Key с частичным UNIQUE; provider_payment_id — поле
      будущего провайдера, мок не заполняет),
      payouts (частичный UNIQUE одной активной заявки на инструктора),
      instructors (user_id PK, commission_percent 0–100 DEFAULT 10,
      price_per_hour_rub NULL; бэкфилл INSERT OR IGNORE из users
      role='instructor'), booking_disputes (частичный UNIQUE открытого
      спора); booking — пересоздание booking_new (status CHECK +
      'completed'; колонки price_per_hour_rub, hold_amount_kop DEFAULT 0,
      completed_at; uq_booking_active_slot пересоздан на new/confirmed).
      Комментарий-обязательство append-only в шапке таблицы transactions.
      Готовность: миграция на копии прод-подобной БД — данные целы,
      повторный старт без ошибок (прецедент контейнера); pytest
      tests/api/test_db.py зелен.
      FR: FR-98…109 (несущие таблицы). NFR: NFR-33/34/35. Зависит от: —.

- [ ] 16.1.2 [code] backend/wallet/ — доменный пакет (журнал/кошельки/
      ledger.py, sweeps.py): SUM-балансы (available/frozen/total ученика;
      earned/balance инструктора; company fee) — единственный источник
      истины; wallet_sweep (авто-релиз — ленивый, BEGIN IMMEDIATE,
      частичный UNIQUE страхует повтор); создание транзакций hold/
      release/refund/topup/payout с расчетом fee = floor(gross×c/100)
      целочисленно; точка создания instructors при одобрении заявки
      (backend/auth/instructor_admin.py, approve-ветка).
      Готовность: unit-прогон балансов на сценариях design «Конечные
      автоматы» (холд→рефанд; холд→релиз с комиссиями 0/10/100 —
      «учитывает факт 0»); импорты доменные (С13).
      FR: FR-106/109/114. NFR: NFR-33/34/35. Зависит от: 16.1.1.

## 16.2 API кошелька/цен/статистики/выплат (после 16.1)

- [ ] 16.2.1 [code] backend/wallet/wallets.py + включение роутера в
      backend/app.py: GET /api/wallet (суммы + история; вызов свипа),
      POST /api/wallet/topup (мок: acquiring_topups + journal topup;
      идемпотентность — клиентский заголовок X-Idempotency-Key →
      idempotency_key с частичным UNIQUE; provider_payment_id не
      заполняется — поле будущего провайдера (NFR-36); валидация суммы —
      положительная, верхний предел MVP 500 000 ₽-эквивалент в копейках —
      защита от опечаток); гварды require_role; ПД: без логирования
      сумм/идентификаторов в текстах логов (наследование).
      Готовность: test_s16_backend.py — кошелек пустого ученика
      (0/0/0), пополнение → доступно+, история содержит topup, повтор с
      тем же X-Idempotency-Key — дубля нет (частичный UNIQUE, NFR-35);
      без ключа каждый вызов — новая операция.
      FR: FR-98/99. NFR: NFR-33/34/35/36. Зависит от: 16.1.2.

- [ ] 16.2.2 [code] инструкторская экономика (backend/wallet/ или
      backend/instructor/): GET /api/instructor/economy (цена, earned,
      balance, комиссия), PUT /api/instructor/price (целые рубли ≥ 0;
      NULL-сброс — явное поле), GET /api/instructor/earnings (месяц по
      ученикам + итог месяца — агрегаты release, net), POST/GET
      /api/instructor/payouts (заявка: amount ≤ balance, bank+phone
      обязательны; guard одной активной — 409).
      Готовность: test_s16_backend.py — цена сохраняется/валидируется;
      статистика на посевных release (10%/0% комиссии — net=gross−fee);
      заявка второй раз до подтверждения — 409; сумма > balance — 422.
      FR: FR-100/110/111. NFR: NFR-33/35. Зависит от: 16.1.2.

- [ ] 16.2.3 [code] админ-контур экономики (backend/wallet/
      admin_transactions.py): GET /api/admin/transactions?type&role&
      user_id&date_from&date_to (+ company_balance_kop в ответе),
      GET /api/admin/payouts?status=requested, POST /api/admin/payouts/
      {id}/confirm (guard balance ≥ amount — иначе 409, заявка остается),
      GET /api/admin/disputes?status=open, POST /api/admin/disputes/{id}/
      resolve {resolution: release|refund, comment обязателен},
      PUT /api/admin/instructors/{id}/commission (0–100, целые),
      GET /api/admin/commissions?year=YYYY (инструктор × SUM fee за год;
      дефолт текущий год).
      Готовность: test_s16_backend.py — фильтры журнала (тип/роль/юзер/
      период), confirm создает payout-транзакцию и списывает balance
      (ровно одна — NFR-35), confirm при недостатке — 409 без списания;
      resolve release/refund закрывает спор (частичный UNIQUE);
      commissions?year — агрегат посевных релизов, год без данных —
      нулевые строки инструкторов (факт 0 — FR-114/115).
      FR: FR-108/109/112/113/114/115. NFR: NFR-33/34/35. Зависит от: 16.1.2.

## 16.3 Холд-интеграция в бронирование (после 16.1; не ждет 16.2)

- [ ] 16.3.1 [code] backend/student/booking.py: create_booking — в ОДНОЙ
      BEGIN IMMEDIATE после существующих проверок: чтение
      instructors.price_per_hour_rub парного инструктора; цена NULL →
      легаси-путь 1:1 (холда нет); цена задана → снапшот в брони +
      hold_amount_kop (цена×100×часы слота, floor до целого часа);
      available < hold → ROLLBACK + 402 {ok:false, error, need_kop,
      available_kop} (бронь НЕ создана); иначе INSERT booking (снапшот) +
      INSERT transactions hold (частичный UNIQUE — гонка проигравшего →
      честный отказ). reject_booking/cancel_booking — refund в той же
      транзакции ТОЛЬКО ДО СТАРТА занятия: перед ветками смены статуса
      (cancel_booking booking.py:737 / reject_booking booking.py:772 —
      сейчас guard только по статусу) код-гвард now < start_time
      экземпляра, иначе 409 {ok:false, error:"Занятие началось"} БЕЗ
      смены статуса и БЕЗ refund (МАЖ-1: refund после старта невозможен —
      исходы холда после старта: complete→release, спор оператора,
      timeout-defrost; деньги не теряются ни в одной ветке); refund-гвард:
      hold_amount_kop>0 и отсутствия refund — идемпотентно.
      complete-эндпоинт POST
      /api/instructor/bookings/{id}/complete (confirmed→completed,
      экземпляр начался: instance_start ≤ now_moscow; completed_at).
      dispute-эндпоинт POST /api/student/bookings/{id}/dispute
      (≤24ч от completed_at, комментарий обязателен, открытый спор — 409;
      код-гвард «живой холд» (МАЖ-2): hold_amount_kop>0 и нет
      release/refund по брони — иначе 422 «спор только по
      тарифицированным броням»; брони с price NULL спора не открывают).
      Свип в точках чтения ДОПОЛНЯЕТСЯ timeout-defrost: брони new/
      confirmed с hold_amount_kop>0, чей экземпляр начался ≥72ч назад,
      без отметки «проведена» и без refund → REFUND ученику (холд не
      висит вечно; MIN-1).
      Отображение: статусы/холды в my_bookings/instructor_bookings
      (легаси-поля без удаления).
      Готовность: test_s16_hold_booking.py — полный цикл design
      «Конечные автоматы»: бронь с ценой→hold (available−/frozen+),
      402 без записи брони, reject→refund, cancel→refund, complete→
      свип до 24ч — релиза НЕТ, после 24ч (заморозка часов/подстановка
      now) — release с gross/fee/net (10% и 0% — «факт 0»), спор в окне
      → свип НЕ релизит → resolve release/refund оператором; МАЖ-гварды:
      cancel/reject ПОСЛЕ старта — 409 «Занятие началось» (статус и холд
      не изменены, refund нет), спор по брони без холда (price NULL) —
      422, timeout-defrost: confirmed-бронь со стартом ≥72ч назад без
      complete → REFUND при свипе (повторный свип без дубля — частичный
      UNIQUE); КОНТРОЛЬ:
      ПОЛНЫЙ прогон tests/api/test_s5_backend.py (27) — зелен БЕЗ ПРАВОК
      (цены NULL в фикстурах); прогон e2e кабинет-кластера
      (test_ui_playwright TC-UI-019/025/026/027, BUG-049/052) — зелен.
      FR: FR-101/102/103/104/105/106/107. NFR: NFR-33/34/35.
      Зависит от: 16.1.2.

## 16.4 UI ученик/инструктор/админ (после 16.2; [P] с 16.3)

- [ ] 16.4.1 [code] cabinet ученика — раздел «Кошелек» (по мокапу
      wallet-student.html): snav + data-tab «Кошелек» (после «Мои брони»),
      #sec-wallet, хеш #/wallet; карточки Доступно/Заморожено/Всего;
      «Пополнить» — модал (ввод рублей → POST amount_kop ×100 —
      целочисленно; честные тосты ошибок); история транзакций (тип/дата/
      описание/сумма ±); попап брони #m-book — обработка 402
      («Недостаточно средств…» + кнопка «Пополнить кошелек» — переход в
      раздел). Существующие якоря/тексты не удаляются (TC-UI-019/059/060).
      Готовность: ручной смоук на dev-стенде против мокапа; e2e
      кабинет-кластер зелен (сценарии не правились).
      FR: FR-98/99/103. NFR: NFR-37. Зависит от: 16.2.1.

- [ ] 16.4.2 [code] instructor-dashboard — «Доходы» и цена часа (по мокапу
      instructor-earnings.html): nav «Доходы» + #sec-earnings; карточки
      Заработано за месяц (net)/Всего за месяц/Доступно к выводу/Комиссия;
      таблица «по ученикам за месяц»; блок «Цена часа» (input целые рубли
      → PUT, «Сохранить» с подтверждением о снятии действия на
      существующие холды — снапшоты); кнопка «Вывести деньги» — модал СБП
      (банк/телефон/сумма → POST payouts; 409 второй активной — честный
      тост); список своих выплат (бейджи заявка/выплачено); «Отметить
      проведенным» на начавшихся confirmed-брони (complete).
      Готовность: смоук против мокапа; негативы BUG-047-кластера e2e
      зелен («Доходы» вне негативного списка).
      FR: FR-100/105/110/111. NFR: NFR-37. Зависит от: 16.2.2.

- [ ] 16.4.3 [code] admin-dashboard — раздел «Транзакции» (по мокапу
      admin-transactions.html): nav «₽ Платежи» → «Транзакции» (soon()
      снят; e2e-якорей на «Платежи» нет — grep 0); #sec-transactions:
      карточка «Баланс компании» (company_balance_kop); фильтры журнала
      (тип/роль/юзер/даты) + таблица (id, дата, тип-бейдж, роль,
      пользователь, источник, сумма; textContent-only — XSS-правило);
      блок «Выплаты — заявки» (инструктор, сумма, банк, телефон,
      «Подтвердить» с confirm() — прецедент admin-диалогов) с честной
      обработкой 409-недостачи; блок «Споры» (бронь/ученик/инструктор/
      комментарий; «Выплатить инструктору»/«Вернуть ученику» — решение с
      обязательным комментарием, кнопка disabled до текста — прецедент
      BUG-046 deny); поле «Комиссия %» у инструктора (таблица
      инструкторов раздела — PUT, валидация 0–100); таблица «Комиссии
      инструкторов за год» + селектор года (дефолт текущий).
      password_hash в исходниках НЕ появляется.
      Готовность: смоук против мокапа; e2e admin-кластер зелен
      (TC-UI-006/011/013/014 без правок).
      FR: FR-108/109/112/113/114/115. NFR: NFR-37. Зависит от: 16.2.3.

## 16.5 Мокапы — приемка и вербатим-фиксация (после 16.4)
  - сверка-заметка (MIN-3 ревью): мокап «Доходы», реализация сохраняет имя таба «Доходы и выплаты» (якоря/BUG-051) — осознанное расхождение

- [ ] 16.5.1 [docs] мокапы wallet-student/instructor-earnings/
      admin-transactions созданы в коммите пакета СА (прецедент 1d40a46);
      задача: сверка инвариантов TC-UI-059/060 (логотип ✓ ОДИН на
      страницу, плитки без тегов «В КАБИНЕТЕ», крошек-дублей нет), сверка
      разметки мокап ↔ реализованные разделы (расхождения — правка
      РЕАЛИЗАЦИИ или мокапа по решению СА с фиксацией), приемка
      Заказчиком (скрины/ссылки), фиксация носителей для вербатим-сверок
      будущих версток (прецедент FR-9 test_cabinet_page).
      Готовность: контрольный grep мокапов (один .check на страницу);
      решение Заказчика зафиксировано.
      FR: FR-116. NFR: NFR-37. Зависит от: 16.4.1/16.4.2/16.4.3.

- [ ] 16.5.2 [docs] architecture/map.md — раздел «Компоненты» дополнен
      блоком «Экономика»: backend/wallet/ (домен), 5 новых таблиц
      (transactions, acquiring_topups, payouts, instructors,
      booking_disputes), эндпоинты контура (design «API-контур»), раздел
      админ-ки «Транзакции». Строка ADR-006 обновляется ТОЛЬКО 16.0.2
      (здесь НЕ дублируется). Карта — живой пос-принтный документ
      (прецедент s10: раздел «Компоненты» дополнялся каждым спринтом).
      Готовность: grep по map.md находит wallet-компоненты, таблицы
      экономики и раздел «Транзакции»; диаграмма/строки консистентны с
      фактом HEAD ветки.
      FR: —. NFR: —. Зависит от: 16.4.1/16.4.2/16.4.3.

## 16.6 Бюджеты, гарды и гейт партии (после всех)

- [ ] 16.6.1 [tests][infra] гарды денег: tests/api/test_qa_s16_money.py —
      source-inspection (прецедент test_qa_sprint1 NFR-002): (а) NFR-33 —
      в backend/wallet/**, backend/student/booking.py, backend/core/db.py
      нет float(/Decimal/round( и деления «/» над денежными величинами
      (только целые и //); (б) NFR-34 — нет `UPDATE transactions`/
      `DELETE FROM transactions` во всем backend/**; (в) NFR-36 — нет
      httpx/requests/urlopen в backend/wallet/** (моки без сети).
      Готовность: тест зелен на HEAD ветки; инварианты в docstring с
      трассировкой TC-S16-NNN (rule 6).
      FR: —. NFR: NFR-33/34/36. Зависит от: 16.2.1…16.3.1.

- [ ] 16.6.2 [infra][tests] ГЕЙТ: npm run build && npm run check:budgets —
      14 входов, пороги 150/200 КБ gzip БЕЗ ИЗМЕНЕНИЙ (чанки страниц
      выросли — замеры в отчете); check_tag_balance — без изменений
      (новых страниц нет — BUG-047); ПОЛНЫЙ pytest tests/ (после сборки
      dist) + полный e2e test_ui_playwright — зелен, 0 правок
      существующих сценариев (NFR-27; git diff тестов — только ДОБАВЛЕНИЕ
      новых кластеров и переработка test_container_contract);
      regress-final PASS с impact-анализом (зоны: booking/кабинеты/
      админка/контейнерный контракт); `openspec validate --all --strict`
      — 0 ✗; self-check состава: каждая дословная цитата Заказчика
      покрыта дельтой (proposal «Отслеживание» ↔ specs/).
      FR: FR-98…116. NFR: NFR-26/27/33…37. Зависит от: 16.0.2, 16.3.1,
      16.4.1…16.4.3, 16.5.1, 16.5.2, 16.6.1.

## Зависимости (волны)

- Волна 0: { 16.0.1 → 16.0.2 } и 16.1.1 — стартуют параллельно
  (гигиена MinIO независима от экономики).
- Волна 1: 16.1.2 (после 16.1.1).
- Волна 2: { 16.2.1, 16.2.2, 16.2.3 } (после 16.1.2; [P] между собой) и
  16.3.1 (после 16.1.2; не ждет 16.2.x).
- Волна 3: { 16.4.1, 16.4.2, 16.4.3 } (после 16.2.x; [P] между собой);
  16.5.1 и 16.5.2 — после 16.4.x.
- Волна 4: 16.6.1 (после денежных задач) → 16.6.2 (гейт, последним).

## Рекомендации к нарезке

- Швы: 16.2.1/16.2.2/16.2.3 — разные роутеры (файлово не пересекаются);
  16.4.x — разные Vue-страницы; backend/app.py — общая зона строк
  include_router: ТОЛЬКО 16.2.1 подключает wallet_router целиком
  (16.2.2/16.2.3 отдают роутеры в 16.2.1 или подключение одной строкой в
  16.2.3 — решить на сессии, НЕ править app.py из трех задач).
- НЕЛЬЗЯ делить: 16.3.1 (холд/refund/complete/dispute — один домен
  booking.py, атомарно); 16.0.1 (compose — один файл); 16.6.2 (гейт —
  одна сессия).
- Общая зона файлов: backend/core/db.py — только 16.1.1;
  backend/student/booking.py — только 16.3.1; backend/wallet/ledger.py +
  sweeps.py — только 16.1.2; tests/web/test_ui_playwright.py — только
  ДОБАВЛЕНИЕ новых кластеров (16.4.x не правят существующие сценарии);
  design/mocks/ — НИКЕМ после коммита пакета (16.5.1 — только сверка и
  приемка; правка мокапа — по решению СА с записью).

## План тестовых прогонов (наборы — отдельные делегации-раннеры)

1. **API/регресс**: `pytest tests/` (кроме playwright и
   test_container_contract) — стенд: репо, env-заглушки conftest; после
   16.3.1 — ОБЯЗАТЕЛЬНО с прогоном test_s5_backend (обратная
   совместимость холда).
2. **Контрактный**: `pytest tests/test_container_contract.py` — после
   16.0.2; локально без Docker (static checks).
3. **e2e полный**: `pytest tests/web/test_ui_playwright.py` — стенд:
   собранный dist (npm ci && npm run build ДО прогона), uvicorn на
   эфемерном порту, Chromium headless; после 16.4.x и на гейте 16.6.2.
4. **Валидации**: `openspec validate --all --strict` +
   `npm run check:budgets` + `git diff --stat` контроль границ —
   локально, секунды-минуты.
Прогоны 1 и 3 НЕ объединять в один сабагент-раннер (разные стенды);
сборка dist — один раз до прогонов 3 и 16.6.2.
