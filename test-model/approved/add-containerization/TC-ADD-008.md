# TC-ADD-008 — Старт на томе с БД предыдущей версии

- ID кейса: TC-ADD-008
- Источник: Requirement: Идемпотентная инициализация БД при старте
- Сценарий спеки: Scenario: Старт на томе с БД предыдущей версии
- Спека: openspec/changes/add-containerization/specs/containerization/spec.md (FR-53)
- Тип: позитивный
- Приоритет: Must

## Сценарий (GIVEN/WHEN/THEN)

- **GIVEN** named volume с БД, созданной предыдущим состоянием кода
- **WHEN** контейнер app стартует
- **THEN** схема доводится до актуальной, данные целы

## Ожидаемый результат

схема доводится до актуальной, данные целы. Отклонение от THEN (иная формулировка статуса/содержимого) — дефект контейнера TC-ADD-008.

## Примечания

- Кейс утвержден на основе спек-дельты add-containerization; code-review пакета —
  code-reviews/add-containerization/review-001.md (вердикт по находкам F-1..F-7).
- Runtime-прогон (docker build / compose up) выполняется на Docker-стенде (задача 5.1);
  статический контракт проверяет tests/test_container_contract.py (TC-ADD-трассировка).
