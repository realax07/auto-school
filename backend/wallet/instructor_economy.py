"""instructor_economy.py — инструкторская экономика (Спринт 16, задача
16.2.2; FR-100/110/111; design.md «API-контур»).

GET  /api/instructor/economy  — цена часа, комиссия, earned (Σrelease.net),
                               balance (заработанное − фактические выплаты);
                               перед чтением — ленивый свип.
PUT  /api/instructor/price    — цена часа: целые рубли ≥ 0; явное поле
                               price_per_hour_rub=None — сброс (занятия
                               бесплатны, брони без холда — FR-100).
                               Смена цены НЕ трогает существующие снапшоты
                               холдов (FR-101 — снапшот при брони).
GET  /api/instructor/earnings — месяц: разбивка release по ученикам + итог
                               месяца (агрегаты журнала, net — «все что
                               получил на руки»); gross/fee — справка.
POST /api/instructor/payouts  — заявка вывода СБП (мок, NFR-36): amount
                               ≤ balance (иначе 422), bank+phone
                               обязательны (422); guard ОДНОЙ активной
                               заявки — 409 (+ частичный UNIQUE
                               uq_payouts_one_pending страхует гонку,
                               NFR-35). Заявка баланс не замораживает
                               (СА-решение MVP).
GET  /api/instructor/payouts  — список своих заявок (банк/телефон видит
                               владелец; ADR-009 ПД: в логи не пишутся).

Гварды: require_role('instructor'); user_id только из сессии — чужая
статистика недоступна. ПД: без логирования сумм/идентификаторов.
"""
import sqlite3

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import backend.core.db as db
import backend.wallet.ledger as ledger
import backend.wallet.sweeps as sweeps
from backend.core.guards import _error, full_name, require_role

router = APIRouter()


class PricePayload(BaseModel):
    # int | None: явный NULL = сброс цены (FR-100). Дефолт — заглушка,
    # валидация в хендлере (конвенция модуля).
    price_per_hour_rub: int | None = 0


class PayoutPayload(BaseModel):
    amount_kop: int = 0
    bank: str = ""
    phone: str = ""


