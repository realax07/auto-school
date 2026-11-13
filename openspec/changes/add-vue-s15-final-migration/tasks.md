# Tasks: add-vue-s15-final-migration

Правила: задача атомарна (одна сессия = одна задача); `[P]` — независимая
задача (параллелится, каждая в своем worktree; пишут против контрактов
design.md, не против кода друг друга). Типы работ: `[code]`/`[tests]`/
`[docs]`/`[infra]`. Каркас — `frontend/vue/` (существует: пилот С9 +
С11 + С12 + С14); правила сборки, сплита и бюджетов — ADR-008, свод
С11/С12/С14 по NFR-26 (в этой партии входов становится 14 — design.md
«Сверка контрактов решения»: в решении «~17» — счет по несуществующим
отдельным страницам booking/admin-cars; фактический состав — 6 страниц,
«booking/admin-cars отдельно не существуют»). Прецеденты — архивы
пилота, С11, С12, С14. Новых npm-зависимостей нет; зависимостей от
параллельных change-пакетов нет.

**Правило партии С15 (директива СА): после КАЖДОЙ задачи — коммит
«[s15] CA: <краткое имя задачи>» + push в ветку feat/s15-final-migration
(отменяет наследуемое «коммиты решает ПМ» из С12/С14).**

## 1. Каркас партии: входы и заглушки

- [ ] 1.1 [code] vite.config.mjs — входы: `cabinet`,
      `instructor-choice`, `admin-login`, `admin-dashboard`,
      `registered`, `policy` (frontend/vue/<имя>.html — имена по
      сегментам маршрутов, паттерн С11/С12/С14); входы — статическая
      разметка-минимум (оболочка + комментарий «перенос — задача
      N.x») + модуль-скрипты /src/pages/<page>/main.js с МИНИМАЛЬНЫМИ
      App.vue-заглушками (полная разметка и wiring — 2.x/3.x/4.x):
      без заглушек вход не собирается и готовность 1.1 недостижима
      (прецедент arch-review-001 MIN-2 С12, задача 2.1 С14);
      scripts/check-budgets.mjs — PAGES: 14 (8 существующих + 6
      новых; пороги НЕ меняются — NFR-26); manualChunks/base '/vue/'/
      outDir — без изменений. МАРШРУТЫ backend/app.py НЕ
      ПЕРЕКЛЮЧАЮТСЯ (легаси обслуживается до 5.1 — design.md
      «Роуты и статика»).
      Готовность: `npm ci && npm run build` — dist содержит 14 входов
      + ассеты с хэшами; `npm run check:budgets` зелен (14 page-
      чанков); легаси-страницы и полный `pytest tests/web/
      test_static.py tests/web/test_cabinet_page.py` — зелен на
      легаси (маршруты еще легаси). `git grep -c "vue:" backend/app.py`
      — без изменений (12 строк: 7 значений карты + комментарии/цикл
      отдачи; восьмая vue-страница /instructors/pending — пилотный
      хендлер вне карты).
      FR: FR-84. NFR: NFR-26. Зависит от: —.

## 2. Admin-контур (после 1.1; порядок: вход → панель)

- [ ] 2.1 [code] src/pages/admin-login/ + вход admin-login.html —
      полный перенос admin-login.html + js/admin/admin-login.js 1:1
      (design.md «Страницы партии»): разметка/стили дословно
      (карточка, «Админка», «Вход только по прямой ссылке», hint
      «Демо-доступ спринта-0: admin / admin»); wiring — @submit-
      эквивалент doLogin: postJSON('/api/admin/login') из
      vue/src/shared/api.js → 200+ok+token → sessionStorage
      'admin_token' → location.href='/admin-dashboard'; иначе/сеть →
      #err.classList-эквивалент (реактивное состояние, текст «Неверный
      логин или пароль» дословно). Проверяемые носители test_static
      («Админка») — во входе.
      Готовность: build + check:budgets зелен; вручную: вход админом
      ведет в /admin-dashboard (легаси), Vue-вход доступен по
      /vue/admin-login.html (dev-прогон); `pytest tests/web/
      test_static.py` зелен.
      FR: FR-84. NFR: NFR-26. Зависит от: 1.1.

