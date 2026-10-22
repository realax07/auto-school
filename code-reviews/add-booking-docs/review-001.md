# Code Review — add-booking-docs, Спринт 5, Партия A (задача 6)

- Ревьюер: code_reviewer (адверсариальный режим: Саботажник / Новичок / Security)
- База: `main...HEAD`, дифф ~6338 строк (28 файлов)
- Скоуп: frontend/, backend/, tests/
- Прогон: `LD_LIBRARY_PATH=~/.cache/pw-libs/root/usr/lib/x86_64-linux-gnu .venv/bin/python -m pytest tests/ -q`
  → **304 passed, 0 failed** (5:26; включая 24 backend-S5 и интеграционные e2e)
- Версия HEAD: d3311c3 «feat(s5-frontend): разделы … e2e интеграционные TC-UI-015…023»

МЕТА: Reviewer-Delegation: deleg_spawn144324141 — spawned hermes chat session (role=code_reviewer, Спринт 5)

---

## Итог: RETURN

Блокеров нет; ядро контура (гонки броней, доступ, файлы, XSS) сделано добротно
и подтверждено тестами. Но найдены 3 MAJOR, из них один — видимый пользователю
баг виджета «Занятия на сегодня» (несовпадение шейпов фронт/бэк, не покрытый
ни одним тестом), один — регресс 500 на легаси-пути создания авто (подтвержден
пробой), один — TOCTOU-окна в PUT availability. Ничего в репозитории не правилось.

---

## Что проверено и подтверждено (без замечаний)

1. **Гонки броней (фокус 1)** — реальная гарантия на месте:
   - миграция `backend/db.py`: таблица `booking` + частичный
     `CREATE UNIQUE INDEX uq_booking_active_slot ON booking(availability_id) WHERE status IN ('new','confirmed')` —
     идемпотентно (test_s5_migration_booking_table_and_indexes / _idempotent_keeps_rows);
   - `booking.create_booking`: `BEGIN IMMEDIATE` до SELECT слота → INSERT,
     `sqlite3.IntegrityError → ROLLBACK → 409 «Слот уже занят»`; предварительный
     SELECT — только UX, гарантией объявлен индекс (честно задокументировано);
   - потокобный тест `test_s5_booking_race_two_students_one_409` (барьер, 2
     потока) проверяет ровно `[200, 409]` и 1 активную запись в БД — не вакуумный;
   - confirm/reject: `UPDATE … WHERE id=? AND status='new'` + rowcount →
     повторное решение 409; reject требует непустой комментарий → 422, слот
     освобождается (ОВ-5). accept/reject guard по статусу подтвержден.
2. **Доступ (фокус 2)** — матрица сходится с design.md:
   - слоты/брони: только ученик accepted-пары (`_pair_accepted`), чужой
     инструктор слота → 404, инструктор не существует → 404, прямой вызов
     без пары → 403 (test_s5_slots_access_guard);
   - ракурсы фото: владелец + ученик accepted-пары; заблокированное авто
     ученику → 404 (ОВ-1/MIN-2); СТС — только владелец, ученику (в т.ч. из
     пары) → 403 (FR-44/NFR-7, test_s5_car_photo_access_matrix_and_sts).
     Ученик СТС не видит — соответствует design.md, ученический cabinet.html
     СТС вообще не запрашивает (grep чистый);
   - «Мои документы»/файлы документов: doc_id парсится серверно, владелец
     проверяется на каждом запросе (email анкеты / instructor_id авто),
     чужой/несуществующий → 404 (test_s5_documents_file_access);
   - админ-эндпоинты (completeness/block) — за X-Admin-Token → 401 без него.
3. **Файлы (фокус 3)** — `uploads.save_image` получил whitelist kinds
   (`license/cars/car_photo/car_sts`, иначе ValueError) — kind не приходит
   от пользователя в путях; имя файла `<uuid>.<ext>` генерится сервером —
   path traversal невозможен; magic bytes JPEG/PNG + ≤5 МБ (`_MAX_IMAGE_BYTES`)
   до записи на диск; angle→колонка — через статические словари
   `_ANGLE_UPDATE_SQL`/`_ANGLE_COLUMNS`, без конкатенации SQL
   (test_s5_new_modules_no_sql_concatenation — grep-контроль).
