<!-- Reviewer-Delegation: deleg-s15-dev1-external | независимый код-ревьюер (не автор диффа) | дифф: 3bec170..cd218ac (7 коммитов) | ветка: feat/s15-final-migration | дата: 2026-11-13 -->

# Code review: ФИНАЛЬНАЯ партия add-vue-s15-final-migration — задачи 1.1, 2.1, 2.2, 3.1, 4.1, 4.2, 5.1 (+критерии 6.1/7.1)

Периметр: весь dev-дифф 3bec170..cd218ac (43 файла, +3083/−2246): каркас 6 входов
(1.1), admin-login/admin-dashboard (2.1/2.2), registered/policy (3.1),
instructor-choice/cabinet (4.1/4.2), фикс-коммит cd218ac (реактивный порт cabinet +
весь объем 5.1: переключение 6 маршрутов, удаление легаси-HTML и каталога js/,
снятие хендлера /js/{path}, переводы носителей тестов). Контекст: design.md пакета
(волны, «Границы правок тестов»), review-001-architecture.md (approve-with-notes,
карта обновлена), ADR-008. BUG-063 (48bd504, волна 3 s13) — в ветке ДО базы ревью;
проверен на сохранность семантики (ниже).

## Вердикт: approve

Все задачи партии приняты. MAJ нет. Два MIN — букинг/докстроки, поведение и
ворота партии не затрагивают. Каждый пункт приоритетов проверен по коду И
прогонами на HEAD (см. «Прогоны ревьюера»).

## 1. Фикс cabinet (cd218ac) — реактивный порт сверен построчно

- Корень бага подтвержден диффом: в 4.2 openBookModal/retryBooking и их
  зависимости жили в onMounted-замыкании, а return setup ссылался на эти
  имена (ReferenceError при setup → пустой setupState → TypeError length в
  шаблоне и биндинги по null). Латентный же класс: retry (setup) звал
  localApi/handleAuthFail/loadRequests из onMounted.
- После фикса: все вызываемые шаблоном имена (viewReqs, reqStatus,
  initialsOf, carText, goReview, retry, bookingsList, gridHead, gridRows,
  bkStatus, bookingTitle, bkCarText, openBookModal, retryBooking, fmtDate)
  объявлены в setup-области; onMounted — только bootstrap (токен,
  /api/auth/me, слушатели, стартовые загрузки). Каждый
  getElementById/querySelector из onMounted сверен с шаблоном App.vue —
  целей-призраков нет.
- Дубль #toast снят: элемент ровно один, в шелле (vue/cabinet.html:198, вне
  #app); в App.vue элемента .toast нет — прецедент review-form С11 сверен
  (там toast тоже только в шелле; документы/дашборд-инструктора С14 с
  toast внутри App.vue — исторический рантайм, партию не касается).
- Незакрытый #app в vue/cabinet.html и vue/instructor-choice.html закрыт
  (+по одному </div>, дифф cd218ac); test_s4_pages_tag_balance по всем 12
  входам и scripts/check_tag_balance.py (7 файлов) — зеленые.
- CSS-якорь TC-UI-014 (.badge.wait) — вербатим в App.vue (строка 253) при
  живом вербатиме в styles.css:32 — идемпотентная анкора под носитель
  design-guard'а «вход+App.vue» (тот же селектор/свойства; CSS глобален —
  дубля визуального нет). test_admin_dashboard_bug046_mock_sync_fragments —
  зелен на HEAD.
- Инварианты: TC-UI-059/060 якоря на месте (.side-brand в разметке,
  «В КАБИНЕТЕ» — 0 вхождений во входе и App.vue); хеш-навигация navTo с
  wantHash/replaceState и стартовыми #/my-requests, #/my-bookings — 1:1;
  токены — session_token/X-Session-Token, admin_token/X-Admin-Token — как
  legacy. Попутно необходимая правка носителя TC-MOD-002: комментарий
  App.vue админки содержал литерал «password_hash», который тест ищет как
  ЗАПРЕЩЕННУЮ строку в носителе — заменен на «хэш пароля» (без этой правки
  test_qa_instructor_flow был бы красным; инвариант не ослаблен).

