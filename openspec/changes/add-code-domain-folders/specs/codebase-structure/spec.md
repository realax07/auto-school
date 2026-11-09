# Delta: codebase-structure

## ADDED Requirements

### Requirement: Доменная организация кода (backend + frontend/js)

Код продукта MUST быть организован в доменные папки: backend — плоские
доменные пакеты core/, auth/, instructor/, student/, policy/ под
backend/; frontend/js — контурные папки shared/, student/, instructor/,
admin/ (гостевые модули — в корне js/). Перекладка MUST быть чистой:
поведение, контракты API, схема БД, single-worker — без изменений.

Источник: decisions/2026-11-08-sprint13-go.md; паттерн 3; директива
2026-10-16.

#### Scenario: Все импорты работают после переноса

- **GIVEN** модули переложены в доменные папки по дереву design.md (инвентарь ссылок: 61 импорт-строка в backend/, 61 строка в 20 тестовых файлах, 18 string-needle)
- **WHEN** выполняется полный набор тестов `pytest tests/ -q` (зеркало CI) и импорт приложения `from backend.app import create_app`
- **THEN** все наборы (tests/unit, tests/api, tests/web, test_container_contract.py) зеленые без смысловых правок — изменены только импорт-строки и пути чтения исходников; графа импортов эквивалентна прежней (те же связи, новые пути)

#### Scenario: Тесты правятся только механически

- **GIVEN** перенос выполнен по волнообразному плану tasks.md (1 backend, 2 frontend/js, 3 regress/образ)
- **WHEN** анализируется дифф тестов относительно HEAD-before
- **THEN** правки ограничены классами: импорт-строки `backend.*`, литералы путей чтения исходников в NFR-инспекциях, строковый таргет monkeypatch, резолв в хелпере conftest frontend_source(); сценарии, needles, маркеры кейсов (TC-*) и GIVEN/WHEN/THEN — без изменений (NFR-27)

### Requirement: Стабильные точки входа и контракт раздачи /js/*

Точки входа MUST оставаться неизменными: uvicorn `backend.app:app`
(Dockerfile CMD, compose, systemd-юнит, run_dev.sh) и `create_app()`.
Раздача легаси-модулей `/js/*` MUST работать для корневых и вложенных
путей с прежним контрактом (content-type, 404 на обход каталога,
скрытые и неизвестные файлы).

Источник: decisions/2026-11-08-sprint13-go.md (критические ограничения).

#### Scenario: Точки входа стабильны

- **GIVEN** перенос выполнен
- **WHEN** проверяются Dockerfile CMD, docker-compose.yml, deploy/autoschool.service, scripts/run_dev.sh и вызов `uvicorn backend.app:app` (в т.ч. изолированный сервер e2e test_ui_playwright)
- **THEN** команды и цели не изменены (`backend.app:app`, `create_app()`); приложение стартует, `GET /api/health` отвечает 200 `{"ok": true}`; сборка образа (`docker compose build app`, scripts/container_test.sh) проходит, backend-набор зеленый внутри образа

#### Scenario: Раздача /js/* из подпапок эквивалентна прежней

- **GIVEN** ES-модули переложены в контурные папки, HTML-src обновлены (6 страниц), route расширен до `/js/{filepath:path}`
- **WHEN** запрашиваются модуль из подпапки (например /js/student/cabinet.js), корневой модуль (/js/policy.js), несуществующий путь и путь с обходом каталога (/js/../.env, /js/.hidden)
- **THEN** первые два отдаются 200 с `application/javascript`; неизвестный путь, обход каталога и скрытые файлы — 404; wiring-тесты (frontend_source: HTML + транзитивные ES-импорты, включая `../…` из подпапок) зеленые без изменения «единицы wiring»
