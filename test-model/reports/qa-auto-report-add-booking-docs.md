# QA-automation отчет — change add-booking-docs (Спринт 5, Партия A, финальный прогон)

- Роль: qa_automation (agents/qa_automation_agent.md)
- Дата прогона: 2026-10-22 (UTC)
- Вход: кейсы change add-booking-docs — TC-S5BE-001…025 (+011b, M-ревью до-кейсы) в tests/test_s5_backend.py; TC-UI-015/016/019/023/024/025 (change add-booking-docs) в tests/test_ui_playwright.py. Кейсы живут трассировкой в docstring тестов (перенос в test-model не требуется — та же схема, что в Спринте 4).
- Коммитов нет (по заданию).

## 1. Полный сьют

Команда (дословно):

```
export LD_LIBRARY_PATH=~/.cache/pw-libs/root/usr/lib/x86_64-linux-gnu && /home/hermes-bot/auto-school/.venv/bin/python -m pytest tests/ -q
```

Tail (дословно):

```
........................................................................ [ 23%]
........................................................................ [ 46%]
........................................................................ [ 70%]
........................................................................ [ 93%]
..................                                                      [100%]
=============================== warnings summary ===============================
../../../../auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
307 passed, 1 warning in 315.37s (0:05:15)
```

## 2. Вердикты прогонов

Backend-сьюит Спринта 5 — `tests/test_s5_backend.py -q`, tail (дословно):

```
..........................                                               [100%]
=============================== warnings summary ===============================
tests/test_s5_backend.py::test_s5_migration_booking_table_and_indexes
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
26 passed, 1 warning in 62.96s (0:01:02)
```

E2E-сьюит — `tests/test_ui_playwright.py -q` (с тем же LD_LIBRARY_PATH), tail (дословно):

```
..................................                                       [100%]
34 passed in 82.27s (0:01:22)
```

Сборка: test_s3_backend — 43 собранных теста, test_s5_backend — 26, test_ui_playwright — 34 (итого 103); остальные 204 сьюта — Спринты 0–4. Прошлый финальный прогон (Спринт 4): 270; сейчас 307 = +37 (26 backend-S5 + доукомплектация e2e/баг-регрессы). Все три прогона зеленые, падений нет, баг-репорты не требуются.

## 3. Маппинг кейсов → автотесты

### TC-S5BE (backend, tests/test_s5_backend.py — TC-ID в docstring каждого теста, rule 6)

| Кейс | Автотест | Покрытие (кратко) |
|---|---|---|
| TC-S5BE-001 | test_s5_migration_booking_table_and_indexes | миграции: таблица booking + индексы |
| TC-S5BE-002 | test_s5_migration_idempotent_keeps_rows | повторный init_db идемпотентен, данные целы |
| TC-S5BE-003 | test_s5_car_creation_requires_sts | создание авто: СТС обязателен (FR-44) |
| TC-S5BE-004 | test_s5_car_sts_file_validation | СТС не JPEG/PNG, >5 МБ → 422, авто не создан |
| TC-S5BE-005 | test_s5_car_photo_angles_upload_replace | 5 ракурсов: загрузка/замена по слотам, выдача отдельно |
| TC-S5BE-006 | test_s5_car_photo_angle_errors | ракурс вне списка / чужой авто / незагруженный → 404 |
| TC-S5BE-007 | test_s5_car_photo_access_matrix_and_sts | матрица доступа: владелец + ученик ПАРЫ; 403/404/401; СТС ученику не выдается (FR-42, MIN-2) |
| TC-S5BE-008 | test_s5_bug_5_2_photo_survives_relogin | баг 5.2: фото переживает перезаход (URL эндпоинта в плитках) |
| TC-S5BE-009 | test_s5_admin_cars_completeness | GET /api/admin/cars/completeness: 401 без токена, комплектность по авто |
| TC-S5BE-010 | test_s5_admin_block_car_min2 | блокировка авто идемпотентна, 404, не ретроактивна (MIN-2) |
| TC-S5BE-011 | test_s5_documents_list_with_license_and_two_cars | «Мои документы»: ВУ + 2 авто = 3 записи (FR-45) |
| TC-S5BE-011b | test_s5_documents_empty_license_state | анкета без ВУ — пустое состояние с подсказкой |
| TC-S5BE-012 | test_s5_documents_file_access | файл документа только владельцу (NFR-7) |
| TC-S5BE-013 | test_s5_slots_access_guard | слоты без пары → 403, несуществующий/не одобренный инструктор → 404 |
| TC-S5BE-014 | test_s5_slots_states | состояния слотов (free/booked/blocked) (FR-47) |
| TC-S5BE-015 | test_s5_booking_create_and_lesson_date_boundary | бронь status='new'; границы lesson_date (MIN-1) |
| TC-S5BE-016 | test_s5_booking_conflict_409_no_record | занятый слот → 409 без записи (частичный UNIQUE); повтор на свой слот |
| TC-S5BE-017 | test_s5_booking_race_two_students_one_409 | ГОНКИ: два ученика на слот — ровно одна бронь (NFR-8) |
| TC-S5BE-018 | test_s5_confirm_flow | confirm: confirmed + decided_at, виден в обоих календарях (FR-48) |
| TC-S5BE-019 | test_s5_reject_requires_comment_and_frees_slot | reject без комментария → 422; с комментарием слот освобожден (ОВ-2) |
| TC-S5BE-020 | test_s5_put_availability_blocked_by_active_bookings | PUT графика при активных бронях → 409 с перечнем слотов (MAJ-1) |
| TC-S5BE-025 | test_s5_put_availability_vs_booking_race_no_orphan | гонка PUT availability × создание брони — сирот нет (M-3 review-001, NFR-8) |
| TC-S5BE-021 | test_s5_calendars_survive_car_deletion | авто пары удален → календари возвращают бронь с car: null (MIN-3) |
| TC-S5BE-022 | test_s5_summary_today_lessons | today_lessons — confirmed на сегодня, локальная дата сервера (FR-49, ОВ-6) |
| TC-S5BE-023 | test_s5_new_modules_no_sql_concatenation | NFR-10←NFR-3: нет конкатенаций в SQL новых модулей |
| TC-S5BE-024 | test_s5_create_car_json_invalid_body_422_not_500 | легаси-JSON путь create_car: клиентский ввод → 422, не 500 (M-2 review-001) |

