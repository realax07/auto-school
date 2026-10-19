# Review-acceptance — add-s3-frontend-links (Спринт 4, Партия A, задача 8)

- МЕТА: Reviewer-Delegation: deleg_spawn20261016192010d00ca1f6 — spawned hermes
  chat session (role=qa_case_reviewer, приемка)
- Ревьюер: qa_case_reviewer (Флоу 1, приемочное ревью Спринта 4, Партия A)
- Дата: 2026-10-16
- Объект: рабочее дерево репозитория (изменения не закоммичены: openspec/changes/
  add-instructor-student-loop/design.md, tests/test_s3_backend.py — modified;
  code-reviews/add-s3-frontend-links/, openspec/changes/add-instructor-student-loop/
  arch-review-s4.md, test-model/reports/qa-auto-report-add-s3-frontend-links.md — untracked).
  Ветка feature/s4-links, HEAD = 8273f45 («fix(s4): итерация 2 по ревью
  add-s3-frontend-links review-001») поверх 5db9cc5 — соответствует ветке ревью.
- Вмешательство в материалы: нулевое (ничего не правлено, артефакт только этот).
- Все прогоны и проверки ниже выполнены приемочным ревьюером самостоятельно
  (не взяты из отчетов).

## Итог: REJECT

Единственное блокирующее основание — чек-лист п.3: трассировка Спринта 4 в
sdd.md НЕ дополнена (задача 8.1-аналог). Остальные пункты чек-листа — PASS.
Исправление механическое, без изменения кода: добавить в sdd.md раздел
«Трассировка (Спринт 4, Партия A)» по образцу §27 (Спринт 3) — что трассировать:
TC-UI-015…018 → tests/test_ui_playwright.py (docstring, плановая), TC-S3BE-040/041 →
tests/test_s3_backend.py (docstring, правило 6), страницы frontend/{my-cars,
review-form, my-requests}.html + маршруты backend/app.py (_PAGE_ROUTES, строки
52–54) → реализации; пограничное дополнение instructor_id в GET /api/student/requests
со ссылкой на arch-review-s4.md (ДОПУСТИТЬ, 2026-10-16) и на внесенную строку
в design.md, Блок 6. После дополнения sdd.md партия принимается по фактам ниже.

## Чек-лист приемки

### 1. Задачи Спринта 4 Партии A выполнены (PLAN.md 4.1–4.6)

**Вердикт: PASS** (с оговоркой по чекбоксам — не блокирует, см. ниже).

- Страницы по согласованным мокапам: design/mocks/{my-cars,my-requests,
  review-form}.html существуют (mtime 17:18–18:17 UTC 2026-10-16 — задача 4.1,
  выбор Заказчика); реализации frontend/{my-cars,my-requests,review-form}.html
  в рабочем дереве, входяте в коммит 5db9cc5 (итерация 1) и 8273f45 (итерация 2).
  Отклонения от мокапов (F2–F4, NIT-1) закрыты в итерации 2 design-guard-строками
  в шапках страниц — подтверждено review-002 и согласуется с кодом.
- Маршруты: backend/app.py `_PAGE_ROUTES` — /my-cars → my-cars.html (стр. 52),
  /review → review-form.html (стр. 53), /my-requests → my-requests.html (стр. 54).
- Навигационные связки: cabinet.html (плитка), instructor-dashboard.html (пункт
  нав → /my-cars), my-requests → /review?instructor= (проверено e2e TC-UI-018 и
  redirect-сценарием /review без параметра в TC-UI-017).
- e2e: TC-UI-015 (стр. 1166), TC-UI-016 (стр. 1240), TC-UI-017 (стр. 1280),
  TC-UI-018 (стр. 1340) в docstrings tests/test_ui_playwright.py — все на живом
  сервере (фикстура server, без page.route), + интеграционный test_s4_pages_
  wired_to_real_api_shapes (TC-S3BE-041) и sanity test_s4_pages_tag_balance (стр. 1454).
- instructor_id — архитектор ДОПУСТИЛ: openspec/changes/add-instructor-student-loop/
  arch-review-s4.md, вердикт «ДОПУСТИТЬ» (4 аргумента), отражение в дизайне
  внесено: design.md Блок 6, строка GET /api/student/requests дополнена пометкой
  «дополнено Спринтом 4, согласовано» (uncommitted diff рабочего дерева подтвержден).
- Оговорка: чекбоксы 4.1–4.6 в PLAN.md не отмечены ([ ]) — как и в Спринте 3
  (там это зафиксировано в acceptance как механический хвост, не блокировавший
  по отдельному чек-листу). Здесь в чек-листе приемки такого пункта нет;
  фиксирую как заметку ПМ, не основание REJECT.

### 2. Артефакты партии

**Вердикт: PASS.**

- code-reviews/add-s3-frontend-links/review-001.md — вердикт RETURN (F1 MAJOR
  блокирующий + F2–F4 MINOR + NIT-1..5), МЕТА deleg_spawn202610161846154d1e4a —
  на месте.
