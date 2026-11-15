"""admin_transactions.py — админ-контур экономики (Спринт 16, задача
16.2.3; FR-108/109/112/113/114/115; design.md «API-контур»; раздел
админки «Транзакции» — дельта specs/admin-transactions).

GET  /api/admin/transactions?type&role&user_id&date_from&date_to
     — весь журнал всех типов и пользователей (без пагинации-урезания
     домена — решение СА: выдаются все с фильтрами, свежие сверху) +
     company_balance_kop (Σrelease.fee — «балланс компании нужен
     в админке», FR-114). Перед чтением — ленивый свип.
GET  /api/admin/payouts?status=requested — очередь активных заявок
     вывода (банк/телефон СБП видит оператор — ADR-009 ПД; в логи не
     пишутся).
POST /api/admin/payouts/{id}/confirm — подтверждение выплаты: guard
     balance ≥ amount ИНАЧЕ 409 (заявка ОСТАЕТСЯ requested, списания
     нет — журнал правды); транзакция payout ровно одна на заявку
     (частичный UNIQUE uq_tx_payout_per_request — NFR-35, идемпотентно);
     повторное подтверждение → 409.
GET  /api/admin/disputes?status=open — открытые споры (бронь, ученик,
     инструктор, комментарий, суммы холда).
POST /api/admin/disputes/{id}/resolve {resolution: release|refund,
     comment обязателен} — решение закрывает спор и холд РОВНО ОДНОЙ
     журнальной транзакцией (release — fee/net по ТЕКУЩЕЙ комиссии;
     refund — полный возврат); повторное решение → 409.
PUT  /api/admin/instructors/{id}/commission {commission_percent}
     — целые 0–100 (иначе 422); применяется к ПОСЛЕДУЮЩИМ релизам
     (текущее значение на момент релиза), существующие транзакции не
     пересчитываются (FR-109).
GET  /api/admin/commissions?year=YYYY — инструктор × SUM fee за год
     (дефолт текущий год); инструктор без релизов года — строка с 0
     (факт 0, FR-115).

Доступ: require_admin (X-Admin-Token) — ученик/инструктор с сессией
журнал не получают (401). SQL параметризованный (NFR-10←NFR-3).
"""
import datetime
import re
import sqlite3

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import backend.core.db as db
import backend.wallet.ledger as ledger
import backend.wallet.sweeps as sweeps
from backend.auth.admin import require_admin
from backend.core.guards import _error, full_name

router = APIRouter()

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ROLES = ("student", "instructor")
_DISPUTE_RESOLUTIONS = ("release", "refund")


def _unauthorized() -> JSONResponse:
    return JSONResponse(status_code=401, content={"ok": False})


class ResolvePayload(BaseModel):
    resolution: str = ""
    comment: str = ""


class CommissionPayload(BaseModel):
    commission_percent: int = -1


def _valid_date(value: str) -> bool:
    """Форма ISO YYYY-MM-DD + существующий календарный день (прецедент
    MIN-4 арх-ревью: «2026-02-30» — не дата)."""
    if not _DATE_RE.match(value or ""):
        return False
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return False
    return True


