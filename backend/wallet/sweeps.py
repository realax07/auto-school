"""sweeps.py — ленивый свип исходов холдов (Спринт 16, задачи 16.1.2 и
16.3.1; design.md «Конечные автоматы» / «Авто-релиз — ЛЕНИВЫЙ СВИП»).

Single-worker (наследованный инвариант ADR-001/002): фоновых потоков и
кронов НЕТ — свип выполняется при чтении точек кошельков/админ-раздела
(GET /api/wallet, /api/instructor/economy|earnings,
/api/admin/transactions, /api/admin/disputes) внутри write-транзакции
BEGIN IMMEDIATE. Детерминизм: ровно один исход холда на бронь страхуют
частичные UNIQUE uq_tx_release_per_booking / uq_tx_refund_per_booking —
повторный свип безобиден (проигравшей строки нет).

Исходы (16.1.2 — авто-релиз; 16.3.1 — timeout-defrost):
(1) АВТО-РЕЛИЗ: брони status='completed' с hold_amount_kop>0, отмеченные
    «проведено» ≥24ч назад, БЕЗ открытого спора и БЕЗ release- И refund-
    транзакции → RELEASE (gross → net инструктору по ТЕКУЩЕЙ комиссии,
    fee платформе; одна транзакция с gross/fee/net — восстанавливаемость).
    Отсутствие refund в условии — терминальность исхода (design «Конечные
    автоматы»: RELEASE/REFUND терминальны, исход ОДИН на бронь; возврат
    по спору исключает последующий релиз — иначе деньги создавались бы
    дважды).
(2) TIMEOUT-DEFROST (16.3.1, MIN-1): брони new/confirmed с холдом, чей
    экземпляр начался ≥72ч назад, «проведена» не отмечена, спора нет,
    исхода нет → REFUND ученику (холд не висит вечно).

Комиссия 0/100 «учитывает факт 0» (FR-114): split в ledger.
release_gross_split — целочисленно (NFR-33).
"""
import datetime
import sqlite3

import backend.wallet.ledger as ledger

RELEASE_DELAY_HOURS = 24
RELEASE_SWEEP_CUTOFF = f"-{RELEASE_DELAY_HOURS} hours"

DEFROST_DELAY_HOURS = 72
_MOSCOW_TZ = datetime.timezone(datetime.timedelta(hours=3))


def instance_start_utc(lesson_date: str, start_time: str) -> datetime.datetime:
    """Начало экземпляра в UTC (lesson_date 'YYYY-MM-DD' + start_time
    'HH:MM' — метки МСК, конвенция booking.instance_start; UTC+3 явно).
    Единая точка сравнения свипа с now_utc (сдвиг формата/зоны ломал бы
    границу 72ч)."""
    day = datetime.date.fromisoformat(lesson_date)
    hour, minute = (int(part) for part in start_time.split(":"))
    msk = datetime.datetime(day.year, day.month, day.day, hour, minute,
                            tzinfo=_MOSCOW_TZ)
    return msk.astimezone(datetime.timezone.utc)


