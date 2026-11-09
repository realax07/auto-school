"""instructor_availability.py — график часов работы (Спринт 3, задача 3.1,
домен instructor-availability; Спринт 10 (add-calendar-weeks-availability,
задача 3.1): типы recurring/one_off, запрет прошлого, дифф-запись MAJ-1).

GET/PUT /api/instructor/availability. Доступ: сессия + role='instructor'
(401 гость, 403 иная роль — specs/instructor-availability).

GET (NFR-29): {ok, intervals:[{weekday, start_time, end_time, slot_type,
date}]} — упорядочены по weekday, start_time (как прежде); slot_type ∈
'recurring'|'one_off'; date — 'YYYY-MM-DD' для one_off, null для
recurring. Поля аддитивны: старые потребители читают weekday/start/end.
Список полон: все recurring-серии и все one_off независимо от дат —
клиент разворачивает серии сам (D7).

PUT — ПОЛНАЯ замена графика обоих типов (FR-29/FR-30, NFR-29):
{intervals:[{weekday, start_time, end_time, slot_type?, date?}]}.
Валидации (422, до транзакции): weekday 0..6, HH:MM, start < end;
slot_type отсутствует → 'recurring' (легаси-тело); one_off — date
обязательна (существующая ISO-дата), weekday обязан совпадать с днем
недели даты (сервер не доверяет клиенту); recurring с date → 422;
дубликаты (с учетом slot_type/date) схлопываются.

ЗАПРЕТ ПРОШЛОГО (D6, FR-93, NFR-31 — серверная проверка КАЖДОГО PUT,
ЕДИНОЕ правило границы MIN-1: ПРОШЕДШИЙ = начало < NOW МСК; инструктору
разрешено править НАЧАВШИЙСЯ текущий слот — начало ≥ NOW). Для тела
НОВОГО формата (с slot_type/date): 422 «Прошедшие слоты не подлежат
изменению», если (а) payload создает/меняет прошедший one_off (date+
start_time < NOW и нет ТОЧНО такой строки в БД) или (б) убирает/меняет
существующий прошедший one_off (immutable-история; прошедшие ЭКЗЕМПЛЯРЫ
recurring-серий не хранятся и не проверяются — D8). ЛЕГАСИ-тело (без
slot_type/date): эффективный payload = recurring-интервалы тела плюс
СУЩЕСТВУЮЩИЕ one_off (ПРОШЕДШИЕ И БУДУЩИЕ) сохраняются без изменений —
правило (б) выполняется конструктивно (MAJ-2 арх-ревью; удалить/изменить
разовый слот можно только полным графиком из нового UI).

MAJ-1 (арх-ревью Спринта 10, политика (б); наследование M-3 review-001):
в транзакции BEGIN IMMEDIATE helper booking.blocking_bookings (тот же
single-writer, что create_booking) проверяет ЭКЗЕМПЛЯРЫ — нераскрытые
активные брони → 409 с перечнем, содержащим дату (FR-92, NFR-29);
прошедшие экземпляры не блокируют (D8).

ЗАПИСЬ — дифф, не wholesale-DELETE+INSERT (design «Экземпляр и разворот
серий»): строки, совпадающие ПОЛНЫМ ключом (weekday, start_time,
end_time, slot_type, slot_date) в старом и новом графике, не
пересоздаются (id сохраняются — ссылки booking.availability_id валидны,
JOIN выдач броней не рвется); DELETE только убранных, INSERT только
добавленных — в той же транзакции. Удаление строки с активными бронями
на НЕПРОШЕДШИХ экземплярах допустимо только при покрытии каждого такого
экземпляра другой строкой нового графика (иначе 409 — см. MAJ-1), при
этом booking.availability_id ПЕРЕПРИВЯЗЫВАЕТСЯ на строку-носитель того
же экземпляра (приоритет one_off; поля брони — ученик, lesson_date,
статус, решения, комментарии — НЕ меняются; на 409 не меняется ничего —
FR-92). Ответ 200 — формат GET (полный сохраненный график).

NOW — единый серверный МСК-хелпер booking.now_moscow (NFR-31, MIN-2
арх-ревью: не наивный now(); TZ=Europe/Moscow закрепляется деплоем —
задача 4.1). SQL — только параметризованный (NFR-3).
"""
import datetime
import re
import sqlite3

