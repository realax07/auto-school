# Impact-анализ — change add-booking-docs (Спринт 5, Партия A, задача 15)

- Роль: qa_impact_analyst (H5)
- Дата: 2026-10-22 (UTC)
- Вход: дельты `openspec/changes/add-booking-docs/specs/` (booking,
  instructor-cars, instructor-documents); тестовый набор `tests/`;
  трассировка TC-ID в docstring (rule 6).
- Связанные артефакты:
  - `code-reviews/add-booking-docs/review-001.md` (итерации 1–2: M-1/M-2/M-3,
    m-1/m-2; итог итерации 2 — APPROVE; отдельный review-002 не создавался —
    переревью оформлено итерацией 2 внутри review-001);
  - `test-model/reviews/add-booking-docs/review-001-design.md` (D-1 →
    итерация 2 approve-with-notes);
  - `test-model/reviews/add-booking-docs/review-acceptance.md` (приемка
    партии, approve);
  - `test-model/reports/qa-auto-report-add-booking-docs.md` (прогоны:
    полный сьют 307 passed; test_s5_backend 26 passed; e2e 34 passed).
- Approved-кейсы партии: `test-model/approved/add-booking-docs/` —
  TC-S5BE-001…025 (+011b, M-ревью-кейсы 024/025) из `tests/test_s5_backend.py`
  и TC-UI-015/016/019/023/024/025 из `tests/test_ui_playwright.py`
  (1 кейс = 1 файл = 1 тест).

## 1. MODIFIED / REMOVED дельты

### MODIFIED (дельта `instructor-cars/spec.md`)

- **«Фото автомобиля доступно владельцу»** — база: мастер-спека
  `openspec/specs/instructor-cars/spec.md` (перенесена в мастер из архивного
  пакета `openspec/changes/archive/2026-10-22-add-instructor-student-loop`
  при его архивации). Новая семантика: 5 обязательных ракурсов (ОВ-1),
  независимое хранение/замена, фото переживает перезагрузку и повторный вход
  (снятие бага 5.2), JPEG/PNG по содержимому ≤5 МБ. Воздействие:
  - эндпоинты: `GET /api/instructor/cars` (новые поля `photos{angle}`,
    `has_sts`, `sts_url`, `blocked` — URL авторизованных эндпоинтов вместо
    файловых путей); новые `POST/GET /api/instructor/cars/{id}/photo/{angle}`,
    `GET /api/instructor/cars/{id}/sts`; легаси `POST/GET
    /api/instructor/cars/{id}/photo` (одиночное фото, Спринт 3) сохранены;
  - существующие тесты: `tests/test_s3_backend.py` (TC-S3BE, авто/фото) —
    легаси-пути на месте, прогон зеленый → keep;
  - страницы: «Мои автомобили» пересобрана внутри дашборда инструктора
    (BUG-047), standalone `/my-cars` удален → 301 (см. REMOVED-поведение UI).

### MODIFIED (без формальной дельта-записи — пометка для ПМ): `instructor-availability`

Мастер-спека `openspec/specs/instructor-availability/spec.md` описывает
«Сохранение и восстановление графика» как безусловную полную замену. В этом
change поведение ограничено через ADDED Requirement booking-дельты
**«Замена графика при активных бронях отклоняется»**: брони ссылаются на слоты
(`booking.availability_id`; FK схемно нет — защита транзакциями), PUT
`/api/instructor/availability` при удалении слота с бронью 'new'/'confirmed'
→ 409 с перечнем `conflicts`; гонка PUT × create_booking закрыта
BEGIN IMMEDIATE (M-3 review-001, TC-S5BE-025). Формального MODIFIED-файла
`specs/instructor-availability/` в change-пакете нет — расхождение
«мастер-семантика vs новое поведение» закроется слиянием дельт при
архивации; отмечено для sa/archive_change.

### REMOVED

- REMOVED Requirements в дельтах отсутствуют (все три дельты —
  MODIFIED/ADDED only).