4. **Модульность (фокус 4)** — `backend/booking.py` (479 строк) и
   `backend/instructor_documents.py` — отдельные домены по директиве
   Заказчика; существующие модули расширены, не раздуты (booking-логика
   в instructor_availability вынесена в `blocking_bookings`/`conflict_error_response`,
   импортируемые из booking.py — без цикла). Дашборды выросли
   (instructor-dashboard.html 1589 строк) из-за решения BUG-047 «разделы
   внутри кабинетов вместо standalone-страниц» — согласуется с
   arch-review/картой, но близко к границе разумного (см. NIT-3).
5. **XSS перенесенного рендера (фокус 5)** — весь новый/перенесенный рендер
   (bookings инструктора, «Мои брони», «Мои автомобили», документы, виджеты)
   строится через DOM-хелперы `node()/el()` с `textContent`; пользовательские
   строки (ФИО, reject_comment, brand/model/plate) через innerHTML не проходят;
   статические обвязки в innerHTML — константы. Комментарий отказа вставлен
   через `createTextNode`. e2e на XSS есть (test_student_choice_xss_…),
   design-guard test_s4_pages_tag_balance на балансе тегов.
6. **e2e интеграционные (фокус 6)** — не вакуумные: test_s5_booking_flow_…
   гоняет живой бэкенд (одобрение инструктора → график → пара → слоты →
   бронь → confirm → 409 повтором, проверка REST-состояния после UI);
   test_s5_car_full_kit_… — комплектность и видимость авто ученику;
   301-редиректы /my-cars, /my-requests (backend/app.py) покрыты
   test_bug047_*_redirects.
7. **Баг 5.2 (фокус 7)** — подтвержден: `list_cars` отдает `photos{angle}` /
   `sts_url` / `photo_url` как URL авторизованных эндпоинтов (не файловые
   пути data/uploads), фронт грузит их blob-ом с X-Session-Token
   (mcLoadImg); test_s5_bug_5_2_photo_survives_relogin проверяет перезагрузку
   списка и повторный вход с новыми байтами файла.
8. Удаление legacy-эндпоинов: standalone my-cars/my-requests убраны,
   301 на разделы кабинетов, old-хэши открывают раздел напрямую.

---

## Findings

### MAJOR

**M-1. frontend/instructor-dashboard.html:667–668 — шейп-мисматч виджета «Занятия на сегодня» (FR-49): фронт читает несуществующие поля.**
`loadSummary()` рендерит `l.student` и `l.time`, а `GET /api/instructor/summary`
(backend/instructor_summary.py, Спринт 5) возвращает `student_full_name`,
`start_time`, `end_time` (плюс `lesson_date`, `booking_id`, `car`). При наличии
подтвержденных броней на сегодня виджет показывает на каждой строке
заглушку «Занятие» с ПУСТЫМ временем — т.е. фича FR-49 видимо сломана.
Тестами не покрыт: оба e2e, трогающие summary, мокают `today_lessons: []`
(test_ui_playwright.py:745, 826), а test_s5_summary_today_lessons проверяет
только API-шейп. Новичок, копирующий старый код виджета, это пронес.
Фикс: `l.student_full_name`, `l.start_time.slice(0,5)+'–'+l.end_time.slice(0,5)`
(+ e2e с непустым today_lessons или живой сценарий).

**M-2. backend/instructor_cars.py `create_car`, легаси-JSON путь — необработанный ValidationError/TypeError → 500 (регресс 422).**
До Спринта 5 тело разбирал Pydantic-параметр хендлера → 422 от фреймворка.
Теперь при не-multipart: `data = CarPayload(**body)` без обработки —
`{"year": "abc"}` поднимает pydantic ValidationError, `[1,2]` — TypeError;
оба уходят в необработанное исключение → 500 на клиентский ввод.
Подтверждено пробой через TestClient (traceback ValidationError: «Input
should be a valid integer … input_value='abc'»). Комментарий в списке броней
(404-трасса) тут не при чем: это чистый клиентский ввод. Фикс: try/except
ValidationError (+ не-JSON тело) → 422 «по первому полю», как докстритит сам
эндпоинт; покрыть тестом.

