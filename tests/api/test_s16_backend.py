"""Спринт 16 — BACKEND-тесты экономики, волна 16.1 (change
add-wallet-economy; задачи 16.1.1/16.1.2 — домен и миграция БД).

Покрывают: миграции экономики (таблицы transactions/acquiring_topups/
payouts/instructors/booking_disputes; пересоздание booking — статус
'completed' + снапшот-колонки, прецедент availability_new/ADR-010;
бэкфилл instructors; идемпотентность), частичные UNIQUE-гарантии
(NFR-35), SUM-балансы ledger (формулы design «Модель данных») на
сценариях «Конечные автоматы»: холд→рефанд, холд→релиз с комиссиями
0/10/100 («учитывает факт 0», FR-114), свип авто-релиза (24ч, спор
блокирует; задача 16.1.2).

tests/api/test_s5_backend.py НЕ расширяется; трассировка TC-S16-NNN
в docstring каждого теста (rule 6). Фикстуры — общий client из conftest;
time.sleep запрещен. Все суммы — целые копейки (NFR-33).
"""
import sqlite3

import pytest

import backend.core.db as db
import backend.wallet.ledger as ledger
import backend.wallet.sweeps as sweeps
from conftest import admin_headers, db_path


# --- helpers ------------------------------------------------------------------


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _instructor_via_approve(client, email="s16instr@example.com") -> int:
    """Создание инструктора через полный контур apply → approve
    (точка создания строки instructors — задача 16.1.2)."""
    body = {
        "surname": "Сшестнадцать",
        "name": "Инструктор",
        "patronymic": "Тестович",
        "phone": "+7 (911) 000-16-16",
        "email": email,
        "address": "г. Тест, ул. Экономики, 16",
        "work_format": "sber",
        "license_number": "1616161616",
        "license_category": "B",
        "experience_years": 3,
        "password": "Instr1616",
        "password_confirm": "Instr1616",
        "consent": True,
    }
    resp = client.post("/api/instructors/apply", json=body)
    assert resp.status_code == 200, resp.text
    conn = _conn()
    app_id = conn.execute(
        "SELECT id FROM instructor_applications WHERE email = ?", (email,)
    ).fetchone()[0]
    conn.close()
    approved = client.post(
        f"/api/admin/instructor-applications/{app_id}/approve",
        headers=admin_headers(client),
    )
    assert approved.status_code == 200, approved.text
    return approved.json()["user_id"]


def _tx(conn, **kwargs):
    """Обертка ledger.insert_transaction с коммитом (unit-сценарии)."""
    tx_id = ledger.insert_transaction(conn, **kwargs)
    conn.commit()
    return tx_id


# --- 16.1.1: миграция ---------------------------------------------------------


def test_s16_migration_booking_completed_and_snapshot_columns(client):
    """TC-S16-001 — booking перестроен: CHECK расширен 'completed',
    снапшот-колонки на месте, индексы пересозданы (задача 16.1.1)."""
    conn = _conn()
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(booking)")}
        assert {"price_per_hour_rub", "hold_amount_kop", "completed_at"} <= columns
        # CHECK 'completed' — INSERT проведенной брони проходит
        conn.execute(
            "INSERT INTO booking (student_id, instructor_id, availability_id,"
            " lesson_date, status, price_per_hour_rub, hold_amount_kop,"
            " completed_at) VALUES (1, 1, 1, '2026-01-01', 'completed',"
            " 1500, 300000, datetime('now'))"
        )
        conn.commit()
        # CHECK 'cancelled' — статуса нет в машине состояний
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO booking (student_id, instructor_id,"
                " availability_id, lesson_date, status)"
                " VALUES (1, 1, 1, '2026-01-02', 'cancelled')"
            )
        conn.rollback()
        indexes = {
            row["name"]
            for row in conn.execute("PRAGMA index_list(booking)").fetchall()
        }
        assert "uq_booking_active_slot" in indexes
        assert "idx_booking_instructor" in indexes
        assert "idx_booking_student" in indexes
        # Частичный UNIQUE — прежний (new/confirmed, БЕЗ completed)
        sql = conn.execute(
            "SELECT sql FROM sqlite_master"
            " WHERE type='index' AND name='uq_booking_active_slot'"
        ).fetchone()["sql"]
        assert "'new','confirmed'" in sql
        assert "completed" not in sql
    finally:
        conn.close()


