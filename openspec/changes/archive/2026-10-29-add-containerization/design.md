# Design: add-containerization

Источники решений: requirements-containerization.md (УТВЕРЖДЕН PLAN),
research.md (альтернативы 1–8), incidents.md INC-001/INC-006 (мотивация:
окружение — артефакт репозитория; секреты — вне образов и вне cp-цепочек),
deploy/ (текущий bare-metal: systemd-юнит + nginx, порт 8390, TLS
self-signed из deploy/tls/ — вне git), backend/config.py + db.py +
uploads.py (env-изоляция: AUTOSCHOOL_DB_PATH, AUTOSCHOOL_UPLOADS_DIR,
секреты только через env без дефолтов), backend/app.py (GET /api/health,
init_db через lifespan, статика из frontend/).

## Контур

```
Хост (публикуются только 80/443)
  ▼
nginx (контейнер; TLS-файлы монтируются, НЕ в образе)
  │  сеть frontend
  ▼
app (образ из Dockerfile: python-slim + .venv, non-root)
  │  uvicorn backend.app:app, single-worker (наследованный инвариант)
  │  HEALTHCHECK → GET /api/health
  │  named volume db     ← AUTOSCHOOL_DB_PATH=/data/db/app.db
  │  named volume uploads← AUTOSCHOOL_UPLOADS_DIR=/data/uploads
  │  сеть backend
  ▼
minio (S3-совместимое хранилище; порт НЕ публикуется наружу)
  │  named volume minio-data
  ▼  (адаптер uploads.py → S3 — задача 6.3, отдельная дельта;
      сейчас uploads работает на volume, MinIO в стеке «готов принимать»)
```

Bare-metal режим (без изменений): systemd-юнит + nginx хоста + .venv
в репо — продолжают работать; переключение режима — окружением, код
один и тот же (FR-57).

## Dockerfile (решения)

- Сборка multi-stage:
  - builder: база python:3.12-slim (pinned тег; digest — задача dev,
    NFR-12); `python -m venv /opt/venv`; `pip install -r
    requirements.txt` с включенным pip-cache в слое builder (в runtime
    не попадает). Требование задачи dev: pin версий requirements.txt
    (сейчас fastapi/uvicorn/bcrypt/python-multipart/pytest/httpx без
    версий).
  - runtime: та же база (pinned), `COPY --from=builder /opt/venv
    /opt/venv`, PATH через ENV; копируются backend/, frontend/,
    requirements.txt; НЕ копируются: .env, deploy/tls/, data/, tests/
    (см. .dockerignore — секреты вне образа, NFR-14). РЕШЕНИЕ (MAJ-1):
    тесты доставляются в контейнер read-only монтированием при прогоне —
    `docker compose run --rm -v ./tests:/app/tests:ro app …` (механика —
    scripts/container_test.sh, CI повторяет ту же команду); образ остается
    прод-чистым — тестов нет в слоях, digest поставки не содержит исходников
    тестов, «тот же образ» из FR-55 соблюдается буквально.
- Non-root (NFR-11): `RUN useradd --create-home appuser`; USER appuser;
  рабочая каталога /app; пути томов /data/db и /data/uploads создаются
  в образе с владельцем appuser (том при первом монтировании наследует
  права каталога образа — иначе root-владелец на томе ломает non-root).
- HEALTHCHECK (NFR-13): `HEALTHCHECK CMD python -c "import
  urllib.request,sys; sys.exit(0 if
  urllib.request.urlopen('http://127.0.0.1:8390/api/health',timeout=3).status==200
  else 1)"` — интерпретатор уже в образе, curl не ставится. Порт 8390 —
  тот же, что в systemd-юните (единый привычный порт).
- Команда: `python -m uvicorn backend.app:app --host 0.0.0.0 --port
  8390` (в контейнере bind 0.0.0.0 — в отличие от 127.0.0.1 в юните;
  наружу все равно выпускает только nginx). CMD в Dockerfile (не
  entrypoint-скрипт) — миграции выполняет lifespan/init_db (FR-53),
  отдельный entrypoint не вводится.

## docker-compose (решения)

- Сервисы:
  - `app`: build из Dockerfile; env_file: .env (секреты вне образа и
    вне git, NFR-14); environment: AUTOSCHOOL_DB_PATH=/data/db/app.db,
    AUTOSCHOOL_UPLOADS_DIR=/data/uploads; volumes: db→/data/db,
    uploads→/data/uploads; healthcheck (тот же python-ччек, что в
    образе); restart: unless-stopped; порты НЕ публикуются (nginx
    ходит по внутренней сети).
  - `nginx`: образ nginx (pinned версия); конфиг — монтирование
    deploy/container/nginx.conf (эквивалент deploy/nginx-autoschool.conf:
    80→301→443, TLS, proxy_pass на app:8390, X-Forwarded-*); TLS-файлы —
    монтирование каталога хоста (пути — env в .env, вне git — INC-006);
    ports: 80, 443; depends_on: app (condition: service_healthy).
  - `minio`: образ minio/minio (pinned версия); команда server
    /data --console-address ":9001"; environment: MINIO_ROOT_USER/
    MINIO_ROOT_PASSWORD — из env_file (вне образа; дефолтные
    minioadmin значения запрещены в .env.example-комментарии);
    volume minio-data→/data; порт 9000 не публикуется (сеть backend),
    9001 — не публикуется (консоль — по необходимости, задача 6.3).
