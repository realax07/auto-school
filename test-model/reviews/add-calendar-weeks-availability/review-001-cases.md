# Review-001 — ревью кейсов add-calendar-weeks-availability (итерация 001)

- Change: add-calendar-weeks-availability
- Ревьюер: qa_case_reviewer (независимый сабагент)
- Дата: 2026-11-05
- Вход (партия ПМ, H3): test-model/new/add-calendar-weeks-availability/ — 17 файлов TC-S10BE-001.md…TC-S10BE-017.md. Файлы TC-S10BE-018.md, TC-S10BE-019.md существуют в new/, в партию не входят и при ревью не открывались.
- Арбитры: openspec/changes/add-calendar-weeks-availability/specs/{instructor-availability,booking}/spec.md (точные заголовки Requirement/Scenario); design.md пакета (D1–D8, MIN-1, MIN-4, «Контракт availability», «Контракт booking», «Экземпляр и разворот серий», «Решения по НФТ»); tests/test_s10_backend.py (19 тест-функций, docstrings + тела); backend/db.py (DDL фактов UNIQUE/CHECK/индексов).
- Границы вердикта: «одобрить» только при отсутствии blocker/major; minor — неблокирующие, фиксируются.

## Вердикт: return

- Blocker: 0. Major: 1 (системное, на 15 кейсов). Minor: 5.
- Перенесено в approved: 2 кейса — TC-S10BE-001, TC-S10BE-006.
- Осталось в new/ (на доработку): 15 кейсов — TC-S10BE-002, 003, 004, 005, 007, 008, 009, 010, 011, 012, 013, 014, 015, 016, 017.
- Основание не содержательное: GIVEN/WHEN/THEN всех 17 кейсов сверены с телами тестов и совпадают; трассировка на точные заголовки спеки у всех кейсов разрешается; приоритеты обоснованы. Единственное major — системный срыв обратной трассировки rule 6: TC-ID в docstring тестов остались от прежней групповой нумерации (001…008), кейсы перенумерованы в поштучные 001…019, и для 15 кейсов docstring заявленного теста несет ЧУЖОЙ существующий TC-ID (например, test_s10_booking_legacy_without_date помечен «TC-S10BE-006», тогда как его кейс — TC-S10BE-007). Объявленный в каждом кейсе механизм связи («кейсы живут трассировкой TC-ID в docstring автотеста») для этих 15 кейсов фактически ложен. После перенумерации docstring (правка зоны qa_automation, содержательные правки кейсов не нужны) кейсы переодобряются без изменений — вердикт «одобрить» на итерации 002.

Reviewer-Delegation: deleg-qr-20261105-s10-external

## Таблица вердиктов

