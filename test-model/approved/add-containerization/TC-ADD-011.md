# TC-ADD-011 — Зависание приложения переводит сервис в unhealthy

- ID кейса: TC-ADD-011
- Источник: Requirement: Healthcheck по /api/health
- Сценарий спеки: Scenario: Зависание приложения переводит сервис в unhealthy
- Спека: openspec/changes/add-containerization/specs/containerization/spec.md (FR-54, NFR-13)
- Тип: негативный
- Приоритет: Must

## Сценарий (GIVEN/WHEN/THEN)

- **GIVEN** приложение в контейнере не отвечает на /api/health (зависание event loop, соединение не отвечает до таймаута проверки)
- **WHEN** healthcheck отрабатывает по расписанию
- **THEN** статус сервиса становится unhealthy

## Ожидаемый результат

статус сервиса становится unhealthy. Отклонение от THEN (иная формулировка статуса/содержимого) — дефект контейнера TC-ADD-011.

## Примечания

- Кейс утвержден на основе спек-дельты add-containerization; code-review пакета —
  code-reviews/add-containerization/review-001.md (вердикт по находкам F-1..F-7).
- Runtime-прогон (docker build / compose up) выполняется на Docker-стенде (задача 5.1);
  статический контракт проверяет tests/test_container_contract.py (TC-ADD-трассировка).
