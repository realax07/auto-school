# Архитектурное ревью change-пакета add-containerization (Спринт 6)

## Вердикт: needs-rework (итерация 1) → approve (итерация 2)

> Пакет спроектирован добротно: non-root с pre-created владельцем каталогов
> томов (§1.1), секреты полностью вне образа и контекста (§1.3), именованные
> тома db/uploads/minio-data + сегментация на две сети (§1.4), bare-metal
> systemd-режим сохраняется без единой правки кода — переключение окружением
> через существующую env-изоляцию config.py/db.py/uploads.py (§1.5), тесты
> «тот же digest, что поставляем» концептуально верны (§1.6). Однако найден
> 1 Major-противоречие внутри пакета: design.md исключает tests/ из образа
> (.dockerignore + список «НЕ копируются»), при этом FR-55/spec-сценарии и
> механика задач 3.1/4.1 требуют прогона pytest ВНУТРИ того же образа —
> в образе, куда tests/ не попали, прогон невозможен, а механизм доставки
> тестов (COPY или read-only mount при compose run) нигде не зафиксирован
> (MAJ-1). Правка локальная: одна строка решения в design.md + синхронизация
> tasks 1.1/3.1, подход контейнеризации не меняется. Возвращается СА,
> править за СА в этой сессии не стал (минимизация вмешательства в дизайн —
> по goal).

| Параметр | Значение |
|---|---|
| Ревьюер | Архитектор (изолированная сессия, Флоу 1, Спринт 6, роль маркера pm) |
| Дата | 2026-10-25 |
| Ревьюемый артефакт | openspec/changes/add-containerization/ — рабочее дерево, изменения НЕ закоммичены (proposal, research, design, specs/containerization, tasks) |
| Проверено по | docs/ba/requirements-containerization.md (УТВЕРЖДЕН PLAN, FR-51…FR-57, NFR-11…NFR-17, все Must), architecture/map.md (паттерны 1–15), architecture/adr/001…005 (ADR-005 последний), deploy/autoschool.service + deploy/nginx-autoschool.conf (текущий bare-metal), backend/config.py + db.py + uploads.py (env-изоляция: AUTOSCHOOL_DB_PATH, AUTOSCHOOL_UPLOADS_DIR, _require без дефолтов), backend/app.py (GET /api/health, init_db через lifespan), requirements.txt (сейчас fastapi/uvicorn/bcrypt/python-multipart/pytest/httpx — без версий), incidents.md INC-001/INC-006 |
| Валидации при ревью | `openspec validate add-containerization --strict` → valid; `openspec validate --all --strict` → 12 passed, 0 failed (реальные прогоны, дословный хвост в конце) |
| Blocker | 0 |
| Major | 1 (MAJ-1) |
| Minor | 4 (MIN-1…MIN-4) |

## 1. Целевые проверки (фокус ревью)

### 1.1 Non-root + pin версий (FR-51, NFR-11, NFR-12) — корректны

- Non-root: `RUN useradd --create-home appuser` + `USER appuser`; ключевая
  деталь design.md правильная и неочевидная — каталоги точек монтирования
  /data/db и /data/uploads создаются в образе с владельцем appuser, чтобы
  named volume при первом монтировании наследовал права каталога образа
  (иначе root-владелец на томе молча ломает non-root). Это ровно та ловушка,
  которая обычно всплывает на стенде в задаче 2.1 — здесь закрыта контрактом
  образа заранее. Готовность задачи 1.1 включает проверку `docker inspect
  USER` — верифицируемо.
- Pin версий: тег python:3.12-slim — согласован с CI (python-version 3.12) и
  systemd-рантаймом (.venv того же интерпретатора) — research.md §1,
  обоснованно; digest честно помечен как задача dev (буква NFR-12 «в идеале
  digest» не нарушена). Требование pin requirements.txt (сейчас версии
  отсутствуют — проверено по файлу) встроено в задачу 1.1 ПЕРЕД кодом, с
  правилом «версии фактически установленные в .venv» — контейнер совпадает с
  bare-metal рантаймом, что одновременно страхует FR-57. Образы nginx/minio —
  pinned в compose (задача 2.1). Замечаний нет.
