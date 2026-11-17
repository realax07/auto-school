# Change: add-code-domain-folders

## Why (Зачем)

Спринт 13 — решение Заказчика 2026-11-08 (decisions/2026-11-08-sprint13-go.md,
telegram:144324141, дословно: «Пока оставим. ДАвай причешем папки с кодом
фронта и бека. Сейчас сплошняком лежат модули, давай их на сервисы разобьем
(папки)»). Прод-контур остается монолитом (app+nginx; разрезание сервисов —
Релиз 1, отложено): партия — ЧИСТАЯ перекладка кода в доменные папки, без
изменения поведения, контрактов API и БД. Паттерн 3 «модульность без
фанатизма» (sdd.md), директива 2026-10-16 «модульная структура».

Ценность партии = структура кода; риск = сломанные импорты/пути. Поэтому
ядро работы — ПОЛНАЯ инвентаризация ссылок до переноса (design.md, таблицы
«Инвентарь ссылок» по классам: механические импорты, string-needle,
веб-пути, нетронутые).

## What Changes (Что меняет)

- **backend/**: 20 модулей из плоского дерева → доменные пакеты
  `core/` (инфраструктура), `auth/`, `instructor/`, `student/`,
  `policy/`. Точка входа НЕ переносится: `backend/app.py` и
  `backend/__init__.py` остаются на месте (uvicorn `backend.app:app`,
  `create_app()` — без изменений: Dockerfile CMD, compose,
  deploy/autoschool.service, scripts/run_dev.sh не правятся).
  Выбранное дерево — ПЛОСКИЕ доменные пакеты под `backend/` (без
  вложенного `domains/`): минимальная глубина импортов и симметрия с
  `frontend/js/{shared,student,instructor,admin}` — обоснование и
  отклоненная альтернатива в design.md «Выбор дерева».
- **frontend/js/**: 8 из 10 ES-модулей → контурные папки `shared/`,
  `student/`, `instructor/`, `admin/`; публичные гостевые модули
  `instructors.js` (лендинг /instructors) и `policy.js` (страница
  /policy) остаются в корне js/ (правило «потребитель страницы» —
  design.md «Выбор дерева js»). Мигрированные на Vue страницы
  (frontend/vue/src/pages/) — НЕ трогаются (ADR-008).
- **Раздача /js/**: единственная содержательная правка кода — хендлер
  в `backend/app.py` расширяется до `/js/{filepath:path}` (сейчас
  `{filename}` односегментный и пути с «/» заведомо 404), с сохранением
  существующих проверок обхода каталогов и content-type. Контракт
  отдачи статики (те же файлы, `application/javascript`) не меняется.
- **Тестовая инфраструктура — только механические правки путей**:
  импорт-строки (61 строка в 20 тестовых файлах), пути чтения
  ИСХОДНИКОВ модулей в статических NFR-инспекциях (17 литералов в 4
  файлах), string-target `monkeypatch.setattr("backend.instructors.db",
  …)` (1), резолв относительных импортов в хелпере
  `tests/conftest.py::frontend_source()` (regex не следует `'../…'` —
  design.md «frontend_source при подпапках»). Сценарии тестов НЕ
  меняются (NFR-27, прецедент s11/s12).
- **specs/**: дельта ADDED в новую кейпабилити `codebase-structure`
  («Доменная организация кода») — по контракту 7 change-пакет несет
  дельты; структура кода фиксируется как требование с MUST-сценариями
  «импорты/точки входа/сборка работают».

## Что НЕ меняет (границы)

- Поведение, контракты API (openapi), схема БД, single-worker,
  localStorage-ключи, маршруты страниц, редиректы — БЕЗ ИЗМЕНЕНИЙ.
- Тесты остаются на своих местах (tests/api, tests/unit, tests/web,
  test_container_contract.py) — правятся только импорт-строки/пути
  чтения исходников; docstring-упоминания старых путей не трогаются.
- Dockerfile (CMD/COPY), docker-compose.yml, deploy/autoschool.service,
  deploy/RUNBOOK.md, scripts/run_dev.sh, CI (.github/workflows) — без
  правок (design.md «Нетронутые ссылки»).
- scripts/flow_preflight.py (PAGES_REL backend/app/pages.py —
  legacy-путь, файла нет и до пакета, чек молчит),
  scripts/smoke_static.py (glob backend/app/*.py матчит остающийся
  app.py), scripts/impact_rules.json (правило pages.py — legacy),
  scripts/check_auth_timing.py (legacy-утилита под дерево
  backend/app/<name>, вне CI) — НЕ трогаются.
- frontend/vue/** (каркас Vue, dist-входы) — не трогается; тесты,
  читающие Vue-исходники (test_login_modal, test_bug001, test_policy),
  пути не меняют (rglob/пути vue не затронуты).

## Отслеживание

- Решение Заказчика 2026-11-08 (decisions/2026-11-08-sprint13-go.md,
  состав Спринта 13 п.1–2, критерии приема) → tasks 1.1–3.4.
- Паттерн 3 «модульность без фанатизма», директива 2026-10-16 →
  proposal «Why», design «Выбор дерева».
- Дельта specs/codebase-structure/spec.md «Доменная организация кода»
  → tasks 1.1–3.4 (MUST-сценарии: импорты, точки входа, раздача /js/,
  сборка образа).
- Инвентарь ссылок (полные таблицы) → design.md «Инвентарь ссылок»
  (классы A/B/C/D).
