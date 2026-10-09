# Review-001 — ревью кейсов add-auth-cabinet (итерация 001)

- Change: add-auth-cabinet
- Ревьюер: qa_case_reviewer (независимый сабагент)
- Дата: 2026-10-09
- Вход: test-model/new/add-auth-cabinet/ — 33 файла (TC-AUTH-001…016, TC-CAB-001…010, TC-INT-001, TC-MOD-001…003, TC-NFR-001…003)
- Арбитры: test-model/checklists/add-auth-cabinet.md (CHK-1…CHK-33); openspec/changes/add-auth-cabinet/specs/{auth,cabinet}/spec.md; sdd.md §9–§13; tests/test_auth.py (автоматизированность TC-AUTH-001…016)
- Границы вердикта: «одобрить» только при отсутствии blocker/major.

## Вердикт: approve-with-notes

- Blocker: 0. Major: 2. Minor: 8.
- Перенесено в approved: 23 кейса (без blocker/major).
- Осталось в new/ (на доработку): 10 кейсов — TC-AUTH-007, TC-AUTH-008, TC-AUTH-009, TC-AUTH-011, TC-AUTH-013, TC-CAB-002, TC-CAB-005, TC-CAB-007, TC-CAB-008, TC-CAB-009.
- Основание не «return»: оба major — потери трассировки через ссылки на несуществующие TC-ID (не соответствие спеке и не невоспроизводимость), содержание проверок корректно; после вставки ссылок на фактические файлы кейсов (или явной пометки «кейс не создан, проверить на итерации авторизации браузерных кейсов») кейсы переодобряются без содержательных правок.

## Покрытие чеклиста

- CHK-1…CHK-33 — каждый покрыт ≥ 1 кейсом; кейсов без CHK-источника нет.
- Разбиение «1 кейс ↔ несколько CHK» (TC-AUTH-003: CHK-5/6/7; TC-AUTH-012: CHK-13/16; TC-AUTH-009: CHK-4/12) — с обоснованием в теле кейса, принято (одна проверочная сессия без дробления).
- Трассировка кейс→CHK→Requirement→FR сверена по всем 33 файлам; Sources совпадают с разделами спек и sdd.

## Замечания

