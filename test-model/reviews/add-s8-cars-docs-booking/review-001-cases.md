# Review-001 — ревью кейсов add-s8-cars-docs-booking (итерация 001, кейсы)

<!-- reviewer: qa_case_reviewer (независимый сабагент); дата: 2026-11-02 -->

- Change: add-s8-cars-docs-booking (Спринт 8)
- Ревьюер: qa_case_reviewer (независимый сабагент)
- Дата: 2026-11-02
- Вход: test-model/new/add-s8-cars-docs-booking/ — 17 файлов (TC-S8BE-001…009, TC-UI-033…040)
- Арбитры: openspec/changes/add-s8-cars-docs-booking/specs/{instructor-documents,instructor-cars,instructor-availability,student-requests}/spec.md; tests/test_s8_backend.py (автотесты TC-S8BE-001…009, docstrings + тела); tests/test_ui_playwright.py (автотесты TC-UI-033…040 + TC-UI-039b, docstrings + тела)
- Границы вердикта: «одобрить» только при отсутствии blocker/major (agents/qa_case_reviewer_agent.md).
- Процедура: файл за файлом, сверка по осям (трассировка / покрытие спеки / негатив-границы / дефекты спеки / воспроизводимость / тестовые данные) + сверка GIVEN/WHEN/THEN с телом автотеста.

## Таблица вердиктов

| Кейс | Автотест (существует) | Вердикт | Замечание |
|---|---|---|---|
| TC-S8BE-001 | test_s8_migration_legacy_seed_and_schema_guards | approve | без замечаний |
| TC-S8BE-002 | test_s8_license_version_lifecycle_and_reject_reason | approve | без замечаний |
| TC-S8BE-003 | test_s8_sts_primary_replacement_and_admin_flow | approve | без замечаний |
| TC-S8BE-004 | test_s8_sts_replacement_keeps_validated_ov6 | approve | без замечаний |
| TC-S8BE-005 | test_s8_access_matrix | approve | без замечаний |
| TC-S8BE-006 | test_s8_my_documents_versions_and_empty_state | approve | без замечаний |
| TC-S8BE-007 | test_s8_car_tiles_use_photo_endpoints_bug52 | approve | замеч. 3 (spec-gap, обзорно) |
| TC-S8BE-008 | test_s8_empty_sts_rule_seed_branch_agree | approve | без замечаний (Should обоснован) |
| TC-S8BE-009 | test_s8_my_students_list_counters_and_access | approve | без замечаний |
| TC-UI-033 | test_s8_my_documents_statuses_versions_and_license_replace | approve | без замечаний |
| TC-UI-034 | test_s8_sts_upload_missing_and_replace_car_modal_422_honest | approve | без замечаний |
| TC-UI-035 | test_s8_cars_and_docs_screens_have_no_widgets | approve | без замечаний |
| TC-UI-036 | test_s8_admin_documents_verify_reject_preview_history | approve | без замечаний |
| TC-UI-037 | test_s8_student_my_bookings_car_card_with_photo | approve | замеч. 1 (minor), замеч. 4 (spec-gap, обзорно) |
| TC-UI-038 | test_s8_bookings_section_removed_redirect_and_slot_reject | approve | без замечаний |
| TC-UI-039 | test_s8_my_students_cards_counters_and_requests_subtab | approve | замеч. 5 (noted, вне кейса) |
| TC-UI-040 | test_s8_sts_gallery_replace_dialog | approve | без замечаний |

## Вердикт: approve

Reviewer-Delegation: deleg-qr-20261102-130653-external

