# TC-ADD-016 — systemd-деплой продолжает работать

- ID кейса: TC-ADD-016
- Источник: Requirement: Обратная совместимость bare-metal-деплоя
- Сценарий спеки: Scenario: systemd-деплой продолжает работать
- Спека: openspec/changes/add-containerization/specs/containerization/spec.md (FR-57)
- Тип: позитивный
- Приоритет: Must

## Сценарий (GIVEN/WHEN/THEN)

- **GIVEN** машина с существующим bare-metal systemd-деплоем
- **WHEN** выполняются pull репозитория и рестарт сервиса
- **THEN** сервис работает как раньше без правок кода приложения

## Ожидаемый результат

сервис работает как раньше без правок кода приложения. Отклонение от THEN (иная формулировка статуса/содержимого) — дефект контейнера TC-ADD-016.

## Примечания

- Кейс утвержден на основе спек-дельты add-containerization; code-review пакета —
  code-reviews/add-containerization/review-001.md (вердикт по находкам F-1..F-7).
- Runtime-прогон (docker build / compose up) выполняется на Docker-стенде (задача 5.1);
  статический контракт проверяет tests/test_container_contract.py (TC-ADD-трассировка).
