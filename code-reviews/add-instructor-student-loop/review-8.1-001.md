<!-- reviewer: code_reviewer (spawned hermes chat session, role=code_reviewer, итерация 2) | дифф: feature/add-instructor-student-loop..feature/s3-fixups (7 файлов, +553/−145) | дата: 2026-10-15 | база: code-reviews/add-instructor-student-loop/review-001.md (RETURN) -->

# Code review (итерация 2): фикс-ветка s3-fixups по review-001

Объект: дифф `feature/add-instructor-student-loop..feature/s3-fixups` —
backend/db.py, backend/student_requests.py, frontend/instructor-choice.html,
frontend/instructor-dashboard.html, tasks.md, tests/test_s3_backend.py,
tests/test_ui_playwright.py. Ветка checked out в worktree (eb4ba6d).

Прогон ревьюером: `export LD_LIBRARY_PATH=~/.cache/pw-libs/root/usr/lib/x86_64-linux-gnu && .venv/bin/python -m pytest tests/test_s3_backend.py tests/test_ui_playwright.py -q` —
**53 passed, 1 warning, 122s** (было 48; +3 backend +2 e2e — ровно новые тесты).

Контрактные шейпы сверены с исходниками бэкенда, не только с диффом:
- GET /api/student/instructors → `{id, full_name, experience_years, rating:{has_reviews,average,count}|{has_reviews:false}, cars:[{brand,model,year,transmission}], availability:[{weekday,start_time,end_time}]}` (student_marketplace.py:202–210) — фронт читает ровно эти имена;
- GET /api/instructor/requests → `{id, status, created_at, decided_at, student_full_name, student_experience_years, car:{id,brand,model,year,transmission}|null}` (student_requests.py:207–212) — зафиксировано тестом на `set(item.keys())`;
- GET /api/instructor/summary → `{student_id, full_name, car:"brand model year"|null, decided_at}` (instructor_summary.py:80–86) — фронт читает full_name/decided_at/car.

## Вердикт: APPROVE

Reviewer-Delegation: deleg_spawn2026101521362109c307 — spawned hermes chat session (role=code_reviewer, итерация 2; id сессии hermes 20261015_213621_09c307)

Все обязательные замечания review-001 устранены. Новых проблем итерация не
внесла (проверено: остаточные innerHTML — только статика/очистка; ответ
IntegrityError-ветки с rollback; guard-ветки accept/deny не оставляют
незакоммиченных записей; мок POST /api/student/requests
`{"ok":true,"request_id":900}` совпадает с реальным ответом
student_requests.py:135).

## Per-finding (по review-001)