- Удаленное UI-поведение (не Requirement): standalone-страницы `/my-cars`,
  `/my-requests` убраны → 301 на разделы кабинетов (BUG-047, директива
  Заказчика). Покрыто `test_bug047_*_redirects` и TC-UI-019.

## 2. Зоны воздействия

- backend: `db.py` (миграция: таблица `booking` + индексы, в т.ч. частичный
  `uq_booking_active_slot`; колонки `photo_front/rear/interior/left/right`,
  `photo_sts`, `blocked` в `instructor_cars` — идемпотентно), новые модули
  `booking.py`, `instructor_documents.py`, `instructor_summary.py`,
  расширенные `instructor_cars.py`, `instructor_availability.py`,
  `uploads.py` (whitelist kinds, magic bytes, ≤5 МБ);
- эндпоинты: `POST /api/instructor/cars` (новый основной контракт — multipart
  с обязательным СТС; JSON-путь остался как совместимость, M-2: 422 вместо
  500), `GET /api/instructor/bookings` (+`reject_comment`, m-2),
  `GET /api/instructor/summary` (+`today_lessons`, шейп — основа M-1),
  новые `GET /api/student/instructors/{id}/slots`,
  `POST/GET /api/student/bookings`,
  `POST /api/instructor/bookings/{id}/confirm|reject`,
  `GET /api/admin/cars/completeness`, `POST /api/admin/cars/{id}/block`,
  `GET /api/instructor/documents[/{doc_id}/file]`;
- frontend: `instructor-dashboard.html` (разделы «Мои автомобили»,
  «Мои документы», «Бронирования», виджет «Занятия на сегодня» — шейп
  `student_full_name/start_time/end_time`), `cabinet.html` («Мои брони»,
  модалка брони скрыта по умолчанию — D-1), `app.py` (301-редиректы);
- БД/миграции, файловое хранилище `data/uploads/{car_photo,car_sts,license}`
  (в тестах — `AUTOSCHOOL_UPLOADS_DIR` в tmp).

## 3. Сквозные процессы

- Полный регресс `pytest tests/ -q` — обязателен (миграция затрагивает схему
  для всех старых сьютов; факт: 307 passed).
- e2e на живом uvicorn-сервере (`server`/`browser` фикстуры) — гонки
  броней/блокировки проверяются сквозно, не только TestClient.
- Миграционная идемпотентность — отдельный кейс (TC-S5BE-002), прогон при
  каждом изменении `db.py`.

## 4. Таблица вердиктов (существующий набор)

| Тест (файл) | Дельта | Вердикт | Обоснование |
|---|---|---|---|
| tests/test_s3_backend.py (TC-S3BE-001…041: авто CRUD, одиночное фото, график) | MODIFIED instructor-cars; ограничение PUT availability | keep | Легаси-эндпоинты сохранены (JSON-создание — путь совместимости; одиночное `/photo` живо); в аранжировках старых тестов активных броней нет → 409-ветка PUT не срабатывает. Подтверждено прогоном 307 passed (qa-auto-report, раздел 1) |
| tests/test_instructor_dashboard.py (TC-FR18D/FR19D/FR21D/FR22D) | MODIFIED instructor-cars (дашборд) | keep | Контракт `/api/instructor/dashboard` и навигация не менялись; новые разделы добавлены, дословные тексты старых страниц не тронуты (тесты зеленые) |
| tests/test_instructor_pages.py (wiring apply/cabinet) | — | keep | Вне зон воздействия дельты |
| tests/test_ui_playwright.py::TC-UI-008 («Календарь», PUT availability) | ограничение PUT availability | keep | Сохранение без активных броней проходит как прежде (409 только при удалении слота с 'new'/'confirmed'); в тесте броней нет |
| tests/test_ui_playwright.py::TC-UI-015, TC-UI-016 | MODIFIED instructor-cars (BUG-047-лейаут) | revalidate → выполнено (keep) | Тесты пересобраны в этом же change под встроенный раздел и новый multipart-контракт; трассировка перенесена с add-s3-frontend-links на add-booking-docs (история переноса ID — замечание 2 qa-auto-report, вынесено на ретро). Обновление проведено, релизный прогон зеленый |
| tests/test_ui_playwright.py::TC-UI-005/009/010/011 (дашборд/запросы/выход/админка) | MODIFIED instructor-cars (лейаут) | keep | Сайдбар/навигация сохранены; новые разделы не ломают старые сценарии (прогон зеленый) |
| tests/test_admin*.py, test_register/test_auth/test_db | REMOVED (нет)/ADDED booking | keep | Дельта не затрагивает контракты Спринтов 0–2; миграция аддитивна (TC-S5BE-001/002) |
| tests/test_bug048_* (TC-UI-020…022) | ADDED instructor-documents/СТС | keep | Анкетная загрузка ВУ не менялась; СТС-валидация — отдельный поток «Моих автомобилей» |

