# Change: add-vue-s12-landing-apply

## Why (Зачем)

Спринт 12, пункт 1 бэклога «Фронтенд-фреймворк — продолжение миграции»
(BACKLOG.md #1): решение Заказчика 2026-11-08 — состав Спринта 12
(decisions/2026-11-08-sprint12-go.md, «Архивируй пакет и Давай дальше»).
Каркас Vue 3 + Vite и пилот /instructors/pending — в проде (Спринт 9,
PR#107, ADR-008); статусный экран отказа и форма отзыва — в проде
(Спринт 11, add-vue-s11-status-forms). Следующая партия плана ADR-008 —
лендинг ученика и анкета инструктора: обе страницы одноцелевые, но
лендинг несет ОБЩИЙ контур модалок входа/регистрации (те же оверлеи —
на легаси instructors.html) и через него проходит вход в кабинеты
(модалки открывают половину e2e-сценариев) — самый рискованный шаг
миграции, поэтому выполняется последней задачей партии. Вместе с партией
закрывается BUG-062 (реестр test-model/bugs/BUG-062.md, решение
Заказчика 2026-11-07: убрать плитку-аватар из шапки «Выбора
инструктора» — «вместе со следующей партией»).

Источники требований: ADR-008
(architecture/adr/008-vue3-vite-migration.md, план С9–С11 «лендинги,
анкета с multipart, кабинеты»); решение Заказчика 2026-11-08
(decisions/2026-11-08-sprint12-go.md); NFR-26 (бюджеты чанков 150/200
КБ gzip — свод С11: каждая мигрированная страница), NFR-27
(e2e-совместимость); FR-1/FR-2/FR-13/FR-17 (вход, route/reason),
FR-78 (согласие в модалке регистрации), FR-10/FR-11/FR-12/FR-77
(CTA, анкета multipart, редирект pending, согласие анкеты); BUG-062.

## What Changes (Что меняет)

- **BUG-062** (отдельная задача пакета, независимая от миграции):
  удалить плитку-аватар `span#avatar` из шапки /instructor-choice
  (frontend/instructor-choice.html + правило `.avatar` CSS + заполнение
  в frontend/js/instructor-choice.js — ФИО #uname остается); негативный
  инвариант «в шапке нет .avatar» — в e2e TC-UI-059 (дополнение сценария
  прямо предписано планом фикса BUG-062 — задокументированное исключение
  из NFR-27, прецедент TC-UI-059 в BUG-059/061); мокапы
  design/mocks/choice-instructor-a/b.html синхронно (плитка + правило
  `.avatar` убраны — прецедент «мокапы choice-a/b синхронно»
  BUG-059/060/061). Страница /instructor-choice остается легаси —
  мигрируется в следующей партии.
- **Анкета инструктора `/instructors/apply` на Vue**: новая страница
  `frontend/vue/src/pages/instructor-apply/` + вход
  `frontend/vue/instructor-apply.html`; wiring legacy
  (frontend/instructor-apply.html + frontend/js/apply.js)
  воспроизводится 1:1 — multipart POST /api/instructors/apply
  (текстовые поля + license_photo), согласие ПД обязательно (FR-77:
  кнопка сабмита блокирована до чекбокса; 422 позиция 1a «Согласие:
  поле обязательно» — серверная проверка, контракт НЕ меняется),
  файловые ошибки 413/415/422 и клиентская валидация ВУ (JPEG/PNG,
  ≤5 МБ) — у поля загрузки; 200 → localStorage-токены опроса (poll/
  exchange) и редирект /instructors/pending. Контракт apply НЕ МЕНЯЕТСЯ.
- **Лендинг `/` на Vue — ПОСЛЕДНЯЯ задача партии (самая рискованная:
  вход в кабинеты идет через модалки лендинга)**: новая страница
  `frontend/vue/src/pages/landing/` + вход `frontend/vue/index.html`;
  разметка 1:1 — hero («Права — без лишнего пути»), шаги 01–04,
  чат-бар «Гига ГАИшник» (визуальная заглушка: alert ai-open/quick/
  to-teachers — перенос как есть), плитки сервисов, футер; модалки
  входа/регистрации (m-login/m-register) выносятся в shared-компоненты
  каркаса (`src/shared/`, прецедент shared/utils.js С11) — легаси
  instructors.html продолжает использовать собственный дубль до своей
  миграции (следующая партия). Контракты НЕ МЕНЯЮТСЯ: POST /api/register
  (consent — FR-78: #reg-submit недоступен до чекбокса), POST
  /api/auth/login (route/reason §15.5: route=rejected → sessionStorage
  «instructor_rejected_reason» ДО редиректа — контракт polling/rejected
  не сломать; пишет его Vue-wiring модалки входа вместо landing.js),
  семантика закрытия BUG-055/056 (крестик/«Отмена»/Esc; фон m-login не
  закрывает; снятие open_login-флагов).
- **Сборка**: vite.config.mjs — два новых входа (multi-entry MPA —
  страница = отдельная точка входа, ОВ-3; SPA/vue-router/pinia
  ЗАПРЕЩЕНЫ); scripts/check-budgets.mjs — page-чанки расширяются до
  пяти (NFR-26: бюджеты КАЖДОЙ мигрированной страницы — свод С11).
  Dockerfile, docker-compose.yml, nginx, CI — БЕЗ ИЗМЕНЕНИЙ: node
  builder-этап собирает dist из всех входов, статика /vue/assets уже
  отдается backend/app.py — только регистрация страниц.
- **backend/app.py**: маршруты `/` и `/instructors/apply` в
  `_PAGE_ROUTES` переключаются на отдачу входов из
  `frontend/vue/dist` (маркер `vue:` — механика С11); legacy-файлы
  frontend/index.html, frontend/js/landing.js,
  frontend/instructor-apply.html, frontend/js/apply.js удаляются
  (замена монолита целиком, ADR-008 п.4). Остальные маршруты и все
  `/api/*` — без изменений.
- **Тесты-потребители legacy-файлов** переводятся на новые носители —
  ТОЛЬКО переносы источников чтения (прецедент 2.3 пилота и 3.1 С11):
  tests/web/test_login_modal.py, tests/web/test_bug001.py,
  tests/api/test_policy.py, tests/web/test_instructor_pages.py (§4.2);
  в tests/web/test_ui_playwright.py — только два источника чтения
  design-guard (tag-balance: + входы vue/index.html и
  vue/instructor-apply.html — прецедент vue/review-form.html С11) и
  негативный инвариант BUG-062 в TC-UI-059. Сценарии e2e не
  переписываются (NFR-27): якоря TC-UI-001/002, TC-UI-004, TC-UI-043…045,
  TC-UI-053, TC-S9UI-003, TC-UI-059/060 зеленые без правок.
- **Проверка бюджетов NFR-26** на артефактах сборки (gzip-размеры чанков
  dist: каждый vendor-чанк ≤150 КБ gzip; JS первого захода КАЖДОЙ из
  пяти страниц ≤200 КБ gzip) — приемочный шаг партии.

## Impact (Последствия)

- Код: `frontend/vue/vite.config.mjs` (+2 входа),
  `frontend/vue/index.html`, `frontend/vue/instructor-apply.html`
  (новые входы), `frontend/vue/src/pages/landing/`,
  `frontend/vue/src/pages/instructor-apply/` (новые страницы),
  `frontend/vue/src/shared/` (НОВОЕ: компоненты модалок входа/регистрации
  — вынос общего контура; api.js/utils.js — без изменений),
  `frontend/vue/scripts/check-budgets.mjs` (+2 page-чанка);
  `backend/app.py` (две строки карты `_PAGE_ROUTES`).
- BUG-062: `frontend/instructor-choice.html` (+ `frontend/js/
  instructor-choice.js`), `design/mocks/choice-instructor-a.html`,
  `design/mocks/choice-instructor-b.html`.
- Удаление: `frontend/index.html`, `frontend/js/landing.js`,
  `frontend/instructor-apply.html`, `frontend/js/apply.js` (после
  переключения маршрутов; остальные 8 монолитов не трогаются).
- Тесты: tests/web/test_login_modal.py, tests/web/test_bug001.py,
  tests/api/test_policy.py, tests/web/test_instructor_pages.py —
  переносы источников чтения (разрешенная правка, прецедент 2.3/3.1);
  tests/web/test_ui_playwright.py — только два переноса носителя
  design-guard + негативный инвариант BUG-062 (обе правки —
  задокументированные исключения, design.md «Границы правок тестов»).
- Master-spec: ADDED домен Frontend — «Лендинг ученика на Vue (/)»,
  «Анкета инструктора на Vue (/instructors/apply)»; ADDED домен
  student-instructor-choice — «Шапка „Выбора инструктора" без
  плитки-аватара (BUG-062)».
- Кейпабилити БЕЗ дельт (проверено по openspec/specs/): PersonalData
  (согласия FR-77/FR-78 — поведение сохранено, ссылки /policy на месте),
  instructor-application (макет-эквивалентность без редизайна, контракт
  apply не меняется), auth/instructor-auth (route/reason — без
  изменений), registration (контракт /api/register не меняется),
  navigation (переходы / → /instructors → /instructors/apply →
  /instructors/pending сохранены), StudentFlow (вход через лендинг —
  те же экраны).
- Зависимости: нет новых пакетов npm (только vue — уже в каркасе);
  зависимостей от параллельных change-пакетов нет.

## Out of scope / допущения

- Остальные страницы плана ADR-008 (`/instructors`, `/cabinet`,
  `/instructor/dashboard`, `/admin-dashboard`, `/registered`,
  `/admin-login`, `/instructor/cabinet-stub`) — следующие партии; в
  объеме только `/`, `/instructors/apply` и BUG-062.
- instructors.html НЕ мигрируется: легаси-дубль модалки входа остается
  как временное состояние (умирает с монолитом при миграции
  /instructors; design.md «Сознательные ограничения»).
- Чат-ассистент «Гига ГАИшник» — перенос ВИЗУАЛЬНОЙ заглушки (alert)
  1:1; реальный чат (Hermes) — вне объема.
- Редизайн обеих страниц, перенос текстов/заголовков иными словами —
  вне объема: визуальная эквивалентность текущим экранам (директива
  «без большого переписывания» ADR-008; тексты мокапа лендинга —
  дословно, включая бренд «Сбер» до команды Заказчика).
- Изменения контрактов: POST /api/register, POST /api/auth/login
  (route/reason), POST /api/instructors/apply (422 позиция 1a),
  localStorage-ключи polling, редиректы — НЕ меняются; `/api/*`
  каркасом не затрагиваются (NFR-27).
- Аватар ученика на /review (шапка формы отзыва, партия С11) — вне
  решения BUG-062 (решение касается шапки «Выбора инструктора»);
  сверка выполнена (design.md «BUG-062»).
- Новые сторонние библиотеки (UI-киты, модальные библиотеки) — не в
  объеме; правило бюджета ADR-008 действует.

## Отслеживание

- FR-1, FR-2, FR-13, FR-17 (вход, route/reason, sessionStorage
  «instructor_rejected_reason») → specs/Frontend/spec.md «Лендинг
  ученика на Vue (/)»; tasks 3.2, 4.2.
- FR-78 (обязательное согласие в модалке регистрации) → specs/Frontend/
  spec.md «Лендинг ученика на Vue (/)»; tasks 3.2.
- FR-10, FR-11, FR-12 (CTA анкеты, multipart с ВУ, редирект pending) →
  specs/Frontend/spec.md «Анкета инструктора на Vue
  (/instructors/apply)»; tasks 3.1, 4.2.
- FR-77 (обязательное согласие анкеты, 422 позиция 1a) → specs/Frontend/
  spec.md «Анкета инструктора на Vue (/instructors/apply)»; tasks 3.1.
- FR-84 (multi-entry, постраничная миграция, ADR-008) → обе дельты
  Frontend; tasks 2.1.
- FR-85 + NFR-27 (e2e без правок сценариев) → дельты (якоря TC-UI-001/
  002/004/043…045/053, TC-S9UI-003); tasks 4.1, 6.1.
- NFR-26 (бюджеты 150/200 КБ gzip на артефактах, каждая страница) →
  tasks 2.1, 5.1.
- BUG-062 → specs/student-instructor-choice/spec.md «Шапка „Выбора
  инструктора" без плитки-аватара (BUG-062)»; task 1.1.
- TC-UI-059 (негативный инвариант) → якорь приемки BUG-062; task 1.1.