- Сети: `frontend` (nginx, app), `backend` (app, minio); nginx — ТОЛЬКО
  frontend (MIN-1: в backend не включается — иначе MinIO 9000/9001
  достижим с nginx без необходимости); minio — только backend (NFR-16).
- Версионирование compose: файл без deprecated `version:` ключа
  (compose spec v2).

## Инициализация БД при старте (FR-53)

Новая механика НЕ вводится: backend/app.py уже выполняет init_db через
lifespan при старте uvicorn; миграции db.py idempotent (механика
users.role, расширения Спринта 5). Контейнер получает volume с существующей
БД — старт доводит схему и не портит данные. Проверка idempotency на
перезапуске — задача dev (см. tasks.md).

## Тесты внутри контейнера (FR-55, NFR-17)

- Один и тот же образ для тестов и поставки (research.md п.7);
  dev-зависимости (pytest, httpx) уже в requirements.txt.
- Механика прогона: `docker compose run --rm -v ./tests:/app/tests:ro
  app python -m pytest tests/ -q` — тесты попадают в контейнер только
  read-only монтированием на время прогона (в образе их нет — решение
  MAJ-1 в §Dockerfile); с переопределением environment:
  AUTOSCHOOL_DB_PATH=/tmp/test.db
  (временная БД в контейнерной ФС, вне named volumes — изоляция от
  состояния, NFR-17) и AUTOSCHOOL_UPLOADS_DIR=/tmp/uploads; e2e (playwright)
  остаются вне контейнера (хостовые, как сейчас) — прогон в контейнере
  покрывает backend-набор; это фиксируется в deploy/container-README.md
  и scripts/container_test.sh.
- CI (FR-56): job в .github/workflows/flow.yml — docker build →
  docker run (pytest внутри, временные пути) на каждый PR; failure
  красит PR. Node-часть (flow_check и пр.) остается в существующем job.

## Обратная совместимость (FR-57)

- deploy/autoschool.service и deploy/nginx-autoschool.conf — без правок.
- Код приложения не меняется: достаточно существующей env-изоляции
  (config.py требует секреты из окружения; db.py/uploads.py берут пути
  из env). Единственное известное отличие контейнера — bind 0.0.0.0 —
  задается аргументом CMD, не кодом.
- deploy/container-README.md: оба режима, переключение, где живут
  секреты/тома; предупреждение INC-001 (не чинить рантайм мимо репо).
- Переключение режимов (MIN-2, обязательная часть контракта README 2.1):
  bare-metal → compose — остановить deploy/autoschool.service (держит
  8390) и host nginx (держит 80/443), затем `compose up`; обратный
  переход — `compose down`, рестарт юнита и host nginx; без остановки
  `compose up` падает по конфликту портов.
- Судьба существующей data/app.db при первом переходе (решение СА):
  compose стартует с ПУСТЫМ named volume db — автоматический перенос не
  выполняется; существующая БД bare-metal в data/ остается нетронутой
  (data/ вне образа и контекста — .dockerignore); при необходимости
  переноса — ручная опциональная процедура в README (копирование app.db
  в том до первого старта: `docker volume create … && docker cp` или
  `docker compose run` с bind-монтированием); init_db доводит схему
  (FR-53, задача 2.2).

## Безопасность (наследование NFR-3, INC-006)

- .dockerignore: .env*, deploy/tls/, data/, .git, .venv, __pycache__,
  node_modules — секреты и состояние не попадают ни в контекст сборки,
  ни в слои.
- .env в git отсутствует (уже gitignored); compose читает env_file с
  хоста; отсутствие обязательных переменных — явная ошибка старта
  (config.py _require), не тихий дефолт.
- Контейнеры: non-root (app), MinIO — свой непривилегированный образ;
  публикация портов — только nginx 80/443.

## План тестовых прогонов (для ПМ)

| Набор | Где | Команда | Стенд | ~время |
|---|---|---|---|---|
| backend в контейнере | CI + локально | docker build → run pytest (временная БД) | Docker | ~3 мин |
| smoke compose | локально/стенд | compose up → curl https/health → down/up → данные целы | Docker | ~5 мин |
| полный хостовый pytest | как сейчас | pytest tests/ -q | bare-metal venv | ~1 мин |
| e2e (playwright) | как сейчас | вне контейнера | хост | как сейчас |

Планируется 3 отдельных запуска (контейнер-тесты, smoke, полный
хостовый) — по одному раннеру на набор.
