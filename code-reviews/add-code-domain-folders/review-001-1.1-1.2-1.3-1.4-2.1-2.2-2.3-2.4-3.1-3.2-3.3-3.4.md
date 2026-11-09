<!-- Reviewer-Delegation: deleg-s13-dev1-external | независимый код-ревьюер (не автор диффа) | дифф: 93b1375..48bd504 (4 коммита) | ветка: feat/s13-domain-folders | дата: 2026-11-09 -->

# Code review: dev-партия add-code-domain-folders — задачи 1.1–3.4 (перекладка кода в доменные папки)

Периметр: весь dev-дифф 93b1375..48bd504 (64 файла, +258/−189): backend →
плоские пакеты core/auth/instructor/student/policy (волна 1), frontend/js →
shared/student/instructor/admin + маршрут /js/{filepath:path} (волна 2),
BUG-063 — детерминизм слотов в setup_pair s5/s7 и future_date в PUT-409
тестах (волна 3). Контекст: design.md пакета (полные таблицы A/B/C/D),
arch-review-001 (approve-with-notes, MIN-1…MIN-5), BUG-063.md.

## Вердикт: approve

Все задачи партии (1.1–1.4, 2.1–2.4, 3.1–3.4) приняты. Замечаний
blocker/major нет; один minor косметический (лишняя пустая строка,
появилась при правке book() в BUG-063). Это чистая перекладка: поведение
не менялось (маршрут /js/* расширен на подпапки с сохранением инвариантов
— единственная продуктовая правка, по design), сценарии тестов не
трогались. Прогоны на HEAD 48bd504: api-выборка 128 passed, unit 22
passed, web-без-Playwright 38 passed, e2e 67 passed, `openspec validate
--strict` — valid.

## Замечания

| Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|
| minor | tests/api/test_s5_backend.py:226–228 | Три пустые строки между `book()` и `first_slot_id` (PEP8 — две): лишняя появилась при добавлении параметра `date` в book() (BUG-063, волна 3). E303, на поведение не влияет, flake-гейтов в CI на это нет. | Свернуть до двух в следующей косметической партии или при первом касании файла; в этом пакете правка не требуется. |

## Наблюдения (не замечания)

- **/js/&lt;путь&gt;/ с хвостовым слэшем → 200** (проба:
  `/js/student/cabinet.js/` — 200 application/javascript; прежний
  односегментный маршрут давал 404 на любой двухсегментный URL).
  Задокументировано arch-review-001 §3: path-converter съедает слэш,
  Path нормализует; URL недокументированы, контракт не задет. Действий
  не требует.
- **tasks.md 2.2(б) — остаток до-MIN-1**: «8 ES-импорт-строк в 6
  модулях» — фактически 9 строк (фронтовый дифф: admin-login.js:2,
  instructors.js:2, cabinet.js:4, dashboard-instructor.js:3–4,
  instructor-cabinet-stub.js:4–5, instructor-choice.js:4–5).
  design.md D4 arch-review исправил на 9, tasks.md — нет. Текст tasks
  вне границ правок партии (тики only) — к диффу не претензия; для ПМ
  при косметическом проходе.
- **BUG-063, теоретическая грань полуночи**: setup_pair вычисляет
  tomorrow/day-after до запроса; переход полуночи между вычислением и
  PUT сделал бы «завтра» «сегодня». Окно — микросекунды вокруг 00:00,
  слоты 10:00/12:00 → практически недостижимо; грань присуща любому
  date-based детерминизму. Не требует действий.
- **Окружение ревьюера для e2e**: chromium не стартовал из-за
  отсутствующих системных библиотек (libatk-1.0.so.0 и пр.; sudo нет).
  Прогон выполнен с `LD_LIBRARY_PATH=~/.cache/pw-libs/root/usr/lib/x86_64-linux-gnu`
  (локальный сташ deb-зависимостей) — 67 passed. Ограничение среды
  ревьюера, не продукта; в среде разработки dev-партии зависимости
  присутствовали (заявленные 67 passed подтверждены независимо).
- **conftest frontend_source()**: HTML кладется в очередь как
  ("js/"+name, html) — группа 1 regex матчит только `/js/…`, а
  относительных src в HTML нет, поэтому для HTML-уровня поведение
  эквивалентно прежнему; транзитивный резолв `../shared/*` из подпапок
  через posixpath.normpath(dirname+ref) корректен — подтверждено
  зеленым web-набором (test_cabinet_page ×5, test_instructor_pages,
  test_instructor_dashboard:305/323, test_s3:1737 — needles прежние).

## Факты проверок (свежие прогоны и пробы на HEAD 48bd504, чистое дерево)

### 1. Полнота переноса — старых путей нет
- `ls backend/*.py` → только app.py и __init__.py; новые пакеты
  core/(4), auth/(5), instructor/(6), student/(4), policy/(1) — дерево
  design.md 1:1.
- grep старых МОДУЛЬНЫХ импортов по tests/
  (`backend.instructors`, `backend.booking`, `backend.db`,
  `from backend import auth/booking` вне нового дерева и т.д.) — пусто;
  остались только needle-строки по design (monkeypatch-таргет уже
  новый, чтения исходников — новые пути).
- Литералы старых путей `backend/<модуль>.py` в tests/ — пусто;
  старых js-имен (`cabinet.js`, `admin-dashboard.js`, …) в
  frontend/*.html и корне js/ — пусто; frontend/js = 4 подпапки +
  instructors.js + policy.js.
- git diff --name-status: 28 R (сходство R091–R100, чистые git mv),
  6 A (5 пустых __init__.py с docstring-заглушкой + BUG-063.md),
  30 M. Dockerfile, docker-compose, CI, deploy/, спеки пакета —
  не тронуты; tasks.md — только тики `[ ]`→`[x]`.

### 2. Импорты и циклы
- Смоук-импорт всех 21 модулей (backend.app + 20 доменных) — OK,
  без циклов; `create_app()` собирается; в sys.modules не осталось
  плоских путей (`backend.booking` и пр.).
- app.py: ровно 17 импорт-строк переписаны (16 router + db), маршрут —
  единственная содержательная правка; сверено с diff.
- Построчный аудит диффа tests/ вне трех исключений (s5, s7, conftest):
  каждая измененная строка — элемент симметричной пары old→new
  (12↔12 `import backend.auth as auth` → `backend.auth.auth as auth`,
  8↔8 db, 5↔5, 4↔4 policy, 2↔2 booking, 1↔1 остальные) либо один из
  17 литералов путей/monkeypatch-таргета. Сценарии, GIVEN/WHEN/THEN,
  needles, маркеры кейсов — не менялись (NFR-27 соблюдена).

### 3. Маршрут /js/{filepath:path} — гвард закрывает обход
Проба TestClient'ом, 13 кейсов — все согласно:
- 200 application/javascript: /js/student/cabinet.js,
  /js/shared/api.js, /js/policy.js, /js/instructors.js (корневые —
  обратная совместимость), /js/student/cabinet.js/ (см. наблюдения);
- 404: /js/../.env (path-as-is), /js/%2e%2e/.env (декодированные
  dot-сегменты), /js//etc/passwd (absolute), /js/.hidden,
  /js/student/.env, /js/./cabinet.js (dot-сегменты в любом месте),
  /js/nope.js, старый URL перенесенного /js/admin-dashboard.js.
Хендлер сверен с design-кодом посимвольно (гвард: startswith("/"),
".." по сегментам, dot-сегменты, is_file, явный
application/javascript, HTTPException 404 без detail).

### 4. NFR-инспекции читают реальные модули на новых путях
- Все 16 целевых файлов существуют и нетривиальны (3–36 КБ):
  student/booking.py 33К, instructor/instructor_cars.py 36К,
  instructor/instructor_documents.py 27К, instructor/instructors.py 18К,
  instructor/instructor_availability.py 17К, instructor/dashboard.py 6К,
  instructor/instructor_summary.py 5К, student/student_requests.py 18К,
  student/student_marketplace.py 9К, student/reviews.py 3К,
  auth/auth.py 11К, auth/instructor_admin.py 9К, auth/admin.py 5К,
  auth/register.py 7К, core/guards.py 2.5К, core/uploads.py 2.8К.
- Списки инспекций сверены с design D3: s3 — 8 имен
  (instructor/instructor_cars, instructor/instructor_availability,
  student/student_marketplace, student/reviews,
  student/student_requests, instructor/instructor_summary,
  core/guards, core/uploads); s5 — 5 имен (student/booking,
  instructor/instructor_documents, instructor/instructor_cars,
  instructor/instructor_availability, instructor/instructor_summary);
  test_instructor_dashboard:348 — backend/instructor/dashboard.py;
  test_qa_instructor_flow:412–414 — instructor/instructors.py,
  auth/instructor_admin.py, auth/auth.py.
- Прогон инспекций в составе наборов — зеленый (см. §6): файлы
  реально читаются (read_text на существующих путях), не пустышки.

### 5. BUG-063 — семантика и минимальность
- setup_pair s5/s7: one_off на завтра (10:00–11:00) и послезавтра
  (12:00–13:00) с `weekday=d.weekday()` — корректно: валидация API
  требует совпадения weekday с днем даты для one_off
  (instructor_availability.py:19). Детерминированно в любой день и
  время прогона.
- future_date(weekday): `(weekday - today.weekday()) % 7 or 7` —
  ближайшая СТРОГО будущая дата с нужным днем недели (совпадение с
  сегодня → +7) — корректно; дубликат в s5 и s7 (по хелперу на файл,
  как setup_pair) — принятый в партии паттерн.
- PUT-409 тесты (s5:1315/1402, s7:1238): recurring-интервалы сохранены
  явным `intervals=[weekday 0/1]` + бронь с явной
  `date=future_date(0)` — семантика кейсов (409-перечень, MAJ-1/MIN-2)
  не изменилась. Бронь s7:851 без date — на one_off-слоте из дефолтного
  setup_pair: сервер берет собственную дату слота (завтра) → 200,
  детерминизм соблюден.
- Минимальность: правки — хелперы setup_pair/future_date/book
  (обратимо-совместимая сигнатура, date=None), 2 вызова book с
  date=future_date(0), 1 явный intervals в s7-409, импорт-строки,
  список инспекции s5. Других смысловых правок в s5/s7 нет.

### 6. Прогоны (HEAD 48bd504)
- `pytest tests/api/test_s3_backend.py tests/api/test_s5_backend.py
  tests/api/test_s7_backend.py tests/api/test_s10_backend.py
  tests/api/test_qa_instructor_flow.py -q` — **128 passed** (271s).
- `pytest tests/unit -q` — **22 passed**.
- `pytest tests/web -q -k "not playwright"` — **38 passed**
  (wiring/статика/policy-needle).
- `pytest tests/web/test_ui_playwright.py -q` — **67 passed** (145s;
  с LD_LIBRARY_PATH-обходом окружения, см. наблюдения) — совпадает с
  заявленными числами партии (371 passed полный набор — выборочно
  подтвержден на уровне 255 тестов этих четырех наборов).
- `openspec validate add-code-domain-folders --strict` — **valid**.

## Итог

- Blocker/Major: нет. Minor: 1 (пустая строка, s5:226–228).
- Границы правок тестов соблюдены (61 импорт-строка/20 файлов,
  17 литералов + monkeypatch, conftest-хелпер — и ничего сверх);
  единственные содержательные правки вне переноса — маршрут /js/* и
  BUG-063, оба заявлены и сверены.
- Вердикт: **approve** — партия к приемке готова.