| Кейс | Вердикт | Замечание |
|---|---|---|
| TC-S10BE-001 | approve | minor-1: back-link верен, но TC-S10BE-001 стоит еще в docstring-ах трех других тестов (idempotent, domain, index) — шум до перенумерации |
| TC-S10BE-002 | return | major-1: docstring test_s10_migration_idempotent_noop = «TC-S10BE-001» (чужой ID) |
| TC-S10BE-003 | return | major-1 (docstring = «TC-S10BE-001»); minor-2: сценарий-якорь — сценарий отображения, кейс проверяет домен-предусловие хранилища — добавить ссылку на design D1/D2 |
| TC-S10BE-004 | return | major-1: docstring test_s10_instance_index… = «TC-S10BE-001» |
| TC-S10BE-005 | return | major-1 (docstring = «TC-S10BE-006»); minor-3: THEN «записи в БД нет» после 422 в теле теста не ассертится (только статус и ok:false) |
| TC-S10BE-006 | approve | minor-1 (аналогично 001: «TC-S10BE-006» стоит еще в docstring-ах тестов exact_instance/legacy_without_date/occupancy_race) |
| TC-S10BE-007 | return | major-1: docstring test_s10_booking_legacy_without_date = «TC-S10BE-006» |
| TC-S10BE-008 | return | major-1: docstring test_s10_booking_cross_row_same_instance_409 = «TC-S10BE-004» |
| TC-S10BE-009 | return | major-1: docstring test_s10_booking_instance_occupancy_and_race = «TC-S10BE-006» |
| TC-S10BE-010 | return | major-1 (docstring = «TC-S10BE-007»); minor-4: сценарий «Свои брони и запросы показаны ровно на своих слотах» в спеке дан с confirmed-бронью, тест покрывает свой запрос 'new' (pending) — требование покрывает оба статуса, зафиксировать в кейсе |
| TC-S10BE-011 | return | major-1: docstring test_s10_slots_date_validation_and_access = «TC-S10BE-007/008» |
| TC-S10BE-012 | return | major-1: docstring test_s10_availability_types_save_and_readback = «TC-S10BE-003» |
| TC-S10BE-013 | return | major-1: docstring test_s10_availability_validation_types = «TC-S10BE-003» |
| TC-S10BE-014 | return | major-1: docstring test_s10_availability_409_instances_with_date = «TC-S10BE-004» |
| TC-S10BE-015 | return | major-1: docstring test_s10_availability_past_ban_new_format = «TC-S10BE-005» |
| TC-S10BE-016 | return | major-1: docstring test_s10_availability_legacy_body_maj2 = «TC-S10BE-002» |
| TC-S10BE-017 | return | major-1: docstring test_s10_availability_diff_write_and_rebind = «TC-S10BE-004» |

## Сверка automated-пометок с tests/test_s10_backend.py

Все 17 кейсов помечены «автоматизирован»; имя теста в каждом кейсе существует. Столбец «docstring TC-ID» — фактический идентификатор в docstring теста.

| TC | Тест в test_s10_backend.py | docstring TC-ID | Сверка |
|---|---|---|---|
| TC-S10BE-001 | test_s10_migration_legacy_becomes_recurring | TC-S10BE-001 | ок (TC-ID и тело совпадают) |
| TC-S10BE-002 | test_s10_migration_idempotent_noop | TC-S10BE-001 | major-1: ID чужой, сценарий в docstring верный |
| TC-S10BE-003 | test_s10_slot_type_unique_and_check_domain | TC-S10BE-001 | major-1 |
| TC-S10BE-004 | test_s10_instance_index_two_dates_ok_same_date_409_domain | TC-S10BE-001 | major-1 |
| TC-S10BE-005 | test_s10_booking_exact_instance_date | TC-S10BE-006 | major-1 |
| TC-S10BE-006 | test_s10_booking_future_boundary_min1 | TC-S10BE-006 | ок (TC-ID и тело совпадают) |
| TC-S10BE-007 | test_s10_booking_legacy_without_date | TC-S10BE-006 | major-1 |
| TC-S10BE-008 | test_s10_booking_cross_row_same_instance_409 | TC-S10BE-004 | major-1 |
| TC-S10BE-009 | test_s10_booking_instance_occupancy_and_race | TC-S10BE-006 | major-1 |
| TC-S10BE-010 | test_s10_slots_week_instances_and_dedup | TC-S10BE-007 | major-1 |
| TC-S10BE-011 | test_s10_slots_date_validation_and_access | TC-S10BE-007/008 | major-1 |
| TC-S10BE-012 | test_s10_availability_types_save_and_readback | TC-S10BE-003 | major-1 |
| TC-S10BE-013 | test_s10_availability_validation_types | TC-S10BE-003 | major-1 |
| TC-S10BE-014 | test_s10_availability_409_instances_with_date | TC-S10BE-004 | major-1 |
| TC-S10BE-015 | test_s10_availability_past_ban_new_format | TC-S10BE-005 | major-1 |
| TC-S10BE-016 | test_s10_availability_legacy_body_maj2 | TC-S10BE-002 | major-1 |
| TC-S10BE-017 | test_s10_availability_diff_write_and_rebind | TC-S10BE-004 | major-1 |

