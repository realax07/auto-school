# Design: add-code-domain-folders

Чистая перекладка кода в доменные папки (решение Заказчика
2026-11-08, decisions/2026-11-08-sprint13-go.md): поведение, контракты
API, схема БД, single-worker — БЕЗ ИЗМЕНЕНИЙ. Ядро — полная
инвентаризация ссылок до переноса (таблицы ниже составлены grep-обходом
tests/, scripts/, backend/, frontend/, Dockerfile, compose,
deploy/*.service, *.md до правок).

## Impact

- Затронутые сервисы: монолит app (backend/ + frontend/js/); новых
  сервисов нет.
- Контракты: openapi-дельты НЕТ (эндпойнты, тела, коды — без изменений).
- Статика (static_v): IR-03 не применим — static_v-маркеров в репо нет
  (backend/app/pages.py не существует); раздача /js/* сохраняет файлы и
  content-type, добавляя подпапки.
- Deploy-матрица/RUNBOOK: без изменений (uvicorn backend.app:app,
  Dockerfile COPY backend/ backend/ накрывает новые подпапки
  автоматически — новых артефактов деплоя нет; откат = git revert).
- Миграции БД: нет.
- Тесты: правки ТОЛЬКО импорт-строки/пути чтения исходников/резолв
  helper (классы A/B/C, полные списки ниже); план прогонов — tasks
  волна 3 (полный pytest, regress, container_test.sh, e2e).

## Выбор дерева backend (решение)

Предварительное дерево задачи предполагало вложенный слой
`domains/` (`backend/domains/auth/…`). Проверка импортами и критерии
(минимальный дифф импортов, читаемость, симметрия с frontend/js) дают
ПЛОСКИЕ доменные пакеты под `backend/`:

- дифф импортов одинаков по числу строк (меняются все `backend.X`
  ссылки в обоих вариантах), но пути короче на сегмент
  (`backend.auth.auth` vs `backend.domains.auth.auth`);
- симметрия с фронтом: `frontend/js/{shared,student,instructor,admin}`
  ↔ `backend/{core,auth,instructor,student,policy}` — одинаковая
  конвенция «контур = одна папка» без служебного слоя;
- служебный слой `domains/` добавлял бы длину без группировки: в репо
  один продукт, домены не пересекаются с инфраструктурой иначе как
  через `core/`.

Корректировки предварительного дерева по фактическим файлам:
- модуль кабинета инструктора называется `dashboard.py` (не
  `instructor_dashboard.py`) — переносится в `instructor/` БЕЗ
  переименования (чистая перекладка, grep/docstring-совместимость);
- состав доменов подтвержден маршрутами (таблица ниже).

### Финальное дерево backend

```
backend/
  __init__.py                  # остается (пакет)
  app.py                       # ТОЧКА ВХОДА: create_app, роутеры,
                               # статика, health — не переносится;
                               # правятся только 17 импорт-строк
  core/                        # инфраструктура
    __init__.py                # новый (пустой)
    config.py  db.py  guards.py  uploads.py
  auth/                        # идентификация/регистрация/админка/модерация
    __init__.py                # новый (пустой)
    auth.py  register.py  admin.py  instructor_admin.py
    application_status.py
  instructor/                  # контур инструктора
    __init__.py                # новый (пустой)
    instructors.py  dashboard.py  instructor_cars.py
    instructor_documents.py  instructor_availability.py
    instructor_summary.py
  student/                     # контур ученика
    __init__.py                # новый (пустой)
    booking.py  student_marketplace.py  student_requests.py  reviews.py
  policy/                      # домен PersonalData
    __init__.py                # новый (пустой)
    policy.py
```

Обоснование доменов по маршрутам (grep @router):
- `auth/`: auth.py (/api/auth/*), register.py (/api/register),
  admin.py (/api/admin/login, /api/admin/users*),
  instructor_admin.py (/api/admin/instructor-applications* —
  административная модерация, require_admin из admin.py),
  application_status.py (/api/instructors/application-status,
  application-exchange — до-сессионный контур заявителя: poll статуса +
  обмен токена на X-Session-Token, auth-механика).
- `instructor/`: instructors.py (POST /api/instructors/apply — заявка
  инструктора), dashboard.py (GET /api/instructor/dashboard),
  instructor_cars/documents/availability/summary (/api/instructor/*).
- `student/`: booking.py (POST/GET /api/student/bookings + инструкторские
  confirm/cancel/reject — один цикл бронирования, инициатор ученик;
  кросс-доменные импорты instructor_availability/instructor_summary/
  student_requests → хелперы booking сохраняются как есть), 
  student_marketplace.py (/api/student/instructors*),
  student_requests.py (/api/student|instructor/requests*),
  reviews.py (POST /api/student/instructors/{id}/reviews).
- `policy/`: policy.py (GET /api/policy, домен PersonalData).
- `core/`: config.py, db.py, guards.py (роль-гварды поверх auth),
  uploads.py (MinIO/S3-загрузки) — импортируются всеми доменами.

### Финальное дерево frontend/js

Правило группировки — потребитель страницы (приватный контур против
публичной гостевой страницы):

```
frontend/js/
  shared/        api.js  utils.js
  student/       cabinet.js  instructor-choice.js
  instructor/    dashboard-instructor.js  instructor-cabinet-stub.js
  admin/         admin-dashboard.js  admin-login.js
  instructors.js # корень: лендинг /instructors (гостевой, до входа)
  policy.js      # корень: страница /policy (гостевая)
```

- `instructors.js` остается в корне, а не в `landing/`: папка ради
  одного модуля избыточна; правило «корень js/ = гостевые модули»
  покрывает оба файла (instructors.js, policy.js) и не спорит с
  контурными папками (кабинетные модули — приватные, session-gated).
- Альтернатива «все в `landing/`» отклонена: два файла в двух разных
  страницах (/instructors — лендинг инструкторов, /policy — ПД), общей
  единицы «landing» в терминах репо нет (лендинг ученика уже на Vue).

## frontend_source при подпапках (решение)

Хелпер `tests/conftest.py::frontend_source()` транзитивно собирает
HTML + подключенные ES-модули. Текущий regex
`src="(/js/[^"]+)"|from\s+'(\./[^']+)'`:
- группа 1 (`src="(/js/…)"`) матчит и многосегментные пути
  (`src="/js/student/cabinet.js"` — `[^"]+` поглощает «/») — HTML-src
  ссылки при подпапках читаются без правки regex;
- группа 2 требует литерально `./` — относительный импорт ИЗ ПОПАПКИ
  `from '../shared/api.js'` НЕ матчится (после кавычки `'..'` не
  удовлетворяет `\./`), т.е. транзитивный обход рвется; кроме того
  текущий резолв `rel = "js/" + ref.lstrip("./")` считает все `./`
  от корня js/, что для модуля в подпапке дает неверный путь.

Правка (механическая, класс C, ~10 строк внутри хелпера):
- regex группа 2 расширяется до `(\.{1,2}/[^']+)` (матчит `./…` и
  `../…`);
- резолв: `/js/…` — от корня frontend (как сейчас), `./…`/`../…` —
  `posixpath.normpath(dirname(модуля) + ref)` относительно папки
  импортирующего модуля. Двойные кавычки в импортах не вводятся
  (как и сейчас). Дедупликация `seen` и объединение источников — без
  изменений; все существующие вызовы frontend_source (7 файлов) и
  состав «единицы wiring» страницы — эквивалентны прежним.

## Раздача /js/* при подпапках (решение)

`backend/app.py`: `@app.get("/js/{filename}")` — односегментный
path-параметр (`/js/student/cabinet.js` не сматчится вовсе) плюс явный
гвард `if "/" in filename or filename.startswith("."): 404`. Правка
хендлера (единственная содержательная правка кода продукта):

```python
@app.get("/js/{filepath:path}")
def js_file(filepath: str):
    if filepath.startswith("/") or ".." in filepath.split("/") \
            or any(part.startswith(".") for part in filepath.split("/")):
        raise HTTPException(status_code=404)
    path = FRONTEND_DIR / "js" / filepath
    if not path.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(path, media_type="application/javascript")
```

Инварианты прежнего хендлера сохранены: обход каталога и скрытые
файлы — 404; неизвестный файл — 404; content-type
application/javascript явно; корневые модули (js/instructors.js,
js/policy.js) отдаются как прежде (обратная совместимость URL).

## Инвентарь ссылок (полный, до переноса)

Классы: **A** — механический ренейм импорт-строки Python; **B** —
string-needle (текстовые ссылки, резолвятся в рантайме/чтением
исходников); **C** — веб-пути (HTML src, ES-импорты, route,
тест-хелпер); **D** — проверено, нетронутое.

### D1. Перенос backend (20 модулей, класс A внутри backend/)

| Файл → новый путь | Потребители-импорты (правятся) |
|---|---|
| config.py → core/config.py | admin.py (import backend.config) |
| db.py → core/db.py | app.py + 15 модулей; тесты: 17 строк |
| guards.py → core/guards.py | booking, instructor_availability, instructor_cars, instructor_documents, instructor_summary, reviews, student_marketplace, student_requests; тесты: чтение исходника (класс B, s3) |
| uploads.py → core/uploads.py | instructor_admin, instructor_cars, instructor_documents, instructors; тесты: 5 строк |
| auth.py → auth/auth.py | app.py (router), application_status, dashboard, guards, instructor_cars; тесты: 16 строк (вкл. `from backend import auth` ×6); чтение исходника ×1 (qa_instructor_flow) |
| register.py → auth/register.py | app.py (router); тесты: 1 строка (register_mod; чтение исходника через inspect.getfile — путь-агностик) |
| admin.py → auth/admin.py | app.py (router), instructor_admin, instructor_cars, instructor_documents; тесты: 3 строки |
| instructor_admin.py → auth/instructor_admin.py | app.py (router); тесты: 1 строка + чтение исходника ×1 |
| application_status.py → auth/application_status.py | app.py (router); тестовых импортов нет |
| instructors.py → instructor/instructors.py | app.py (router); тесты: 3 строки + monkeypatch-string ×1 + чтение исходника ×1 |
| dashboard.py → instructor/dashboard.py | app.py (router); тесты: чтение исходника ×1 (test_instructor_dashboard:348) |
| instructor_cars.py → instructor/instructor_cars.py | app.py (router); чтения исходников ×2 (s3, s5) |
| instructor_documents.py → instructor/instructor_documents.py | app.py (router), instructor_cars; чтение исходника ×1 (s5) |
| instructor_availability.py → instructor/instructor_availability.py | app.py (router); тесты: 2 строки (`from backend.instructor_availability import …` unit + `import backend.instructor_availability as ia` s5); чтения исходников ×2 |
| instructor_summary.py → instructor/instructor_summary.py | app.py (router); чтения исходников ×2 (s3, s5) |
| booking.py → student/booking.py | app.py (router); тесты: 3 строки `from backend import booking as booking_domain` (s5/s8/s10); чтение исходника ×1 (s5) |
| student_marketplace.py → student/student_marketplace.py | app.py (router); чтение исходника ×1 (s3) |
| student_requests.py → student/student_requests.py | app.py (router); тесты: 1 строка (from backend.booking import local_today — учтено в booking); чтение исходника ×1 (s3) |
| reviews.py → student/reviews.py | app.py (router); чтение исходника ×1 (s3) |
| policy.py → policy/policy.py | app.py (router), instructors, register; тесты: 5 строк |

Новые файлы: 5 × `__init__.py` (пустые, docstring-заглушка домена).
app.py: 17 импорт-строк (16 router-импортов + `import backend.db as db`)
правятся; маршрут `/js/{filename}` → класс C (см. выше).

### D2. Правки импортов в тестах (класс A: 61 строка в 20 файлах)

| Тест-файл | Строк | Что меняется (модуль → новый путь) |
|---|---|---|
| tests/unit/test_unit_policy.py | 1 | backend.policy → backend.policy.policy |
| tests/unit/test_unit_availability.py | 1 | backend.instructor_availability → backend.instructor.instructor_availability |
| tests/api/test_s9_backend.py | 2 | instructors; db (backend.app-строка не трогается) |
| tests/api/test_admin.py | 1 | admin |
| tests/api/test_s5_backend.py | 4 | `from backend import booking`; db; uploads; instructor_availability |
| tests/api/test_policy.py | 6 | policy ×4; db ×2 |
| tests/api/test_instructors_apply.py | 2 | db; instructors |
| tests/api/test_register.py | 3 | admin; db; register |
| tests/api/test_auth_route.py | 3 | `from backend import auth`; AUTH_FAIL_MESSAGE ×2 |
| tests/api/test_s10_backend.py | 2 | `from backend import booking`; db |
| tests/api/test_auth.py | 9 | `from backend import auth` ×3; import auth ×5; auth_router ×1 (backend.app-строка не трогается) |
| tests/api/test_s3_backend.py | 2 | db ×2 |
| tests/api/test_s7_backend.py | 4 | db; uploads ×3 |
| tests/api/test_db.py | 1 | db |
| tests/api/test_instructor_dashboard.py | 1 | auth |
| tests/api/test_instructor_admin.py | 4 | db; admin; instructor_admin; instructors |
| tests/api/test_qa_instructor_flow.py | 5 | `from backend import auth`; db; auth ×3 |
| tests/api/test_s8_backend.py | 4 | `from backend import booking`; db ×2; uploads |
| tests/api/test_qa_sprint1.py | 4 | `from backend import auth`; auth ×3 |
| tests/web/test_bug001.py | 2 | db ×2 (backend.app-строка не трогается) |

Не правятся (функционально): `from backend.app import create_app`
(conftest:95, s9:631, auth:79, bug001:9, static:34) — app.py остается;
`uvicorn backend.app:app` (test_ui_playwright:218) — остается.

### D3. String-needle в тестах (класс B: 18 правок)

| Файл:строка | Ссылка | Правка |
|---|---|---|
| test_qa_instructor_flow.py:239 | `monkeypatch.setattr("backend.instructors.db", _RaceDB)` — строковый таргет резолвится в рантайме | `"backend.instructor.instructors.db"` |
| test_qa_instructor_flow.py:412–414 | чтение исходников: backend/instructors.py, backend/instructor_admin.py, backend/auth.py | backend/instructor/instructors.py, backend/auth/instructor_admin.py, backend/auth/auth.py |
| test_s5_backend.py:1573–1577 | «no sql concatenation»-инспекция читает ИСХОДНИКИ: booking.py, instructor_documents.py, instructor_cars.py, instructor_availability.py, instructor_summary.py | пути → student/booking.py, instructor/*.py |
| test_s3_backend.py:1674–1683 | та же инспекция: instructor_cars.py, instructor_availability.py, student_marketplace.py, reviews.py, student_requests.py, instructor_summary.py, guards.py, uploads.py | пути → instructor/*, student/*, core/guards.py, core/uploads.py |
| test_instructor_dashboard.py:348 | чтение исходника backend/dashboard.py (NFR-2 `WHERE id = ?`) | backend/instructor/dashboard.py |

Путь-агностичные (НЕ трогаются): test_register.py:496,
test_db.py:357, test_qa_sprint1.py:104 — читают исходник через
`Path(module.__file__)`; test_policy.py:276–282 — rglob по frontend/.

### D4. Веб-пути (класс C: 16 правок)

HTML `src="/js/…"` (6 правок, 2 страницы без правок):

| Страница | Было | Стало |
|---|---|---|
| admin-dashboard.html:373 | /js/admin-dashboard.js | /js/admin/admin-dashboard.js |
| admin-login.html:30 | /js/admin-login.js | /js/admin/admin-login.js |
| cabinet.html:384 | /js/cabinet.js | /js/student/cabinet.js |
| instructor-cabinet-stub.html:56 | /js/instructor-cabinet-stub.js | /js/instructor/instructor-cabinet-stub.js |
| instructor-choice.html:200 | /js/instructor-choice.js | /js/student/instructor-choice.js |
| instructor-dashboard.html:784 | /js/dashboard-instructor.js | /js/instructor/dashboard-instructor.js |
| instructors.html:32 | /js/instructors.js | без правки (модуль в корне) |
| policy.html:35 | /js/policy.js | без правки (модуль в корне) |

ES-импорты внутри модулей (8 строк в 6 файлах): admin-login.js:1 и
instructors.js:2 `./api.js` → `../shared/api.js` / `./shared/api.js`;
cabinet.js:4 `./utils.js` → `../shared/utils.js`;
dashboard-instructor.js:3–4, instructor-cabinet-stub.js:4–5,
instructor-choice.js:4–5 — `../shared/{api,utils}.js`.
api.js, utils.js, admin-dashboard.js, policy.js внутренних импортов
не имеют (grep `from` — 0 строк).

Тестовые хелперы: conftest `frontend_source()` (резолв, см. выше);
route `/js/{filename}` → `/js/{filepath:path}` в app.py (см. выше).
Needle теста `'/js/policy.js' in page.text` (test_policy.py:181) —
без правки (модуль в корне).

### D5. Нетронутые ссылки (класс D — проверены, правки не требуют)

- Dockerfile: `COPY backend/ backend/` накрывает подпапки;
  `CMD … uvicorn backend.app:app …` — точка входа сохранена.
- docker-compose.yml: путей к модулям backend нет (только сети/имена).
- deploy/autoschool.service: `uvicorn backend.app:app` — сохранен.
- deploy/container-README.md:20 («uvicorn backend.app:app,
  single-worker») — остается верным дословно.
- scripts/run_dev.sh: `uvicorn backend.app:app` — сохранен.
- tests/web/test_ui_playwright.py: спавн `uvicorn backend.app:app`
  (:218) — сохранен; пути страниц — frontend/*.html не двигаются.
- tests/test_container_contract.py: ссылок на модули backend нет
  (только compose/Dockerfile/CI тексты — не правятся).
- scripts/flow_preflight.py:50 `PAGES_REL = "backend/app/pages.py"` и
  regex `^backend/app/pages\.py$` — legacy (файла нет и до пакета,
  чек молчит); scripts/smoke_static.py:27 glob `backend/app/*.py` —
  матчит остающийся app.py; scripts/impact_rules.json:60–62 (правило
  pages.py) — legacy, не срабатывает.
- scripts/check_auth_timing.py (ищет auth-модуль в backend/app/<name>)
  — legacy-утилита под сервисное дерево, вне CI, уже несовместима с
  плоским деревом — вне объема.
- tests/conftest.py:30 `sys.path.insert(0, ROOT/"backend")` — не
  трогается (bare-импортов модулей нет).
- CI .github/workflows/flow.yml: греп `^(backend|frontend|…)/` — класс
  путей, не имена модулей; `pytest tests/ -q`, `docker build` — без
  правок.
- Docstring-упоминания старых путей (tests/web/test_cabinet_page.py
  «js/cabinet.js», test_s10_backend.py:22 «monkeypatch
  backend.booking.now_moscow», docs/superpowers/plans/*, комментарии
  frontend/vue/* про legacy js) — исторические тексты, не трогаются.
- frontend/vue/** (каркас Vue, vite.config.mjs, dist-входы) — не
  трогается; тесты, читающие vue-исходники, пути не меняют.

## Границы правок тестов

Разрешено (фиксируется отдельным списком в отчете партии):
1. импорт-строки `backend.*` в тестах — 61 строка в 20 файлах (D2);
2. литералы путей чтения ИСХОДНИКОВ модулей в статических NFR-
   инспекциях — 17 литералов в 4 файлах (D3);
3. строковый таргет monkeypatch — 1 (D3);
4. резолв относительных импортов в conftest frontend_source() —
   инфраструктурный helper, механика обхода сохраняется (D4);
5. НИКАКИХ правок сценариев, GIVEN/WHEN/THEN, needles, маркеров
   кейсов (NFR-27; прецеденты s11/s12).

## Сознательные ограничения (задокументированы)

- Поведение, контракты API, схема БД, single-worker, маршруты страниц,
  редиректы, localStorage-ключи — без изменений; новый URL-схемы
  раздачи нет: старые пути /js/<file>.js валидны для корневых модулей,
  для переложенных модулей URL меняет ТОЛЬКО HTML-src (клиенты —
  собственные страницы репо; внешний контракт статики не документирован
  и не потребляется третьими клиентами — проверка: grep /js/ по
  contracts/, docs/, deploy/ — ссылок нет).
- Кросс-доменные импорты сохраняются как есть (guards→auth,
  instructor_availability→booking, instructor_cars→instructor_documents
  и т.п.) — перекладка не вводит новых абстракций/интерфейсов
  (паттерн 3 «модульность без фанатизма»; разрезание сервисов —
  Релиз 1).
- Имена модулей НЕ меняются (в т.ч. `auth/auth.py`, `policy/policy.py`
  — удвоение сегмента принимается ради grep/истории/диффа; переименование
  = смена идентификаторов вне механики).
- Docstring-упоминания старых путей в коде продукта и тестах — не
  вычищаются (текст, не поведение; отдельная косметика вне партии).
- sys.path-хак conftest (ROOT/backend) — не убирается (вне объема).
- static_v-бампы, static-инфраструктура (IR-03) — не применимы
  (механики static_v в репо нет).

## План прогонов (детали — tasks, волна 3)

- tests/unit + tests/api (TestClient, без сети) — после волны 1.
- tests/web без Playwright (wiring через frontend_source) — после
  волны 2; Playwright-e2e — волна 3.
- Полный `pytest tests/ -q` (зеркало CI), regress-final по чек-листу
  партии, `scripts/container_test.sh` (сборка образа + прогон
  backend-набора внутри образа), e2e-набор — волна 3.