- [ ] 2.2 [code] src/pages/admin-dashboard/ + вход
      admin-dashboard.html — полный перенос admin-dashboard.html +
      js/admin/admin-dashboard.js 1:1 (крупнейший перенос контура;
      design.md «Страницы партии» и «Стратегия вербатим-мокапов»):
      гвард admin_token (нет → /admin-login; 401 любого API →
      /admin-login); 4 раздела одной страницы (showSection-эквивалент
      @click, тексты кнопок дословно — has_text-якоря e2e);
      Пользователи (#users-table/#rows/#count/#empty, textContent-
      эквиваленты, exportCsv: fetch /api/admin/users/export.csv с
      X-Admin-Token → blob → a.download='users.csv'); Заявки
      (#app-rows, thead БЕЗ «Действия» — BUG-046, модалка #ic-*:
      карточка, license-image blob/objectURL, confirm('Одобрить
      заявку? Будет создана учетная запись инструктора.') СОХРАНТ,
      deny #ic-deny-box: #ic-deny-confirm disabled до непустого
      комментария); Автомобили С7 (#ac-*: фильтры data-f, чек-лист
      комплектности, validate, #ac-toast); Документы С8 (#dc-*:
      вкладки pending/history, фильтры, предпросмотр blob, verify,
      reject с #dc-reason — #dc-deny-go disabled до текста); CSS —
      дословно в styles.css (фрагменты BUG-046: .badge.wait, rowhint).
      password_hash в исходниках НЕТ.
      Готовность: build + check:budgets зелен; smoke-прогон разделов
      на dev-сервере против легаси-поведения; `pytest tests/api/
      test_admin.py tests/api/test_admin_users.py tests/api/
      test_instructor_admin.py` зелен (API не тронуты).
      FR: FR-24/FR-25 + С7/С8-разделы. NFR: NFR-26. Зависит от: 1.1
      (файлово не пересекается с 2.1 — допускается параллель при
      свободных руннерах; интеграция панели — после входа).

## 3. Мелкие страницы (после 1.1; [P] к волне 2)

- [ ] 3.1 [P][code] src/pages/registered/ + вход registered.html;
      src/pages/policy/ + вход policy.html — полные переносы 1:1:
      registered — заглушка С0 дословно, ВКЛЮЧАЯ note «демонстрационная
      страница спринта-0» и кнопку «Личный кабинет» (href=
      «landing-students.html» + onclick alert('Заглушка: личный
      кабинет появится в следующем спринте') + return false —
      поведение legacy воспроизведено честно, design.md «Сознательные
      ограничения»); policy — оболочка (#policy-meta/#policy-text,
      .back, бренд) + логика js/policy.js в App.vue: fetch('/api/
      policy') → 'Версия: '+v+' от '+d (конкатенация дословно —
      MIN-2), абзацы split(/\n\s*\n/) → интерполяция (текстовые узлы
      — NFR-25), ошибка/не-JSON/сеть → p.policy-error «Политика
      временно недоступна. Попробуйте позже» + пустой #policy-meta;
      текст политики в исходниках НЕТ.
      Готовность: build + check:budgets зелен; `pytest tests/api/
      test_policy.py` — зелен на легаси-носителе (перенос носителя —
      5.1); маркер «Регистрация завершена» — во входе.
      FR: FR-76/NFR-25, TC-REG-016/018. NFR: NFR-26. Зависит от: 1.1.

## 4. Student-контур (после 1.1; порядок: choice → cabinet)

- [ ] 4.1 [P][code] src/pages/instructor-choice/ + вход
      instructor-choice.html — полный перенос instructor-choice.html +
      js/student/instructor-choice.js 1:1 (design.md «Страницы
      партии»): гвард (getToken → toLogin), ФИО (#uname из
      /api/auth/me), фильтры (#f-trans/#f-rating/#f-exp/#f-day/
      #f-from/#f-to/#reset/#empty-reset) → buildQuery + fetchSeq-гонка,
      сортировка #sort (rating/exp/name, localeCompare 'ru'), карточки
      article.card[data-id] (инициалы-инлайн, expWord из shared,
      ratingNode-эквиваленты «☆ Нет отзывов»/«★ X.Y»/«N отзывов»,
      pills авто, slotrow часов), apply (sent-состояние «✓ Заявка
      отправлена», 409-тост без кэширования — review-001 #14),
      empty-состояние, logout (POST /api/auth/logout → clearSession →
      «/»), сайдбар a.snav (href="/cabinet", "/cabinet#/my-requests",
      "/cabinet#/my-bookings" — якорь TC-UI-019). XSS — интерполяция
      (текстовые узлы). vue/src/shared/utils.js — НЕ расширяется этой
      задачей (expWord/toast уже там; fioOf/fmtDate — задача 4.2).
      Готовность: build + check:budgets зелен; `pytest tests/api/
      test_s3_backend.py` зелен (API не тронуты; носитель needle'ов —
      5.1).
      FR: FR-31/32/35/36. NFR: NFR-26. Зависит от: 1.1.

- [ ] 4.2 [code] src/pages/cabinet/ + вход cabinet.html — полный
      перенос cabinet.html + js/student/cabinet.js 1:1 (КРУПНЕЙШИЙ
      перенос партии; design.md «Страницы партии», «Стратегия
      вербатим-мокапов»): гвард session_token → /api/auth/me
      (X-Session-Token; 401/!ok → toLogin), ФИО (fioOf) и «Добро
      пожаловать, {name}!», logout; комментарий wiring cabinet.html —
      во входе ДОСЛОВНО (носитель wiring-маркеров
      test_integration_sprint1); хеш-навигация navTo (#/my-requests,
      #/my-bookings, wantHash-синхронизация); «Мои заявки» (фильтры
      data-f + счетчики, instructor_id:r.instructor_id — дословно,
      бейджи st-*, комментарии, retry, «Оставить отзыв» →
      /review?instructor=…); «Мои брони» С10 (bk-pair/bk-nopair,
      недели bk-prev/bk-this/bk-next + #bk-range ±12 мес, запрет
      прошлого .past, карточка авто С7 bk-car-*, легенда, bk-grid,
      попап #m-book [data-close-book] → POST {availability_id, date},
      409 «Слот уже занят», bk-list/bk-count, retry); чат-бар/quick/
      плитки-заглушки alert; #toast вне #app; плитки
      #tile-instructor/#tile-requests. vue/src/shared/utils.js —
      дополнить fioOf/fmtDate ДОСЛОВНО из js/shared/utils.js
      (design.md «Судьба каталога js/»). CSS — дословно в styles.css
      (все строки мокапа — подмножество; проверка 5.1).
      Готовность: build + check:budgets зелен; smoke: вход учеником
      через лендинг (модалки С12) → кабинет; разделы и календарь на
      dev-сервере против легаси-поведения; `pytest tests/api/
      test_integration_sprint1.py` зелен на легаси-носителях (перенос
      — 5.1).
      FR: FR-5…FR-9 + С5/С7/С10-разделы. NFR: NFR-26. Зависит от: 1.1,
      4.1 (shared/utils.js — общая зона: fioOf/fmtDate добавляет
      только 4.2).

## 5. ФИНАЛЬНАЯ ЧИСТКА (после 2.x, 3.1, 4.1, 4.2 — одна сессия, НЕ делить)

- [ ] 5.1 [code] переключение и удаление одним коммитом:
      (а) backend/app.py `_PAGE_ROUTES` — все 6 легаси-строк →
      «vue:<вход>» («/registered» → vue:registered.html,
      «/admin-login» → vue:admin-login.html, «/admin-dashboard» →
      vue:admin-dashboard.html, «/cabinet» → vue:cabinet.html,
      «/instructor-choice» → vue:instructor-choice.html, «/policy» →
      vue:policy.html); контроль изъятия несуществующих маршрутов:
      grep карты — все значения указывают на входы dist, фантомных
      /booking, /instructor/bookings, /admin/cars, /admin/documents в
      карте нет (изымать нечего — design.md «Сверка»);
      (б) удаление frontend/{cabinet,instructor-choice,admin-login,
      admin-dashboard,registered,policy}.html и каталога frontend/js/
      ЦЕЛИКОМ (7 модулей); (в) удаление хендлера GET /js/{path};
      (г) переносы носителей тестов — ПОЛНЫЙ СПИСОК design.md
      «Переносы тестов»: test_cabinet_page.py (7 тестов на вход +
      App.vue + styles.css; MOCKUP без правок),
      test_integration_sprint1.py (byte-equality → признак входа
      каркаса), test_policy.py ('/js/policy.js' → '/vue/assets/'),
      test_qa_instructor_flow.py (password_hash-носитель на вход +
      App.vue), test_s3_backend.py (checks["cabinet.html"] → вход +
      App.vue, needles дословно), test_ui_playwright.py — РОВНО 4
      точки (BUG-046-носитель; TC-UI-007 снятие route.fulfill →
      живой маршрут; TC-UI-019 носители cab/choice; tag-balance −2/+6)
      — остальные сценарии НЕ ТРОГАЮТСЯ (контроль: git diff — только
      эти правки); scripts/check_tag_balance.py (DEFAULT −3/+6).
      Готовность: `git grep -n "frontend/js\|/js/" frontend backend
      tests scripts` — пусто (кроме исторических sdd.md/code-reviews/
      test-model); `ls frontend` — только vue/; все значения карты —
      vue:; `pytest tests/` (кроме playwright) зелен ПОСЛЕ сборки
      dist; фронт-контур e2e-носителей зелен.
      FR: FR-84. NFR: NFR-27. Зависит от: 2.1, 2.2, 3.1, 4.1, 4.2.

## 6. Бюджеты (после 5.1)

- [ ] 6.1 [infra] `npm run build && npm run check:budgets` — 14
      page-чанков: vendor ≤150 КБ gzip; JS первого захода КАЖДОЙ
      страницы ≤200 КБ gzip; чужих page-чанков в замыканиях нет.
      Gzip-замеры всех page-чанков — в отчет задачи (крупнейший —
      cabinet: стили в styles.css-чанк, wiring плоский; при превышении
      — сокращение зависимостей, НЕ ослабление проверки — design.md
      «Решения по НФТ»). Контроль budgets-скрипта: PAGES.length = 14.
      Готовность: check:budgets зелен; замеры зафиксированы в отчете.
      FR: —. NFR: NFR-26. Зависит от: 5.1.

## 7. Полный регресс и валидации (гейт партии)

- [ ] 7.1 [tests] полный e2e: `pytest tests/web/test_ui_playwright.py`
      против собранного dist (сборка ДО прогона — обязательный шаг) —
      все сценарии passed, 0 правок сценариев (допустимый дифф файла —
      только 4 переноса design-guard 5.1; контроль git diff); полный
      `pytest tests/` зелен (после сборки dist); якоря-контроль:
      TC-UI-002/006/007/011/013/014/019/025/026/027/044/052/059/060,
      BUG-046/049/052, admin-контур (dialog/CSV/комплектность/
      документы), хеши #/my-requests#/my-bookings, policy/registered.
      Валидации: `openspec validate add-vue-s15-final-migration
      --strict` и `openspec validate --all --strict` — valid/green.
      Финал-контроль: `ls frontend` — без легаси-HTML; `git grep -c
      "vue:" backend/app.py` — все значения карты; regress-final PASS
      c impact-анализом (MODIFIED Frontend: 6 страниц + финал;
      REMOVED легаси-носители и хендлер /js; зоны регресса —
      student/admin/policy контуры).
      Готовность: полный pytest зелен; e2e зелен; validate strict
      зелен; frontend/ без легаси; бюджеты 14 — зелен.
      FR: FR-85. NFR: NFR-26/27. Зависит от: 5.1, 6.1.

## Зависимости (волны)

- Волна 0: 1.1 (входы + заглушки + budgets-скрипт) — единственная
  точка входа для всех переносов; одна сессия.
- Волна 1 (после 1.1): { 2.1 → 2.2 (admin), 3.1 [P], 4.1 [P] } —
  admin последовательностью (вход → панель); мелкие и choice
  параллятся (файлово не пересекаются). 4.2 (cabinet) — ПОСЛЕ 4.1:
  общая зона vue/src/shared/utils.js (fioOf/fmtDate добавляет только
  4.2) и самый рискованный перенос — последним по порядку интеграции.
- Волна 2: 5.1 — строго после ВСЕХ переносов (2.1, 2.2, 3.1, 4.1,
  4.2); НЕ делить (переключение 6 маршрутов + удаление 6 файлов +
  js/ + хендлер + все носители тестов — один коммит).
- Волна 3: 6.1 (бюджеты по финальным чанкам) → 7.1 (гейт: полный
  e2e + validate).

## Рекомендации к нарезке

- Швы: (а) 2.1/2.2 — разные страницы, но один контур: панель после
  входа; (б) 3.1 — обе мелкие страницы одной сессией (крошечные);
  (в) 4.1 → 4.2 — последовательность по shared/utils.js и риску;
  (г) 5.1 — монолитная сессия.
- НЕЛЬЗЯ делить: 5.1 (маршруты/файлы/носители — атомарно, иначе
  красное промежуточное состояние); 6.1 до финала 5.1 (бюджеты по
  финальным чанкам); 7.1 — после всех.
- Общая зона файлов (не делить между задачами): frontend/vue/
  vite.config.mjs и scripts/check-budgets.mjs — только 1.1;
  vue/src/shared/utils.js — только 4.2 (дополнение fioOf/fmtDate);
  backend/app.py — только 5.1 (в 1.1 не трогается); tests/web/
  test_ui_playwright.py — только 5.1 (4 точки); tests/web/
  test_cabinet_page.py — только 5.1; src/pages/<page>/ — по задаче
  своей страницы; design/mocks/ — НИКЕМ (мокапы не синхронизируются).

## План тестовых прогонов (наборы — отдельные делегации-раннеры)

1. **API/регресс**: `pytest tests/` (кроме playwright) — после сборки
   dist (все 13 маршрутов страниц отдают dist только с ней); стенд:
   репо, env-заглушки conftest; ~5–10 мин.
2. **e2e полный**: `pytest tests/web/test_ui_playwright.py` — стенд:
   собранный dist (`npm ci && npm run build` ДО прогона — обязательный
   шаг), uvicorn на эфемерном порту, Chromium headless; ~20–40 мин
   (student+admin контуры целиком на Vue — самые долгие).
3. **Валидации**: `openspec validate --all --strict` +
   `npm run check:budgets` + `git diff --stat` контроль границ —
   секунды, локально без стенда.
Прогоны 1 и 2 НЕ объединять в один сабагент-раннер (разные стенды и
длительности); сборка dist выполняется один раз до прогонов 2, 6.1 и
регресса 7.1.
