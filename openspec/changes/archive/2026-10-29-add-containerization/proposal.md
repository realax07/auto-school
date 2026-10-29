# Change: add-containerization

## Why (Зачем)

Спринт 6, Партия A (PLAN.md, задачи 6.1–6.5): контейнеризация. Сегодня
рантайм живет в общемашиночных окружениях и bare-metal systemd — INC-001
(рецидивирующий 502): обновление тулчейна сбросило python-окружение,
uvicorn «пропал», фикс потерялся в рантайм-копии юнита; INC-006 — секреты
в cp-цепочках деплой-скриптов. Окружение должно быть артефактом репозитория,
воспроизводимым одной командой, а не состоянием машины.

Источник требований: `docs/ba/requirements-containerization.md`
(УТВЕРЖДЕН PLAN: FR-51…FR-57, NFR-11…NFR-17, все Must; открытых
вопросов нет — объем утвержден составом Спринта 6).

## What Changes (Что меняет)

- Домен `containerization` (НОВЫЙ, ADDED):
  - Dockerfile: python-slim + multi-stage (.venv собирается в
    builder-этапе и переносится в финальный образ), запуск от non-root
    пользователя (FR-51, NFR-11), pin базового образа и зависимостей
    (NFR-12);
  - healthcheck по существующему GET /api/health — HEALTHCHECK в образе
    + healthcheck compose-сервиса, средствами python из образа (FR-54,
    NFR-13);
  - docker-compose: app + nginx (reverse proxy — эквивалент
    deploy/nginx-autoschool.conf, TLS-файлы монтируются) + MinIO
    (S3-совместимое хранилище — подготовка контура под задачу 6.3,
    адаптер uploads.py — отдельная дельта); именованные тома db/uploads;
    две сети (внешняя nginx, внутренняя app+MinIO); наружу — только
    80/443 (FR-52, NFR-14, NFR-15, NFR-16);
  - идемпотентная инициализация БД при старте контейнера —
    существующая init_db/lifespan, новая механика не изобретается
    (FR-53);
  - тесты ВНУТРИ контейнера на том же образе (pytest с временной БД) —
    одна механика локально и в CI (FR-55, NFR-17);
  - CI: job сборки образа + прогон тестов в контейнере на каждый PR
    (FR-56);
  - обратная совместимость: bare-metal systemd-деплой (deploy/)
    остается рабочим режимом, переключение режима — окружением
    (env-переменные AUTOSCHOOL_DB_PATH / AUTOSCHOOL_UPLOADS_DIR /
    env_file .env уже изолированы в коде), код приложения не меняется
    (FR-57).

Код доменной логики, API и фронтенд — БЕЗ ИЗМЕНЕНИЙ: контейнеризация не
меняет наблюдаемое поведение приложения.

## Impact (Последствия)

- Код: НОВЫЕ файлы `Dockerfile`, `.dockerignore`, `docker-compose.yml`
  (в корне репо; compose-файлы nginx/minio — через build-контекст и
  конфиги в `deploy/container/`), опциональный скрипт прогона тестов в
  контейнере (`scripts/container_test.sh`). Код backend/ и frontend/ —
  без изменений (ожидается, что env-изоляции достаточно; если dev
  вскроет жесткий путь — точечный фикс с тестом).
- CI: расширение `.github/workflows/flow.yml` — job build+test-in-container.
- Эксплуатация: второй поддерживаемый режим деплоя (compose) рядом с
  systemd; инструкции — `deploy/container-README.md`. Секреты — только
  через env_file/.env вне образа и вне git (наследование NFR-3, INC-006).
- Master-spec: домен `containerization` создается этой дельтой; остальные
  домены не меняются.
- ADR-006 (архитектор, задача 6.2): контур, volumes, secrets.
- sdd.md дополняется разделом «Спринт 6» (задача СА/приемки).

## Out of scope / допущения

- S3-адаптер uploads.py и перенос файлов в MinIO — задача 6.3, отдельная
  дельта (здесь MinIO только в стеке).
- Модульный JS — Партия B (slug modular-js), вне пакета.
- Продовый TLS, оркестрация (k8s/swarm), watchtower/внешний мониторинг —
  вне скоупа.
- Отказ от bare-metal: НЕ делаем — systemd-режим остается рабочим (FR-57).
- Допущение: один узел, single-worker uvicorn (наследованный инвариант) —
  compose не вводит репликацию app.

## Отслеживание

- FR-51, NFR-11, NFR-12 → specs/containerization/spec.md (ADDED «Образ
  приложения»).
- FR-52, NFR-14, NFR-15, NFR-16 → specs/containerization/spec.md
  (ADDED «Compose-стек app + nginx + MinIO»).
- FR-53 → specs/containerization/spec.md (ADDED «Идемпотентная
  инициализация БД при старте»).
- FR-54, NFR-13 → specs/containerization/spec.md (ADDED «Healthcheck»).
- FR-55, NFR-17 → specs/containerization/spec.md (ADDED «Тесты внутри
  контейнера»).
- FR-56 → specs/containerization/spec.md (ADDED «CI: сборка образа и
  тесты в контейнере»).
- FR-57 → specs/containerization/spec.md (ADDED «Обратная совместимость
  bare-metal»).