## 2. Превентивная проверка остальных 5 страниц — паттерн не повторяется

- admin-dashboard: шаблон БЕЗ интерполяций — только @click-бриджи
  (showSection/exportCsv/soon/adminLogout), все четверо объявлены в setup;
  реализации в onMounted подсаживаются в bridge В КОНЦЕ монтирования —
  бриджи вызываются только кликами (после монтирования), References-дыры
  нет. admin-login/registered/policy — вся логика в setup (doLogin,
  stubCabinet, showError/paras), onMounted только fetch-bootstrap; все
  возвращенные имена определены. instructor-choice: все 13 id, которых
  касается onMounted (uname, f-trans/f-exp/f-day, f-rating, rating-val,
  f-from/f-to, sort, reset, empty-reset, logout), есть в шаблоне App.vue;
  имена из return — в setup-области.
- getElementById-цели, отсутствующие в DOM, не найдены ни на одной из 6
  страниц (grep + ревью каждого onMounted против своего шаблона).

## 3. NFR-27: дифф test_ui_playwright.py — РОВНО разрешенное

git diff 3bec170..HEAD -- tests/web/test_ui_playwright.py содержит только
четыре разрешенные design-guard точки + комментарии: (а) BUG-046-носитель —
page_html = вход + App.vue; (б) TC-UI-007 — helper _serve_frontend удален,
перехват снят, страница читается живым маршрутом; (в) TC-UI-019 — носители
cab/choice = входы + App.vue («BUG-047 чтение dash» отдельных правок не
потребовало: dash читает vue-носители с С14, в диффе — контекст без правок);
(г) tag-balance −2 легаси / +6 входов (итого 12: 8 прежних vue + 4 новых
партии… точно: +cabinet, +instructor-choice к прежним, +admin-login,
+admin-dashboard, +registered, +policy). Селекторы, маршруты, ожидания и
логика сценариев — не тронуты (сверено по всем хункам). Переводы носителей в
test_cabinet_page (CABINET→вход; cabinet_source = вход+App.vue+utils; CSS —
styles.css построчно; MOCKUP не тронут), test_integration_sprint1
(byte-equality → признак входа «200 + /vue/assets/», прецедент пилота
MAJ-1), test_policy ('/js/policy.js' → '/vue/assets/'; id-якоря и
grep-контроль текста — без правок), test_qa_instructor_flow (носитель UI =
вход + App.vue), test_s3_backend (needles «api/student/requests»,
«instructor_id:r.instructor_id» — ДОСЛОВНЫ) — по design, ослаблений нет.

## 4. Легаси/сироты

- ls frontend/ → только vue/; 6 легаси-HTML и каталог js/ (7 модулей)
  удалены тем же коммитом, что и переключение карты (атомарность 5.1
  соблюдена).
- backend/app.py: хендлер GET /js/{filepath:path} удален (в файле остались
  только комментарии-история); /vue/assets не тронут; _PAGE_REDIRECTS и
  пилотный /instructors/pending — без изменений; все 13 значений
  _PAGE_ROUTES — «vue:», каждое указывает на существующий вход dist
  (сверено со сборкой), фантомных /booking, /instructor/bookings,
  /admin/cars, /admin/documents нет — 404-сирот в карте нет.
- CI (flow.yml) и Dockerfile функциональных ссылок на /js не содержат.
- Остаточные упоминания frontend/js и /js/ вне исторических носителей —
  ТОЛЬКО комментарии/docstring-и (см. MIN-2); функциональных ссылок
  (script-src, чтение файлов, маршруты, носители тестов) — ноль.

## 5. BUG-063 (48bd504) — семантика s5/s7 не задета

