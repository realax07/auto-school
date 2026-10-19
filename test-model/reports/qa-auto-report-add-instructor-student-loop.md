# QA-automation отчет — change add-instructor-student-loop (Спринт 3, Партия A, финальный прогон)

- Роль: qa_automation (agents/qa_automation_agent.md)
- Дата прогона: 2026-10-15 (UTC)
- Вход: test-model/approved/add-instructor-student-loop/ — 44 кейса (TC-*)
- Автотесты: tests/test_s3_backend.py (39), tests/test_ui_playwright.py (14; из них 5 — TC-UI-007…011 этого change)
- Коммитов нет (по заданию).

## 1. Полный прогон

Команда (дословно):

```
export LD_LIBRARY_PATH=~/.cache/pw-libs/root/usr/lib/x86_64-linux-gnu && .venv/bin/python -m pytest tests/ -q
```

Tail (дословно):

```
........................................................................ [ 28%]
........................................................................ [ 56%]
........................................................................ [ 84%]
.........................................                                [100%]
=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
257 passed, 1 warning in 249.84s (0:04:09)
```

Точечные прогоны целевых файлов:

- `tests/test_s3_backend.py -q` → `39 passed, 1 warning in 78.96s (0:01:18)`
- `tests/test_ui_playwright.py -q` → `14 passed in 29.90s`

Вердикт: сьют зеленый полностью, падений нет, баг-репорты не требуются.

Примечание по числам: в постановке указаны «48 и 15» — фактическое число тестов в файлах 39 и 14 (53 суммарно; остальные 204 теста сьюта — Спринты 0–2). Расхождение зафиксировано, тесты не терялись: pytest собрал и прогнал все 257.

## 2. Маппинг кейсов TC-* → автотесты

Контекст (FLOW-ERROR, см. раздел 4): в docstring тестов test_s3_backend.py TC-трассировка не ведется, поэтому маппинг ниже — содержательный, post-hoc (по GIVEN/WHEN/THEN кейса против тела теста). Тесты test_ui_playwright.py с TC-UI-* — плановая трассировка этого change.

### Домен instructor-documents (ВУ)

| Кейс | Автотест(ы) | Покрытие |
|---|---|---|
| TC-VUD-001 | test_s3_backend.py::test_apply_multipart_saves_license_image | полный (файл в license/, license_photo_path; без файла → NULL) |
| TC-VUD-002 | test_s3_backend.py::test_apply_rejects_bad_file_type_and_size | частичный: PDF→422, >5 МБ→422, заявка не создана; граница «ровно 5 МБ принимается» — НЕ автоматизирована |
| TC-VUD-003 | test_s3_backend.py::test_admin_card_and_license_image | полный (200 image/png с валидным токеном) |
| TC-VUD-004 | test_s3_backend.py::test_admin_card_and_license_image | полный (без токена/неверный токен/ученическая сессия → 401; 999999 → 404; без ВУ → 404) |
| TC-VUD-005 | test_s3_backend.py::test_license_image_direct_url_not_served | полный (прямой URL → 404) |
| TC-VUD-006 | test_s3_backend.py::test_admin_card_and_license_image + test_ui_playwright.py::test_admin_row_click_opens_card_and_loads_license_image (TC-UI-011) | полный (карточка с ВУ и без ВУ; визуал модалки — только функционально, см. раздел 3) |

### Домен instructor-cars

| Кейс | Автотест(ы) | Покрытие |
|---|---|---|
| TC-CAR-001 | test_s3_backend.py::test_cars_crud_happy_path | полный |
| TC-CAR-002 | test_s3_backend.py::test_cars_access_401_403 + ::test_car_not_visible_to_other_instructor_and_foreign_404 | полный (изоляция, 401/403) |
| TC-CAR-003 | test_s3_backend.py::test_cars_validation_422_per_field | полный (422 по полю) |
| TC-CAR-004 | test_s3_backend.py::test_car_photo_upload_and_owner_only | полный (привязка, JPEG/PNG, выдача владельцу) |
| TC-CAR-005 | test_s3_backend.py::test_car_photo_upload_and_owner_only | полный (матрица 401/403/404/404-без-фото) |
| TC-CAR-006 | test_s3_backend.py::test_car_photo_upload_and_owner_only | частичный: PDF и >5 МБ → 422, фото не привязано; граница «ровно 5 МБ» — НЕ автоматизирована |
| TC-CAR-007 | test_s3_backend.py::test_cars_crud_happy_path (PATCH) + ::test_car_not_visible_to_other_instructor_and_foreign_404 (чужой не изменяется) | полный |
| TC-CAR-008 | test_s3_backend.py::test_car_delete_unbinds_student_keeps_link + ::test_car_not_visible_to_other_instructor_and_foreign_404 (чужой не удаляется) | полный (car_id→NULL, статус accepted, ученик в summary) |

