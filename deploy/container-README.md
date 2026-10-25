# Контейнерный деплой (docker compose) — Спринт 6, ADR-006

Альтернативный контур деплоя рядом с действующим bare-metal (systemd).
Код приложения один и тот же — режим задается окружением (FR-57),
`deploy/autoschool.service` и `deploy/nginx-autoschool.conf` не меняются.

> **Предупреждение INC-001:** не чинить рантайм мимо репозитория. Любой
> фикс конфига на машине — временный; источник истины — git. Починил на
> стенде — сразу заводи PR на источник (Dockerfile/compose/deploy/).

## Состав стека

```
Хост (наружу только 80/443)
  ▼
nginx  (nginx:1.29-trixie, pinned; TLS и конфиг — монтирования)
  │  сеть frontend
  ▼
app    (образ из Dockerfile: python:3.12-slim pinned, venv, non-root appuser)
  │  uvicorn backend.app:app, single-worker, HEALTHCHECK /api/health
  │  named volumes: db → /data/db (app.db), uploads → /data/uploads
  │  сеть backend
  ▼
minio  (pinned release-тег; S3-контур под задачу 6.3; 9000/9001 не публикуются)
```

## Где живут секреты и тома

- **Секреты** — только `.env` рядом с `docker-compose.yml` (вне git, вне
  контекста сборки — `.dockerignore` исключает `.env*`; INC-006). Обязательные
  для приложения: `ADMIN_USER`, `ADMIN_PASSWORD_HASH`, `SECRET` (см.
  `.env.example`). Для MinIO: `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` —
  **дефолтные minioadmin запрещены** (арх-ревью), задайте собственные.
  `TLS_DIR` — каталог хоста с `cert.pem`/`key.pem` (по умолчанию
  `./deploy/tls`), монтируется в nginx read-only, в образ не попадает.
- **Состояние** — named volumes `db`, `uploads`, `minio-data`. Переживают
  `compose down`/`up`; файлы на хосте принадлежат uid appuser — обслуживание
  тома требует root/docker (осознанное ограничение ADR-006).

## Оба режима деплоя

| | bare-metal (действующий) | compose (новый) |
|---|---|---|
| Приложение | systemd-юнит `deploy/autoschool.service`, .venv в репо, порт 8390 | контейнер `app`, внутренний порт 8390 |
| Прокси | host nginx, `deploy/nginx-autoschool.conf` | контейнер `nginx`, `deploy/container/nginx.conf` |
| БД / загрузки | `data/app.db`, `data/uploads/` в репо | named volumes `db`, `uploads` |
| Секреты | `.env` в каталоге репо | `.env` рядом с compose (отдельный файл!) |
| Сборка окружения | `.venv` (pip) | `docker compose build` |

Существующая БД bare-metal (`data/app.db`) при первом переходе НЕ переносится
автоматически: compose стартует с пустым томом, bare-metal данные остаются
нетронутыми (`data/` вне образа и контекста — `.dockerignore`). Схему на
пустом/старом томе доводит init_db через lifespan (FR-53, идемпотентно).

### Переключение bare-metal → compose

1. `sudo systemctl stop autoschool` — юнит держит порт 8390.
2. Остановить host nginx (держит 80/443): `sudo systemctl stop nginx`.
3. Подготовить `.env` рядом с compose (секреты) и TLS-каталог (`TLS_DIR`).
4. `docker compose up -d --build`.
5. Проверка: `docker compose ps` (app healthy), `curl -k https://127.0.0.1/api/health`,
   `ss -tlnp` — слушаются только 80/443.

Без шагов 1–2 `compose up` падает по конфликту портов 80/443/8390.

### Переключение compose → bare-metal (обратно)

1. `docker compose down` (данные томов сохраняются; `docker compose down -v`
   УДАЛЯЕТ тома — не использовать без намерения).
2. `sudo systemctl start nginx`; `sudo systemctl start autoschool`.
3. Проверка: `curl http://127.0.0.1:8390/api/health` и лендинг по https.

### Ручной перенос data/app.db в compose-том (опционально)

Автоматики нет (решение СА). При необходимости — до первого старта compose:

```
docker volume create autoschool_db
docker cp data/app.db autoschool_db:/data/db/app.db   # том пустой, владелец встанет по каталогу образа (appuser)
docker compose up -d   # init_db доводит схему
```

Загрузки: аналогично `docker cp data/uploads/. autoschool_uploads:/data/uploads`.
После переноса bare-metal-каталоги не используются и не изменяются.

## Тесты в контейнере (задача 3.1, MAJ-1)

Образ для тестов и поставки — ОДИН digest, отдельного test-образа нет.
`tests/` в образ не копируются — доставляются read-only монтированием
на время прогона:

```
scripts/container_test.sh
# эквивалентно:
docker compose run --rm \
  -e AUTOSCHOOL_DB_PATH=/tmp/test.db -e AUTOSCHOOL_UPLOADS_DIR=/tmp/uploads \
  -e ADMIN_USER=admin -e ADMIN_PASSWORD_HASH=x -e SECRET=container-test-secret \
  -v ./tests:/app/tests:ro \
  app python -m pytest /app/tests -q
```

Временная БД/загрузки — в `/tmp` контейнерной ФС, вне named volumes:
повторный прогон не зависит от состояния томов (NFR-17). На чистой машине
без `.env` скрипт создает временный и удаляет после прогона.

**e2e (playwright) остаются хостовыми** — контейнерный прогон покрывает
только backend-набор (playwright в образ не ставится, соответствующие тесты
скипаются `importorskip`). Тот же скрипт выполняет CI (job `docker-build`,
`.github/workflows/flow.yml`) — сборка на PR без пуша в registry.
