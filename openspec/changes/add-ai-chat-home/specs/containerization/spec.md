# Delta: containerization

## REMOVED Requirements

### Requirement: Compose-стек из двух сервисов (app + nginx)

**ПРИЧИНА УДАЛЕНИЯ (решение Заказчика 2026-11-21: внешний инференс
«ГигаЧата» — «отдельным сервисом с конфигом», модель строго
glm-5.3-flash)**: в стек добавляется сервис ai-bridge (GLM-инференс
ассистента, внутренняя сеть, без публикации портов, конфиг с ключом —
вне репо), требование «ровно двух сервисов» утрачивает силу.
Заменяющее требование — «Compose-стек app + nginx + ai-bridge»
(ADDED ниже). Запрет MinIO сохраняется в новом требовании дословно.

## ADDED Requirements

### Requirement: Compose-стек app + nginx + ai-bridge

Репозиторий MUST содержать docker-compose-стек из ТРЁХ сервисов: app,
nginx (как в ред. 16.0) и ai-bridge — внутренний сервис GLM-инференса
ассистента «ГигаЧат» (без публикации портов, только сеть frontend;
конфиг с ключом монтируется :ro и gitignored). Данные БД и загрузок —
на именованных томах (db, uploads). Сервисов minio и тома minio-data
в стеке быть не должно.

#### Scenario: Данные переживают пересоздание контейнеров

- **GIVEN** поднятый стек, в котором создан пользователь и загружен файл
- **WHEN** выполняется `docker compose down` и затем `docker compose up`
- **THEN** записи БД и загруженные файлы доступны без восстановительных действий (named volumes db и uploads)

#### Scenario: Сервисы стека — {app, nginx, ai-bridge}, без MinIO

- **GIVEN** docker-compose.yml репозитория
- **WHEN** перечислены сервисы, volumes и сети
- **THEN** services = {app, nginx, ai-bridge} (ровно); сервиса minio и volume minio-data нет; у ai-bridge нет секции ports; `docker compose config` валиден
