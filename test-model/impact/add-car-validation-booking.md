# Impact-анализ — change add-car-validation-booking (Спринт 7, Партия A)

- Роль: qa_impact_analyst (H5)
- Дата: 2026-10-31 (UTC)
- Вход: дельты `openspec/changes/add-car-validation-booking/specs/` (instructor-cars,
  instructor-availability, booking, instructor-documents,
  student-instructor-choice, navigation); тестовый набор `tests/`;
  трассировка TC-ID в docstring (rule 6).
- Связанные артефакты:
  - `code-reviews/add-car-validation-booking/review-001.md` (итерация 1 —
    RETURN с MAJ-1 «замена фото у validated не возвращает на валидацию»;
    итерация 3 — APPROVE, все findings per-finding закрыты; прогон
    340 passed = 338 + 2 новых: TC-S7BE-019 backend, TC-UI-032 e2e);
  - `test-model/reviews/add-car-validation-booking/review-002-design.md`
    (design check approve-with-notes; D-1 итерации 1 FIXED; e2e-волны:
    34 → 31 → финал 34/34 в составе полного сьюта);
  - `test-model/reviews/add-car-validation-booking/review-acceptance.md`
    (приемка партии, итерация 2 — ACCEPT; спектр ревью скорректирован ПМ
    на change add-car-validation-booking);
  - `sdd.md` §29 «Трассировка (Спринт 7, Партия A)» (INC-007, восстановлена ПМ);
  - qa-auto-report для этого change ОТСУТСТВУЕТ
    (`test-model/reports/` содержит отчеты только Спринтов 3/5) — прогоны
    партии зафиксированы в review-001 итерациях 1/3 и review-002-design;
    пробел отмечен для ПМ (см. раздел 8).
- Approved-кейсы партии: `test-model/approved/add-car-validation-booking/` —
  TC-S7BE-001, 001b, 003…019 (включая 019 в двух носителях — коллизия ID,
  см. раздел 5) из `tests/test_s7_backend.py` и TC-UI-030/031/032 из
  `tests/test_ui_playwright.py` (1 кейс = 1 файл = 1 тест).

## 1. MODIFIED / REMOVED дельты

### MODIFIED `instructor-cars` — «Фото автомобиля доступно владельцу» (ракурсы + СТС + комплектность)

- База: мастер-спека после Спринта 5 (5 ракурсов + СТС, авторизованные URL
  `photos{angle}`). Семантика Спринта 7: статусы draft/validating/validated
  определяют выдачу фото ученику; СТС существующего авто — через
  `POST/GET …/photo/sts` (angle='sts'); комплектность = «≥3 ракурса из 5
  И СТС» — гейт админ-подтверждения (ОВ-4).
- Воздействие на эндпоинты:
  - новые: `POST …/{id}/submit` (+алиас send-to-validation), `POST …/{id}/withdraw`
    (+алиас back-to-draft), `GET /api/admin/cars/completeness` (+алиас
    `GET /api/admin/cars`), `POST /api/admin/cars/{id}/validate`;
  - измененные: `GET /api/instructor/cars` (+`status`, +counters),
    `POST/GET …/photo/{angle}` (angle расширен значением 'sts';
    у validated замена ракурса/СТС возвращает авто в validating — MAJ-1,
    итерация 3 review-001);
  - покрытие: TC-S7BE-001…010, 013, 016, 019 (оба носителя), TC-UI-030…032.

### MODIFIED `instructor-availability` — «Сохранение и восстановление графика» (MAJ-1 409)

- Полная замена PUT ограничена наследуемым требованием MAJ-1 арх-ревью
  Спринта 5: PUT, удаляющий интервал с активной бронью ('new'/'confirmed')
  → 409 с перечнем `conflicts`, график не изменен; интервалы с только
  'rejected' бронями замене не мешают; guard внутри write-транзакции.
