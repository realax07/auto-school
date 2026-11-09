# Arch-review 001: add-code-domain-folders (Спринт 13)

- Дата: 2026-11-09
- Ревьюер: архитектор (Hermes)
- Коммит СА-фазы: 9d3a510 «[s13] CA: пакет add-code-domain-folders»
- База проверки: фактический код на HEAD 9d3a510 — backend/ (20 модулей +
  app.py + __init__.py), frontend/js/ (10 модулей), frontend/*.html (8),
  tests/ (unit/api/web, conftest, test_container_contract), scripts/,
  deploy/, Dockerfile, .dockerignore, CI — инвентарь design.md сверен
  grep-обходом по всем четырем классам (A/B/C/D), route и conftest-хелпер
  сверены построчно

## Вердикт

**approve-with-notes** (MAJ — нет; MIN-1…MIN-5 — счетные уточнения и
до-шлифовка критериев готовности, внесены коммитом arch-review;
блокировки dev-старта нет).

Карта: **без изменений** (см. раздел 7).

## 1. Полнота инвентаря — сверена пофакто, пропущенных ссылок нет

- **Класс A (Python-импорты).** backend/ — ровно 61 строка: 17 в app.py
  (16 router-импортов :15–30 + `import backend.db as db` :14) + 44 в
  переносимых модулях (43 dotted + единственный from-импорт без точки
  `from backend import booking` instructor_availability.py:66). Таблица
  D2 пофайлово сверена построчно: все 20 файлов и все 61 строка
  подтверждены (test_auth.py — 9: `from backend import auth` ×2 (:93,
  :268) + `import backend.auth` ×6 (:207…:372) + auth_router ×1 (:80));
  «не правятся»-список (`from backend.app import create_app` ×5 —
  conftest:95, s9:631, auth:79, bug001:9, static:34; uvicorn
  `backend.app:app` test_ui_playwright:218) подтвержден. Заявка tasks
  1.2 «17 в app.py + 44 в модулях» — точна.
- **Класс B (string-needle).** Полный свип литералов чтения исходников:
  ровно 17 в 4 файлах — test_s5_backend:1573–1577 (5 имен),
  test_s3_backend:1674–1683 (8), test_instructor_dashboard:348 (1),
  test_qa_instructor_flow:412–414 (3, путь-литералы `ROOT / rel`) —
  плюс monkeypatch-строка qa_instructor_flow:239 = 18. Других чтений
  исходников модулей в tests/ нет (grep `ROOT / "backend"` — только
  файлы из списка + sys.path-хак conftest:30). Путь-агностичные
  (inspect.getfile — test_register:496; `__file__` — test_db:357,
  test_qa_sprint1:104; rglob — test_policy:276–282) подтверждены:
  «не трогаются» — верно.
- **Класс C (веб-пути).** `src="/js/"` — ровно 8 страниц, 6 правок + 2
  корневые без правок; все номера строк design (373/30/384/56/200/784/
  32/35) сходятся. ES-импорты — фактически **9 строк в 6 файлах**
  (design в заголовке пишет 8, при перечислении называет все 9 —
  MIN-1); api.js/utils.js/admin-dashboard.js/policy.js внутренних
  импортов не имеют — grep подтвержден.
- **Класс D (нетронутые).** Точки входа подтверждены: Dockerfile:48
  `COPY backend/ backend/` (новые подпапки накрываются автоматически,
  .dockerignore ничего из backend/ не исключает), Dockerfile:83 CMD,
  deploy/autoschool.service:11, scripts/run_dev.sh:9,
  test_ui_playwright:218 — все `backend.app:app`. nginx-autoschool.conf
  — единственный `location /` (прокси на app; /js/* раздает app —
  сегодня и после). CI flow.yml:121 — grep по КЛАССУ путей
  `^(backend|frontend|…)/`. scripts/: flow_preflight (PAGES_REL
  backend/app/pages.py — файла нет и до пакета, чек молчит),
  smoke_static (glob backend/app/*.py матчит остающийся app.py),
  impact_rules.json:60–62 (exists-guard, правило молчит),
  check_auth_timing (legacy backend/app/<name>, вне CI) — сверено,
  D5 верен. Дополнение: scripts/codegraph.py (PY_DIR «backend/app»,
  JS_DIRS «frontend/static/js») в D5 не назван — оба пути не существуют
  и до, и после пакета, py/js-графы молчат в обоих состояниях (MIN-3,
  реестр дополнен коммитом ревью).

Пропущенных функциональных ссылок НЕ найдено: за пределами таблиц
D1–D4 и реестра D5 ничего перенос не ломает. Счетчики-строки в
потребительской колонке D1 местами приблизительны (db «app.py + 15
модулей» — факт 16; auth «тесты: 16 строк / from-import ×6» — факт
21 / ×5; внутренние потребители booking — instructor_availability/
instructor_summary/student_requests — названы в §домены, но не в
строке таблицы; deferred-импорт register.py:175 → auth не упомянут) —
агрегаты (61 = 17+44) и пофайловый D2 точны, критерии готовности
grep-овые (см. MIN-1/MIN-4) — на механику переноса не влияет.

## 2. Дерево: плоские пакеты — согласовано с паттерном 3 и директивой 2026-10-16

- Плоские доменные пакеты под backend/ вместо вложенного `domains/`:
  пути короче на сегмент, симметрия с frontend/js/{shared,student,
  instructor,admin}, служебный слой без группирующей нагрузки —
  соответствует паттерну 3 «модульность без фанатизма» (границы
  модулей существуют с s3/s5/s9; папка их фиксирует, новых абстракций
  и интерфейсов не вводится) и прецеденту директивы 2026-10-16
  (js-зонинг). Кросс-доменные импорты сохраняются как есть — осознанно
  задокументировано; разрезание на сервисы — Релиз 1.
- Коллизий имен нет: все импорты абсолютные `backend.*`; bare-импортов
  перенесенных модулей в tests/, backend/, scripts/ нет (grep пуст) —
  sys.path-хак conftest:30 (ROOT/backend) остается безвредным и после
  превращения backend/auth.py в пакет backend/auth/ (пакет с пустым
  __init__.py никого не шадовит: ни один код не делает `import auth`).
  Имена core/auth/instructor/student/policy как субмодули backend
  ни с чем сторонним не пересекаются.
- __init__.py: 5 новых пустых (docstring-заглушка) — достаточно;
  backend/__init__.py и app.py остаются на месте.
- Состав доменов подтвержден маршрутами (@router сверено): спорных
  модулей нет — instructor_admin (админская модерация) в auth/ и
  application_status (до-сессионный auth-контур) в auth/
  документированы и согласуются с правилом префиксов; dashboard.py
  переносится без переименования (чистая перекладка) — принято.

## 3. Единственная продуктовая правка — /js/{filepath:path}: гвард закрывает обход

Сверено с фактическим хендлером (app.py:137–144): инварианты (гвард на
«/» и «.», is_file, явный application/javascript, HTTPException 404
без detail) сохраняются 1:1 и расширяются корректно:

- Обход каталога: ".." проверяется ПОСЕГМЕНТНО по декодированному пути
  (uvicorn/starlette декодируют %2e%2e до матчинга) → 404; двойное
  кодирование дает литеральное имя файла → is_file()=False → 404.
  Absolute («/js//etc/passwd» → filepath="/etc/passwd") —
  startswith("/") → 404. Скрытые/точечные сегменты («.env», «.hidden»,
  «x/.y», «/js/./x.js») — startswith(".") по любому сегменту → 404.
  Backslash на Linux — не разделитель: «x\..\y» — литеральное имя →
  404 (а «..\…» вдобавок отсекается dot-гвардом). «/js/» (пустой
  filepath) → is_file()=False → 404. НезKnown файл → 404 как прежде.
- content-type: явный application/javascript для корневых и вложенных —
  как сегодня (не зависеть от системных mimetypes).
- Совместимость: корневые URL /js/instructors.js, /js/policy.js
  остаются валидны (needle test_policy:181 жив; страницы instructors/
  policy — без правок); 6 HTML-src обновляются в той же задаче 2.2,
  атомарно с route. Внешних потребителей /js/-URL нет (grep
  contracts/, docs/, deploy/ — только описательное «frontend/js/*» в
  историческом requirements-sprint8.md:87, URL-контракта нет); e2e по
  /js/-URL не ходит (сверено — там только json content_type-строки).
- Наблюдение (не замечание, в review-файл): хвостовой слэш
  «/js/student/cabinet.js/» теперь отдаст 200 (path-converter съедает
  слэш, Path нормализует) вместо прежнего 404 односегментного
  маршрута — косметика на недокументированных URL, контракт не задет.

## 4. conftest frontend_source(): подход верен для транзитивных импортов

Текущий код сверен (conftest:60–75): группа 2 regex требует литеральный
`./` (`from\s+'(\./[^']+)'`, строка 64), резолв `rel.lstrip("./")` от
корня js/ (строка 68) — диагноз design точен: `../shared/api.js` из
подпапки не сматчится вовсе, а при сматченности резолв был бы неверен.
Правка (`(\.{1,2}/[^']+)` + posixpath.normpath(dirname(модуля)+ref);
`/js/…` — от корня frontend) корректна: cabinet.js (student/)
`../shared/utils.js` → js/shared/utils.js; instructors.js (корень)
`./shared/api.js` → js/shared/api.js; нормализация делает dedup по
`seen` устойчивым к разным спецификаторам одного модуля; очередь+seen
циклы ES-импортов не разворачивают (как и сегодня). Двойных кавычек в
js-импортах нет (grep — все одинарные), расширение группы 2 на них не
требуется. Реализация потребует нести папку модуля вместе с текстом в
очереди (~10 строк) — укладывается в «механическую правку хелпера»,
границы NFR-27 не нарушает.

Уточнение факта (MIN-2): фактических вызовов frontend_source — 4
тест-файла, 11 вызовов (test_s3_backend:1737; test_instructor_
dashboard:305/323; test_cabinet_page ×5; test_instructor_pages:94/377),
не «7 файлов»: test_login_modal упоминает хелпер только в docstring
(читает vue-исходники своим vue_landing_source), test_policy ходит
rglob без хелпера. На механику не влияет («вызовы не правятся»
истинно для всех), счетная строка уточнена в design/tasks коммитом.

## 5. Циклы: граф импортов — DAG, перенос циклов не создает

Кросс-импорты сверены по факту (grep backend/): policy/config/db/
uploads — листья (backend.*-импортов нет); auth→db; guards→auth,db;
booking→db,guards; instructor_availability→booking,guards;
instructor_summary→booking,guards; student_requests→booking,guards;
instructor_cars→instructor_documents,admin,uploads,auth,guards;
instructor_documents→admin,uploads,guards; instructor_admin→admin,
uploads; instructors→policy,uploads; register→db,policy + deferred
auth (_session_issue внутри функции, register.py:175);
application_status, dashboard→auth,db; reviews, student_marketplace→
db,guards. Обратных ребер нет: booking не импортирует availability/
summary/requests; auth не импортирует guards; instructor_documents не
импортирует instructor_cars. Перенос меняет пути, не ребра — циклы не
возникают ни на уровне пакетов, ни модулей; deferred-импорт
register→auth цикла тоже не создает (auth→db только).

## 6. Спеки и критерии готовности — валидны; два grep-критерия дошлифованы

- `openspec validate add-code-domain-folders --strict` — ЗЕЛЕНЫЙ
  (проверено на HEAD 9d3a510).
- 2 ADDED Requirements / 4 MUST-сценария GIVEN-WHEN-THEN; MUST
  уместны (доменная организация, чистота перекладки, стабильность
  точек входа, контракт /js/*). Длины текстов требований: 478 и 427
  знаков — ≤500 (проверено скриптом).
- Кейпабилити codebase-structure — новая (в openspec/specs/
  отсутствует), ADDED-only корректен; именование в конвенции дэшей.
  Инвентарные числа сценария (61 импорт-строка в backend/, 61 строка
  в 20 тестовых файлах, 18 string-needle) сверены с фактом — точны.
  Сценарии проверяемы (полный pytest + импорт приложения; дифф тестов
  по классам; точки входа + сборка образа + health; 200/404-матрица
  /js/ + wiring с `../…`).
- Конфликтов с мастер-спеками нет: дельта только ADDED; поведение/
  контракты существующих кейпабилити (booking, auth, instructor-*,
  PersonalData, containerization, StudentFlow и др.) не затронуты.
- Критерии готовности: 1.2-grep `from backend\.|import backend\.`
  не покрывает форму `from backend import` (единственный случай —
  instructor_availability.py:66; страховка — импорт-смоук в 1.2 и
  зеленая волна 1.4, но критерий должен ловить сам) — MIN-4,
  альтернатива добавлена в tasks.md. 1.3-grep `backend\.(db|auth|
  booking|policy)` матчит docstring-носители, объявленные нетронутыми
  (s10:22, qa_flow:34/54/452, auth_route:40, README:77…) — уточнение
  «функциональных, docstring не считаются» добавлено (MIN-5).
  curl-проба /js/../.env в 2.2 без --path-as-is нормализуется самим
  curl (проверка прошла бы «мимо») — уточнено (MIN-5).

## 7. Архитектурная карта

Карта: **без изменений**.

Пакет не вводит новых архитектурных решений: границы модулей
существуют с s3/s5/s9 (карта — паттерн 3 и схема «Компоненты» — их уже
описывает), точка входа, деплой-контур, контракты и БД неизменны.
Схема «Компоненты» остается точной на уровне имен и обязанностей
модулей (имена не меняются, роли не переезжают); пакетная группировка —
свойство дерева файлов, не паттерна. Доменное решение Заказчика
2026-11-08 фиксируется дельтой codebase-structure — этого достаточно
(ADR не требуется: нового техстека/границ процессов нет). Косметическая
аннотация группировки в «Компонентах» уместна после приемки партии,
не на СА-фазе (прецедент s11: рутинный рефреш — после приемки).

## Итог

- MAJ: нет.
- MIN-1 (счет design): D4-заголовок «8 строк в 6 файлах» при
  перечисленных 9, admin-login.js:1 → факт :2, класс C «16 правок» →
  17; потребительские счетчики D1 приблизительны (db «+15 модулей» →
  факт 16; auth «тесты: 16 / ×6» → факт 21 / ×5; deferred
  register.py:175 → auth и внутренние потребители booking не названы
  в строках таблицы — агрегат 44 и D2 точны). Уточнено в design.md
  этим коммитом.
- MIN-2 (счет design/tasks): «вызовы frontend_source (7 файлов)» —
  фактически 4 файла / 11 вызовов (test_login_modal — docstring,
  test_policy — rglob). Уточнено в design.md и tasks.md.
- MIN-3 (реестр D5): scripts/codegraph.py (PY_DIR «backend/app»,
  JS_DIRS «frontend/static/js» — оба пути не существуют до и после,
  графы молчат) не назван. Дополнен в design.md.
- MIN-4 (критерий 1.2): grep готовности не покрывает форму
  `from backend import` — альтернатива добавлена в tasks.md.
- MIN-5 (критерии 1.3/2.2): 1.3-grep vs docstring-носители — уточнено;
  curl-проба /js/../.env — добавлен --path-as-is. Правки в tasks.md.
- Сверка инвентаря: D1 (агрегат 61 = 17+44), D2 (61 в 20 файлах,
  построчно), D3 (17 литералов + 1 monkeypatch), D4 (HTML 6 правок +
  2 корня; ES 9 строк), D5 (точки входа/скрипты/CI) — полны;
  пропущенных функциональных ссылок нет.
- Вердикт: **approve-with-notes** — dev-старт разрешен (волны
  1→2→3 по tasks.md).
