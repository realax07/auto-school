# Arch-review 001: add-vue-s14-instructor-loop (Спринт 14)

- Дата: 2026-11-12
- Ревьюер: архитектор (Hermes)
- Коммит СА-фазы: b264a26 «[s14] CA: пакет add-vue-s14-instructor-loop»
- База проверки: фактический код на HEAD b264a26 — backend/app.py
  (карта `_PAGE_ROUTES`/`_PAGE_REDIRECTS`, цикл `vue:`, пилотный
  хендлер), backend/auth/auth.py, backend/instructor/instructor_documents.py,
  frontend/vue/vite.config.mjs, frontend/vue/scripts/check-budgets.mjs,
  frontend/vue/src/shared/LoginModal.vue, frontend/vue/src/pages/landing/
  App.vue, легаси frontend/instructors.html + js/instructors.js,
  frontend/instructor-dashboard.html + js/instructor/
  dashboard-instructor.js, frontend/instructor-cabinet-stub.html + js,
  tests/ (grep-обход всех потребителей легаси), scripts/check_tag_balance.py,
  CI flow.yml, openspec/specs/ (мастер-спеки 19 доменов), openspec
  validate --all --strict.

## Вердикт

**approve-with-notes** (MAJ — нет; MIN-1 — счетная неточность design.md
в разделе НФТ, исправлена коммитом arch-review; наблюдения Obs-1/Obs-2 —
без действий на СА-фазе. Блокировки dev-старта нет.)

Карта: **без изменений** (см. раздел 8).

## 1. ADR-008: multi-entry, бюджеты NFR-26, удаление легаси — сверено пофакто

- **Состав входов.** vite.config.mjs — ровно 5 существующих входов
  (instructors-pending, instructors-rejected, review-form, index,
  instructor-apply — строки 23–39). Партия добавляет ровно 3
  (instructors, instructor-dashboard, documents). 5 + 3 = **8
  page-чанков** — утверждение CA в proposal/tasks/design точно. Решение
  Заказчика (decisions/2026-11-09-sprint14-go.md:31,44) говорит «станет
  7 страниц»/«бюджеты 7 чанков» — расхождение реально, reconcile СА в
  design «Сверка контрактов решения» (8, правка решения не делается) —
  корректная обработка: NFR-26 «каждая мигрированная страница»
  выполняется только при 8; комментарий с чеком состава заложен в
  check-budgets (задача 2.1) и замер 5.1 — по восьми.
- **check-budgets.mjs** сегодня имеет PAGES из 5 имен (строка 34) и
  замыкание/бюджеты по каждой — расширение карты до восьми в 2.1
  механически корректно: скрипт строит замыкание входа из dist-HTML
  (строки 91–109), новые входы подхватываются без правок логики.
- **Documents — БЕЗ отдельного легаси-входа: валидно.** Дизайн-гвард
  BUG-047 (test_ui_playwright.py:1187–1194) — негативный список
  standalone-страниц проверяет `frontend/documents.html` в корне
  frontend/; новая страница создается сразу как `frontend/vue/
  documents.html` — инвариант остается зеленым БЕЗ ПРАВОК, легаси-версии
  страницы не существует ни до, ни после партии (критерий решения
  «documents.html — в archive легаси» — тривиально). Негативный список
  в пакете не трогается — подтверждено задачей 4.1.
- **TC-UI-028 «сайдбар РОВНО» (BUG-051, test_ui_playwright.py:1227).**
  Сценарий мокает API через page.route и проверяет точный перечень
  data-tab кабинета; раздел «Профиль и документы» остается разделом
  кабинета, ссылку на /instructor/documents из сайдбара пакет НЕ
  добавляет — сценарий зелен без правок. Двойная точка входа к
  документам — сознательное состояние, задокументировано в design
  «Сознательные ограничения».
- **Удаление легаси ЦЕЛИКОМ.** Четыре файла партии (instructors.html
  19 085 Б, js/instructors.js 3 125 Б, instructor-dashboard.html
  85 584 Б, js/instructor/dashboard-instructor.js 98 649 Б) + пара
  заглушки (5 196 Б + 1 280 Б) удаляются одновременно с переключением
  маршрутов (4.1+4.2 одной сессией — параллельное существование версий
  исключено, ADR-008 п.4). Остальные монолиты (registered/admin-*/cabinet/
  instructor-choice/policy + instructor-bookings, booking) не трогаются.
  Замечание design «~60 КБ JS wiring» — фактический размер файла
  98 649 Б ≈ 96 КБ (см. MIN-1).

## 2. Роуты: vue:-маркеры, механика app.py, изъятие cabinet-stub

- Механика маркера существует: `_PAGE_ROUTES` содержит «vue:index.html»
  (:44), «vue:instructor-apply.html» (:54), «vue:instructors-rejected.html»
  (:63), «vue:review-form.html» (:75); цикл отдачи (:179–200) читает
  VUE_DIST_DIR при префиксе `vue:`, 404 без dist. Перевод «/instructors»
  → «vue:instructors.html», «/instructor/dashboard» →
  «vue:instructor-dashboard.html», новая строка «/instructor/documents»
  → «vue:documents.html» — ровно паттерн С11/С12 «одной строкой карты».
  Имена совпадают с dist-артефактами входов (multi-entry: dist/<entry>.html).
- Пилотный хендлер /instructors/pending (:151) — вне карты, пакетом не
  трогается (сверено с задачей 4.2). `_PAGE_REDIRECTS` /my-cars →
  /instructor/dashboard#/my-cars (:86–88) — сохранение хеша раздела
  подтверждено design (navTo + хеш-синхронизация в Vue-версии).
- Статика /vue/assets/:174 — покрывает новые чанки без изменений;
  base '/vue/' и manualChunks (vue/@vue/ → 'vue', /src/shared/ →
  'shared') в конфиге присутствуют — loginWiring.js попадет в
  shared-чанк автоматически, отдельного правила не требует.
- Изъятие «/instructor/cabinet-stub» (:64): переходов на маршрут в
  коде нет (grep по backend/, frontend/, tests/ — только строка карты,
  тест-список test_auth_route.py:253 и исторические носители sdd.md/
  code-reviews/test-model) — недостижимость подтверждена; удаление
  строки карты + файлов + §4.4 (ровно 2 теста: :353, :369) + пункт
  списка маршрутов — консистентно в 1.1.

## 3. Модалки: последний дубль, variant, консолидация wiring

- **Разметка instructors.html дословна в описании variant.** Все пять
  отличий от landing-варианта сверены по факту легаси: (1) `<p>Войдите
  в личный кабинет</p>` — без class="sub"; (2) подписи полей — `<span>`,
  не `<label>`; (3) кнопки `btn primary`/`btn ghost` (у landing —
  `btn btn-primary`/`btn btn-ghost`); (4) НЕТ alt-строки «Нет аккаунта?»
  и #to-register; (5) тот же набор id (m-login, login-close ВНЕ карточки,
  login-email/password/error/submit, data-close на «Отмене»).
  Существующий LoginModal.vue ('landing') при добавлении пропа variant
  дефолтный рендер не меняет — e2e лендинга и LOGIN_MODAL_TEXTS
  (носитель vue/index.html между маркерами) не затронуты.
- **wiring js/instructors.js — сверен построчно.** data-open-login →
  локальное открытие БЕЗ sessionStorage-флагов (BUG-055, строки 4–15);
  закрытие — крестик/«Отмена»(data-close)/Esc, клик по фону НЕ закрывает
  (BUG-056 — обработчика e.target нет, строки 16–28); #open-form →
  location.href='/instructors/apply'. Сабмит: postJSON('/api/auth/login')
  → setToken → route-маппинг §15.5 (route==='cabinet' →
  /instructor/dashboard, 'pending' → /instructors/pending, 'rejected' →
  sessionStorage.setItem('instructor_rejected_reason', reason) ДО
  редиректа /instructors/rejected, else → /cabinet) — design обязывает
  сохранить фрагменты дословно в shared/loginWiring.js.
