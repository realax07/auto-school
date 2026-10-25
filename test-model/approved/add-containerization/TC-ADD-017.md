# TC-ADD-017 — Переключение на контейнерный режим без правок кода

- ID кейса: TC-ADD-017
- Источник: Requirement: Обратная совместимость bare-metal-деплоя
- Сценарий спеки: Scenario: Переключение на контейнерный режим без правок кода
- Спека: openspec/changes/add-containerization/specs/containerization/spec.md (FR-57)
- Тип: позитивный
- Приоритет: Must

## Сценарий (GIVEN/WHEN/THEN)

- **GIVEN** принято решение поднять стенд через compose
- **WHEN** режим переключается
- **THEN** изменяются только окружение и конфигурации (env, compose, nginx-конфиг), код backend/ и frontend/ не меняется, оба режима описаны в документации репозитория

## Ожидаемый результат

изменяются только окружение и конфигурации (env, compose, nginx-конфиг), код backend/ и frontend/ не меняется, оба режима описаны в документации репозитория. Отклонение от THEN (иная формулировка статуса/содержимого) — дефект контейнера TC-ADD-017.

## Примечания

- Кейс утвержден на основе спек-дельты add-containerization; code-review пакета —
  code-reviews/add-containerization/review-001.md (вердикт по находкам F-1..F-7).
- Runtime-прогон (docker build / compose up) выполняется на Docker-стенде (задача 5.1);
  статический контракт проверяет tests/test_container_contract.py (TC-ADD-трассировка).