Итог: retire — 0; revalidate (pending_update) — 0 на момент прогона
(единственный revalidate TC-UI-015/016 закрыт в этом же change).

## 5. Новые тестовые требования дельты (покрытие партией)

- Миграции и идемпотентность — TC-S5BE-001/002.
- СТС при создании (FR-44), валидация файла (NFR-9) — TC-S5BE-003/004,
  TC-UI-015/023.
- 5 ракурсов: хранение/замена/ошибки/матрица доступа, баг 5.2 —
  TC-S5BE-005…008, TC-UI-016, TC-UI-024-integration.
- Комплектность и блокировка (ОВ-1, MIN-2) — TC-S5BE-009/010,
  TC-UI-024-integration.
- «Мои документы» (FR-45) — TC-S5BE-011/011b/012.
- Слоты/брони (FR-46…FR-50), гонки (NFR-8), границы lesson_date (MIN-1),
  confirm/reject (ОВ-2), сироты (MAJ-1/M-3), MIN-3, FR-49/ОВ-6 —
  TC-S5BE-013…022/025, TC-UI-025, TC-UI-024-widget-m1 (M-1).
- NFR-10 (параметризованный SQL) — TC-S5BE-023.
- BUG-047-лейаут/back-ссылки — TC-UI-015/019.

Коллизия TC-UI-024 (два теста — виджет M-1 и интеграция «авто»): в
approved-партии разнесены в файлы `TC-UI-024-widget-m1.md` и
`TC-UI-024-integration.md`; постоянный отдельный ID (например, TC-UI-026) —
решение ПМ/ретро (замечание 1 qa-auto-report).

## 6. Средовые требования прогона

- `AUTOSCHOOL_DB_PATH` в tmp_path, чистая БД на тест; `init_db` при старте
  (фикстура `client`, tests/conftest.py); `time.sleep` запрещен.
- `AUTOSCHOOL_UPLOADS_DIR` в tmp_path (NFR-1: вне frontend/) — фикстура `api`
  в tests/test_s5_backend.py; гонки — `threading.Barrier`, без таймингов
  (окно M-3 задается monkeypatch, не сном).
- e2e: playwright с `LD_LIBRARY_PATH=~/.cache/pw-libs/root/usr/lib/x86_64-linux-gnu`
  (браузерные либы); живой сервер — репликация session-фикстуры `server`.
- Интерпретатор: /home/hermes-bot/auto-school/.venv/bin/python (3.14).

## 7. План прогонов (сверка с tasks.md/qa-auto-report)

- Полный сьют `pytest tests/ -q` — 307 passed (факты: qa-auto-report,
  review-001 итерация 2). Исключений (revalidate/retire) из прогона нет.
- Отдельные прогоны `tests/test_s5_backend.py -q` (26 passed) и
  `tests/test_ui_playwright.py -q` (34 passed) — как волны партии.
- Расхождений плана SA и вердиктов нет; единственная открытая пометка —
  формализация MODIFIED-дельты `instructor-availability` (раздел 1) и
  TC-ID коллизии TC-UI-024 — решения ПМ, не гейты.