- Воздействие: `PUT /api/instructor/availability` — новая 409-ветка;
  регресс-контур `tests/test_s5_backend.py` (гонка PUT × booking,
  наследник TC-S5BE-025) и `tests/test_ui_playwright.py::TC-UI-008`.
  Покрытие: TC-S7BE-018.

### MODIFIED `booking` — «Подтвержденная бронь в календарях обоих» (car_status-бейджи + фото по статусу)

- Выдача авто брони дополнена `car_status` + `photo_url` (приоритет front)
  с видимость-семантикой ОВ-2: validated — фото у обоих; validating —
  фото + бейдж «Не проверено» (у владельца — с фото во всех статусах);
  draft — у ученика без `photo_url` (плейсхолдер, бронь видна); авто
  удален (car_id NULL) — `car = null` («—»), не ошибка.
- Воздействие: `GET /api/student/bookings`, `GET /api/instructor/bookings`,
  `GET /api/instructor/summary` (виджет, MIN-2 FIXED: viewer='instructor'
  явно); frontend `cabinet.html`/виджет «Занятия на сегодня».
  Покрытие: TC-S7BE-014/015, TC-UI-030.

### MODIFIED `instructor-documents` — «Раздел «Мои документы» инструктора»

- Список включает СТС ВСЕХ авто владельца независимо от статуса валидации;
  дозагрузка СТС (angle='sts') добавляет запись «на месте».
  Покрытие: TC-S7BE-017.

### MODIFIED `student-instructor-choice` — «Каталог одобренных инструкторов для ученика»

- Каталог и авто-фильтры серверно ограничены `status='validated'`;
  инструктор без validated-авто остается в каталоге с пустым блоком авто.
  Воздействие: `student_marketplace.py` (SQL WHERE), TC-S7BE-011, TC-UI-030.

### MODIFIED `navigation` / ADDED «Единая навигация по ролям без демо-заглушек»

- Сайдбар админки без заглушек «Отношения»/«Расписания» (FR-58) —
  воздействие на `admin-dashboard.html` и существующие admin-тесты;
  покрытие: TC-UI-031; регресс `test_s3_backend.py` (sdd.md §29).

### REMOVED `instructor-cars` — два Requirement

- **«Комплектность фото автомобиля проверяет администратор»**: контур
  блокировки Спринта 5 заменен статусной моделью (админ ПОДТВЕРЖДАЕТ, ОВ-4).
  Эндпоинт `POST /api/admin/cars/{id}/block` удален (TC-S7BE-010 — 404/405,
  колонка `blocked` новыми эндпоинтами не читается); регресс-наследник
  `test_s5_backend.py::test_s5_admin_block_removed_bookings_survive`
  обновлен (авто в 'validated' аранжировке).
- **«Одиночное фото автомобиля без ракурса (фото-контракт Спринта 3)»**:
  legacy `POST/GET /api/instructor/cars/{id}/photo` удален (корень
  СТС-симптома «kind=car_sts не сохраняется»); колонка `photo_path`
  устаревшая без миграции данных. По MIN-4 фото-кластер Спринта 3
  (`tests/test_s3_backend.py::TC-S3BE-008`, 12+ проверок) ОБНОВЛЕН на
  параметризованный `…/photo/front` + ассерт отсутствия legacy-маршрута —
  фиксация вместо молчаливой поломки (sdd.md §29, прим. 2). Баг 5.2
  закрыт удалением `photo_path/photo_url`-полей из выдачи плиток
  (TC-S7BE-019-bug52-tiles, задача 3.1).

## 2. Зоны воздействия

- backend: `db.py` (idempotent-миграция колонки `status TEXT NOT NULL
  DEFAULT 'validated' CHECK (draft/validating/validated)` через
  `_COLUMN_MIGRATIONS`), `instructor_cars.py` (статусная машина
  `_car_transition`, upload с возвратом validated→validating в той же
  транзакции), `instructor_admin.py`/completeness+validate,
  `student_marketplace.py` (каталог только validated), `booking.py`
  (car_status/photo_url), `instructor_availability.py` (MAJ-1 guard),
  `instructor_summary.py` (MIN-2);
