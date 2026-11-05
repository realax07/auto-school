"""SQLite-слой (sdd.md §4): файл data/app.db, WAL, только параметризованные
запросы (?-плейсхолдеры, NFR-2). В БД только хранение, без логики."""
import os
import sqlite3
from pathlib import Path

_DEFAULT_DB_PATH = os.path.join("data", "app.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  surname TEXT NOT NULL,
  name TEXT NOT NULL,
  patronymic TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  phone TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS instructor_applications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  surname TEXT NOT NULL,
  name TEXT NOT NULL,
  patronymic TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  phone TEXT NOT NULL,
  address TEXT NOT NULL,
  work_format TEXT NOT NULL,
  plate TEXT NOT NULL DEFAULT '',
  license_number TEXT NOT NULL,
  license_date TEXT NOT NULL DEFAULT '',
  license_category TEXT NOT NULL,
  experience TEXT NOT NULL DEFAULT '',
  password_hash TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'waiting',
  review_comment TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS instructor_cars (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  instructor_id INTEGER NOT NULL,
  brand TEXT NOT NULL,
  model TEXT NOT NULL,
  year INTEGER NOT NULL,
  plate TEXT NOT NULL,
  transmission TEXT NOT NULL CHECK (transmission IN ('manual','automatic')),
  photo_path TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_instructor_cars_instructor
  ON instructor_cars(instructor_id);

CREATE TABLE IF NOT EXISTS availability (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  instructor_id INTEGER NOT NULL,
  weekday INTEGER NOT NULL CHECK (weekday BETWEEN 0 AND 6),
  start_time TEXT NOT NULL,
  end_time TEXT NOT NULL,
  -- Спринт 10 (add-calendar-weeks-availability, задача 1.1, D1/ADR-010):
  -- тип слота на записи — recurring (еженедельная серия weekday+время)
  -- или one_off (конкретная дата slot_date, FR-90).
  slot_type TEXT NOT NULL DEFAULT 'recurring'
    CHECK (slot_type IN ('recurring','one_off')),
  -- дата экземпляра one_off 'YYYY-MM-DD'; '' для recurring (CHECK ниже).
  slot_date TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  -- recurring ⇒ без даты, one_off ⇒ с датой (design.md «Модель данных»).
  CHECK (
    (slot_type = 'recurring' AND slot_date = '')
    OR (slot_type = 'one_off' AND slot_date <> '')
  ),
  -- Новый UNIQUE: recurring-дубли невозможны, как прежде; one_off допускает
  -- ту же пару «день недели + время» на ДРУГУЮ дату; совпадение one_off с
  -- экземпляром серии — ДВЕ строки (FR-90/FR-91, занятость едина — MAJ-1).
  UNIQUE (instructor_id, weekday, start_time, end_time, slot_date)
);
CREATE INDEX IF NOT EXISTS idx_availability_instructor
  ON availability(instructor_id);

CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  instructor_id INTEGER NOT NULL,
  student_id INTEGER NOT NULL,
  rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
  text TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (instructor_id, student_id)
);
CREATE INDEX IF NOT EXISTS idx_reviews_instructor
  ON reviews(instructor_id);

CREATE TABLE IF NOT EXISTS student_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL,
  instructor_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'new'
    CHECK (status IN ('new','accepted','denied')),
  deny_comment TEXT,
  car_id INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  decided_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_student_requests_instructor
  ON student_requests(instructor_id, status);
CREATE INDEX IF NOT EXISTS idx_student_requests_student
  ON student_requests(student_id, status);

-- Спринт 3, фикс-ветка (code-review review-001 #6, гонка дубликата):
-- частичный UNIQUE-индекс гарантирует «не более одной АКТИВНОЙ
-- (new/accepted) заявки ученика этому инструктору» на уровне БД —
-- check-then-insert в create_request не защищает от параллельных POST
-- (sync-эндпоинты FastAPI выполняются в threadpool). Отказы (denied)
-- индекс не учитывает — повторная заявка после отказа допустима (ОВ-2).
CREATE UNIQUE INDEX IF NOT EXISTS uq_student_requests_active
  ON student_requests(student_id, instructor_id)
  WHERE status IN ('new','accepted');

-- Спринт 5 (add-booking-docs, задача 4.1): бронирование слотов.
-- Гарантия единственности (NFR-8) — частичный UNIQUE-индекс ниже.
CREATE TABLE IF NOT EXISTS booking (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL,
  instructor_id INTEGER NOT NULL,
  availability_id INTEGER NOT NULL,
  lesson_date TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'new'
    CHECK (status IN ('new','confirmed','rejected')),
  reject_comment TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  decided_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_booking_instructor
  ON booking(instructor_id, status);
CREATE INDEX IF NOT EXISTS idx_booking_student
  ON booking(student_id, status);
-- Максимум одна АКТИВНАЯ (new/confirmed) бронь на ЭКЗЕМПЛЯР слота —
-- (availability_id, lesson_date); отклоненные не мешают повторному
-- запросу (ОВ-5). Спринт 10 (задача 1.1, D4): разные ДАТЫ одной
-- recurring-серии бронируются независимо; занятость ВНУТРИ одной строки
-- графика держит индекс, совпадение one_off с экземпляром серии (две
-- строки) — кросс-строчной проверкой create_booking (MAJ-1, booking.py).
CREATE UNIQUE INDEX IF NOT EXISTS uq_booking_active_slot
  ON booking(availability_id, lesson_date) WHERE status IN ('new','confirmed');

-- Спринт 8 (add-s8-cars-docs-booking, задача 1.1): статусная модель
-- документов (FR-70, ОВ-2): версии ВУ анкеты (license) и СТС авто
-- (car_sts). Канонические колонки (license_photo_path / photo_sts)
-- остаются указателем ДЕЙСТВУЮЩЕЙ версии; pending-версия живет только
-- здесь. reject_reason — причина отказа, при rejected обязательна
-- непустой (CHECK, ОВ-1). Версии не логируются и не выдаются помимо
-- авторизованных эндпоинтов (NFR-22).
CREATE TABLE IF NOT EXISTS document_versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  target_type TEXT NOT NULL CHECK (target_type IN ('license','car_sts')),
  target_id INTEGER NOT NULL,
  version INTEGER NOT NULL,
  file_path TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending','verified','rejected')),
  reject_reason TEXT
    CHECK (status <> 'rejected'
           OR (reject_reason IS NOT NULL AND reject_reason <> '')),
  uploaded_at TEXT NOT NULL,
  decided_at TEXT,
  UNIQUE (target_type, target_id, version)
);
-- ОВ-7: ровно одна ОЖИДАЮЩАЯ версия на документ (уровень схемы;
-- частичный UNIQUE — механика uq_booking_active_slot).
CREATE UNIQUE INDEX IF NOT EXISTS uq_document_versions_pending
  ON document_versions(target_type, target_id) WHERE status = 'pending';
"""

# Спринт 0–1: users.role (add-instructor-flow, задача 1.2, sdd.md §16).
_USERS_ROLE_MIGRATION = (
    "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'student'"
)

# Спринт 3 (add-instructor-student-loop): idempotent-миграции по образцу
# users.role. experience_years — стаж числом (arch-review итерация 2,
# MAJ-3: users NOT NULL DEFAULT 0, заявка — NULL); license_photo_path —
# файл ВУ анкеты (NULL = заявка без ВУ).
_COLUMN_MIGRATIONS = (
    ("users", "experience_years",
     "ALTER TABLE users ADD COLUMN experience_years INTEGER NOT NULL DEFAULT 0"),
    ("instructor_applications", "experience_years",
     "ALTER TABLE instructor_applications ADD COLUMN experience_years INTEGER"),
    ("instructor_applications", "license_photo_path",
     "ALTER TABLE instructor_applications ADD COLUMN license_photo_path TEXT"),
    # Спринт 5 (add-booking-docs, задача 2.1): фото 5 ракурсов + СТС +
    # блокировка админом. photo_path — устаревшая (новые эндпоинты ее
    # не читают и не пишут), данные не мигрируют (design.md MIN-4).
    ("instructor_cars", "photo_front",
     "ALTER TABLE instructor_cars ADD COLUMN photo_front TEXT"),
    ("instructor_cars", "photo_rear",
     "ALTER TABLE instructor_cars ADD COLUMN photo_rear TEXT"),
    ("instructor_cars", "photo_interior",
     "ALTER TABLE instructor_cars ADD COLUMN photo_interior TEXT"),
    ("instructor_cars", "photo_left",
     "ALTER TABLE instructor_cars ADD COLUMN photo_left TEXT"),
    ("instructor_cars", "photo_right",
     "ALTER TABLE instructor_cars ADD COLUMN photo_right TEXT"),
    ("instructor_cars", "photo_sts",
     "ALTER TABLE instructor_cars ADD COLUMN photo_sts TEXT"),
    ("instructor_cars", "blocked",
     "ALTER TABLE instructor_cars ADD COLUMN blocked INTEGER NOT NULL DEFAULT 0"),
    # Спринт 7 (add-car-validation-booking, задача 1.1): статус валидации.
    # ОВ-1: существующие строки получают 'validated' через DEFAULT — авто,
    # жившее до статусной модели, не исчезает из каталога и пар. CHECK
    # ограничивает значения машиной статусов draft/validating/validated.
    ("instructor_cars", "status",
     "ALTER TABLE instructor_cars ADD COLUMN status TEXT NOT NULL DEFAULT"
     " 'validated' CHECK (status IN ('draft','validating','validated'))"),
    # Спринт 9 (add-personal-data-policy, задача 3.1): фиксация согласия
    # (FR-77/FR-79, NFR-27). TEXT NULL у легаси — записи, созданные ДО
    # введения фиксации; SEED/BACKFILL НЕ ДЕЛАЕТСЯ (design.md «Модель
    # данных»: дату/версию согласия легаси-записей взять неоткуда).
    # Непустоту обоих полей у НОВЫХ записей обеспечивает сервер
    # (register.py/instructors.py заполняют в одной транзакции с INSERT).
    ("users", "consent_at",
     "ALTER TABLE users ADD COLUMN consent_at TEXT"),
    ("users", "consent_policy_version",
     "ALTER TABLE users ADD COLUMN consent_policy_version TEXT"),
    ("instructor_applications", "consent_at",
     "ALTER TABLE instructor_applications ADD COLUMN consent_at TEXT"),
    ("instructor_applications", "consent_policy_version",
     "ALTER TABLE instructor_applications ADD COLUMN"
     " consent_policy_version TEXT"),
    ("instructor_applications", "poll_token",
     "ALTER TABLE instructor_applications ADD COLUMN poll_token TEXT"),
    ("instructor_applications", "exchange_token",
     "ALTER TABLE instructor_applications ADD COLUMN exchange_token TEXT"),
)

# Спринт 9 (add-application-status-polling, задача 1.1): частичные
# UNIQUE-индексы токенов (design.md «Модель данных») — защита от дублей и
# точечный параметризованный lookup по токену. Создаются ПОСЛЕ
# _COLUMN_MIGRATIONS: индексы ссылаются на колонки, добавляемые ALTER
# TABLE, — на legacy-БД их нет до миграции, а executescript(_SCHEMA)
# выполняется раньше миграционного цикла.
_TOKEN_INDEXES = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_instructor_applications_poll_token
  ON instructor_applications(poll_token) WHERE poll_token IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_instructor_applications_exchange_token
  ON instructor_applications(exchange_token)
  WHERE exchange_token IS NOT NULL;
"""

# Спринт 10 (add-calendar-weeks-availability, задача 1.1, NFR-30, D2):
# DDL перестройки availability — РОВНО новый _SCHEMA-вид таблицы (иначе
# свежая и мигрированная БД разошлись бы в ограничениях). SQLite не снимает
# табличный UNIQUE через ALTER — таблица перестраивается. Выполняется
# ПОШАГОВО conn.execute (не executescript — тот делает неявный COMMIT и
# разорвал бы транзакцию BEGIN IMMEDIATE).
_AVAILABILITY_NEW_DDL = """
CREATE TABLE availability_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  instructor_id INTEGER NOT NULL,
  weekday INTEGER NOT NULL CHECK (weekday BETWEEN 0 AND 6),
  start_time TEXT NOT NULL,
  end_time TEXT NOT NULL,
  slot_type TEXT NOT NULL DEFAULT 'recurring'
    CHECK (slot_type IN ('recurring','one_off')),
  slot_date TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  CHECK (
    (slot_type = 'recurring' AND slot_date = '')
    OR (slot_type = 'one_off' AND slot_date <> '')
  ),
  UNIQUE (instructor_id, weekday, start_time, end_time, slot_date)
)
"""

# INSERT … SELECT — id и created_at СОХРАНЯЮТСЯ (ссылки
# booking.availability_id остаются валидными); slot_type/slot_date новые
# строки получают через DEFAULT ('recurring', '') — существующие интервалы
# становятся повторяющимися БЕЗ перезаписи данных (FR-97).
_AVAILABILITY_COPY = (
    "INSERT INTO availability_new"
    " (id, instructor_id, weekday, start_time, end_time, created_at)"
    " SELECT id, instructor_id, weekday, start_time, end_time, created_at"
    " FROM availability"
)


def _migrate_availability_slots(conn: sqlite3.Connection) -> None:
    """Спринт 10 (задача 1.1): idempotent-миграция recurring/one_off —
    guard по отсутствию колонки slot_type (повторный запуск — no-op,
    дубли невозможны, NFR-30). ОДНА транзакция BEGIN IMMEDIATE:
    перестройка availability (новый UNIQUE с slot_date) + замена
    частичного индекса брони на экземпляры (availability_id, lesson_date)
    — design.md «Модель данных», D2/D4. Существующие строки → recurring
    через DEFAULT; данные не теряются (INSERT SELECT всех строк).
    Откат отката не требуется: колонки аддитивны, старый код читает
    старые колонки без изменений."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(availability)")}
    if "slot_type" in columns:
        return
    conn.isolation_level = None
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(_AVAILABILITY_NEW_DDL)
        conn.execute(_AVAILABILITY_COPY)
        conn.execute("DROP TABLE availability")
        conn.execute("ALTER TABLE availability_new RENAME TO availability")
        # Индекс инструктора пересоздается после rebuild (design.md).
        conn.execute("DROP INDEX IF EXISTS idx_availability_instructor")
        conn.execute(
            "CREATE INDEX idx_availability_instructor"
            " ON availability(instructor_id)"
        )
        # Занятость ЭКЗЕМПЛЯРА (D4): старый индекс был по availability_id
        # без даты — заменяется на (availability_id, lesson_date) WHERE
        # active. Существующие данные совместимы (две активные брони
        # одного availability_id сегодня невозможны — старый индекс строже).
        conn.execute("DROP INDEX IF EXISTS uq_booking_active_slot")
        conn.execute(
            "CREATE UNIQUE INDEX uq_booking_active_slot"
            " ON booking(availability_id, lesson_date)"
            " WHERE status IN ('new','confirmed')"
        )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def _seed_one_document(
    conn: sqlite3.Connection,
    target_type: str,
    target_id: int,
    file_path: str,
    uploaded_at: str,
) -> None:
    """Seed ОДНОГО документа (NFR-24): строк нет → verified v1 (тот же
    файл); строки есть → ничего не менять (idempotent — повторный запуск
    init_db ничего не делает)."""
    exists = conn.execute(
        "SELECT 1 FROM document_versions"
        " WHERE target_type = ? AND target_id = ? LIMIT 1",
        (target_type, target_id),
    ).fetchone()
    if exists is not None:
        return
    conn.execute(
        "INSERT INTO document_versions (target_type, target_id, version,"
        " file_path, status, uploaded_at, decided_at)"
        " VALUES (?, ?, 1, ?, 'verified', ?, ?)",
        (target_type, target_id, file_path, uploaded_at, uploaded_at),
    )


def _seed_document_versions(conn: sqlite3.Connection) -> None:
    """Спринт 8 (задача 1.1, NFR-24): существующие документы — ВУ анкет
    (license_photo_path) и СТС авто (photo_sts) — получают verified v1
    (uploaded_at = created_at строки; решили de facto при загрузке).
    Анкета без ВУ / авто без СТС — строк не создают (пустые состояния
    сохраняются). Правило «есть документ» — НЕПУСТАЯ строка канонической
    колонки (IS NOT NULL AND <> ''); это то же правило, что в sts-ветке
    инструктор_cars и флагах has_sts (хелпер
    instructor_documents.has_canonical_file — review-003 #3: одно правило
    для NULL и пустой строки; db.py — нижний слой, хелпер домена не
    импортирует). Вызывается ПОСЛЕ _COLUMN_MIGRATIONS (колонки могут
    добавляться миграцией). SQL статический, только ?-плейсхолдеры."""
    rows = conn.execute(
        "SELECT id, license_photo_path, created_at"
        " FROM instructor_applications"
        " WHERE license_photo_path IS NOT NULL AND license_photo_path <> ''"
    ).fetchall()
    for row in rows:
        _seed_one_document(
            conn, "license", row["id"], row["license_photo_path"],
            row["created_at"],
        )
    rows = conn.execute(
        "SELECT id, photo_sts, created_at FROM instructor_cars"
        " WHERE photo_sts IS NOT NULL AND photo_sts <> ''"
    ).fetchall()
    for row in rows:
        _seed_one_document(
            conn, "car_sts", row["id"], row["photo_sts"], row["created_at"]
        )


def init_db() -> None:
    """Создание схемы (users, instructor_applications + 4 таблицы контура
    «инструктор ↔ ученик»: instructor_cars, availability, reviews,
    student_requests) + idempotent-миграции: существующие базы Спринтов
    0–2 поднимаются без пересоздания, записи остаются учениками
    (role='student', experience_years=0); Спринт 8 — таблица
    document_versions + seed verified v1 существующих документов;
    Спринт 9 — колонки токенов заявки (poll_token / exchange_token,
    NULL у исторических строк — без backfill) + частичные UNIQUE-индексы;
    Спринт 10 — перестройка availability под recurring/one_off (слоты
    легаси становятся recurring через DEFAULT, id/created_at сохраняются)
    + индекс занятости экземпляра брони (availability_id, lesson_date)."""
    conn = get_conn()
    try:
        conn.executescript(_SCHEMA)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        if "role" not in columns:
            conn.execute(_USERS_ROLE_MIGRATION)
        for table, column, ddl in _COLUMN_MIGRATIONS:
            columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
            if column not in columns:
                conn.execute(ddl)
        # Спринт 10 (задача 1.1): перестройка availability под
        # recurring/one_off + индекс занятости экземпляра (NFR-30, D2/D4).
        _migrate_availability_slots(conn)
        conn.executescript(_TOKEN_INDEXES)
        _seed_document_versions(conn)
        conn.commit()
    finally:
        conn.close()


def _db_path() -> str:
    return os.environ.get("AUTOSCHOOL_DB_PATH", _DEFAULT_DB_PATH)


def get_conn() -> sqlite3.Connection:
    """Соединение с SQLite (data/app.db, WAL, row_factory=Row)."""
    path = Path(_db_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn
