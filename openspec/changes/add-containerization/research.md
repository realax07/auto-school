# Research: add-containerization

Альтернативы ключевых техрешений (решения — design.md).

## 1. База образа: slim vs alpine vs full

- python:alpine — меньше, но bcrypt (C-расширение) тянет сборочные
  зависимости; риск колес. Отклонено.
- python:full — тяжелый, лишние пакеты в прод-образе. Отклонено.
- python:3.12-slim (pinned tag/digest) — совпадает с CI
  (.github/workflows: python-version 3.12) и systemd-рантаймом
  (.venv того же интерпретатора). ВЫБРАНО.

## 2. Зависимости: system pip vs .venv multi-stage

- pip install в system site-packages — просто, но(builder) мусор и
  несовместимо с политикой PEP 668 свежих debian-based slim. Отклонено.
- .venv в builder-этапе, перенос /opt/venv в runtime COPY --from —
  финальный образ без pip-кэшей и компиляторов; прямое наследование
  урока INC-001 («инфраструктура должна жить в проекте»). ВЫБРАНО.

## 3. Healthcheck: curl/wget vs python stdlib

- Устанавливать curl ради healthcheck — лишний пакет в прод-образе.
- python -c urllib-запрос к /api/health — интерпретатор уже в образе.
  ВЫБРАНО (NFR-13).

## 4. Хранение состояния: bind mounts vs named volumes

- Bind mounts на каталоги репо (data/) — работает, но связывает стенд с
  деревом репозитория и правами хоста (non-root в контейнере vs uid
  хоста). Отклонено для стека.
- Named volumes (db, uploads) — переживают down/up, не зависят от дерева
  репо; пути внутри контейнера переопределяются существующими env
  (AUTOSCHOOL_DB_PATH, AUTOSCHOOL_UPLOADS_DIR). ВЫБРАНО (NFR-15).

## 5. Сети compose: одна сеть vs сегментация

- Одна default-сеть — проще, но MinIO и nginx в одном сегменте с app.
- Две сети: frontend (nginx наружу) + backend (app ↔ MinIO); публикуются
  только 80/443 nginx. ВЫБРАНО (NFR-16).

## 6. MinIO сейчас vs вместе с S3-адаптером (задача 6.3)

- Отложить MinIO до адаптера — тогда стек поменяется дважды.
- Включить MinIO в стек сейчас (данные на named volume), адаптер файлов
  uploads.py — отдельная дельта; файловый интерфейс уже изолирован.
  ВЫБРАНО (план: 6.1 → 6.3).

## 7. Тесты: отдельный test-target образ vs тот же образ

- Multi-stage test-target с dev-зависимостями — второй артефакт, риск
  рассинхрона «тестировали не то, что поставляем».
- Один образ (в requirements.txt уже включены dev-зависимости pytest/
  httpx — объем мал), тесты прогоняются в нем же с временной БД;
  «тестировали ровно тот digest, что поставляем». ВЫБРАНО (FR-55).
  Pin версий requirements.txt — NFR-12, задача dev.

## 8. Bare-metal совместимость: правка юнита vs env-переключение

- Отдельная ветка конфигов/юнита для контейнеров — дублирование.
- Ноль изменений кода: оба режима настраиваются окружением (env-файл,
  переменные путей уже изолированы в config.py/db.py/uploads.py).
  ВЫБРАНО (FR-57).