**M-3. backend/instructor_availability.py `put_availability` — TOCTOU: проверка конфликтов (MAJ-1) вне транзакции записи; окно для брони-сироты.**
`blocking_bookings()` выполняется SELECT-ом ДО начала неявной write-транзакции
(DELETE), т.е. без `BEGIN IMMEDIATE`. create_booking сериализуется через
BEGIN IMMEDIATE, но PUT с ним не соревнуется на участке
«проверка → DELETE → INSERT». Последовательность: инструктор прошел проверку
(конфликтов нет) → ученик успел создать бронь на удаляемый слот (успешно:
UNIQUE видит только брони, а слот еще жив) → PUT удаляет availability.
У `booking` НЕТ FK на availability (колонка голая INTEGER), поэтому бронь-
сирота молча исчезает из обоих списков (JOIN availability), а
confirm/reject по ней — 404 навсегда. Вероятность мала, но это ровно тот
класс гонок, который Спринт 5 объявил закрытым (NFR-8). Фикс дешевый:
`BEGIN IMMEDIATE` перед blocking_bookings в той же транзакции, что и
DELETE/INSERT (сериализуется с create_booking), в перспективе — FK.

### MINOR

**m-1. backend/instructor_documents.py `_sts_documents` — докстринг противоречит коду; легаси-авто без СТС молча невидимы в «Мои документы».**
Докстринг обещает «авто без СТС — с флагом has_file=False», код делает
`if not row["photo_sts"]: continue`. При этом JSON-путь create_car (без СТС)
остался как «путь совместимости Спринта 3» — такие авто можно создавать и
сейчас, и они никогда не появятся в разделе (спека FR-45: «СТС по каждому
автомобилю»; сценарий «СТС автомобилей отображаются»). Админ увидит дыру
только через completeness. Фикс: показывать запись с has_file=false и
подсказкой, либо исключить создание авто без СТС (закрыть легаси-путь) —
но тогда честно обновить докстринг и спеку.

**m-2. frontend/instructor-dashboard.html:1438–1441 — мертвый рендер `b.comment`.**
Ветка «Ваш комментарий при отказе» в списке броней инструктора читает
`b.comment`, но `GET /api/instructor/bookings` не возвращает ни `comment`,
ни `reject_comment` — ветка никогда не выполняется. Либо отдавать свой
reject_comment в инструкторском списке, либо убрать мертвый код (сейчас он
вводит в заблуждение следующего разработчика; ученический кабинет свой
`reject_comment` показывает корректно — cabinet.html:724).

**m-3. backend/instructor_cars.py `upload_car_photo_angle` — проверка владения, запись файла и UPDATE разнесены; ответ «ok» при 0 строк.**
Между `_own_car` и финальным `UPDATE` авто может быть удалено (другой таб
или параллельный запрос): UPDATE вернет rowcount=0, но эндпоинт ответит
`{"ok": True, "url": …}`, а свежезаписанный файл останется сиротой на диске.
Фикс: проверять rowcount (или повторный EXISTS) и убирать файл при промахе.

**m-4. Бронь-сироты невидимы без диагностики (смежное с M-3).**
`my_bookings` / `instructor_bookings` / summary используют INNER JOIN
availability: при любой потере слота (легаси-замены графика до MAJ-1,
TOCTOU из M-3) бронь молча исчезает из интерфейсов у обеих сторон — ни
флага, ни «слот canceled». Минимум — LEFT JOIN с деградацией «слот удален»,
либо запрет физического DELETE слотов с бронями на уровне схемы/логики.

### NIT

**n-1.** backend/instructor_cars.py, докстринг `get_car_photo`: лишний символ
`»` перед закрывающими кавычками (`ответ image/*.»"""`) — опечатка этого диффа.

**n-2.** Сквозные `student_id or 0` / `instructor_id or 0` (booking.py,
instructor_cars.py, instructor_summary.py): require_role гарантирует int,
`or 0` — шум, маскирующий реальный None, если контракт guards когда-нибудь
изменится. Убрать или заменить явным assert-ом в guards.

**n-3.** instructor-dashboard.html (1589 строк) — уже монолит; следующие
спринты с разделами стоит планировать как вынос секций в модули/бандлы,
иначе директива «не раздувать» начнет нарушаться на фронте (на бэке она
соблюдена точно).

**n-4.** `GET /api/instructor/documents/{id}/file` — просмотр и скачивание
это один ответ без Content-Disposition; браузерный «скачать» для <img>-строк
остается на усмотрение клиента. Спековый сценарий «скачивание доступно»
формально выполняется, но если Заказчик ждет файл-аттачмент — добавлять
`?download=1` с Content-Disposition: attachment (вне критического пути).

---

## Ответы на прямые вопросы постановки

- **UNIQUE+транзакция реально в миграции?** Да: `uq_booking_active_slot`
  (частичный, WHERE status IN ('new','confirmed')) в db.py-схеме; BEGIN
  IMMEDIATE + IntegrityError→409 — в create_booking; гонка проверена
  потокобным тестом. НО: у PUT availability та же дисциплина не выдержана (M-3).