Коммит волны 3 — предок базы ревью (3bec170); дифф партии s5/s7-тесты не
трогает (git diff 3bec170..HEAD -- tests/api/test_s5_backend.py
test_s7_backend.py пуст). Сверка критерия на HEAD: one_off —
d1=today+1/d2=today+2 с weekday=d.weekday() (test_s5:176–182,
test_s7:212–218); future_date = (weekday − today.weekday()) % 7, `or 7` —
строго будущая (test_s5:209–214, test_s7:191–196). Детерминизм сохранен.

## 6. Бюджеты NFR-26 (6.1)

npm ci-стенд ревьюера: npm run build — OK, 14 входов; npm run
check:budgets — OK «страниц: 14»; gzip-замеры page-чанков (CLI `gzip -c |
wc -c`): cabinet 8.5 КБ, admin-dashboard 9.4 КБ, instructor-choice 3.9 КБ,
admin-login 0.9 КБ, registered 0.9 КБ, policy 0.9 КБ (прочие 1.0–22.6 КБ);
JS первого захода: максимум 50.7 КБ gzip (instructor-dashboard), cabinet
37.2 КБ, admin-dashboard 38.0 КБ — бюджеты ≤200/≤150 КБ с запасом; чужих
page-чанков в замыканиях нет. Пороги не менялись.

## 7. Качество Vue

- Консистентность: все 6 страниц — один паттерн (вход-разметка + main.js +
  App.vue с плоским JS и реактивными списками; заголовки-комментарии
  унифицированы; «Разметку держать синхронной с App.vue» соблюдена — тела
  разметки входов сверены с легаси диффом: у 5 из 6 расхождение — только
  шапка-комментарий партии; см. Obs-2 по cabinet).
- XSS: v-html нет нигде в партии; интерполяции = текстовые узлы;
  innerHTML-свертки admin (verdict-блоки, miss.join) — построчно 1:1 с
  легаси admin-dashboard.js (не новый вектор); таблица users —
  textContent-only (унаследованный фикс XSS).
- Ключи/токены: session_token/admin_token, X-Session-Token/X-Admin-Token —
  дословно; sessionStorage-контракты не тронуты.
- Стили/хелперы: fioOf/fmtDate — дословный перенос из js/shared/utils.js
  (сверено диффом); подтверждения confirm('Одобрить заявку?…'), 409-тосты,
  sent-кэш без кэширования 409 — как в legacy/review-001 #14.

## Прогоны ревьюера (HEAD cd218ac, чистое дерево)

- npm run build — OK (14 входов); check:budgets — OK (замеры в §6).
- pytest tests/ без браузерного файла — **387 passed** (включая все
  носители: test_cabinet_page 7, test_static 10, integration_sprint1+
  policy+qa_instructor_flow 50, s3_backend+tag-balance 55 и весь
  API-регресс; BUG-063-набор s5/s7 внутри — зелен).