- code-reviews/add-s3-frontend-links/review-002.md — вердикт APPROVE, МЕТА
  deleg_spawn2026101618510128ecea — на месте. Per-finding сверен с рабочим
  деревом: F1 фиксен по существу (frontend/my-requests.html, render() строит
  список из `list`, не `reqs` — проверено чтением кода, стр. 187–190).
- test-model/reports/qa-auto-report-add-s3-frontend-links.md — на месте; независимо
  воспроизведен полный сьют (см. п.4): 270 passed — совпадает с отчетом.
- Design check — согласование мокапов Заказчиком 2026-10-16: отдельного
  standalone-артефакта не обнаружено; фактические свидетельства — мокапы в
  design/mocks/ (задача 4.1 «→ выбор Заказчика»), отработка мокапных замечаний
  в ревью-цикле (F2–F4/NIT-1 — документирование отклонений design-guard) и
  строки страниц. Отмечаю ПМ: если формат требует отдельного design-check
  артефакта — добить (не блокирует: содержательно согласование подтверждено).

### 3. sdd.md: трассировка Спринта 4 дополнена?

**Вердикт: FAIL — единственное блокирующее основание REJECT.**

- sdd.md (729 строк) заканчивается §27 «Трассировка (Спринт 3, Партия A)».
- grep по sdd.md: «Спринт 4», «add-s3-frontend-links», «TC-UI-015»…«TC-UI-018»,
  «my-cars», «Мои автомобили» — ноль вхождений.
- Чек-лист приемки прямо требует: трассировка не дополнена → REJECT
  (задача 8.1-аналог). Необходимое исправление описано в шапке вердикта.

### 4. Валидации (выполнены приемочным ревьюером)

**Вердикт: PASS.**

- `openspec validate --all --strict` → 5 passed, 0 failed (add-auth-cabinet,
  add-instructor-cabinet, add-instructor-flow, add-instructor-student-loop,
  add-registration-admin), exit 0 — воспроизведено.
- `python3 scripts/flow_check.py .` → «flow_check: OK — порядок артефактов
  соответствует флоу», exit 0; попутный FLOW-WARNING об устаревших промптах
  фабрики — это известный долг 4.B3 (Партия B), не блокирует.
- flow_check хвост в tests/test_s3_backend.py (docstring, стр. 11–18,
  uncommitted diff): исключение «TC-трассировка не ведется» уточнено —
  TC-S3BE-040/041 несут TC-ID по правилу 6, 39 backend-тестов Спринта 3
  (TC-S3BE-001…039) остаются без TC-ID, долг закрытия — за ПМ/arch-review.
  Известный долг подтвержден в заявленном объеме, не блокирует.
- Полный сьют: `LD_LIBRARY_PATH=~/.cache/pw-libs/root/usr/lib/x86_64-linux-gnu
  .venv/bin/python -m pytest tests/ -q` → **270 passed, 1 warning in 244.21s**
  — воспроизведено независимо, совпадает с QA-отчетом (257 → 270, +13 новых).

## Наблюдения (не блокируют, ПМ на усмотрение)

1. **Расхождение review-002 NIT-4 с рабочим деревом.** review-002 утверждает
   «scripts/check_tag_balance_s4.py удален», но файл существует, трекается
   (добавлен в 5db9cc5) и при запуске проходит (3 страницы OK). Существо NIT-4
   достигнуто — параметризованный test_s4_pages_tag_balance есть и работает, —
   но заявление об удалении в review-002 фактически неверно для рабочего
   дерева. Ничего не правлю (постановка); ПМ: либо удалить скрипт при коммите,
   либо принять как безвредный остаток.
2. Чекбоксы 4.1–4.6 PLAN.md не отмечены (см. п.1) — механический хвост.
3. Отдельный артефакт design check отсутствует (см. п.2).

---

# Итерация 2

- МЕТА: Reviewer-Delegation: deleg_spawn20261016192500i2qa — spawned hermes
  chat session (role=qa_case_reviewer, приемка, итерация 2)
- Ревьюер: qa_case_reviewer (Флоу 1, приемочное ревью Спринта 4, Партия A,
  повторный заход по итогам итерации 1)
- Дата: 2026-10-16
- Объект: то же рабочее дерево, HEAD = 8273f45, ветка feature/s4-links
  (не изменился с итерации 1, проверено git log/branch/status).
- Вмешательство в материалы: нулевое (ничего не правлено, артефакт только
  этот; diff рабочего дерева относительно итерации 1 — только sdd.md +44
  строки, design.md-строка из итерации 1 не менялась).
- Все прогоны и проверки ниже выполнены приемочным ревьюером самостоятельно.

## Итог: ACCEPT

Блокирующее основание итерации 1 (п.3 чек-листа — трассировка Спринта 4 в
sdd.md) устранено. Остальные пункты чек-листа итерации 1 перепроверены и
остаются в силе. Партия A принимается.

## 1. sdd.md: трассировка Спринта 4 дополнена? (было: FAIL)

**Вердикт: PASS — основание REJECT итерации 1 снято.**

- sdd.md (773 строки) дополнен разделом «SDD (дополнение): Трассировка
  (Спринт 4, Партия A)» + §28 (строки 733–773), по образцу §27 (Спринт 3),
  как и требовалось в вердикте итерации 1.
- Полнота: покрыты все 6 строк Партии A — «Мои автомобили» (CRUD + маршрут
  /my-cars + нав из instructor-dashboard), «Фото автомобиля» (multipart,
  превью, выдача по сессии владельца), «Оставить отзыв» (сабмит + 409-блок +
  маршрут /review + связка my-requests → /review?instructor=), «Мои заявки»
  (бейджи, deny_comment, «Повторить заявку» ОВ-2 + маршрут /my-requests +
  плитка из cabinet.html), пограничное дополнение instructor_id в
  GET /api/student/requests (со ссылками на arch-review-s4.md «ДОПУСТИТЬ»
  и design.md Блок 6 — обе ссылки сверены с файлами: пометка «дополнено
  Спринтом 4, согласовано» в design.md стр. 222, uncommitted diff
  подтвержден), статические маршруты _PAGE_ROUTES (строки 52–54 backend/
  app.py — сверено с кодом).
- Тесты в трассировке существуют — выборочно открыты: TC-UI-015 (docstring
  tests/test_ui_playwright.py стр. 1166), TC-UI-017 (стр. 1280), TC-UI-018
  (стр. 1340); TC-S3BE-040 (tests/test_s3_backend.py стр. 1633), TC-S3BE-041
  (стр. 1643); TC-UI-016 (стр. 1240) — по grep. Все упомянутые в таблице
  файлы существуют (frontend/{my-cars,review-form,my-requests}.html,
  design/mocks/*, backend/{app.py,instructor_cars.py,student_requests.py} —
  instructor_id в ответе my_requests подтвержден, backend/student_requests.py
  стр. 167).
- Примечание 2 раздела корректно разводит диапазоны: TC-UI-012…014 —
  итерация BUG-046 (Спринт 3, change add-instructor-student-loop), в Партию A
  не входят; трассировка Партии A — TC-UI-015…018 + TC-S3BE-040/041.

## 2. Остальные пункты чек-листа итерации 1 — остаются в силе

Перепроверено по факту, не по памяти:

- **п.1 (задачи 4.1–4.6): PASS.** Рабочее дерево/HEAD не изменились
  (8273f45 поверх 5db9cc5), страницы, маршруты, нав-связки, e2e — на месте.
  Оговорка по неотмеченным чекбоксам PLAN.md — без изменений (заметка ПМ).
- **п.2 (артефакты партии): PASS.** review-001 (RETURN), review-002
  (APPROVE), qa-auto-report, arch-review-s4.md — существуют (проверено ls);
  design.md-строка Блока 6 — в силе.
- **п.4 (валидации): PASS, воспроизведено заново в итерации 2:**
  - `PATH="$(npm prefix -g)/bin:$PATH" openspec validate --all --strict` →
    5 passed, 0 failed, exit 0;
  - `python3 scripts/flow_check.py .` → «flow_check: OK — порядок артефактов
    соответствует флоу», exit 0; попутный FLOW-WARNING — известный долг
    4.B3, не блокирует (без изменений с итерации 1);
  - полный сьют `LD_LIBRARY_PATH=~/.cache/pw-libs/root/usr/lib/x86_64-
    linux-gnu .venv/bin/python -m pytest tests/ -q` → **270 passed,
    1 warning in 235.59s** — воспроизведен и в итерации 2, совпадает
    с итерацией 1 и QA-отчетом.

## Наблюдение итерации 2 (не блокирует, ПМ на усмотрение)

4. **TC-UI-012 как литеральный ID в тестах отсутствует.** BUG-046
   (test-model/bugs/BUG-046-admin-actions-modal.md, стр. 24) и примечание 2
   в sdd.md называют диапазон «TC-UI-012…014», но в
   tests/test_ui_playwright.py есть только TC-UI-011 (стр. 1017,
   test_admin_row_click_opens_card_and_loads_license_image), TC-UI-013
   (стр. 438), TC-UI-014 (стр. 495); grep по tests/ на «TC-UI-012» — ноль.
   Это долг трассировки Спринта 3/BUG-046, вне скоупа Партии A (change
   add-s3-frontend-links): трассировка этого change полна и точна. ПМ:
   либо присвоить ID третьему тесту BUG-046, либо скорректировать диапазон
   в BUG-046/sdd.md при закрытии долга исключения TC-ID (правило 6).

## Сводный вердикт

- Итерация 1: REJECT (трассировка sdd.md отсутствовала) — основание снято.
- **Итерация 2: ACCEPT.** Партия A Спринта 4 (change add-s3-frontend-links)
  принимается: задачи 4.1–4.6 выполнены, артефакты на месте, трассировка в
  sdd.md §28 полна и сверена с кодом и тестами, валидации (openspec strict,
  flow_check, полный сьют 270 passed) воспроизведены приемочным ревьюером.