- **IntegrityError→409?** Да, с ROLLBACK и без записи (проверено тестом и
  кодом).
- **accept/reject guard по статусу?** Да: `WHERE id=? AND status='new'` +
  rowcount→409; reject без комментария → 422, статус не меняется.
- **Слоты/брони только участники accepted-пары?** Да (серверно, 403/404).
- **Студент видит СТС?** Нет — по design (FR-44/NFR-7): только владелец,
  ученику из пары 403; фронт ученика СТС не запрашивает. Соответствует.
- **kinds через uploads.py, MIME/размер/traversal?** Да: whitelist kinds,
  sniff_image (magic bytes + 5 МБ) до записи, uuid-имена — traversal
  исключен; angle→колонка без конкатенации SQL.
- **XSS перенесенного рендера?** Чисто: textContent/createTextNode,
  innerHTML только для статических обвязок.
- **e2e не вакуумные?** Основные — нет (живой бэкенд, сквозные сценарии,
  проверки REST-состояния и computed style). Исключение — виджет today_lessons:
  e2e мокают его пустым, чем и пропустили M-1.
- **5.2: photo_path в плитках реально отдается?** Да, авторизованные URL
  эндпоинтов (`photos{angle}`/`sts_url`), перепроверено тестом на повторный
  вход + байты файла; путь data/uploads клиенту не отдается.

## Верификация

- Полный прогон: **304 passed** (0 failed), 5:26 — команда из постановки,
  exit 0.
- Проба M-2 выполнена на этом worktree отдельным скриптом (TestClient,
  чистая tmp-БД): подтвержден необработанный ValidationError на
  `year:"abc"` (500-класс вместо 422).
- Место M-1 подтверждено сопоставлением кода фронт/бэк и отсутствием
  какого-либо теста с непустым today_lessons.
- Ничего в репозитории не изменено (единственные записи — этот файл отчета).

Reviewer-Delegation: deleg_spawn144324141 — spawned hermes chat session (role=code_reviewer, Спринт 5)

---

# Итерация 2 — переревью коммита 5eed848

- Дифф итерации: `git diff HEAD~1..HEAD` (коммит дева «fix(s5): итерация 2
  по review-001 — M-1/M-2/M-3 + MINOR»; 7 файлов, +224/−14)
- Прогон: `export LD_LIBRARY_PATH=~/.cache/pw-libs/root/usr/lib/x86_64-linux-gnu && /home/hermes-bot/auto-school/.venv/bin/python -m pytest tests/ -q`
  → **307 passed, 0 failed** (5:11; было 304 — +3 новых теста), exit 0.

## Итог: APPROVE

Все три MAJOR закрыты корректно, оба затронутых MINOR — тоже; новые тесты
по построению падают на старом коде (разобрано ниже). Ничего нового не
внесено: дифф точечный, вне находок логика не тронута. В репозитории
ничего не правилось (единственные записи — секции этого отчета).

## Per-finding

**M-1 — FIXED.** `loadSummary()` (frontend/instructor-dashboard.html:664–671)
теперь читает реальные поля бэка: `l.student_full_name` и окно
`(l.start_time||'').slice(0,5)+'–'+(l.end_time||'').slice(0,5)` — точно шейп
`GET /api/instructor/summary` (instructor_summary.py). Покрытие добавлено по
существу: новый e2e `test_instructor_summary_today_lessons_widget_renders_real_shape`
(TC-UI-024) мокает НЕпустой `today_lessons` строго по шейпу бэка
(student_full_name/start_time/end_time «ЧЧ:ММ:СС») и проверяет отрисовку
`b` = «Ольга Нечаева» и `small` = «10:00–11:30». На старом коде (`l.student`
→ заглушка «Занятие», `l.time` → пусто) оба expect падают — тест не вакуумный.

**M-2 — FIXED.** backend/instructor_cars.py: новый `_car_payload_from_body()` —
не-объект (список/строка/null) и `TypeError` → 422 «Тело: ожидается JSON-объект
автомобиля»; `ValidationError` → 422 по первому полю с человекочитаемой меткой
(`_CAR_FIELD_LABELS`: «Год: некорректное значение» и т.д.). Легаси-путь
create_car использует хелпер вместо голого `CarPayload(**body)` — 500 на
клиентском вводе больше недостижим. Тест
`test_s5_create_car_json_invalid_body_422_not_500` (TC-S5BE-024) гоняет оба
класса (`year:"abc"`, `[1,2]`), проверяет 422 + «Год» в тексте ошибки и
ОТСУТСТВИЕ записи в БД. На старом коде оба запроса — 500 (ValidationError/
TypeError не обработаны) → тест падает. Подтверждено кодом, прогон зеленый.

