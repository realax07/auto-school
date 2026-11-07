# Tasks: add-vue-s11-status-forms

Правила: задача атомарна (одна сессия = одна задача); `[P]` — независимая
задача (параллелится, каждая в своем worktree; пишут против контрактов
design.md, не против кода друг друга). Типы работ: `[code]`/`[tests]`/
`[docs]`/`[infra]`. Каркас — `frontend/vue/` (уже существует — пилот,
PR#107); правила сборки, сплита и плана — ADR-008
(`architecture/adr/008-vue3-vite-migration.md`); прецедент — пакет
add-vue-framework-pilot (архив 2026-11-05). Зависимостей от параллельных
change-пакетов нет; новых npm-зависимостей нет. Коммиты не входят в задачи
(решает ПМ/приемка).

## 1. Сборка: точки входа партии

- [ ] 1.1 [code] vite.config.mjs + входы + скрипт бюджетов: input +=
      instructors-rejected (frontend/vue/instructors-rejected.html) и
      review-form (frontend/vue/review-form.html) — статическая разметка
      экранов (эквивалент legacy 1:1) + модуль-скрипт /src/pages/<page>/
      main.js; manualChunks/base '/vue/'/outDir — без изменений;
      scripts/check-budgets.mjs — page-чанки: instructors-pending +
      instructors-rejected + review-form, замыкание первого захода и
      «чужие page-чанки» — по каждой странице (бюджеты NFR-26 не меняются).
      src/shared/utils.js — перенос toast (#toast, ms-параметр) и expWord
      из frontend/js/utils.js (свой код в shared-чанке; frontend/js/*.js
      НЕ трогаются — ими пользуются немигрированные монолиты).
      Готовность: `npm ci && npm run build` — dist содержит оба входа
      instructors-rejected.html/review-form.html + ассеты с хэшами;
      `npm run check:budgets` зелен (3 page-чанка); `npm run dev` поднимает
      обе страницы; вендорного кода в чанках страниц нет.
      FR: FR-84. NFR: NFR-26. Зависит от: —.

## 2. Страницы на Vue

- [ ] 2.1 [code] frontend/vue/src/pages/instructor-rejected/ — полный
      перенос экрана отказа: разметка/стили 1:1 без редизайна (шапка,
      карточка — kicker «Заявка инструктора», h1 «Заявка отклонена»,
      пояснение, блок причины #reason-block скрытый + #reason-text,
      кнопки «На главную» → / и «О лендинге для инструкторов» →
      /instructors, футер) + поведение js/instructor-rejected.js в App.vue
      (onMounted): причина из sessionStorage «instructor_rejected_reason»
      (пишет модалка входа при route=rejected — КОНТРАКТ ЛОГИНА НЕ
      МЕНЯЕТСЯ), try/catch на недоступность хранилища; пусто/нет — блок
      скрыт; статус при загрузке НЕ проверяется — НОЛЬ запросов к API.
      Id-якорь e2e #reason-text сохранен (TC-S9UI-003).
      Готовность: разметка входа синхронна App.vue; TC-S9UI-003-якорь
      (#reason-text, sessionStorage) зелен на прогоне 5.1; нулевая
      network-активность страницы (инспекция запросов); скриншот-сверка
      визуальной эквивалентности.
      FR: FR-13, FR-17. NFR: NFR-27. Зависит от: 1.1.

- [ ] 2.2 [P][code] frontend/vue/src/pages/review-form/ — полный перенос
      формы отзыва, wiring js/review-form.js 1:1 (детали — design.md
      «Страница /review на Vue»): ?instructor= → числовой id, без id →
      location.href='/my-requests' (301 → /cabinet#/my-requests); нет
      токена → toLogin; GET /api/auth/me → #uname/#avatar; GET
      /api/student/instructors/{id} → карточка (#i-name, #i-ava, #i-sub
      стаж+авто, #i-rating агрегат FR-35; not ok → тост «Инструктор
      не найден»); звёзды hover/click + LABELS + #stars-lab; #review-text
      maxlength 1000 + #counter «N / 1000» (класс over); #send активна при
      rating>0, текст непустой, ≤1000; POST .../reviews — ТОЛЬКО 401 →
      toLogin (403 — тост, NFR-2), 200 → «Отзыв отправлен» + тост, 409 →
      «Отзыв уже отправлен» + тост + кнопка активна, прочие → тост
      ошибки; состояние — данными сервера при каждой загрузке (reload
      показывает форму заново); тосты #toast 3200 мс (shared/utils.js);
      v-html ЗАПРЕЩЕН; id-якоря e2e дословно (#view-form/#view-done/
      #done-title/#send/#review-text/#i-name/#i-ava/#i-sub/#i-rating/
      #stars-lab/#counter/#toast/#uname/#avatar, .star[data-v]).
      Готовность: якоря TC-UI-017/TC-UI-018 зелен на прогоне 5.1 без
      правок сценариев; скриншот-сверка визуальной эквивалентности;
      контракты вызовов — через src/shared/api.js (без изменений).
      FR: FR-5, FR-34, FR-35. NFR: NFR-2, NFR-5, NFR-27. Зависит от: 1.1.

## 3. Переключение маршрутов и удаление легаси

- [ ] 3.1 [code] удаление легаси + перевод тестов-потребителей: удалить
      frontend/instructor-rejected.html, frontend/js/instructor-rejected.js,
      frontend/review-form.html, frontend/js/review-form.js; исключить
      "/instructors/rejected" и "/review" из легаси-отдачи `_PAGE_ROUTES`.
      Перевод потребителей (прецедент 2.3 пилота; границы — design.md
      «Границы правок тестов»): tests/web/test_instructor_pages.py
      (test_rejected_page_exists_and_reason_wiring — источник: вход +
      App.vue; тексты/ключ sessionStorage/поведенческие фрагменты —
      дословно, стековые фрагменты legacy — на эквиваленты Vue);
      tests/api/test_s3_backend.py (TC-S3BE-041: носитель review — вход +
      компонент Vue, needle POST-URL дословно); tests/web/
      test_ui_playwright.py — ТОЛЬКО два переноса пути чтения (TC-UI-019:
      frontend/review-form.html → frontend/vue/review-form.html;
      NIT-4 test_s4_pages_tag_balance: тот же перенос) — утверждения
      дословно, сценарии не тронуты.
      Готовность: grep по репо — ссылок на 4 легаси-файла нет (кроме
      исторических docstring/архива); `git diff tests/
      test_ui_playwright.py` — только два переноса пути чтения;
      tests/test_instructor_pages.py + tests/api/test_s3_backend.py
      зеленые.
      FR: FR-84, FR-85. NFR: NFR-27. Зависит от: 2.1, 2.2 (страницы
      существуют — перевод тестов на их носители).

- [ ] 3.2 [code] backend/app.py — регистрация двух страниц в `_PAGE_ROUTES`:
      значения с маркером каркаса "vue:instructors-rejected.html" и
      "vue:review-form.html"; цикл отдачи при префиксе "vue:" читает
      VUE_DIST_DIR (404 при отсутствии dist — паттерн пилотного хендлера),
      media_type text/html; charset=utf-8; пилотный хендлер
      /instructors/pending НЕ трогается; статика /vue/assets/* — БЕЗ
      ИЗМЕНЕНИЙ (покрывает новые чанки); _PAGE_REDIRECTS и /api/* — БЕЗ
      ИЗМЕНЕНИЙ. Выполняется в одной сессии с 3.1 (без промежуточного
      пуша — design.md «Роуты и статика»).
      Готовность: GET /instructors/rejected и GET /review отдают входы
      dist (html со ссылками на /vue/assets); test_auth_route::
      test_new_static_routes_served и test_s3_backend::test_s4_static_
      route_review зеленые (после сборки dist); остальные маршруты
      карты — как прежде.
      FR: FR-84. NFR: NFR-27. Зависит от: 3.1.

## 4. Бюджеты чанков NFR-26 на артефактах сборки

- [ ] 4.1 [tests] прогон сборки + замер gzip: `npm ci && npm run build &&
      npm run check:budgets` (скрипт 1.1): (а) каждый vendor-чанк
      ≤150 КБ gzip; (б) JS первого захода КАЖДОЙ страницы (page-чанк +
      static-import graph: shared + vue) ≤200 КБ gzip — отдельно для
      instructors-pending, instructors-rejected, review-form; (в) в бандле
      страницы нет чужих page-чанков (multi-entry). Фактические размеры
      всех чанков — в отчете задачи.
      Готовность: оба бюджета соблюдены на трех страницах; при превышении
      — сокращение зависимостей (без новых библиотек), не ослабление
      проверки.
      FR: FR-84. NFR: NFR-26. Зависит от: 1.1, 2.1, 2.2 (финальные чанки).

## 5. e2e-совместимость и приемка партии

- [ ] 5.1 [tests] полный прогон Playwright-набора БЕЗ правок сценариев:
      `npm ci && npm run build` → `pytest tests/test_ui_playwright.py`
      (60 сценариев; фикстура server поднимает uvicorn backend.app:app,
      маршруты /instructors/rejected и /review отдают dist). Правки
      test_ui_playwright.py в этом пакете — только два переноса источника
      чтения (3.1): `git diff` контроль; селекторы/маршруты/ожидания
      сценариев не тронуты. Якоря партии: TC-S9UI-003 (rejected-редирект
      с причиной, #reason-text), TC-UI-017/TC-UI-018 (форма отзыва
      1:1), TC-UI-019 (back-links). Регресс смежных доменов:
      `pytest tests/web/test_instructor_pages.py tests/api/
      test_s3_backend.py tests/api/test_auth_route.py tests/web/
      test_login_modal.py` зеленый; полный `pytest tests/` — зеленый
      (после сборки dist). Валидации: `openspec validate
      add-vue-s11-status-forms --strict` и `openspec validate --all
      --strict` зеленые.
      Готовность: полный набор e2e passed, 0 правок сценариев (кроме
      двух задокументированных переносов источника чтения); маршруты и
      /api/* — без ломающих изменений.
      FR: FR-85. NFR: NFR-27. Зависит от: 3.2, 4.1.

## Зависимости

- 1.1 (входы+бюджет-скрипт) → { 2.1 [P], 2.2 [P] } — страницы параллятся
  (разные каталоги src/pages/, общий shared/utils.js создает 1.1).
- 2.1 и 2.2 → 3.1 (перевод тестов-потребителей требует готовых носителей);
  3.1 → 3.2 (подряд в одной сессии, без промежуточного пуша).
- 4.1 — после 2.1/2.2 (финальные чанки); 5.1 — последняя (после 3.2 и 4.1).

## Рекомендации к нарезке

- Швы: (а) rejected-страница (2.1) и (б) review-страница (2.2) — параллельны
  [P] после 1.1; интеграция (3.1+3.2) — одна сессия.
- НЕЛЬЗЯ делить: 3.1 и 3.2 (удаление легаси без немедленной регистрации
  маршрутов оставляет маршрут без отдачи); 4.1 нельзя выполнять до финала
  2.1/2.2 (бюджеты считаются по финальным чанкам); 5.1 — после всех.
- Общая зона файлов (не делить между задачами): frontend/vue/vite.config.mjs
  и scripts/check-budgets.mjs — только 1.1; backend/app.py — только 3.1/3.2;
  tests/web/test_ui_playwright.py — только 3.1 (два переноса);
  src/shared/ — только 1.1.

## План тестовых прогонов (наборы — отдельные делегации-раннеры)

1. **API/регресс**: `pytest tests/` (кроме playwright) — после сборки dist
   (маршруты партии отдают 404 без нее); стенд: репо, env-заглушки
   conftest; ~5–10 мин.
2. **e2e полный**: `pytest tests/test_ui_playwright.py` — стенд:
   собранный dist (`npm ci && npm run build` ДО прогона — обязательный
   шаг), uvicorn на эфемерном порту, Chromium headless; ~15–30 мин.
3. **Валидации**: `openspec validate --all --strict` +
   `npm run check:budgets` — секунды, локально без стенда.
Прогоны 1 и 2 НЕ объединять в один сабагент-раннер (разные стенды и
длительности); сборка dist выполняется один раз до прогонов 2, 4.1 и
регресса 5.1.