- эндпоинты: перечислены в разделе 1; удаленные: `POST
  /api/admin/cars/{id}/block`, legacy `POST/GET …/photo` (одиночное);
- frontend: `instructor-dashboard.html` + `dashboard-instructor.js`
  («Мои автомобили»: бейджи статусов, модалка-галерея, mcPurgeCarUrls,
  честная копия MAJ-1(б) «вернет авто на валидацию»), `admin-dashboard.html`
  (раздел «Автомобили»: фильтр, счетчик, чек-лист, disabled-кнопка),
  `cabinet.html`/`cabinet.js` (бейджи «Проверено»/«Не проверено»,
  loadImgAuth blob-revoke), `instructor-choice.html`;
- БД/миграции: аддитивная колонка, идемпотентная (TC-S7BE-001/001b);
  существующие строки → 'validated' (ОВ-1).

## 3. Сквозные процессы

- Полный регресс `pytest tests/ -q` обязателен: миграция меняет схему
  instructor_cars для всех старых сьютов (факт итерации 3: 340 passed).
- e2e на живом uvicorn-сервере (`server`/`browser`): статусный флоу
  инструктор→админ→ученик сквозно (TC-UI-030), замена фото у validated
  (TC-UI-032).
- Идемпотентность миграции — прогон при каждом изменении `db.py`
  (TC-S7BE-001, механика users.role).
- Миграционная аранжировка существующих авто ('validated') коснулась
  аранжировок test_s5_backend: `set_car_status('validated')` переставлен
  ПОСЛЕ upload_angle (иначе замена фото сама возвращает в validating —
  найдено автором, подтверждено review-001 итерацией 3).

## 4. Таблица вердиктов (существующий набор)

| Тест (файл) | Дельта | Вердикт | Обоснование |
|---|---|---|---|
| tests/test_s3_backend.py (TC-S3BE-001…041) | REMOVED legacy /photo; MODIFIED instructor-cars | keep (обновлен в change) | TC-S3BE-008 фото-кластер переведен на `/photo/front` + ассерт отсутствия legacy-маршрута (MIN-4, sdd §29 прим. 2); CRUD/график вне зон изменения; полный прогон зеленый |
| tests/test_s5_backend.py (TC-S5BE-001…025) | MODIFIED instructor-cars (статусы), MAJ-1 availability, REMOVED block | keep (аранжировки обновлены) | `set_car_status('validated')` после upload_angle (review-001 итер. 3); `test_s5_admin_block_removed_bookings_survive` — авто 'validated', блок-эндпоинт отсутствует; MAJ-1 409-ветка — регресс TC-S7BE-018; прогон зеленый |
| tests/test_ui_playwright.py::TC-UI-008 (Календарь, PUT availability) | MAJ-1 409 | keep | Сохранение без активных броней проходит как прежде (409 только при удалении слота с 'new'/'confirmed'); в тесте броней нет |
| tests/test_ui_playwright.py::TC-UI-015/016/023/024/025 | MODIFIED instructor-cars/booking | keep | «Мои автомобили»/«Мои документы»/бронирование — дословные тексты и контракты Спринта 5 не сломаны; прогон e2e 34 passed |
| tests/test_admin*.py, test_register/test_auth/test_db | REMOVED admin block; миграция | keep | Админ-контур Спринтов 0–2 не тронут; миграция аддитивна и идемпотентна (TC-S7BE-001) |
| tests/test_bug047_*, TC-UI-019 (redirects) | — | keep | Вне зон воздействия дельты |

Итог: retire — 0; revalidate вне change — 0 (все правки существующих
тестов выполнены внутри change и зафиксированы в review-001/002).

## 5. Новые тестовые требования дельты (покрытие партией)

- Миграция/идемпотентность/CHECK-домен — TC-S7BE-001/001b (ОВ-1).
- Статусная машина: draft-INSERT, переходы, guard-и, алиасы ТЗ ПМ —
  TC-S7BE-003…006 (ОВ-3).
