# Design: add-vue-s11-status-forms

Источники решений: ADR-008 (architecture/adr/008-vue3-vite-migration.md —
стек, multi-entry, бюджеты, план С10–С11 «одноцелевые экраны и простые
формы»); решение Заказчика 2026-11-06 «Продолжаем пункт 1 из бэклога»
(BACKLOG.md #1); прецедент — пакет add-vue-framework-pilot
(openspec/changes/archive/2026-11-05-add-vue-framework-pilot/: задачи
2.1/2.3/4.1, design.md); ADR-001 (статика тем же сервисом), ADR-006
(multi-stage образ); существующий каркас frontend/vue/ (задачи пилота
выполнены, пилот в проде — PR#107).

## Baseline (что есть, без этого пакета не меняется)

- Каркас Vue 3 + Vite — frontend/vue/: multi-entry (вход
  instructors-pending.html), manualChunks (vue → 'vue', сторонние пакеты →
  чанки по пакетам, /src/shared/ → 'shared'), base '/vue/', dist не в git,
  pinned-версии (vue 3.5.44, vite 8.3.5, @vitejs/plugin-vue 6.0.10),
  dev-proxy /api/* → 127.0.0.1:8390, скрипт npm run check:budgets.
- backend/app.py: `_PAGE_ROUTES` — карта маршрутов страниц (FileResponse из
  frontend/); пилотный маршрут /instructors/pending — ВНЕ карты, выделенный
  хендлер с отдачей `frontend/vue/dist/instructors-pending.html` (404 при
  отсутствии dist); статика каркаса `GET /vue/assets/{path}` (content-type
  по суффиксу явно: .js/.css; обход каталогов исключен); редиректы
  `_PAGE_REDIRECTS` (/my-requests → /cabinet#/my-requests, 301).
- Контур: Dockerfile уже содержит node builder-этап (npm ci → npm run
  build, runtime забирает dist через COPY --from); CI flow.yml собирает
  dist ПЕРЕД pytest; compose/nginx — без сборки.
- Легаси в объеме партии: `frontend/instructor-rejected.html` +
  `frontend/js/instructor-rejected.js` (экран отказа: причина из
  sessionStorage «instructor_rejected_reason», скрытый блок #reason-block/
  #reason-text, ноль запросов) и `frontend/review-form.html` +
  `frontend/js/review-form.js` (форма отзыва, wiring — see ниже).
- Контракты (НЕ меняются): логин route/reason (инструктор deny →
  route='rejected', reason — пишет модалка входа landing.js в
  sessionStorage; спека instructor-auth «Роутинг после входа по статусу»);
  POST /api/student/instructors/{id}/reviews (backend/reviews.py: сессия
  student; 403 без принятой пары — NFR-2; 422 rating/text; 409 повтор —
  UNIQUE, NFR-5); GET /api/student/instructors/{id} (карточка + агрегат
  FR-35); GET /api/auth/me (ФИО, FR-5); редиректы _PAGE_REDIRECTS.

## Потребители легаси-файлов (полный список, судьба каждого)

| Потребитель | Что читает | Судьба в пакете |
|---|---|---|
| backend/app.py `_PAGE_ROUTES` (:52, :62) | отдача файлов | 3.1 — исключение из карты, 3.2 — регистрация с отдачей dist |
| tests/web/test_instructor_pages.py:283–303 (test_rejected_page_exists_and_reason_wiring) | page()+frontend_source легаси | 3.1 — ПЕРЕВОД на вход+компонент Vue (прецедент 2.3 пилота; правка разрешена) |
| tests/api/test_s3_backend.py:1725–1737 (test_s4_pages_wired_to_real_api_shapes, TC-S3BE-041) | frontend_source("review-form.html"), needle POST-URL | 3.1 — перенос носителя на вход+компонент Vue, needle контракта дословно |
| tests/api/test_s3_backend.py::test_s4_static_route_review (TC-S3BE-040) | GET /review → 200 «Оставить отзыв» | без правок: маршрут тот же, статическая разметка входа 1:1 содержит заголовок; dist в CI/образе есть |
| tests/api/test_auth_route.py::test_new_static_routes_served | GET /instructors/rejected → 200 text/html | без правок: маршрут тот же, отдача dist (как у пилотного маршрута) |
| tests/web/test_ui_playwright.py:1221 (TC-UI-019 test_back_links_lead_to_role_home) | frontend/review-form.html: assert 'href="/my-requests"' | 3.1 — перенос пути чтения на frontend/vue/review-form.html; утверждение дословно (разметка входа содержит ссылку) |
| tests/web/test_ui_playwright.py:4418–4457 (test_s4_pages_tag_balance, NIT-4) | frontend/review-form.html: баланс тегов | 3.1 — перенос пути чтения на frontend/vue/review-form.html (вход — валидный HTML) |
| tests/web/test_ui_playwright.py: TC-S9UI-003, TC-UI-017, TC-UI-018 | поведенческие (маршруты, #reason-text, #view-form/#send/#done-title, .star[data-v]) | БЕЗ ПРАВОК — id-якоря сохраняются в Vue-версии (NFR-27) |
| tests/web/test_login_modal.py:111–120 | landing.js (route='rejected' → sessionStorage) | без правок — landing.js не затрагивается (упоминание файла в docstring — историческое) |

## Границы правок тестов (NFR-27 — разграничение)

- «0 правок сценариев» по-прежнему означает: селекторы, маршруты, ожидания
  и логика сценариев tests/test_ui_playwright.py не переписываются;
  поведенческие якоря партии (TC-S9UI-003, TC-UI-017, TC-UI-018) —
  дословно.
- КОНФЛИКТ, который партия обязана снять явно: два СТАТИЧЕСКИХ файла-
  потребителя в test_ui_playwright.py (TC-UI-019 — grep-маркер
  `href="/my-requests"`; NIT-4 tag-balance) читают
  `frontend/review-form.html` напрямую — удаление файла по ADR-008 п.4
  роняет их с FileNotFoundError. Решение — прецедент 2.3 пилота («перевод
  тестов-потребителей legacy-файла на новый вход — разрешенная и ожидаемая
  работа пакета»): путь чтения обоих переключается на вход каркаса
  `frontend/vue/review-form.html`. Это НЕ правка сценариев: утверждения,
  селекторы и семантика проверок дословны, меняется только носитель
  источника (монолит → вход), e2e-сценарии остаются зелеными на том же
  прогоне. Правка ограничена ДВУМЯ строками пути чтения; контроль —
  `git diff tests/test_ui_playwright.py` содержит только эти два переноса
  (задача 3.1, проверка в 5.1).
- tests/web/test_instructor_pages.py и tests/api/test_s3_backend.py —
  легаси-тесты-потребители страниц: правки разрешены (вне
  test_ui_playwright.py; тот же прецедент).

## Точки входа Vite (решение)

- vite.config.mjs, `rollupOptions.input` дополняется двумя входами (порядок
  и правила пилота — без изменений):
  - `instructors-rejected` → `frontend/vue/instructors-rejected.html`
    (dist/instructors-rejected.html; имя по сегменту маршрута — паттерн
    пилота instructors-pending.html);
  - `review-form` → `frontend/vue/review-form.html`
    (dist/review-form.html; историческое имя артефакта сохранено —
    маршрут /review).
- Вход = статическая разметка экрана (эквивалент legacy 1:1) + модуль-скрипт
  `/src/pages/<page>/main.js`; до гидрации видна та же разметка (паттерн
  пилота; «Разметку держать синхронной с App.vue»).
- Страницы: `frontend/vue/src/pages/instructor-rejected/` (main.js,
  App.vue, styles.css) и `frontend/vue/src/pages/review-form/` (main.js,
  App.vue, styles.css). Стили — дословный перенос из legacy html (без
  редизайна).
- Shared-чанк: `src/shared/api.js` уже содержит полный клиент пилота
  (getToken/setToken/toLogin/api/handleAuthFail/apiGet/apiSend/postJSON —
  контракты не меняются); дополняется `src/shared/utils.js` — перенос
  toast (единый #toast, ms-параметр) и expWord из frontend/js/utils.js
  (это СВОЙ код в чанке shared, не библиотека; правка frontend/js/*.js
  НЕВМОЖЕНА — им продолжают пользоваться немигрированные монолиты).
- scripts/check-budgets.mjs: карта page-чанков расширяется до трех
  (instructors-pending, instructors-rejected, review-form); замыкание
  первого захода и проверка «чужих page-чанков» — по КАЖДОЙ странице;
  бюджеты не меняются (NFR-26).
- Новых npm-зависимостей НЕТ; pinia/vue-router НЕ вводятся (ОВ-3).

## Роуты и статика (backend/app.py)

- 3.1: оба маршрута исключаются из легаси-отдачи карты
  (`"/instructors/rejected"`, `"/review"`); 3.2 — регистрация в
  `_PAGE_ROUTES` с маркером каркаса: значение вида
  `vue:instructors-rejected.html` / `vue:review-form.html`; цикл отдачи при
  префиксе `vue:` читает файл из `VUE_DIST_DIR`, при отсутствии — 404
  (паттерн пилотного хендлера), media_type `text/html; charset=utf-8`.
  Карта остается единственным декларативным реестром маршрутов страниц —
  следующие партии добавляют страницы одной строкой.
- Пилотный хендлер `/instructors/pending` НЕ трогается (работает как есть;
  унификация с vue:-механикой — консолидация будущей партии, не в объеме).
- Статика `/vue/assets/{path}` уже существует и покрывает новые чанки
  (.js/.css в карте суффиксов) — БЕЗ ИЗМЕНЕНИЙ; шрифты/картинки страницам
  не нужны (системные шрифты, эмодзи-глифы — как в legacy).
- `_PAGE_REDIRECTS` (/my-requests 301 → /cabinet#/my-requests) — БЕЗ
  ИЗМЕНЕНИЙ (обе страницы зависят от него: back-ссылка review и редирект
  без ?instructor=).
- `/api/*` — БЕЗ ИЗМЕНЕНИЙ (NFR-27). review-form вызывает те же
  эндпоинты, что legacy (последовательность и заголовки — через
  src/shared/api.js, идентичный frontend/js/api.js).
- Между 3.1 и 3.2 существует переходное состояние (маршрут без отдачи);
  задачи выполняются подряд в одной сессии, промежуточный пуш/PR не
  делается; e2e-гейт партии — 5.1 после 3.2.

## Dockerfile / compose / CI — изменений сборки НЕ требуется

- node builder-этап собирает dist из ВСЕХ входов vite.config.mjs одной
  командой — новые входы попадают в образ автоматически; runtime уже
  забирает `frontend/vue/dist` целиком.
- docker-compose.yml, nginx (reverse proxy), .dockerignore — БЕЗ
  ИЗМЕНЕНИЙ; CI flow.yml уже делает `npm ci && npm run build` перед pytest
  — покрывает оба новых входа.
- bare-metal (FR-57): порядок `npm ci && npm run build` перед деплоем —
  без изменений (комментарий Dockerfile пилота).
- Локальный регресс: перед `pytest tests/` обязательна сборка dist —
  маршруты отдают 404 без нее (то же поведение, что у пилотного маршрута
  с Спринта 9; CI собирает всегда).

## Страница /instructors/rejected на Vue (2.1)

- Перенос 1:1 (без редизайна): шапка (бренд «СберАвтошкола», «← Вернуться
  на лендинг» → /instructors), карточка (иконка, kicker «Заявка
  инструктора», h1 «Заявка отклонена», пояснение), блок причины
  (#reason-block — скрыт по умолчанию; #reason-text), кнопки «На главную»
  (→ /) и «О лендинге для инструкторов» (→ /instructors), футер. Тексты —
  дословно (языковой зонинг RU). Якорь e2e: #reason-text (TC-S9UI-003).
- Поведение js/instructor-rejected.js — в App.vue (onMounted): чтение
  sessionStorage «instructor_rejected_reason» в try/catch (недоступен —
  без причины); значение есть → текст в #reason-text и показ блока;
  пусто/нет → блок скрыт. Статус при загрузке НЕ проверяется, запросов
  НОЛЬ (наследование FR-17: причина приходит только из ответа логина —
  контракт instructor-auth route/reason не меняется; пишет его
  landing.js, он не затрагивается).
- Сессионного контракта у страницы нет: открытие по прямой ссылке —
  нейтральный экран без персональной причины (не раскрывать чужую —
  существующее решение design).

## Страница /review на Vue (2.2)

- Перенос wiring 1:1 из frontend/js/review-form.js (все реакции — те же,
  в том же порядке):
  - сессия: нет токена → toLogin() (redirect /, модалка входа); на GET-ах
    401/403 → handleAuthFail → toLogin (единый паттерн кабинетов);
  - query: `?instructor=` → числовой id; 0/нет → `location.href =
    '/my-requests'` (далее 301 → /cabinet#/my-requests — BUG-047);
  - ФИО/аватар ученика: GET /api/auth/me → #uname, инициалы #avatar (FR-5);
  - контекст: GET /api/student/instructors/{id} → карточка (#i-name — ФИО,
    #i-ava — инициалы, #i-sub — «Стаж N <expWord>» + автомобили через
    «·», #i-rating — агрегат FR-35: «X.X ★» + «N отзывов учеников» либо
    «☆» + «отзывов пока нет»); не найден (not ok) → тост «Инструктор
    не найден»;
  - звёзды: hover — предпросмотр, mouseleave — возврат, click — фиксация;
    подпись #stars-lab (LABELS 1–5, «Оценка: …» через <b>); валидация
    кнопки #send: rating>0 И текст непустой И длина ≤1000;
  - textarea maxlength=1000, счетчик #counter «N / 1000», класс over при
    переполнении;
  - POST /api/student/instructors/{id}/reviews {rating, text:trim}:
    ТОЛЬКО 401 → toLogin (403 — бизнес-ошибка тостом, NFR-2);
    200/ok → состояние «Отправлен» (#view-form скрыта, #view-done видна,
    #done-title «Отзыв отправлен») + тост «Отзыв отправлен: оценка X из 5.
    Спасибо — он появится в карточке инструктора.»; 409 → состояние
    «уже оставлен» (#done-title «Отзыв уже отправлен») + тост «Отзыв: вы
    уже оставляли отзыв этому инструктору.» + кнопка обратно активна;
    прочие → тост (error сервера || «Не удалось отправить отзыв»),
    кнопка активна;
  - состояние выбирается ДАННЫМИ СЕРВЕРА при каждой загрузке (reload
    после 200/409 показывает форму заново — поведение TC-UI-017).
- Тосты — единый паттерн legacy: элемент #toast, длительность 3200 мс
  (baseToast review-form), один таймер на страницу (перенос в
  src/shared/utils.js).
- URL вызовов инструктора — строковой конкатенацией как в legacy
  (`'/api/student/instructors/'+instructorId+'/reviews'`): needle
  TC-S3BE-041 (`instructors/'+instructorId+'/reviews`) проверяется
  дословно по носителю «вход + компонент» — template literals НЕ
  вводить (иначе перенос в 3.1 уронит needle).
- DOM-якоря e2e сохраняются дословно: #uname, #avatar, #i-name, #i-ava,
  #i-sub, #i-rating, #stars-lab, #review-text, #counter, #send, #view-form,
  #view-done, #done-title, #toast, кнопки .star с data-v="1..5";
  back-ссылка `<a class="back" href="/my-requests">← Назад к заявкам</a>` —
  в статической разметке входа (якорь TC-UI-019).
- XSS-правило legacy («пользовательские строки — только textContent»)
  воспроизводится интерполяцией Vue ({{ }} — экранирование по умолчанию);
  v-html ЗАПРЕЩЕН на странице (наследование review-001 add-s3-frontend-links).
- Задокументированные отклонения от мокапа legacy (наследуются без
  изменений): в done-состоянии нет done-stars/done-text/даты (свой отзыв
  из API не возвращается — после reload отрисовать неоткуда); ссылка
  «Вернуться к моим заявкам» вместо «Вернуться к инструктору»;
  back-ссылки шапки убраны (BUG-047).

## Обработка ошибок форм — тосты как в legacy (сводно)

| Ответ | Реакция (1:1 legacy) |
|---|---|
| GET-и: 401/403, нет токена | toLogin() — редирект на главную, к модалке входа |
| POST: 401 | toLogin() (только 401 — сессия) |
| POST: 403 | тост с error сервера (бизнес-ошибка NFR-2, БЕЗ редиректа) |
| POST: 409 | done «Отзыв уже отправлен» + тост + кнопка активна |
| POST: 422/прочие | тост (error сервера || «Не удалось отправить отзыв») |
| GET контекста: not ok | тост «Инструктор не найден» |
| network (status 0) | ветка «прочие» — тост «Не удалось отправить отзыв» |
| rejected-страница: sessionStorage недоступен | тихо, без причины (try/catch) |

## Решения по НФТ

- **NFR-26:** бюджеты проверяются на артефактах сборки
  (npm run check:budgets — расширение 1.1: три page-чанка, замыкание
  первого захода по каждой странице; gzip CLI `gzip -c | wc -c`): каждый
  vendor-чанк ≤150 КБ gzip; JS первого захода КАЖДОЙ из трех страниц
  ≤200 КБ gzip; в бандле страницы нет чужих page-чанков (multi-entry).
  Review-страница — та же зависимость vue + shared, запас бюджета
  сохраняется; замеры — в отчете 4.1.
- **NFR-27:** полный набор tests/test_ui_playwright.py зелен без правок
  СЦЕНАРИЕВ (допустимый дифф — только два переноса источника чтения,
  см. «Границы правок тестов»); маршруты, редиректы и /api/* — без
  ломающих изменений; статика /vue/assets — существующее добавление.
- **NFR-2/NFR-5:** серверные проверки POST отзыва не трогаются
  (backend/reviews.py без изменений) — клиент воспроизводит только
  реакции.
- Наследуются без изменений: ADR-001 (статика тем же сервисом), FR-57
  (bare-metal), ADR-006 (multi-stage, pinned), NFR-13/14 (не затрагиваются).

## Сознательные ограничения (задокументированы)

- dist и node_modules — не в git (наследование каркаса); входы и компоненты
  — в git.
- Пилотный хендлер /instructors/pending остается выделенным вне карты —
  механическая унификация не делается (риск для работающего маршрута
  без функциональной выгоды; консолидация — будущая партия).
- Переходное состояние между 3.1 и 3.2 (маршрут без отдачи) существует
  только внутри одной сессии работ; гейт — 5.1 после 3.2.
- Два источника чтения в test_ui_playwright.py переключаются на вход
  каркаса — задокументированное исключение из «0 правок» (см. «Границы
  правок тестов»); альтернативы отклонены: сохранение легаси-файла как
  «мертвого» (параллельное существование версий — против ADR-008 п.4),
  правка карты путей через conftest (шире необходимого диффа).
- done-состояние review без деталей своего отзыва — наследованное
  отклонение от мокапа (не «регресс» миграции; воспроизводится 1:1).
- Тосты — без библиотеки компонентов: перенос собственного хелпера в
  shared-чанк (новый vendor-чанк против бюджетов NFR-26 не вводится).
- Контроль бюджетов остается приемочным ручным шагом (не CI-гейт) —
  наследование ограничения пилота.
- Тексты/заголовки/стили — только перенос текущих (директива «без большого
  переписывания»; редизайн — вне миграции).

## Соответствие ADR-001/006/008

Отступлений нет: multi-entry MPA (страница = отдельная точка входа,
SPA/vue-router/pinia запрещены — ОВ-3); замена монолита целиком с
удалением легаси (ADR-008 п.4); vendor-сплит и бюджеты NFR-26 — правила
пилота; статика тем же сервисом (ADR-001) через существующие `/vue/assets`;
контур доставки без изменений (ADR-006, builder-этап уже в Dockerfile);
критерий приема — зеленый полный e2e (ADR-008 п.6, FR-85/NFR-27).
