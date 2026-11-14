# Code Review: add-wallet-economy (review-001)

- Дата: 2026-11-14
- Ревьюер: code_reviewer (независимая сторона, AI Factory)
- Reviewer-Delegation: deleg-s16-dev-external
- Дифф: `git diff 1fa849b..bf0bd55` — ветка feat/s16-economy (6 dev-коммитов:
  fbb82fe 16.0 MinIO-чистка → bf0bd55 16.4–16.6 UI/бюджеты/карта; пакет СА
  4d55833/1f8c36c с мокапами и спеками — до диапазона, сверены на ветке)
- Scope: backend/wallet/** (новый домен), backend/student/booking.py,
  backend/core/db.py, backend/app.py, backend/auth/instructor_admin.py,
  frontend/vue (cabinet / instructor-dashboard / admin-dashboard + оболочки),
  tests/ (3 новых API-файла, контракт контейнера, e2e), MinIO-инвентарь,
  architecture/map.md, .env.example / flow.yml / container_test.sh / README /
  ADR-006 / BACKLOG.
- Волны в диффе: 1.0 (16.0 MinIO), 1.1 (16.1 домен/миграция), 1.2 (16.2 API),
  1.3 (16.3 холды в booking), 1.4–1.6 (16.4 UI, 16.5 мокапы-сверка,
  16.6 бюджеты/гарды/карта).

## Вердикт: approve

Деньги считаются правильно и только целочисленно, журнал append-only,
FSM холда соответствует design.md (включая спорные края МАЖ-1/МАЖ-2 и
гонки через BEGIN IMMEDIATE + частичные UNIQUE), балансы — только SUM,
гварды доступа повторяют семантику существующих эндпоинтов, единственная
правка старого API-теста — заявленная адаптация TC-S8BE-009, и она
легитимна. Находки: 3 MIN (см. ниже), блокирующих нет.

## Верификация (что реально прогонялось)

| Проверка | Результат |
|---|---|
| `pytest tests/ -q` (worktree, interpreter с pytest 9.1.1/fastapi 0.143.1) | **438 passed, 63 errors** — все 63 error = fixture `BrowserType.launch` в tests/web/test_ui_playwright.py: `libatk-1.0.so.0: cannot open shared object file` (в этом окружении нет системных библиотек chromium, sudo недоступен). 438+63 = **501 collected** — точно совпадает с заявленными «501 passed» у dev (у него браузер работал). Из 501: 389 backend/contract — **все passed** здесь; web: 49 non-browser passed, 63 browser — ошибка окружения (запуск браузера) |
| `pytest tests/web/ --collect-only` | 112 items — совпадает с «tests/web = 112»; test_ui_playwright: 76 items (73 базовых + 3 новых функции), остальные web-файлы не тронуты |
| `npm run build && npm run check:budgets` | OK: бюджеты NFR-26 соблюдены (страниц: **14**), пороги без изменений; чанки: cabinet 11.5, admin-dashboard 13.4, instructor-dashboard 25.5, shared 25.2 КБ gzip |
| `python3 scripts/check_tag_balance.py` | все входы OK |
| `openspec validate --all --strict` | **25 passed, 0 failed** |
| `git diff 1fa849b..bf0bd55 -- tests/` — правки старых тестов | ТОЛЬКО: test_s8_backend.py (TC-S8BE-009, см. ниже), test_container_contract.py (4 minio-точки — заявлено design-инвентарем 16.0), test_ui_playwright.py (**0 удаленных строк** — только дополнение; NFR-27 соблюден) |
| grep `UPDATE trans…` / `DELETE[ ]FROM[ ]transactions` по backend/ | 0 вхождений (NFR-34); `float(` / `round(` в backend/wallet — 0; `Decimal` — только слово в докстринге ledger.py:7 (код чист) |
| grep `minio` вне исторических носителей | чисто: compose/README/map/BA-доки/CI/env/container_test.sh/BACKLOG-п.4 вычищены; остаются только PLAN.md (итоги Спринта 6 — исторический), openspec/specs/containerization/spec.md (до архива не трогается — правка через дельту, дельта в пакете есть), ADR-006 (только статусная приписка, история не переписана), BACKLOG п.4-инцидент 2026-10-30 (историческая запись), негативный текст теста-гарда |
| Математика release (независимый пересчет) | `net = gross×(100−c)//100`, `fee = gross−net`: c=10 @ gross 123456 → net 111110/fee 12346, conservation fee+net=gross ✓; c=0 → (0,gross), c=100 → (gross,0) ✓; gross 101 @ c=33 → fee 34/net 67 — хвост платформе ✓; gross=0 → (0,0) (и недостижимо: CHECK amount_kop>0 + все исполнители требуют hold>0) |

## Приоритет 1 — математика release и NFR-33

`backend/wallet/ledger.py::release_gross_split` — ровно формула design
(floor, хвост платформе, факт 0 при c=0). Комиссия берется на момент
релиза (текущее instructors.commission_percent) — в свипе и в
admin_dispute_resolve, историческая восстанавливаема из строки release
(gross/fee/net в одной транзакции). hold_amount_kop = цена×100×часы,
часы floor целыми минутами (`hours_between`), тест-покрытие крайних
случаев: c=0/10/100, floor 2.5ч→2ч, цена 999₽/0₽ (TC-S16-008/009).
Гард test_qa_s16_money (float/Decimal/round/деление «/» по коду без
докстрингов и строк) зелен; сам гард зоной денег покрывает wallet/**,
booking.py, db.py — по design. Float во фронте отсутствует: показ ₽ —
целые `(a-(a%100))/100` (cabinet App.vue `rubFmt`, instructor `ernRub`).

## Приоритет 2 — FSM vs design.md

- refund СТРОГО до старта: cancel/reject — гвард
  `instance_start(...) <= now_moscow()` → 409 «Занятие началось» ДО
  веток смены статуса и refund (booking.py:890/943); строгая граница
  `now < start` совпадает с design.
- Спор только при живом холде (МАЖ-2): create_dispute требует
  status='completed' + окно ≤24ч от completed_at + hold_amount_kop>0 +
  `_hold_alive` (нет release/refund в журнале); price NULL → 422;
  открытый спор → 409 + частичный UNIQUE uq_disputes_open страхует
  гонку (booking.py:1052-1105).
- complete → авто-релиз 24ч ленивым свипом; complete запрещен при
  исполненном холде (409 БЕЗ смены статуса — иначе релиз создал бы
  деньги из ничего; тест TC-S16-040-а); completed_at =
  datetime('now')-формат, свип сравнивает строково тем же форматом UTC.
- timeout-defrost 72ч: new/confirmed + холд + instance_start (МСК→UTC
  явно) ≤ NOW−72ч + нет открытого спора + нет исхода → REFUND (свип-2).
- Идемпотентность: release/refund/payout/hold — частичные UNIQUE на
  бронь/заявку ( проигравший → IntegrityError → честный 409 / no-op в
  свипе); topup — X-Idempotency-Key: частичный UNIQUE uq_topups_idem +
  предпроверка внутри BEGIN IMMEDIATE, гонка повторов → победитель
  вставил, проигравший возвращает результат первого (NFR-35 ✓).
- payout confirm-guard: balance ≥ amount ИНАЧЕ 409, заявка ОСТАЕТСЯ
  requested, списания нет (admin_transactions.py:253-268) — по design.
- Гонка спор-vs-свип: create_dispute, resolve, свип — все BEGIN
  IMMEDIATE (single-writer SQLite сериализует); тест TC-S16-040-в
  имитирует победившего исполнителя прямой вставкой → resolve
  проигравшего → 409 «Холд уже исполнен».
- Разрывы FSM нет: из completed нет выхода (cancel/reject → 409 по
  статусу или МАЖ-1), спор не открывается после исполнения холда
  (422/409), свип исключает брони с любым исходом И с открытым спором.

## Приоритет 3 — целостность ledger

Балансы только SUM по transactions (student_balances / instructor_balances /
company_balance) — колонок-счетчиков нет; UPDATE/DELETE по журналу в
backend отсутствуют (grep + гвард). Отрицательные балансы недостижимы:
402 при нехватке ДО INSERT брони/холда (CREATE откатывается —
{ok:false, error, need_kop, available_kop}, тест TC-S16-031);
payout-суммы ≤ balance на момент confirm; release/refund = ровно
hold_amount_kop той же брони (пишутся атомарно в одной транзакции,
потом не мутируются) → frozen не уходит в минус; CHECK-контракты
журнала (type/amount>0/payout-status) в схеме. Компенсирующая механика
единственная — refund. Замечание вне дефекта: индексов под агрегаты
(student_id/instructor_id + type) нет — соответствует design (только
idx_tx_user/idx_tx_booking), на MVP-масштабах не проблема.

## Приоритет 4 — гварды доступа

/api/wallet* — require_role(student) по X-Session-Token; владельца
параметром не выбрать (user_id только из сессии) — чужой кошелек
недоступен по построению + тест s16_wallet_isolation_between_students.
/api/instructor/* — require_role(instructor); payouts/earnings — только
свои строки (WHERE instructor_id = сессия). /api/admin/* — require_admin
(X-Admin-Token) с телом 401 {ok:false} — паттерн 1:1 существующего
admin_users (backend/auth/admin.py:76-80); 403-семантика ученик/
инструктор — require_role, тела {ok:false} — механика guards.py Спринта 3
без изменений. Сlosures/инъекций нет: SQL параметризован везде
(единственные f-строки — имена фильтров из белых списков, значения — ?).

## Приоритет 5 — адаптация TC-S8BE-009: ЛЕГИТИМНА

Политика МАЖ-1 (Спринт 16) запрещает reject прошлой брони — старый кейс
создавал rejected-бронь прошлого экземпляра (iso(-5)) и ожидал 200.
Адаптация 79e6ee7: отклоняемая бронь переведена на БУДУЩИЙ экземпляр
(iso(3)) с сохранением семантики счетчиков «Мои ученики», плюс
УСИЛЕНИЕ негативом — reject начавшегося экземпляра → 409 «Занятие
началось», статус не меняется. Это ЕДИНСТВЕННАЯ правка старого
API-теста (git diff tests/ — test_s8_backend.py 24 строки; остальное —
новые файлы и заявленная переработка test_container_contract;
test_ui_playwright — только добавление, 0 удаленных строк). Считаю
адаптацию обоснованной и минимальной.

## Приоритет 6 — UI/мокапы

- Все три раздела на местах с якорями: #sec-wallet (cabinet App.vue +
  оболочка), #sec-earnings (instructor-dashboard), #sec-transactions
  (admin-dashboard); в мокапах те же якоря присутствуют; «₽ Платежи»
  soon() снят, e2e-якорей «Платежи» нет (TC-UI-062 проверяет
  отрицание).
- TC-UI-059/060: негативы BUG-047-кластера не задеты (правки кабинета —
  добавление таба после «Мои брони» и секций/модалок; существующие
  позитивные якоря не удалялись); в новых мокапах тегов «В КАБИНЕТЕ»
  нет, логотип один на страницу (grep).
- Ошибки API — тосты/инлайн-блоки, не alert: 402 брони — честный блок
  «Недостаточно средств» с need/available и кнопкой «Пополнить кошелек»
  внутри открытого модала (модал НЕ закрывается); 409/422 — toast с
  текстом сервера; resolve-модал оператора — кнопки disabled без
  комментария. confirm() только на payout-подтверждении оператора — это
  СУЩЕСТВУЮЩАЯ конвенция админки («Одобрить заявку?», e2e-якорь), не
  голый alert об ошибке.
- Входные HTML-консистентны с другими входами (wal-/ern-/tx- префиксы
  классов в стилях страниц, бюджеты 14 входов не изменились, build зелен).

## Приоритет 7 — 16.0 MinIO: полнота

Инвентарь design выполнен весь: compose (сервис+volume+сеть backend
удалены, комментарии переписаны), контракт ×4 (services=={app,nginx}+
volumes/networks, негатив «minio отсутствует» + запрет вхождений,
dockerfile-пин без minio, CI без dummy-env шага), flow.yml,
container_test.sh, .env.example (ОБА блока, включая pre-existing дубль
CHANGE_ME_*), container-README, requirements-containerization (FR-52/
NFR-14/16 переписаны под факт с датой), map (строка 16 + диаграмма +
ADR-строка + MIN-1 «ЗАКРЫТО 16.0»), ADR-006 — только приписка,
BACKLOG «add-wallet-economics»→«add-wallet-economy» (ровно одна строка).
Исторические носители (PLAN, spec до архива, инцидент BACKLOG) не
тронуты — по плану.

## Приоритет 8 — карта

Блок «Экономика 16.1–16.4» факт-точен: 5 таблиц и их роль, холд-цикл
(снапшот → refund до старта/409 → complete → 24ч релиз / 72ч defrost,
ленивый свип, single-worker), формула floor с комиссией на момент
релиза, price NULL = вне экономики, эндпоинты /api/wallet*,
/api/instructor/economy*, /api/admin/transactions* с носителями токенов,
UI-разделы. Строка 16/ADR-таблица — факт удаления MinIO с датой.

## Приоритет 9 — миграция booking_new

Пересоздание по прецеденту ADR-010: INSERT…SELECT переносит ВСЕ строки
с id/created_at/decided_at (ссылки журнала на booking_id валидны),
легаси-строки получают price NULL/hold 0/completed_at NULL (вне
экономики, легаси-путь 1:1 — тест TC-S16-041); guard по отсутствию
hold_amount_kop — идемпотентно (тест повторного старта); индексы
пересоздаются, uq_booking_active_slot — по-прежнему new/confirmed БЕЗ
completed. Бэкфилл instructors INSERT OR IGNORE из users (role=
'instructor') — идемпотентен, кастомные комиссии не перезаписывает;
точка создания строки при approve — в той же транзакции одобрения
(instructor_admin.py). Тесты TC-S16-001/002/003/006 зеленые.

## Находки

### MIN-1 · UX-wiring · инструкторский дашборд: демо-кнопки «Все операции ↗» и «Мои доходы и выплаты» не открывают новый реальный раздел

frontend/vue/src/pages/instructor-dashboard/App.vue:118 и :126 (и
дублирующий статический слой frontend/vue/instructor-dashboard.html:97
и :105) вызывают `navTo('Доходы')`, тогда как реальный раздел после
16.4.2 — таб «Доходы и выплаты» (navTo сравнивает точное имя,
App.vue:554). Клик меняет только заголовок — секция #sec-earnings не
открывается. Поведение НЕ регрессия (до спринта кнопка на демо-панели
вела так же в никуда), но теперь у кнопки появился реальный адресат.
Фикс — одна константа имени в 4 точках (или алиас в navTo).

### MIN-2 · отчетная точность · commit bf0bd55 «e2e +39 кейсов»

Фактическая декомпозиция: +3 pytest-функции (TC-UI-061/062/063; файл
73→76 items, tests/web целиком 109→112 items, что и подтверждает
«tests/web = 112»); «+39» — это assert-уровень (~36 expect/assert в
новых функциях + сами функции). Кейсы качественные и только
добавленные (NFR-27 соблюден, 0 удаленных строк), но в отчетных
числах партии декомпозицию стоит писать явно.

### MIN-3 · мокап-сверка · подпись нав-раздела инструктора

Мокап design/mocks/instructor-earnings.html — пункт нав «Доходы»
(design.md: «nav с „Доходы“ active»); реализация сознательно сохраняет
существовавшее до спринта имя таба «Доходы и выплаты» (демо-таб с этим
именем был якорем; переименование задело бы существующие якоря —
прецедент BUG-051 о переименованиях). Решение правомерное, но слово в
слово мокап и разметка расходятся — зафиксировать в 16.5-сверке
(носитель вербатим-сверки), чтобы будущий grep-контроль не счел это
расхождением.

## Ограничения ревью

Браузерные e2e (63 items) в этом окружении не исполняемы: chromium
headless-shell не стартует (нет libatk и соседних библиотек, sudo
недоступен) — по ним верифицированы: сборка dist, бюджеты,
tag-balance, сбор коллекций (112) и то, что правки — только
дополнения; рантайм-результат «e2e зелен» принят по прогону dev
(438+63=501 — число сходится поэлементно). Docker/compose-прогоны
16.0 (runtime) — статические + контрактные тесты (зеленые);
 digest nginx не верифицировался (без registry).

## Итог

Деньги: формулы/журнал/гонки/гварды — соответствуют design и СА-решениям,
критические пути покрыты тестами (миграция, уники, 402, МАЖ-1/МАЖ-2,
defrost, идемпотентность, изоляция кошельков, confirm-guard). Старые
контракты не сломаны (легаси price NULL 1:1, s5/cabinet-кластеры без
правок). Находки MIN-1…MIN-3 не блокируют слияние; MIN-1 желательно
закрыть малым фиксом в этой же ветке.