- pytest tests/web/test_ui_playwright.py — **13 passed** (все
  design-guard'ы файла: BUG-046-фрагменты + tag-balance ×12), **60 ERROR
  на fixture browser**: в стенде ревью нет системных библиотек Chromium
  (libatk-1.0.so.0; sudo недоступен) — браузерная часть в этой среде
  невоспроизводима. Утверждение dev «e2e 73 passed» — из сообщения
  cd218ac; независимо НЕ воспроизведено (Obs-1), противоречий статике не
  найдено: все статические якоря браузерных сценариев сверены в коде (§1–2,
  §7).
- scripts/check_tag_balance.py — 7 файлов OK; openspec validate
  add-vue-s15-final-migration --strict — valid.

## Замечания

| Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|
| minor | openspec/changes/add-vue-s15-final-migration/tasks.md:168,202,214 | Букинг партии: 5.1/6.1/7.1 остаются «[ ]», хотя содержимое 5.1 доставлено (в cd218ac), а критерии 6.1 (бюджеты) и 7.1 (validate; не-браузерный pytest; design-guard'ы) воспроизведены зелеными на HEAD. Кроме того, весь атомарный объем 5.1 (карта+удаления+носители) коммитится под заголовком «dev (fix): cabinet App.vue» — правило партии «коммит после КАЖДОЙ задачи» для 5.1 собственной коммит-записи не получило (само требование атомарности 5.1 одним коммитом соблюдено). На код и ворота не влияет — трассируемость приемки. | Отметить 5.1/6.1/7.1 в tasks.md по факту гейта (после браузерного e2e на стенде dev) и в следующем коммите упомянуть объем 5.1; код не трогать. |
| minor | frontend/vue/src/shared/api.js:4; frontend/vue/src/shared/utils.js:5; frontend/vue/src/pages/instructor-pending/App.vue:36; frontend/vue/src/pages/review-form/App.vue:90; tests/conftest.py:44 (docstring) | Устаревшие комментарии о frontend/js в ЖИВЫХ носителях: «немигрированные монолиты продолжают читать frontend/js/api.js», «frontend/js/*.js НЕ трогаются» и ссылки на js/apply.js, js/api.js — после удаления каталога это ложные утверждения. Критерий готовности 5.1 «git grep "frontend/js\|/js/" frontend backend tests scripts — пусто (кроме исторических sdd.md/code-reviews/test-model)» буквой не выполнен именно из-за этих комментариев (функциональная чистота — полная: ссылок нет, §4). | Докстрочная чистка в следующей docs-партии (право правки комментариев живых носителей не требует переноса гвардов — строки-носители фрагментов не затрагивает); исторические sdd/reviews не трогать. |

## Наблюдения (не замечания)

- **Obs-1 — браузерный e2e не воспроизведен в стенде ревью**: 60
  сценариев test_ui_playwright требуют Chromium (libatk отсутствует,
  привилегий на установку нет). Все 13 не-браузерных тестов файла и
  статические якоря браузерных сценариев — зеленые/сверены; расхождений с
  заявлением dev (73 passed) не обнаружено.
- **Obs-2 — cabinet #bk-grid**: легаси держал сетку пустой до JS
  (уголок «время» создавался рендером), Vue-вход/App.vue держат уголок
  статично — задокументировано в шапке App.vue; отличие только в
  ДО-гидратационном DOM, вид/поведение после гидрации эквивалентны,
  вербатим-тесты мокапа зеленые.
- **Obs-3 — scripts/check_tag_balance.py:14**: опечатка в комментарии
  («носителиdesign-guard'ов» — пропущен пробел). Тривия, рядом с MIN-2.
- **Obs-4 — .badge.wait дублируется** (styles.css:32 + App.vue:253) —
  осознанная идемпотентная анкора под носитель «вход+App.vue» (§1);
  срабатывать сработает один раз стилем, конфликта свойств нет.
- **Obs-5 — BUG-063** (48bd504) вне диффа; сверка семантики s5/s7 — §5,
  зелен в общем прогоне.

## Итог

- **Вердикт: approve.** MAJ нет; MIN-1 (букинг tasks/коммит-заголовок 5.1),
  MIN-2 (устаревшие докстроки о frontend/js) — вне кода поведения, ворота
  NFR-26/NFR-27/ADR-008 соблюдены и воспроизведены.
- Соответствие arch-review-001: все три MIN архитектора отработаны (счет
  карты 13 «vue:»; api.js — тела дословны, легаси-копия удалена; Obs-1
  TC-UI-007 реализован выбранным архитектором способом — живой маршрут).
- Остаточное для гейта вне кода: браузерный полный e2e на стенде dev
  (заявлен зеленым в cd218ac), тик 5.1–7.1 в tasks.md, regress-final PASS с
  impact-анализом — предметы финальной волны 7.1, не этого ревью.
