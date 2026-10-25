# TC-ADD-010 — Здоровый контейнер сообщается healthy

- ID кейса: TC-ADD-010
- Источник: Requirement: Healthcheck по /api/health
- Сценарий спеки: Scenario: Здоровый контейнер сообщается healthy
- Спека: openspec/changes/add-containerization/specs/containerization/spec.md (FR-54, NFR-13)
- Тип: позитивный
- Приоритет: Must

## Сценарий (GIVEN/WHEN/THEN)

- **GIVEN** работающий контейнер app
- **WHEN** выполняется `docker compose ps` (или docker ps)
- **THEN** сервис app имеет статус healthy

## Ожидаемый результат

сервис app имеет статус healthy. Отклонение от THEN (иная формулировка статуса/содержимого) — дефект контейнера TC-ADD-010.

## Примечания

- Кейс утвержден на основе спек-дельты add-containerization; code-review пакета —
  code-reviews/add-containerization/review-001.md (вердикт по находкам F-1..F-7).
- Runtime-прогон (docker build / compose up) выполняется на Docker-стенде (задача 5.1);
  статический контракт проверяет tests/test_container_contract.py (TC-ADD-трассировка).