Причина расхождения установлена: docstring-и и раздел tasks.md «Backend tests/test_s10_backend.py» используют прежнюю групповую нумерацию (001 миграция/домены; 002 легаси PUT; 003 PUT типы; 004 409/дифф; 005 запрет прошлого; 006 POST bookings; 007/008 GET slots), а партия кейсов раздробила эти группы в поштучные TC-S10BE-001…019. Сценарные трассировки внутри docstring при этом точны — устарели только номера.

## Покрытие сценариев спеки (в границах backend-волны)

Серверные сценарии обеих дельт покрыты кейсами партии: миграция (3/3 — TC-001/002), MAJ-1 409 + rejected + прошедшие (TC-014), легаси PUT MAJ-2 (TC-016), запрет прошлого серверно (TC-015), бронь на дате экземпляра / граница будущего / легаси POST (TC-005/006/007), кросс-строчность и гонка (TC-008/009), домены хранилища (TC-003/004), выдача экземпляров недели и дедупликация (TC-010/011/012/013). Браузерные сценарии дельт (навигация «←»/«→», подпись диапазона, «сегодня», попап-редактор, клик-ограничения прошлого) — вне зоны backend-партии, идут волной UI (TC-S10UI-…); сценарий «Изменение графика перезаписывает сохраненный» серверно покрыт тестами перепривязки, кейсы которых в партию 001–017 не входят. Кейсов без сценарного/требовательного якоря в спеке нет; ни одна ссылка не ведет на несуществующий заголовок (проверено по обеим дельтам).

## Замечания

| № | Кейс | Серьезность | Дефект | Рекомендация |
|---|---|---|---|---|
| major-1 | TC-S10BE-002…005, 007…017 (15 кейсов) | major | Срыв rule 6: TC-ID в docstring заявленного теста не совпадает с ID кейса (таблица выше); ссылка ведет на существующий, но ЧУЖОЙ кейс — например, grep «TC-S10BE-004» находит 5 тестов, из которых тест кейса TC-S10BE-004 не ни один | Перенумеровать TC-ID в docstring tests/test_s10_backend.py под партию 001…019 (правка зоны qa_automation/dev); содержательные правки кейсов не требуются; после фикса — переодобрение итерацией 002 |
| minor-1 | TC-S10BE-001, TC-S10BE-006 | minor | TC-ID этих кейсов стоит также в docstring-ах чужих тестов (у 001 — еще 3, у 006 — еще 3) — обратный поиск по ID до перенумерации дает шум | Устраняется тем же фикс major-1; кейс не возвращать |
| minor-2 | TC-S10BE-003 | minor | Якорь-сценарий «Совпадение разового… отображается одним слотом» — сценарий отображения; кейс проверяет домен-предусловие хранилища (обе строки допускаются) | Добавить в трассировку ссылку на design D1/D2 «Таблица availability» (в docstring теста она есть, в кейсе — нет) |
| minor-3 | TC-S10BE-005 | minor | THEN «дата вне weekday серии → 422, записи в БД нет»: отсутствие записи тестом не ассертится (только 422 и ok:false) | Либо добавить COUNT-ассерт в тест, либо сузить формулировку THEN кейса |
| minor-4 | TC-S10BE-010 | minor | Сценарий «Свои брони и запросы показаны ровно на своих слотах» сформулирован в спеке с подтвержденной бронью; тест покрывает свой запрос 'new' (state pending) — требование покрывает оба статуса | Зафиксировать в кейсе, что проверен статус запроса ('new'); при желании добавить confirmed-шаг в тест |
| minor-5 | TC-S10BE-015 | minor | THEN «первые три PUT → 422 „Прошедшие слоты не подлежат изменению“»: точный текст ошибки ассертится только у первого PUT, у 2-го и 3-го — только статус | Допассерт текста для 2-го/3-го PUT или смягчить формулировку |

## Проверка фактов

