<!-- Reviewer-Delegation: deleg-s12-dev1-external | независимый код-ревьюер (не автор диффа) | дифф: 76b26d9..2563258 (8 коммитов) | ветка: feat/s12-landing-apply | дата: 2026-11-08 -->

# Code review: dev-партия add-vue-s12-landing-apply — задачи 1.1, 2.1, 3.1, 3.2, 4.1, 4.2, 5.1, 6.1 (Vue-миграция: лендинг /, анкета /instructors/apply, BUG-062)

Периметр: весь dev-дифф 76b26d9..2563258 (25 файлов, +825/−397): BUG-062 (1.1),
входы+shared-модалки+бюджет-скрипт (2.1), анкета (3.1), лендинг (3.2),
удаление легаси+переводы тестов (4.1), маршруты (4.2), бюджеты NFR-26 (5.1),
e2e-гейт (6.1). Контекст: proposal/design/tasks пакета, arch-review-001
(approve-with-notes, MIN-1…MIN-3 учтены), ADR-008, план фикса BUG-062.

## Вердикт: approve

Все 8 задач партии приняты. Замечаний blocker/major нет; один minor
(устаревшая диагностическая утилита — вне контуров и CI, не блокирует
партию). Arch-review MIN-1 (счетчик 15 fd.append), MIN-2 (заглушки 2.1),
MIN-3 (импорт-эквивалент носителя) — реализованы (факты ниже).

## Замечания

| Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|
| minor | scripts/check_hero_overlap.py:37 (функционально), :2, :66 (docstring/дефолт) | Остаточная функциональная ссылка на удаленный легаси `frontend/index.html`: скрипт открывает `http://…/index.html` из `frontend/` — после удаления файла скрипт BUG-050 при запуске получает 404 и падает на селекторах. Критерий готовности 4.1 «ссылок нет (кроме docstring/archive/code-reviews/mocks/sdd)» формально не выполнен: строка 37 — живой код, не docstring. Скрипт вне CI и вне pytest (упоминается только в историческом test-model/bugs/BUG-050-hero-overlap.md), на поведение страниц и ворота партии не влияет — потому не blocker/major. | Удалить скрипт (предмет BUG-050 — легаси-hero — не существует) либо перепросить на вход dist (`frontend/vue/dist/index.html`) в следующей партии; в этом пакете правка не требуется (вне спеки пакета, дизайн-список потребителей скрипт тоже не содержал — пробел СА-фазы, не dev). |

## Наблюдения (не замечания)

- **Rolldown-чанк shared (артефакт бандлера — зафиксировать в приемке):**
  в сборке Vite 8/Rolldown часть runtime Vue легла в shared-чанк
  (`shared-*.js` 61.4 КБ raw / 23.8 КБ gzip; `vue-*.js` всего 9.3 КБ raw /
  4.1 КБ gzip) — S11 давал раздельные ~23 КБ (vue) и доли КБ (shared).
  Ворота NFR-26 соблюдаются: классификация ролей в check-budgets.mjs
  устойчива (shared — собственная роль, вне vendor-бюджета), первый заход
  каждой из 5 страниц ≤32.7 КБ gzip при бюджете 200, vendor ≤150, чужих
  page-чанков нет. Действий не требует; отслеживать при будущих
  зависимости/апгрейдах тулчейна.
- backend/app.py:4 (docstring) все еще описывает старую статику
  («/ → frontend/index.html») — разрешенный исторический носитель по
  критерию 4.1, но вводит в заблуждение; обновить opportunistic.
- test_login_modal.py: assert `from './api.js'` не заменен буквальным
  эквивалентом, а покрыт конструкцией носителя `vue_landing_source()`
  (вход + App.vue + shared/api.js): импорт
  `from '../../shared/api.js'` присутствует в App.vue:79, ребро
  page→shared подтверждается замыканием импортов в check:budgets.
  Соответствует MIN-3 design («механический эквивалент»); ослабления нет.

## Факты проверок (свежие прогоны на HEAD 2563258, чистое дерево)