- Blocker: 0. Major: 0. Minor: 1 (TC-UI-037, день недели в GIVEN).
- Approved: 17/17 — все кейсы копируются в test-model/approved/add-s8-cars-docs-booking/.
- Основание: у каждого кейса автотест существует с точным именем; TC-ID в docstring (rule 6); GIVEN/WHEN/THEN соответствуют телу теста пошагово (включая коды ответов, поля контрактов, маркеры UI и содержимое файлов ROOT_JPEG/PNG/PDF/JPEG2); ссылки трассировки ведут на существующие заголовки Requirements/Scenarios спек change-пакета; Приоритеты обоснованы (Must — FR/ОВ-основы change; единственный Should, TC-S8BE-008, — согласованность правила MINOR review-003 #3, обоснование в кейсе).

## Замечания

| № | Кейс/зона | Серьезность | Дефект | Рекомендация |
|---|---|---|---|---|
| 1 | TC-UI-037 | minor | GIVEN называет слот «Пт(3)»: weekday=3 при конвенции Mon=0 — четверг (калибр той же партии TC-UI-038 «Ср(2)» — верен). Имя дня в GIVEN декоративное: ни тест, ни UI его не ассертят | При чистке new/ (отдельный цикл ПМ) заменить на «Чт(3)»; содержательных правок не требуется |
| 2 | дефект спеки (эскалация ПМ) | minor | specs/instructor-cars: нет Scenario под выдачу плиткам URL авторизованных фото-эндпоинтов (photos/sts_url, без файловых путей) — базу бага 5.2/FR-42 в дельте покрывает только «Диагностика СТС-симптома…» | Зафиксировать scenario в спеке или task-заметке ПМ; автор TC-S8BE-007 гэп честно пометил в кейсе |
| 3 | TC-S8BE-007 | minor | Следствие замеч. 2: трассировка кейса «ближайшая» (Requirement + Scenario с аннотацией), не дословная | Кейс корректен как есть; правка — в спеке, не в кейсе |
| 4 | дефект спеки (эскалация ПМ) | minor | specs/*/spec.md: нет Scenario под карточку авто с фото в «Моих брони» ученика (photo_url брони/пары, X-Session-Token, naturalWidth) — проверено по контракту Спринта 7/8, NFR-23 | Автор TC-UI-037 гэп честно пометил; добавить scenario в дельту student-booking-домена при следующей правке спек |
| 5 | TC-UI-039 / партия | info | В tests/test_ui_playwright.py есть автоматизированный TC-UI-039b (test_s8_my_students_missing_backend_honest_error — честная ошибка при 404 GET /api/instructor/students); он вне диапазона партии TC-UI-033…040, кейс не заказан | Решение ПМ: заказать кейс TC-UI-039b в следующей партии или принять тест как сверх-покрытие qa_automation |
| 6 | покрытие спеки (обзор, ПМ) | info | Scenarios без прямого кейса в партии: «СТС отображается независимо от статуса валидации авто» (покрыт косвенно TC-UI-034 — карточка draft-авто Kia Rio, и TC-S8BE-006), «Статусы документов не влияют на авто и активность инструктора» (частично — ОВ-6-кейсы TC-S8BE-004/TC-UI-034/040; каталог/брони — наследование NFR-23), «Замена СТС не трогает комплектность и ракурсы» (частично TC-S8BE-004: photo_front/photo_sts), «Сохранить/Отменить» графика с 409 MAJ-1 (наследование FR-68, новых кейсов не заказано) | Оценить ПМ при планировании: прямые кейсы или приемка косвенного покрытия; blocker/major нет, на вердикт партии не влияет |
| 7 | продукт (обзор, вне зоны) | info | Дефектов продукта при статической сверке кейс↔тест↔спека не обнаружено; честные 422-страховки (reject без причины, недопустимый файл, 404/409) реализованы и на бэке, и в UI-моках/бэке согласованно | — |

## Сверка кейсов с автотестами (оси ревью)

| Кейс | Имя теста | GIVEN/WHEN/THEN vs тело | Трассировка | Приоритет |
|---|---|---|---|---|
| TC-S8BE-001 | test_s8_migration_legacy_seed_and_schema_guards | ок (seed 2 строк, idempotent, UNIQUE pending, CHECK rejected, IntegrityError-гарды, rollback) | ок (4 ссылки — существующие заголовки) | Must (FR-70, NFR-24) — ок |
| TC-S8BE-002 | test_s8_license_version_lifecycle_and_reject_reason | ок (422 PDF/5МБ, «не мигает», reject 422/причина, last_rejected, замещение v2, verify-переключение, 409, pending-список) | ок (10 ссылок) | Must — ок |
| TC-S8BE-003 | test_s8_sts_primary_replacement_and_admin_flow | ок (verified v1 сразу, draft не меняется, замещение ОВ-7, админ-список с авто+ФИО, preview ROOT_JPEG2, verify, active_version) | ок (10 ссылок) | Must — ок |
| TC-S8BE-004 | test_s8_sts_replacement_keeps_validated_ov6 | ок (validated сохранен, photo_sts/front на месте, ракурс right → validating) | ок (3 ссылки) | Must (ОВ-6) — ок |
| TC-S8BE-005 | test_s8_access_matrix | ок (401/401/401 админ-контур, фильтр 422, гость 401/ученик 403, 404-неразличение, 999999 → 404 file/verify/reject) | ок (6 ссылок) | Must (NFR-22) — ок |
| TC-S8BE-006 | test_s8_my_documents_versions_and_empty_state | ок (license_hint, documents == [], active/pending/last_rejected, привязка car.id) | ок (4 ссылки) | Must (FR-70) — ок |
| TC-S8BE-007 | test_s8_car_tiles_use_photo_endpoints_bug52 | ок (photos.front/sts_url, нет «data/» и photo_path, 200 с содержимым, повторный список) | ок с оговоркой (замеч. 2–3) | Must — ок |
| TC-S8BE-008 | test_s8_empty_sts_rule_seed_branch_agree | ок (seed [] по '', has_sts False/sts_url None/counters False, первичная дозагрузка → verified v1, флаги True после) | ок (4 ссылки с аннотациями) | Should — обоснован |
| TC-S8BE-009 | test_s8_my_students_list_counters_and_access | ок ([s1,s2] у A, next_lesson{завтра,09:00,23:00}, 2/3, s2 None/0/0, B — только s3, 401/401/403) | ок (5 ссылок) | Must (FR-75) — ок |
| TC-UI-033 | test_s8_my_documents_statuses_versions_and_license_replace | ок (1+2 карточки, бейджи статусов, причина отказа, naturalWidth, warnbox, отмена без POST, multipart поле file, reload, X-Session-Token) | ок (7 ссылок) | Must — ок |
| TC-UI-034 | test_s8_sts_upload_missing_and_replace_car_modal_422_honest | ок («нет СТС»+Загрузить, первичная без диалога, поле photo, «Заменить СТС», честный тост ОВ-6, 422 честно, список не перезагружен) | ок (8 ссылок) | Must — ок |
| TC-UI-035 | test_s8_cars_and_docs_screens_have_no_widgets | ок (3 виджета на главной, display:none на двух экранах, возврат) | ок (4 ссылки) | Must (FR-73) — ок |
| TC-UI-036 | test_s8_admin_documents_verify_reject_preview_history | ок (pending 2 строки, фильтр, naturalWidth + X-Admin-Token, verify → история, disabled без причины, 422 честно, повторный клик, история с причиной) | ок (6 ссылок) | Must — ок |
| TC-UI-037 | test_s8_student_my_bookings_car_card_with_photo | ок (карточка, «Проверено», naturalWidth, X-Session-Token, карточка выше #bk-grid, «Подтверждена») — день недели в GIVEN: замеч. 1 | ок с оговоркой (замеч. 4) | Must — ок |
| TC-UI-038 | test_s8_bookings_section_removed_redirect_and_slot_reject | ок (без остатков, редирект с очисткой хеша, .reqslot data-k 2-14, соседний чист, disabled/причина, POST {comment}, reload) | ок (4 ссылки) | Must (FR-74) — ок |
| TC-UI-039 | test_s8_my_students_cards_counters_and_requests_subtab | ок (без сайдбар-пункта, карточки 2/«·2», счетчики, «нет — …», XSS-гигиена, подраздел, accept → 3/«·3») | ок (4 ссылки) | Must — ок |
| TC-UI-040 | test_s8_sts_gallery_replace_dialog | ок (диалог вместо file chooser, warnbox, отмена без POST, один POST, честный тост) | ок (4 ссылки) | Must (FR-71, MAJ-2) — ок |

## Проверка прогоном (факты, 2026-11-02, этот хост)

- `pytest tests/test_s8_backend.py -q` → **9 passed** (21.7s; 1 warning Starlette DeprecationWarning — не связан). Бэкенд-волна партии подтверждена живым прогоном.
- `pytest tests/test_ui_playwright.py --collect-only -q` → 50 collected; все 8 целевых функций TC-UI-033…040 (+ TC-UI-039b) собираются с точными именами.
- Исполнение UI-волны на этом хосте невозможно: chromium headless_shell не стартует — ldd: not found libatk-1.0, libatk-bridge-2.0, libXcomposite, libXdamage, libXfixes, libXrandr, libgbm, libasound, libatspi (environmental; ровно этот случай описан в docstring модуля). UI-волна здесь НЕ прогонялась; ссылка на «359 passed (integration, лог ПМ)» в кейсах — утверждение ПМ, этим ревью не перепроверялось.
- G8 (код тестов S8): `sleep` отсутствует (только упоминание запрета в docstring); TC-ID в docstring всех 17 функций; ассерты дословны кейсам (коды, поля, содержимое байтов); селекторы — стабильные id/семантические (`.nav button[data-tab=…]`, `#stu-cards .student`); изоляция — моки/фикстуры на тест, чужих данных нет.

## Итог по переносу

- В test-model/approved/add-s8-cars-docs-booking/ копируются все 17 кейсов (TC-S8BE-001…009, TC-UI-033…040).
- Возвращенных (return) кейсов нет; оригиналы в test-model/new/ не тронуты (чистка — отдельный цикл ПМ).
- Minor-замечание 1 (TC-UI-037) и обзорные пункты 2–7 — к следующему циклу ПМ, вердикт не блокируют.
