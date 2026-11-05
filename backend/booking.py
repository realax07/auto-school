"""booking.py — бронирование слотов (Спринт 5, задача 4.1; design.md
блок C, домен booking — отдельный модуль по директиве Заказчика).

GET  /api/student/instructors/{id}/slots — график инструктора с состояниями
     слотов (только для ПРИНЯТОЙ пары — серверная проверка, FR-46);
     Спринт 10 (задача 2.1, D7): + параметр ?date= — ЭКЗЕМПЛЯРЫ недели
     (разворот серий в даты, дедупликация one_off×серия — MAJ-1 (б));
POST /api/student/bookings               — запрос брони (FR-47); Спринт 10:
     + опциональная date (точный экземпляр, FR-95), проверка будущего
     «начало > NOW (МСК)» (FR-96, NFR-31), КРОСС-СТРОЧНАЯ проверка
     экземпляра ВНУТРИ BEGIN IMMEDIATE (MAJ-1 арх-ревью Спринта 10 (б));
GET  /api/student/bookings               — «Мои брони»/календарь ученика
     (FR-48, FR-49);
GET  /api/instructor/bookings            — входящие брони инструктора
     (FR-48, FR-49);
POST /api/instructor/bookings/{id}/confirm — подтверждение (FR-48);
POST /api/instructor/bookings/{id}/reject  — отклонение, комментарий
     обязателен (ОВ-2, FR-48);
POST /api/instructor/bookings/{id}/cancel  — отмена ПОДТВЕРЖДЕННОЙ брони
     (BUG-049), без комментария;
helper blocking_bookings — согласование PUT availability с активными
     бронями (MAJ-1): уровень ЭКЗЕМПЛЯРОВ (дата+время) — слоты с бронями
     'new'/'confirmed', НЕ покрытые новым графиком (серий или one_off),
     блокируют замену → 409 с перечнем, содержащим дату (FR-92);
     прошедшие экземпляры (начало < NOW) не блокируют (D8).

Гонки (NFR-8): POST запроса брони — транзакция BEGIN IMMEDIATE + частичный
UNIQUE-индекс uq_booking_active_slot (db.py, Спринт 10: по ЭКЗЕМПЛЯРУ —
availability_id + lesson_date): INSERT при уже занятом экземпляре →
IntegrityError → откат → 409 «Слот уже занят», записи нет. Совпадение
one_off с экземпляром серии (две строки графика) закрывается КРОСС-
СТРОЧНОЙ проверкой в той же транзакции — single-writer сериализует с PUT
availability (наследование M-3 review-001). Предварительный SELECT —
только UX-уровень, гарантиями являются проверка+индекс.

lesson_date (MIN-1): материализуется при создании брони — ближайшая дата
weekday слота по ЛОКАЛЬНОЙ ДАТЕ СЕРВЕРА (datetime.date.today()); Спринт
10: поле date запроса задает ТОЧНУЮ дату экземпляра; для one_off —
slot_date. Граница «прошедший/будущий» (FR-93/FR-96, NFR-31) — по
now_moscow() (ЕДИНЫЙ МСК-хелпер, MIN-2 арх-ревью: не наивный now() —
прецедент MIN-4 review-001).

Единственность решения (FR-48): confirm/reject — UPDATE … WHERE id=? AND
status='new' с проверкой rowcount (0 → 409), повторное решение → 409.
Связь «ученик принят» — student_requests.status='accepted' (ADR-004).
Блокировка авто (MIN-2) контур брони НЕ затрагивает: существующие брони
видны, новые брони не запрещаются.

SQL — только параметризованный (NFR-10←NFR-3); ФИО/токены не логируются.
"""
import datetime
import re
import sqlite3

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import backend.db as db
from backend.guards import _error, full_name, require_role

router = APIRouter()

_ACTIVE_STATUSES = ("new", "confirmed")

_WEEKDAY_NAMES = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")

