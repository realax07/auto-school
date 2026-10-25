# TC-ADD-014 — Падающий тест красит PR

- ID кейса: TC-ADD-014
- Источник: Requirement: CI собирает образ и гоняет тесты в контейнере
- Сценарий спеки: Scenario: Падающий тест красит PR
- Спека: openspec/changes/add-containerization/specs/containerization/spec.md (FR-56)
- Тип: негативный
- Приоритет: Must

## Сценарий (GIVEN/WHEN/THEN)

- **GIVEN** pull request с падающим тестом
- **WHEN** CI завершает прогон тестов внутри собранного образа
- **THEN** статус проверки — ошибка

## Ожидаемый результат

статус проверки — ошибка. Отклонение от THEN (иная формулировка статуса/содержимого) — дефект контейнера TC-ADD-014.

## Примечания

- Кейс утвержден на основе спек-дельты add-containerization; code-review пакета —
  code-reviews/add-containerization/review-001.md (вердикт по находкам F-1..F-7).
- Runtime-прогон (docker build / compose up) выполняется на Docker-стенде (задача 5.1);
  статический контракт проверяет tests/test_container_contract.py (TC-ADD-трассировка).