def wallet_sweep(conn: sqlite3.Connection) -> int:
    """Свип исходов холдов (design «Авто-релиз — ЛЕНИВЫЙ СВИП»):
    BEGIN IMMEDIATE; два SELECT'а кандидатов:
    (1) АВТО-РЕЛИЗ: completed + холд + отметка старше 24ч + нет открытого
        спора + НЕТ исхода (release ИЛИ refund — терминальность, исход
        один) → RELEASE (gross = hold_amount_kop, fee/net по текущей
        комиссии инструктора; строка instructors гарантируется
        ensure_instructor_row — комиссия DEFAULT 10);
    (2) TIMEOUT-DEFROST (16.3.1, MIN-1): new/confirmed + холд + экземпляр
        начался ≥72ч назад + нет открытого спора + нет исхода → REFUND
        ученику (инструктор за 72ч не отметил «проведена» и не отменил
        до старта — холд не висит вечно).
    Возвращает число созданных исходов (релизы + разморозки — для
    тестов/логов). IntegrityError частичного UNIQUE (гонка параллельного
    свипа) глушится по-строчно: исход уже создан другим соединением —
    идемпотентно."""
    conn.isolation_level = None
    conn.execute("BEGIN IMMEDIATE")
    executed = 0
    try:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        cutoff = (
            now_utc - datetime.timedelta(hours=RELEASE_DELAY_HOURS)
        ).strftime("%Y-%m-%d %H:%M:%S")
        candidates = conn.execute(
            "SELECT b.id, b.student_id, b.instructor_id, b.hold_amount_kop"
            " FROM booking AS b"
            " WHERE b.status = 'completed' AND b.hold_amount_kop > 0"
            " AND b.completed_at IS NOT NULL AND b.completed_at <= ?"
            " AND NOT EXISTS ("
            "   SELECT 1 FROM booking_disputes d"
            "   WHERE d.booking_id = b.id AND d.resolution IS NULL)"
            " AND NOT EXISTS ("
            "   SELECT 1 FROM transactions t"
            "   WHERE t.booking_id = b.id"
            "     AND t.type IN ('release', 'refund'))",
            (cutoff,),
        ).fetchall()
        for row in candidates:
            instructor = ledger.ensure_instructor_row(conn, row["instructor_id"])
            fee_kop, net_kop = ledger.release_gross_split(
                row["hold_amount_kop"], instructor["commission_percent"]
            )
            try:
                ledger.insert_transaction(
                    conn,
                    tx_type="release",
                    user_id=row["student_id"],
                    amount_kop=row["hold_amount_kop"],
                    booking_id=row["id"],
                    student_id=row["student_id"],
                    instructor_id=row["instructor_id"],
                    amount_gross_kop=row["hold_amount_kop"],
                    fee_kop=fee_kop,
                    amount_net_kop=net_kop,
                )
            except sqlite3.IntegrityError:
                # Ровно один исход на бронь (частичный UNIQUE,
                # NFR-35): параллельный свип успел раньше — no-op.
                continue
            executed += 1

        # (2) TIMEOUT-DEFROST (16.3.1): new/confirmed, экземпляр начался
        # ≥72ч назад — начало экземпляра (МСК) сравнивается с NOW в UTC
        # (единая точка instance_start_utc). Отметки «проведена» нет по
        # условию статуса (new/confirmed ≠ completed).
        defrost_cutoff = now_utc - datetime.timedelta(
            hours=DEFROST_DELAY_HOURS
        )
        defrost = conn.execute(
            "SELECT b.id, b.student_id, b.instructor_id, b.hold_amount_kop,"
            " b.lesson_date, a.start_time"
            " FROM booking AS b"
            " JOIN availability AS a ON a.id = b.availability_id"
            " WHERE b.status IN ('new', 'confirmed')"
            " AND b.hold_amount_kop > 0"
            " AND NOT EXISTS ("
            "   SELECT 1 FROM booking_disputes d"
            "   WHERE d.booking_id = b.id AND d.resolution IS NULL)"
            " AND NOT EXISTS ("
            "   SELECT 1 FROM transactions t"
            "   WHERE t.booking_id = b.id"
            "     AND t.type IN ('release', 'refund'))"
        ).fetchall()
        for row in defrost:
            if instance_start_utc(
                row["lesson_date"], row["start_time"]
            ) > defrost_cutoff:
                continue
            try:
                ledger.insert_transaction(
                    conn,
                    tx_type="refund",
                    user_id=row["student_id"],
                    amount_kop=row["hold_amount_kop"],
                    booking_id=row["id"],
                    student_id=row["student_id"],
                    instructor_id=row["instructor_id"],
                )
            except sqlite3.IntegrityError:
                continue
            executed += 1
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return executed