- Multi-stage: venv в builder, `COPY --from=builder /opt/venv`, pip-cache не
  покидает builder — сценарий «Builder-артефакты не попадают в финальный
  образ» покрывает это инспекцией. CORRECT.

### 1.2 Healthcheck (FR-54, NFR-13) — корректен

- HEALTHCHECK в образе + healthcheck compose-сервиса — двойное покрытие по
  букве FR-54; nginx (depends_on app, condition: service_healthy) уже опирается
  на признак живости — соответствие намерению ТЗ («nginx и внешние
  оркестраторы могут опираться»).
- Средство проверки — python stdlib (urllib) из того же образа, curl не
  ставится — дословно NFR-13. Порт 8390 единый с systemd-юнитом — проверено
  по deploy/autoschool.service (ExecStart --port 8390): привычный порт, меньше
  сюрпризов при переключении режимов.
- Параметры HEALTHCHECK (interval/timeout/retries/start_period) контрактом не
  зафиксированы — для старта на большом томе start_period существенен, иначе
  init_db на холодном старте может надуть unhealthy до готовности. Деталь dev,
  но зафиксировать стоит — MIN-4.

### 1.3 Секреты вне образа (NFR-14, наследование INC-006/NFR-3) — корректно, полно

- .dockerignore: .env*, deploy/tls/, data/, .git, .venv, __pycache__,
  node_modules — секреты и состояние не попадают ни в контекст сборки, ни в
  слои; сценарий «Секреты не зашиты в образ» покрывает инспекцией и образа, и
  контекста. TLS — только монтирование файлов хоста (пути вне git через env).
- App: env_file .env, отсутствие обязательных переменных — явная ошибка старта
  через config.py `_require` (проверено по коду), не тихий дефолт. MinIO:
  MINIO_ROOT_USER/PASSWORD из env_file, дефолтные minioadmin запрещены
  комментарием в .env.example (design.md). Один .env на app и minio —
  допустимо: будущему S3-адаптеру (задача 6.3) ключи MinIO в app и нужны.
- Использование compose secrets (docker secrets) вместо env_file не
  требуется — буква NFR-14 разрешает env_file/секреты compose; chosen вариант
  проще и достаточен для одного узла. Замечаний нет.

### 1.4 Volumes + сети (FR-52, NFR-15, NFR-16) — корректны, с одним замечанием

- Именованные тома db/uploads/minio-data; пути в контейнере переопределяются
  СУЩЕСТВУЮЩИМИ env (AUTOSCHOOL_DB_PATH, AUTOSCHOOL_UPLOADS_DIR — проверено
  по db.py:187 и uploads.py:33) — новая механика не изобретается, сценарий
  «данные переживают down/up» верифицируем задачей 2.1. Bind mounts отклонены
  обоснованно (research.md §4: связка с деревом репо и uid хоста).
- Сети: frontend/backend, minio — только backend, порты app/minio не
  публикуются, наружу только 80/443 nginx — дословно NFR-16, сценарий
  `ss -tlnp` в готовности 2.1. НО: design.md внутренне противоречив —
  диаграмма контура ведет nginx→app по сети frontend (nginx в backend не
  нужен), а текст раздела compose подключает nginx «к обеим» сетям, что
  делает MinIO достижимым из nginx без необходимости — лишняя поверхность при
  заданной сегментации. Рекомендация: frontend = nginx+app, backend = app+minio;
  nginx в backend не включать — MIN-1.
- SQLite WAL на named volume — работоспособно (файл БД + wal-сегменты на одном
  томе), single-worker-инвариант наследуется (proposal: compose не вводит
  репликацию app) — рассуждение верное.

### 1.5 Обратная совместимость bare-metal (FR-57, INC-001) — корректна

