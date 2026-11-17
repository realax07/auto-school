# Design: add-vue-s12-landing-apply

Источники решений: ADR-008 (architecture/adr/008-vue3-vite-migration.md —
стек, multi-entry, бюджеты, план «лендинги, анкета с multipart»);
решение Заказчика 2026-11-08 (decisions/2026-11-08-sprint12-go.md —
состав С12, включая BUG-062); прецеденты — add-vue-framework-pilot
(задачи 2.1/2.3/4.1) и add-vue-s11-status-forms (архивы: структура
пакета, vue:-маркеры в _PAGE_ROUTES, переносы источников чтения,
NFR-26 свод С11); BUG-062 (test-model/bugs/BUG-062.md, план фикса);
BUG-055/056 (семантика модалки входа); BUG-059/060/061 (прецедент
«мокапы choice-a/b синхронно» + негативные инварианты TC-UI-059).

## Baseline (что есть, без этого пакета не меняется)

- Каркас Vue 3 + Vite — frontend/vue/: multi-entry (входы
  instructors-pending, instructors-rejected, review-form),
  manualChunks (vue → 'vue', сторонние пакеты → чанки по пакетам,
  /src/shared/ → 'shared'), base '/vue/', dist не в git, pinned-версии
  (vue 3.5.44, vite 8.3.5, @vitejs/plugin-vue 6.0.10), dev-proxy /api/*
  → 127.0.0.1:8390, скрипт npm run check:budgets (3 page-чанка).
- backend/app.py: `_PAGE_ROUTES` — карта маршрутов страниц; значения
  с маркером `vue:<вход dist>` читаются из VUE_DIST_DIR (404 при
  отсутствии dist; media_type text/html; charset=utf-8) — механика
  С11; пилотный хендлер /instructors/pending — вне карты, не трогается;
  статика `GET /vue/assets/{path}` (.js/.css) существует.
- Контур: Dockerfile содержит node builder-этап; CI flow.yml собирает
  dist ПЕРЕД pytest; compose/nginx — без сборки.
- Легаси в объеме: `frontend/index.html` + `frontend/js/landing.js`
  (лендинг: hero, шаги, чат-бар-заглушка, плитки, модалки m-login/
  m-register с consent; wiring — постJSON через js/api.js) и
  `frontend/instructor-apply.html` + `frontend/js/apply.js` (анкета:
  multipart, ВУ с миниатюрой BUG-048, consent FR-77).
- Общий контур модалок: та же пара оверлеев (m-login с ids
  login-email/login-password/login-error/login-submit/login-close)
  продублирована в легаси `frontend/instructors.html` (+ wiring в
  js/instructors.js, атрибут data-open-login); instructors.html
  мигрируется в СЛЕДУЮЩЕЙ партии и в этом пакете не трогается.
- Контракты (НЕ меняются): POST /api/register {…, consent} — 200
  {ok, token} → setToken + location.href='/cabinet', 422
  {ok:false, error} в #reg-error (FR-78: кнопка #reg-submit disabled до
  #reg-consent); POST /api/auth/login → route §15.5: 'cabinet' →
  /instructor/dashboard, 'pending' → /instructors/pending, 'rejected' →
  sessionStorage «instructor_rejected_reason» ДО редиректа на
  /instructors/rejected (причина читает экран С11), default 'student-cabinet'
  → /cabinet; ошибка — res.data.error в #login-error; POST
  /api/instructors/apply — multipart (snake_case-поля + license_photo +
  consent), 200 {ok, poll_token?, exchange_token?} → localStorage
  application_poll_token/application_exchange_token → /instructors/pending,
  413/415/422 → файловые ошибки у поля ВУ («Файл: …») + notice под
  формой, согласие — 422 позиция 1a «Согласие: поле обязательно»
  (сервер, FR-77/MIN-2); sessionStorage open_login/open_login_from
  снимаются при закрытии модалки (BUG-056).
- NFR-26 свод С11: бюджеты проверяются для КАЖДОЙ мигрированной
  страницы (сейчас 3, с партией — 5).

## Потребители легаси-файлов (полный список, судьба каждого)

| Потребитель | Что читает | Судьба в пакете |
|---|---|---|
| backend/app.py `_PAGE_ROUTES` ("/", "/instructors/apply") | отдача файлов | 4.1 — исключение из карты, 4.2 — регистрация `vue:index.html` / `vue:instructor-apply.html` (одна сессия) |
| tests/web/test_login_modal.py (LOGIN_MODAL_TEXTS, тексты модалки) | frontend/index.html (блок между комментариями «Модалка: Вход/Регистрация») | 4.1 — перенос пути чтения на `frontend/vue/index.html`; тексты дословны — модалки переносятся в вход 1:1 (разметка входа = носитель текстов) |
| tests/web/test_login_modal.py (WIRING_FRAGMENTS, route-маппинг) | frontend_source("index.html") = html + /js/* рекурсивно | 4.1 — перенос носителя: вход + `src/pages/landing/App.vue` + `src/shared/api.js`; фрагменты контракта сохранены дословно в Vue-коде (см. «Границы правок тестов») |
| tests/web/test_login_modal.py (test_tc_auth_landing_page_served_with_wiring) | GET / + GET /js/landing.js + GET /js/api.js | 4.1 — GET / зелен без правок (dist в CI/образе; «СберАвтошкола» в входе); GET /js/landing.js переносится на носитель из репо (вход + App.vue + shared/api.js) — модуль /js/landing.js удален |
| tests/web/test_bug001.py (TC-AUTH-019) | frontend_source("index.html") | 4.1 — перенос носителя: вход + App.vue + shared/api.js; фрагменты postJSON('/api/register', setToken, location.href='/cabinet' — дословны |
| tests/api/test_policy.py (TC-PD-005, ссылка /policy из обоих согласий) | frontend_source("instructor-apply.html"), frontend_source("index.html") | 4.1 — перенос носителей: instructor-apply — вход + App.vue ('href="/policy" target="_blank"' и '.checkline' — в разметке входа; "fd.append('consent'" — в App.vue дословно); лендинг — вход + App.vue ('id="reg-consent"' — в разметке; фрагменты consent — см. подстановки) |
| tests/web/test_instructor_pages.py §4.2 (5 тестов: тексты/CSS мокапа, пароли, ссылки, формат, wiring сабмита) | page("instructor-apply.html"), frontend_source("instructor-apply.html"), split("<style>") | 4.1 — перенос носителей: page() → вход `frontend/vue/instructor-apply.html`; frontend_source → вход + App.vue; CSS-сверка — стили страницы в `src/pages/instructor-apply/styles.css` (перенос дословный) вместо inline `<style>` |
| tests/web/test_ui_playwright.py (62 сценария) | поведенческие: селекторы/маршруты/ожидания | БЕЗ ПРАВОК — id/классы/тексты сохраняются в Vue-версии (NFR-27): TC-UI-001 (.intro h1, #m-login по центру), TC-UI-002/043/044/045 (#m-register, #reg-*, #reg-consent, #reg-submit, ссылка /policy), TC-UI-053 (#login-close, Esc, фон), TC-UI-004 (#registration, #license-file, .checkline, редирект pending), TC-S9UI-003/TC-UI-005 (#login-*, route-редиректы), TC-UI-059/060 (вход ученика) |
| tests/web/test_ui_playwright.py (test_s4_pages_tag_balance, NIT-4) | список файлов (vue/review-form.html, instructor-choice.html, …) | 4.1 — перенос носителя design-guard: + `vue/index.html`, + `vue/instructor-apply.html` (прецедент vue/review-form.html С11) |
| tests/web/test_ui_playwright.py (TC-UI-059) | поведенческий + негативные маркеры BUG-059/060/061 | 1.1 — ДОПОЛНЯЕТСЯ негативным инвариантом «в шапке /instructor-choice нет .avatar» — прямо предписано планом фикса BUG-062 (задокументированное исключение из «0 правок», прецедент TC-UI-059 в BUG-059/061) |
| tests/web/test_static.py (GET / → 200 «СберАвтошкола», reg-password wiring) | маршрут / | БЕЗ ПРАВОК: вход из dist содержит бренд и разметку модалки 1:1; dist обязателен (CI/образ собирают; локально — `npm ci && npm run build` перед pytest, наследование С11) |
| tests/api/test_auth_route.py (test_new_static_routes_served: /instructors/apply) | 200 text/html | БЕЗ ПРАВОК: маршрут тот же, отдача dist (как /instructors/rejected С11) |
| tests/api/test_register.py, tests/api/test_integration_sprint1.py | только API / cabinet.html | БЕЗ ПРАВОК — не потребители удаляемых файлов |
| design/mocks/choice-instructor-a.html, choice-instructor-b.html | мокап «Выбора инструктора» | 1.1 — СИНХРОНИЗАЦИЯ с BUG-062: плитка `<span class="avatar">ИИ</span>` и правило `.avatar{…}` убраны (прецедент «мокапы choice-a/b синхронно» BUG-059/060/061) |

## Границы правок тестов (NFR-27 — разграничение)

- «0 правок сценариев» по-прежнему означает: селекторы, маршруты,
  ожидания и логика сценариев tests/web/test_ui_playwright.py не
  переписываются. Допустимый дифф по этому файлу — ТОЛЬКО: (а) два
  переноса носителя design-guard в test_s4_pages_tag_balance (+2 строки
  параметризации — прецедент vue/review-form.html С11); (б) негативный
  инвариант BUG-062 в TC-UI-059 (прямо предписан планом фикса BUG-062,
  решение Заказчика). Контроль: `git diff tests/web/test_ui_playwright.py`
  содержит только эти правки (задача 4.1, проверка в 6.1).
- tests/web/test_login_modal.py, tests/web/test_bug001.py,
  tests/api/test_policy.py, tests/web/test_instructor_pages.py —
  легаси-тесты-потребители страниц: правки разрешены (вне
  test_ui_playwright.py; прецедент 2.3 пилота и 3.1 С11). Право правки
  НЕ означает право ослаблять: проверяемые тексты, контракты и
  поведенческие фрагменты — дословно, меняется носитель источника.
- Подстановки «стековых фрагментов legacy» (задокументированные
  эквиваленты Vue — прецедент «style.display = ''» → v-show="reason"
  С11):
  - test_login_modal.py: `err.textContent=` → эквивалент Vue — сообщение
    ошибки сервера рендерится в `#login-error` / `#reg-error` из
    реактивного состояния (интерполяция {{ }}); `res.data.error`,
    `postJSON('/api/auth/login'`, `setToken(res.data.token)`,
    `sessionStorage.setItem(TOKEN_KEY`, `'session_token'`,
    `location.href='/cabinet'`, весь route-маппинг
    (`route==='cabinet'`→/instructor/dashboard, `route==='pending'`→
    /instructors/pending, `route==='rejected'`+sessionStorage
    «instructor_rejected_reason» ДО редиректа, `route||'student-cabinet'`)
    и порядок `res.status===200&&res.data.ok` ДО route-разбора —
    СОХРАНЯЮТСЯ дословно (плоский JS в App.vue) — правки не требуют;
  - test_bug001.py: все три фрагмента — дословно (правка только носителя);
  - test_policy.py: `regSubmit.disabled=!regConsent.checked` → эквивалент
    Vue — `:disabled` кнопки #reg-submit от состояния чекбокса
    (кнопка недоступна до установки — семантика FR-78 сохранена);
    `consent:regConsent.checked` → эквивалент — consent в payload
    сабмита из того же состояния; `fd.append('consent'` — дословно
    (FormData анкеты переносится построчно как в apply.js);
  - test_login_modal.py (носитель из репо): импорт-фрагмент носителя
    `from './api.js'` → механический эквивалент — импорт shared/api.js
    из Vue-модуля (относительный путь к src/shared); сам клиент
    postJSON/setToken переносится дословно (arch-review-001 MIN-3);
  - test_instructor_pages.py §4.2: `updateFormat` /
    `plate.disabled=!own` / `if(!own)plate.value=''` → эквивалент Vue —
    реактивная связь radio формата с состоянием поля госномера
    (disabled/очистка/приглушение — семантика мокапа сохранена);
    `notice.classList.add('show')` → эквивалент — класс show notice из
    реактивного состояния (`:class`); `fetch('/api/instructors/apply'`,
    `method:'POST'`, `new FormData()`, все `fd.append('…'` (15 строк
    legacy: 14 полей + consent; тест-кортеж покрывает 13 — MIN-1),
    `location.href='/instructors/pending'`,
    `5*1024*1024`, `validateLicenseFile`, отсутствие sessionStorage —
    дословно; тексты/разметка входа — дословно, CSS-строки мокапа —
    дословно в styles.css.

## Точки входа Vite (решение)

- vite.config.mjs, `rollupOptions.input` дополняется двумя входами
  (правила пилота — без изменений):
  - `index` → `frontend/vue/index.html` (dist/index.html; имя входа
    «index» — сохраняет имя артефакта маршрута /);
  - `instructor-apply` → `frontend/vue/instructor-apply.html`
    (dist/instructor-apply.html; имя по сегменту маршрута — паттерн
    С11).
- Вход = статическая разметка страницы (эквивалент legacy 1:1) +
  модуль-скрипт `/src/pages/<page>/main.js`; до гидрации видна та же
  разметка (паттерн пилота/С11; «Разметку держать синхронной с
  App.vue»).
- Страницы: `frontend/vue/src/pages/landing/` (main.js, App.vue,
  styles.css) и `frontend/vue/src/pages/instructor-apply/` (main.js,
  App.vue, styles.css). Стили — дословный перенос из legacy html
  (без редизайна); у анкеты — перенос сверяется построчно с мокапом
  (TC §4.2), у лендинга — с текущим index.html.
- scripts/check-budgets.mjs: карта page-чанков расширяется до пяти
  (instructors-pending, instructors-rejected, review-form, index,
  instructor-apply); замыкание первого захода и «чужие page-чанки» —
  по КАЖДОЙ странице; бюджеты не меняются (NFR-26).
- Новых npm-зависимостей НЕТ; pinia/vue-router НЕ вводятся (ОВ-3).

## Судьба общего контура модалок входа/регистрации (решение)

- Модалки m-login/m-register — вынос в shared-компоненты каркаса:
  `frontend/vue/src/shared/LoginModal.vue` и
  `frontend/vue/src/shared/RegisterModal.vue` (+ при необходимости
  `src/shared/authModal.css` с общими стилями overlay/modal/reg-check —
  свой код в чанке shared, НЕ библиотека; новых npm-пакетов нет).
  Разметка модалок — дословный перенос из index.html (тексты мокапа —
  носитель LOGIN_MODAL_TEXTS: комментарии «Модалка: Вход/Регистрация»
  и разметка между ними сохраняются в статической разметке входа
  index.html 1:1, компоненты монтируются поверх этих узлов — паттерн
  «статическая разметка + гидрация» пилота).
- Wiring модалок (открытие data-open, закрытие BUG-055/056, consent
  FR-78, сабмиты, route-маппинг) — в App.vue лендинга (страница —
  единственный потребитель в этой партии). Вынос wiring в shared-
  композабл НЕ делается: второй потребитель (/instructors) появится
  только в следующей партии — вынос выполняется тогда, на живом
  втором потребителе (консолидация, как shared/utils.js С11 переносился
  при живом потребителе).
- Легаси-дубль в instructors.html остается КАК ЕСТЬ (та же разметка id
  + wiring js/instructors.js, data-open-login) — временное состояние
  постраничной миграции (ADR-008: дубли исчезают по мере миграции);
  умирает вместе с монолитом при миграции /instructors. Конфликта id
  нет: разные страницы = разные бандлы (multi-entry), модалки никогда
  не оказываются в одном DOM.
- Сверка контракта: легаси-дубль и Vue-версия пишут одни и те же
  ключи (session_token, open_login, open_login_from,
  instructor_rejected_reason) — поведение polling/rejected не зависит
  от того, через какую из двух модалок выполнен вход.

## Роуты и статика (backend/app.py)

- 4.1: оба маршрута исключаются из легаси-отдачи карты (`"/"`,
  `"/instructors/apply"`); 4.2 — регистрация в `_PAGE_ROUTES` с
  маркером каркаса: `"vue:index.html"` / `"vue:instructor-apply.html"`;
  цикл отдачи при префиксе `vue:` — без изменений (читает
  VUE_DIST_DIR, 404 при отсутствии dist). Карта остается единым
  декларативным реестром маршрутов.
- Статика `/vue/assets/{path}` — БЕЗ ИЗМЕНЕНИЙ (покрывает новые
  чанки); шрифты/картинки страницам не нужны (системные шрифты,
  эмодзи-глифы — как в legacy).
- `_PAGE_REDIRECTS`, пилотный хендлер /instructors/pending, `/api/*` —
  БЕЗ ИЗМЕНЕНИЙ (NFR-27).
- Между 4.1 и 4.2 существует переходное состояние (маршрут без отдачи);
  задачи выполняются подряд в одной сессии, промежуточный пуш/PR не
  делается; e2e-гейт партии — 6.1 после 4.2 и 5.1.

## Dockerfile / compose / CI — изменений сборки НЕ требуется

- node builder-этап собирает dist из ВСЕХ входов vite.config.mjs одной
  командой — новые входы попадают в образ автоматически.
- docker-compose.yml, nginx, .dockerignore — БЕЗ ИЗМЕНЕНИЙ; CI
  flow.yml уже делает `npm ci && npm run build` перед pytest.
- bare-metal (FR-57): порядок `npm ci && npm run build` перед деплоем —
  без изменений.
- Локальный регресс: перед `pytest tests/` обязательна сборка dist —
  маршруты `/` и `/instructors/apply` отдают 404 без нее (то же
  поведение, что у маршрутов С11; CI собирает всегда).

## Страница / на Vue (3.2 — последняя задача партии)

- Перенос 1:1 (без редизайна): header (бренд «СберАвтошкола» с
  градиентным em, nav-заглушки «О программе/Тарифы/Вопросы», кнопки
  .auth data-open=register/login), hero (.intro — eyebrow «СОВРЕМЕННАЯ
  АВТОШКОЛА ОТ СБЕРА», h1 «Права — без лишнего пути.», подзаголовок),
  шаги 01–04 (.steps s1–s4), чат-бар «Гига ГАИшник» (.assistant,
  .ai-head, .avatar-градиент, .prompt c #ai-open, .quick 5 кнопок —
  ВИЗУАЛЬНАЯ ЗАГЛУШКА), плитки футера (3 .feature + .tagline с
  #to-teachers), фоновые .road-градиенты и медиазапросы (включая
  порог nav 1200 — BUG-050 MINOR-1). Тексты — дословно.
- Поведение js/landing.js — в App.vue (1:1): открытие/закрытие модалок
  (data-open/data-close/Esc; фон НЕ закрывает #m-login — BUG-056;
  снятие open_login/open_login_from при закрытии), consent-гейт
  регистрации (FR-78), сабмиты и route-маппинг входа (контракты — см.
  Baseline; sessionStorage «instructor_rejected_reason» пишет Vue-wiring
  модалки входа — контракт polling/rejected не сломан), заглушки
  ai-open/quick/to-teachers (alert — те же тексты).
- Якоря e2e дословно: .intro h1, .auth [data-open="login"/"register"],
  #m-login/#m-register (.overlay.open), #login-email/#login-password/
  #login-submit/#login-error, #reg-surname/#reg-name/#reg-patronymic/
  #reg-email/#reg-phone/#reg-password/#reg-password-confirm/
  #reg-consent/#reg-submit/#reg-error, #login-close (data-close),
  .reg-check a[href='/policy'], #ai-open, .quick button, #to-teachers,
  .brand em (rgb(53,216,121)).
- Зависимость страницы: `src/shared/LoginModal.vue` +
  `src/shared/RegisterModal.vue` (см. «Судьба общего контура модалок»);
  api-вызовы — через `src/shared/api.js` (postJSON/setToken — контракты
  не меняются).

## Страница /instructors/apply на Vue (3.1)

- Перенос 1:1 (без редизайна): header (бренд → /instructors, «←
  Вернуться на лендинг»), intro-колонка (eyebrow «Подключение
  инструкторов», h1 «Начнём с простого.», шаги 01/02/03, side-note),
  form-card (прогресс, секции 01/02/02.1/03, поля с id/name 1:1,
  choice own/sber, upload-блок BUG-048 с #license-thumb,
  .checkline-согласие со ссылкой /policy, .submit-row, #notice), футер.
  Тексты и CSS мокапа registration-instructor.html — дословно (носитель
  TC §4.2).
- Поведение js/apply.js — в App.vue (1:1): переключение формата
  own/sber (госномер disabled+очистка+приглушение — эквивалент Vue
  реактивной связью), выбор файла ВУ → миниатюра objectURL / ошибка
  (клиентская валидация JPEG/PNG ≤5 МБ — тексты совпадают с серверными),
  consent-гейт кнопки (FR-77), сабмит — FormData построчно как legacy
  (15 fd.append-строк: 14 полей + consent 'true'/'false', + условный
  license_photo — arch-review-001 MIN-1), fetch
  '/api/instructors/apply' method:'POST'; 200 → localStorage-токены
  опроса (application_poll_token/application_exchange_token) → редирект
  /instructors/pending; 413/415/422-файловые → у поля ВУ + notice;
  прочие 422 (включая согласие — позиция 1a) → notice. Ошибка сети →
  notice «Ошибка сети». Сессия по заявке не выдается — sessionStorage
  на странице не используется.
- Якоря e2e дословно: #surname/#name/#patronymic/#phone/#email/
  #address/#plate/#license-number/#license-date/#license-category/
  #experience/#password/#password-confirm, input[name="format"],
  #registration button.submit, .checkline input, .upload/.upload-icon,
  #license-file/#license-thumb/#license-error/#file-name/#pick-file,
  #notice; редирект **/instructors/pending → h1 «Заявка на
  рассмотрении» (TC-UI-004).

