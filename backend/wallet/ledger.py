"""ledger.py — журнал денег и SUM-балансы (Спринт 16, задача 16.1.2;
design.md «Модель данных», «Денежные правила»; FR-98/106/109/114/115).

ЕДИНЫЙ источник истины о деньгах — append-only журнал transactions
(NFR-34): балансы НЕ хранятся колонками-счетчиками, а вычисляются SUM
по журналу при каждом чтении. Все суммы — целые копейки (NFR-33);
арифметика только целочисленная (float/Decimal/round запрещены —
гард test_qa_s16_money).

Формулы балансов (сверка со сценариями спеки wallet):
  ученик:
    available = Σtopup(user) − Σhold(user) + Σrefund(user)
      — холд единожду покидает available при постановке, refund
      возвращает его; release.gross НЕ вычитается из available повторно
      (деньги ушли из available еще при холде) — иначе сумма «терялась»
      бы в total = available + frozen;
    frozen    = Σhold(user) − Σrelease.gross(student_id=я) − Σrefund(user)
      — release/refund исполняют холд: замороженное уходит инструктору
      (gross) или возвращается ученику;
    total     = available + frozen.
  инструктор:
    earned_net = Σrelease.net(instructor_id=я)
    balance    = earned_net − Σpayout(user=я)
      — заявка выплаты баланс не замораживает (СА-решение MVP):
      списание = факт выплаты (confirm оператора).
  платформа:
    company_balance = Σrelease.fee (комиссия 0 вносит 0 фактом — FR-114).

Разбиение релиза (FR-106): net = gross × (100 − c) // 100 (floor —
целочисленное деление), fee = gross − net (хвост платформе); комиссия c
берется НА МОМЕНТ РЕЛИЗА (текущее instructors.commission_percent).

Валидация/точка создания строк инструктора: ensure_instructor_row —
INSERT OR IGNORE (PK user_id), вызывается при одобрении заявки
(backend/auth/instructor_admin.py, approve-ветка) и в эндпоинтах
экономики (страховка от рассинхрона).
"""
import datetime
import sqlite3

# Денежные типы журнала (CHECK в схеме db.py — источник правды).
TX_TYPES = ("topup", "hold", "release", "refund", "payout")

# Граница верхнего предела пополнения MVP: 500 000 ₽ в копейках
# (защита от опечаток, задача 16.2.1).
TOPUP_MAX_KOP = 50_000_000


def release_gross_split(gross_kop: int, commission_percent: int) -> tuple[int, int]:
    """Разбиение gross на (fee, net) по комиссии c (FR-106, NFR-33):
    net = gross × (100 − c) // 100 — floor целочисленно; fee = gross − net
    (хвост платформе; c=0 → fee=0 — «учитывает факт 0», FR-114; c=100 →
    net=0, fee=gross). Возвращает целые копейки."""
    net_kop = gross_kop * (100 - commission_percent) // 100
    fee_kop = gross_kop - net_kop
    return fee_kop, net_kop


def hours_between(start_time: str, end_time: str) -> int:
    """Длительность слота целыми часами (design «Денежные правила»):
    (end − start) целыми минутами // 60 — нецелые интервалы floor,
    хвост не тарифицируется; «HH:MM»-строки графика availability."""
    sh, sm = (int(part) for part in start_time.split(":"))
    eh, em = (int(part) for part in end_time.split(":"))
    minutes = (eh * 60 + em) - (sh * 60 + sm)
    return minutes // 60


def hold_amount_kop(price_per_hour_rub: int, start_time: str, end_time: str) -> int:
    """Сумма холда: цена часа (целые рубли) × 100 (точная целочисленная
    конвертация в копейки) × часы слота (floor до целого часа)."""
    return price_per_hour_rub * 100 * hours_between(start_time, end_time)


def insert_transaction(
    conn: sqlite3.Connection,
    *,
    tx_type: str,
    user_id: int,
    amount_kop: int,
    booking_id: int | None = None,
    payout_id: int | None = None,
    topup_id: int | None = None,
    student_id: int | None = None,
    instructor_id: int | None = None,
    amount_gross_kop: int | None = None,
    fee_kop: int | None = None,
    amount_net_kop: int | None = None,
    note: str | None = None,
) -> int:
    """INSERT в журнал (append-only — других записей в transactions нет;
    NFR-34). Вызывается ВНУТРИ write-транзакции вызывающего кода
    (BEGIN IMMEDIATE — NFR-35); частичные UNIQUE держат ровно одно
    движение на бронь/заявку. Возвращает id строки."""
    if tx_type not in TX_TYPES:
        raise ValueError(f"неизвестный тип транзакции: {tx_type}")
    cur = conn.execute(
        "INSERT INTO transactions (type, user_id, amount_kop, booking_id,"
        " payout_id, topup_id, student_id, instructor_id, amount_gross_kop,"
        " fee_kop, amount_net_kop, note)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            tx_type, user_id, amount_kop, booking_id, payout_id, topup_id,
            student_id, instructor_id, amount_gross_kop, fee_kop,
            amount_net_kop, note,
        ),
    )
    lastrowid = cur.lastrowid
    assert lastrowid is not None, "INSERT в transactions не вернул rowid"
    return int(lastrowid)


def ensure_instructor_row(conn: sqlite3.Connection, instructor_id: int) -> sqlite3.Row:
    """Строка instructors инструктора (гарантия существования): INSERT OR
    IGNORE (PK user_id) + SELECT — идемпотентно, существующая строка
    (кастомная комиссия/цена) не перезаписывается. Комиссия по умолчанию
    10 — DEFAULT схемы (FR-109)."""
    conn.execute(
        "INSERT OR IGNORE INTO instructors (user_id) VALUES (?)",
        (instructor_id,),
    )
    return conn.execute(
        "SELECT user_id, commission_percent, price_per_hour_rub"
        " FROM instructors WHERE user_id = ?",
        (instructor_id,),
    ).fetchone()


