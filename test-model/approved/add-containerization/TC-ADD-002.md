# TC-ADD-002 — Builder-артефакты не попадают в финальный образ

- ID кейса: TC-ADD-002
- Источник: Requirement: Образ приложения
- Сценарий спеки: Scenario: Builder-артефакты не попадают в финальный образ
- Спека: openspec/changes/add-containerization/specs/containerization/spec.md (FR-51, NFR-11, NFR-12)
- Тип: позитивный
- Приоритет: Must

## Сценарий (GIVEN/WHEN/THEN)

- **GIVEN** образ собран через multi-stage (builder-этап с pip-кэшами и venv)
- **WHEN** финальный образ инспектируется
- **THEN** в нем нет артефактов builder-этапа (кэши pip, компиляторы), а виртуальное окружение с зависимостями присутствует

## Ожидаемый результат

в нем нет артефактов builder-этапа (кэши pip, компиляторы), а виртуальное окружение с зависимостями присутствует. Отклонение от THEN (иная формулировка статуса/содержимого) — дефект контейнера TC-ADD-002.

## Примечания

- Кейс утвержден на основе спек-дельты add-containerization; code-review пакета —
  code-reviews/add-containerization/review-001.md (вердикт по находкам F-1..F-7).
- Runtime-прогон (docker build / compose up) выполняется на Docker-стенде (задача 5.1);
  статический контракт проверяет tests/test_container_contract.py (TC-ADD-трассировка).
