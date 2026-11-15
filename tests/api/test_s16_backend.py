"""Спринт 16 — BACKEND-тесты экономики, волны 16.1 и 16.2 (change
add-wallet-economy; задачи 16.1.1/16.1.2 — домен и миграция БД;
16.2.1/16.2.2/16.2.3 — API кошелька/цен/статистики/выплат и админ-контур
«Транзакции»).

Покрывают: миграции экономики (таблицы transactions/acquiring_topups/
payouts/instructors/booking_disputes; пересоздание booking — статус
'completed' + снапшот-колонки, прецедент availability_new/ADR-010;
бэкфилл instructors; идемпотентность), частичные UNIQUE-гарантии
(NFR-35), SUM-балансы ledger (формулы design «Модель данных») на
сценариях «Конечные автоматы»: холд→рефанд, холд→релиз с комиссиями
0/10/100 («учитывает факт 0», FR-114), свип авто-релиза (24ч, спор
блокирует; задача 16.1.2); API 16.2 — кошелек ученика (пустой 0/0/0,
пополнение с идемпотентностью X-Idempotency-Key — NFR-35, валидация
сумм), цена часа и комиссия (админ-поле 0–100), доходы инструктора
(месяц по ученикам + итог, net), payout заявка→confirm оператором
(guard баланса — 409 без списания), решение споров release/refund
(комментарий обязателен, повтор — 409), журнал оператора (фильтры
тип/роль/юзер/период + company_balance_kop) и комиссии за год (факт 0,
FR-115). Денежные величины — целые копейки (NFR-33).

tests/api/test_s5_backend.py НЕ расширяется; трассировка TC-S16-NNN
в docstring каждого теста (rule 6). Фикстуры — общий client из conftest;
time.sleep запрещен. Все суммы — целые копейки (NFR-33).
"""
import sqlite3

import pytest

import backend.core.db as db
import backend.wallet.ledger as ledger
import backend.wallet.sweeps as sweeps
from conftest import admin_headers, db_path, register


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


# --- 16.2.1: API кошелька ученика ----------------------------------------------


def _student(client, email):
    """Регистрация + вход ученика → {token, id} (конвенция test_s5)."""
    resp = register(client, email=email)
    assert resp.status_code == 200, resp.text
    conn = _conn()
    user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", (email,)
    ).fetchone()[0]
    conn.close()
    login = client.post(
        "/api/auth/login", json={"email": email, "password": "Qwerty123"}
    )
    assert login.status_code == 200, login.text
    return {"token": login.json()["token"], "id": user_id}


def test_s16_wallet_empty_and_guards(client):
    """TC-S16-011 — кошелек пустого ученика: 0/0/0, история пуста
    (корректные нули, спека wallet); без токена — 401; инструктор —
    403 (require_role, задача 16.2.1)."""
    student = _student(client, "s16w@example.com")
    resp = client.get("/api/wallet", headers={"X-Session-Token": student["token"]})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["available_kop"] == 0
    assert body["frozen_kop"] == 0
    assert body["total_kop"] == 0
    assert body["transactions"] == []
    assert client.get("/api/wallet").status_code == 401
    instructor = _instructor_via_approve(
        client, "s16w-instr@example.com"
    )
    login = client.post(
        "/api/auth/login",
        json={"email": "s16w-instr@example.com", "password": "Instr1616"},
    )
    resp = client.get(
        "/api/wallet",
        headers={"X-Session-Token": login.json()["token"]},
    )
    assert resp.status_code == 403


