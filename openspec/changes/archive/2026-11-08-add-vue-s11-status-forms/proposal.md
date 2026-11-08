# Change: add-vue-s11-status-forms

## Why (Зачем)

Спринт 11, пункт 1 бэклога «Фронтенд-фреймворк — продолжение миграции»
(BACKLOG.md #1): решение Заказчика 2026-11-06 — «Продолжаем пункт 1 из
бэклога». Каркас Vue 3 + Vite и пилот /instructors/pending — в проде
(Спринт 9, PR#107, ADR-008); фронт остается на 12 HTML-монолитах
`frontend/*.html`. Следующая партия плана ADR-008 («Спринт 10–11:
одноцелевые экраны и простые формы») — статусный экран отказа и форма
отзыва: обе страницы одноцелевые, ноль сложного состояния — тот же паттерн
«экран = точка входа», что у пилота, плюс первая ФОРМА на новом стеке.

Источник требований: ADR-008
(`architecture/adr/008-vue3-vite-migration.md`, план Спринты 9–11);
решение Заказчика 2026-11-06 (пункт 1 бэклога); NFR-26 (бюджеты чанков
150/200 КБ gzip), NFR-27 (e2e-совместимость); FR-13/FR-17 (экран отказа,
роутинг логина), FR-5/FR-34/FR-35 (форма отзыва, агрегат рейтинга).

## What Changes (Что меняет)

- Миграция страницы `/instructors/rejected` (экран отказа заявки, пара к
  пилоту `/instructors/pending`): новая Vue-страница
  `frontend/vue/src/pages/instructor-rejected/` + вход
  `frontend/vue/instructors-rejected.html`; причина отказа — как сейчас из
  ответа логина (route/reason → sessionStorage
  «instructor_rejected_reason», пишет модалка входа на лендинге) —
  КОНТРАКТ НЕ МЕНЯЕТСЯ. Страница — чистый экран: ноль запросов при
  загрузке (наследование behavior legacy js/instructor-rejected.js).
- Миграция страницы `/review` (форма отзыва): новая Vue-страница
  `frontend/vue/src/pages/review-form/` + вход
  `frontend/vue/review-form.html`; wiring legacy (frontend/review-form.html
  + frontend/js/review-form.js) воспроизводится 1:1 — query ?instructor=,
  редирект при отсутствии пары (/my-requests → 301 →
  /cabinet#/my-requests), карточка инструктора, звёзды/счетчик/валидация,
  состояния «отправлен»/«уже оставлен» данными сервера, тосты. Контракт
  POST отзыва (backend/reviews.py) НЕ МЕНЯЕТСЯ.
- Сборка: vite.config.mjs получает два новых входа (multi-entry MPA —
  страница = отдельная точка входа, ОВ-3; SPA/vue-router/pinia
  ЗАПРЕЩЕНЫ); scripts/check-budgets.mjs расширяется на три page-чанка.
  Dockerfile, docker-compose.yml, nginx, CI — БЕЗ ИЗМЕНЕНИЙ: node
  builder-этап уже собирает dist из всех входов, статика /vue/assets уже
  отдается backend/app.py — только регистрация двух страниц.
- backend/app.py: маршруты `/instructors/rejected` и `/review` в
  `_PAGE_ROUTES` переключаются на отдачу входов из
  `frontend/vue/dist` (регистрация в карте с маркером каркаса); legacy-файлы
  `frontend/instructor-rejected.html`, `frontend/js/instructor-rejected.js`,
  `frontend/review-form.html`, `frontend/js/review-form.js` удаляются
  (замена монолита целиком, ADR-008 п.4). Остальные 10 маршрутов страниц и
  все `/api/*` — без изменений.
- Тесты-потребители legacy-файлов переводятся на новые носители (прецедент
  2.3 пилота): tests/web/test_instructor_pages.py,
  tests/api/test_s3_backend.py и ДВА источника чтения файлов в
  tests/web/test_ui_playwright.py (механический перенос пути чтения на вход
  каркаса — сценарии, селекторы и ожидания дословно; границы — design.md
  «Границы правок тестов»). Набор e2e остается зеленым без правок сценариев
  (NFR-27): якоря TC-S9UI-003 (rejected, #reason-text), TC-UI-017/TC-UI-018
  (review), TC-UI-019 (back-links).
- Проверка бюджетов NFR-26 на артефактах сборки (gzip-размеры чанков dist:
  каждый vendor-чанк ≤150 КБ gzip; JS первого захода каждой страницы
  ≤200 КБ gzip) — приемочный шаг партии.

## Impact (Последствия)

- Код: `frontend/vue/vite.config.mjs` (+2 входа),
  `frontend/vue/instructors-rejected.html`, `frontend/vue/review-form.html`
  (новые входы), `frontend/vue/src/pages/instructor-rejected/`,
  `frontend/vue/src/pages/review-form/` (новые страницы),
  `frontend/vue/src/shared/` (расширение общих утилит — перенос
  toast/expWord из js/utils.js; api.js уже перенесен пилотом),
  `frontend/vue/scripts/check-budgets.mjs` (+2 page-чанка);
  `backend/app.py` (две строки карты `_PAGE_ROUTES` + выбор источника
  отдачи). Dockerfile/.dockerignore/docker-compose.yml/nginx/CI — БЕЗ
  ИЗМЕНЕНИЙ.
- Удаление: `frontend/instructor-rejected.html`,
  `frontend/js/instructor-rejected.js`, `frontend/review-form.html`,
  `frontend/js/review-form.js` (после переключения маршрутов; остальные
  10 монолитов не трогаются).
- Тесты: tests/web/test_instructor_pages.py (перевод
  test_rejected_page_exists_and_reason_wiring на вход каркаса — разрешенная
  правка, прецедент 2.3); tests/api/test_s3_backend.py (перенос носителя
  wiring-проверки TC-S3BE-041); tests/web/test_ui_playwright.py — ТОЛЬКО
  два перевода источника чтения (TC-UI-019, NIT-4 tag-balance), сценарии
  не переписываются (NFR-27).
- Master-spec: ADDED домен Frontend — «Статусный экран отказа заявки на
  Vue (/instructors/rejected)», «Форма отзыва на Vue (/review)».
- Кейпабилити БЕЗ дельт (проверено по openspec/specs/): navigation
  (маршруты и навигационные ссылки не меняются), reviews (контракт POST
  и агрегат — без изменений), StudentFlow (переход polling → экран
  отказа сохранен, TC-S9UI-003 зеленый без правок), instructor-auth
  (роутинг логина route/reason — без изменений), instructor-application
  (не затрагивается).
- Зависимости: нет новых пакетов npm (только vue — уже в каркасе);
  зависимостей от параллельных change-пакетов нет.

## Out of scope / допущения

- Остальные страницы плана ADR-008 (`/registered`, `/admin-login`,
  `/instructor/cabinet-stub`, лендинги, анкета с multipart, кабинеты) —
  следующие партии; в объеме только /instructors/rejected и /review.
- Монолитный SPA, vue-router, pinia — НЕ вводятся (ОВ-3: страница =
  отдельная точка входа; обеим страницам достаточно локального состояния).
- Редизайн обеих страниц, перенос текстов/заголовков иными словами —
  вне объема: визуальная эквивалентность текущим экранам (наследование
  директивы «без большого переписывания» ADR-008).
- Изменения контрактов: POST /api/student/instructors/{id}/reviews,
  GET /api/student/instructors/{id}, GET /api/auth/me, логин route/reason,
  редиректы `_PAGE_REDIRECTS` (/my-requests → /cabinet#/my-requests) —
  НЕ меняются; `/api/*` каркасом не затрагиваются (NFR-27).
- Унификация пилотного хендлера /instructors/pending с новым механизмом
  отдачи карты — вне объема (пилот не трогается; унификация —
  консолидация будущей партии).
- Новые сторонние библиотеки (UI-кит, toast-библиотеки) — не в объеме;
  правило бюджета ADR-008 действует.

## Отслеживание

- FR-13, FR-17 (экран отказа, причина из логина) →
  specs/Frontend/spec.md «Статусный экран отказа заявки на Vue
  (/instructors/rejected)»; tasks 2.1, 3.1.
- FR-5, FR-34, FR-35 (форма отзыва, агрегат рейтинга) →
  specs/Frontend/spec.md «Форма отзыва на Vue (/review)»; tasks 2.2.
- FR-84 (multi-entry, постраничная миграция, ADR-008) → обе дельты;
  tasks 1.1, 3.2.
- FR-85 + NFR-27 (e2e без правок сценариев) → дельты (сценарии-якоря);
  tasks 3.1, 5.1.
- NFR-26 (бюджеты 150/200 КБ gzip на артефактах) → tasks 1.1, 4.1.
- TC-S9UI-003, TC-UI-017, TC-UI-018, TC-UI-019, TC-S3BE-040/041 →
  якоря приемки; tasks 3.1, 5.1.
