# Review-002 — ревью кейсов add-calendar-weeks-availability (итерация 002, проверка фикса)

- Change: add-calendar-weeks-availability
- Ревьюер: qa_case_reviewer (независимый сабагент)
- Дата: 2026-11-05
- Тип итерации: повторное ревью после фикса по итогам итерации 001 (review-001-cases.md, вердикт «return»): один системный major-001/1 — TC-ID в docstring тестов не совпадал с ID кейсов (групповая нумерация 001…008 против поштучной партии 001…019). Обещание итерации 001: после перенумерации docstring-ов все возвращенные кейсы переодобряются без правок, файлы кейсов не изменяются.
- Фикс, проверяемый итерацией: перенумерация TC-ID в docstring tests/test_s10_backend.py под партию 001…019 по маппингу «Автотест» из файлов кейсов (change add-calendar-weeks-availability; пакет add-calendar-weeks-voice / TC-S9UI в проверку не входит).
- Вход итерации 002 — 17 кейсов на approve: 15 возвращенных итерацией 001 (TC-S10BE-002…005, 007…017) + TC-S10BE-018, TC-S10BE-019 (существовали в new/ вне партии 001 и при ревью не открывались; включены указанием ПМ, ревьюются полноосно впервые). Партия целиком: 19 кейсов = 2 approved итерации 001 (TC-S10BE-001, TC-S10BE-006) + 17 настоящей итерации.
- Границы: содержательные правки кейсов не требовались и не вносились — файлы кейсов в new/ не изменялись с итерации 001 (git: единственная модификация рабочего дерева — tests/test_s10_backend.py).
- Арбитры: те же, что в итерации 001 — openspec/changes/add-calendar-weeks-availability/specs/{instructor-availability,booking}/spec.md, design.md пакета, tests/test_s10_backend.py, backend/db.py.

## Проверка фикса (механическая, 2026-11-05)