- deploy/autoschool.service и deploy/nginx-autoschool.conf — без правок;
  код приложения не меняется: env-изоляции достаточно (проверено: config.py
  требует секреты из окружения без дефолтов; db.py/uploads.py берут пути из
  env с дефолтами, совместимыми с systemd-юнитом). Единственное отличие
  контейнера — bind 0.0.0.0 против 127.0.0.1 — задается аргументом CMD,
  не кодом. Прямое наследование урока INC-001 («инфраструктура — артефакт
  репозитория») и INC-006 зафиксировано в README-контракте (задача 2.1).
- Pin requirements.txt по «фактически установленным в .venv» гарантирует, что
  bare-metal рантайм от пина не сдвинется — продумано.
- НО: процедура переключения режимов не зафиксирована как обязательная часть
  контракта 2.1 — host nginx занимает 80/443 и systemd-юнит занимает 8390;
  `compose up` без их остановки упадет по конфликту портов. README должен
  описывать переключение в обе стороны (остановка юнита + host nginx → up;
  down → рестарт юнита) — MIN-2.

### 1.6 Тесты в контейнере (FR-55, NFR-17, FR-56) — концепт верен, доставка тестов не определена — MAJ-1

- Концепция «тестировали ровно тот digest, что поставляем» (research.md §7,
  отказ от отдельного test-target) — правильная и соответствует букве FR-55;
  dev-зависимости (pytest, httpx) уже в requirements.txt — отдельного
  test-слоя не нужно; изоляция прогона (временная БД /tmp/test.db вне named
  volumes) — дословно NFR-17; e2e остается хостовым — граница зафиксирована.
- CI (FR-56): build → прогон pytest внутри собранного образа, оба отказа
  (ломающий Dockerfile, падающий тест) покрывают два сценария спеки — полное.
- НО см. MAJ-1: design.md одновременно исключает tests/ из образа и требует
  `pytest tests/` внутри того же образа.

### 1.7 MinIO как будущее файловое хранилище — контур корректен

- MinIO в стеке сразу, S3-адаптер uploads.py — задача 6.3, отдельная дельта;
  загрузки продолжают работать на volume (сценарий «MinIO готов принимать
  данные, файлы пока на volume» фиксирует ровно это переходное состояние);
  консоль 9001 не публикуется, 9000 — только backend-сеть. Файловый интерфейс
  изолирован в uploads.py (проверено: AUTOSCHOOL_UPLOADS_DIR — единственная
  точка путей) — адаптер не потребует правок доменных модулей. Граница
  «дельта на задачу 6.3» чистая, замечаний нет.

## 2. Полнота пакета

| Условие | Статус |
|---|---|
| ТЗ УТВЕРЖДЕН (FR-51…FR-57, NFR-11…NFR-17, все Must; ОВ нет — объем утвержден составом Спринта 6) | ✓ |
| Каждое Must-требование покрыто Requirement дельты | ✓ (7 Requirements = 7 блоков трассировки proposal.md: образ, compose-стек, секреты/сети, init БД, healthcheck, тесты в контейнере, CI, bare-metal) |
| Каждый Requirement — ≥1 Scenario GIVEN/WHEN/THEN | ✓ (14 сценариев; негативные/инспекционные во всех доменах) |
| Модальность RFC 2119 осознанна | ✓ |
| Нет реализации в spec.md | ✓ (HEALTHCHECK-команды, имена сетей/томов, compose-структура — в design/tasks, не в spec.md) |
| research.md — альтернативы ключевых решений | ✓ (8 развилок, отклонения обоснованы) |
| tasks.md: атомарность, [P], зависимости | ✓ (общая зона requirements.txt — только 1.1; 2.1 неделима; интеграция 5.1 после всех; приемка 6.5) |
| Открытые вопросы ТЗ | ✓ (нет; спорные места сеть/порты/имена томов зафиксированы design.md) |
| Согласованность design ↔ tasks ↔ specs внутри пакета | ✗ — см. MAJ-1 (tests/), MIN-1 (сети) |

## 3. Major-замечания

### MAJ-1: tests/ исключены из образа, но FR-55 требует прогона pytest внутри того же образа — механизм доставки тестов не определен

