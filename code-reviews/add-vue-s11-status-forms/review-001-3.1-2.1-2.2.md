<!-- reviewer: code_reviewer (независимая сессия, SELF_REVIEW-защита) | дифф: 0eda9e2..bf9367c (19 файлов, +693/−345; задачи 1.1, 2.1, 2.2, 3.1+3.2, 4.1, 5.1) | дерево: wt-s11-vue, ветка feat/s11-vue-status-forms, HEAD bf9367c | дата: 2026-11-07 -->

# Code review: задачи 1.1–5.1 (change add-vue-s11-status-forms)

Дифф `0eda9e2..bf9367c` — реализация пакета целиком: входы
frontend/vue/{instructors-rejected,review-form}.html, страницы
src/pages/{instructor-rejected,review-form}/, src/shared/utils.js,
vite.config.mjs (+2 входа), check-budgets.mjs (3 page-чанка),
backend/app.py (vue:-маркер в `_PAGE_ROUTES` + цикл отдачи из
VUE_DIST_DIR), удаление 4 легаси-файлов, перевод тестов-потребителей.
Ревью по трем кругам: (1) контрактная точность — сверка 1:1 с удаленными
legacy-носителями (`git show 0eda9e2:frontend/review-form.html`,
`frontend/js/review-form.js`, `frontend/instructor-rejected.html`,
`frontend/js/instructor-rejected.js`); (2) NFR-27 границы (дифф
test_ui_playwright.py, needle TC-S3BE-041); (3) сборка/бюджеты/роуты
прогоном. Архив review-001-architecture (approve-with-notes, MIN-1/MIN-2)
и ADR-008 приняты как рамка.

Проверка исполнением (ревьюером, свежий вывод этой сессии):

- `npm run build` — green (6 чанков; оба входа в dist). `npm run
  check:budgets` — OK на ТРЕХ страницах: vue=24.1 КБ gzip (vendor ≤150),
  первые заходы 25.6/27.1/28.3 КБ gzip (≤200), чужих page-чанков нет;
  shared/utils.js лег в `shared`-чанк 0.6 КБ gzip — vendor-зависимости не
  создал; package.json не менялся (deps: только vue, diff 0 строк).
- `pytest tests/api/test_s3_backend.py::test_s4_pages_wired_to_real_api_shapes
  tests/api/test_s3_backend.py::test_s4_static_route_review
  tests/web/test_instructor_pages.py
  tests/api/test_auth_route.py::test_new_static_routes_served` — **16
  passed** (TC-S3BE-040/041, переведенный test_rejected_page_exists_
  and_reason_wiring, отдача обоих маршрутов из dist).
- `pytest tests/web/test_ui_playwright.py::test_s4_pages_tag_balance` —
  **4 passed** (включая vue/review-form.html).
- `openspec validate add-vue-s11-status-forms --strict` — Change is valid.
- NFR-27 дифф: `git diff 0eda9e2..bf9367c -- tests/web/test_ui_playwright.py`
  — ровно ДВА переноса источника чтения (:1221 TC-UI-019, :4424 NIT-4),
  утверждения дословны; сценарии/селекторы/ожидания не тронуты.
- Грепы по новым исходникам: innerHTML/insertAdjacentHTML/eval/v-html —
  0 вхождений (все пользовательские строки — интерполяция {{ }}; v-html
  запрещен и не используется); остаточные ссылки на 4 легаси-файла —
  только комментарии/docstring/исторические носители (test_login_modal.py:111
  — docstring, допущен MIN-1 arch-review); ключ sessionStorage
  «instructor_rejected_reason» согласован по всем носителям (пишут
  landing.js:70 и instructors.js:46 вне диффа, читают
  instructor-rejected/App.vue:34 и пилот).
