# TC-ADD-015 — Ломающий Dockerfile красит PR

- ID кейса: TC-ADD-015
- Источник: Requirement: CI собирает образ и гоняет тесты в контейнере
- Сценарий спеки: Scenario: Ломающий Dockerfile красит PR
- Спека: openspec/changes/add-containerization/specs/containerization/spec.md (FR-56)
- Тип: негативный
- Приоритет: Must

## Сценарий (GIVEN/WHEN/THEN)

- **GIVEN** pull request с Dockerfile, сборка которого падает
- **WHEN** CI выполняет job сборки образа
- **THEN** статус проверки — ошибка

## Ожидаемый результат

статус проверки — ошибка. Отклонение от THEN (иная формулировка статуса/содержимого) — дефект контейнера TC-ADD-015.

## Примечания

- Кейс утвержден на основе спек-дельты add-containerization; code-review пакета —
  code-reviews/add-containerization/review-001.md (вердикт по находкам F-1..F-7).
- Runtime-прогон (docker build / compose up) выполняется на Docker-стенде (задача 5.1);
  статический контракт проверяет tests/test_container_contract.py (TC-ADD-трассировка).