### Домен instructor-availability (календарь)

| Кейс | Автотест(ы) | Покрытие |
|---|---|---|
| TC-CAL-001 | test_s3_backend.py::test_availability_save_and_readback (API) + test_ui_playwright.py::test_instructor_calendar_slot_toggle_and_put_availability (TC-UI-008: клик по слоту, PUT) | API — полный; UI-подсветка ячеек — функционально (состояние+запрос), визуальный рендер — ручной |
| TC-CAL-002 | test_s3_backend.py::test_availability_validation_422 | полный (14:00–10:00, weekday 7, 25:00; график не сохранен) |
| TC-CAL-003 | test_s3_backend.py::test_availability_access_401_403 | полный |
| TC-CAL-004 | test_s3_backend.py::test_availability_save_and_readback (перезаход) + ::test_availability_full_replace_and_dedup (полная замена, дедуп) | полный |

### Домен student-instructor-choice (каталог)

| Кейс | Автотест(ы) | Покрытие |
|---|---|---|
| TC-CHO-001 | test_s3_backend.py::test_marketplace_lists_only_approved | полный (только approved; waiting вне users; шейп карточки) |
| TC-CHO-002 | test_s3_backend.py::test_marketplace_access_401_403 | полный |
| TC-CHO-003 | test_s3_backend.py::test_marketplace_filters (КПП/рейтинг/стаж, MIN-1, 422, пустое состояние) + test_ui_playwright.py::test_student_choice_filters_narrow_and_apply_request (TC-UI-007, UI-слой) | полный |
| TC-CHO-004 | test_s3_backend.py::test_marketplace_filters (free_weekday/free_from/free_to, пересечение, пустой результат) | полный |
| TC-CHO-005 | test_s3_backend.py::test_marketplace_lists_only_approved + ::test_marketplace_filters (TestClient без сети; каталог и фильтры работают офлайн) | частичный: шаг 1 (работоспособность без гео) покрыт де-факто; шаг 2 (инспекция отсутствия внешних вызовов карт) — ручной |

### Домен reviews

| Кейс | Автотест(ы) | Покрытие |
|---|---|---|
| TC-REV-001 | test_s3_backend.py::test_review_happy_duplicate_and_validation | полный |
| TC-REV-002 | test_s3_backend.py::test_review_requires_accepted_link_server_side | полный (только 'new' → 403; мимо UI → 403; отзыв не создан) |
| TC-REV-003 | test_s3_backend.py::test_review_happy_duplicate_and_validation | полный (409, в БД ровно один) |
| TC-REV-004 | test_s3_backend.py::test_review_happy_duplicate_and_validation | полный (0, 6, пустой текст, >1000 симв.) |
| TC-REV-005 | test_s3_backend.py::test_marketplace_card_detail_and_aggregate | полный (5,4 → 4.5, count 2) |
| TC-REV-006 | test_s3_backend.py::test_marketplace_card_detail_and_aggregate + ::test_marketplace_lists_only_approved (has_reviews:false) | полный |

### Домен student-requests (контур «инструктор ↔ ученик»)

| Кейс | Автотест(ы) | Покрытие |
|---|---|---|
| TC-REQ-001 | test_s3_backend.py::test_request_submit_duplicate_parallel_and_repeat + ::test_instructor_sees_only_own_requests + ::test_instructor_requests_contract_shape + test_ui_playwright.py::test_student_choice_filters_narrow_and_apply_request (TC-UI-007, POST из UI) | полный |
| TC-REQ-002 | test_s3_backend.py::test_request_submit_duplicate_parallel_and_repeat (409 без записи) + ::test_active_request_unique_index_blocks_duplicate_at_db_level (UNIQUE на уровне БД) | полный |
| TC-REQ-003 | test_s3_backend.py::test_request_submit_duplicate_parallel_and_repeat (параллельная Б, повтор после отказа) | полный |
| TC-REQ-004 | test_s3_backend.py::test_request_to_unapproved_instructor_404 | полный (waiting/несуществующий → 404) |
| TC-REQ-005 | test_s3_backend.py::test_instructor_sees_only_own_requests + ::test_instructor_requests_contract_shape (ФИО, стаж, дата) | полный |
| TC-REQ-006 | test_s3_backend.py::test_deny_requires_comment_and_visible_to_student + test_ui_playwright.py::test_instructor_requests_deny_locked_until_comment_accept_with_car (TC-UI-009: кнопка заблокирована до комментария) | полный |
| TC-REQ-007 | test_s3_backend.py::test_deny_and_accept_of_foreign_request_404_and_double_409 + ::test_instructor_sees_only_own_requests | полный (404, статус не изменен) |
| TC-REQ-008 | test_s3_backend.py::test_live_request_flow_submit_accept_closes_others + ::test_accept_requires_car_zero_cars_409_foreign_car_422 (своим авто) + ::test_assign_student_car_rebind_and_guards | полный (связь создана, car в контракте) |
| TC-REQ-009 | test_s3_backend.py::test_accept_requires_car_zero_cars_409_foreign_car_422 | полный (0 авто → 409; чужой car_id → 422) |
| TC-REQ-010 | test_s3_backend.py::test_accept_closes_other_active_requests_new_and_accepted + ::test_live_request_flow_submit_accept_closes_others | полный ('new' и 'accepted' закрываются, системный комментарий виден ученику) |
| TC-REQ-011 | test_s3_backend.py::test_accept_closes_other_active_requests_new_and_accepted (MAJ-1: разрыв существующей accepted-связи, summary_b пуст) + ::test_live_request_flow_submit_accept_closes_others (повторное решение → 409) | полный |
| TC-REQ-012 | test_s3_backend.py::test_assign_student_car_rebind_and_guards | полный (свое авто → 200, car_id обновлен) |
| TC-REQ-013 | test_s3_backend.py::test_assign_student_car_rebind_and_guards | полный (чужой car → 422; чужой ученик → 404; связь не меняется) |
| TC-REQ-014 | test_s3_backend.py::test_summary_widgets (до/после принятия) + ::test_car_delete_unbinds_student_keeps_link (ученик остается) | полный |
| TC-REQ-015 | test_s3_backend.py::test_summary_widgets (today_lessons — честный []) | полный |