from fastapi import APIRouter, Header
from pydantic import BaseModel

from backend.student import booking as booking_domain
import backend.core.db as db
from backend.student.booking import blocking_bookings, conflict_error_response
from backend.core.guards import _error, require_role

router = APIRouter()

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

_PAST_SLOT_ERROR = "Прошедшие слоты не подлежат изменению"


class Interval(BaseModel):
    # Дефолты вместо Pydantic-required — валидация в хендлере.
    weekday: int = -1
    start_time: str = ""
    end_time: str = ""
    slot_type: str = ""  # '' = не указан (легаси-тело) → 'recurring'
    date: str = ""       # '' = не указана (легаси-тело; для one_off обязательна)


class AvailabilityPayload(BaseModel):
    intervals: list[Interval] = []


def _hhmm_valid(value: str) -> bool:
    return bool(_TIME_RE.match(value or ""))


def _slot_rows(
    payload: AvailabilityPayload,
) -> tuple[list[tuple[int, str, str, str, str]], bool, str | None]:
    """Валидация intervals нового контракта; дубликаты (с учетом
    slot_type/date) схлопываются (design.md «Контракт availability»).
    Возвращает (отсортированные уникальные ПОЛНЫЕ ключи
    (weekday, start_time, end_time, slot_type, slot_date), признак
    ЛЕГАСИ-тела (ни один интервал не несет slot_type/date), ошибка)."""
    legacy = all(
        interval.slot_type == "" and interval.date == ""
        for interval in payload.intervals
    )
    seen: set[tuple[int, str, str, str, str]] = set()
    for interval in payload.intervals:
        if interval.weekday < 0 or interval.weekday > 6:
            return [], legacy, "День недели: целое число от 0 (пн) до 6 (вс)"
        if not _hhmm_valid(interval.start_time) or not _hhmm_valid(
            interval.end_time
        ):
            return [], legacy, "Время: укажите границы интервала в формате ЧЧ:ММ"
        if interval.start_time >= interval.end_time:
            return [], legacy, "Интервал: начало должно быть раньше конца"
        if legacy:
            seen.add(
                (interval.weekday, interval.start_time,
                 interval.end_time, "recurring", "")
            )
            continue
        slot_type = interval.slot_type or "recurring"
        if slot_type not in ("recurring", "one_off"):
            return [], legacy, "Тип слота: укажите 'recurring' или 'one_off'"
        if slot_type == "one_off":
            slot_date = booking_domain.parse_iso_date(interval.date)
            if slot_date is None:
                return [], legacy, (
                    "Дата разового слота: укажите существующую дату"
                    " в формате ГГГГ-ММ-ДД"
                )
            if interval.weekday != slot_date.weekday():
                return [], legacy, (
                    "День недели разового слота: не совпадает с днем"
                    " недели даты"
                )
            seen.add(
                (interval.weekday, interval.start_time,
                 interval.end_time, "one_off", slot_date.isoformat())
            )
        else:
            if interval.date:
                return [], legacy, (
                    "Дата: указывается только для разового слота (one_off)"
                )
            seen.add(
                (interval.weekday, interval.start_time,
                 interval.end_time, "recurring", "")
            )
    return sorted(seen), legacy, None


def _db_rows(
    conn: sqlite3.Connection, instructor_id: int
) -> dict[tuple[int, str, str, str, str], sqlite3.Row]:
    """Текущий график инструктора: полный ключ → строка (id сохраняется
    у совпадающих строк — дифф-запись MAJ-1)."""
    rows = conn.execute(
        "SELECT id, weekday, start_time, end_time, slot_type, slot_date"
        " FROM availability WHERE instructor_id = ?",
        (instructor_id,),
    ).fetchall()
    return {
        (row["weekday"], row["start_time"], row["end_time"],
         row["slot_type"], row["slot_date"]): row
        for row in rows
    }