- Живой прогон сессии (2026-11-05, ревьюер): `.venv/bin/python -m pytest tests/test_s10_backend.py -q` → **19 passed, 1 warning in 58.65s** — заявление кейсов «19 passed» подтверждено.
- «Полный прогон: 365 passed — факт ПМ» — ссылка на факт ПМ; независимая перепроверка ревьюером (2026-11-05): `.venv/bin/python -m pytest tests/ -q --ignore=tests/test_ui_playwright.py` → **367 passed, 1 warning in 574.04s**. Точная цифра ПМ (365) не воспроизведена: расхождение ±2 на другом скоупе прогона (браузерный файл исключен; состав набора мог отличаться на момент прогона ПМ). Ключевой для партии факт — 19/19 по tests/test_s10_backend.py — подтвержден обоими прогонами.
- DDL-факты кейсов сверены с backend/db.py: UNIQUE (instructor_id, weekday, start_time, end_time, slot_date); CHECK (recurring ⇒ slot_date='', one_off ⇒ slot_date<>''); CHECK slot_type IN ('recurring','one_off'); частичный UNIQUE-индекс uq_booking_active_slot ON booking(availability_id, lesson_date) WHERE status IN ('new','confirmed'); индекс idx_availability_instructor — все присутствуют, формулировки TC-001/003/004 точны.
- Дизайн-якоря кейсов существуют в design.md: D1/D2 («Таблица availability — расширяется (перестройка, D1/D2)»), D4 («Таблица booking — только замена индекса»), D5 («Контракт availability (NFR-29; D5)»), D6 (запрет прошлого, 422), D7 (GET slots?date=), D8 («Экземпляр и разворот серий (D3, D8)»), MIN-1 (materialize_lesson_date), MIN-4 (date-валидация ДО приведения), «Решения по НФТ».
- Перекрестная ссылка TC-S10BE-003 → «API-валидации Must в TC-S10BE-013» подтверждена (кейс TC-S10BE-013 существует и покрывает заявленное).
- Негатив/границы: у каждого валидационного требования партии есть негативные кейсы (422-классы — TC-013/011/006/007; 409-классы — TC-008/009/014; граница MIN-1 «ровно NOW» — TC-006/015; rejected/прошедшие — TC-004/014; гонка — TC-009). Ось выполнена.

## Дефекты продукта (обзорно, вне вердикта)

- Дефектов продукта при сверке кейс↔тест↔спека не обнаружено: все ассерты соответствуют сценариям дельт, ослабленных проверок нет, time.sleep не используется (NOW подменяется monkeypatch backend.booking.now_moscow — соответствует design «Решения по НФТ»).
- Замечание к нумерации (эскалация ПМ, не дефект продукта): три артефакта используют две схемы нумерации одних и тех же проверок — (а) партия кейсов new/ 001…019 (поштучная), (б) docstring тестов + tasks.md (раздел «Backend tests», строки «Кейсы:» задач 1.1/2.1/3.1 — групповая 001…008). Требуется решение ПМ: канонизировать поштучную нумерацию, перенумеровать docstring-и и обновить карту задач в tasks.md; иначе последующие волны (qa_automation, G8-ревью, отчеты покрытия) будут воспроизводить расхождение.

## Статистика и итоги

| Категория | Количество | Кейсы |
|---|---|---|
| Одобрено, перенесено в approved (нет blocker/major) | 2 | TC-S10BE-001, TC-S10BE-006 |
| Возвращено в new/ (major-1; minor при наличии перечислен в таблице вердиктов) | 15 | TC-S10BE-002, 003, 004, 005, 007, 008, 009, 010, 011, 012, 013, 014, 015, 016, 017 |

Итог итерации 001: вернуть партию по одному системному major (перенумерация TC-ID в docstring тестов под партию 001…019). Содержание всех 17 кейсов (GIVEN/WHEN/THEN, трассировка на точные заголовки спеки, приоритеты, тестовые данные) проверено и признано корректным; содержательных правок кейсы не требуют — после фикса docstring-ов все 15 возвращенных кейсов переодобряются на итерации 002 без правок (одобрить), файлы кейсов при этом не изменяются.