@router.get("/api/admin/transactions")
def admin_transactions(
    type: str = "",
    role: str = "",
    user_id: int = 0,
    date_from: str = "",
    date_to: str = "",
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    """Журнал всех транзакций с фильтрами (FR-113) + баланс компании
    (FR-114). Фильтры: type ∈ журнальных типов (иначе 422), role
    (student/instructor), user_id, период дат [date_from; date_to]
    включительно по created_at (UTC журнала). Пустой результат —
    валидное состояние."""
    try:
        require_admin(x_admin_token=x_admin_token)
    except HTTPException:
        return _unauthorized()

    if type and type not in ledger.TX_TYPES:
        return _error(422, "Тип: неизвестный тип транзакции")
    if role and role not in _ROLES:
        return _error(422, "Роль: student или instructor")
    if date_from and not _valid_date(date_from):
        return _error(422, "Дата от: ожидается ГГГГ-ММ-ДД")
    if date_to and not _valid_date(date_to):
        return _error(422, "Дата до: ожидается ГГГГ-ММ-ДД")

    conn = db.get_conn()
    try:
        sweeps.wallet_sweep(conn)
        where = ["1 = 1"]
        params: list = []
        if type:
            where.append("t.type = ?")
            params.append(type)
        if role or user_id:
            where.append("t.user_id = u.id")
        if role:
            where.append("u.role = ?")
            params.append(role)
        if user_id:
            where.append("t.user_id = ?")
            params.append(user_id)
        if date_from:
            where.append("t.created_at >= ?")
            params.append(f"{date_from} 00:00:00")
        if date_to:
            where.append("t.created_at <= ?")
            params.append(f"{date_to} 23:59:59")
        rows = conn.execute(
            "SELECT t.id, t.type, t.user_id, u.role AS role,"
            " t.amount_kop, t.booking_id, t.payout_id, t.topup_id,"
            " t.student_id, t.instructor_id, t.amount_gross_kop, t.fee_kop,"
            " t.amount_net_kop, t.created_at"
            " FROM transactions AS t JOIN users AS u ON u.id = t.user_id"
            f" WHERE {' AND '.join(where)}"
            " ORDER BY t.created_at DESC, t.id DESC",
            tuple(params),
        ).fetchall()
        company_balance = ledger.company_balance(conn)
    finally:
        conn.close()
    return {
        "ok": True,
        "company_balance_kop": company_balance,
        "transactions": [
            {
                "id": row["id"],
                "type": row["type"],
                "created_at": row["created_at"],
                "role": row["role"],
                "user_id": row["user_id"],
                "amount_kop": row["amount_kop"],
                "booking_id": row["booking_id"],
                "payout_id": row["payout_id"],
                "topup_id": row["topup_id"],
                "amount_gross_kop": row["amount_gross_kop"],
                "fee_kop": row["fee_kop"],
                "amount_net_kop": row["amount_net_kop"],
            }
            for row in rows
        ],
    }


@router.get("/api/admin/payouts")
def admin_payouts(
    status: str = "requested",
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    """Заявки вывода по статусу (дефолт — очередь requested, FR-112)."""
    try:
        require_admin(x_admin_token=x_admin_token)
    except HTTPException:
        return _unauthorized()
    if status not in ("requested", "paid", "all"):
        return _error(422, "Статус: requested, paid или all")

    conn = db.get_conn()
    try:
        sweeps.wallet_sweep(conn)
        if status == "all":
            rows = conn.execute(
                "SELECT p.id, p.instructor_id, p.amount_kop, p.channel,"
                " p.bank, p.phone, p.status, p.requested_at, p.paid_at"
                " FROM payouts AS p"
                " ORDER BY p.requested_at DESC, p.id DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT p.id, p.instructor_id, p.amount_kop, p.channel,"
                " p.bank, p.phone, p.status, p.requested_at, p.paid_at"
                " FROM payouts AS p WHERE p.status = ?"
                " ORDER BY p.requested_at DESC, p.id DESC",
                (status,),
            ).fetchall()
        payouts = []
        for row in rows:
            instructor = conn.execute(
                "SELECT surname, name, patronymic FROM users WHERE id = ?",
                (row["instructor_id"],),
            ).fetchone()
            payouts.append({
                "id": row["id"],
                "instructor_id": row["instructor_id"],
                "instructor_full_name": (
                    full_name(instructor) if instructor else ""
                ),
                "amount_kop": row["amount_kop"],
                "channel": row["channel"],
                "bank": row["bank"],
                "phone": row["phone"],
                "status": row["status"],
                "requested_at": row["requested_at"],
                "paid_at": row["paid_at"],
            })
    finally:
        conn.close()
    return {"ok": True, "payouts": payouts}


@router.post("/api/admin/payouts/{payout_id}/confirm")
def admin_payout_confirm(
    payout_id: int,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    """Подтверждение выплаты (FR-112): ровно одна payout-транзакция
    (частичный UNIQUE), balance −= amount; недостаток — 409 БЕЗ списания
    (заявка остается requested — деньги не списаны, журнал правды);
    повторное подтверждение → 409."""
    try:
        require_admin(x_admin_token=x_admin_token)
    except HTTPException:
        return _unauthorized()

    conn = db.get_conn()
    try:
        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT id, instructor_id, amount_kop, status FROM payouts"
            " WHERE id = ?",
            (payout_id,),
        ).fetchone()
        if row is None:
            conn.execute("ROLLBACK")
            return _error(404, "Заявка не найдена")
        if row["status"] != "requested":
            conn.execute("ROLLBACK")
            return _error(409, "Заявка уже подтверждена")
        balances = ledger.instructor_balances(conn, row["instructor_id"])
        if balances["balance_kop"] < row["amount_kop"]:
            # Недостача к моменту подтверждения: без списания, заявка
            # остается активной (design «Конечные автоматы: Выплата»).
            conn.execute("ROLLBACK")
            return JSONResponse(
                status_code=409,
                content={
                    "ok": False,
                    "error": (
                        "Недостаточно средств на балансе инструктора — "
                        "заявка осталась активной"
                    ),
                    "balance_kop": balances["balance_kop"],
                    "amount_kop": row["amount_kop"],
                },
            )
        try:
            ledger.insert_transaction(
                conn,
                tx_type="payout",
                user_id=row["instructor_id"],
                amount_kop=row["amount_kop"],
                payout_id=row["id"],
            )
        except sqlite3.IntegrityError:
            # Ровно одна транзакция на заявку (NFR-35, гонка повторных
            # confirm).
            conn.execute("ROLLBACK")
            return _error(409, "Заявка уже подтверждена")
        conn.execute(
            "UPDATE payouts SET status = 'paid', paid_at = datetime('now')"
            " WHERE id = ? AND status = 'requested'",
            (payout_id,),
        )
        conn.execute("COMMIT")
    finally:
        conn.close()
    conn = db.get_conn()
    try:
        balances = ledger.instructor_balances(conn, row["instructor_id"])
    finally:
        conn.close()
    return {
        "ok": True,
        "payout_id": payout_id,
        "amount_kop": row["amount_kop"],
        "balance_kop": balances["balance_kop"],
    }


@router.get("/api/admin/disputes")
def admin_disputes(
    status: str = "open",
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    """Споры по статусу (дефолт — открытые, FR-108): бронь, ученик,
    инструктор, комментарий, суммы холда — материал решения оператора."""
    try:
        require_admin(x_admin_token=x_admin_token)
    except HTTPException:
        return _unauthorized()
    if status not in ("open", "resolved", "all"):
        return _error(422, "Статус: open, resolved или all")

    conn = db.get_conn()
    try:
        sweeps.wallet_sweep(conn)
        where = ""
        params: list = []
        if status == "open":
            where = " WHERE d.resolution IS NULL"
        elif status == "resolved":
            where = " WHERE d.resolution IS NOT NULL"
        rows = conn.execute(
            "SELECT d.id, d.booking_id, d.student_id, d.comment,"
            " d.resolution, d.operator_comment, d.created_at, d.resolved_at,"
            " b.instructor_id, b.hold_amount_kop, b.status AS booking_status"
            " FROM booking_disputes AS d"
            " JOIN booking AS b ON b.id = d.booking_id"
            f"{where} ORDER BY d.created_at DESC, d.id DESC",
            tuple(params),
        ).fetchall()
        disputes = []
        for row in rows:
            student = conn.execute(
                "SELECT surname, name, patronymic FROM users WHERE id = ?",
                (row["student_id"],),
            ).fetchone()
            instructor = conn.execute(
                "SELECT surname, name, patronymic FROM users WHERE id = ?",
                (row["instructor_id"],),
            ).fetchone()
            disputes.append({
                "id": row["id"],
                "booking_id": row["booking_id"],
                "student_id": row["student_id"],
                "student_full_name": full_name(student) if student else "",
                "instructor_id": row["instructor_id"],
                "instructor_full_name": (
                    full_name(instructor) if instructor else ""
                ),
                "hold_amount_kop": row["hold_amount_kop"],
                "booking_status": row["booking_status"],
                "comment": row["comment"],
                "resolution": row["resolution"],
                "operator_comment": row["operator_comment"],
                "created_at": row["created_at"],
                "resolved_at": row["resolved_at"],
            })
    finally:
        conn.close()
    return {"ok": True, "disputes": disputes}


@router.post("/api/admin/disputes/{dispute_id}/resolve")
def admin_dispute_resolve(
    dispute_id: int,
    data: ResolvePayload,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    """Решение по спору (FR-108): release (fee/net по текущей комиссии,
    инструктору net, платформе fee) ИЛИ refund (полный возврат ученику);
    комментарий обязателен (422); решение закрывает спор и холд ровно
    одной транзакцией; повторное — 409."""
    try:
        require_admin(x_admin_token=x_admin_token)
    except HTTPException:
        return _unauthorized()
    resolution = (data.resolution or "").strip()
    if resolution not in _DISPUTE_RESOLUTIONS:
        return _error(422, "Решение: release или refund")
    if not (data.comment or "").strip():
        return _error(422, "Комментарий: поле обязательно")

    conn = db.get_conn()
    try:
        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        dispute = conn.execute(
            "SELECT id, booking_id, student_id, resolution"
            " FROM booking_disputes WHERE id = ?",
            (dispute_id,),
        ).fetchone()
        if dispute is None:
            conn.execute("ROLLBACK")
            return _error(404, "Спор не найден")
        if dispute["resolution"] is not None:
            conn.execute("ROLLBACK")
            return _error(409, "Спор уже решен")
        booking = conn.execute(
            "SELECT id, student_id, instructor_id, hold_amount_kop"
            " FROM booking WHERE id = ?",
            (dispute["booking_id"],),
        ).fetchone()
        gross = booking["hold_amount_kop"] if booking else 0
        if gross <= 0:
            # Спор без холда не должен был открыться (МАЖ-2 гвард
            # ученического эндпоинта); решение невозможно — журнальный
            # CHECK amount_kop > 0 не пропустит нулевой исход.
            conn.execute("ROLLBACK")
            return _error(409, "По брони нет живого холда")
        instructor_row = ledger.ensure_instructor_row(
            conn, booking["instructor_id"]
        )
        try:
            if resolution == "release":
                fee_kop, net_kop = ledger.release_gross_split(
                    gross, instructor_row["commission_percent"]
                )
                ledger.insert_transaction(
                    conn,
                    tx_type="release",
                    user_id=dispute["student_id"],
                    amount_kop=gross,
                    booking_id=booking["id"],
                    student_id=dispute["student_id"],
                    instructor_id=booking["instructor_id"],
                    amount_gross_kop=gross,
                    fee_kop=fee_kop,
                    amount_net_kop=net_kop,
                )
            else:
                ledger.insert_transaction(
                    conn,
                    tx_type="refund",
                    user_id=dispute["student_id"],
                    amount_kop=gross,
                    booking_id=booking["id"],
                    student_id=dispute["student_id"],
                    instructor_id=booking["instructor_id"],
                )
        except sqlite3.IntegrityError:
            # Холд уже исполнен (частичный UNIQUE, NFR-35) — спор
            # не может быть решен повторным движением.
            conn.execute("ROLLBACK")
            return _error(409, "Холд уже исполнен — решение невозможно")
        conn.execute(
            "UPDATE booking_disputes SET resolution = ?,"
            " operator_comment = ?, resolved_at = datetime('now')"
            " WHERE id = ? AND resolution IS NULL",
            (resolution, data.comment.strip(), dispute_id),
        )
        conn.execute("COMMIT")
    finally:
        conn.close()
    return {"ok": True, "dispute_id": dispute_id, "resolution": resolution}


@router.put("/api/admin/instructors/{instructor_id}/commission")
def admin_set_commission(
    instructor_id: int,
    data: CommissionPayload,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    """Комиссия инструктора (FR-109, дословно «в админке ставится каждому
    инструктору»): целые 0–100 (иначе 422); инструктор не найден → 404;
    применяется к последующим релизам."""
    try:
        require_admin(x_admin_token=x_admin_token)
    except HTTPException:
        return _unauthorized()
    value = data.commission_percent
    if not 0 <= value <= 100:
        return _error(422, "Комиссия: целые проценты 0–100")

    conn = db.get_conn()
    try:
        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        user = conn.execute(
            "SELECT id FROM users WHERE id = ? AND role = 'instructor'",
            (instructor_id,),
        ).fetchone()
        if user is None:
            conn.execute("ROLLBACK")
            return _error(404, "Инструктор не найден")
        ledger.ensure_instructor_row(conn, instructor_id)
        conn.execute(
            "UPDATE instructors SET commission_percent = ?,"
            " updated_at = datetime('now') WHERE user_id = ?",
            (value, instructor_id),
        )
        conn.execute("COMMIT")
    finally:
        conn.close()
    return {
        "ok": True,
        "instructor_id": instructor_id,
        "commission_percent": value,
    }


@router.get("/api/admin/commissions")
def admin_commissions(
    year: int = 0,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    """Комиссии инструкторов за год (FR-115): инструктор × SUM fee
    release-транзакций года; дефолт — текущий год; без релизов за год —
    нулевые строки (факт 0)."""
    try:
        require_admin(x_admin_token=x_admin_token)
    except HTTPException:
        return _unauthorized()
    if year <= 0:
        year = datetime.datetime.now(datetime.timezone.utc).year
    if not 2000 <= year <= 9999:
        return _error(422, "Год: YYYY")

    conn = db.get_conn()
    try:
        sweeps.wallet_sweep(conn)
        rows = ledger.yearly_commissions(conn, year)
        commissions = []
        for row in rows:
            instructor = conn.execute(
                "SELECT surname, name, patronymic FROM users WHERE id = ?",
                (row["instructor_id"],),
            ).fetchone()
            commissions.append({
                "instructor_id": row["instructor_id"],
                "instructor_full_name": (
                    full_name(instructor) if instructor else ""
                ),
                "fee_kop": row["fee_kop"],
                "releases": row["releases"],
            })
    finally:
        conn.close()
    return {"ok": True, "year": year, "commissions": commissions}
