# Tasks: add-code-domain-folders

Правила: задача атомарна (одна сессия = одна задача); `[P]` —
независимая задача (параллелится, каждая в своем worktree). Типы:
`[code]`/`[tests]`/`[infra]`. Партия — ЧИСТАЯ перекладка (решение
Заказчика 2026-11-08): поведение/контракты/БД не меняются; правки
тестов — только импорт-строки/пути чтения исходников/резолв хелпера
(design.md «Границы правок тестов»). Полный инвентарь ссылок —
design.md «Инвентарь ссылок» (классы A/B/C/D). Коммиты не входят в
задачи (решает ПМ/приемка). Граница каждой волны — зеленые наборы
на текущем дереве (контракт «наборы зеленые» между задачами).

## 1. Волна 1 — backend: перенос + импорты + прогоны api/unit

- [ ] 1.1 [code] Перенести 20 модулей `git mv` в доменные пакеты
      (дерево design.md): core/{config,db,guards,uploads}.py,
      auth/{auth,register,admin,instructor_admin,application_status}.py,
      instructor/{instructors,dashboard,instructor_cars,
      instructor_documents,instructor_availability,
      instructor_summary}.py, student/{booking,student_marketplace,
      student_requests,reviews}.py, policy/policy.py; создать 5 пустых
      `__init__.py` (core, auth, instructor, student, policy —
      docstring-заглушка домена). `backend/app.py` и
      `backend/__init__.py` НЕ переносить. Имена модулей не менять.
      Готовность: `ls backend/**` соответствует дереву design.md;
      `git status` — только R-записи (rename) + 5 новых файлов;
      старые пути отсутствуют.
      FR: — (структура). NFR: —. Зависит от: —.

- [ ] 1.2 [code] Переписать импорты внутри backend: 17 строк в app.py
      (16 router-импортов + `import backend.db as db`) и 44 строки в
      переносимых модулях (полный список связей — design.md D1;
      `import backend.config as config` → `backend.core.config` и
      т.д.). Импорт-граф не менять (кросс-доменные связи сохраняются).
      Готовность: `grep -rn "from backend\.\|import backend\." backend/`
      показывает только пути нового дерева; `python -c "from
      backend.app import create_app; create_app()"` — без ошибок;
      `uvicorn backend.app:app` стартует, GET /api/health — 200.
      FR: —. NFR: —. Зависит от: 1.1.

- [ ] 1.3 [tests] Механические правки путей в тестах (сценарии не
      трогать): (а) 61 импорт-строка в 20 файлах — построчный список
      design.md D2; (б) string-needle: monkeypatch-таргет
      `"backend.instructors.db"` → `"backend.instructor.instructors.db"`
      (test_qa_instructor_flow:239) и 17 литералов путей чтения
      исходников в NFR-инспекциях (test_s5:1573–1577 — 5 имен;
      test_s3:1674–1683 — 8 имен; test_instructor_dashboard:348;
      test_qa_instructor_flow:412–414 — 3 имени; design.md D3);
      (в) conftest: `from backend.app import create_app` и
      sys.path-хак — не трогаются; docstring-упоминания старых путей —
      не трогаются. Список правок зафиксировать в отчете партии.
      Готовность: `grep -rn "backend\.\(db\|auth\|booking\|policy\)"
      tests/ --include="*.py"` не находит старых функциональных
      ссылок; списки модулей в s3/s5-инспекциях ссылаются на новые
      пути (файлы читаются).
      FR: —. NFR: NFR-27 (граница). Зависит от: 1.2.

- [ ] 1.4 [tests] Прогон наборов волны 1: `pytest tests/unit -q`,
      `pytest tests/api -q` (TestClient, без сети), смоук-импорт
      приложения. tests/web и e2e — в волнах 2–3 (пока js-дерево не
      тронуто, web-набор остается зеленым на прежней статике).
      Готовность: unit + api зеленые; `git grep -n "uvicorn backend
      .app:app" Dockerfile deploy/autoschool.service
      scripts/run_dev.sh` — без изменений.
      FR: —. NFR: NFR-2/NFR-3 (NFR-инспекции исходников на новых
      путях). Зависит от: 1.2, 1.3.

## 2. Волна 2 — frontend/js: перенос + HTML src + route + прогоны web