def test_s16_migration_rebuild_keeps_rows_and_defaults(client):
    """TC-S16-002 — легаси-строки брони переживают пересоздание
    (прецедент ADR-010): id/created_at сохранены, новые колонки —
    DEFAULT (price NULL, hold 0, completed_at NULL) — вне экономики."""
    conn = _conn()
    try:
        conn.execute(
            "INSERT INTO booking (student_id, instructor_id, availability_id,"
            " lesson_date, status, created_at, decided_at)"
            " VALUES (10, 20, 30, '2025-05-05', 'confirmed',"
            " '2025-05-01 10:00:00', '2025-05-01 11:00:00')"
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM booking WHERE student_id = 10"
        ).fetchone()
        legacy_id, legacy_created = row["id"], row["created_at"]
    finally:
        conn.close()
    # Повторный init_db на существующей БД (контейнерный прецедент FR-53)
    db.init_db()
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT * FROM booking WHERE student_id = 10"
        ).fetchone()
        assert row["id"] == legacy_id
        assert row["created_at"] == legacy_created
        assert row["price_per_hour_rub"] is None
        assert row["hold_amount_kop"] == 0
        assert row["completed_at"] is None
    finally:
        conn.close()


def test_s16_migration_idempotent_repeat_start(client):
    """TC-S16-003 — повторный старт без ошибок и без дублей (NFR-30
    наследование, FR-53): init_db дважды — данные целы, схема та же."""
    conn = _conn()
    try:
        conn.execute(
            "INSERT INTO booking (student_id, instructor_id, availability_id,"
            " lesson_date, status) VALUES (11, 21, 31, '2025-06-06', 'new')"
        )
        conn.commit()
        before = conn.execute("SELECT COUNT(*) c FROM booking").fetchone()["c"]
    finally:
        conn.close()
    db.init_db()
    db.init_db()
    conn = _conn()
    try:
        after = conn.execute("SELECT COUNT(*) c FROM booking").fetchone()["c"]
        assert after == before
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert {
            "transactions", "acquiring_topups", "payouts", "instructors",
            "booking_disputes",
        } <= tables
    finally:
        conn.close()


def test_s16_tx_partial_uniques(client):
    """TC-S16-004 — частичные UNIQUE журнала (NFR-35): ровно один
    hold/release/refund на бронь, ровно один payout на заявку (задача
    16.1.1, design «Модель данных»)."""
    conn = _conn()
    try:
        conn.execute(
            "INSERT INTO booking (student_id, instructor_id, availability_id,"
            " lesson_date, status, hold_amount_kop)"
            " VALUES (1, 2, 3, '2026-03-01', 'new', 500000)"
        )
        conn.commit()
        booking_id = conn.execute(
            "SELECT id FROM booking WHERE student_id = 1"
        ).fetchone()[0]
        _tx(conn, tx_type="hold", user_id=1, amount_kop=500000,
            booking_id=booking_id, student_id=1, instructor_id=2)
        with pytest.raises(sqlite3.IntegrityError):
            ledger.insert_transaction(
                conn, tx_type="hold", user_id=1, amount_kop=500000,
                booking_id=booking_id, student_id=1, instructor_id=2,
            )
        conn.rollback()
        _tx(conn, tx_type="release", user_id=1, amount_kop=500000,
            booking_id=booking_id, student_id=1, instructor_id=2,
            amount_gross_kop=500000, fee_kop=50000, amount_net_kop=450000)
        with pytest.raises(sqlite3.IntegrityError):
            ledger.insert_transaction(
                conn, tx_type="release", user_id=1, amount_kop=500000,
                booking_id=booking_id, student_id=1, instructor_id=2,
                amount_gross_kop=500000, fee_kop=50000, amount_net_kop=450000,
            )
        conn.rollback()
        # refund после release — допустимо схемой (исход один в домене,
        # гарантирует свип/гварды), но ВТОРОЙ refund — нет
        _tx(conn, tx_type="refund", user_id=1, amount_kop=500000,
            booking_id=booking_id, student_id=1)
        with pytest.raises(sqlite3.IntegrityError):
            ledger.insert_transaction(
                conn, tx_type="refund", user_id=1, amount_kop=500000,
                booking_id=booking_id, student_id=1,
            )
        conn.rollback()
        # payout: ровно одна транзакция на заявку
        conn.execute(
            "INSERT INTO payouts (instructor_id, amount_kop, bank, phone)"
            " VALUES (2, 100000, 'Сбер', '+79000000000')"
        )
        conn.commit()
        payout_id = conn.execute(
            "SELECT id FROM payouts WHERE instructor_id = 2"
        ).fetchone()[0]
        _tx(conn, tx_type="payout", user_id=2, amount_kop=100000,
            payout_id=payout_id)
        with pytest.raises(sqlite3.IntegrityError):
            ledger.insert_transaction(
                conn, tx_type="payout", user_id=2, amount_kop=100000,
                payout_id=payout_id,
            )
        conn.rollback()
        # topup без booking_id — строк сколько угодно (NULL не в индексе)
        _tx(conn, tx_type="topup", user_id=1, amount_kop=100000)
        _tx(conn, tx_type="topup", user_id=1, amount_kop=100000)
    finally:
        conn.close()