| № | Кейс | Серьезность | Дефект | Рекомендация |
|---|---|---|---|---|
| 1 | TC-AUTH-008 | major | Потеря трассировки: шаг 4 и THEN ссылаются на «TC-AUTH-020/TC-AUTH-021» — таких кейсов в партии нет (максимум TC-AUTH-016); браузерная ветка CHK-9 в партии фактически не имеет адресата | Заменить ссылку: «браузерная часть — кейсы домена cabinet (TC-CAB-002, 401-редирект)» или на фактический ID из будущей партии |
| 2 | TC-AUTH-009 | major | Потеря трассировки: THEN ссылается на «TC-AUTH-018» — кейса не существует; фронт-часть CHK-4 покрыта TC-CAB-004 | Заменить ссылку на TC-CAB-004 |
| 3 | TC-AUTH-007 | minor | Шаг 3 («повторить после чужих успешных входов») не имеет аналога в автоматизированном тесте test_forged_token_401 (там только /me и /logout без чужих входов) — automated-пометка шире фактического покрытия теста | Либо пометить шаг 3 как ручной довесок, либо сузить статус до «automated (частично)» |
| 4 | TC-AUTH-011 | minor | automated-пометка охватывает шаги 5 (SELECT users) лишь косвенно: test_password_not_in_logs проверяет только caplog-текст, прямой SELECT из users в тесте отсутствует (в отличие от TC-AUTH-002, где SELECT есть) | Сузить статус до «automated (логи) + manual (SELECT users)» или добавить SELECT-ассерт в тест |
| 5 | TC-AUTH-013 | minor | Шаг 5 (контроль блокировки на IP-A с корректными кредами) частично дублирует TC-AUTH-012 — не дефект, но связь не указана | Добавить в тело ссылку «шаг 5 — контроль, подробный сценарий в TC-AUTH-012» |
| 6 | TC-CAB-002 | minor | Предусловие опечатка: «сервис собан» → «собран»; вариант B ссылается на «TC-CAB-003/TC-AUTH-009» — корректно, но без указания, что TC-CAB-003 — из этой же партии | Исправить опечатку; указать партию |
| 7 | TC-CAB-005 | minor | Ожидаемый результат шага 3 содержит конкатенацию «ЛИЧНЫЙ КАБИНЕТДобро пожаловать, Иван!» без разделителя — фактически текстовая интерпретация DOM (div.greet содержит текст «ЛИЧНЫЙ КАБИНЕТ» и <b> внутри); как записано, читается как одна строка | Переформулировать: «.greet содержит текст "ЛИЧНЫЙ КАБИНЕТ" и вложенный <b> "Добро пожаловать, Иван!"» |
| 8 | TC-CAB-007 | minor | automated-пометка (test_cab_page_exists_and_marker_texts + structure_matches_mockup_verbatim) проверяет HTML-файл, а не рендер под пользователем; GIVEN «ученик открыл кабинет» шире автоматизации; опечатка в источнике: «плитки-сервиски» → «плитки-сервисы» | Сузить статус до «automated (HTML-маркеры) + manual (браузер)»; исправить опечатку |
| 9 | TC-CAB-008 | minor | Ожидаемый результат ссылается на alert «Заглушка: сервис появится в следующем спринте» как на допустимое поведение — факт подтвержден (test_cab_page_keeps_mockup_stub_alert, мокап сохраняет alert), но спека говорит только «никакого сервисного действия»; alert-поведение — из мокапа, не из дельты | Добавить в источник ссылку на мокап/design поток 2 (поведение клика — как в мокапе), чтобы ожидание не выглядело изобретенным |
| 10 | TC-CAB-009 | minor | Маркер «Спроси что угодно про обучение, экзамен или ПДД...» — в мокапе многоточие «...» (три точки) внутри span.prompt; в кейсе оно есть, но шаг 3 требует посимвольной сверки «каждой непустой строки <style>», что дублирует test_cab_page_structure_matches_mockup_verbatim дословно — статус automated корректен; замечание: в маркерах кейса отсутствуют «СЕРВИСЫ», «Когда экзамен?», «Мой прогресс», «Готов ли я<br>к экзамену?», присутствующие в автотесте — список кейса уже, чем фактическая проверка (не дефект соответствия, а неполнота списка) | Дополнить список маркеров до полного набора автотеста (или сослаться на него) |

## Статистика

| Категория | Количество | Кейсы |
|---|---|---|
| Перенесено в approved (замечаний нет / только вне-блокирующие ниже minor) | 23 | TC-AUTH-001…006, TC-AUTH-010, TC-AUTH-012, TC-AUTH-014…016, TC-CAB-001, TC-CAB-003, TC-CAB-004, TC-CAB-006, TC-CAB-010, TC-INT-001, TC-MOD-001…003, TC-NFR-001…003 |
| Осталось в new/ (major: замечания 1–2; minor: 3–10) | 10 | TC-AUTH-007, TC-AUTH-008, TC-AUTH-009, TC-AUTH-011, TC-AUTH-013, TC-CAB-002, TC-CAB-005, TC-CAB-007, TC-CAB-008, TC-CAB-009 |

Примечание к статистике: в approved перенесены и кейсы без единого замечания, и кейсы, у которых замечания отсутствовали в этой итерации; кейсы с хотя бы одним замечанием любой серьезности остаются в new/ до устранения (TC-AUTH-013, TC-CAB-002 — только minor, вернутся на итерации 002).

## Сверка automated-пометок TC-AUTH-001…016 с tests/test_auth.py