- **Консолидация на живом втором потребителе — реальна.** App.vue
  лендинга «/» содержит идентичный doLogin (:124–137) и те же фрагменты
  контракта; перенос в композабл — механический. WIRING_FRAGMENTS
  test_login_modal.py (:56–63) — плоский JS, совместим с композаблом;
  перенос носителя (+loginWiring.js в vue_landing_source) заложен в 3.1.
  Копий m-login в репо ровно две: frontend/instructors.html (умирает) и
  frontend/vue/index.html — «последний дубль» подтвержден; после партии
  `git grep 'id="m-login"' frontend -- '*.html'` — только frontend/vue/*.
- **Связка с С9/С11.** Потребители ключа на Vue существуют:
  instructor-rejected/App.vue и instructor-pending/App.vue читают
  REJECTED_REASON_KEY='instructor_rejected_reason' — контракт
  polling/rejected не зависит от точки входа модалки; open_login* пишутся
  только лендингом «/» (снятие при закрытии :157–158 — BUG-056),
  /instructors флагов не касается — семантика постранично сохранена.

## 4. Кабинет: фактический гвард, демо 2.2, раздел документов

- **Гвард = фактический, решение Заказчика исправлено корректно.**
  GET /api/instructor/me в backend НЕ существует (grep по backend/ —
  пусто). Легаси-гвард: fetch('/api/auth/me', X-Session-Token) → !r.ok →
  '/' (dashboard-instructor.js:20–29) + fetch('/api/instructor/dashboard')
  → 401/403 → toLogin('/') (:180–187); ФИО/инициалы из ответа /api/auth/me
  (FR-20). design «Сверка контрактов решения» фиксирует замену
  «GET /api/instructor/me» из решения на фактический гвард без ввода
  новых контрактов — правильно. Для /instructor/documents: гость → 401,
  чужая роль → 403 (instructor_documents.py:326–327, require_role) —
  редирект на «/» по 401/403 покрывает оба случая.
- **Демо-данные 2.2** присутствуют в легаси и переносятся как есть:
  demo-tag «демо» ×5, панели «Ближайшее занятие»/«Последние операции»/
  «Быстрые действия», разделы «Доходы и выплаты»/«Материалы и обучение» —
  соответствует решению («демо-данные сохраняются», реальные — будущие
  партии). «Мой день»/«Мои ученики» — реальные API (summary/requests/
  students) — как в legacy с С3/С8.
- **Документы-контракты не меняются:** GET /api/instructor/documents,
  GET …/{doc_id}/file (только владелец), POST …/license ('file'),
  POST /api/instructor/cars/{id}/photo/sts ('photo') — сверены с
  инструкторскими модулями; раздел «Профиль и документы» кабинета
  остается (e2e TC-UI-033/034/040/042 не переписываются), новая страница
  — та же функциональность (мастер-требование «Раздел "Мои документы"
  инструктора» — carrier-neutral, дельта не требуется).
- **TC-UI-028** — проходит (см. раздел 1): сайдбар переносится «ровно
  перечнем», BUG-051-инварианты (без «Бронирования»/«Мой автомобиль»/
  «Запросы учеников»-пункта, имя «Профиль и документы») воспроизведены
  в design 3.2 дословно.

## 5. Переносы тестов: полнота grep, MIN-2, behavioral — ноль правок

- **Grep-обход потребителей легаси (py/yml/mjs/json/Dockerfile, вне
  исторических носителей)** — список закрыт полностью, каждый потребитель
  из design-таблицы подтвержден:
  backend/app.py:50,64,67 (карта — 1.1/4.1/4.2); scripts/check_tag_balance.py:14
  (DEFAULT — перенос в 4.1); tests/api/test_s3_backend.py:1728 (needles
  дашборда); tests/api/test_instructor_dashboard.py:45,305,323 (PAGE +
  frontend_source; ровно 12 тестов — счет design точен); tests/web/
  test_ui_playwright.py:1190 (негативный список — БЕЗ ПРАВОК), :1195
  (BUG-047-чтение dash — перенос носителя), :4423 (tag-balance список —
  −легаси, +3 vue-входа); tests/web/test_instructor_pages.py (§4.1 —
  ровно 4 теста :31–117, §4.4 — ровно 2 :353,369); tests/api/
  test_auth_route.py:253 (−cabinet-stub в 1.1, +/instructor/documents
  в 4.2). Иных потребителей нет (test_static.py, conftest — чисто);
  CI flow.yml:27 собирает dist ДО pytest — правки CI не нужны.
- **Mechanica переносов реальна:** frontend_source следует только
  /js/-модулям legacy; прецедент С11 читает vue-носители напрямую
  (test_s3_backend.py:1743–1752: вход + App.vue) — заявленный способ
  переносов (вход + App.vue + shared) соответствует работающему
  прецеденту.
- **Needles конкатенации MIN-2 (прецедент С12):** needle
  `cars/'+t.carId+'/photo/'+t.angle` и `c.sts_url` — строковая
  конкатенация URL; design «Границы правок тестов» и tasks 4.1 прямо
  обязывают сохранить конкатенацию в Vue-коде (template literals НЕ
  вводить) — прецедент С11 (review-form) закреплен в носителе теста.
- **Behavioral — ноль правок сценариев:** допустимый дифф
  test_ui_playwright.py ограничен двумя design-guard переносами
  (список параметризации tag-balance; чтение dash в
  test_back_links_lead_to_role_home); TC-UI-003/005/008/009/010/015/016/
  023/024/025…028/030/033/034/040/042/052, TC-S9UI-003, accept-flow,
  xss — не правятся; якоря (id/классы/хеши) в design 3.1–3.3
  перечислены дословно и сверены с легаси. Контроль `git diff` в 4.1/6.1
  заложен. Прецедент «судьба legacy-тестов удаленной страницы» (§4.4
  удаляются) — arch-review-002 пилота MAJ-1 — соблюден.

## 6. Спеки: дельты, инвариант MODIFIED, валидации

- Состав дельт: Frontend — ADDED ×3 («Лендинг инструкторов на Vue
  (/instructors)», «Кабинет инструктора на Vue (/instructor/dashboard)»,
  «Мои документы на Vue (/instructor/documents)»); instructor-auth —
  MODIFIED «Роутинг после входа по статусу» + REMOVED «Заглушка кабинета
  инструктора». Вопрос по student-instructor-choice: дельта НЕ нужна —
  instructor-choice.html и выбор учеником пакетом не трогаются (вне
  состава решения). Дельт на instructor-dashboard/instructor-documents/
  navigation/auth не требуется: мастер-требования carrier-neutral
  (макет — design/mocks/dashboard-instructor.html, требование раздела
  документов — функциональное, не носитель) — сверено.
- **Инвариант MODIFIED соблюден:** все 4 заголовка сценариев базового
  требования «Роутинг после входа по статусу» сохранены дословно —
  включая сознательно сохраненный «Пользователь найден — заглушка
  кабинета» (содержание обновлено на /instructor/dashboard, заголовок —
  инвариант дельты; причина задокументирована в REMOVED-блоке).
  REMOVED-требование существует в мастере. Объем дельт — 112 и 54 строки
  (≤500), сценарии в формате GIVEN/WHEN/THEN.
- **Коллизий нет:** С12 (add-vue-s12-landing-apply) еще не архивирована,
  ее ADDED Frontend-требования («Лендинг ученика на Vue (/)», «Анкета
  инструктора на Vue (/instructors/apply)») — иные заголовки; код С12 в
  дереве есть (LoginModal/App.vue) — консолидация опирается на
  существующий код. openspec validate add-vue-s14-instructor-loop
  --strict — «Change … is valid»; openspec validate --all --strict —
  23 passed, 0 failed (прогон ревьюера на HEAD).

## 7. Риски — оценка

- **Демо-данные 2.2 в Vue-кабинете** — риск нулевой по архитектуре:
  перенос as-is помечен demo-tag, решение Заказчика фиксирует «сохраняются»;
  реальная замена — будущие функциональные партии (вне пакета).
- **BUG-047 guard** — зелен: негативный список path-based (frontend/ корень),
  vue-входы его не нарушают. См. Obs-2 о перспектива.
- **Бюджеты при 8 входах** — приемка замеряет 5.1 на артефактах; оценки
  design (vue ~20 КБ gzip + shared, стили в styles.css вне JS-бюджета,
  wiring без библиотек) — правдоподобны с запасом 200 КБ даже при
  фактических ~96 КБ raw wiring кабинета; политика «при превышении —
  сокращение зависимостей, не ослабление проверки» корректна.
- **Переходное состояние 4.1→4.2** внутри одной сессии (маршрут без
  отдачи не пушится) — риск рассинхрона исключен процедурно; 1.1
  параллелится безопасно (файловых пересечений нет; общие зоны app.py/
  test_auth_route/test_instructor_pages с 4.x помечены «не параллелить»).

## 8. MIN и наблюдения

- **MIN-1 (исправлен коммитом arch-review):** design.md «Решения по
  НФТ» оценивает кабинет как «≈85 КБ html + ~60 КБ JS wiring» —
  фактический размер frontend/js/instructor/dashboard-instructor.js —
  98 649 Б ≈ 96 КБ. На решения пакета не влияет (бюджеты считаются по
  gzip dist, стили уходят в CSS-чанк), но цифра занижает крупнейший
  перенос партии в ~1.6 раза — поправлена на фактическую.
- **Obs-1 (без действий):** мастер-сценарий Frontend «Мигрированная
  страница не оставляет legacy-версии» pinned на «остальные 12
  HTML-монолитов» — устарел еще с С11/С12 (прецедент: не дельта’d);
  после партии в frontend/ остается 6 монолитов. Предлагаю консолидацию
  этого сценария в будущей docs/specs-партии (вне С14).
- **Obs-2 (без действий):** зеленость BUG-047-гварда опирается на
  path-based негативный список (frontend/ корень). Если будущая партия
  обобщит список на vue/входы, /instructor/documents попадет под
  определение standalone — решение Заказчика 2026-11-09 (новый маршрут)
  старше по смыслу, чем директива BUG-047; design «Сознательные
  ограничения» уже документирует двойную точку входа. QA 6.1 — держать
  в поле зрения.

### Архитектурная карта

Карта: **без изменений**. Пакет не вводит новых архитектурных решений:
паттерн партии (multi-entry MPA, замена монолита целиком, бюджеты на
артефактах) — уже зафиксирован в ADR-008 и строке 18 карты; новый
вход/страница и консолидация модалок — исполнение плана, а не новое
решение (точка входа, деплой-контур, контракты /api/* и БД неизменны).
Рутинный рефреш карты (число мигрированных страниц, судьба последнего
дубля модалок) — после приемки партии (прецедент s11/s13).

## Итог

- MAJ: нет.
- MIN-1: счет design «~60 КБ JS wiring» → факт ~96 КБ (исправлено
  коммитом arch-review).
- Obs-1/Obs-2: без действий на СА-фазе (зафиксированы выше).
- Вердикт: **approve-with-notes** — dev-старт по задачам 1.1 → 2.1 →
  3.1 → 3.2 / 3.3 [P] → 4.1+4.2 → 5.1 → 6.1 разрешен; гейты — 5.1
  (бюджеты на 8 страницах) и 6.1 (полный e2e без правок сценариев,
  `git diff tests/web/test_ui_playwright.py` — только два design-guard
  переноса).
