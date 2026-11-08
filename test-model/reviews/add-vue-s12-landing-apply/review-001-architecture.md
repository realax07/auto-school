# Arch-review 001: add-vue-s12-landing-apply (Спринт 12)

- Дата: 2026-11-08
- Ревьюер: архитектор (Hermes)
- Коммит СА-фазы: c3dca78 «[s12] CA: пакет add-vue-s12-landing-apply»
- База проверки: фактический код (backend/app.py, frontend/vue/ + vite.config.mjs
  + scripts/check-budgets.mjs, frontend/index.html, frontend/js/landing.js,
  frontend/instructor-apply.html, frontend/js/apply.js, frontend/instructors.html,
  frontend/js/instructors.js, frontend/instructor-choice.html,
  frontend/js/instructor-choice.js, design/mocks/choice-instructor-a/b.html,
  tests/ — grep-сверки и подсчеты по факту) + ADR-008 +
  openspec/changes/archive/2026-11-08-add-vue-s11-status-forms (прецедент) +
  архитектурная карта (паттерн 18) + решение Заказчика 2026-11-08
  (decisions/2026-11-08-sprint12-go.md) + реестр test-model/bugs/BUG-062.md

## Вердикт

**approve-with-notes** (MAJ — нет; MIN-1…MIN-3 — уточнения оболочки,
внесены коммитом arch-review; блокировки dev-старта нет).

Карта: **без изменений** (см. раздел 8).

## 1. ADR-008 / механизм маршрутов — без отступлений

- Multi-entry MPA: два новых входа `frontend/vue/index.html` (имя `index` —
  dist/index.html, имя артефакта маршрута / сохранено) и
  `frontend/vue/instructor-apply.html` (паттерн С11 «имя по сегменту»);
  SPA/vue-router/pinia не вводятся (ОВ-3) — формулировки proposal/design/tasks
  едины. Новый npm-зависимостей нет.
- Механизм `vue:<файл>` сверен с фактическим кодом backend/app.py:39–73
  (карта) и :164–181 (цикл отдачи: префикс `vue:` → VUE_DIST_DIR, 404 без
  dist, text/html; charset=utf-8). Добавление `vue:index.html` /
  `vue:instructor-apply.html` — две строки карты, механика не меняется.
  Пилотный хендлер /instructors/pending (:143–146) — вне карты и не
  трогается; С11-маршруты (`/instructors/rejected`, `/review`) в карте не
  задеваются — пилот + 2 маршрута С11 не ломаются. Проверено: замена
  значений "/" и "/instructors/apply" не влияет на порядок регистрации
  (карта регистрируется после выделенного хендлера, коллизий нет).
- Статика `/vue/assets/*` (:149–163, карта суффиксов .js/.css) покрывает
  новые чанки без правок; шрифты/картинки страницам не нужны (сверено с
  legacy: системные шрифты, эмодзи-глифы). Контур доставки (Dockerfile node
  builder-этап, compose, nginx, CI `npm ci && npm run build` перед pytest) —
  правки не требуются: dist собирается из ВСЕХ входов одной командой.
- Удаление legacy ЦЕЛИКОМ (ADR-008 п.4): 4 файла (index.html, landing.js,
  instructor-apply.html, apply.js) — «параллельное существование версий»
  отклонено явно (design, «Сознательные ограничения»). Верно.
- NFR-26: master-spec сформулирован генерально («КАЖДОЙ мигрированной
  страницы») — свод С11 наследуется без дельты на NFR-26. Согласен.

## 2. Дубль модалок instructors.html — ограничения достаточны

Фактическая сверка двух копий контура (index.html+landing.js vs
instructors.html+instructors.js):

- sessionStorage-ключи ИДЕНТИЧНЫ: session_token — через общий клиент
  (frontend/js/api.js и frontend/vue/src/shared/api.js — дословно одинаковый
  postJSON/setToken, сверено построчно); instructor_rejected_reason —
  одинаковый код `sessionStorage.setItem(...)` ДО редиректа
  (landing.js:70 ≡ instructors.js:46). open_login/open_login_from
  instructors.js НЕ пишет (BUG-055, осознанно) — landing.js только снимает
  их; других писателей в репо нет (grep: 3 вхождения, все — landing.js:
  14–15 и комментарии). Дивергенции ключей нет и не появится.