| TC | Тест в test_auth.py | Пометка кейса | Сверка |
|---|---|---|---|
| TC-AUTH-001 | test_login_success_issues_token | automated | ок (токен 43 base64url, ok:true) |
| TC-AUTH-002 | test_login_checks_password_against_bcrypt_hash | automated | ок ($2b$, checkpw косвенно через успех входа; SELECT/префикс — в тесте) |
| TC-AUTH-003 | test_login_failures_identical_message | automated | ок (401, идентичная строка, AUTH_FAIL_MESSAGE) |
| TC-AUTH-004 | test_login_empty_fields_422 | automated | ок (422, «Email/Пароль: поле обязательно», без token) |
| TC-AUTH-005 | test_me_returns_user_record | automated | ок (тело user == записям, посимвольно) |
| TC-AUTH-006 | test_me_logout_without_token_401 | automated | ок (401 {ok:false} на /me и /logout) |
| TC-AUTH-007 | test_forged_token_401 | automated | частично: в тесте нет шага 3 (после чужих входов) — замечание 3 |
| TC-AUTH-008 | test_expired_token_401 | automated | ок (сдвиг time.time мимо TTL, без sleep; фронт-ветка — отдельный браузерный кейс) |
| TC-AUTH-009 | test_logout_invalidates_token | automated | ок (200 {ok:true}, затем /me 401) |
| TC-AUTH-010 | test_logout_without_valid_token_401 | automated | ок (401 {ok:false}) |
| TC-AUTH-011 | test_password_not_in_logs | automated | частично: логи покрыты, SELECT users в тесте нет — замечание 4 |
| TC-AUTH-012 | test_bruteforce_blocks_ip_without_credential_check | automated | ок (5 неудач, верные креды → 401/единый текст, без token) |
| TC-AUTH-013 | test_bruteforce_block_is_per_ip | automated | частично: тест покрывает успех с чужого IP; отказной шаг 4 и контроль шага 5 в тесте свернуты — замечание 5 |
| TC-AUTH-014 | test_bruteforce_block_expires_and_escalates | automated | ок (первая ≤ base…max, нарастание, истечение сдвигом времени, level не меняется) |
| TC-AUTH-015 | test_bruteforce_reset_after_success | automated | ок (fails == N-2, успех → 0, изолированные неудачи не блокируют) |
| TC-AUTH-016 | test_bruteforce_window_reset | automated | ок (R-BF3: окно 900 с сбрасывает fails → 1) |

## Константы спеки/дизайна, сверенные с backend/auth.py (для D2)

- _BF_MAX_FAILURES = 5; _BF_BASE_BLOCK_SECONDS = 30; _BF_MAX_BLOCK_SECONDS = 900 (15 мин); _BF_WINDOW_SECONDS = 900; _TOKEN_TTL_SECONDS = 43200 (12 ч); AUTH_FAIL_MESSAGE = «Неверный email или пароль».
- Значения в кейсах (TC-AUTH-012 «= 5», TC-AUTH-014 «30 с / 15 мин», TC-AUTH-016 «= 900», TC-AUTH-008 «12 ч») соответствуют фактическим; правило «читать из backend/auth.py, не хардкодить» соблюдено.

## Проверка фактов по другим артефактам

- tests/test_cabinet_page.py, tests/test_integration_sprint1.py, tests/test_login_modal.py — все функции, упомянутые в automated/manual-пометках TC-CAB/TC-INT/TC-MOD, существуют с точными именами.
- tests/conftest.py: ADMIN_USER=admin, ADMIN_PASSWORD=admin-pass-2026 — TC-INT-001 «admin / admin-pass-2026» верно.
- design/mocks/cabinet-student.html и login-modal.html существуют; строки TC-CAB-009/TC-MOD-003 (маркеры, «Вход», «Войдите в личный кабинет», плейсхолдеры, alt «Зарегистрироваться», «ЛИЧНЫЙ КАБИНЕТ», «Добро пожаловать, Иван!») дословно подтверждены в мокапах и frontend/index.html.
- TC-REG-001, TC-REG-013, TC-ADM-005 существуют в approved/add-registration-admin/ (трассировка TC-INT-001 корректна).
- scripts/check_auth_timing.py существует (ссылка TC-NFR-001).
- frontend/index.html: модалка m-login с id login-email/login-password/login-submit/login-error, sessionStorage['session_token'], location.href='/cabinet', res.data.error — подтверждено (TC-MOD-001/002/003).

## Прочее (вне вердикта, ПМ)

- Дефекты спеки D1–D10, учтенные в кейсах (D2 параметричность, D3 трактовка «страница входа», D10 порядок 401/422), отражены корректно; новых дефектов спеки при ревью не найдено.
- TC-NFR-002 справедливо оставлен manual: динамическая проба `' OR 1=1 --` в test_auth.py не автоматизирована (есть только совпадение отказа в test_login_failures_identical_message по другой причине); рекомендация автору — не блокирует, кейс корректен как manual.