- Контракты сверены с legacy: rejected — причина из sessionStorage в
  onMounted, try/catch, ноль запросов (App.vue импортирует только vue;
  api-клиент не подключается); status при загрузке не проверяется;
  прямой вход — нейтральный экран. review — ?instructor= → числовой id,
  0/нет → location.href='/my-requests' (301 в кабинет не тронут),
  нет токена → toLogin, GET /api/auth/me + GET контекста + POST с
  реакциями 401→toLogin / 200→done+тост / 409→done «уже отправлен»+кнопка
  активна / прочие (403/422/network)→тост — порядок и тексты дословны;
  DOM-якоря и .star[data-v] на месте; back-ссылка href="/my-requests" во
  входе (frontend/vue/review-form.html:66). Роуты: `vue:`-маркер →
  VUE_DIST_DIR, 404 без dist, media_type text/html; charset=utf-8; пилотный
  хендлер /instructors/pending вне карты не тронут; _PAGE_REDIRECTS и
  /api/* без изменений; CI/Dockerfile/compose/nginx не тронуты (19 файлов
  диффа это подтверждают).

## Вердикт: return

Reviewer-Delegation: deleg-s11-dev1-external

## Замечания

| # | Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|---|
| 1 | **MAJ** | frontend/vue/src/pages/review-form/App.vue:186 (код) vs :23 (комментарий); tests/api/test_s3_backend.py:1749–1750 | Носитель needle TC-S3BE-041 стал ВАКУУМНЫМ: assert ищет `instructors/'+instructorId+'/reviews` во «вход + App.vue», и строка встречается ТОЛЬКО в шапке-комментарии App.vue:23, цитирующей сам needle. Фактический код (App.vue:186) пишет URL с пробелами — `'/api/student/instructors/' + instructorId + '/reviews'` — и needle дословно НЕ содержит (legacy js/review-form.js:83 был без пробелов и матчился кодом). Гард деградировал: перевод строки 186 на template literal тест НЕ заметит (комментарий продолжит матчиться). Это противоречит design.md «Страница /review на Vue» (needle проверяется дословно по носителю; template literals НЕ вводить — MIN-2 arch-review) и готовности 3.1 «needle POST-URL дословно»; docstring теста (:1723–1726) при этом утверждает, что конкатенация сохранена «в Vue-коде» — проверкой это больше не подтверждается. Тест зелен, но защищает не то, для чего создан. | Вернуть байт-паритет с legacy: убрать пробелы вокруг `+` в обеих конкатенациях App.vue (186: POST `/reviews`, 221: GET контекста) — `'/api/student/instructors/'+instructorId+'/reviews'` — тогда needle снова матчится кодом, а не комментарием. Правка 2 строки, e2e-поведения не меняет (формат провода тот же); после правки — повторное ревью (NNN+1) точечно по носителю needle. |
| 2 | MIN | frontend/vue/src/pages/review-form/App.vue:69, :108, :184, :197, :200 | Недокументированное микроотклонение от 1:1 wiring: флаг `sending` держит #send выключенным весь полет POST, тогда как legacy на input во время запроса ПЕРЕвключал кнопку через validate() (и безусловно включал на 409/ошибке даже если поля сделали невалидными в полете). Поведение Vue защитное (исключает двойной сабмит) и TC-UI-017 зелен, но строго это не 1:1 — а comment App.vue:184 заявляет «как legacy btn.disabled=true», описывая только половину отличия. | Задокументировать отклонение в комментарии у `sending` (одна строка: «в отличие от legacy кнопка остается выключенной до ответа — защита от двойного сабмита») ИЛИ убрать флаг ради строгого 1:1. Не блокирует; можно совместить с правкой MAJ-1. |

Не является замечанием (соответствует контракту/решениям):

- **Rejected-страница (2.1)** — полный эквивалент legacy: разметка входа
  посимвольно повторяет удаленный instructor-rejected.html (включая
  предгидрационный style="display:none" на #reason-block), поведение
  js/instructor-rejected.js 1:1 в onMounted (ключ, try/catch, ноль
  запросов — api.js не импортируется), v-show="reason" как эквивалент
  стекового фрагмента «style.display = ''» (перевод разрешен формулировкой
  3.1, тест :308–312 это и проверяет).
- **check-budgets.mjs** — рефакторинг корректный: PAGES-карта, замыкание
  по каждой странице, чек (в) чинит и старую косвенность (сравнивал с
  захардкоженным 'instructors-pending'), бюджеты не ослаблены.
- **backend/app.py** — `vue:`-механика минимальна и следует паттерну
  пилота; карта остается единственным реестром; порядок регистрации
  (пилот до цикла карты) не создает теневых совпадений (маршрут
  /instructors/pending в карте отсутствует).
- **Удаление легаси (3.1)** — все 4 файла отсутствуют в дереве
  (instructor-rejected.html учтен git-детектом как R067 в styles.css);
  10 остальных монолитов не тронуты.
- **Тексты/стили/заголовки** — дословный перенос, редизайна нет;
  done-состояние без деталей своего отзыва — наследованное задокументированное
  отклонение от мокапа.

## Проверено / не проверено

Проверено прогоном в этой сессии: сборка, бюджеты (3 страницы), openspec
strict, TC-S3BE-040/041, test_instructor_pages (весь файл),
test_auth_route::test_new_static_routes_served, NIT-4 tag-balance,
статическая часть TC-UI-019 (href="/my-requests" во входе), дифф-границы
NFR-27, грепы XSS/легаси-ссылок/ключей.

Не проверено (ограничение среды ревью, не кода): браузерные e2e
TC-UI-017/018, TC-S9UI-003, поведенческая часть TC-UI-019 — chromium
headless-shell в среде ревью не стартует (нет системных библиотек
libatk-1.0.so.0, sudo недоступен); принят отчет 5.1 (коммит bf9367c,
e2e 63 passed) + статическая верификация якорей выше. После правки MAJ-1
повторный прогон затронутых якорей обязателен на стороне dev (стандартный
контур 5.1).

## Итог

- MAJ-1: needle TC-S3BE-041 матчится комментарием, не кодом (App.vue:186
  vs :23) — гард контракта вакуумный. Fix: байт-паритет конкатенации с
  legacy (убрать пробелы вокруг `+`, строки 186 и 221).
- MIN-1: недокументированное отклонение `sending` от 1:1 (App.vue:184 и
  контекст) — задокументировать или убрать.
- Вердикт: **return** — dev-партия качественная и по сути готова
  (единственный блокер — 2-строчный), но ворота контракта TC-S3BE-041
  обязаны оставаться действующими до merge; повторное ревью — точечное
  (носитель needle + комментарий MIN), история append-only.

## Постскриптум (ПМ, 2026-11-07)

Вердикт review-001: return по MAJ-1/MIN-1; находки устранены коммитом 3c3d47d и подтверждены ре-ревью review-002 (approve). Итоговое решение по кейсам TC-S11UI-001…009: к автоматизации и приемке партии — одобрить.
