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
    «проведено» ≥24ч назад, БЕЗ открытого спора и БЕЗ release-транзакции
    → RELEASE (gross → net инструктору по ТЕКУЩЕЙ комиссии, fee
    платформе; одна транзакция с gross/fee/net — восстанавливаемость).
(2) TIMEOUT-DEFROST (16.3.1, MIN-1): брони new/confirmed с холдом, чей
    экземпляр начался ≥72ч назад, «проведена» не отмечена, спора нет,
    refund нет → REFUND ученику (холд не висит вечно).

Комиссия 0/100 «учитывает факт 0» (FR-114): split в ledger.
release_gross_split — целочисленно (NFR-33).
"""
import datetime
import sqlite3

import backend.wallet.ledger as ledger

RELEASE_DELAY_HOURS = 24
RELEASE_SWEEP_CUTOFF = f"-{RELEASE_DELAY_HOURS} hours"


def wallet_sweep(conn: sqlite3.Connection) -> int:
    """Свип авто-релиза (16.1.2): BEGIN IMMEDIATE; SELECT кандидатов —
    completed + холд + отметка старше 24ч + нет открытого спора + нет
    release; на каждого — RELEASE-транзакция (gross = hold_amount_kop,
    fee/net по текущей комиссии инструктора; строка instructors
    гарантируется ensure_instructor_row — комиссия DEFAULT 10).
    Возвращает число созданных релизов (для тестов/логов).
    IntegrityError частичного UNIQUE (гонка параллельного свипа)
    глушится по-строчно: релиз уже создан другим соединением —
    идемпотентно."""
    conn.isolation_level = None
    conn.execute("BEGIN IMMEDIATE")
    released = 0
    try:
        cutoff = (
            datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(hours=RELEASE_DELAY_HOURS)
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
            "   WHERE t.booking_id = b.id AND t.type = 'release')",
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
                # Ровно один release на бронь (частичный UNIQUE,
                # NFR-35): параллельный свип успел раньше — no-op.
                continue
            released += 1
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return released
