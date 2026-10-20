# Code Review — BUG-047, задача 2 (разделы внутри кабинетов)

- МЕТА: Reviewer-Delegation: deleg_spawn20261020155018e1dbc0 — spawned hermes chat session (role=code_reviewer, BUG-047)
- Ревьюируемый коммит: b6393e20335860d2576d313861745c70fd2cc501 (HEAD, дерево чистое)
- Файлы: frontend/instructor-dashboard.html, frontend/cabinet.html, frontend/review-form.html, frontend/instructor-choice.html, frontend/my-cars.html (удален), frontend/my-requests.html (удален), backend/app.py, tests/test_ui_playwright.py, tests/test_s3_backend.py

## Вердикт: **APPROVE**

Регресс: `.venv/bin/python -m pytest tests/ -q` → **274 passed, 1 warning in 268.95s** (свежий прогон ревьюером, LD_LIBRARY_PATH pw-libs). Замечаний blocker/major нет; 2 minor + 2 наблюдения — не блокируют.

## Замечания

| # | Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|---|
| 1 | minor | frontend/instructor-dashboard.html:110 (новый глобальный `.car`) против :28 (`.w-stu .car`) и JS :464 | Заявленный в комментарии «коллизий со стилями дашборда нет» неточен: бейдж авто в виджете «Мои ученики» (`node('span','car',…)` внутри `.w-stu`) теперь матчится и с перенесенным глобальным `.car{…}`. Скоуп-правило `.w-stu .car` перебивает общие свойства (border/background/padding/radius/margin), но НЕ display:flex, flex-direction:column, min-width:0, inset box-shadow, transition — бейдж стал flex-контейнером с внутренней тенью. Визуальный эффект почти незаметен, но это реальная коллизия имен, а не «1в1». | Переименовать класс карточки в перенесенном блоке (`.car` → `.car-card`) или скоупить перенесенные стили под `#sec-cars`. |
| 2 | minor | frontend/review-form.html:129 | Кнопка «Назад к заявкам» ведет на `/my-requests`, т.е. через собственный 301 → `/cabinet#/my-requests`. Работает (редирект сохранен сознательно), но лишний hop и зависимость от редиректа там, где целевой адрес известен. | Прямая ссылка `href="/cabinet#/my-requests"`. |

### Наблюдения (вне вердикта)

- tests/test_ui_playwright.py TC-UI-019 — проверка навигации по разметке файлов (не браузер), но это заявлено в docstring и продолжение прецедента a47a421; поведенческая сторона покрыта двумя новыми e2e-редиректами (см. ниже). Не вакуумные.
- frontend/cabinet.html:72 `.hero{min-height:auto}` — переопределение вычисленного стиля мокапа без правки его строк; design-guard (test_cabinet_page.py) проходит, соответствует решению Заказчика о едином лейауте.

## Проверено (Scenario)

1. **Сайдбар в обоих кабинетах, активный пункт** — инструктор: `.nav button[data-tab="Мои автомобили"]` подсвечивается классом `active` (navTo, :462-реестр табов + `#sec-cars`), хеш `#/my-cars` открывает раздел и переживает reload (replaceState, :1003). Ученик: `.snav` «Главная»/«Мои заявки»/«Выбрать инструктора» (cabinet.html:187-191), класс `on`, хеш `#/my-requests`, `#sec-home` скрывается. Покрыто e2e test_bug047_mycars_route_redirects_into_dashboard, test_bug047_myrequests_route_redirects_into_cabinet, TC-UI-015/017.
2. **JS не задублирован, конфликтов нет** — id: дубликатов нет ни в одном из 4 HTML (uniq -d пуст; перенесенные id count/cars/m-add/f-*/m-del/… в старом дашборде отсутствовали). Глобальные имена дашборда: перенос с префиксом `mc*` (mcCars/mcRender/mcUploadPhoto/…), существующие el/node/apiGet/apiSend/token/toast переиспользуются, сигнатуры сверены (node → textContent). cabinet: новый код внутри существующего IIFE, `api/toast/el/handleAuthFail` — единственные определения; toLogin/clearSession существуют. CSS: старый дашборд не определял ни один из перенесенных классов, кроме `.car` (см. замечание 1); `.toast` — одно определение (в диффе контекст); старый cabinet не имел ни одного из добавленных классов (совпадение `.status` — ложное, это JS `res.status,`).
3. **301-редиректы** — `_PAGE_REDIRECTS` c default-args в замыкании (нет классической ловли late-binding), RedirectResponse 301; цели `/instructor/dashboard#/my-requests`-аналоги существуют в `_PAGE_ROUTES`; петли нет (цепочка /review без id → /my-requests → 301 → /cabinet#/my-requests конечна). Статики-маунта в app.py нет — удаленные файлы недостижимы. Тесты: test_bug047_old_routes_redirect_301 (оба пути, точный Location), e2e через реальный переход.
4. **XSS перенесенного рендера** — mcRender и render() кабинета: только createElement/textContent (node/el), dataset через свойства, `a.href='/review?instructor='+id` — конкатенация в property, схему подменить нельзя; blob-превью через URL.createObjectURL; del-what/тосты через textContent. innerHTML='' только для очистки контейнеров. Регресс XSS-тестов сьюта зеленый.
5. **e2e не вакуумные** — новые TC-UI (redirect в дашборд/кабинет) — реальный браузер, реальный 301 (wait_for_url), реальные токены (_student_token/_approve_instructor), проверки видимости/класса/текста; TC-UI-015 прогоняет CRUD авто на живом бэкенде через клик по сайдбару. См. наблюдение про TC-UI-019.
6. **review-form без центрирования** — `.crumb` absolute-центрирование убрано (:90→:91), шапка flex space-between + `.hgroup`; back-ссылки из-под шапки удалены, кнопка в форме есть (замечание 2 — minor). instructor-choice: аналогично, `.back` стили добавлены.
7. **Бэкенд не задет** — `git show b6393e2 --stat`: из backend/ тронут только app.py (import RedirectResponse + таблица редиректов + регистрация), prod-логики (API, db, admin) диф не содержит. Дерево чистое, HEAD = b6393e2.

## Не проверено

- Визуальный результат в реальном браузере на-eye (только assertions Playwright); точная степень визуального эффекта замечания 1 не измерялась.
- Реальные 301 вне TestClient/Playwright-сервера (nginx/прод-прокси, сохранение фрагмента Location браузером) — вне скоупа сьюта.
- test-model/bugs/PLAN.md — не ревьюил (вне scope).