def test_s16_domain_tables_constraints(client):
    """TC-S16-005 — CHECK/UNIQUE доменных таблиц: идемпотентность
    пополнения (uq_topups_idem), одна активная заявка выплаты
    (uq_payouts_one_pending), один открытый спор (uq_disputes_open),
    границы комиссии 0–100 (задача 16.1.1)."""
    conn = _conn()
    try:
        conn.execute(
            "INSERT INTO acquiring_topups (student_id, amount_kop,"
            " idempotency_key) VALUES (1, 100000, 'key-1')"
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO acquiring_topups (student_id, amount_kop,"
                " idempotency_key) VALUES (1, 100000, 'key-1')"
            )
        conn.rollback()
        # NULL-ключ — не конфликтует (каждый вызов — новая операция)
        conn.execute(
            "INSERT INTO acquiring_topups (student_id, amount_kop,"
            " idempotency_key) VALUES (1, 50000, NULL)"
        )
        conn.execute(
            "INSERT INTO acquiring_topups (student_id, amount_kop,"
            " idempotency_key) VALUES (1, 50000, NULL)"
        )
        conn.commit()

        conn.execute(
            "INSERT INTO payouts (instructor_id, amount_kop, bank, phone)"
            " VALUES (7, 100000, 'ВТБ', '+79000000001')"
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO payouts (instructor_id, amount_kop, bank, phone)"
                " VALUES (7, 50000, 'Т-Банк', '+79000000002')"
            )
        conn.rollback()
        conn.execute(
            "UPDATE payouts SET status = 'paid', paid_at = datetime('now')"
            " WHERE instructor_id = 7"
        )
        conn.commit()
        # paid-заявка не в индексе — новая активная допустима
        conn.execute(
            "INSERT INTO payouts (instructor_id, amount_kop, bank, phone)"
            " VALUES (7, 50000, 'Т-Банк', '+79000000002')"
        )
        conn.commit()

        conn.execute(
            "INSERT INTO booking_disputes (booking_id, student_id, comment)"
            " VALUES (9, 1, 'Опоздал инструктор')"
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO booking_disputes (booking_id, student_id,"
                " comment) VALUES (9, 1, 'Второй спор')"
            )
        conn.rollback()
        conn.execute(
            "UPDATE booking_disputes SET resolution = 'refund',"
            " operator_comment = 'Подтверждено', resolved_at = datetime('now')"
            " WHERE booking_id = 9"
        )
        conn.commit()
        # решенный спор закрыт — новый открытый допустим схемой (окно
        # домена: открытие только при живом холде — гварды booking.py)
        conn.execute(
            "INSERT INTO booking_disputes (booking_id, student_id, comment)"
            " VALUES (9, 1, 'Повтор после решения')"
        )
        conn.commit()

        conn.execute("INSERT INTO instructors (user_id) VALUES (77)")
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO instructors (user_id, commission_percent)"
                " VALUES (78, 101)"
            )
        conn.rollback()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO instructors (user_id, commission_percent)"
                " VALUES (78, -1)"
            )
        conn.rollback()
        conn.execute(
            "INSERT INTO instructors (user_id, commission_percent)"
            " VALUES (78, 0)"
        )
        conn.execute(
            "INSERT INTO instructors (user_id, commission_percent)"
            " VALUES (79, 100)"
        )
        conn.commit()
    finally:
        conn.close()