1. Маппинг «Автотест» → тест → docstring TC-ID: скрипт свел поле «Автотест» всех 19 файлов кейсов с docstring-ами всех 19 тест-функций tests/test_s10_backend.py → **19/19 совпадений «docstring TC-ID == ID кейса», 0 несовпадений**.
2. Биекция: дубликатов TC-ID в docstring-ах нет (каждый ID встречается ровно один раз), тестов без TC-S10BE-ID нет — шум обратного поиска (minor-001/1) устранен тем же фикс-ом.
3. Скоуп изменений: дифф tests/test_s10_backend.py — ровно 34 измененные строки (17 пар «старый→новый» TC-ID), все — строки docstring; тела тестов, ассерты и прочий код диффом не затронуты (проверено построчным фильтром диффа).
4. Живой прогон сессии: `.venv/bin/python -m pytest tests/test_s10_backend.py -q` → **19 passed, 1 warning in 50.08s**.
5. Первое полное ревью TC-S10BE-018/019 (в партию 001 не входили): трассировка на точные заголовки спеки подтверждена по дельте instructor-availability («### Requirement: Сохранение и восстановление графика», «#### Scenario: Изменение графика перезаписывает сохраненный», «### Requirement: Типы слотов: повторяющиеся и разовые» — существуют verbatim); GIVEN/WHEN/THEN дословно покрыты телами тестов (200 при одном PUT; ровно одна НОВАЯ строка id≠удаленной, slot_type/slot_date соответствуют; перепривязка активной брони на нового носителя, lesson_date и статус 'new' прежние, JOIN booking×availability = 1 — сирота невозможна); данные конкретны (Чт 16:00–18:00, d = четверг следующей недели, фиктивный NOW); граница MAJ-1 «замена носителя при активной брони» покрыта.

Факт для ПМ (на вердикт по кейсам не влияет): на момент ревью фикс docstring-ов находится в рабочем дереве ветки feat/s10-calendar-package **незакоммиченным** (git status: ` M tests/test_s10_backend.py`; HEAD — docs-коммит 840fe78, `git diff HEAD~1..HEAD -- tests/test_s10_backend.py` пуст; коммит «test(s10-policy): адаптация…» в refs не существует). Настоящее ревью подтверждает состояние рабочего дерева; коммит фикса до push — зона ПМ/dev, ревьюер git не трогает (границы задачи).

## Таблица вердиктов (17 кейсов)

| Кейс | Вердикт | Основание |
|---|---|---|
| TC-S10BE-002 | approve | переодобрение без правок: major-001/1 устранен — docstring test_s10_migration_idempotent_noop = «TC-S10BE-002» |
| TC-S10BE-003 | approve | переодобрение без правок (docstring test_s10_slot_type_unique_and_check_domain = «TC-S10BE-003»); minor-001/2 остается неблокирующей записью review-001 |
| TC-S10BE-004 | approve | переодобрение без правок (docstring test_s10_instance_index_two_dates_ok_same_date_409_domain = «TC-S10BE-004») |
| TC-S10BE-005 | approve | переодобрение без правок (docstring test_s10_booking_exact_instance_date = «TC-S10BE-005»); minor-001/3 — неблокирующая запись review-001 |
| TC-S10BE-007 | approve | переодобрение без правок (docstring test_s10_booking_legacy_without_date = «TC-S10BE-007») |
| TC-S10BE-008 | approve | переодобрение без правок (docstring test_s10_booking_cross_row_same_instance_409 = «TC-S10BE-008») |
| TC-S10BE-009 | approve | переодобрение без правок (docstring test_s10_booking_instance_occupancy_and_race = «TC-S10BE-009») |
| TC-S10BE-010 | approve | переодобрение без правок (docstring test_s10_slots_week_instances_and_dedup = «TC-S10BE-010»); minor-001/4 — неблокирующая запись review-001 |
| TC-S10BE-011 | approve | переодобрение без правок (docstring test_s10_slots_date_validation_and_access = «TC-S10BE-011») |
| TC-S10BE-012 | approve | переодобрение без правок (docstring test_s10_availability_types_save_and_readback = «TC-S10BE-012») |
| TC-S10BE-013 | approve | переодобрение без правок (docstring test_s10_availability_validation_types = «TC-S10BE-013») |
| TC-S10BE-014 | approve | переодобрение без правок (docstring test_s10_availability_409_instances_with_date = «TC-S10BE-014») |
| TC-S10BE-015 | approve | переодобрение без правок (docstring test_s10_availability_past_ban_new_format = «TC-S10BE-015»); minor-001/5 — неблокирующая запись review-001 |
| TC-S10BE-016 | approve | переодобрение без правок (docstring test_s10_availability_legacy_body_maj2 = «TC-S10BE-016») |
| TC-S10BE-017 | approve | переодобрение без правок (docstring test_s10_availability_diff_write_and_rebind = «TC-S10BE-017») |
| TC-S10BE-018 | approve | первое полное ревью: трассировка verbatim подтверждена, тело test_s10_availability_rebind_series_to_oneoff_new_carrier дословно покрывает GIVEN/WHEN/THEN (серия→one_off одним PUT, 200; 1 новая строка id≠старой; rebind на нового носителя, JOIN=1), docstring = «TC-S10BE-018», данные конкретны |
| TC-S10BE-019 | approve | первое полное ревью: симметрично 018 (one_off→серия), тело test_s10_availability_rebind_oneoff_to_series_new_carrier дословно покрывает GIVEN/WHEN/THEN (1 новая строка recurring slot_date=''; rebind, JOIN=1), docstring = «TC-S10BE-019» |

## Вердикт: approve

Одобрить.

Reviewer-Delegation: deleg-qr-20261104-s10-002-external

## Замечания

- Итог: одобрить — **19/19 approved** по пакету add-calendar-weeks-availability: 2 из итерации 001 (TC-S10BE-001, TC-S10BE-006) + 17 настоящей итерации (таблица выше).
- Все 17 кейсов перенесены КОПИЕЙ в test-model/approved/add-calendar-weeks-availability/ (побайтовое сравнение new/↔approved/ — идентичны; исходники в new/ не изменялись и не удалялись — та же механика, что в итерации 001 для TC-S10BE-001/006).
- Файлы кейсов с итерации 001 не изменялись — обещание итерации 001 «файлы кейсов при этом не изменяются» выполнено.
- Minor-замечания review-001 (minor-2…minor-5) остаются неблокирующими записями истории в review-001-cases.md (append-only, здесь не дублируются и не снимаются); minor-001/1 (чужие TC-ID в docstring-ах) устранен фикс-ом итерации 002 (биекция без дубликатов).
- Браузерные сценарии дельт (TC-S10UI-…) — вне зоны backend-партии, как зафиксировано в review-001; на вердикт не влияют.
- Для ПМ: зафиксированный в «Проверка фикса» факт о незакоммиченном состоянии фикса — до push/merge ветку нужно дополнить коммитом перенумерации docstring-ов, иначе на origin трассировка rule 6 останется разорванной, а CI/provenance увидят файл без исправления.
- Reviewer-Delegation — плейсхолдер, ПМ заменит на фактический id при record-review.