| # | Серьезность | Вердикт | Чем закрыт |
|---|---|---|---|
| 1 | BLOCKER (stored XSS) | **FIXED** | instructor-choice.html: рендер полностью переведен на createElement/textContent (`el()`-хелпер, render():265–305); нормализаторы-«догадки» (instFio/carsPill/slotText со строковой конкатенацией) удалены. instructor-dashboard.html: `node()`-хелпер; renderRequests/acceptPanelNode/denyPanelNode/loadSummary/loadRequests — пользовательские строки (ФИО, brand/model/plate, комментарии) только через textContent. Остаточные innerHTML (choice:265; dashboard:251, 314–316, 334, 356–358, 446, 527, 531) — очистка контейнеров, статические пустые состояния, чип даты из Intl.DateTimeFormat и сетка календаря из констант CAL_DAYS/CAL_HOURS — пользовательский ввод не участвует. Регресс-тест есть: test_student_choice_xss_instructor_name_not_executed — инструктор с `surname` = `<img src=x onerror=window.__xss=1>` проходит apply→approve, ученик открывает каталог: window.__xss undefined, img-элементов нет, payload виден как текст |
| 2 | MAJOR (контракт /requests) | **FIXED** | Фронт: rqFio→`r.student_full_name`, rqExp→`r.student_experience_years`, rqCarName→объект `r.car` (brand+model), rqDate→`created_at`; фиктивные student_fio/student/comment/`[object Object]`-ветки удалены. Мертвый rqComment («Комментарий ученика») удален вместе с веткой |
| 3 | MAJOR (FR-37 стаж) | **FIXED** | student_requests.py:210–214 — `student_experience_years` в элементе ответа; контракт-тест test_instructor_requests_contract_shape проверяет наличие поля и точный набор ключей |
| 4 | MAJOR (контракт summary) | **FIXED** | Фронт: `s.full_name`, `s.decided_at` (дата «с инструктора с …»), car-строка с фолбэком «авто не выбрано»; алиасы fio/since/accepted_at удалены. Живая проверка сквозняком — в test_instructor_accept_flow_real_backend: виджет показывает «Смирнова Ольга Павловна» + «Škoda Rapid 2020» после accept без перезагрузки |
| 5 | MAJOR (вакуумные e2e) | **FIXED** | (а) Все моки переписаны на реальные шейпы (_instructor_card → full_name/experience_years/cars с id/availability; requests → student_full_name/student_experience_years/car/decided_at; POST-ответ request_id). (б) +2 интеграционных e2e на живом бэкенде без page.route: test_instructor_accept_flow_real_backend (полный поток apply→approve→login→car→заявка учеником→кабинет инструктора→accept с выбором авто→виджеты+бэкенд-сверка FR-38) и test_student_choice_xss_instructor_name_not_executed (см. #1). (в) +2 backend-интеграционных на TestClient: test_live_request_flow_submit_accept_closes_others (поток заявки: 2 инструктора → accept → автозакрытие ОВ-1 → 409 повторного решения → ФИО/стаж/авто в ответах) и test_instructor_requests_contract_shape (контракт шейпа, точный набор ключей до и после accept) |
| 6 | MAJOR (гонка дубликата) | **FIXED** | Частичный UNIQUE-индекс `uq_student_requests_active ON student_requests(student_id, instructor_id) WHERE status IN ('new','accepted')` в db.py (идемпотентно, в общем SCHEMA-блоке); в create_request INSERT обернут try/except sqlite3.IntegrityError → rollback + 409 (по образцу reviews.py); denied-заявки индекс не учитывает — повторная заявка после отказа допустима (ОВ-2). UNIQUE-тест: test_active_request_unique_index_blocks_duplicate_at_db_level — второй активный INSERT ловит IntegrityError на уровне БД, denied-дубликат вставляется (count==2) |
| 7 | MAJOR (гонка перехода статуса) | **FIXED** | accept_request: `UPDATE … WHERE id=? AND status='new'` + `rowcount==0 → 409 «Заявка: решение уже принято»` (до каскада автозакрытия — ошибочная ветка ничего не пишет); deny_request: тот же guard+rowcount. Интерливинг accept/deny больше не перезаписывает решение молча; покрыт в test_live_request_flow (повторный accept по закрытой → 409) |
| 8 | MAJOR (скоуп tasks.md) | **FIXED** (для требованного объема) | 2.2, 5.2, 6.3 помечены `[→ Партия B/след. спринт — code-review review-001 #8…]` с обоснованием «фронтенд-потребителя в Партии A нет, API готов». Остаток: частичный пункт 6.4 («Мои ученики» + перекрепление PATCH /api/instructor/students/{id}/car) пометки не получил — перенос в Партию B для этой части не зафиксирован. Не блокирует: эндпоинт ОВ-3 в списке обязательных фиксов review-001 не значился, решение за ПМ — не потерять при планировании Партии B |
| 9–14 | MINOR | В бэклог (как и предписано итогом review-001) | Не входили в обязательный список; #14 попутно улучшен: 409 больше не кэшируется в `sent` (choice.html:304–306) |

## Не является замечанием (проверено в этой итерации)

- Прогон 53 passed на фикс-ветке; новые тесты реально падают на сломанном
  контракте по построению (моки = точные шейпы бэкенда, контракт-тест =
  `set(keys) == {...}` — любое добавление/удаление поля ловится).
- Комментарии в коде ссылаются на review-001 корректно, без выдуманных номеров.
- В репозитории ревьюером ничего не правилось (НИЧЕГО не править — соблюдено).

## Итог

APPROVE. Обязательный список review-001 (#1–#7) закрыт, #8 закрыт в требуемом
объеме (2.2/5.2/6.3 → Партия B). Хвост: частичный 6.4 без пометки переноса —
в бэклог ПМа, не блокирует. Прогон: 53 passed, 1 warning, 122s.

МЕТА: Reviewer-Delegation: deleg_spawn2026101521362109c307 — spawned hermes chat session (role=code_reviewer, итерация 2; id сессии hermes 20261015_213621_09c307)