## BUG-062 (1.1 — отдельная задача пакета)

- Страница /instructor-choice ОСТАЕТСЯ легаси (миграция — следующая
  партия с доработками кабинета): правка минимальна.
- frontend/instructor-choice.html: из шапки убирается
  `<span class="avatar" id="avatar">—</span>` (блок .user — ФИО #uname
  и «Выйти» остаются) и правило `.avatar{width:34px;…}`; медиазапросы
  и прочие правила не трогаются.
- frontend/js/instructor-choice.js: убирается заполнение
  `document.getElementById('avatar').textContent=…` (строка в
  обработчике /api/auth/me); чтение ФИО #uname — без изменений.
- e2e TC-UI-059 (test_tc_ui_059_student_cabinet_single_logo_no_crumbs):
  в секцию /instructor-choice добавляется негативный инвариант
  «в шапке нет .avatar» (assert count==0 для header .avatar) —
  дополнение прямо предписано планом фикса BUG-062; остальное тело
  сценария не трогается.
- Мокапы choice-instructor-a/b.html — синхронно: та же плитка
  (`<span class="avatar">ИИ</span>` в .user) и то же правило `.avatar`
  убираются (прецедент «мокапы choice-a/b синхронно» BUG-059/060/061).
- Сверка «инициалы нигде больше в контуре ученика не выводятся»
  (план BUG-062): шапка /cabinet — уже без аватара (uname + «Выйти»);
  `.avatar` в cabinet.html — декоративный круг ассистента «Гига
  ГАИшник» (ai-head, не инициалы, не трогается); инициалы ученика
  остаются ТОЛЬКО на /review (шапка формы отзыва, партия С11, #avatar)
  — вне решения BUG-062 (решение Заказчика касается шапки «Выбора
  инструктора»); фиксируется как известное отклонение, не в объеме.

## Обработка ошибок — реакции 1:1 legacy (сводно)

| Ответ | Лендинг (модалки) | Анкета |
|---|---|---|
| 200 ok | register → setToken → /cabinet; login → route-маппинг §15.5 | 200 → localStorage-токены → /instructors/pending |
| 422 | res.data.error → #reg-error / #login-error | согласие — «Согласие: поле обязательно» в notice; файловые («Файл: …») — у поля ВУ + notice |
| 401/403 | res.data.error → #login-error (единое сообщение) | n/a (сессии нет) |
| 413/415 | n/a | файловые тексты у поля ВУ + notice |
| network | «Ошибка сети» в #reg-error / #login-error | notice «Ошибка сети» |
| закрытие модалки | крестик/«Отмена»/Esc; фон не закрывает #m-login (BUG-055/056); open_login-флаги сняты | n/a |

## Решения по НФТ

- **NFR-26:** бюджеты проверяются на артефактах сборки
  (npm run check:budgets — расширение 2.1: ПЯТЬ page-чанков, замыкание
  первого захода и «чужие page-чанки» по каждой): каждый vendor-чанк
  ≤150 КБ gzip; JS первого захода КАЖДОЙ из пяти страниц ≤200 КБ gzip.
  Лендинг — крупнейший перенос стилей (≈18 КБ исходного html) —
  стили уходят в styles.css-чанк страницы, вендорного кода в чанке
  нет; запас бюджета сохраняется (vue-чанк ~20 КБ gzip). Замеры — в
  отчете 5.1.
- **NFR-27:** полный набор tests/web/test_ui_playwright.py зелен без
  правок СЦЕНАРИЕВ (допустимый дифф — только два переноса носителя
  design-guard и негативный инвариант BUG-062, см. «Границы правок
  тестов»); маршруты, редиректы и /api/* — без ломающих изменений.
- Наследуются без изменений: ADR-001 (статика тем же сервисом), FR-57
  (bare-metal), ADR-006 (multi-stage, pinned), ADR-009 (политика ПД —
  согласия FR-77/FR-78 воспроизводятся 1:1), NFR-2/NFR-5 (не
  затрагиваются).

## Сознательные ограничения (задокументированы)

- **Временный дубль контура модалок входа**: легаси instructors.html
  продолжает нести собственную копию m-login (разметка + wiring в
  js/instructors.js) до своей миграции (следующая партия). Альтернатива
  «править легаси под shared» отклонена: js/instructors.html-монолит не
  может импортировать Vue-компоненты (нет сборки), правка легаси
  добавила бы риск без миграционной выгоды. Дубль умирает вместе с
  монолитом (ADR-008 п.4); ключи sessionStorage и контракты у двух
  версий идентичны.
- Вынос wiring модалок в shared-композабл отложен до миграции
  /instructors (второго живого потребителя) — консолидация на живом
  потребителе, прецедент shared/utils.js С11.
- Чат-бар «Гига ГАИшник» — перенос визуальной заглушки (alert-тексты
  дословно); подключение реального ассистента — вне объема миграции.
- dist и node_modules — не в git; входы и компоненты — в git.
- Пилотный хендлер /instructors/pending остается выделенным вне карты —
  унификация не делается (наследование С11).
- Переходное состояние между 4.1 и 4.2 (маршруты без отдачи) существует
  только внутри одной сессии работ; гейт — 6.1 после 4.2.
- Два переноса носителя design-guard и негативный инвариант BUG-062 в
  test_ui_playwright.py — задокументированные исключения из «0 правок»
  (см. «Границы правок тестов»); альтернативы отклонены: сохранение
  легаси-файлов как «мертвых» (параллельное существование версий —
  против ADR-008 п.4), правка frontend_source/conftest (шире
  необходимого диффа).
- Контроль бюджетов остается приемочным ручным шагом (не CI-гейт) —
  наследование ограничения пилота.
- Тексты/заголовки/стили — только перенос текущих (директива «без
  большого переписывания»; редизайн — вне миграции; текстовки лендинга
  — дословно по референсу, включая бренд «Сбер» — замена по команде
  Заказчика, которой не было).
- sdd.md в пакетах миграции не ведется (прецедент пилота/С11).
- Порядок задач: анкета (3.1) раньше лендинга (3.2); лендинг —
  ПОСЛЕДНЯЯ задача партии, т.к. через его модалки идет вход в кабинеты
  (около половины e2e-сценариев: 10 заходов на / и 11 открытий модалок
  в test_ui_playwright.py) — максимальный blast radius, интегрируется
  последним, гейт — 6.1.

## Соответствие ADR-001/006/008/009

Отступлений нет: multi-entry MPA (страница = отдельная точка входа,
SPA/vue-router/pinia запрещены — ОВ-3); замена монолита целиком с
удалением легаси (ADR-008 п.4); vendor-сплит и бюджеты NFR-26 — правила
пилота, свод С11 (каждая страница); статика тем же сервисом (ADR-001)
через существующие `/vue/assets`; контур доставки без изменений
(ADR-006); критерий приема — зеленый полный e2e (ADR-008 п.6,
FR-85/NFR-27); согласия ПД — FR-77/FR-78 1:1 (ADR-009).