def _past_ban_violation(
    conn: sqlite3.Connection,
    instructor_id: int,
    rows: list[tuple[int, str, str, str, str]],
    legacy: bool,
) -> bool:
    """ЗАПРОТ ПРОШЛОГО (D6, FR-93, NFR-31; единое правило MIN-1:
    ПРОШЕДШИЙ = начало < NOW МСК). ЛЕГАСИ-тело — всегда False: правило
    выполняется конструктивно (существующие one_off сервером сохранены —
    MAJ-2). Тело нового формата — True, если:
    (а) payload создает/меняет прошедший one_off (date+start_time < NOW,
    нет ТОЧНО такой строки в БД), либо
    (б) убирает/меняет существующий прошедший one_off (каждый прошедший
    one_off БД обязан присутствовать в payload без изменений —
    immutable-история). Инструктору разрешено править НАЧАВШИЙСЯ текущий
    слот (начало ≥ NOW — граница «ровно NOW» проходит)."""
    if legacy:
        return False
    now = booking_domain.now_moscow()
    db_rows = _db_rows(conn, instructor_id)
    past_one_offs = {
        key for key in db_rows
        if key[3] == "one_off"
        and booking_domain.instance_start(key[4], key[1]) < now
    }
    payload_keys = set(rows)
    # (а) payload создает/меняет прошедший one_off
    for key in payload_keys:
        if key[3] == "one_off" and booking_domain.instance_start(
            key[4], key[1]
        ) < now and key not in db_rows:
            return True
    # (б) payload убирает/меняет существующий прошедший one_off
    return any(key not in payload_keys for key in past_one_offs)


def _rebind_bookings(
    conn: sqlite3.Connection,
    instructor_id: int,
    removed_rows: list[sqlite3.Row],
    new_rows: list[tuple[int, str, str, str, str]],
    now: datetime.datetime,
) -> None:
    """Перепривязка booking.availability_id при удалении строки-носителя:
    активные брони НЕПРОШЕДШИХ экземпляров удаляемой строки переходят на
    строку-носитель того же экземпляра нового графика (приоритет one_off;
    поля брони НЕ меняются). Вызывается ПОСЛЕ INSERT to_insert
    (review-003-3.1 major-1): носитель может быть только что вставленной
    строкой («смена типа» серия→one_off / one_off→серия) — SELECT-поиск
    в БД находит его только в этом порядке. Достижение этой точки
    гарантирует покрытие (проверка blocking_bookings → 409 иначе);
    прошедшие экземпляры не блокируют замену и не перепривязываются
    (история — брони, D8/MIN-3)."""
    carriers = set(new_rows)
    for row in removed_rows:
        bookings = conn.execute(
            "SELECT id, lesson_date FROM booking"
            " WHERE availability_id = ? AND status IN (?, ?)",
            (row["id"], *booking_domain._ACTIVE_STATUSES),
        ).fetchall()
        for booking_row in bookings:
            lesson_date = booking_row["lesson_date"]
            if booking_domain.instance_start(
                lesson_date, row["start_time"]
            ) < now:
                continue
            weekday = datetime.date.fromisoformat(lesson_date).weekday()
            carrier_key = (
                (weekday, row["start_time"], row["end_time"],
                 "one_off", lesson_date)
                if (weekday, row["start_time"], row["end_time"],
                    "one_off", lesson_date) in carriers
                else (weekday, row["start_time"], row["end_time"],
                      "recurring", "")
            )
            carrier = conn.execute(
                "SELECT id FROM availability WHERE instructor_id = ?"
                " AND weekday = ? AND start_time = ? AND end_time = ?"
                " AND slot_type = ? AND slot_date = ?",
                (instructor_id, *carrier_key),
            ).fetchone()
            if carrier is not None:
                conn.execute(
                    "UPDATE booking SET availability_id = ? WHERE id = ?",
                    (carrier["id"], booking_row["id"]),
                )


@router.get("/api/instructor/availability")
def get_availability(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Интервалы текущего графика (FR-30; Спринт 10 NFR-29: + slot_type,
    date), упорядочены по дню и началу; date — null для recurring."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT weekday, start_time, end_time, slot_type, slot_date"
            " FROM availability"
            " WHERE instructor_id = ?"
            " ORDER BY weekday, start_time, end_time, slot_date",
            (instructor_id,),
        ).fetchall()
    finally:
        conn.close()
    intervals = [
        {"weekday": row["weekday"], "start_time": row["start_time"],
         "end_time": row["end_time"], "slot_type": row["slot_type"],
         "date": row["slot_date"] or None}
        for row in rows
    ]
    return {"ok": True, "intervals": intervals}


