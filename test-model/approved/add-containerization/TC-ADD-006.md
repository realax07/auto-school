# TC-ADD-006 — Наружу публикуются только порты nginx

- ID кейса: TC-ADD-006
- Источник: Requirement: Секреты вне образа и сегментация сетей
- Сценарий спеки: Scenario: Наружу публикуются только порты nginx
- Спека: openspec/changes/add-containerization/specs/containerization/spec.md (NFR-14, NFR-16)
- Тип: позитивный
- Приоритет: Must

## Сценарий (GIVEN/WHEN/THEN)

- **GIVEN** стек поднят
- **WHEN** просматриваются публикуемые порты хоста
- **THEN** слушаются только порты nginx (80/443); порты app и MinIO не публикуются и доступны только внутри сетей стека

## Ожидаемый результат

слушаются только порты nginx (80/443); порты app и MinIO не публикуются и доступны только внутри сетей стека. Отклонение от THEN (иная формулировка статуса/содержимого) — дефект контейнера TC-ADD-006.

## Примечания

- Кейс утвержден на основе спек-дельты add-containerization; code-review пакета —
  code-reviews/add-containerization/review-001.md (вердикт по находкам F-1..F-7).
- Runtime-прогон (docker build / compose up) выполняется на Docker-стенде (задача 5.1);
  статический контракт проверяет tests/test_container_contract.py (TC-ADD-трассировка).