- consent-чекбокс FR-78 расхождению не подвержен в принципе: модалка
  m-register существует ТОЛЬКО на лендинге (в instructors.html — только
  m-login, чекбокса нет); после партии единственный носитель согласия
  регистрации — Vue-модалка. Единая реализация, а не две.
- ids (login-email/login-password/login-error/login-submit/login-close)
  идентичны. Разметка копий УЖЕ расходится косметически сегодня
  (`<p class="sub">` vs `<p>`, `<label>` vs `<span>`, btn-primary vs
  `btn primary`) — дубль пакета не создает НОВОГО риска: легаси-копия
  остается «как есть», поведение идентично.
- e2e через легаси-модалки /instructors — фактический подсчет по
  test_ui_playwright.py: 2 сценария (test_instructors_landing_brand_and_cta,
  test_bug056_instructor_login_modal_close_semantics; 4 вхождения
  data-open-login) — instructors.html в пакете НЕ трогается, сценарии
  остаются зелеными без правок. Через лендинг /: факт «10 заходов на / и
  11 открытий модалок» подтвержден точным подсчетом (10 page.goto("/"),
  11 вхождений data-open="login"/"register") — цифры design.md точны.
- Вынос wiring в shared-композабл отложен до живого второго потребителя
  (миграция /instructors) — прецедент shared/utils.js С11; согласен:
  консолидация без второго потребителя дублировала бы код впустую.
- Вывод: «Сознательные ограничения» покрывают риск полностью; временное
  состояние умирает вместе с монолитом (ADR-008 п.4).

## 3. Потребители легаси-файлов — список переносов ПОЛОН

Греп по tests/ и frontend/ (index.html, instructor-apply.html, landing.js,
apply.js) подтверждает: функциональных потребителей вне списка design.md
«Потребители легаси-файлов» НЕТ:

| Потребитель (факт) | Судьба | Проверка |
|---|---|---|
| backend/app.py:40,76 (_PAGE_ROUTES "/", "/instructors/apply") | 4.1 исключение + 4.2 vue:-регистрация, одна сессия | ок |
| tests/web/test_login_modal.py (LOGIN_MODAL_TEXTS, маркеры «Модалка: Вход/Регистрация», WIRING_FRAGMENTS, GET /js/landing.js, route-маппинг + порядок ok→route) | 4.1 перенос носителя на вход vue/index.html + App.vue + shared/api.js | ок; маркеры и тексты дословно во входе; `method: 'POST'`, `sessionStorage.setItem(TOKEN_KEY`, `'session_token'` живут в shared/api.js дословно (сверено с vue/src/shared/api.js); route-маппинг — плоский JS в App.vue (см. MIN-3) |
| tests/web/test_bug001.py:70 (TC-AUTH-019: postJSON('/api/register', setToken, /cabinet) | 4.1 перенос носителя | ок — все три фрагмента в landing.js:43,46,48 дословно переносятся |
| tests/api/test_policy.py:299–311 (TC-PD-005) | 4.1 перенос носителей, две подстановки | ок — подстановки `regSubmit.disabled=…` и `consent:regConsent.checked` задокументированы; `href="/policy" target="_blank"`, `.checkline`, `id="reg-consent"`, `fd.append('consent'` — дословно |
| tests/web/test_instructor_pages.py §4.2 (5 тестов: тексты+CSS мокапа, пароли, ссылки /instructors, updateFormat, wiring сабмита) | 4.1 перенос: page() → вход; CSS-сверка → styles.css; подстановки | ок — подстановки перечислены полностью; href=/instructors (бренд + «← Вернуться на лендинг») — в списке якорей design |
| tests/web/test_ui_playwright.py:4423–4426 (tag-balance: instructor-dashboard, cabinet, vue/review-form, instructor-choice) | 4.1 +2 строки параметризации (vue/index.html, vue/instructor-apply.html) | ок — прецедент vue/review-form.html; суммарный дифф файла = 2 строки + инвариант 1.1, контроль git diff в 6.1 |
| tests/web/test_ui_playwright.py:4113–4114 (docstring «frontend/js/apply.js:84-85») | без правок | ок — docstring, grep-исключение «исторические носители: docstring…» в 4.1 учтено (прецедент MIN-1 ревью С11) |
| tests/web/test_static.py (GET / → «СберАвтошкола», reg-password), tests/api/test_auth_route.py (200 text/html) | БЕЗ ПРАВОК | ок — dist/index.html содержит бренд и разметку модалок 1:1; требование сборки dist документировано |
| tests (polling-серия): _seed_application_tokens кладет localStorage через init-скрипт | БЕЗ ПРАВОК | ок — от apply.js не зависит (docstring только) |
| session-переходы: instructor-choice.js:161 и cabinet.js:20,51 → location.href='/' | вне диффа | ок — маршрут / остается, выход/redirect'ы падают на Vue-лендинг; выбор «на главную» не задействует удаленные файлы |
| instructors.js:3 (location.href='/instructors/apply') и instructors.html (CTA href) | вне диффа | ок — маршрут тот же |

Итого: план тестовых переносов (4 файла + 2 правки в test_ui_playwright.py)
полон; сценарии e2e не переписываются — NFR-27 соблюдается.

## 4. Контракты — замены корректны, ничего не теряется

- Login route/reason: landing.js:63–76 — `res.status===200&&res.data.ok`,
  `route||'student-cabinet'`, 4 ветви, `sessionStorage.setItem(
  'instructor_rejected_reason', res.data.reason||'')` ДО
  `location.href='/instructors/rejected'` — дизайн требует дословный
  перенос в App.vue (плоский JS) + сохранение ПОРЯДКА ok→route (тест
  test_login_route_mapping_wiring проверяет `idx_ok < idx_route`);
  TC-S9UI-003 зелен без правок. Контракт polling/rejected жив.
- Register consent FR-78: серверная проверка register.py:73 («Согласие:
  поле обязательно») не меняется; клиентский гейт `:disabled` от состояния
  чекбокса — задокументированный эквивалент (семантика «недоступна до
  установки» сохранена, e2e TC-UI-002/043–045 проверяют поведение, не код).
- Apply multipart: factual base — apply.js:62–80, 15 fd.append-строк
  (14 snake_case-полей + consent 'true'/'false') + условный license_photo
  с именем файла; fetch method:'POST' телом FormData; 200 →
  application_poll_token/application_exchange_token в localStorage ДО
  редиректа; 413/415/422-файловые → #license-error + notice, согласие
  (instructors.py:163, позиция 1a) и прочие → notice; сеть → notice
  «Ошибка сети»; sessionStorage на странице нет. Дизайн воспроизводит все
  ветки 1:1 (таблица «Обработка ошибок» свершена с apply.js:98–114).
  Счетчик «13 полей» в исходных текстах пакета был неточен — MIN-1
  (исправлен).
- «Стековые» подстановки (err.textContent → интерполяция {{ }};
  regSubmit.disabled → :disabled; updateFormat/plate.disabled/
  notice.classList.add('show') → реактивные связки/:class) — каждая
  сохраняет наблюдаемое поведение, проверяемое тестами (тексты сервера,
  disabled-семантика, класс show). Теряемых фрагментов нет;
  `validateLicenseFile`, `5*1024*1024`, `new FormData()`, все fd.append,
  URL-строки, localStorage-ключи — дословно.

## 5. BUG-062 (1.1) — полон, соответствует плану фикса

- Сверено с test-model/bugs/BUG-062.md («План фикса»): span#avatar +
  правило `.avatar` (instructor-choice.html:31,128) + заполнение
  (instructor-choice.js:14) — все три точки в задаче 1.1; мокапы
  choice-instructor-a/b (плитка «ИИ» + то же правило :21/:20) —
  синхронно, прецедент BUG-059/060/061 подтвержден по реестрам.
- Сверка «инициалы нигде больше в контуре ученика»: grep id="avatar" по
  frontend/design — /instructor-choice (цель фикса), /review (Vue С11,
  инициалы ученика — вне решения, зафиксировано), cabinet.html
  (декоративный круг ассистента ai-head — не трогается, верно),
  instructor-dashboard/instructor-cabinet-stub (инструкторский контур,
  вне «контура ученика»). Полнота сверки в design подтверждена фактами.
- e2e-инвариант: TC-UI-059 (test_tc_ui_059_...:4621–4663) реально
  проходит через / (модалка лендинга) → /cabinet → /instructor-choice;
  добавка «в шапке нет .avatar» в секцию /instructor-choice — ровно то,
  что предписывает план фикса; BUG-061-инвариант (right_gap < 40) не
  страдает (удаление плитки не меняет space-between-прижатие .user) —
  «вёрстка BUG-061 не поехала» в готовности 1.1 учтено.
- 1.1 [P]-независима от миграции (файловых пересечений с 2.1/3.x нет);
  общая зона test_ui_playwright.py с 4.1 («не параллелить в разных
  worktrees») задокументирована в «Рекомендациях к нарезке» — противоречия
  с [P] нет.

## 6. Бюджеты NFR-26 — расширение механическое, запас реальный

- check-budgets.mjs: page-роль — список PAGES (:33), замыкание строится от
  dist/<page>.html для КАЖДОЙ (:90–108), first-load и «чужие page-чанки» —
  по каждой (:141–158). Расширение PAGES до 5 (+# index, instructor-apply)
  — правка одной строки+карты имен; dist/index.html и
  dist/instructor-apply.html порождаются входами автоматически. Регулярка
  входа требует .js (CSS не мешает), хэш-суффикс 8 символов — проверено на
  действующих 3 страницах, обобщается без изменений.
- Реалистичность 200 КБ gzip на первый заход лендинга: замеры пилота —
  vue-чанк ~23 КБ gzip, полный первый заход ~26 КБ (код-ревью 4.1 пилота);
  стили лендинга (~18 КБ raw html) уходят в CSS-чанк (в JS-бюджет не
  входят — скрипт считает только .js; формулировка NFR-26 «JS первого
  захода» соблюдена точно); page-чанк = компиляция шаблона App.vue,
  shared — дословный api.js. Оценка первого захода лендинга ~35–45 КБ gzip
  — запас >4x. «Вендорного кода в чанках страниц нет» — конструктивно
  (manualChunks). Замер в 5.1 по финальным чанкам, контроль остается
  ручным приемочным шагом — наследование пилота, задокументировано.

## 7. Порядок задач — обоснован; гейт 6.1

- 1.1 (BUG-062) — независимая, файловых пересечений нет: верно (легаси
  instructor-choice + мокапы + 1 сценарий e2e). 2.1 → 3.1 → 3.2: лендинг
  последним — обоснование подтверждено фактом (10 заходов на / и 11
  открытий модалок — вход в кабинеты; максимальный blast radius),
  интеграция последней + гейт 6.1. Зависимость 3.2 от 3.1 —
  интеграционная (порядок слияния), не кодовая; формулировка волны
  «параллятся по замыслу, НО 3.1 → 3.2» читается двояко, но итоговый
  порядок задан однозначно (наблюдение, не замечание).
- Промежуточные состояния пуше-безопасны: до 4.2 легаси отдается как
  прежде (входы 2.1/страницы 3.x на маршруты не влияют); 4.1+4.2 — одна
  сессия без промежуточного пуша (маршрут без отдачи не существует в
  репозитории) — «НЕЛЬЗЯ делить» задокументировано. После 4.2 dist
  обязателен — CI собирает всегда, локальный порядок (build перед pytest)
  унаследован С11 и задокументирован.
- Риски 6.1: единственный реальный — невыполнимая готовность 2.1 без
  App.vue-заглушек (вход ссылается на /src/pages/<page>/main.js — без
  модуля build падает, CI красный уже на 2.1) — MIN-2 (исправлен:
  заглушки отнесены к 2.1). Полный набор (62 сценария) + регресс-список
  + openspec strict — проверено: `openspec validate add-vue-s12-landing-apply
  --strict` и `--all --strict` зеленые на коммите arch-review.

## 8. Спеки и архитектурная карта

- Дельта Frontend: 2 ADDED Requirements, MUST-формулировки, 10 сценариев
  GIVEN/WHEN/THEN (лендинг: отдача каркасом, route/reason с rejected-ДО-редиректа,
  регистрация FR-78, семантика модалок/заглушки, визуальная эквивалентность;
  анкета: отдача, контракт 200+токены, согласие 422 1a, ошибки файла у поля,
  визуальная эквивалентность) — сценарии полны против FR-1/2/10…13/17/77/78
  и якорей e2e. Дельта student-instructor-choice: 1 ADDED Requirement,
  3 сценария (нет плитки / ФИО+«Выйти» не пострадали / мокапы синхронны) —
  полно. Конфликтов с master-spec нет (в Frontend нет требований про
  лендинг/анкету; student-instructor-choice про шапку — новые).
  `openspec validate --strict` — зеленый.
- Карта: **без изменений**. Паттерн 18 (architecture/map.md) уже описывает
  миграцию как повторяемый паттерн, включая план «С9 пилот — ВЫПОЛНЕН →
  С11 статусные экраны/простые формы → далее лендинги/анкета/кабинеты»:
  лендинг / и анкета /instructors/apply — плановые ступени С11→С12, новых
  архитектурных решений пакет не вводит (`vue:`-маркер и shared-чанк —
  механическое расширение описанного). Рутинный рефреш статуса колонки
  паттерна 18 («С12: лендинг + анкета — ВЫПОЛНЕН») — ПОСЛЕ приемки
  партии, не на этапе СА (прецедент ревью С11).

## Итог

- MAJ: нет.
- MIN-1: счетчик multipart-полей «13 полей» ≠ факту (apply.js: 15
  fd.append-строк — 14 полей + consent; + условный license_photo;
  тест-кортеж §4.2 покрывает 13 фрагментов) — исправлен в tasks 3.1 и
  design («Границы правок тестов», «Страница /instructors/apply на Vue»)
  этим коммитом.
- MIN-2: готовность 2.1 (build + check:budgets зелен) недостижима без
  модулей страниц — вход ссылается на /src/pages/<page>/main.js; уточнено
  в tasks 2.1: минимальные App.vue-заглушки создает 2.1, полную
  разметку-копию и wiring — 3.1/3.2 (этим коммитом).
- MIN-3: подстановка импорт-фрагмента носителя `from './api.js'`
  (test_login_modal.py) не была в списке эквивалентов — импорт shared/api.js
  из Vue-модуля меняет относительный путь; добавлена в design «Границы
  правок тестов» (этим коммитом). Сам клиент postJSON/setToken — дословно.
- Наблюдение (не замечание): в переходный период разметка модалок
  существует в трех носителях (легаси instructors.html; статическая копия
  входа vue/index.html — носитель LOGIN_MODAL_TEXTS; LoginModal.vue) —
  это унаследованный паттерн пилота/С11 «статическая разметка + гидрация»
  («Разметку держать синхронной с App.vue»), консолидация — при миграции
  /instructors; design фиксирует судьбу каждого носителя.
- Наблюдение: зависимость 3.2→3.1 — интеграционная, не кодовая
  (формулировка волны «параллятся по замыслу, НО» двояка; порядок верен).
- Вердикт: **approve-with-notes** — dev-старт разрешен; волны
  1.1 [P] / 2.1 → 3.1 → 3.2 → 4.1+4.2 (одна сессия) → 5.1 → 6.1 согласованы.
