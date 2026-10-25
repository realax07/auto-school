# TC-ADD-004 — Данные переживают пересоздание контейнеров

- ID кейса: TC-ADD-004
- Источник: Requirement: Compose-стек app + nginx + MinIO
- Сценарий спеки: Scenario: Данные переживают пересоздание контейнеров
- Спека: openspec/changes/add-containerization/specs/containerization/spec.md (FR-52, NFR-15)
- Тип: позитивный
- Приоритет: Must

## Сценарий (GIVEN/WHEN/THEN)

- **GIVEN** поднятый стек, в котором создан пользователь и загружен файл
- **WHEN** выполняется `docker compose down` и затем `docker compose up`
- **THEN** записи БД и загруженные файлы доступны без восстановительных действий (named volumes db и uploads)

## Ожидаемый результат

записи БД и загруженные файлы доступны без восстановительных действий (named volumes db и uploads). Отклонение от THEN (иная формулировка статуса/содержимого) — дефект контейнера TC-ADD-004.

## Примечания

- Кейс утвержден на основе спек-дельты add-containerization; code-review пакета —
  code-reviews/add-containerization/review-001.md (вердикт по находкам F-1..F-7).
- Runtime-прогон (docker build / compose up) выполняется на Docker-стенде (задача 5.1);
  статический контракт проверяет tests/test_container_contract.py (TC-ADD-трассировка).