@router.put("/api/instructor/availability")
def put_availability(
    data: AvailabilityPayload,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Полная замена графика (FR-29/FR-30; Спринт 10 — типы/даты, запрет
    прошлого, дифф-запись): валидация до записи → 422; ЗАПРОТ ПРОШЛОГО —
    422 (D6/NFR-31, единая граница MIN-1); MAJ-1 (проверка экземпляров
    booking.blocking_bookings) и дифф-запись (совпадающие полным ключом
    строки не пересоздаются — id сохраняются, бронь-сирота невозможна —
    нет FK booking→availability) в ОДНОЙ write-транзакции BEGIN
    IMMEDIATE (M-3 review-001: сериализация с create_booking — бронь на
    убираемый экземпляр не может появиться после проверки)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    rows, legacy, error = _slot_rows(data)
    if error is not None:
        return _error(422, error)

    conn: sqlite3.Connection = db.get_conn()
    try:
        # MAJ-1 (Спринт 10, наследование Спринта 5): замена графика
        # отклоняется 409, если убираемые ЭКЗЕМПЛЯРЫ (дата+время) имеют
        # активные брони и не покрыты новым графиком; график НЕ изменен —
        # инструктор сначала решает брони (booking.py).
        # M-3 (review-001, NFR-8): BEGIN IMMEDIATE ДО проверки —
        # проверка (blocking_bookings на уровне ЭКЗЕМПЛЯРОВ — MAJ-1
        # арх-ревью Спринта 10, политика (б)) и дифф-запись в одной
        # write-транзакции, сериализуется с create_booking (тоже BEGIN
        # IMMEDIATE): окно TOCTOU «проверка → удаление» закрыто.
        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        try:
            db_rows = _db_rows(conn, instructor_id or 0)
            if legacy:
                # ЛЕГАСИ-тело (MAJ-2): эффективный payload = recurring из
                # тела + СУЩЕСТВУЮЩИЕ one_off (прошедшие И будущие)
                # сохраняются без изменений (NFR-29).
                one_offs = [
                    key for key in db_rows if key[3] == "one_off"
                ]
                effective = sorted(set(rows) | set(one_offs))
            else:
                effective = rows
                if _past_ban_violation(
                    conn, instructor_id or 0, rows, legacy
                ):
                    conn.execute("ROLLBACK")
                    return _error(422, _PAST_SLOT_ERROR)
            conflicts = blocking_bookings(
                conn, instructor_id or 0, effective
            )
            if conflicts:
                conn.execute("ROLLBACK")
                return conflict_error_response(conflicts)
            # Дифф-запись (design «Экземпляр и разворот серий», MAJ-1):
            # совпадающие полным ключом строки НЕ пересоздаются.
            # ПОРЯДОК (review-003-3.1 major-1): INSERT → перепривязка →
            # DELETE — rebind ищет носителя SELECT-ом в БД и обязан видеть
            # уже вставленные строки нового графика: при «смене типа»
            # (серия удалена + one_off добавлен на дату брони, и
            # симметрично one_off→серия) носитель существует ТОЛЬКО после
            # INSERT; прежний порядок (rebind до insert) молча пропускал
            # перепривязку → DELETE оставлял бронь-сироту (невидима для
            # INNER JOIN выдач и кросс-строчной проверки create_booking).
            # Порядок безопасен по UNIQUE-коллизиям: ключи to_insert
            # отсутствуют в db_rows (не конфликтуют при вставке), ключи
            # to_delete отсутствуют в effective/to_insert (не удалят
            # вставленное) — insert/delete разъединены.
            to_insert = [key for key in effective if key not in db_rows]
            to_delete = [row for key, row in db_rows.items()
                         if key not in set(effective)]
            now = booking_domain.now_moscow()
            conn.executemany(
                "INSERT INTO availability (instructor_id, weekday,"
                " start_time, end_time, slot_type, slot_date)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (instructor_id, *key)
                    for key in to_insert
                ],
            )
            _rebind_bookings(
                conn, instructor_id or 0, to_delete, effective, now
            )
            for row in to_delete:
                conn.execute(
                    "DELETE FROM availability WHERE id = ?", (row["id"],)
                )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        saved = _db_rows(conn, instructor_id or 0)
    finally:
        conn.close()
    intervals = [
        {"weekday": key[0], "start_time": key[1], "end_time": key[2],
         "slot_type": key[3], "date": key[4] or None}
        for key in sorted(saved)
    ]
    return {"ok": True, "intervals": intervals}