**M-3 — FIXED.** backend/instructor_availability.py `put_availability`:
`conn.isolation_level = None; BEGIN IMMEDIATE` теперь ДО `blocking_bookings()`,
проверка конфликтов и DELETE/INSERT — в одной write-транзакции, COMMIT в конце,
ROLLBACK на ветке конфликтов. Так как `create_booking` сериализуется тем же
`BEGIN IMMEDIATE` (booking.py:270–271), а SQLite — однописатель, окно
«проверка → удаление» закрыто: конкурирующая бронь либо блокируется локом
PUT ( OperationalError на стороне ученика), либо успела до захвата лока —
и тогда PUT видит ее в blocking_bookings → 409, слот жив. Схемно `booking`
по-прежнему без FK на availability, но сирота теперь невыводима.
Тест `test_s5_put_availability_vs_booking_race_no_orphan` (TC-S5BE-025):
monkeypatch `blocking_bookings` вставляет бронь отдельным соединением
(timeout=0.25) ровно в окне «сразу после проверки»; инвариант проверяется в
обеих ветках (бронь успела → 409 + слот жив + бронь жива; бронь заблокирована
→ 200 + записей 0) плюс главный ассерт `not (bookings and not slot_alive)`.
На старом коде проверка шла в autocommit → INSERT успевает, PUT молча удаляет
слот под живой бронью → `bookings=1, slot_alive=0` → инвариант падает.
Тест детерминированный (не спит на таймингах — окно задано самим патчем).

**m-1 — FIXED.** Докстринг `_sts_documents` приведен в соответствие с кодом:
«авто БЕЗ СТС (легаси-JSON-путь Спринта 3) ЯВНО пропускаются (continue) —
в „Мои документы" не попадают (видимы админу через completeness)». Из двух
предложенных в review-001 опций выбрана честная документация текущего
поведения — принято (поведение не менялось, спека-вопрос остается за
Заказчиком, блокирующим не является).

**m-2 — FIXED.** `GET /api/instructor/bookings` теперь отдает
`reject_comment` (только при status='rejected', иначе None); фронт
`bkRenderList` читает `b.reject_comment` вместо мертвого `b.comment`,
вставка по-прежнему через `createTextNode` (XSS-дисциплина не тронута).
Тест-ассерт добавлен в `test_s5_reject_requires_comment_and_frees_slot`:
инструкторский список возвращает тот же reject_comment, что и ученический
view. Нюанс (не блокирует): метка «Комментарий ученика» в этой ветке теперь
гарантированно недостижима (reject_comment отдается только при rejected) —
остаточный мертвый литерал, NIT-класса.

## Новое в диффе — ничего сверх находок

Проверены все 7 файлов диффа вне фиксов: правки не меняют поведение остальных
путей (booking.py — только SELECT + докстринг; instructor_documents.py —
только докстринг; n-1-опечатка `»` в докстринге get_car_photo заодно
исправлена). Новых MAJOR/MINOR не обнаружено. Два некритичных наблюдения
в копилку (не требуют итерации):

- **n-5 (наблюдение).** `put_availability`: если `BEGIN IMMEDIATE` не сможет
  взять write-лок за busy_timeout (по умолчанию 5 c, конкурент — долгоживущий
  писатель), будет необработанный OperationalError → 500. Это тот же класс
  поведения, что и до фикса (DELETE под чужим локом падал так же), регрессом
  не является; при желании — try/except → 503/409 «занято, повторите».
- Остальные NIT итерации 1 (n-2 `or 0`, n-3 монолит дашборда, n-4
  Content-Disposition, m-3/m-4) в постановке итерации 2 не значились —
  не проверялись как требования, состояния не менялось.

## Верификация итерации 2

- Полный прогон из постановки: **307 passed, 0 failed** (5:11), exit 0.
- Каждое «FIXED» подтверждено чтением кода на HEAD (5eed848), а не только
  результатами тестов; для каждого нового теста разобрано, почему он падает
  на d3311c3 (см. per-finding).
- Ничего в репозитории не изменено (единственные записи — этот файл отчета).

Reviewer-Delegation: deleg_spawn20261022211418c06711 — spawned hermes chat session (role=code_reviewer, Спринт 5, итерация 2)
