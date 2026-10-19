# Review-acceptance — add-instructor-student-loop (Спринт 3, Партия A, итерация 1)

- МЕТА: Reviewer-Delegation: spawned hermes chat session (role=qa_case_reviewer, приемка)
- Ревьюер: qa_case_reviewer (Флоу 1, приемочное ревью Партии A)
- Дата: 2026-10-15
- Объект: рабочее дерево репозитория (изменения не закоммичены: tasks.md, sdd.md —
  modified; code-reviews/, test-model/{approved,new,reviews,checklists}/,
  qa-auto-report — untracked). HEAD = eb4ba6d на ветке feature/s3-fixups
  (фикс-ветка поверх feature/add-instructor-student-loop, дифф ревьюился в
  review-002 как feature/add-instructor-student-loop..feature/s3-fixups — ветка
  ревью соответствует фактической, ожидание «ветка = feature/add-instructor-student-loop»
  зафиксировано как расхождение в наименовании, не по содержанию).
- Вмешательство в материалы: нулевое (ничего не правлено, артефакт только этот).

## Чек-лист приемки

### 1. tasks.md: 8.1 [x]; остальные [x] либо явно помечены → Партия B

**Вердикт: FAIL.**

- 8.1: [x] — OK (единственный отмеченный пункт; дифф рабочего дерева
  подтверждает, что отметка внесена в этой партии).