# Строгий ISO YYYY-MM-DD (форму проверяет регекс, существование дня —
# date.fromisoformat; «2026-02-30» → None — MIN-4 арх-ревью).
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# NOW — московское время (NFR-31, MIN-2): UTC+3 явно, единая точка с
# клиентом (клиент вычисляет МСК как UTC+3 — design «Клиентский контракт»).
_MOSCOW_TZ = datetime.timezone(datetime.timedelta(hours=3))


class BookingCreatePayload(BaseModel):
    # Дефолты вместо Pydantic-required — валидация в хендлере.
    availability_id: int = 0
    # Спринт 10 (FR-95): опциональная дата экземпляра 'YYYY-MM-DD'.
    date: str = ""


class RejectPayload(BaseModel):
    comment: str = ""


def now_moscow() -> datetime.datetime:
    """Текущее время МСК (NFR-31, MIN-2 арх-ревью) — ЕДИНЫЙ серверный
    хелпер границы «ПРОШЕДШИЙ = начало < NOW» (FR-93/FR-96). Не наивный
    now()/today(): прецедент MIN-4 review-001 — наивная локальная дата в
    UTC-контейнере смещает границу на 3 часа. TZ=Europe/Moscow закреплена
    деплоем (задача 4.1), граница — UTC+3 явно."""
    return datetime.datetime.now(_MOSCOW_TZ)


def parse_iso_date(value: str) -> datetime.date | None:
    """Строгий парсер 'YYYY-MM-DD': форма — регекс, несуществующий
    календарный день (2026-02-30) → None (MIN-4 арх-ревью)."""
    if not _DATE_RE.match(value or ""):
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


def instance_start(lesson_date: str, start_time: str) -> datetime.datetime:
    """Начало экземпляра (дата 'YYYY-MM-DD' + время 'HH:MM') по МСК —
    единая точка сравнения с now_moscow() (NFR-31; решение «начавшийся»
    — по НАЧАЛУ слота, не по концу)."""
    day = datetime.date.fromisoformat(lesson_date)
    hour, minute = (int(part) for part in start_time.split(":"))
    return datetime.datetime(
        day.year, day.month, day.day, hour, minute, tzinfo=_MOSCOW_TZ,
    )


def local_today() -> datetime.date:
    """Локальная дата сервера (MIN-1) — единое правило для lesson_date
    и «today» виджета «Занятия на сегодня»."""
    return datetime.date.today()


def materialize_lesson_date(weekday: int) -> str:
    """Ближайшая дата weekday (0=пн) от локальной даты сервера (MIN-1):
    сегодняшний weekday → сегодня, иначе ближайшие впереди."""
    today = local_today()
    days_ahead = (weekday - today.weekday()) % 7
    return (today + datetime.timedelta(days=days_ahead)).isoformat()


def _pair_accepted(
    conn: sqlite3.Connection, student_id: int, instructor_id: int
) -> bool:
    """Связь «ученик принят» (Спринт 3): активная accepted-заявка."""
    return conn.execute(
        "SELECT 1 FROM student_requests"
        " WHERE student_id = ? AND instructor_id = ? AND status = 'accepted'",
        (student_id, instructor_id),
    ).fetchone() is not None


def _car_brief(
    conn: sqlite3.Connection,
    car_id: int | None,
    viewer: str = "student",
) -> dict | None:
    """Авто пары для календарей (MIN-3): car_id NULL/удален → None («—»),
    не ошибка. Спринт 7 (задача 6.1): + car_status (флаг бейджа ОВ-2) и
    photo_url (первый доступный ракурс, приоритет front); draft → у
    ученика БЕЗ photo_url (плейсхолдер на клиенте, бронь видна), владелец
    видит свои фото во всех статусах. blocked (MIN-2, устаревшая колонка)
    календарь НЕ читает — видимость регулируется status."""
    if not car_id:
        return None
    row = conn.execute(
        "SELECT id, brand, model, year, transmission, status,"
        " photo_front, photo_rear, photo_interior, photo_left, photo_right"
        " FROM instructor_cars WHERE id = ?",
        (car_id,),
    ).fetchone()
    if row is None:
        return None
    photo_url = None
    if viewer == "instructor" or row["status"] in ("validating", "validated"):
        for angle in ("front", "rear", "interior", "left", "right"):
            if row[f"photo_{angle}"] is not None:
                photo_url = f"/api/instructor/cars/{car_id}/photo/{angle}"
                break
    return {
        "id": row["id"],
        "brand": row["brand"],
        "model": row["model"],
        "year": row["year"],
        "transmission": row["transmission"],
        "car_status": row["status"],
        "photo_url": photo_url,
    }


