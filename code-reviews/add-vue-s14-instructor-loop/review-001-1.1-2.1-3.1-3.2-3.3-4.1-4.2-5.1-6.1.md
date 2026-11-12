<!-- Reviewer-Delegation: deleg-s14-dev1-external | независимый код-ревьюер (не автор диффа) | дифф: e895c82..2ac3fe1 (8 dev-коммитов) | ветка: feat/s14-instructor-loop | дата: 2026-11-12 -->

# Code review: dev-партия add-vue-s14-instructor-loop — задачи 1.1, 2.1, 3.1, 3.2, 3.3, 4.1, 4.2, 5.1, 6.1 (Vue-миграция: лендинг инструкторов /instructors, кабинет /instructor/dashboard, «Мои документы» /instructor/documents, чистка stub, консолидация модалок)

Периметр: весь dev-дифф e895c82..HEAD (30 файлов, +2240/−685): stub-чистка
(1.1), входы партии + бюджет-скрипт (2.1), лендинг инструкторов +
консолидация wiring входа (3.1), кабинет (3.2), документы — новая страница
(3.3), удаление легаси + переводы тестов-потребителей (4.1), маршруты
(4.2), бюджеты NFR-26 (5.1), e2e-гейт (6.1). Контекст: proposal/design/tasks
пакета, review-001-architecture.md (approve-with-notes, MIN-1 — счет
~96 КБ wiring кабинета — учтен в design), ADR-008, BUG-047/BUG-051/
BUG-054/BUG-055/BUG-056, sdd §15.5.

## Вердикт: approve

Все 9 задач партии приняты. Замечаний blocker/major нет. Ключевые контракты
проверены дословно против git-истории легаси (программные сравнения, не
глазами): (1) wiring кабинета после нормализации пробелов — ПОБАЙТОВО
идентичен dashboard-instructor.js@e895c82 (кроме import-путей, vue-обертки
и замены window.* → bridge); (2) 13 общих функций раздела документов —
идентичны; (3) тела входов instructors/dashboard — идентичны легаси
(+#app-обертка); (4) разметка variant 'instructors' LoginModal — дословна
(все 5 отличий); (5) route/reason §15.5 — дословен, причина отказа пишется
ДО редиректа. Ворота 6.1 зеленые: полный e2e 69 passed БЕЗ правок сценариев
(дифф test_ui_playwright.py — ровно два design-guard переноса), регресс
носителей 94 passed, бюджеты 8 страниц green, openspec validate --all
--strict 23 passed.

## Замечания

| Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|
| minor | openspec/changes/add-vue-s14-instructor-loop/design.md:389 | Сводная таблица «Обработка ошибок» утверждает для документов «m-replace — фон НЕ закрывает (как legacy)» — фактическое поведение легаси ОБРАТНОЕ: dashboard-instructor.js@e895c82:1505 закрывает диалог по клику на фон (`e.target===this → docsCloseReplace()`). Обе Vue-копии (кабинет 3.2 — побайтовый перенос, документы 3.3 — App.vue:396) корректно следуют связующему правилу «1:1 legacy», т.е. код прав, неточна сводка в design. Носитель после arch-review не правится в пакете (прецедент «исторические носители»); на поведение и ворота не влияет. | Правка одной клетки таблицы — в будущей docs-партии или при следующем касании пакета; в С14 не требуется. |

## Наблюдения (не замечания)

- **Документы: статический вход без onclick на «Выйти»** —
  vue/documents.html:39 («оболочка», новый файл без легаси-предка) имеет
  `<button class="icon-btn" title="Выйти">` без обработчика; рабочий
  `@click="logout()"` появляется после гидрации (App.vue:44). Окно до
  гидрации — миллисекунды, у страницы нет легаси-паритета (в отличие от
  кабинета, где статический вход сохраняет onclick 1:1 с легаси).
  Действий не требует; заметить при будущих e2e страницы.
- **Rolldown-раскладка (артефакт бандлера — зафиксировать в приемке):**
  как и в С12, большая часть runtime Vue легла в shared-чанк
  (shared 63.9 КБ raw / 24.7 КБ gzip; vue-чанк 9.3 КБ raw / 4.1 КБ gzip);
  page-чанк кабинета 80.4 КБ raw / 22.6 КБ gzip. Ворота NFR-26 соблюдаются
  с запасом: первый заход кабинета — максимум партии, 50.1 КБ gzip при
  бюджете 200; остальные страницы 29.3–33.5 КБ; vendor ≤150; чужих
  page-чанков нет (check-budgets: «страниц: 8» — OK).
- **BUG-062 — вне диффа, подтверждено**: инвариант касается
  instructor-choice.html (ученический контур, следующая партия) — файл
  пакетом не тронут (нет в diffstat), наследие не задето.
- **Стенд ревьюера**: запуск e2e потребовал локальной досборки окружения
  Chromium (libatk/libatk-bridge/libgbm/libasound и X-библиотеки отсутствуют
  в контейнере; доcommence из пула noble, LD_LIBRARY_PATH) — к коду партии
  отношения не имеет; на собранном свежем dist набор зелен (см. факты).

## Факты проверок (свежие прогоны на HEAD 2ac3fe1, чистое дерево, dist пересобран)

### 1. Модалки/вход инструктора (3.1) — приоритет ревью
- **variant 'instructors' — дословно, 5 отличий из design**:
  LoginModal.vue (v-else-ветка) vs легаси instructors.html@e895c82:22–31 —
  p БЕЗ .sub ✓, подписи `<span>` вместо `<label>` ✓, кнопки `btn
  primary`/`btn ghost` ✓, БЕЗ alt-строки «Нет аккаунта?»/#to-register ✓,
  набор id тот же, #login-close ВНЕ карточки БЕЗ data-close (закрытие
  вешается wiring напрямую — как легаси js/instructors.js:26) ✓. Дефолтный
  рендер 'landing' не меняется (v-if ветка — прежняя разметка С12 дословно;
  prop variant default 'landing').