- [ ] 2.1 [code] Перенести 8 модулей `git mv`: shared/{api,utils}.js,
      student/{cabinet,instructor-choice}.js, instructor/
      {dashboard-instructor,instructor-cabinet-stub}.js,
      admin/{admin-dashboard,admin-login}.js; instructors.js и
      policy.js остаются в корне js/ (design.md «Финальное дерево
      frontend/js»). frontend/vue/** не трогать.
      Готовность: `ls frontend/js/**` соответствует дереву;
      `git status` — только R-записи.
      FR: —. NFR: —. Зависит от: — (от волны 1 не зависит технически,
      выполняется после зеленой волны 1).

- [ ] 2.2 [code] Обновить веб-пути: (а) 6 HTML `src="/js/…"` —
      соответствие design.md D4 (instructors.html, policy.html — без
      правок); (б) 8 ES-импорт-строк в 6 модулях → `../shared/*`
      (из подпапок) и `./shared/api.js` (instructors.js из корня);
      (в) route в backend/app.py: `/js/{filename}` →
      `/js/{filepath:path}` с гвардом обхода каталога/скрытых сегментов
      и прежним content-type (код — design.md «Раздача /js/*»).
      Готовность: `grep -rn 'src="/js/' frontend/*.html` — все пути
      существуют на диске; curl /js/student/cabinet.js — 200
      application/javascript; /js/policy.js — 200; /js/../.env,
      /js/.hidden, /js/nope.js — 404.
      FR: —. NFR: —. Зависит от: 2.1.

- [ ] 2.3 [tests] Правка хелпера conftest `frontend_source()` (design
      «frontend_source при подпапках»): regex группа 2 →
      `(\.{1,2}/[^']+)`, резолв `./…`/`../…` относительно папки
      импортирующего модуля (posixpath.normpath), `/js/…` — от корня
      frontend; дедупликация и состав «единицы wiring» без изменений.
      Тесты-вызовы frontend_source (7 файлов) не правятся.
      Готовность: wiring-тесты зеленые (test_cabinet_page,
      test_instructor_pages, test_instructor_dashboard:305/323,
      test_s3:1737, test_policy — объединенный источник каждой
      страницы содержит прежние needles: api/student/requests,
      cars/'+t.carId+'/photo/'+t.angle и т.д.).
      FR: —. NFR: NFR-27. Зависит от: 2.1, 2.2.

- [ ] 2.4 [tests] Прогон наборов волны 2: `pytest tests/web -q -k
      "not playwright"` (wiring/статика через TestClient), точечно
      test_policy (needle '/js/policy.js' — без правок), тесты
      раздачи статики (test_static). Готовность: web-набор без
      Playwright зеленый; diff тестов волны 2 = только conftest-хелпер.
      FR: —. NFR: NFR-27. Зависит от: 2.2, 2.3.

## 3. Волна 3 — regress/e2e/образ + приемка

- [ ] 3.1 [tests] Полный regress: `env -u GITHUB_EVENT_PATH pytest
      tests/ -q` (зеркало CI, включает test_container_contract).
      Готовность: 0 failed; diff тестов относительно HEAD-before
      ограничен design.md D2/D3/D4 (проверка `git diff --stat —
      tests/`).
      FR: —. NFR: NFR-27. Зависит от: 1.4, 2.4.

- [ ] 3.2 [tests] Playwright e2e (полный browser-набор test_ui_
      playwright: uvicorn backend.app:app на эфемерном порту):
      сценарии кабинетов/лендинга/модалок — зеленые без правок
      (NFR-27); дополнительно smoke сети: браузер грузит
      /js/student/cabinet.js и /js/shared/api.js без 404 в консоли.
      Готовность: e2e PASS.
      FR: —. NFR: NFR-27. Зависит от: 3.1.

- [ ] 3.3 [infra] Сборка образа + контейнерная верификация:
      `docker compose build app` (backend/ копируется целиком — новые
      подпапки в контексте), `bash scripts/container_test.sh` (прогон
      backend-набора внутри образа, тот же digest), HEALTHCHECK
      /api/health внутри контейнера. Dockerfile/compose/.dockerignore/
      CI — без правок (design.md D5).
      Готовность: образ собран, набор внутри образа зелен,
      container_test.sh → «OK: backend-набор зеленый».
      FR: —. NFR: NFR-16 (minio в backend-сети — не задет). Зависит
      от: 3.1.

- [ ] 3.4 [tests] regress-final: зафиксировать PASS на финальном
      дереве (прецедент s12: последний коммит партии), сверить чек-
      лист приемки решения Заказчика: «новое дерево доменов; все
      наборы зеленые без смысловых правок; сборка образа + полный
      e2e; openspec strict». Отчет партии: выбранное дерево, размер
      инвентаря по классам (A: 122 импорт-строки; B: 18; C: 16;
      D: реестр нетронутых), список правок тестов, результаты
      validate.
      Готовность: regress-final PASS; `openspec validate
      add-code-domain-folders --strict` → valid; `openspec validate
      --all --strict` — green.
      FR: —. NFR: —. Зависит от: 3.1–3.3.

## Зависимости (волны)

- Волна 1 (1.1→1.2→1.3→1.4) — backend-перенос, граница: unit+api
  зеленые.
- Волна 2 (2.1→2.2→2.3→2.4) — frontend/js, граница: web-без-Playwright
  зеленый; начинается после 1.4 (последовательные партии в одном
  worktree, параллелить волны в одном дереве нельзя — общие прогоны).
- Волна 3 (3.1→3.2/3.3→3.4) — полный regress/e2e/образ/приемка.

## Рекомендации к нарезке

- 1.1+1.2 — одна сессия (атомарный перенос: файлы и их импорты
  неразделимы); 1.3 — отдельная сессия (тестовые правки + список);
  1.4 — короткий прогон-задача.
- 2.1+2.2 — одна сессия (js-дерево + HTML/route); 2.3 — в той же или
  следующей сессии с 2.4.
- 3.1–3.4 — регресс-сессия (по прецеденту s12 regress-final).
