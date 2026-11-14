"""wallets.py — кошелек ученика (Спринт 16, задача 16.2.1; FR-98/99;
design.md «API-контур», «Конечные автоматы: Пополнение (мок)»).

GET  /api/wallet — балансы (SUM по журналу — ledger.student_balances,
единственный источник истины) + история транзакций владельца; ПЕРЕД
чтением — ленивый свип исходов холдов (sweeps.wallet_sweep, BEGIN
IMMEDIATE: авто-релиз ≥24ч после «проведено»; расхождение материализации
— секунды-минуты, детерминизм сумм не страдает — design «Сознательные
ограничения»).

POST /api/wallet/topup — мок-пополнение (NFR-36: provider='mock'
захардкожен, внешних вызовов нет): запись acquiring_topups (ОТДЕЛЬНО от
журнала — решение Заказчика «База эквайринга наверное отдельно должна
быть») + транзакция topup. Идемпотентность (NFR-35): клиентский
X-Idempotency-Key → частичный UNIQUE uq_topups_idem — повтор с тем же
ключом возвращает результат первой операции, дубля нет; без ключа
каждый вызов — новая операция. provider_payment_id не заполняется —
поле будущего провайдера. Валидация суммы: положительная целая (копейки
— NFR-33), верхний предел MVP 500 000 ₽-эквивалент — защита от опечаток.

Гварды: require_role (ученик); чужой кошелек недоступен — user_id
берется ТОЛЬКО из сессии, параметров владельца в API нет. ПД: суммы и
идентификаторы в текстах логов не пишутся (наследование NFR-логов —
логирования в домене нет).
"""
import sqlite3

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import backend.core.db as db
import backend.wallet.ledger as ledger
import backend.wallet.sweeps as sweeps
from backend.core.guards import _error, require_role

router = APIRouter()

# Краткие описания типов журнала для истории кошелька (RU — домен сервиса).
_TX_LABELS = {
    "topup": "Пополнение кошелька",
    "hold": "Заморозка средств — бронь занятия",
    "release": "Списание — занятие проведено",
    "refund": "Возврат средств — бронь отменена",
    "payout": "Выплата инструктору",
}
# Направление движения денег владельца кошелька (+ приходит, − уходит).
_TX_SIGNS = {"topup": 1, "refund": 1, "hold": -1, "release": -1, "payout": -1}


class TopupPayload(BaseModel):
    # Дефолт вместо Pydantic-required — валидация в хендлере
    # (единая конвенция сообщений).
    amount_kop: int = 0


def _history(conn: sqlite3.Connection, student_id: int) -> list[dict]:
    """История владельца: его движения из журнала, свежие сверху.
    release-строки приходят с user_id = ученик (его холд исполнен)."""
    rows = conn.execute(
        "SELECT id, type, amount_kop, booking_id, payout_id, topup_id,"
        " amount_gross_kop, fee_kop, amount_net_kop, note, created_at"
        " FROM transactions WHERE user_id = ?"
        " ORDER BY created_at DESC, id DESC",
        (student_id,),
    ).fetchall()
    items = []
    for row in rows:
        if row["type"] == "release":
            # Для ученика расход = gross (замороженное ушло инструктору);
            # net/fee — справка о разбиении (восстанавливаемость, NFR-34).
            shown = row["amount_gross_kop"] or row["amount_kop"]
        else:
            shown = row["amount_kop"]
        items.append({
            "id": row["id"],
            "type": row["type"],
            "created_at": row["created_at"],
            "amount_kop": shown,
            "sign": _TX_SIGNS[row["type"]],
            "description": _TX_LABELS[row["type"]],
            "booking_id": row["booking_id"],
        })
    return items


@router.get("/api/wallet")
def wallet(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Кошелек ученика (FR-98): available/frozen/total (SUM по журналу)
    + история транзакций владельца; перед чтением — ленивый свип.
    Кошелек нового ученика — корректные нули (0/0/0)."""
    student_id, err = require_role(x_session_token, "student")
    if err is not None:
        return err

    conn = db.get_conn()
    try:
        # Ленивый свип (авто-релиз) ДО вычисления балансов — design
        # «Точки вызова»: GET /api/wallet.
        sweeps.wallet_sweep(conn)
        balances = ledger.student_balances(conn, student_id)
        return {
            "ok": True,
            **balances,
            "transactions": _history(conn, student_id),
        }
    finally:
        conn.close()


@router.post("/api/wallet/topup")
def wallet_topup(
    data: TopupPayload,
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
):
    """Мок-пополнение (FR-99, NFR-35/36): acquiring_topups + транзакция
    topup; идемпотентность по клиентскому ключу; суммы — целые копейки,
    0 < amount ≤ TOPUP_MAX_KOP (500 000 ₽-эквивалент) → иначе 422,
    записей нет."""
    student_id, err = require_role(x_session_token, "student")
    if err is not None:
        return err
    if data.amount_kop <= 0:
        return _error(422, "Сумма: должна быть положительной (целые копейки)")
    if data.amount_kop > ledger.TOPUP_MAX_KOP:
        return _error(422, "Сумма: превышает предел одной операции пополнения")

    # Ключ идемпотентности: пустой заголовок приравнен к отсутствующему.
    idempotency_key = (x_idempotency_key or "").strip() or None

    conn = db.get_conn()
    try:
        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        try:
            if idempotency_key is not None:
                existing = conn.execute(
                    "SELECT id FROM acquiring_topups WHERE idempotency_key = ?",
                    (idempotency_key,),
                ).fetchone()
                if existing is not None:
                    # Повтор с тем же ключом — результат первой операции
                    # (NFR-35): дубль-транзакции нет, баланс не удваивается.
                    conn.execute("COMMIT")
                    return _topup_result(conn, existing["id"])
            cur = conn.execute(
                "INSERT INTO acquiring_topups (student_id, amount_kop,"
                " idempotency_key) VALUES (?, ?, ?)",
                (student_id, data.amount_kop, idempotency_key),
            )
            topup_id = int(cur.lastrowid)
            ledger.insert_transaction(
                conn,
                tx_type="topup",
                user_id=student_id,
                amount_kop=data.amount_kop,
                topup_id=topup_id,
            )
            conn.execute("COMMIT")
        except sqlite3.IntegrityError:
            # Гонка двух повторов с одним ключом (частичный UNIQUE,
            # NFR-35): проигравший возвращает результат победителя.
            conn.execute("ROLLBACK")
            if idempotency_key is None:
                raise
            existing = conn.execute(
                "SELECT id FROM acquiring_topups WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing is None:
                return _error(409, "Пополнение: повтор не распознан")
            return _topup_result(conn, existing["id"])
    finally:
        conn.close()
    conn = db.get_conn()
    try:
        return _topup_result(conn, topup_id)
    finally:
        conn.close()


def _topup_result(conn: sqlite3.Connection, topup_id: int) -> JSONResponse | dict:
    """Единый ответ пополнения: факт topup + обновленный available.
    provider_payment_id не возвращается — мок его не заполняет (NFR-36)."""
    row = conn.execute(
        "SELECT id, student_id, amount_kop, status, created_at"
        " FROM acquiring_topups WHERE id = ?",
        (topup_id,),
    ).fetchone()
    balances = ledger.student_balances(conn, row["student_id"])
    return {
        "ok": True,
        "topup_id": row["id"],
        "amount_kop": row["amount_kop"],
        "status": row["status"],
        "available_kop": balances["available_kop"],
    }