- **loginWiring.js — route/reason §15.5 дословно**: postJSON('/api/auth/login')
  → setToken(res.data.token) → route-маппинг (cabinet → /instructor/dashboard,
  pending → /instructors/pending, rejected → sessionStorage
  'instructor_rejected_reason' ДО location.href='/instructors/rejected' —
  loginWiring.js:38, порядок операторов сохранен, else → /cabinet); порядок
  `res.status===200&&res.data.ok` сохранен; `location.href='/';` НЕТ
  (BUG-055-инвариант теста зелен). Потребители ключа не задеты:
  instructor-rejected/App.vue:34 и instructor-pending/App.vue:52 читают
  тот же ключ (файлы вне диффа).
- **Лендинг «/» переключен на композабл ДОСЛОВНО**: дифф landing/App.vue —
  ровно перенос doLogin (фрагменты совпадают с композаблом символ-в-символ),
  register-wiring остался; BUG-056-семантика (снятие open_login* при
  закрытии, App.vue:147–148) не тронута; setToken-импорт жив (doRegister).
- **wiring js/instructors.js 1:1** в App.vue onMounted: data-open-login —
  локальное открытие БЕЗ флагов (body overflow hidden, фокус #login-email),
  закрытие #login-close/[data-close]/Esc, клик по фону НЕ закрывает,
  #open-form → location.href='/instructors/apply'.
- **Последний дубль умер**: `grep 'id="m-login"' frontend --include=*.html` →
  только frontend/vue/* (index.html, instructors.html; dist вне git);
  легаси instructors.html/js/instructors.js удалены.
- **Синхронность входа**: тело vue/instructors.html vs легаси instructors.html
  — ПОБАЙТОВО идентично (кроме #app-обертки и script-src); App.vue template
  vs статический вход — канонически идентичны (программное сравнение с
  нормализацией пробелов и onclick≡@click; расхождение 0).

### 2. Кабинет (3.2) и документы (3.3)
- **Гвард — фактический**: fetch('/api/auth/me',{X-Session-Token}) →
  !r.ok → location.href='/' (App.vue:445–446) + fetch('/api/instructor/
  dashboard') → res.status===401||res.status===403 → toLogin('/')(App.vue:
  609–612); ФИО/инициалы из /api/auth/me (FR-20). GET /api/instructor/me в
  коде НЕ появляется (grep по frontend/backend/tests — только упоминание
  в комментарии-сверке design). Гвард документов — тот же (auth/me → 401 →
  '/'; GET /api/instructor/documents 401/403 → '/' — App.vue:322–325).
- **Wiring кабинета — побайтовый перенос**: скрипт App.vue vs
  dashboard-instructor.js@e895c82 после нормализации пробелов/комментариев —
  diff содержит ТОЛЬКО: import-пути ('../shared' → '../../shared', +vue),
  vue-обертку (setup/onMounted) и блок window.toast/navTo/changeWeek/logout
  → bridge.* (то же 4 имени; window не засоряется — onclick→@click бридж
  без утечек). Оставшиеся 25 innerHTML — идентичны легаси (очистки/статичные
  шаблоны; пользовательские строки — через node()/textContent, включая
  причину отказа документа — App.vue-документы:253).
- **MIN-2 needles дословны**: '/api/instructor/cars/'+t.carId+'/photo/'+t.angle
  (App.vue:1552), c.sts_url (App.vue:1433) — конкатенация строк сохранена,
  template literals не введены; test_s3_backend green.
- **Демо-данные 2.2 сохранены**: 3 demo-tag «демо» (сайдбар Расписание/
  Доходы/Материалы) — счет совпадает с легаси; статические панели (stats 84
  600 ₽, appointments, «Ближайшее занятие», «Последние операции», «Мой
  автомобиль») перенесены 1:1 (вход идентичен легаси-телу); реальные API —
  только там, где были в легаси (summary/requests/students/dashboard/
  documents/cars) — «оживления» демо нет (скрипт идентичен легаси).
- **Сайдбар РОВНО (BUG-051/TC-UI-028)**: 9 data-tab (Мой день, Расписание,
  Календарь, Мои ученики, Мои автомобили, Доходы и выплаты, Материалы и
  обучение, Профиль и документы, __logout__) — перечень и порядок идентичны
  легаси; «Бронирования»/«Мой автомобиль»/«Запросы учеников» в навигации
  НЕТ; ссылку на /instructor/documents пакет не добавлял. TC-UI-028 зелен
  (в прогоне 69 passed).
- **Раздел документов кабинета и страница — 1:1**: docName/docMetaText/
  docVersionLine/docSubverNodes/docCardNode/mcValidatePhoto/mcLoadImg/
  mcUpload/docsAskReplace/docsCloseReplace/docsPickFile/docsStartUpload/
  docsCloseReplaceSilent — 13/13 функций ПОБАЙТОВО идентичны легаси
  (программное сравнение); FR-69 (merge СТС по cars), FR-71 (диалог с
  явной кнопкой; первая загрузка без предупреждения), FR-72 (перезагрузка
  после загрузки), BUG-054 (стрелки НАД фото, Esc; фон m-view закрывает,
  m-replace — как легаси, см. замечание minor). Оболочка страницы — бренд →
  dashboard, «← В кабинет», logout → /instructors; контракты ('file'/'photo')
  не менялись; standalone frontend/documents.html НЕ создан.
- **BUG-047**: негативный список standalone в test_back_links_lead_to_
  role_home — БЕЗ ПРАВОК; frontend/ корень — 6 монолитов (choice/admin×2/
  cabinet/policy/registered), documents.html отсутствует. Инвариант зелен.

### 3. NFR-27 / переводы носителей (4.1) — контроль git diff
- **test_ui_playwright.py — ровно два design-guard переноса** (полный дифф
  прочитан): (а) test_back_links_lead_to_role_home — чтение dash → вход
  vue/instructor-dashboard.html + App.vue (конкатенация двух носителей;
  комментарий-маркер задачи 4.1); (б) параметризация tag-balance —
  −instructor-dashboard.html, +cabinet.html перенос строки, +vue/
  instructor-dashboard.html +vue/instructors.html +vue/documents.html.
  Селекторы/маршруты/ожидания сценариев — не тронуты (0 иных дифф-строк).
- **test_instructor_pages.py**: §4.1 — носители page()/frontend_source() →
  вход vue/instructors.html + App.vue + loginWiring.js + styles.css
  (CSS-сверка мокапа → styles.css, перенос дословный — styles.css идентичен
  легаси-<style> за вычетом пустой строки); контракты
  (location.href='/instructors/apply', data-open-login, postJSON('/api/auth/
  login', отсутствие location.href='/';) — дословны; §4.4 — ровно 2 теста
  удалены вместе со страницей (прецедент MAJ-1 пилота); §4.2/§4.3 — не
  тронуты.
- **test_instructor_dashboard.py**: PAGE → vue-вход; vue_dashboard_source() =
  вход + App.vue + shared/api.js + utils.js; needles (fetch('/api/instructor/
  dashboard', 'X-Session-Token', navTo, document.querySelectorAll('.nav
  button')) — дословны; CSS-носитель → styles.css (идентичен мокапу-легаси).
- **test_s3_backend.py**: носитель дашборда → вход + App.vue; 3 needles —
  дословны (конкатенация сохранена); cabinet-проверка не тронута.
- **test_login_modal.py**: vue_landing_source() + loginWiring.js; фрагменты
  WIRING_FRAGMENTS и LOGIN_MODAL_TEXTS — без правок (пройдены).
- **test_auth_route.py**: −"/instructor/cabinet-stub", +"/instructor/
  documents" (инвариант 200 text/html без правок логики) — ровно 1.1/4.2.
- **check_tag_balance.py**: DEFAULT instructor-dashboard.html → vue-вход;
  прогон OK (4 файла).

### 4. Легаси-чистка (1.1/4.1) и маршруты (4.2)
- Удалены целиком 6 файлов: instructors.html (19 085 Б), instructor-dashboard.html
  (85 584 Б), js/instructors.js, js/instructor/dashboard-instructor.js
  (98 649 Б), instructor-cabinet-stub.html, js/instructor/instructor-cabinet-stub.js;
  каталога frontend/js/instructor больше нет.
- `git grep cabinet-stub -- frontend backend tests` — ПУСТО; остаточные
  упоминания имен легаси в дереве — только комментарии/docstring (проверено
  grep-обходом .py/.yml/.mjs/.json вне исторических носителей — живых
  чтений путей нет).
- _PAGE_ROUTES: −"/instructor/cabinet-stub"; "/instructors" →
  "vue:instructors.html", "/instructor/dashboard" → "vue:instructor-
  dashboard.html", NEW "/instructor/documents" → "vue:documents.html";
  пилотный хендлер /instructors/pending, vue:-маршруты С11/С12
  (vue:index/vue:instructor-apply/vue:instructors-rejected/vue:review-form),
  _PAGE_REDIRECTS (/my-cars → dashboard#/my-cars), /vue/assets/* — БЕЗ
  ИЗМЕНЕНИЙ; 4.1+4.2 в одной сессии (коммиты da02fe3→2ac3fe1 без
  промежуточного состояния «маршрут без отдачи» в пуше).

### 5. Сборка и бюджеты (2.1/5.1)
- vite.config.mjs: ровно +3 входа (instructors, instructor-dashboard,
  documents), manualChunks/base/pinned-версии — без изменений.
- check-budgets.mjs: PAGES = 8 (комментарий о reconcile «7→8» — design
  «Сверка контрактов решения»).
- Свежий прогон: npm run build OK (крупнейший page-чанк
  instructor-dashboard 80.43 КБ / 22.55 КБ gzip; documents 15.17 / 5.37);
  npm run check:budgets — «OK: бюджеты NFR-26 соблюдены (страниц: 8)»:
  первый заход instructors-pending 30.2 / instructors-rejected 29.3 /
  review-form 31.4 / index 30.6 / instructor-apply 33.3 / instructors 30.9 /
  instructor-dashboard 50.1 / documents 33.5 КБ gzip (≤200); vendor
  modulepreload 0.4 + vue 4.0 (≤150); чужих page-чанков нет.
- tag-balance: python3 scripts/check_tag_balance.py — OK (4 файла).
- openspec validate add-vue-s14-instructor-loop --strict — valid;
  openspec validate --all --strict — 23 passed, 0 failed. Спек-дельты
  сверены: Frontend ADDED ×3 (заголовки = маршруты партии),
  instructor-auth MODIFIED (заголовок инварианта «Пользователь найден —
  заглушка кабинета» сохранен дословно, содержание → /instructor/dashboard)
  + REMOVED (Reason заполнен).

### 6. Ворота 6.1 — прогон ревьюера (свежий dist, чистое дерево)
- `pytest tests/web/test_instructor_pages.py tests/api/test_auth_route.py
  tests/api/test_instructor_dashboard.py tests/api/test_s3_backend.py
  tests/web/test_login_modal.py tests/web/test_bug001.py
  tests/web/test_static.py` — **94 passed** (108s).
- `pytest tests/web/test_ui_playwright.py` — **69 passed** (142s):
  TC-UI-003/005/008/009/010/015/016/023/024/025…028/030/033/034/040/042/
  052/059/060, TC-S9UI-003, accept-flow, xss, BUG-047/tag-balance guards —
  на селекторах и ожиданиях без правок. Совпадает с отчетом 6.1
  (152+69 = полный pytest + playwright на стенде разработчика; на стенде
  ревьюера переведенные и регрессные носители — 94, playwright — 69).
- Первая попытка e2e на стенде ревьюера дала 60 ERROR (Chromium не
  стартовал: libatk-1.0.so.0 отсутствует в контейнере — environmental,
  до code не относится); после досборки библиотек — 69 passed.

## Итог

- MAJ: нет. MIN: 1 (сводка design.md:389 о m-replace/фон противоречит
  фактическому legacy и обеим Vue-копиям; код прав — правка design вне
  пакета). Наблюдения: 4 (без действий).
- Вердикт: **approve** — партия к приемке; ворота 5.1/6.1 выполнены на
  артефактах, NFR-27 соблюден (дифф test_ui_playwright.py — только
  задокументированные design-guard переносы).