def _pair_car(
    conn: sqlite3.Connection,
    student_id: int,
    instructor_id: int,
    viewer: str = "student",
) -> dict | None:
    """Авто пары «следует за перекреплением» (ОВ-6): car_id берется из
    ТЕКУЩЕЙ accepted-заявки на момент выдачи; viewer — правило photo_url
    по статусу (задача 6.1)."""
    row = conn.execute(
        "SELECT car_id FROM student_requests"
        " WHERE student_id = ? AND instructor_id = ? AND status = 'accepted'",
        (student_id, instructor_id),
    ).fetchone()
    if row is None:
        return None
    return _car_brief(conn, row["car_id"], viewer)


def blocking_bookings(
    conn: sqlite3.Connection,
    instructor_id: int,
    rows,
) -> list[dict]:
    """MAJ-1 (Спринт 10, задача 2.1/3.1 — политика (б) арх-ревью): уровень
    ЭКЗЕМПЛЯРОВ. Активная бронь ('new'/'confirmed') → экземпляр
    (weekday, start_time, end_time, date=booking.lesson_date); конфликт,
    если НОВЫЙ график не покрывает (дата, время): покрытие — one_off с
    этой датой+временем ИЛИ серия с этим weekday+временем, совпадение
    интервалов — ТОЧНОЕ (design «Сознательные ограничения»).
    rows — полный НОВЫЙ график: кортежи (weekday, start_time, end_time,
    slot_type, slot_date); легаси-форма (weekday, start_time, end_time)
    трактуется как recurring (до перехода PUT на полные ключи — задача
    3.1). Экземпляры с началом < NOW (МСК) не конфликтуют (прошедшее не
    блокирует замену — история фиксируется бронями, D8); слоты с только
    'rejected' бронями не мешают (design). Пустой список → замена
    допустима."""
    now = now_moscow()
    keep = {
        row if len(row) == 5 else (*row, "recurring", "") for row in rows
    }
    db_rows = conn.execute(
        "SELECT b.lesson_date, b.status, a.start_time, a.end_time"
        " FROM booking AS b JOIN availability AS a ON a.id = b.availability_id"
        " WHERE a.instructor_id = ? AND b.status IN (?, ?)",
        (instructor_id, *_ACTIVE_STATUSES),
    ).fetchall()
    conflicts: dict[tuple[str, str, str], list[str]] = {}
    for row in db_rows:
        if instance_start(row["lesson_date"], row["start_time"]) < now:
            continue
        date = row["lesson_date"]
        weekday = datetime.date.fromisoformat(date).weekday()
        covered = (
            (weekday, row["start_time"], row["end_time"], "one_off", date)
            in keep
            or (weekday, row["start_time"], row["end_time"], "recurring", "")
            in keep
        )
        if not covered:
            key = (date, row["start_time"], row["end_time"])
            conflicts.setdefault(key, []).append(row["status"])
    return [
        {
            "weekday": datetime.date.fromisoformat(date).weekday(),
            "start_time": start,
            "end_time": end,
            "date": date,
            "booking_statuses": sorted(statuses),
        }
        for (date, start, end), statuses in sorted(conflicts.items())
    ]


def _slot_conflict_text(conflicts: list[dict]) -> str:
    parts = [
        "{} {} {}–{} ({})".format(
            _WEEKDAY_NAMES[c["weekday"]],
            c.get("date") or "",
            c["start_time"],
            c["end_time"],
            ", ".join(c["booking_statuses"]),
        ).replace("  ", " ")
        for c in conflicts
    ]
    return (
        "В графике есть слоты с активными бронями: "
        + "; ".join(parts)
        + ". Сначала решите брони (подтвердите или отклоните)"
    )