- Явно помечены → Партия B: 2.2, 5.2, 6.3 — OK (маркер
  «[→ Партия B/след. спринт — code-review review-001 #8…]» на месте).
- 6.4: частичный перенос в Партию B НЕ зафиксирован — задача остается `[ ]`
  без пометки. Это известный остаток, прямо названный в review-002 #8
  («частичный пункт 6.4 («Мои ученики» + перекрепление PATCH
  /api/instructor/students/{id}/car) пометки не получил… решение за ПМ»).
- ГЛАВНОЕ: выполненные задачи 1.1, 1.2, 1.3, 2.1, 3.1, 3.2, 4.1, 4.2, 5.1,
  6.1, 6.2, 6.4 (осн. часть), 7.1 — все остаются `[ ]` (13 чекбоксов не
  отмечено). Факт выполнения подтверждается независимо (код, тесты, ревью),
  но по чек-листу приемки выполненные задачи должны быть `[x]`. Для сравнения:
  закрытые change-пакеты спринтов 1–2 (add-instructor-flow, add-registration-admin)
  имеют задачи с отметками [x].

Необходимое исправление — механическое, без изменения кода: проставить [x]
выполненным задачам и добавить явную пометку переноса остатка 6.4 → Партия B.

### 2. sdd.md: раздел «Трассировка (Спринт 3, Партия A)»

**Вердикт: PASS.**

- sdd.md, §27 «Трассировка (Спринт 3, Партия A)» (строки 686+): FR-23…FR-41 —
  все 19 присутствуют; NFR-1…NFR-6 — все 6 присутствуют. Каждая строка:
  реализация (файл/эндпоинт/функция) + тесты.
- Выборочная сверка тестов на факт существования (имена из трассировки ↔ код):
  - tests/test_s3_backend.py::test_apply_multipart_saves_license_image (FR-23) — есть, стр. 564
  - ::test_admin_card_and_license_image (FR-24/25, NFR-1) — есть, стр. 651
  - ::test_cars_crud_happy_path (FR-26/28) — есть, стр. 236
  - ::test_availability_save_and_readback (FR-29/30) — есть, стр. 466
  - ::test_marketplace_filters (FR-32/33) — есть, стр. 792
  - ::test_review_requires_accepted_link_server_side (FR-34, NFR-2) — есть, стр. 934
  - ::test_live_request_flow_submit_accept_closes_others (FR-39) — есть, стр. 1088
  - ::test_summary_widgets (FR-40/41) — есть, стр. 1477
  - ::test_new_modules_no_sql_concatenation (NFR-3) — есть, стр. 1523
  - tests/test_ui_playwright.py: TC-UI-007…TC-UI-011 в docstring (FR-25/29/32/36/38) — есть, стр. 533/589/648/892/921
- Реализационные файлы из трассировки существуют: backend/{uploads,
  instructor_admin, instructor_cars, instructor_availability, student_marketplace,
  reviews, student_requests, instructor_summary, instructors}.py.
- Отмеченные в трассировке ручные хвосты (NFR-4, граница 5 МБ, инспекция
  гео-вызовов) декларированы честно, со ссылкой на QA-отчет §3 — допустимо.

### 3. Комплект артефактов

**Вердикт: PASS.**

| Артефакт | Ожидание | Факт |
|---|---|---|
| openspec/…/arch-review.md | approve, итерация 2 | «needs-rework (итерация 1) → approve (итерация 2)»; раздел «Итерация 2», итоговый вердикт «approve», per-finding вердикты MAJ-1…3/MIN-1…4 — на месте |
| code-reviews/…/review-001.md | RETURN | «Вердикт: RETURN», 1 BLOCKER (XSS) + MAJOR'ы, живой прогон 48 passed ревьюером |
| code-reviews/…/review-002.md | APPROVE | «Вердикт: APPROVE», все #1–#8 FIXED, прогон 53 passed (+3 backend, +2 e2e ровно новые) |
| test-model/reviews/…/review-001-design.md | approve-with-notes | «Вердикт: approve-with-notes», 3 MATCH + заметки N1–N3 (не блокируют) |
| test-model/reviews/…/review-001-cases.md | RETURN → итерация 2 APPROVE | Итерация 1: «RETURN» (1 blocker, 1 major); итерация 2: «APPROVE» партия из 44 кейсов |
| test-model/reports/qa-auto-report-add-instructor-student-loop.md | есть | Полный прогон 257 passed, 1 warning, 249.84s; точечно 39 backend + 14 e2e; расхождение «48/15 vs 39/14» зафиксировано в отчете |
| test-model/approved/ == test-model/new/ | 44 == 44, diff -r чистый | diff -r — без различий; 44 файла в каждой (CAL 4, CAR 8, CHO 5, REQ 15, REV 6, VUD 6) |

Выборочное открытие кейсов (6 файлов): TC-REQ-005, TC-CAL-002, TC-CAR-004,
TC-CHO-003, TC-REV-002, TC-VUD-003 — структурно полные (ID кейса, ID чеклиста,
источник → Requirement → FR, тип, приоритет Must, статус).

### 4. Валидации

**Вердикт: PASS с оговоркой (1 новый хвост flow_check).**

- `openspec validate --all --strict` (PATH=$(npm prefix -g)/bin):
  «Totals: 5 passed, 0 failed (5 items)» — зеленый, включая
  change/add-instructor-student-loop. Фактический прогон при приемке.
- `python3 scripts/flow_check.py .` — фактический хвост при приемке:
  ```
  FLOW-WARNING: промпты устарели относительно ~/ai-factory: README.md, architect_agent.md, ba_agent.md, code_reviewer_agent.md, debug_agent.md — обнови: factory_init.py --target auto-school --name <name> --force
  FLOW-ERROR: openspec/changes/add-instructor-student-loop: 1 закрытых dev-задач без code-review — каталог code-reviews/add-instructor-student-loop/ пуст или без approve-вердиктов (J10): 8.1
  FLOW-ERROR: tests/test_s3_backend.py: тесты без TC-трассировки в docstring (rule 6)
  flow_check: 2 ошибок(и)
  ```
  - rule 6 (test_s3_backend без TC-ID в docstring) — известный долг, принят.
  - FLOW-WARNING по промптам — известный, вне скоупа партии.
  - НОВОЕ (в известном списке не значилось): J10 по 8.1. Корневая причина
    установлена (scripts/flow_check.py, стр. 22–24): чекер атрибутирует
    approve по имени файла `review-NNN-<task…>.md`; фактические имена
    `review-001.md` / `review-002.md` под оба паттерна не подпадают и
    пропускаются, поэтому approve review-002 не связывается с задачей 8.1.
    Субстанция ревью есть (review-001 RETURN → review-002 APPROVE, см. §3) —
    это дефект наименования артефактов, а не отсутствие ревью. Требует
    решения ПМ (переименование/маппинг review-mapping.json) — в этой приемке
    не исправлялось.

## Итог

**Вердикт: REJECT** (одна формальная причина; содержательная часть партии —
принята).

- Содержательно Партия A закрыта: трассировка полна и верифицируема, комплект
  ревью полный с корректной эскалацией RETURN→APPROVE, сьют зеленый (257
  passed факт), кейсы 44 == 44, openspec --strict зеленый.
- Единственный блокер приемки — чек-лист п.1: 13 выполненных задач (1.1–1.3,
  2.1, 3.1–3.2, 4.1–4.2, 5.1, 6.1–6.2, 6.4-осн., 7.1) не отмечены [x], а
  частичный перенос 6.4 → Партия B не помечен. Исправление механическое,
  кода не касается; после правки tasks.md и решения по J10-неймингу ревью
  (переименование code-reviews/review-00N.md в формат с task-id либо
  review-mapping.json) повторная приемка сводится к перепроверке п.1 и хвоста
  flow_check.
- Наблюдение (не блокер): работа шла в рабочем дереве ветки feature/s3-fixups
  (HEAD eb4ba6d), а не feature/add-instructor-student-loop; правки tasks.md/sdd.md
  не закоммичены. При закрытии партии — закоммитить и слить в согласованную ветку.