### 1. Лендинг / (самый рискованный — модалки)
- **Разметка m-login/m-register дословна**: тело `frontend/vue/index.html`
  (без #app-обертки и комментариев) сравнено программно с телом легаси
  `frontend/index.html@76b26d9` — ПОБАЙТОВО ИДЕНТИЧНО (diff пуст),
  включая комментарии-маркеры «Модалка: Вход/Регистрация» — носитель
  LOGIN_MODAL_TEXTS (test_login_modal.py:40–45: заголовок, подзаголовок,
  подписи, плейсхолдеры — все во входе). **Тест проходит: свежий прогон
  `pytest tests/web/test_login_modal.py …` — 45 passed, 1 warning,
  10.28s** (вместе с test_bug001/test_instructor_pages/test_policy).
- **route/reason §15.5**: App.vue:132–138 — порядок
  `res.status===200&&res.data.ok` ДО route-разбора (тест
  test_login_route_mapping_wiring проверяет idx_ok<idx_route — зелен);
  `route==='rejected'` → `sessionStorage.setItem('instructor_rejected_reason',res.data.reason||'')`
  ДО `location.href='/instructors/rejected'` (App.vue:137) — код
  посимвольно равен легаси landing.js:70 и живому легаси-дублю
  instructors.js:46 (С11-контракт polling/rejected не сломан).
  Остальные ветви: cabinet→/instructor/dashboard, pending→
  /instructors/pending, default→/cabinet — дословно.
- **Consent FR-78**: RegisterModal.vue:37 `:disabled="!regConsent"` от
  @change чекбокса (статическая разметка несет `disabled` до гидрации) —
  задокументированный эквивалент `regSubmit.disabled=!regConsent.checked`;
  consent в payload из того же checked (App.vue:105) — эквивалент
  `consent:regConsent.checked`; тесты test_policy.py (TC-PD-005) зеленые.
- **BUG-055/056**: data-open/data-close/Esc, фон НЕ закрывает #m-login,
  снятие open_login/open_login_from при закрытии (App.vue:147–164) —
  1:1 с landing.js:4–21.
- **Легаси-дубль instructors.html НЕ тронут**: `git diff
  76b26d9..2563258 -- frontend/instructors.html frontend/js/instructors.js`
  пуст; instructors.js:46 (тот же ключ rejected-причины) и data-open-login —
  как были. Id-коллизий нет: разные бандлы (multi-entry).
- Заглушки ai-open/quick/to-teachers — alert-тексты дословно
  (App.vue:170–172 ≡ landing.js:79–81).

### 2. Анкета /instructors/apply
- **multipart**: App.vue:127–144 — ровно 15 `fd.append` (14 snake_case-полей
  + consent 'true'/'false') + условный `fd.append('license_photo',lf,lf.name)`
  (MIN-1 закрыт: счетчик в задачах/design исправлен до партии);
  построчно равен легаси apply.js:62–79 (сверено построчно).
- **422 позиция 1a**: не-«Файл» сообщение → только #notice
  (`noticeShow.value=true`, :class="{show: noticeShow}") — равен
  apply.js:103–108; файловые (413/415/422 с «Файл»-префиксом) →
  #license-error + notice. «Согласие: поле обязательно» попадает в
  notice — контракт сервера не менялся (проверка test_policy зеленая).
- **URL/контракты дословно**: `fetch('/api/instructors/apply',{method:'POST',body:fd})`
  (≡apply.js:80), `location.href='/instructors/pending'`,
  localStorage `application_poll_token`/`application_exchange_token`
  ДО редиректа (App.vue:154–158 ≡ apply.js:92–96); sessionStorage на
  странице отсутствует (тест-ассерт зеленый).
- **BUG-048 миниатюра**: objectURL/отзыв, has-file класс, клиентская
  валидация `5*1024*1024`/`validateLicenseFile` — дословно (≡apply.js:11–33);
  тексты ошибок = серверным.
- **Формат own/sber**: реактивный эквивалент updateFormat —
  `:disabled="plateDisabled"`, watch очищает plate при sber, opacity .55
  (App.vue:55–58) — тест-подстановки §4.2 зеленые.
- **CSS мокапа**: styles.css страницы сверена программно с inline-style
  легаси instructor-apply.html@76b26d9 — ИДЕНТИЧНА (без учета
  переносов строк); статическая разметка входа равна легаси телу
  1:1 (программная сверка).

### 3. BUG-062 (1.1)
- frontend/instructor-choice.html: `<span class="avatar" id="avatar">—</span>`
  и правило `.avatar{width:34px;…}` удалены (дифф — ровно 2 хунка,
  медиазапросы и .user/#uname не тронуты); instructor-choice.js:
  заполнение `document.getElementById('avatar').textContent=…` удалено,
  ФИО #uname сохранено. Готовность-греп: `git grep 'id="avatar"'
  frontend/instructor-choice.html` — пусто; grep "avatar" по странице/js —
  пусто.
- Мокапы choice-instructor-a/b.html — СИНХРОННО: та же плитка «ИИ» и то
  же правило `.avatar` убраны в обоих (диффы зеркальны, прецедент
  BUG-059/060/061 соблюден).
- TC-UI-059: негативный инвариант `assert page.locator("header
  .avatar").count() == 0` добавлен в секцию /instructor-choice
  (test_ui_playwright.py:4654–4656), остальное тело сценария не тронуто;
  BUG-061-инвариант (right_gap<40) на месте. Остаточные `.avatar` в
  frontend/ — вне решения по design (cabinet декор-круг ассистента,
  instructors.html легаси, instructor-dashboard/stub инструкторский
  контур, /review Vue С11 — инициалы ученика, задокументированное
  отклонение; vue/index.html+landing — декор «Гига ГАИшник»).

### 4. NFR-27: границы правок тестов
- `git diff 76b26d9..2563258 -- tests/web/test_ui_playwright.py` — РОВНО
  два разрешенных блока: (а) test_s4_pages_tag_balance +2 входа
  `vue/index.html`, `vue/instructor-apply.html` (прецедент
  vue/review-form.html С11); (б) негативный инвариант BUG-062 в
  TC-UI-059. Селекторы/маршруты/ожидания сценариев не тронуты. Свежий
  прогон design-guard: **6 passed** (включая оба новых входа).
- Переводы носителей — только источники чтения + задокументированные
  эквиваленты: test_login_modal.py (INDEX→vue/index.html;
  vue_landing_source = вход+App.vue+shared/api.js+оба модальных
  компонента; снят только `err.textContent=` — заменен ассертами
  `loginError.value=…`/`regError.value=…`/`{{ error }}`/id-якоря — все
  присутствуют в App.vue/RegisterModal/LoginModal; MIN-3 покрыт
  конструкцией носителя); test_bug001.py (три фрагмента дословны —
  postJSON('/api/register', setToken(res.data.token),
  location.href='/cabinet' найдены в App.vue:107–112);
  test_policy.py (подстановки `:disabled="!regConsent"` и
  `consent:document.getElementById('reg-consent').checked` — в
  RegisterModal.vue:37 и App.vue:105; `fd.append('consent'` дословно);
  test_instructor_pages.py §4.2 (5 тестов: page()→вход, CSS→styles.css,
  подстановки plateDisabled/noticeShow/opacity — все в App.vue;
  `sessionStorage`-ассерт зелен). Контракты/тексты не ослаблены.
- «БЕЗ ПРАВОК»-потребители: test_static.py + test_auth_route.py — свежий
  прогон **20 passed** (GET / отдаёт dist-вход с брендом и
  `/vue/assets/index-…`; /instructors/apply — 200 text/html).

### 5. Легаси удалены целиком
- `git ls-tree 2563258` — frontend/index.html, frontend/js/landing.js,
  frontend/instructor-apply.html, frontend/js/apply.js ОТСУТСТВУЮТ
  (дифф: −115 apply.js, −82 landing.js, −99 index.html,
  instructor-apply.html перенесен в vue/ вход).
- Греп остаточных ссылок по backend/frontend/tests/scripts: только
  разрешенные носители (docstring backend/app.py:4,6-инструкции маршрутов,
  исторические docstring тестов, комментарии instructors.js:29,
  новые пути vue-носителей) + НАЙДЕННОЕ minor в
  scripts/check_hero_overlap.py (таблица замечаний).

### 6. Бюджеты/сборка (5.1 воспроизведен)
- Свежие `npm run build` + `npm run check:budgets` на HEAD:
  **ОК — 5 страниц**, первые заходы instructors-rejected 28.7 /
  instructors-pending 29.6 / index 30.2 / review-form 30.8 /
  instructor-apply 32.7 КБ gzip (≤200); vendor: modulepreload-polyfill
  0.4, vue 4.0 КБ gzip (≤150); чужих page-чанков нет. Совпадает с
  отчетом 5.1 (28.7–32.7). dist собирается одной командой из всех
  входов — Dockerfile/CI правок не требуют (не тронуты — подтверждено
  списком файлов диффа).
- Rolldown-наблюдение — см. «Наблюдения».

### 7. Vue-качество
- Shared-компоненты: LoginModal/RegisterModal — разметка 1:1 со
  статической (дословный перенос, id-якоря дословно); wiring — ТОЛЬКО в
  App.vue лендинга (без дублей в компонентах); вынос wiring в
  shared-композабл отложен до второго потребителя (design, консолидация
  на живом потребителе). src/shared/api.js и utils.js — не тронуты
  (наследованы С11).
- XSS-гарды: v-html/innerHTML/dangerously — НЕТ в src (grep пуст);
  ошибки/notice/имя файла — интерполяция {{ }} (экранирование Vue),
  эквивалент textContent легаси; миниатюра — :src objectURL локального
  файла.
- sessionStorage-ключи согласованы: session_token — общий
  shared/api.js; instructor_rejected_reason — посимвольно одинаковый
  setItem ДО редиректа в Vue и легаси-дубле; open_login/open_login_from
  — только снятие при закрытии (≡легаси); на анкете sessionStorage нет.

### 8. Прочее
- backend/app.py: только две записи карты `_PAGE_ROUTES`
  (`"/": "vue:index.html"`, `"/instructors/apply": "vue:instructor-apply.html"`)
  с комментариями; цикл отдачи `vue:`/статика /vue/assets/
  _PAGE_REDIRECTS/пилотный хендлер — не тронуты (дифф = карта).
- vite.config.mjs: +2 входа (index/instructor-apply), manualChunks/base —
  без изменений; check-budgets.mjs: PAGES+2, бюджеты не менялись.
- Новых npm-зависимостей нет (package.json вне диффа); SPA/vue-router/
  pinia не введены (ОВ-3/FR-84) — main.js обеих страниц: createApp().mount('#app').
- tasks.md: 8/8 задач [x]; коммиты соответствуют волнам (1.1 / 2.1 /
  3.1 / 3.2 / 4.1+4.2+переводы / 5.1 / 6.1).
- Валидации: `openspec validate add-vue-s12-landing-apply --strict` —
  valid; `openspec validate --all --strict` — **21 passed, 0 failed**.

## Что НЕ проверено (и почему)

- **Браузерная часть Playwright-набора локально НЕ воспроизведена**:
  на машине ревью Chromium не стартует — отсутствие системной библиотеки
  `libatk-1.0.so.0` (ldconfig: 0 вхождений), прав нет (sudo требует
  пароль; apt недоступен). Прогон `pytest tests/web/test_ui_playwright.py`
  дает 7 passed / 60 ERROR — все 60 ERROR это TargetClosedError на
  BrowserType.launch (среда), не ассерты; collect = 67 тестов (совпадает
  с заявленным 6.1). Не-браузерная часть (design-guard) — зеленая локально.
  Браузерные сценарии принимаются по факту прогонов dev-делегации 6.1
  (коммит 2563258: полный e2e 67 passed, кабинет+интеграция+unit 36
  passed, NFR-001 изолированно passed) + компенсирующая статическая
  верификация ревьюера: побайтовая идентичность разметки/стилей обеих
  страниц, дословность wiring-контрактов, зеленые носители-тесты.
  Рекомендация ПМ: при наличии стенда с браузерами прогнать
  `pytest tests/web/test_ui_playwright.py` еще раз на merge-коммите
  (регламента не требует — гейт 6.1 задокументирован dev-прогоном).

## Проверенные Scenario (сверка по спекам дельты)

- Frontend «Лендинг ученика на Vue (/)»: отдача каркасом (GET / →
  dist-вход, тест зелен); route/reason с rejected-ДО-редиректа (код +
  тест); регистрация FR-78 (:disabled-гейт + consent в payload, тесты);
  семантика модалок BUG-055/056 (код 1:1 + docstring-якоря); заглушки
  alert дословно; визуальная эквивалентность — побайтовая сверка
  разметки и CSS.
- Frontend «Анкета инструктора на Vue (/instructors/apply)»: отдача
  (test_auth_route зелен); контракт 200+токены до редиректа (код 1:1);
  согласие 422 → notice (код 1:1); файловые ошибки у поля ВУ (код 1:1 +
  тест-ассерты); визуальная эквивалентность — побайтовая сверка.
- student-instructor-choice «Шапка без плитки-аватара (BUG-062)»: плитка
  и правило удалены (грепы пусты); ФИО+«Выйти» не пострадали (дифф —
  только 2 точки); мокапы синхронны (зеркальные диффы); негативный
  инвариант в TC-UI-059 добавлен (инвариант BrowserType-зависим —
  принят по прогону 6.1, см. «НЕ проверено»).

## Итог

- blocker: 0; major: 0; minor: 1 (scripts/check_hero_overlap.py —
  вне ворот партии, рекомендация в таблице).
- Вердикт: **approve** — партия к приемке; Rolldown-наблюдение и
  недоступность локального браузерного прогона зафиксировать в приемке.