Design.md (Dockerfile-контракт) прямо перечисляет: «копируются backend/,
frontend/, requirements.txt; НЕ копируются: .env, deploy/tls/, data/,
tests/». Tasks 1.1 повторяет этот контракт (venv + backend/ + frontend/,
.dockerignore без tests/, но и без COPY tests/). При этом: spec
«Тесты внутри контейнера на том же образе» — «GIVEN собранный образ WHEN
внутри контейнера ИЗ ЭТОГО ОБРАЗА выполняется pytest»; tasks 3.1 — «docker
compose run --rm app python -m pytest tests/» с требованием «тесты и
поставка — один digest (никакого отдельного test-образа)»; tasks 4.1 (CI) —
«прогон pytest внутри собранного образа». В образ, собранном по контракту
1.1, tests/ не попадают (в контекст они включены — .dockerignore их не
исключает, но COPY не делает), и ни design.md («решение ниже» в §Dockerfile
не содержит самого решения), ни tasks 3.1/4.1 не фиксируют, КАК тесты
доставляются в контейнер: COPY tests/ в образ (тогда это противоречит
собственному списку «НЕ копируются» и .dockerignore-контракту 1.1) или
read-only монтирование tests/ при прогоне (`compose run -v
./tests:/app/tests:ro`, тогда образ чист, но механику прогона и CI-шаг нужно
описать именно так). Достижимый исход без правки: задача 3.1 падает на
первом прогоне («pytest: tests/ не найден»), CI-контракт 4.1 невыполним как
написан. Требование к СА: выбрать и зафиксировать ОДИН механизм —
рекомендую read-only mount при compose run (образ остается прод-чистым —
тесты не в слоях, digest поставки не содержит исходников тестов, «тот же
образ» из FR-55 соблюдается буквально; монтированием управляет
scripts/container_test.sh, CI повторяет ту же команду) — либо COPY tests/ с
явной правкой списка «НЕ копируются» и .dockerignore. Синхронизировать:
design.md (§Dockerfile + §Тесты), tasks 1.1 (контракт образа), 3.1 (механика
прогона), 4.1 (CI-шаг). Сценарий спеки правки не требует — он фиксирует
наблюдаемое требование, а не механизм.

## 4. Minor-замечания

### MIN-1: nginx в сети backend — внутреннее противоречие design.md и лишняя достижимость MinIO
Диаграмма контура: nginx → (frontend) → app → (backend) → minio. Текст
раздела compose: «nginx подключен к обеим (нужен app), app — к backend и
frontend». «Нужен app» выполняется сетью frontend (nginx↔app); подключение
nginx к backend открывает MinIO (9000) и консоль (9001) с nginx-контейнера
без всякой необходимости — против духа NFR-16 при уже выбранной сегментации.
Одна строка в design.md: nginx — только frontend.

### MIN-2: процедура переключения режимов (порты 80/443/8390) не зафиксирована в контракте 2.1
Host nginx держит 80/443, systemd-юнит — 8390; compose-стеку нужны те же
80/443 (и не нужен 8390 наружу, но его держит юнит). `compose up` на живом
bare-metal-стенде упадет по конфликту портов — это первое, что случится при
реальном переключении, а README-контракт (задача 2.1) обязан описывать
переключение в обе стороны: остановка `deploy/autoschool.service` + host
nginx → `compose up`; обратный переход — `compose down` → рестарт юнита и
nginx, с проверкой сохранности данных на томах (данные Systemd-эры в
data/ и томов compose — РАЗНЫЕ хранилища: миграция данных bare-metal →
named volume при первом переключении не описана вовсе). Зафиксировать в
README + одну строку в design.md (включая судьбу существующей data/app.db
при переходе: ручная инициализация тома или старт с пустой БД — решение СА).