def student_balances(conn: sqlite3.Connection, student_id: int) -> dict:
    """Кошелек ученика (FR-98): SUM по журналу — формулы в докстринге
    модуля. Возвращает {'available_kop', 'frozen_kop', 'total_kop'}."""
    row = conn.execute(
        "SELECT"
        " (SELECT COALESCE(SUM(amount_kop), 0) FROM transactions"
        "   WHERE user_id = ? AND type = 'topup') AS topups,"
        " (SELECT COALESCE(SUM(amount_kop), 0) FROM transactions"
        "   WHERE user_id = ? AND type = 'hold') AS holds,"
        " (SELECT COALESCE(SUM(amount_kop), 0) FROM transactions"
        "   WHERE user_id = ? AND type = 'refund') AS refunds,"
        " (SELECT COALESCE(SUM(amount_gross_kop), 0) FROM transactions"
        "   WHERE student_id = ? AND type = 'release') AS released_gross",
        (student_id, student_id, student_id, student_id),
    ).fetchone()
    available = row["topups"] - row["holds"] + row["refunds"]
    frozen = row["holds"] - row["released_gross"] - row["refunds"]
    return {
        "available_kop": available,
        "frozen_kop": frozen,
        "total_kop": available + frozen,
    }


def instructor_balances(conn: sqlite3.Connection, instructor_id: int) -> dict:
    """Балансы инструктора (FR-110): earned_net (Σrelease.net) и balance
    (заработанное минус фактические выплаты — Σpayout по user_id)."""
    row = conn.execute(
        "SELECT"
        " (SELECT COALESCE(SUM(amount_net_kop), 0) FROM transactions"
        "   WHERE instructor_id = ? AND type = 'release') AS earned_net,"
        " (SELECT COALESCE(SUM(amount_kop), 0) FROM transactions"
        "   WHERE user_id = ? AND type = 'payout') AS paid_out",
        (instructor_id, instructor_id),
    ).fetchone()
    earned_net = row["earned_net"]
    return {
        "earned_net_kop": earned_net,
        "paid_out_kop": row["paid_out"],
        "balance_kop": earned_net - row["paid_out"],
    }


def company_balance(conn: sqlite3.Connection) -> int:
    """Баланс компании (FR-114): SUM fee по release журнала (без отдельной
    таблицы); релизы с комиссией 0 вносят 0 фактом."""
    row = conn.execute(
        "SELECT COALESCE(SUM(fee_kop), 0) AS total FROM transactions"
        " WHERE type = 'release'"
    ).fetchone()
    return row["total"]


def month_earnings(
    conn: sqlite3.Connection, instructor_id: int, year: int, month: int
) -> dict:
    """Статистика месяца инструктора (FR-110): разбивка release по
    ученикам + итог месяца — агрегаты net (справочно gross/fee).
    Границы месяца — по created_at (UTC) журнала."""
    prefix = f"{year:04d}-{month:02d}-%"
    rows = conn.execute(
        "SELECT t.student_id, t.amount_net_kop, t.amount_gross_kop, t.fee_kop"
        " FROM transactions t"
        " WHERE t.instructor_id = ? AND t.type = 'release'"
        " AND t.created_at LIKE ?",
        (instructor_id, prefix),
    ).fetchall()
    by_student: dict[int, dict] = {}
    total_net = total_gross = total_fee = 0
    for row in rows:
        entry = by_student.setdefault(
            row["student_id"],
            {"student_id": row["student_id"], "net_kop": 0, "gross_kop": 0},
        )
        entry["net_kop"] += row["amount_net_kop"]
        entry["gross_kop"] += row["amount_gross_kop"]
        total_net += row["amount_net_kop"]
        total_gross += row["amount_gross_kop"]
        total_fee += row["fee_kop"]
    return {
        "by_student": sorted(
            by_student.values(), key=lambda e: (-e["net_kop"], e["student_id"])
        ),
        "total_net_kop": total_net,
        "total_gross_kop": total_gross,
        "total_fee_kop": total_fee,
    }


def yearly_commissions(conn: sqlite3.Connection, year: int) -> list[dict]:
    """Комиссии инструкторов за год (FR-115): инструктор × SUM fee его
    release-транзакций года (агрегат журнала); инструкторы без релизов
    года — строка с 0 (факт 0). Год — по created_at (UTC)."""
    rows = conn.execute(
        "SELECT i.user_id AS instructor_id,"
        " COALESCE(SUM(t.fee_kop), 0) AS fee_kop,"
        " COUNT(t.id) AS releases"
        " FROM instructors i"
        " LEFT JOIN transactions t ON t.instructor_id = i.user_id"
        "  AND t.type = 'release'"
        "  AND CAST(strftime('%Y', t.created_at) AS INTEGER) = ?"
        " GROUP BY i.user_id ORDER BY fee_kop DESC, i.user_id",
        (year,),
    ).fetchall()
    return [
        {
            "instructor_id": row["instructor_id"],
            "fee_kop": row["fee_kop"],
            "releases": row["releases"],
        }
        for row in rows
    ]


def utc_now_string() -> str:
    """Текущее UTC в формате datetime('now') ('YYYY-MM-DD HH:MM:SS') —
    единая точка сравнения с created_at/completed_at журнала (сдвиги
    формата ломали бы лексические границы свипа)."""
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