@router.get("/api/instructor/economy")
def economy(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Экономика инструктора (FR-109/110): цена часа, комиссия (текущая),
    earned_net и balance — SUM по журналу; перед чтением — ленивый свип
    (design «Точки вызова»: GET /api/instructor/economy)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        sweeps.wallet_sweep(conn)
        row = ledger.ensure_instructor_row(conn, instructor_id)
        balances = ledger.instructor_balances(conn, instructor_id)
        return {
            "ok": True,
            "price_per_hour_rub": row["price_per_hour_rub"],
            "commission_percent": row["commission_percent"],
            "earned_net_kop": balances["earned_net_kop"],
            "balance_kop": balances["balance_kop"],
            "paid_out_kop": balances["paid_out_kop"],
        }
    finally:
        conn.close()


@router.put("/api/instructor/price")
def set_price(
    data: PricePayload,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Цена часа (FR-100): целые рубли ≥ 0 (0 = бесплатное занятие —
    брони без холда; NULL = «цена не задана», легаси-путь 1:1).
    Снапшоты существующих броней/холдов НЕ пересчитываются."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err
    price = data.price_per_hour_rub
    if price is not None and price < 0:
        return _error(422, "Цена часа: неотрицательные целые рубли")

    conn = db.get_conn()
    try:
        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        ledger.ensure_instructor_row(conn, instructor_id)
        conn.execute(
            "UPDATE instructors SET price_per_hour_rub = ?,"
            " updated_at = datetime('now') WHERE user_id = ?",
            (price, instructor_id),
        )
        conn.execute("COMMIT")
        row = conn.execute(
            "SELECT price_per_hour_rub FROM instructors WHERE user_id = ?",
            (instructor_id,),
        ).fetchone()
    finally:
        conn.close()
    return {"ok": True, "price_per_hour_rub": row["price_per_hour_rub"]}


@router.get("/api/instructor/earnings")
def earnings(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Статистика месяца (FR-110): разбивка release по ученикам + итог
    месяца (net); месяц — текущий (UTC журнала). Пустой месяц — нули
    без ошибки (корректное пустое состояние)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        sweeps.wallet_sweep(conn)
        import datetime
        today = datetime.datetime.now(datetime.timezone.utc)
        data = ledger.month_earnings(
            conn, instructor_id, today.year, today.month
        )
        by_student = []
        for entry in data["by_student"]:
            student = conn.execute(
                "SELECT surname, name, patronymic FROM users WHERE id = ?",
                (entry["student_id"],),
            ).fetchone()
            by_student.append({
                **entry,
                "student_full_name": full_name(student) if student else "",
            })
        return {
            "ok": True,
            "year": today.year,
            "month": today.month,
            "total_net_kop": data["total_net_kop"],
            "total_gross_kop": data["total_gross_kop"],
            "total_fee_kop": data["total_fee_kop"],
            "by_student": by_student,
        }
    finally:
        conn.close()


@router.post("/api/instructor/payouts")
def create_payout(
    data: PayoutPayload,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Заявка вывода СБП (FR-111, мок NFR-36): amount ≤ balance (иначе
    422 — сумма больше доступного), bank+phone обязательны (422);
    одна активная заявка — 409 (guard + частичный UNIQUE)."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err
    if data.amount_kop <= 0:
        return _error(422, "Сумма: должна быть положительной (целые копейки)")
    if not data.bank.strip():
        return _error(422, "Банк: поле обязательно")
    if not data.phone.strip():
        return _error(422, "Телефон: поле обязательно")

    conn = db.get_conn()
    try:
        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        # Заявка баланс не замораживает — но сумма не может превышать
        # текущий balance (журнал = истина; СА-решение MVP).
        balances = ledger.instructor_balances(conn, instructor_id)
        if data.amount_kop > balances["balance_kop"]:
            conn.execute("ROLLBACK")
            return _error(
                422,
                "Сумма: превышает доступный баланс к выводу",
            )
        try:
            cur = conn.execute(
                "INSERT INTO payouts (instructor_id, amount_kop, bank, phone)"
                " VALUES (?, ?, ?, ?)",
                (instructor_id, data.amount_kop, data.bank.strip(),
                 data.phone.strip()),
            )
            lastrowid = cur.lastrowid
            assert lastrowid is not None
            payout_id = int(lastrowid)
            conn.execute("COMMIT")
        except sqlite3.IntegrityError:
            # uq_payouts_one_pending — гонка/повтор: активная заявка
            # уже есть (NFR-35).
            conn.execute("ROLLBACK")
            return _error(409, "У вас уже есть активная заявка на вывод")
    finally:
        conn.close()
    return {"ok": True, "payout_id": payout_id, "status": "requested"}


@router.get("/api/instructor/payouts")
def my_payouts(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Список СВОИХ заявок вывода (FR-111): банк/телефон — только
    владельцу (ADR-009 ПД); бейджи статусов заявка/выплачено."""
    instructor_id, err = require_role(x_session_token, "instructor")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT id, amount_kop, channel, bank, phone, status,"
            " requested_at, paid_at FROM payouts"
            " WHERE instructor_id = ?"
            " ORDER BY requested_at DESC, id DESC",
            (instructor_id,),
        ).fetchall()
    finally:
        conn.close()
    return {
        "ok": True,
        "payouts": [
            {
                "id": row["id"],
                "amount_kop": row["amount_kop"],
                "channel": row["channel"],
                "bank": row["bank"],
                "phone": row["phone"],
                "status": row["status"],
                "requested_at": row["requested_at"],
                "paid_at": row["paid_at"],
            }
            for row in rows
        ],
    }