### MIN-3: сценарий unhealthy недостижим в заявленной формулировке
Спека: «GIVEN процесс uvicorn внутри контейнера ЗАВЕРШЕН АВАРИЙНО WHEN
healthcheck отрабатывает THEN статус становится unhealthy». При CMD
python -m uvicorn завершение процесса = завершение контейнера (PID 1) —
docker покажет exited + сработает restart: unless-stopped, но не unhealthy
(unhealthy — статус работающего контейнера). Достижимый путь unhealthy —
зависание (блокировка event loop, соединение не отвечает → таймаут чека).
Переформулировать сценарий: «GIVEN приложение в контейнере не отвечает на
/api/health (зависание) …». Поведение верное, формулировка — нет.

### MIN-4: параметры HEALTHCHECK (start_period и пр.) не зафиксированы
interval/timeout/retries/start_period отдаются dev на усмотрение; для старта
на томе с накопленной БД init_db может превысить дефолтный window и надуть
unhealthy (с scenario зависит_on service_healthy это может остановить подъем
стека). Одна строка в tasks 1.1: задать start_period с запасом на init_db
(значение — за dev), остальное по умолчанию.

## 5. Пограничные вопросы к СА (списком)

1. MAJ-1: механизм доставки тестов в контейнер — read-only mount при
   compose run (рекомендовано: образ без тестов в слоях) или COPY tests/ в
   образ; синхронная правка design/tasks 1.1/3.1/4.1.
2. MIN-1: nginx — только сеть frontend.
3. MIN-2: процедура переключения режимов + судьба существующей data/app.db
   при первом переходе bare-metal → compose (перенос в том / старт с пустой).
4. MIN-3: переформулировка unhealthy-сценария на зависание.
5. MIN-4: start_period в контракте HEALTHCHECK (значение — за dev).

## 6. Влияние на архитектурную карту и ADR

- architecture/map.md дополнен этой сессией: паттерн 16 (контейнерный контур
  Спринта 6), новый раздел «Контейнерный контур» с диаграммой compose-стека,
  строка ADR-006 в таблице решений, обновлены статусы отложенных вопросов
  (паттерн 4 «сервисы в контейнерах» — реализован; оркестрация — compose
  выбран для сервисного контура, k8s/swarm — вне скоупа), раздел техдолга
  Спринта 6 (включая MAJ-1/MIN этого ревью до устранения).
- architecture/adr/006-containerization.md создан: контур compose
  app+nginx+MinIO (две сети, публикация только 80/443), named volumes
  db/uploads/minio-data, секреты — env_file/монтирования вне образов
  (наследование NFR-3/INC-006), переход bare-metal→compose без правок кода
  (env-изоляция, наследование INC-001), MinIO в стеке сразу — адаптер
  uploads.py отдельной дельтой (6.3). Статус «Принято» — ключевые решения
  от MAJ-1 не зависят (MAJ-1 лишь требует доопределить механику доставки
  тестов в уже выбранный контур; сам контур одобрен; прецедент — ADR-003/
  004/005), ссылка на ревью зафиксирована в шапке.
- Новых архитектурных механизмов уровня приложения пакет не вводит: код
  backend/ и frontend/ — без изменений (env-изоляция признана достаточной;
  точечный фикс жесткого пути с тестом — оговоренный в tasks.md исключение).
  Отступлений от ADR-001…005 нет (single-worker, статика тем же сервисом,
  in-memory сессии/токены, SQLite WAL — наследуются).

## 7. Валидации (дословный хвост, состояние пакета на момент ревью)

```
$ openspec validate add-containerization --strict
Change 'add-containerization' is valid
$ openspec validate --all --strict
- Validating...
✓ change/add-auth-cabinet
✓ change/add-booking-docs
✓ change/add-containerization
✓ change/add-instructor-cabinet
✓ change/add-instructor-flow
✓ change/add-registration-admin
✓ spec/instructor-availability
✓ spec/instructor-cars
✓ spec/instructor-documents
✓ spec/reviews
✓ spec/student-instructor-choice
✓ spec/student-requests
Totals: 12 passed, 0 failed (12 items)
```

## Итерация 2 (арх-ревью повтором, 2026-10-25)

> СА заявил закрытие всех замечаний итерации 1. Проверено каждое по
> фактическому дереву пакета (design.md, tasks.md, specs/containerization/spec.md
> — правки СА от 16:11). Все 5 замечаний закрыты по решениям итерации 1,
> нового архитектурного противоречия не внесено. Итог: **approve**.