def conflict_error_response(conflicts: list[dict]) -> JSONResponse:
    """409 PUT availability (MAJ-1) с ПЕРЕЧНЕМ затронутых слотов
    (weekday, интервал, статус брони) — график не изменен."""
    return JSONResponse(
        status_code=409,
        content={
            "ok": False,
            "error": _slot_conflict_text(conflicts),
            "conflicts": conflicts,
        },
    )


# --- Ученик -----------------------------------------------------------------


@router.get("/api/student/instructors/{instructor_id}/slots")
def instructor_slots(
    instructor_id: int,
    date: str = "",
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """График инструктора для ПРИНЯТОГО ученика (FR-46, FR-50): серверная
    проверка пары — иначе 403 (в т.ч. прямой вызов мимо UI); инструктор
    не существует/не одобрен → 404.

    Без параметра date — легаси-ответ БЕЗ ИЗМЕНЕНИЙ (старый UI и
    существующие тесты): {ok, slots:[{id, weekday, start_time, end_time,
    state}]} — состояния: free / busy (чужая ИЛИ своя подтвержденная
    активная бронь, кем — не раскрывается) / pending (СВОЙ запрос 'new').

    С параметром date (Спринт 10, задача 2.1, D7 — FR-94/FR-95): любой
    день отображаемой недели, сервер приводит к понедельнику этой недели;
    date не ISO YYYY-MM-DD или несуществующий календарный день → 422
    {ok:false} ДО приведения (MIN-4 арх-ревью). Ответ: {ok, week:{monday,
    sunday}, instances:[{availability_id, date, weekday, start_time,
    end_time, state}]} — разворот серий в ЭКЗЕМПЛЯРЫ недели (recurring —
    дата серии в этой неделе, включая прошедшие дни — для прошлых недель
    ученик видит свои статусы; one_off — только если slot_date попадает в
    неделю); ДЕДУПЛИКАЦИЯ совпавших экземпляров (recurring×one_off,
    одинаковые date+start_time+end_time) — ОДИН instance с
    availability_id строки-носителя с приоритетом one_off (FR-90), state
    агрегируется по всем покрывающим строкам (MAJ-1: занятость экземпляра
    едина — бронь через вторую строку отклонена create_booking-ом);
    pending старше busy (наследование состояний, поднятое с
    availability_id на (id, date))."""
    student_id, err = require_role(x_session_token, "student")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        instructor = conn.execute(
            "SELECT id FROM users WHERE id = ? AND role = 'instructor'",
            (instructor_id,),
        ).fetchone()
        if instructor is None:
            return _error(404, "Инструктор не найден")
        if not _pair_accepted(conn, student_id or 0, instructor_id):
            return _error(403, "Нет принятой пары с этим инструктором")

        intervals = conn.execute(
            "SELECT id, weekday, start_time, end_time FROM availability"
            " WHERE instructor_id = ? ORDER BY weekday, start_time, end_time",
            (instructor_id,),
        ).fetchall()
        active = conn.execute(
            "SELECT b.availability_id, b.lesson_date, b.student_id, b.status,"
            " a.start_time, a.end_time"
            " FROM booking AS b JOIN availability AS a ON a.id = b.availability_id"
            " WHERE b.instructor_id = ? AND b.status IN (?, ?)",
            (instructor_id, *_ACTIVE_STATUSES),
        ).fetchall()

        if not date:
            # Легаси-ответ (без изменений): состояния по строке графика.
            mine = {row["availability_id"]: row["status"] for row in active
                    if row["student_id"] == student_id}
            busy = {row["availability_id"] for row in active}
            slots = [
                {
                    "id": row["id"],
                    "weekday": row["weekday"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "state": (
                        "pending" if mine.get(row["id"]) == "new"
                        else "busy" if row["id"] in busy
                        else "free"
                    ),
                }
                for row in intervals
            ]
            return {"ok": True, "slots": slots}

        # Спринт 10 (D7/MIN-4): валидация ДО приведения к понедельнику.
        day = parse_iso_date(date)
        if day is None:
            return _error(
                422, "Дата: ожидается существующая дата в формате ГГГГ-ММ-ДД"
            )
        monday = day - datetime.timedelta(days=day.weekday())
        sunday = monday + datetime.timedelta(days=6)

        rows = conn.execute(
            "SELECT id, weekday, start_time, end_time, slot_type, slot_date"
            " FROM availability WHERE instructor_id = ?"
            " ORDER BY weekday, start_time, end_time",
            (instructor_id,),
        ).fetchall()

        # Экземпляры недели: recurring — дата серии в этой неделе;
        # one_off — только на slot_date, если попала в неделю.
        # Совпадение (date+start+end) — ОДИН instance, availability_id
        # строки-носителя с приоритетом one_off (FR-90): recurring
        # добавляются первыми, one_off перезаписывают носителя.
        instances: dict[tuple[str, str, str], dict] = {}
        for row in rows:
            if row["slot_type"] != "recurring":
                continue
            day_iso = (
                monday + datetime.timedelta(days=row["weekday"])
            ).isoformat()
            instances.setdefault(
                (day_iso, row["start_time"], row["end_time"]),
                {
                    "availability_id": row["id"],
                    "date": day_iso,
                    "weekday": row["weekday"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                },
            )
        for row in rows:
            if row["slot_type"] != "one_off":
                continue
            if not (monday.isoformat() <= row["slot_date"] <= sunday.isoformat()):
                continue
            weekday = datetime.date.fromisoformat(row["slot_date"]).weekday()
            instances[row["slot_date"], row["start_time"], row["end_time"]] = {
                "availability_id": row["id"],
                "date": row["slot_date"],
                "weekday": weekday,
                "start_time": row["start_time"],
                "end_time": row["end_time"],
            }

        # state агрегируется по ВСЕМ покрывающим строкам: активные брони
        # группируются по экземпляру (lesson_date + точное время строки).
        by_instance: dict[tuple[str, str, str], list[tuple[int, str]]] = {}
        for row in active:
            key = (row["lesson_date"], row["start_time"], row["end_time"])
            by_instance.setdefault(key, []).append(
                (row["student_id"], row["status"])
            )
        result = []
        for key, instance in instances.items():
            instance_bookings = by_instance.get(key, [])
            instance["state"] = (
                "pending"
                if any(sid == student_id and status == "new"
                       for sid, status in instance_bookings)
                else "busy" if instance_bookings
                else "free"
            )
            result.append(instance)
        result.sort(key=lambda i: (i["date"], i["start_time"], i["end_time"]))
        return {
            "ok": True,
            "week": {"monday": monday.isoformat(), "sunday": sunday.isoformat()},
            "instances": result,
        }
    finally:
        conn.close()


@router.post("/api/student/bookings")
def create_booking(
    data: BookingCreatePayload,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Запрос брони (FR-47, NFR-8; Спринт 10 — FR-95/FR-96, NFR-31, MAJ-1):
    слот не существует → 404; нет принятой пары с инструктором слота →
    403; date не соответствует слоту → 422 (recurring — день недели
    серии, one_off — ровно slot_date); экземпляр начался/прошел (начало
    ≤ NOW МСК) → 422 «Слот уже начался или прошел» (FR-96 — строго
    больше NOW, независимо от клиента); экземпляр занят → 409 «Слот уже
    занят» без записи. Без date — легаси-вызов: materialize_lesson_date
    (ближайшая дата weekday, MIN-1), для one_off — slot_date.

    Транзакция BEGIN IMMEDIATE (single-writer, сериализация с PUT
    availability — наследование M-3 review-001): КРОСС-СТРОЧНАЯ проверка
    экземпляра (MAJ-1 арх-ревью Спринта 10, политика (б)) ДО INSERT —
    активная бронь ('new'/'confirmed') ЛЮБОЙ строки графика этого
    инструктора, покрывающая (lesson_date, start_time, end_time) → 409;
    совпадение one_off с экземпляром серии (две строки) не дает двух
    активных броней на один физический экземпляр. Частичный
    UNIQUE-индекс (availability_id, lesson_date) остается гарантией
    ВНУТРИ строки: параллельный INSERT проигравшего роняет индекс, а не
    портит данные. Совпадение интервалов — ТОЧНОЕ (дата+start+end);
    частично пересекающиеся интервалы разных строк одним экземпляром не
    считаются (наследование, design «Сознательные ограничения»)."""
    student_id, err = require_role(x_session_token, "student")
    if err is not None:
        return err
    if data.availability_id <= 0:
        return _error(422, "Слот: поле обязательно")

    requested_date = None
    if data.date:
        requested_date = parse_iso_date(data.date)
        if requested_date is None:
            return _error(
                422, "Дата: ожидается существующая дата в формате ГГГГ-ММ-ДД"
            )

    conn = db.get_conn()
    try:
        # Пара (FR-46/FR-47): совсем нет принятой пары → 403; слот не
        # существует либо принадлежит НЕ инструктору пары → 404.
        pairs = {
            row["instructor_id"]
            for row in conn.execute(
                "SELECT DISTINCT instructor_id FROM student_requests"
                " WHERE student_id = ? AND status = 'accepted'",
                (student_id,),
            ).fetchall()
        }
        if not pairs:
            return _error(403, "Нет принятой пары с инструктором")

        # Гонка (NFR-8): запись лочится до конца транзакции —
        # сериализация с PUT availability и параллельными POST
        # (проверки и INSERT в одной write-транзакции).
        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        slot = conn.execute(
            "SELECT id, instructor_id, weekday, start_time, end_time,"
            " slot_type, slot_date FROM availability WHERE id = ?",
            (data.availability_id,),
        ).fetchone()
        if slot is None or slot["instructor_id"] not in pairs:
            conn.execute("ROLLBACK")
            return _error(404, "Слот не найден")

        # Точная дата экземпляра (FR-95, D4): поле date запроса; легаси —
        # materialize_lesson_date как прежде; one_off — slot_date.
        if requested_date is not None:
            if slot["slot_type"] == "one_off":
                if requested_date.isoformat() != slot["slot_date"]:
                    conn.execute("ROLLBACK")
                    return _error(
                        422, "Дата: разовый слот бронируется на свою дату"
                    )
            elif requested_date.weekday() != slot["weekday"]:
                conn.execute("ROLLBACK")
                return _error(422, "Дата: не попадает на день недели слота")
            lesson_date = requested_date.isoformat()
        elif slot["slot_type"] == "one_off":
            lesson_date = slot["slot_date"]
        else:
            lesson_date = materialize_lesson_date(slot["weekday"])

        # Будущее (FR-96, NFR-31): начало экземпляра СТРОГО больше NOW
        # (МСК) — иначе 422 независимо от клиента; решение «начавшийся»
        # — по началу слота (не по концу). Легаси-путь материализует
        # ≥ сегодня; кейс «сегодня, но уже начался» отклоняется.
        if instance_start(lesson_date, slot["start_time"]) <= now_moscow():
            conn.execute("ROLLBACK")
            return _error(422, "Слот уже начался или прошел")

        # Кросс-строчная проверка экземпляра (MAJ-1, политика (б)) — В ТОЙ
        # ЖЕ транзакции, ДО INSERT: активная бронь любой строки графика
        # инструктора, покрывающая запрошенный экземпляр (дата+время), →
        # 409 «Слот уже занят», записи нет.
        busy = conn.execute(
            "SELECT 1 FROM booking AS b"
            " JOIN availability AS a ON a.id = b.availability_id"
            " WHERE a.instructor_id = ? AND b.status IN (?, ?)"
            " AND b.lesson_date = ? AND a.start_time = ? AND a.end_time = ?"
            " LIMIT 1",
            (slot["instructor_id"], *_ACTIVE_STATUSES, lesson_date,
             slot["start_time"], slot["end_time"]),
        ).fetchone()
        if busy is not None:
            conn.execute("ROLLBACK")
            return _error(409, "Слот уже занят")

        try:
            cur = conn.execute(
                "INSERT INTO booking (student_id, instructor_id,"
                " availability_id, lesson_date, status)"
                " VALUES (?, ?, ?, ?, 'new')",
                (student_id, slot["instructor_id"], data.availability_id,
                 lesson_date),
            )
        except sqlite3.IntegrityError:
            # Гарантия внутри строки: частичный UNIQUE
            # (availability_id, lesson_date) — параллельный проигравший.
            conn.execute("ROLLBACK")
            return _error(409, "Слот уже занят")
        booking_id = cur.lastrowid
        conn.execute("COMMIT")
    finally:
        conn.close()
    return {
        "ok": True,
        "booking_id": booking_id,
        "status": "new",
        "lesson_date": lesson_date,
    }


def _booking_row(conn: sqlite3.Connection, booking_id: int):
    return conn.execute(
        "SELECT b.id, b.student_id, b.instructor_id, b.status,"
        " b.reject_comment, b.lesson_date, b.created_at, b.decided_at,"
        " a.weekday, a.start_time, a.end_time"
        " FROM booking AS b JOIN availability AS a ON a.id = b.availability_id"
        " WHERE b.id = ?",
        (booking_id,),
    ).fetchone()


@router.get("/api/student/bookings")
def my_bookings(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """«Мои брони»/календарь ученика (FR-48, FR-49): статус, дата/время
    слота, инструктор (ФИО), авто пары (следует за перекреплением, ОВ-6;
    удален → null — корректное пустое состояние, MIN-3), reject_comment
    при отклонении (ОВ-2)."""
    student_id, err = require_role(x_session_token, "student")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT b.id, b.instructor_id, b.status, b.reject_comment,"
            " b.lesson_date, b.created_at, b.decided_at,"
            " a.weekday, a.start_time, a.end_time"
            " FROM booking AS b JOIN availability AS a"
            " ON a.id = b.availability_id"
            " WHERE b.student_id = ?"
            " ORDER BY b.lesson_date, a.start_time, b.id",
            (student_id,),
        ).fetchall()
        bookings = []
        for row in rows:
            instructor = conn.execute(
                "SELECT surname, name, patronymic FROM users WHERE id = ?",
                (row["instructor_id"],),
            ).fetchone()
            bookings.append({
                "id": row["id"],
                "status": row["status"],
                "lesson_date": row["lesson_date"],
                "weekday": row["weekday"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "instructor_full_name": (
                    full_name(instructor) if instructor else ""
                ),
                "car": _pair_car(conn, student_id or 0, row["instructor_id"]),
                "reject_comment": (
                    row["reject_comment"] if row["status"] == "rejected" else None
                ),
                "created_at": row["created_at"],
                "decided_at": row["decided_at"],
            })
    finally:
        conn.close()
    return {"ok": True, "bookings": bookings}


# --- Инструктор -------------------------------------------------------------


@router.get("/api/instructor/bookings")
def instructor_bookings(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Входящие брони ТОЛЬКО этого инструктора (FR-48): ученик (ФИО),
    слот (дата/время), статус, авто пары (null при удалении — MIN-3);
    reject_comment при отклонении (ОВ-2) — рендерится в разделе
    «Бронирования» как «Ваш комментарий при отказе»."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT b.id, b.student_id, b.status, b.reject_comment,"
            " b.lesson_date, b.created_at, b.decided_at,"
            " a.weekday, a.start_time, a.end_time"
            " FROM booking AS b JOIN availability AS a"
            " ON a.id = b.availability_id"
            " WHERE b.instructor_id = ?"
            " ORDER BY b.lesson_date, a.start_time, b.id",
            (instructor_id,),
        ).fetchall()
        bookings = []
        for row in rows:
            student = conn.execute(
                "SELECT surname, name, patronymic FROM users WHERE id = ?",
                (row["student_id"],),
            ).fetchone()
            bookings.append({
                "id": row["id"],
                "status": row["status"],
                "lesson_date": row["lesson_date"],
                "weekday": row["weekday"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "student_full_name": full_name(student) if student else "",
                "car": _pair_car(
                    conn, row["student_id"], instructor_id or 0, "instructor"
                ),
                "reject_comment": (
                    row["reject_comment"] if row["status"] == "rejected" else None
                ),
                "created_at": row["created_at"],
                "decided_at": row["decided_at"],
            })
    finally:
        conn.close()
    return {"ok": True, "bookings": bookings}


@router.post("/api/instructor/bookings/{booking_id}/confirm")
def confirm_booking(
    booking_id: int,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Подтверждение (FR-48, NFR-8): только своя бронь → иначе 404;
    только 'new' → иначе 409; БЕЗ комментария (ОВ-2). Атомарно: guard
    AND status='new' + rowcount; конкурирующая бронь на слоте невозможна
    (частичный UNIQUE держит слот этой бронью)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        row = _booking_row(conn, booking_id)
        if row is None or row["instructor_id"] != instructor_id:
            return _error(404, "Бронь не найдена")
        cur = conn.execute(
            "UPDATE booking SET status = 'confirmed', decided_at = datetime('now')"
            " WHERE id = ? AND status = 'new'",
            (booking_id,),
        )
        if cur.rowcount == 0:
            return _error(409, "Бронь: решение уже принято")
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "status": "confirmed"}


@router.post("/api/instructor/bookings/{booking_id}/cancel")
def cancel_booking(
    booking_id: int,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Отмена ПОДТВЕРЖДЕННОЙ брони (BUG-049, скрины Заказчика 2026-10-23):
    только своя бронь → иначе 404; guard-статус 'confirmed' (решения по
    'new' — confirm/reject) → иначе 409; БЕЗ комментария (аналог confirm —
    за инструктора текст не пишем, reject_comment остается NULL).
    Эффект: status='rejected' (CHECK в db.py статуса 'cancelled' не знает),
    decided_at; слот освобождается — 'rejected' выпадает из частичного
    индекса uq_booking_active_slot (ОВ-5). Атомарно: guard
    AND status='confirmed' + rowcount (0 → 409)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        row = _booking_row(conn, booking_id)
        if row is None or row["instructor_id"] != instructor_id:
            return _error(404, "Бронь не найдена")
        cur = conn.execute(
            "UPDATE booking SET status = 'rejected',"
            " decided_at = datetime('now') WHERE id = ? AND status = 'confirmed'",
            (booking_id,),
        )
        if cur.rowcount == 0:
            return _error(409, "Бронь: решение уже принято")
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "status": "rejected"}


@router.post("/api/instructor/bookings/{booking_id}/reject")
def reject_booking(
    booking_id: int,
    data: RejectPayload | None = None,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Отклонение (ОВ-2, FR-48): комментарий непустой обязателен —
    пустой/отсутствующий → 422, действие заблокировано, статус 'new'
    остается; только своя и 'new' → иначе 404/409. Эффект: 'rejected' +
    reject_comment; слот освобождается (ОВ-5) — повторный запрос
    возможен (rejected выпадает из частичного индекса)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    comment = (data.comment if data is not None else "") or ""
    if not comment.strip():
        return _error(422, "Комментарий: поле обязательно")

    conn = db.get_conn()
    try:
        row = _booking_row(conn, booking_id)
        if row is None or row["instructor_id"] != instructor_id:
            return _error(404, "Бронь не найдена")
        cur = conn.execute(
            "UPDATE booking SET status = 'rejected', reject_comment = ?,"
            " decided_at = datetime('now') WHERE id = ? AND status = 'new'",
            (comment.strip(), booking_id),
        )
        if cur.rowcount == 0:
            return _error(409, "Бронь: решение уже принято")
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "status": "rejected"}
