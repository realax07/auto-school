# TC-ADD-013 — Тестируется ровно поставляемый digest

- ID кейса: TC-ADD-013
- Источник: Requirement: Тесты внутри контейнера на том же образе
- Сценарий спеки: Scenario: Тестируется ровно поставляемый digest
- Спека: openspec/changes/add-containerization/specs/containerization/spec.md (FR-55, NFR-17)
- Тип: позитивный
- Приоритет: Must

## Сценарий (GIVEN/WHEN/THEN)

- **GIVEN** образ собран и протестирован в контейнере
- **WHEN** стек поднимается тем же образом
- **THEN** используется тот же digest образа, на котором прогонялись тесты

## Ожидаемый результат

используется тот же digest образа, на котором прогонялись тесты. Отклонение от THEN (иная формулировка статуса/содержимого) — дефект контейнера TC-ADD-013.

## Примечания

- Кейс утвержден на основе спек-дельты add-containerization; code-review пакета —
  code-reviews/add-containerization/review-001.md (вердикт по находкам F-1..F-7).
- Runtime-прогон (docker build / compose up) выполняется на Docker-стенде (задача 5.1);
  статический контракт проверяет tests/test_container_contract.py (TC-ADD-трассировка).