- Админ-контур: список/фильтр, validate-порог, 409-гuard, REMOVED block —
  TC-S7BE-007…010 (ОВ-4).
- Видимость по ОВ-2: каталог, матрица фото, СТС — TC-S7BE-011…013.
- Бронирование: бейджи/фото по статусам, удаленный авто — TC-S7BE-014/015.
- СТС существующего авто + «Мои документы» — TC-S7BE-016/017.
- MAJ-1 регресс PUT availability — TC-S7BE-018.
- MAJ-1 review-001 (validated→validating при замене) — TC-S7BE-019
  (revalidate) + TC-UI-032; баг 5.2 плитки — TC-S7BE-019 (bug 5.2).
- e2e: сквозной статусный флоу — TC-UI-030; админ-фильтр/чек-лист/навигация —
  TC-UI-031; замена фото у validated — TC-UI-032.

Коллизия TC-S7BE-019 (два теста-носителя: MAJ-1 revalidate и баг 5.2
плитки — прецедент TC-UI-024 Спринта 5): в approved-партии разнесены в
`TC-S7BE-019-revalidate-maj1.md` и `TC-S7BE-019-bug52-tiles.md`;
постоянные отдельные ID — решение ПМ/ретро.

## 6. Разрывы нумерации (НЕ закрыты тестами — на решение ПМ)

- TC-S7BE-020…025: в `sdd.md` §29 упомянут TC-S7BE-020 («регресс
  TC-S7BE-018», booking × availability MAJ-1), TC-S7BE-021…025 не
  упоминаются нигде. В `tests/test_s7_backend.py` тестов/докстрингов с
  этими ID НЕТ (фактический максимум — 019). Кейсы НЕ создавались
  (запрет на выдумывание); фактический регресс MAJ-1 покрыт TC-S7BE-018.
- TC-UI-033: упомянут в `sdd.md` §29 («навигация: сайдбар выбора
  инструктора, админ-заглушки»), в `tests/test_ui_playwright.py` теста с
  этим ID НЕТ (фактический максимум — TC-UI-032; админ-заглушки покрыты
  TC-UI-031). Кейс НЕ создавался.

## 7. Средовые требования прогона

- `AUTOSCHOOL_DB_PATH` в tmp_path, чистая БД на тест; `init_db` при старте
  (фикстура `client`, tests/conftest.py); `time.sleep` запрещен.
- `AUTOSCHOOL_UPLOADS_DIR` в tmp_path (NFR-1: вне frontend/) — фикстура
  `api` tests/test_s7_backend.py.
- e2e: playwright с `LD_LIBRARY_PATH=~/.cache/pw-libs/root/usr/lib/x86_64-linux-gnu`;
  живой сервер — репликация session-фикстур `server`/`browser`.
- Интерпретатор: /home/hermes-bot/auto-school/.venv/bin/python (3.14).

## 8. План прогонов (сверка с review-артефактами)

- Полный сьют `pytest tests/ -q`: итерация 1 — 338 passed (review-001),
  итерация 3 — 340 passed (338 + TC-S7BE-019 backend + TC-UI-032 e2e),
  EXIT=0 (review-001 «Итерация 3»).
- Отдельные прогоны: `tests/test_ui_playwright.py -q` — 34 (итерация 2) →
  31 (итерация 3 после MAJ-1) → финал 34/34 в составе полного сьюта
  (review-002-design); `tests/test_s3_backend.py`/`test_s5_backend.py` —
  в составе полного прогона, зеленые.
- qa-auto-report для change отсутствует (см. шапку) — числа взяты из
  review-001/002-design/acceptance; точных независимых прогонов s3/s5
  отдельными командами в артефактах change не зафиксировано (отмечено).
- Приемка: review-acceptance итерация 2 — ACCEPT (тесты 338/338 в формулировке
  приемки; фактический финальный хвост — 340 passed, расхождение формулировки,
  не гейт). Исключений (revalidate/retire) из прогона нет.