| Замечание | Статус | Основание (проверено по файлам) |
|---|---|---|
| MAJ-1 (доставка тестов в контейнер) | **FIXED** | Выбран рекомендованный механизм — read-only mount при compose run: design.md §Dockerfile «РЕШЕНИЕ (MAJ-1)» (`-v ./tests:/app/tests:ro`, механика — scripts/container_test.sh, CI повторяет ту же команду); design.md §Тесты дублирует механику с изоляцией /tmp/test.db; tasks 1.1 — «tests/ в образ НЕ копируются (доставка — read-only монтирование, решение MAJ-1)»; tasks 3.1 — та же команда, «тесты и поставка — один digest»; tasks 4.1 — CI «той же командой, что задача 3.1». Все четыре точки синхронизации (design §Dockerfile + §Тесты, tasks 1.1/3.1/4.1) согласованы; spec-сценарий не тронут — как и требовалось (он фиксирует наблюдаемое требование, не механизм). «Тот же digest» FR-55 соблюдается буквально. |
| MIN-1 (nginx в backend) | **FIXED** | design.md §Сети: «nginx — ТОЛЬКО frontend (в backend не включается)»; контур-диаграмма ведет nginx→app только по frontend; tasks 2.1 — «nginx — только сеть frontend (не backend — MIN-1)». MinIO из nginx более не достижим, NFR-16 соблюден. |
| MIN-2 (переключение режимов) | **FIXED** | design.md §Обратная совместимость: процедура в ОБЕ стороны как обязательная часть контракта README 2.1 (остановка юнита + host nginx → up; down → рестарт), конфликт портов 80/443/8390 назван; судьба data/app.db решена СА: старт с ПУСТЫМ томом, bare-metal данные нетронуты, перенос — опциональная ручная процедура в README. Tasks 2.1 повторяет контракт дословно. |
| MIN-3 (недостижимый unhealthy) | **FIXED** | spec.md сценарий переформулирован: «GIVEN приложение в контейнере не отвечает на /api/health (зависание event loop, соединение не отвечает до таймаута проверки)» — достижимость unhealthy (таймаут чека на живом контейнере) восстановлена, поведение верное. |
| MIN-4 (HEALTHCHECK start_period) | **FIXED** | tasks 1.1: «HEALTHCHECK задает start_period с запасом на init_db при холодном старте на большом томе (значение — за dev, остальное по умолчанию; MIN-4)» — ровно формулировка итерации 1. |

Замечания нового уровня: не выявлено. Одно косметическое наблюдение вне
вердикта (не невязка, правка не требуется, но dev пусть учтет): в design.md
§Тесты строка про CI написана как «docker build → docker run», тогда как
нормативный контракт tasks 4.1 и design §Dockerfile («CI повторяет ту же
команду») однозначно фиксирует compose run с read-only монтированием —
NFR-17 «одна и та же механика локально и в CI» контрактом 4.1 выполняется;
формулировку §Тесты можно привести к единому виду при удобстве.

Итог итерации 2: MAJ-1 FIXED, MIN-1…MIN-4 FIXED, новых Blocker/Major/Minor
нет. Вердикт: **approve**. Пакет готов к реализации (задачи 1.1–5.2), ADR-006
и паттерн 16 map.md остаются в силе без правок.

Валидации итерации 2 (дословный хвост, PATH: $(npm prefix -g)/bin):

```
$ openspec validate add-containerization --strict
Change 'add-containerization' is valid
$ openspec validate --all --strict
- Validating...
✓ change/add-auth-cabinet
✓ change/add-booking-docs
✓ change/add-containerization
✓ change/add-instructor-cabinet
✓ change/add-instructor-flow
✓ change/add-registration-admin
✓ spec/instructor-availability
✓ spec/instructor-cars
✓ spec/instructor-documents
✓ spec/reviews
✓ spec/student-instructor-choice
✓ spec/student-requests
Totals: 12 passed, 0 failed (12 items)
```