def test_s16_wallet_topup_and_history(client):
    """TC-S16-012 — пополнение мгновенно зачисляется (спека wallet):
    acquiring_topups (mock/succeeded, provider_payment_id NULL) +
    транзакция topup; available+, история содержит topup (FR-99)."""
    student = _student(client, "s16w-top@example.com")
    resp = client.post(
        "/api/wallet/topup",
        json={"amount_kop": 250_000},
        headers={"X-Session-Token": student["token"]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["available_kop"] == 250_000
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT * FROM acquiring_topups WHERE id = ?",
            (body["topup_id"],),
        ).fetchone()
        assert row["provider"] == "mock"
        assert row["status"] == "succeeded"
        assert row["provider_payment_id"] is None  # поле будущего провайдера
    finally:
        conn.close()
    wallet = client.get(
        "/api/wallet", headers={"X-Session-Token": student["token"]}
    ).json()
    types = [t["type"] for t in wallet["transactions"]]
    assert "topup" in types
    assert wallet["transactions"][0]["sign"] == 1


def test_s16_wallet_topup_idempotency_key_vs_no_key(client):
    """TC-S16-013 — идемпотентность пополнения (NFR-35): повтор с тем же
    X-Idempotency-Key — дубля нет, баланс не удваивается (результат
    первой операции); без ключа каждый вызов — новая операция."""
    student = _student(client, "s16w-idem@example.com")
    headers = {"X-Session-Token": student["token"],
               "X-Idempotency-Key": "op-2026-16-1"}
    first = client.post("/api/wallet/topup", json={"amount_kop": 100_000},
                        headers=headers)
    assert first.status_code == 200
    repeat = client.post("/api/wallet/topup", json={"amount_kop": 100_000},
                         headers=headers)
    assert repeat.status_code == 200
    assert repeat.json()["topup_id"] == first.json()["topup_id"]
    conn = _conn()
    try:
        topups = conn.execute(
            "SELECT COUNT(*) c FROM acquiring_topups"
            " WHERE idempotency_key = 'op-2026-16-1'"
        ).fetchone()["c"]
        txs = conn.execute(
            "SELECT COUNT(*) c FROM transactions t"
            " JOIN acquiring_topups a ON a.id = t.topup_id"
            " WHERE a.idempotency_key = 'op-2026-16-1'"
        ).fetchone()["c"]
        assert topups == 1 and txs == 1
    finally:
        conn.close()
    wallet = client.get(
        "/api/wallet", headers={"X-Session-Token": student["token"]}
    ).json()
    assert wallet["available_kop"] == 100_000
    # Без ключа — каждая операция новая
    for _ in range(2):
        resp = client.post(
            "/api/wallet/topup", json={"amount_kop": 50_000},
            headers={"X-Session-Token": student["token"]},
        )
        assert resp.status_code == 200
    conn = _conn()
    try:
        null_key = conn.execute(
            "SELECT COUNT(*) c FROM acquiring_topups"
            " WHERE idempotency_key IS NULL"
        ).fetchone()["c"]
        assert null_key == 2
    finally:
        conn.close()
    wallet = client.get(
        "/api/wallet", headers={"X-Session-Token": student["token"]}
    ).json()
    assert wallet["available_kop"] == 200_000


def test_s16_wallet_topup_validation_limits(client):
    """TC-S16-014 — валидация суммы (спека wallet «Некорректная сумма»):
    неположительная/нецелая/сверх предела (500 000 ₽-эквивалент) → 422,
    записей нет, баланс не изменился (задача 16.2.1)."""
    student = _student(client, "s16w-valid@example.com")
    headers = {"X-Session-Token": student["token"]}
    for amount in (0, -100, ledger.TOPUP_MAX_KOP + 1):
        resp = client.post("/api/wallet/topup", json={"amount_kop": amount},
                           headers=headers)
        assert resp.status_code == 422, (amount, resp.text)
    # нецелая сумма — pydantic int (дробная часть → 422)
    resp = client.post("/api/wallet/topup", json={"amount_kop": 100.5},
                       headers=headers)
    assert resp.status_code == 422
    resp = client.post("/api/wallet/topup", json={"amount_kop": "abc"},
                       headers=headers)
    assert resp.status_code == 422
    conn = _conn()
    try:
        assert conn.execute(
            "SELECT COUNT(*) c FROM acquiring_topups"
        ).fetchone()["c"] == 0
        assert conn.execute(
            "SELECT COUNT(*) c FROM transactions"
        ).fetchone()["c"] == 0
    finally:
        conn.close()


def test_s16_wallet_isolation_between_students(client):
    """TC-S16-017 — чужой кошелек недоступен (спека wallet): кошелек Б
    показывает ТОЛЬКО данные Б; параметра владельца в API нет —
    user_id только из сессии (задача 16.2.1)."""
    a = _student(client, "s16w-a@example.com")
    b = _student(client, "s16w-b@example.com")
    client.post("/api/wallet/topup", json={"amount_kop": 300_000},
                headers={"X-Session-Token": a["token"]})
    wallet_b = client.get(
        "/api/wallet", headers={"X-Session-Token": b["token"]}
    ).json()
    assert wallet_b["available_kop"] == 0
    assert wallet_b["transactions"] == []


# --- 16.2.2: инструкторская экономика ------------------------------------------


def test_s16_instructor_price_save_validate_reset(client):
    """TC-S16-018 — цена часа (FR-100): сохраняется; валидируется
    (отрицательная → 422, прежнее значение сохранено); NULL-сброс —
    явное поле; GET economy отражает (задача 16.2.2)."""
    _instructor_via_approve(client, "s16p@example.com")
    login = client.post(
        "/api/auth/login",
        json={"email": "s16p@example.com", "password": "Instr1616"},
    )
    headers = {"X-Session-Token": login.json()["token"]}
    economy = client.get("/api/instructor/economy", headers=headers).json()
    assert economy["ok"] is True
    assert economy["price_per_hour_rub"] is None
    assert economy["commission_percent"] == 10  # DEFAULT схемы (FR-109)
    resp = client.put("/api/instructor/price",
                      json={"price_per_hour_rub": 1500}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["price_per_hour_rub"] == 1500
    resp = client.put("/api/instructor/price",
                      json={"price_per_hour_rub": -5}, headers=headers)
    assert resp.status_code == 422
    economy = client.get("/api/instructor/economy", headers=headers).json()
    assert economy["price_per_hour_rub"] == 1500  # прежнее сохранено
    # нецелое → 422 (pydantic int)
    resp = client.put("/api/instructor/price",
                      json={"price_per_hour_rub": 1.5}, headers=headers)
    assert resp.status_code == 422
    # NULL-сброс — явное поле
    resp = client.put("/api/instructor/price",
                      json={"price_per_hour_rub": None}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["price_per_hour_rub"] is None
    # ученик на инструкторский эндпоинт — 403
    student = _student(client, "s16p-student@example.com")
    resp = client.get(
        "/api/instructor/economy",
        headers={"X-Session-Token": student["token"]},
    )
    assert resp.status_code == 403


def test_s16_instructor_earnings_month_by_student(client):
    """TC-S16-018b — статистика месяца (FR-110): посевные release
    (10% и 0% комиссии) → разбивка по ученикам net=gross−fee + итог
    месяца; месяц без заработка — нули (задача 16.2.2)."""
    instructor_id = _instructor_via_approve(client, "s16e@example.com")
    login = client.post(
        "/api/auth/login",
        json={"email": "s16e@example.com", "password": "Instr1616"},
    )
    headers = {"X-Session-Token": login.json()["token"]}
    # Пустой месяц — нули без ошибки
    empty = client.get("/api/instructor/earnings", headers=headers).json()
    assert empty["ok"] is True
    assert empty["total_net_kop"] == 0 and empty["by_student"] == []
    # Посев release: ученик 1 (комиссия 10), ученик 2 (после смены на 0)
    conn = _conn()
    try:
        gross1 = 400_000
        fee1, net1 = ledger.release_gross_split(gross1, 10)
        ledger.insert_transaction(
            conn, tx_type="release", user_id=901, amount_kop=gross1,
            booking_id=901, student_id=901, instructor_id=instructor_id,
            amount_gross_kop=gross1, fee_kop=fee1, amount_net_kop=net1,
        )
        conn.commit()
        gross2 = 600_000
        ledger.insert_transaction(
            conn, tx_type="release", user_id=902, amount_kop=gross2,
            booking_id=902, student_id=902, instructor_id=instructor_id,
            amount_gross_kop=gross2, fee_kop=0, amount_net_kop=gross2,
        )
        conn.commit()
    finally:
        conn.close()
    data = client.get("/api/instructor/earnings", headers=headers).json()
    assert data["total_net_kop"] == net1 + gross2
    assert data["total_gross_kop"] == gross1 + gross2
    by_id = {e["student_id"]: e for e in data["by_student"]}
    assert by_id[901]["net_kop"] == net1
    assert by_id[902]["net_kop"] == gross2  # комиссия 0: net = gross
    # Чужая статистика недоступна (спека instructor-management)
    _instructor_via_approve(client, "s16e2@example.com")
    login2 = client.post(
        "/api/auth/login",
        json={"email": "s16e2@example.com", "password": "Instr1616"},
    )
    other = client.get(
        "/api/instructor/earnings",
        headers={"X-Session-Token": login2.json()["token"]},
    ).json()
    assert other["total_net_kop"] == 0


def _arrange_instructor_with_pending_payout(client, email="s16po@example.com"):
    """Аранжировка выплаты: инструктор через approve + release-посев
    (balance = net) + активная заявка 300 000. Возвращает кортеж
    (instructor_id, payout_id, balance_kop)."""
    instructor_id = _instructor_via_approve(client, email)
    conn = _conn()
    try:
        gross = 1_000_000
        fee, net = ledger.release_gross_split(gross, 10)
        ledger.insert_transaction(
            conn, tx_type="release", user_id=910, amount_kop=gross,
            booking_id=910, student_id=910, instructor_id=instructor_id,
            amount_gross_kop=gross, fee_kop=fee, amount_net_kop=net,
        )
        conn.commit()
    finally:
        conn.close()
    resp = client.post(
        "/api/instructor/payouts",
        json={"amount_kop": 300_000, "bank": "Сбер", "phone": "+79000000000"},
        headers=_instr_headers(client, email),
    )
    assert resp.status_code == 200, resp.text
    return instructor_id, resp.json()["payout_id"], net


def _instr_headers(client, email, password="Instr1616"):
    login = client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )
    assert login.status_code == 200, login.text
    return {"X-Session-Token": login.json()["token"]}


def test_s16_instructor_payout_request_guards(client):
    """TC-S16-019 — заявка вывода (FR-111): создается при amount ≤
    balance; вторая активная → 409; сумма > balance → 422; bank/phone
    обязательны → 422; список своих заявок; баланс заявкой не
    замораживается (задача 16.2.2)."""
    instructor_id = _instructor_via_approve(client, "s16po@example.com")
    headers = _instr_headers(client, "s16po@example.com")
    # Баланс 0: заявка сверх → 422
    resp = client.post(
        "/api/instructor/payouts",
        json={"amount_kop": 50_000, "bank": "Сбер", "phone": "+79000000000"},
        headers=headers,
    )
    assert resp.status_code == 422
    # Посев release → balance
    conn = _conn()
    try:
        gross = 1_000_000
        fee, net = ledger.release_gross_split(gross, 10)
        ledger.insert_transaction(
            conn, tx_type="release", user_id=910, amount_kop=gross,
            booking_id=910, student_id=910, instructor_id=instructor_id,
            amount_gross_kop=gross, fee_kop=fee, amount_net_kop=net,
        )
        conn.commit()
    finally:
        conn.close()
    # bank/phone обязательны
    resp = client.post(
        "/api/instructor/payouts",
        json={"amount_kop": 50_000, "bank": "", "phone": "+79000000000"},
        headers=headers,
    )
    assert resp.status_code == 422
    resp = client.post(
        "/api/instructor/payouts",
        json={"amount_kop": 50_000, "bank": "Сбер", "phone": ""},
        headers=headers,
    )
    assert resp.status_code == 422
    # Заявка > balance → 422
    resp = client.post(
        "/api/instructor/payouts",
        json={"amount_kop": 5_000_000, "bank": "Сбер",
              "phone": "+79000000000"},
        headers=headers,
    )
    assert resp.status_code == 422
    # Успешная заявка: баланс НЕ изменился (заявка не замораживает)
    resp = client.post(
        "/api/instructor/payouts",
        json={"amount_kop": 300_000, "bank": "Сбер",
              "phone": "+79000000000"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    payout_id = resp.json()["payout_id"]
    economy = client.get("/api/instructor/economy", headers=headers).json()
    assert economy["balance_kop"] == net
    # Вторая активная → 409
    resp = client.post(
        "/api/instructor/payouts",
        json={"amount_kop": 10_000, "bank": "ВТБ", "phone": "+79000000001"},
        headers=headers,
    )
    assert resp.status_code == 409
    # Список своих
    listed = client.get("/api/instructor/payouts", headers=headers).json()
    assert [p["id"] for p in listed["payouts"]] == [payout_id]
    assert listed["payouts"][0]["status"] == "requested"
    assert listed["payouts"][0]["bank"] == "Сбер"


# --- 16.2.3: админ-контур --------------------------------------------------------


def test_s16_admin_transactions_filters_and_company_balance(client):
    """TC-S16-020 — журнал оператора (FR-113/114): все типы/пользователи,
    свежие сверху; фильтры тип/роль/юзер/период; company_balance_kop =
    SUM fee (задача 16.2.3)."""
    admin = admin_headers(client)
    # Реальные пользователи (JOIN журнала на users — роль фильтра)
    s1 = _student(client, "s16adm-a@example.com")
    s2 = _student(client, "s16adm-b@example.com")
    conn = _conn()
    try:
        ledger.insert_transaction(conn, tx_type="topup", user_id=s1["id"],
                                  amount_kop=100_000, topup_id=1)
        ledger.insert_transaction(conn, tx_type="hold", user_id=s1["id"],
                                  amount_kop=60_000, booking_id=800,
                                  student_id=s1["id"], instructor_id=s2["id"])
        ledger.insert_transaction(
            conn, tx_type="release", user_id=s1["id"], amount_kop=60_000,
            booking_id=800, student_id=s1["id"], instructor_id=s2["id"],
            amount_gross_kop=60_000, fee_kop=6_000, amount_net_kop=54_000,
        )
        ledger.insert_transaction(conn, tx_type="topup", user_id=s2["id"],
                                  amount_kop=10_000, topup_id=2)
        conn.commit()
    finally:
        conn.close()
    admin = admin_headers(client)
    resp = client.get("/api/admin/transactions", headers=admin)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["company_balance_kop"] == 6_000
    types = [t["type"] for t in body["transactions"]]
    assert set(types) == {"topup", "hold", "release"}
    assert types == ["topup", "release", "hold", "topup"]  # свежие сверху
    # Фильтр типа
    only_release = client.get(
        "/api/admin/transactions?type=release", headers=admin
    ).json()
    assert [t["type"] for t in only_release["transactions"]] == ["release"]
    # Фильтр роли
    students = client.get(
        "/api/admin/transactions?role=student", headers=admin
    ).json()
    assert {t["role"] for t in students["transactions"]} == {"student"}
    # Фильтр юзера
    mine = client.get(
        f"/api/admin/transactions?user_id={s2['id']}", headers=admin
    ).json()
    assert {t["user_id"] for t in mine["transactions"]} == {s2["id"]}
    # Фильтр периода: только будущая дата — пусто (валидное состояние)
    empty = client.get(
        "/api/admin/transactions?date_from=2030-01-01", headers=admin
    ).json()
    assert empty["transactions"] == []
    assert empty["company_balance_kop"] == 6_000  # баланс не фильтруется
    # Неверный тип → 422
    assert client.get(
        "/api/admin/transactions?type=hack", headers=admin
    ).status_code == 422
    assert client.get(
        "/api/admin/transactions?date_from=2026-02-30", headers=admin
    ).status_code == 422
    # Доступ: сессия ученика не заменяет админ-токен (401)
    student = _student(client, "s16adm-st@example.com")
    assert client.get(
        "/api/admin/transactions",
        headers={"X-Session-Token": student["token"]},
    ).status_code == 401


def test_s16_admin_payout_confirm_and_insufficiency(client):
    """TC-S16-021 — подтверждение выплаты оператором (FR-112): ровно одна
    payout-транзакция, balance−, статус paid; повтор → 409; недостаток —
    409 без списания, заявка остается requested (задача 16.2.3)."""
    instructor_id, payout_id, net = _arrange_instructor_with_pending_payout(
        client, "s16conf@example.com"
    )
    admin = admin_headers(client)
    # Очередь requested содержит заявку
    queue = client.get("/api/admin/payouts", headers=admin).json()
    assert [p["id"] for p in queue["payouts"]] == [payout_id]
    # Искусственное списание (имитация «суммарные списания уменьшили
    # баланс» — спека payouts): balance → net − 300_000 < amount
    conn = _conn()
    try:
        ledger.insert_transaction(
            conn, tx_type="payout", user_id=instructor_id, amount_kop=net,
        )
        conn.commit()
        balance_after = ledger.instructor_balances(conn, instructor_id)
        assert balance_after["balance_kop"] < 300_000
    finally:
        conn.close()
    # Недостача: 409 без списания, заявка ОСТАЕТСЯ requested
    resp = client.post(f"/api/admin/payouts/{payout_id}/confirm", headers=admin)
    assert resp.status_code == 409, resp.text
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT status FROM payouts WHERE id = ?", (payout_id,)
        ).fetchone()
        assert row["status"] == "requested"
        assert conn.execute(
            "SELECT COUNT(*) c FROM transactions WHERE payout_id = ?",
            (payout_id,),
        ).fetchone()["c"] == 0
    finally:
        conn.close()
    # Восстанавливаем баланс новым release (500 000, комиссия 10)
    conn = _conn()
    try:
        gross = 500_000
        fee, net2 = ledger.release_gross_split(gross, 10)
        ledger.insert_transaction(
            conn, tx_type="release", user_id=910, amount_kop=gross,
            booking_id=911, student_id=910, instructor_id=instructor_id,
            amount_gross_kop=gross, fee_kop=fee, amount_net_kop=net2,
        )
        conn.commit()
    finally:
        conn.close()
    conn = _conn()
    try:
        assert ledger.instructor_balances(conn, instructor_id)["balance_kop"] \
            >= 300_000
    finally:
        conn.close()
    # Успешный confirm: ровно одна транзакция, balance−, статус paid
    resp = client.post(f"/api/admin/payouts/{payout_id}/confirm", headers=admin)
    assert resp.status_code == 200, resp.text
    conn = _conn()
    try:
        txs = conn.execute(
            "SELECT * FROM transactions WHERE payout_id = ? AND type='payout'",
            (payout_id,),
        ).fetchall()
        assert len(txs) == 1
        row = conn.execute(
            "SELECT status, paid_at FROM payouts WHERE id = ?", (payout_id,)
        ).fetchone()
        assert row["status"] == "paid" and row["paid_at"] is not None
    finally:
        conn.close()
    balance_now = ledger.instructor_balances(_conn(), instructor_id)
    assert balance_now["balance_kop"] < 300_000 + net2  # списание прошло
    # Повторный confirm → 409, дубль-транзакции нет
    resp = client.post(f"/api/admin/payouts/{payout_id}/confirm", headers=admin)
    assert resp.status_code == 409
    conn = _conn()
    try:
        assert conn.execute(
            "SELECT COUNT(*) c FROM transactions WHERE payout_id = ?",
            (payout_id,),
        ).fetchone()["c"] == 1
    finally:
        conn.close()
    # paid-заявка не в очереди requested
    queue = client.get("/api/admin/payouts", headers=admin).json()
    assert queue["payouts"] == []
    # Несуществующая заявка → 404
    assert client.post("/api/admin/payouts/999999/confirm",
                       headers=admin).status_code == 404


def _seed_dispute(client, *, suffix, gross=250_000):
    """Аранжировка спора: пара users (уникальные email по suffix),
    completed бронь с холдом, hold-транзакция, открытый спор.
    Возвращает (instructor_id, student_id, booking_id, dispute_id, gross)."""
    conn = _conn()
    try:
        conn.execute(
            "INSERT INTO users (surname, name, patronymic, email, phone,"
            " password_hash, role) VALUES ('Спорный', 'Инструктор', 'И.',"
            " ?, '+79000000009', 'x', 'instructor')",
            (f"s16d-instr-{suffix}@example.com",),
        )
        instructor_id = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (f"s16d-instr-{suffix}@example.com",),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO instructors (user_id, commission_percent)"
            " VALUES (?, 10)", (instructor_id,),
        )
        conn.execute(
            "INSERT INTO users (surname, name, patronymic, email, phone,"
            " password_hash, role) VALUES ('Спорный', 'Ученик', 'У.',"
            " ?, '+79000000010', 'x', 'student')",
            (f"s16d-student-{suffix}@example.com",),
        )
        real_student = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (f"s16d-student-{suffix}@example.com",),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO booking (student_id, instructor_id, availability_id,"
            " lesson_date, status, hold_amount_kop, completed_at)"
            " VALUES (?, ?, 1, '2026-01-10', 'completed', ?, datetime('now'))",
            (real_student, instructor_id, gross),
        )
        booking_id = int(conn.execute(
            "SELECT id FROM booking WHERE student_id = ?", (real_student,)
        ).fetchone()[0])
        ledger.insert_transaction(
            conn, tx_type="hold", user_id=real_student, amount_kop=gross,
            booking_id=booking_id, student_id=real_student,
            instructor_id=instructor_id,
        )
        conn.commit()
        conn.execute(
            "INSERT INTO booking_disputes (booking_id, student_id, comment)"
            " VALUES (?, ?, 'Качество занятия не устроило')",
            (booking_id, real_student),
        )
        conn.commit()
        dispute_id = conn.execute(
            "SELECT id FROM booking_disputes WHERE booking_id = ?",
            (booking_id,),
        ).fetchone()[0]
    finally:
        conn.close()
    return instructor_id, real_student, booking_id, int(dispute_id), gross


def test_s16_admin_disputes_resolve_release_refund(client):
    """TC-S16-022 — решение спора оператором (FR-108): release (fee/net
    по текущей комиссии) и refund (полный возврат) закрывают спор и холд
    РОВНО одной транзакцией; комментарий обязателен (422); повторное
    решение → 409 (задача 16.2.3)."""
    admin = admin_headers(client)
    # Список открытых
    instr_id, student_id, booking_id, dispute_id, gross = _seed_dispute(
        client, suffix="ref"
    )
    open_list = client.get("/api/admin/disputes", headers=admin).json()
    assert len(open_list["disputes"]) == 1
    assert open_list["disputes"][0]["hold_amount_kop"] == gross
    assert open_list["disputes"][0]["student_full_name"] == "Спорный Ученик У."
    # Решение без комментария → 422
    resp = client.post(
        f"/api/admin/disputes/{dispute_id}/resolve",
        json={"resolution": "refund", "comment": ""},
        headers=admin,
    )
    assert resp.status_code == 422
    # Неизвестное решение → 422
    resp = client.post(
        f"/api/admin/disputes/{dispute_id}/resolve",
        json={"resolution": "cancel", "comment": "х"},
        headers=admin,
    )
    assert resp.status_code == 422
    # resolve refund: полный возврат, спор закрыт
    resp = client.post(
        f"/api/admin/disputes/{dispute_id}/resolve",
        json={"resolution": "refund", "comment": "Подтверждено учеником"},
        headers=admin,
    )
    assert resp.status_code == 200, resp.text
    conn = _conn()
    try:
        tx = conn.execute(
            "SELECT * FROM transactions WHERE booking_id = ?"
            " AND type = 'refund'", (booking_id,),
        ).fetchone()
        assert tx is not None and tx["amount_kop"] == gross
        dispute = conn.execute(
            "SELECT resolution, operator_comment, resolved_at"
            " FROM booking_disputes WHERE id = ?", (dispute_id,),
        ).fetchone()
        assert dispute["resolution"] == "refund"
        assert dispute["operator_comment"] == "Подтверждено учеником"
        assert dispute["resolved_at"] is not None
    finally:
        conn.close()
    # Повторное решение → 409
    resp = client.post(
        f"/api/admin/disputes/{dispute_id}/resolve",
        json={"resolution": "release", "comment": "поздно"},
        headers=admin,
    )
    assert resp.status_code == 409
    # Решенный спор не в открытых
    assert client.get("/api/admin/disputes", headers=admin).json()["disputes"] == []
    # release-ветка: второй спор (новая бронь) → release с fee/net
    instr2, stud2, book2, disp2, gross2 = _seed_dispute(
        client, suffix="rel", gross=200_000
    )
    resp = client.post(
        f"/api/admin/disputes/{disp2}/resolve",
        json={"resolution": "release", "comment": "Занятие состоялось"},
        headers=admin,
    )
    assert resp.status_code == 200, resp.text
    conn = _conn()
    try:
        tx = conn.execute(
            "SELECT * FROM transactions WHERE booking_id = ?"
            " AND type = 'release'", (book2,),
        ).fetchone()
        fee, net = ledger.release_gross_split(gross2, 10)
        assert tx["fee_kop"] == fee and tx["amount_net_kop"] == net
        assert tx["amount_gross_kop"] == gross2
    finally:
        conn.close()


def test_s16_admin_commission_and_yearly_commissions(client):
    """TC-S16-023 — комиссия оператором (FR-109) и таблица комиссий за
    год (FR-115): PUT 0–100 (границы; 101 → 422; не-инструктор → 404);
    GET commissions?year — агрегат посевных релизов; год без данных —
    нулевые строки инструкторов (факт 0); дефолт — текущий год
    (задача 16.2.3)."""
    admin = admin_headers(client)
    instructor_id = _instructor_via_approve(client, "s16c@example.com")
    # PUT границы
    resp = client.put(
        f"/api/admin/instructors/{instructor_id}/commission",
        json={"commission_percent": 25}, headers=admin,
    )
    assert resp.status_code == 200 and resp.json()["commission_percent"] == 25
    assert client.put(
        f"/api/admin/instructors/{instructor_id}/commission",
        json={"commission_percent": 101}, headers=admin,
    ).status_code == 422
    assert client.put(
        f"/api/admin/instructors/{instructor_id}/commission",
        json={"commission_percent": -1}, headers=admin,
    ).status_code == 422
    assert client.put(
        "/api/admin/instructors/999999/commission",
        json={"commission_percent": 10}, headers=admin,
    ).status_code == 404
    # Посев release за текущий год (комиссия 25) и «прошлый» год (fee 777)
    conn = _conn()
    try:
        gross = 200_000
        fee, net = ledger.release_gross_split(gross, 25)
        ledger.insert_transaction(
            conn, tx_type="release", user_id=940, amount_kop=gross,
            booking_id=940, student_id=940, instructor_id=instructor_id,
            amount_gross_kop=gross, fee_kop=fee, amount_net_kop=net,
        )
        conn.commit()
    finally:
        conn.close()
    import datetime
    year = datetime.datetime.now(datetime.timezone.utc).year
    data = client.get(f"/api/admin/commissions?year={year}", headers=admin).json()
    assert data["year"] == year
    row = next(
        c for c in data["commissions"]
        if c["instructor_id"] == instructor_id
    )
    assert row["fee_kop"] == fee  # 25% от 200000 = 50000
    # Дефолт — текущий год
    default = client.get("/api/admin/commissions", headers=admin).json()
    assert default["year"] == year
    # Год без данных: инструктор присутствует с нулевой строкой (факт 0)
    empty_year = client.get("/api/admin/commissions?year=2030", headers=admin).json()
    row_empty = next(
        c for c in empty_year["commissions"]
        if c["instructor_id"] == instructor_id
    )
    assert row_empty["fee_kop"] == 0 and row_empty["releases"] == 0
    # Неверный год → 422
    assert client.get(
        "/api/admin/commissions?year=abcd", headers=admin
    ).status_code == 422