Сводка: 26/26 тестов файла трассированы, 26 уникальных TC-S5BE, биекция кейс↔тест.

### TC-UI (live e2e, tests/test_ui_playwright.py — change add-booking-docs)

| Кейс | Автотест | Покрытие (кратко) |
|---|---|---|
| TC-UI-015 | test_s4_my_cars_add_edit_delete_car | «Мои автомобили» ВНУТРИ дашборда (BUG-047) на живом бэкенде: добавление/правка/удаление, списки UI+API |
| TC-UI-016 | test_s4_my_cars_photo_upload_progress_and_preview | слоты ракурсов: клик по пустому слоту → выбор файла → превью на карточке, has_photo |
| TC-UI-019 | test_back_links_lead_to_role_home | back-ссылки встроенных разделов ведут на ролевую домашнюю (BUG-047) |
| TC-UI-023 | test_bug048_mycars_photo_thumbnail_before_send_and_errors | миниатюра выбранного фото СТС до отправки, ошибки файла (BUG-048) |
| TC-UI-024 (M-1 review-001) | test_instructor_summary_today_lessons_widget_renders_real_shape | виджет «Занятия на сегодня» рендерит непустой today_lessons по РЕАЛЬНОМУ шейпу бэка |
| TC-UI-024 (интеграция) | test_s5_car_full_kit_completeness_and_student_sees_car | интеграция «авто»: полный комплект ракурсов = комплектность админа; ученик пары видит авто, СТС не выдается (FR-42/FR-44) |
| TC-UI-025 | test_s5_booking_flow_slots_request_confirm_and_409 | интеграция «бронирование»: слоты → запрос → confirm, конфликт 409, на живом бэкенде (FR-42…FR-50) |

Замечания по трассировке TC-UI (не блокируют партию, на усмотрение ПМ/ретро):

1. Коллизия TC-UI-024: два разных теста в одном файле несут один TC-ID (виджет M-1 и интеграция «авто»). Rule 6 формально соблюден (ID есть), но биекция кейс↔тест нарушена — одному из тестов нужен отдельный ID (например, TC-UI-026).
2. TC-UI-015/016 в Спринте 4 трассировались на change add-s3-frontend-links (прошлый отчет, раздел 3); сейчас docstring тех же функций несут «change add-booking-docs» (разделы пересобраны под BUG-047). История переноса ID между changes нигде не зафиксирована — отмечено для ретро.

### Неавтоматизированное (визуал)

- design/mocks/booking-student.html, booking-instructor.html, my-cars.html, my-documents.html — визуальная приемка мокапов (design_validator / выбор варианта Заказчиком) автотестами не покрывается и по контракту не переносится в e2e; в сьюте только косвенный structural sanity (tag-balance, маркеры заголовков в TC-S5BE/TC-UI-015).
- Pixel-perfect соответствие реализованных страниц мокапам — ручная стадия design check, вне зоны qa_automation.

## 4. Статус rule 6

### test_s3_backend.py — долг INC-005: ЗАКРЫТ

- Было (Спринт 3): 39 backend-тестов (TC-S3BE-001…039) без TC-ID в docstring — осознанный долг, INC-005 в incidents.md.
- Факт сейчас (проверено грепом файла): все тесты несут TC-ID — TC-S3BE-001…039 (Спринт 3), TC-S3BE-040/041 (Спринт 4, add-s3-frontend-links). PLAN.md: «TC-трассировка 129 кейсов (INC-005 закрыт, гейт 0 ошибок) | [x] PR#65» — долг закрыт в Спринте 4, правило 6 для файла выполняется полностью.
- Единственное исключение: test_bug047_old_routes_redirect_301 (параметризованный, 2 кейса) — регресс BUG-047 без TC-ID (трассировка на баг-репорт test-model/bugs/BUG-047-*, не на TC-кейс). Мелочь, отмечено для ретро, гейт не нарушает.

### test_s5_backend.py — ЧИСТ

TC-S5BE присутствуют: 26 тестов — 26 docstring с TC-S5BE-NNN (001…023, 025, 011b, 024; 26 уникальных ID), биекция полная. Шапка файла фиксирует: test_s3_backend Спринта 3 не расширяется, все новые кейсы — здесь, трассировка в docstring (rule 6). Нарушений нет.

## 5. Перенос партии

Не требуется: кейсы change add-booking-docs живут трассировкой в docstring тестов (схема Спринта 4); test-model/approved|new/add-booking-docs не создаются.

## 6. Изменения в репозитории

- Добавлен только этот отчет: test-model/reports/qa-auto-report-add-booking-docs.md.
- Тесты и код не менялись. Коммитов нет (по заданию).