### Сводка

- 44 кейса: 42 покрыты автоматическими тестами (из них 3 частично: TC-VUD-002, TC-CAR-006 — без границы «ровно 5 МБ»; TC-CHO-005 — без ручной инспекции кода), 0 кейсов без автоматического покрытия вовсе.
- UI-слой дополнительно: TC-UI-007 (выбор/заявка), TC-UI-008 (календарь), TC-UI-009 (отказ/принятие), TC-UI-010 (logout → /instructors — долг review-001, вне TC-* набора), TC-UI-011 (админ-карточка + ВУ).
- Автотесты без прямого TC (следствие FLOW-ERROR, раздел 4): 3 миграционных (test_migration_*), test_apply_experience_years_validation_and_transfer (MAJ-3), test_accept_401_403, test_summary_access_401_403, test_new_modules_no_sql_concatenation (NFR-3).

## 3. Что НЕ автоматизировано (ручные шаги)

1. Визуальная часть TC-CAL-001 (шаг 3: «ячейки Пн 10:00–14:00 отмечены рабочими») — проверяется только состояние слота и корректность PUT (TC-UI-008), фактический рендер подсветки — вручную по чек-листу.
2. Визуальные проверки вёрстки (допуски позиционирования, пустые состояния «глазами») — в духе TC-UI-001…006 (6px-допуски); для этого change таких кейсов в партии нет, ручной чек-лист.
3. Граница «файл ровно 5 МБ принимается» (CHK-3/CHK-19; внутри TC-VUD-002 шаг 3, TC-CAR-006 шаг 3) — автотесты проверяют только «> 5 МБ → 422»; граничный вариант ровно 5 МБ не воспроизведен.
4. TC-CHO-005 шаг 2 — инспекция кода/журналов на отсутствие обращений к картографическим сервисам (шаг 1 покрыт де-факто: TestClient исполняется без сети).
5. Эксплуатационные ручные проверки чек-листа: поведение на uvicorn/single-worker реального стенда (кейсы допускают TestClient), проверка «живости» GET /api/health как отдельный ручной шаг.

## 4. Известный FLOW-ERROR test_s3_backend (осознанный долг)

В tests/test_s3_backend.py (строки 1–10 docstring) зафиксировано: «TC-трассировка не ведется (backend-тесты, не test-model)». Одновременно кейсы партии (все 44) содержат пометку: «плановые TC-ID в docstring автотестов действуют до утверждения, rule 6» — т.е. rule 6 ожидает TC-трассировку из docstring. Требование и реализация расходятся: backend-тесты этого change не несут TC-ID, и трассировка существует только в этом отчете (содержательный маппинг, post-hoc). Зафиксировано как осознанный долг конвейера; не блокирует партию (все кейсы покрыты, сьют зеленый). Устранение — либо добавить TC-ID в docstring test_s3_backend.py, либо зафиксировать в правиле 6 исключение для backend-доменных тестов; решение за ПМ/arch-review.

## 5. Перенос партии

- test-model/new/add-instructor-student-loop/ → test-model/approved/add-instructor-student-loop/
- Скопировано 44 файла, `diff -r` — IDENTICAL (verbatim, без правок).
- Коммитов нет (по заданию).