def test_s16_instructors_backfill_and_approve_point(client):
    """TC-S16-006 — instructors: бэкфилл init_db (INSERT OR IGNORE из
    users role='instructor', комиссия DEFAULT 10) и точка создания при
    approve (задача 16.1.1/16.1.2, FR-109)."""
    # Легаси-инструктор: users-строка без instructors-строки
    conn = _conn()
    try:
        conn.execute(
            "INSERT INTO users (surname, name, patronymic, email, phone,"
            " password_hash, role) VALUES ('Легаси', 'Инструктор', 'О.',"
            " 'legacy-s16@example.com', '+79000000003', 'x', 'instructor')"
        )
        conn.commit()
        legacy_id = conn.execute(
            "SELECT id FROM users WHERE email = 'legacy-s16@example.com'"
        ).fetchone()[0]
    finally:
        conn.close()
    db.init_db()
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT * FROM instructors WHERE user_id = ?", (legacy_id,)
        ).fetchone()
        assert row is not None
        assert row["commission_percent"] == 10
        assert row["price_per_hour_rub"] is None
    finally:
        conn.close()
    # approve-ветка создает строку в той же транзакции
    user_id = _instructor_via_approve(client)
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT * FROM instructors WHERE user_id = ?", (user_id,)
        ).fetchone()
        assert row is not None
        assert row["commission_percent"] == 10
        assert row["price_per_hour_rub"] is None
    finally:
        conn.close()
    # Повторный init_db НЕ перезаписывает (INSERT OR IGNORE)
    conn = _conn()
    try:
        conn.execute(
            "UPDATE instructors SET commission_percent = 25 WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()
    finally:
        conn.close()
    db.init_db()
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT commission_percent FROM instructors WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        assert row["commission_percent"] == 25
    finally:
        conn.close()


# --- 16.1.2: ledger — балансы на сценариях «Конечные автоматы» ----------------


def test_s16_ledger_balances_hold_refund_cycle(client):
    """TC-S16-007 — холд→рефанд (design «Конечные автоматы»): пополнение,
    холд (available−, frozen+), refund (frozen−, available+); total
    постоянен; SUM-балансы = арифметике журнала (FR-98, NFR-33)."""
    conn = _conn()
    try:
        assert ledger.student_balances(conn, 500) == {
            "available_kop": 0, "frozen_kop": 0, "total_kop": 0,
        }
        _tx(conn, tx_type="topup", user_id=500, amount_kop=1_000_000)
        b = ledger.student_balances(conn, 500)
        assert b == {"available_kop": 1_000_000, "frozen_kop": 0,
                     "total_kop": 1_000_000}
        _tx(conn, tx_type="hold", user_id=500, amount_kop=700_000,
            booking_id=42, student_id=500, instructor_id=9)
        b = ledger.student_balances(conn, 500)
        assert b["available_kop"] == 300_000
        assert b["frozen_kop"] == 700_000
        assert b["total_kop"] == 1_000_000
        _tx(conn, tx_type="refund", user_id=500, amount_kop=700_000,
            booking_id=42, student_id=500)
        b = ledger.student_balances(conn, 500)
        assert b == {"available_kop": 1_000_000, "frozen_kop": 0,
                     "total_kop": 1_000_000}
    finally:
        conn.close()


def test_s16_ledger_release_split_and_balances_commissions_0_10_100(client):
    """TC-S16-008 — релиз с комиссиями 0/10/100: floor-разбиение
    (net = gross×(100−c)//100, fee = gross−net), факт 0 при c=0 (FR-106/
    FR-114); earned/balance инструктора и баланс компании — SUM по
    журналу (задача 16.1.2)."""
    conn = _conn()
    try:
        gross = 123_456
        # c=0: fee=0, net=gross (fact 0)
        assert ledger.release_gross_split(gross, 0) == (0, gross)
        # c=10: net = floor(gross×90/100) = 111110, fee = хвост
        fee, net = ledger.release_gross_split(gross, 10)
        assert net == gross * 90 // 100
        assert fee == gross - net
        assert fee + net == gross
        # c=100: net=0, fee=gross
        assert ledger.release_gross_split(gross, 100) == (gross, 0)

        # Сценарий: инструктор 60 c=10 — ученик 40 холд→release
        conn.execute(
            "INSERT INTO instructors (user_id, commission_percent)"
            " VALUES (60, 10)"
        )
        conn.commit()
        _tx(conn, tx_type="topup", user_id=40, amount_kop=2_000_000)
        _tx(conn, tx_type="hold", user_id=40, amount_kop=gross,
            booking_id=61, student_id=40, instructor_id=60)
        fee_kop, net_kop = ledger.release_gross_split(gross, 10)
        _tx(conn, tx_type="release", user_id=40, amount_kop=gross,
            booking_id=61, student_id=40, instructor_id=60,
            amount_gross_kop=gross, fee_kop=fee_kop, amount_net_kop=net_kop)
        student = ledger.student_balances(conn, 40)
        # холд покинул available при постановке; release исполнил frozen
        assert student["available_kop"] == 2_000_000 - gross
        assert student["frozen_kop"] == 0
        assert student["total_kop"] == 2_000_000 - gross
        instructor = ledger.instructor_balances(conn, 60)
        assert instructor["earned_net_kop"] == net_kop
        assert instructor["balance_kop"] == net_kop
        assert ledger.company_balance(conn) == fee_kop
        # Выплата: balance −= payout; заявка баланс не замораживает
        _tx(conn, tx_type="payout", user_id=60, amount_kop=10_000)
        instructor = ledger.instructor_balances(conn, 60)
        assert instructor["balance_kop"] == net_kop - 10_000
        assert ledger.company_balance(conn) == fee_kop  # факт 0 при c=0:
        # добавляем релиз инструктора с комиссией 0 — баланс компании
        # не меняется (нулевая комиссия вносит 0 фактом)
        conn.execute(
            "INSERT INTO instructors (user_id, commission_percent)"
            " VALUES (61, 0)"
        )
        conn.commit()
        gross0 = 500_000
        _tx(conn, tx_type="release", user_id=41, amount_kop=gross0,
            booking_id=62, student_id=41, instructor_id=61,
            amount_gross_kop=gross0, fee_kop=0, amount_net_kop=gross0)
        assert ledger.company_balance(conn) == fee_kop
        instructor0 = ledger.instructor_balances(conn, 61)
        assert instructor0["earned_net_kop"] == gross0
    finally:
        conn.close()


def test_s16_ledger_hold_amount_kop_hours_floor(client):
    """TC-S16-009 — сумма холда: цена×100×часы; нецелые интервалы —
    floor до целого часа (design «Денежные правила», NFR-33)."""
    assert ledger.hours_between("10:00", "12:00") == 2
    assert ledger.hours_between("10:00", "12:30") == 2  # floor, хвост не тарифицируется
    assert ledger.hold_amount_kop(1500, "10:00", "12:00") == 300_000
    assert ledger.hold_amount_kop(0, "10:00", "14:00") == 0
    assert ledger.hold_amount_kop(999, "08:15", "10:45") == 199_800


def _completed_booking(conn, *, student_id, instructor_id, hold_kop,
                       completed_at, status="completed", hold_alive=True):
    cur = conn.execute(
        "INSERT INTO booking (student_id, instructor_id, availability_id,"
        " lesson_date, status, hold_amount_kop, completed_at)"
        " VALUES (?, ?, 1, '2026-01-10', ?, ?, ?)",
        (student_id, instructor_id, status, hold_kop, completed_at),
    )
    conn.commit()
    booking_id = int(cur.lastrowid)
    if hold_alive:
        _tx(conn, tx_type="hold", user_id=student_id, amount_kop=hold_kop,
            booking_id=booking_id, student_id=student_id,
            instructor_id=instructor_id)
    return booking_id


def test_s16_sweep_release_after_24h_dispute_blocks_and_rerun_idempotent(client):
    """TC-S16-010 — свип авто-релиза (задача 16.1.2): completed ≥24ч →
    release ровно один (повторный свип без дубля — частичный UNIQUE);
    до 24ч релиза нет; открытый спор блокирует; комиссия берется
    ТЕКУЩЕЙ (25 → fee/net по ней)."""
    conn = _conn()
    try:
        conn.execute(
            "INSERT INTO instructors (user_id, commission_percent)"
            " VALUES (71, 25)"
        )
        conn.commit()
        _tx(conn, tx_type="topup", user_id=70, amount_kop=10_000_000)
        # (а) готов к релизу: отметка 30ч назад
        b_ready = _completed_booking(
            conn, student_id=70, instructor_id=71, hold_kop=400_000,
            completed_at="2026-01-09 00:00:00",
        )
        # (б) окно не вышло: отметка 1ч назад — ставим будущую
        # относительно cutoff (created_at больше now−24h невозможно
        # подделать — используем свежую отметку через datetime('now'))
        conn.execute(
            "INSERT INTO booking (student_id, instructor_id, availability_id,"
            " lesson_date, status, hold_amount_kop, completed_at)"
            " VALUES (70, 71, 1, '2026-01-10', 'completed', 200000,"
            " datetime('now'))"
        )
        conn.commit()
        b_fresh = conn.execute(
            "SELECT id FROM booking WHERE hold_amount_kop = 200000"
        ).fetchone()[0]
        _tx(conn, tx_type="hold", user_id=70, amount_kop=200_000,
            booking_id=b_fresh, student_id=70, instructor_id=71)
        # (в) спор открыт → блок
        b_disputed = _completed_booking(
            conn, student_id=70, instructor_id=71, hold_kop=100_000,
            completed_at="2026-01-09 00:00:00",
        )
        conn.execute(
            "INSERT INTO booking_disputes (booking_id, student_id, comment)"
            " VALUES (?, 70, 'Разбирается')", (b_disputed,),
        )
        conn.commit()
    finally:
        conn.close()

    released = sweeps.wallet_sweep(_conn())
    assert released == 1  # только (а)
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT * FROM transactions WHERE booking_id = ?"
            " AND type = 'release'", (b_ready,),
        ).fetchone()
        assert row is not None
        assert row["amount_gross_kop"] == 400_000
        assert row["fee_kop"] == 100_000      # 25% от 400000
        assert row["amount_net_kop"] == 300_000
        assert row["student_id"] == 70 and row["instructor_id"] == 71
        # (б) и (в) — без транзакций исхода
        for bid in (b_fresh, b_disputed):
            assert conn.execute(
                "SELECT COUNT(*) c FROM transactions"
                " WHERE booking_id = ? AND type IN ('release','refund')",
                (bid,),
            ).fetchone()["c"] == 0
        instructor = ledger.instructor_balances(conn, 71)
        assert instructor["earned_net_kop"] == 300_000
    finally:
        conn.close()
    # Повторный свип — безобиден (частичный UNIQUE, NFR-35)
    assert sweeps.wallet_sweep(_conn()) == 0
    conn = _conn()
    try:
        count = conn.execute(
            "SELECT COUNT(*) c FROM transactions WHERE type = 'release'"
        ).fetchone()["c"]
        assert count == 1
    finally:
        conn.close()
