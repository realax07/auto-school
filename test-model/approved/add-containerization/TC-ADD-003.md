# TC-ADD-003 — Версии зафиксированы

- ID кейса: TC-ADD-003
- Источник: Requirement: Образ приложения
- Сценарий спеки: Scenario: Версии зафиксированы
- Спека: openspec/changes/add-containerization/specs/containerization/spec.md (FR-51, NFR-11, NFR-12)
- Тип: позитивный
- Приоритет: Must

## Сценарий (GIVEN/WHEN/THEN)

- **GIVEN** Dockerfile и requirements.txt изменены вне задачи
- **WHEN** выполняется повторная сборка без изменения зафиксированных входов
- **THEN** базовый образ, версии зависимостей и версии образов nginx/MinIO берутся из зафиксированных значений, а не из плавающих тегов

## Ожидаемый результат

базовый образ, версии зависимостей и версии образов nginx/MinIO берутся из зафиксированных значений, а не из плавающих тегов. Отклонение от THEN (иная формулировка статуса/содержимого) — дефект контейнера TC-ADD-003.

## Примечания

- Кейс утвержден на основе спек-дельты add-containerization; code-review пакета —
  code-reviews/add-containerization/review-001.md (вердикт по находкам F-1..F-7).
- Runtime-прогон (docker build / compose up) выполняется на Docker-стенде (задача 5.1);
  статический контракт проверяет tests/test_container_contract.py (TC-ADD-трассировка).
