"""Спринт 16 — BACKEND-тесты холд-интеграции в бронирование (change
add-wallet-economy; задача 16.3.1; design.md «Конечные автоматы» —
полный FSM: бронь→холд, reject/cancel→refund СТРОГО ДО СТАРТА (МАЖ-1),
complete→авто-релиз 24ч (ленивый свип), timeout-defrost 72ч, спор
(ТОЛЬКО живой холд — МАЖ-2) → решение оператора).

Сценарии:
- снапшот цены при брони + HOLD (available−/frozen+, FR-101/102);
- 402 при нехватке — БЕЗ записи брони и холда (FR-103);
- reject/cancel → refund в той же транзакции (FR-104); после старта —
  409 «Занятие началось», статус и холд не изменены (МАЖ-1);
- complete («проведено», экземпляр начался) → до 24ч релиза НЕТ, после
  24ч — release с gross/fee/net; комиссия — НА МОМЕНТ РЕЛИЗА (10% и
  0% — «учитывает факт 0», FR-106/114);
- спор в окне 24ч → свип НЕ релизит → resolve release/refund оператором
  (FR-107); повторное решение → 409; спор по исполненному холду — 422;
- timeout-defrost: new/confirmed со стартом ≥72ч назад без «проведено»
  → REFUND при свипе, повторный свип без дубля (частичный UNIQUE);
- легаси-путь: цена NULL → холда нет, поведение 1:1 (s5 не ломается).

Время — прямой контролем БД (completed_at/lesson_date подстановка;
time.sleep запрещен, спека qa-pipeline). Все суммы — целые копейки
(NFR-33); трассировка TC-S16-NNN в docstring каждого теста (rule 6).
"""
import datetime
import sqlite3

from conftest import admin_headers, db_path, register

INSTR_PASSWORD = "Instr1616"


# --- helpers ------------------------------------------------------------------


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _headers(token):
    return {"X-Session-Token": token}


def _login(client, email, password):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


def _setup_world(client, *, email_suffix, price_per_hour=None):
    """Полная аранжировка: инструктор (+опц. цена часа) + авто + слоты
    one_off (завтра 10:00–12:00, послезавтра 12:00–13:00 —
    детерминированно будущие, BUG-063) + ученик + accepted пара.
    Возвращает {instr_token, instr_id, student_token, student_id,
    slot1, slot2}."""
    body = {
        "surname": "Холдовый",
        "name": "Инструктор",
        "patronymic": "Тестович",
        "phone": "+7 (911) 100-16-30",
        "email": f"s16h-instr-{email_suffix}@example.com",
        "address": "г. Тест, ул. Холдов, 1",
        "work_format": "sber",
        "license_number": "1616161616",
        "license_category": "B",
        "experience_years": 3,
        "password": INSTR_PASSWORD,
        "password_confirm": INSTR_PASSWORD,
        "consent": True,
    }
    resp = client.post("/api/instructors/apply", json=body)
    assert resp.status_code == 200, resp.text
    conn = _conn()
    app_id = conn.execute(
        "SELECT id FROM instructor_applications WHERE email = ?",
        (body["email"],),
    ).fetchone()[0]
    conn.close()
    approved = client.post(
        f"/api/admin/instructor-applications/{app_id}/approve",
        headers=admin_headers(client),
    )
    assert approved.status_code == 200, approved.text
    instr_token = _login(client, body["email"], INSTR_PASSWORD)
    instr_id = approved.json()["user_id"]

    if price_per_hour is not None:
        resp = client.put(
            "/api/instructor/price",
            json={"price_per_hour_rub": price_per_hour},
            headers=_headers(instr_token),
        )
        assert resp.status_code == 200, resp.text

    car = client.post(
        "/api/instructor/cars",
        json={"brand": "Škoda", "model": "Rapid", "year": 2020,
              "plate": "А123АА777", "transmission": "automatic"},
        headers=_headers(instr_token),
    )
    assert car.status_code == 200, car.text
    car_id = car.json()["car_id"]

    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    after = datetime.date.today() + datetime.timedelta(days=2)
    saved = client.put(
        "/api/instructor/availability",
        json={"intervals": [
            {"slot_type": "one_off", "date": tomorrow.isoformat(),
             "weekday": tomorrow.weekday(),
             "start_time": "10:00", "end_time": "12:00"},
            {"slot_type": "one_off", "date": after.isoformat(),
             "weekday": after.weekday(),
             "start_time": "12:00", "end_time": "13:00"},
        ]},
        headers=_headers(instr_token),
    )
    assert saved.status_code == 200, saved.text

    email = f"s16h-student-{email_suffix}@example.com"
    reg = register(client, email=email)
    assert reg.status_code == 200, reg.text
    conn = _conn()
    student_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", (email,)
    ).fetchone()[0]
    conn.close()
    student_token = _login(client, email, "Qwerty123")
    req = client.post(
        "/api/student/requests",
        json={"instructor_id": instr_id},
        headers=_headers(student_token),
    )
    assert req.status_code == 200, req.text
    accepted = client.post(
        f"/api/instructor/requests/{req.json()['request_id']}/accept",
        json={"car_id": car_id},
        headers=_headers(instr_token),
    )
    assert accepted.status_code == 200, accepted.text

    # Слоты — напрямую из БД по дате экземпляра (легаси-/slots-ответ
    # сортирует по weekday — порядок инвертируется на границе недели):
    # slot1 — завтра 10:00–12:00 (2 ч), slot2 — послезавтра 12:00–13:00
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT id FROM availability"
            " WHERE instructor_id = ? AND slot_type = 'one_off'"
            " ORDER BY slot_date, start_time",
            (instr_id,),
        ).fetchall()
        slot1, slot2 = rows[0]["id"], rows[1]["id"]
    finally:
        conn.close()
    return {
        "instr_token": instr_token,
        "instr_id": instr_id,
        "student_token": student_token,
        "student_id": student_id,
        "slot1": slot1,   # завтра 10:00–12:00 (2 ч)
        "slot2": slot2,   # послезавтра 12:00–13:00 (1 ч)
    }


def _topup(client, token, amount_kop):
    resp = client.post(
        "/api/wallet/topup", json={"amount_kop": amount_kop},
        headers=_headers(token),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _book(client, token, availability_id):
    return client.post(
        "/api/student/bookings",
        json={"availability_id": availability_id},
        headers=_headers(token),
    )


def _booking_row(booking_id):
    conn = _conn()
    try:
        return conn.execute(
            "SELECT * FROM booking WHERE id = ?", (booking_id,)
        ).fetchone()
    finally:
        conn.close()


def _txs(booking_id, *types):
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT type, amount_kop, amount_gross_kop, fee_kop,"
            " amount_net_kop FROM transactions WHERE booking_id = ?"
            " ORDER BY id",
            (booking_id,),
        ).fetchall()
        return [r for r in rows if not types or r["type"] in types]
    finally:
        conn.close()


def _wallet(client, token):
    resp = client.get("/api/wallet", headers=_headers(token))
    assert resp.status_code == 200, resp.text
    return resp.json()


def _backdate_start(booking_id, days_ago):
    """Подстановка часов (детерминизм без sleep): экземпляр начался
    N суток назад (NFR-31 граница — по началу слота)."""
    conn = _conn()
    try:
        past = (datetime.date.today() - datetime.timedelta(days=days_ago)).isoformat()
        conn.execute(
            "UPDATE booking SET lesson_date = ? WHERE id = ?",
            (past, booking_id),
        )
        conn.commit()
    finally:
        conn.close()


def _backdate_completed(booking_id, hours_ago):
    conn = _conn()
    try:
        conn.execute(
            "UPDATE booking SET completed_at ="
            " datetime('now', ?) WHERE id = ?",
            (f"-{hours_ago} hours", booking_id),
        )
        conn.commit()
    finally:
        conn.close()


def _confirm_and_complete(client, world, booking_id, *, started_days_ago=1):
    """confirm + (подстановка прошедшего экземпляра) + complete
    («проведено» — свежий completed_at)."""
    resp = client.post(
        f"/api/instructor/bookings/{booking_id}/confirm",
        headers=_headers(world["instr_token"]),
    )
    assert resp.status_code == 200, resp.text
    _backdate_start(booking_id, started_days_ago)
    resp = client.post(
        f"/api/instructor/bookings/{booking_id}/complete",
        headers=_headers(world["instr_token"]),
    )
    assert resp.status_code == 200, resp.text


# --- HOLD при брони (FR-101/102/103) ------------------------------------------


def test_s16_hold_snapshot_and_frozen_on_create(client):
    """TC-S16-030 — бронь с ценой (FR-101/102): снапшот цены в брони +
    hold_amount_kop = цена×100×часы слота (1500₽ × 2ч = 300 000 коп);
    hold-транзакция в журнале; available−/frozen+ (SUM-балансы);
    отображение в my_bookings (легаси-поля без удаления)."""
    world = _setup_world(client, email_suffix="hold", price_per_hour=1500)
    _topup(client, world["student_token"], 500_000)
    resp = _book(client, world["student_token"], world["slot1"])
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["price_per_hour_rub"] == 1500
    assert body["hold_amount_kop"] == 300_000  # 1500×100×2 (NFR-33)
    booking_id = body["booking_id"]

    row = _booking_row(booking_id)
    assert row["price_per_hour_rub"] == 1500   # снапшот на момент брони
    assert row["hold_amount_kop"] == 300_000
    assert row["status"] == "new"
    hold = _txs(booking_id, "hold")
    assert len(hold) == 1 and hold[0]["amount_kop"] == 300_000

    wallet = _wallet(client, world["student_token"])
    assert wallet["available_kop"] == 200_000
    assert wallet["frozen_kop"] == 300_000
    assert wallet["total_kop"] == 500_000

    mine = client.get(
        "/api/student/bookings", headers=_headers(world["student_token"])
    ).json()["bookings"]
    entry = next(b for b in mine if b["id"] == booking_id)
    assert entry["hold_amount_kop"] == 300_000
    assert entry["price_per_hour_rub"] == 1500
    # У инструктора тоже (отображение):
    theirs = client.get(
        "/api/instructor/bookings", headers=_headers(world["instr_token"])
    ).json()["bookings"]
    assert theirs[0]["hold_amount_kop"] == 300_000


def test_s16_hold_insufficient_funds_402_no_booking(client):
    """TC-S16-031 — 402 при нехватке (FR-103): {ok:false, error, need_kop,
    available_kop}; бронь и холд НЕ создаются (откат транзакции);
    слот остается свободным — повтор с достаточным балансом проходит."""
    world = _setup_world(client, email_suffix="402", price_per_hour=1500)
    _topup(client, world["student_token"], 100_000)  # < 300 000
    resp = _book(client, world["student_token"], world["slot1"])
    assert resp.status_code == 402, resp.text
    body = resp.json()
    assert body["ok"] is False
    assert body["need_kop"] == 200_000
    assert body["available_kop"] == 100_000
    conn = _conn()
    try:
        assert conn.execute(
            "SELECT COUNT(*) c FROM booking WHERE student_id = ?",
            (world["student_id"],),
        ).fetchone()["c"] == 0
        # Журнал содержит только topup; hold НЕ создан
        assert conn.execute(
            "SELECT COUNT(*) c FROM transactions WHERE type = 'hold'"
        ).fetchone()["c"] == 0
        assert conn.execute(
            "SELECT COUNT(*) c FROM transactions WHERE type = 'topup'"
        ).fetchone()["c"] == 1
    finally:
        conn.close()
    # Дополнил кошелек → бронь проходит (слот не был занят 402-попыткой)
    _topup(client, world["student_token"], 200_000)
    resp = _book(client, world["student_token"], world["slot1"])
    assert resp.status_code == 200, resp.text


# --- reject/cancel → refund (FR-104) и МАЖ-1 ----------------------------------


def test_s16_hold_reject_refund_before_start(client):
    """TC-S16-032 — reject ДО старта (FR-104): refund в той же
    транзакции (frozen−, available+); повторный reject → 409; дубля
    refund нет (частичный UNIQUE)."""
    world = _setup_world(client, email_suffix="rej", price_per_hour=1500)
    _topup(client, world["student_token"], 400_000)
    booking_id = _book(client, world["student_token"], world["slot1"]).json()[
        "booking_id"
    ]
    resp = client.post(
        f"/api/instructor/bookings/{booking_id}/reject",
        json={"comment": "Не смогу в это окно"},
        headers=_headers(world["instr_token"]),
    )
    assert resp.status_code == 200, resp.text
    row = _booking_row(booking_id)
    assert row["status"] == "rejected"
    refund = _txs(booking_id, "refund")
    assert len(refund) == 1 and refund[0]["amount_kop"] == 300_000
    wallet = _wallet(client, world["student_token"])
    assert wallet["available_kop"] == 400_000
    assert wallet["frozen_kop"] == 0
    # Повторный reject — 409, refund второй НЕ создается
    resp = client.post(
        f"/api/instructor/bookings/{booking_id}/reject",
        json={"comment": "опять"},
        headers=_headers(world["instr_token"]),
    )
    assert resp.status_code == 409
    assert len(_txs(booking_id, "refund")) == 1


def test_s16_hold_cancel_refund_and_legacy_guards(client):
    """TC-S16-033 — cancel ДО старта (FR-104, BUG-049-механика):
    refund живого холда; cancel по 'new' → 409 (легаси-гвард сохранен);
    повторный cancel → 409."""
    world = _setup_world(client, email_suffix="cxl", price_per_hour=1500)
    _topup(client, world["student_token"], 400_000)
    booking_id = _book(client, world["student_token"], world["slot1"]).json()[
        "booking_id"
    ]
    # cancel по 'new' — 409 (решения по 'new' — confirm/reject)
    assert client.post(
        f"/api/instructor/bookings/{booking_id}/cancel",
        headers=_headers(world["instr_token"]),
    ).status_code == 409
    assert client.post(
        f"/api/instructor/bookings/{booking_id}/confirm",
        headers=_headers(world["instr_token"]),
    ).status_code == 200
    resp = client.post(
        f"/api/instructor/bookings/{booking_id}/cancel",
        headers=_headers(world["instr_token"]),
    )
    assert resp.status_code == 200, resp.text
    assert _booking_row(booking_id)["status"] == "rejected"
    refund = _txs(booking_id, "refund")
    assert len(refund) == 1 and refund[0]["amount_kop"] == 300_000
    wallet = _wallet(client, world["student_token"])
    assert wallet["available_kop"] == 400_000 and wallet["frozen_kop"] == 0
    assert client.post(
        f"/api/instructor/bookings/{booking_id}/cancel",
        headers=_headers(world["instr_token"]),
    ).status_code == 409
    assert len(_txs(booking_id, "refund")) == 1


def test_s16_maj1_cancel_reject_after_start_409(client):
    """TC-S16-034 — МАЖ-1: cancel/reject ПОСЛЕ старта занятия → 409
    «Занятие началось» БЕЗ смены статуса и БЕЗ refund (подстановка
    прошедшего lesson_date; деньги не теряются ни в одной ветке)."""
    world = _setup_world(client, email_suffix="maj1", price_per_hour=1500)
    _topup(client, world["student_token"], 500_000)
    b_cancel = _book(client, world["student_token"], world["slot1"]).json()[
        "booking_id"
    ]
    b_reject = _book(client, world["student_token"], world["slot2"]).json()[
        "booking_id"
    ]
    assert client.post(
        f"/api/instructor/bookings/{b_cancel}/confirm",
        headers=_headers(world["instr_token"]),
    ).status_code == 200
    # Часы: экземпляры «начались» (вчера)
    _backdate_start(b_cancel, 1)
    _backdate_start(b_reject, 1)
    resp = client.post(
        f"/api/instructor/bookings/{b_cancel}/cancel",
        headers=_headers(world["instr_token"]),
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "Занятие началось"
    resp = client.post(
        f"/api/instructor/bookings/{b_reject}/reject",
        json={"comment": "поздно"},
        headers=_headers(world["instr_token"]),
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "Занятие началось"
    # Статусы и холды не изменены, refund НЕТ (1 день < 72ч — defrost
    # тоже не затрагивает)
    assert _booking_row(b_cancel)["status"] == "confirmed"
    assert _booking_row(b_reject)["status"] == "new"
    assert len(_txs(b_cancel, "refund")) == 0
    assert len(_txs(b_reject, "refund")) == 0
    wallet = _wallet(client, world["student_token"])
    assert wallet["frozen_kop"] == 450_000  # 300 000 + 150 000
    assert wallet["available_kop"] == 50_000  # 500 000 − 450 000


# --- complete → авто-релиз 24ч (FR-105/106) -----------------------------------


def test_s16_complete_and_lazy_release_after_24h(client):
    """TC-S16-035 — complete («проведено», FR-105): экземпляр начался —
    иначе 409; до 24ч свип релиза НЕ создает; после 24ч (подстановка
    completed_at) — release с gross/fee/net (комиссия 10: fee=30 000,
    net=270 000); повторный свип без дубля; баланс компании = fee."""
    world = _setup_world(client, email_suffix="rel", price_per_hour=1500)
    _topup(client, world["student_token"], 500_000)
    booking_id = _book(client, world["student_token"], world["slot1"]).json()[
        "booking_id"
    ]
    # complete ДО старта → 409
    assert client.post(
        f"/api/instructor/bookings/{booking_id}/confirm",
        headers=_headers(world["instr_token"]),
    ).status_code == 200
    resp = client.post(
        f"/api/instructor/bookings/{booking_id}/complete",
        headers=_headers(world["instr_token"]),
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "Занятие еще не началось"
    # Экземпляр начался → complete проходит («проведено»)
    _backdate_start(booking_id, 1)
    resp = client.post(
        f"/api/instructor/bookings/{booking_id}/complete",
        headers=_headers(world["instr_token"]),
    )
    assert resp.status_code == 200, resp.text
    row = _booking_row(booking_id)
    assert row["status"] == "completed" and row["completed_at"] is not None

    # До 24ч: свип (точка чтения кошелька) релиза НЕ создает
    wallet = _wallet(client, world["student_token"])
    assert wallet["frozen_kop"] == 300_000
    assert _txs(booking_id, "release") == []

    # После 24ч: авто-релиз — комиссия НА МОМЕНТ РЕЛИЗА (10, DEFAULT)
    _backdate_completed(booking_id, 25)
    wallet = _wallet(client, world["student_token"])
    assert wallet["frozen_kop"] == 0
    assert wallet["available_kop"] == 200_000  # 500 000 − 300 000 gross
    release = _txs(booking_id, "release")
    assert len(release) == 1
    assert release[0]["amount_gross_kop"] == 300_000
    assert release[0]["fee_kop"] == 30_000       # floor(300000×10/100)
    assert release[0]["amount_net_kop"] == 270_000
    # Инструктор: earned/balance (net), админ: баланс компании (fee)
    econ = client.get(
        "/api/instructor/economy", headers=_headers(world["instr_token"])
    ).json()
    assert econ["earned_net_kop"] == 270_000
    assert econ["balance_kop"] == 270_000
    admin = client.get(
        "/api/admin/transactions", headers=admin_headers(client)
    ).json()
    assert admin["company_balance_kop"] == 30_000
    # Повторный свип — безобиден (ровно один release, NFR-35)
    _wallet(client, world["student_token"])
    assert len(_txs(booking_id, "release")) == 1


def test_s16_release_commission_zero_fact(client):
    """TC-S16-036 — комиссия 0 на момент релиза («учитывает факт 0»,
    FR-114): fee=0, net=gross; баланс компании не меняется (0 фактом)."""
    world = _setup_world(client, email_suffix="c0", price_per_hour=1000)
    admin = admin_headers(client)
    resp = client.put(
        f"/api/admin/instructors/{world['instr_id']}/commission",
        json={"commission_percent": 0}, headers=admin,
    )
    assert resp.status_code == 200, resp.text
    _topup(client, world["student_token"], 300_000)
    booking_id = _book(client, world["student_token"], world["slot1"]).json()[
        "booking_id"
    ]
    _confirm_and_complete(client, world, booking_id)
    _backdate_completed(booking_id, 25)
    wallet = _wallet(client, world["student_token"])
    assert wallet["frozen_kop"] == 0
    release = _txs(booking_id, "release")
    assert len(release) == 1
    assert release[0]["amount_gross_kop"] == 200_000  # 1000₽ × 100 × 2ч
    assert release[0]["fee_kop"] == 0          # факт 0
    assert release[0]["amount_net_kop"] == 200_000
    admin_view = client.get(
        "/api/admin/transactions", headers=admin
    ).json()
    assert admin_view["company_balance_kop"] == 0


# --- Спор (МАЖ-2, FR-107) и решение оператора ---------------------------------


def test_s16_dispute_blocks_sweep_then_operator_resolves(client):
    """TC-S16-037 — спор в окне 24ч → свип НЕ релизит (даже после
    дедлайна) → resolve refund/release оператором закрывает спор и холд
    РОВНО одной транзакцией; повторное решение → 409; новый спор по
    исполненному холду → 422 (МАЖ-2)."""
    world = _setup_world(client, email_suffix="disp", price_per_hour=1500)
    admin = admin_headers(client)
    _topup(client, world["student_token"], 500_000)
    b_refund = _book(client, world["student_token"], world["slot1"]).json()[
        "booking_id"
    ]
    b_release = _book(client, world["student_token"], world["slot2"]).json()[
        "booking_id"
    ]
    _confirm_and_complete(client, world, b_refund)
    _confirm_and_complete(client, world, b_release)

    # Спор по обеим брони (окно открыто — completed_at свежий)
    for bid in (b_refund, b_release):
        resp = client.post(
            f"/api/student/bookings/{bid}/dispute",
            json={"comment": "Занятие не состоялось в полном объеме"},
            headers=_headers(world["student_token"]),
        )
        assert resp.status_code == 200, resp.text
    # Повторный спор по той же брони → 409
    assert client.post(
        f"/api/student/bookings/{b_refund}/dispute",
        json={"comment": "второй"},
        headers=_headers(world["student_token"]),
    ).status_code == 409

    # Дедлайн релиза прошел — но спор открыт: свип НЕ релизит
    _backdate_completed(b_refund, 25)
    _backdate_completed(b_release, 25)
    wallet = _wallet(client, world["student_token"])
    assert wallet["frozen_kop"] == 450_000  # оба холда живы
    assert _txs(b_refund, "release", "refund") == []
    assert _txs(b_release, "release", "refund") == []

    # Оператор видит открытые споры (бронь/ученик/инструктор/холд)
    open_list = client.get("/api/admin/disputes", headers=admin).json()
    assert {d["booking_id"] for d in open_list["disputes"]} == {
        b_refund, b_release
    }

    # resolve refund — полный возврат, спор закрыт
    disp_refund = next(
        d for d in open_list["disputes"] if d["booking_id"] == b_refund
    )
    resp = client.post(
        f"/api/admin/disputes/{disp_refund['id']}/resolve",
        json={"resolution": "refund", "comment": "Подтверждено: занятия не было"},
        headers=admin,
    )
    assert resp.status_code == 200, resp.text
    refund = _txs(b_refund, "refund")
    assert len(refund) == 1 and refund[0]["amount_kop"] == 300_000
    # Повторное решение → 409; релиз после refund НЕ создается
    # (исход холда — ровно один, терминальность)
    resp = client.post(
        f"/api/admin/disputes/{disp_refund['id']}/resolve",
        json={"resolution": "release", "comment": "поздно"},
        headers=admin,
    )
    assert resp.status_code == 409
    _wallet(client, world["student_token"])
    assert _txs(b_refund, "release") == []

    # resolve release — fee/net по ТЕКУЩЕЙ комиссии (10)
    disp_release = next(
        d for d in open_list["disputes"] if d["booking_id"] == b_release
    )
    resp = client.post(
        f"/api/admin/disputes/{disp_release['id']}/resolve",
        json={"resolution": "release", "comment": "Занятие состоялось"},
        headers=admin,
    )
    assert resp.status_code == 200, resp.text
    release = _txs(b_release, "release")
    assert len(release) == 1
    assert release[0]["amount_gross_kop"] == 150_000  # 1ч × 1500₽ × 100
    assert release[0]["fee_kop"] == 15_000
    assert release[0]["amount_net_kop"] == 135_000

    # Итог балансов: refund вернул 300 000, release исполнил 150 000
    wallet = _wallet(client, world["student_token"])
    assert wallet["available_kop"] == 350_000  # 500 000 − 150 000 gross
    assert wallet["frozen_kop"] == 0
    # Новый спор по исполненному холду → 422 (МАЖ-2): возвращаем свежую
    # отметку «проведено» (подстановка часов), иначе окно 24ч закрыло бы
    # спор раньше hold-гварда (409)
    conn = _conn()
    try:
        conn.execute(
            "UPDATE booking SET completed_at = datetime('now')"
            " WHERE id = ?",
            (b_release,),
        )
        conn.commit()
    finally:
        conn.close()
    resp = client.post(
        f"/api/student/bookings/{b_release}/dispute",
        json={"comment": "еще раз"},
        headers=_headers(world["student_token"]),
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "Спор: только по тарифицированным броням"
    assert client.get(
        "/api/admin/disputes", headers=admin
    ).json()["disputes"] == []


def test_s16_dispute_guards_window_hold_ownership(client):
    """TC-S16-038 — гварды спора (МАЖ-2): без комментария → 422; чужая
    бронь → 404; не-проведенная бронь → 409; окно 24ч закрыто → 409;
    бронь с ценой NULL (холда нет) → 422 «Спор: только по
    тарифицированным броням»."""
    world = _setup_world(client, email_suffix="gd", price_per_hour=1500)
    # Второй инструктор БЕЗ цены (легаси) + его ученик для 404/price-NULL
    other = _setup_world(client, email_suffix="gd2", price_per_hour=None)
    _topup(client, world["student_token"], 500_000)
    _topup(client, other["student_token"], 500_000)

    b_timed = _book(client, world["student_token"], world["slot1"]).json()[
        "booking_id"
    ]
    b_free = _book(client, other["student_token"], other["slot1"]).json()[
        "booking_id"
    ]
    # (а) не проведена → 409
    resp = client.post(
        f"/api/student/bookings/{b_timed}/dispute",
        json={"comment": "еще не было"},
        headers=_headers(world["student_token"]),
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "Спор: только по проведенным занятиям"
    # (б) чужая бронь → 404
    resp = client.post(
        f"/api/student/bookings/{b_free}/dispute",
        json={"comment": "не моя"},
        headers=_headers(world["student_token"]),
    )
    assert resp.status_code == 404
    # (в) без комментария → 422 (на проведенной)
    _confirm_and_complete(client, world, b_timed)
    resp = client.post(
        f"/api/student/bookings/{b_timed}/dispute",
        json={"comment": ""},
        headers=_headers(world["student_token"]),
    )
    assert resp.status_code == 422
    # (г) окно 24ч закрыто → 409 (холд жив, но время вышло)
    _backdate_completed(b_timed, 25)
    resp = client.post(
        f"/api/student/bookings/{b_timed}/dispute",
        json={"comment": "дня два назад было"},
        headers=_headers(world["student_token"]),
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "Окно спора закрыто (24ч с момента занятия)"
    # (д) price NULL (бесплатное занятие, hold_amount=0): спор НЕ
    # открывается — 422, МАЖ-2
    _confirm_and_complete(client, other, b_free)
    resp = client.post(
        f"/api/student/bookings/{b_free}/dispute",
        json={"comment": "бесплатное, но обидно"},
        headers=_headers(other["student_token"]),
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "Спор: только по тарифицированным броням"
    conn = _conn()
    try:
        assert conn.execute(
            "SELECT COUNT(*) c FROM booking_disputes"
        ).fetchone()["c"] == 0
    finally:
        conn.close()


# --- timeout-defrost 72ч (MIN-1) и гонки исходов -------------------------------


def test_s16_timeout_defrost_72h_refund(client):
    """TC-S16-039 — timeout-defrost (MIN-1): confirmed-бронь со стартом
    ≥72ч назад БЕЗ «проведено» → REFUND при свипе (холд не висит вечно);
    статус брони не меняется; повторный свип без дубля; свежая бронь
    defrost не затрагивается."""
    world = _setup_world(client, email_suffix="def", price_per_hour=1500)
    _topup(client, world["student_token"], 450_000)
    b_old = _book(client, world["student_token"], world["slot1"]).json()[
        "booking_id"
    ]
    b_fresh = _book(client, world["student_token"], world["slot2"]).json()[
        "booking_id"
    ]
    assert client.post(
        f"/api/instructor/bookings/{b_old}/confirm",
        headers=_headers(world["instr_token"]),
    ).status_code == 200
    # Часы: старый экземпляр начался 4 суток назад (≥72ч), свежий — в
    # будущем
    _backdate_start(b_old, 4)
    wallet = _wallet(client, world["student_token"])
    assert wallet["frozen_kop"] == 150_000   # только живой холд свежей брони
    refund = _txs(b_old, "refund")
    assert len(refund) == 1 and refund[0]["amount_kop"] == 300_000
    assert _booking_row(b_old)["status"] == "confirmed"  # статус НЕ меняется
    # Повторный свип — без дубля (частичный UNIQUE, NFR-35)
    _wallet(client, world["student_token"])
    assert len(_txs(b_old, "refund")) == 1
    # Полный размороз: available = 450 000 − 150 000 (fresh hold) = 300 000
    wallet = _wallet(client, world["student_token"])
    assert wallet["available_kop"] == 300_000 and wallet["frozen_kop"] == 150_000


def test_s16_race_outcomes_terminal_and_complete_guard(client):
    """TC-S16-040 — терминальность исходов и гварды гонок (design
    «Конечные автоматы»): complete ПОСЛЕ defrost → 409 (статус не
    меняется — иначе релиз создал бы деньги из ничего); resolve по
    исполненному холду → 409 «Холд уже исполнен»; спор по исполненному
    холду → 422."""
    world = _setup_world(client, email_suffix="race", price_per_hour=1500)
    admin = admin_headers(client)
    _topup(client, world["student_token"], 500_000)
    b_defrost = _book(client, world["student_token"], world["slot1"]).json()[
        "booking_id"
    ]
    b_dispute = _book(client, world["student_token"], world["slot2"]).json()[
        "booking_id"
    ]
    # (а) defrost исполнил холд → complete запрещен, статус confirmed
    assert client.post(
        f"/api/instructor/bookings/{b_defrost}/confirm",
        headers=_headers(world["instr_token"]),
    ).status_code == 200
    _backdate_start(b_defrost, 4)
    assert _wallet(client, world["student_token"])["frozen_kop"] == 150_000
    resp = client.post(
        f"/api/instructor/bookings/{b_defrost}/complete",
        headers=_headers(world["instr_token"]),
    )
    assert resp.status_code == 409
    assert "Холд уже исполнен" in resp.json()["error"]
    assert _booking_row(b_defrost)["status"] == "confirmed"
    assert _txs(b_defrost, "release") == []

    # (б) спор + дедлайн → resolve release; ПОСЛЕ решения повтор → 409,
    # спора снова нет (422)
    _confirm_and_complete(client, world, b_dispute)
    resp = client.post(
        f"/api/student/bookings/{b_dispute}/dispute",
        json={"comment": "Качество не устроило"},
        headers=_headers(world["student_token"]),
    )
    assert resp.status_code == 200, resp.text
    _backdate_completed(b_dispute, 30)
    # Свип: спор открыт → ни release, ни defrost (completed не в defrost)
    assert _wallet(client, world["student_token"])["frozen_kop"] == 150_000
    disp = client.get("/api/admin/disputes", headers=admin).json()[
        "disputes"
    ][0]
    resp = client.post(
        f"/api/admin/disputes/{disp['id']}/resolve",
        json={"resolution": "release", "comment": "Проведено подтверждено"},
        headers=admin,
    )
    assert resp.status_code == 200, resp.text
    # Холд исполнен; окно 24ч закрыто (completed_at −30ч) → повторный
    # спор невозможен: 409 (гвард окна; 422 исполненного холда на свежем
    # окне — TC-S16-037)
    assert client.post(
        f"/api/student/bookings/{b_dispute}/dispute",
        json={"comment": "снова"},
        headers=_headers(world["student_token"]),
    ).status_code == 409

    # (в) гонка спор-vs-свип (design «Конечные автоматы»: RELEASE/REFUND
    # терминальны): холд исполнен «параллельным победителем» (прямая
    # вставка release — имитация выигравшего исполнителя) → resolve
    # проигравшего → 409 «Холд уже исполнен», INSERT исхода роняет
    # частичный UNIQUE (NFR-35)
    import backend.wallet.ledger as ledger

    world2 = _setup_world(client, email_suffix="race2", price_per_hour=1000)
    _topup(client, world2["student_token"], 500_000)
    b3 = _book(client, world2["student_token"], world2["slot1"]).json()[
        "booking_id"
    ]
    _confirm_and_complete(client, world2, b3)
    resp = client.post(
        f"/api/student/bookings/{b3}/dispute",
        json={"comment": "Разбираем"},
        headers=_headers(world2["student_token"]),
    )
    assert resp.status_code == 200, resp.text
    conn = _conn()
    try:
        fee, net = ledger.release_gross_split(200_000, 10)
        ledger.insert_transaction(
            conn, tx_type="release", user_id=world2["student_id"],
            amount_kop=200_000, booking_id=b3,
            student_id=world2["student_id"],
            instructor_id=world2["instr_id"],
            amount_gross_kop=200_000, fee_kop=fee, amount_net_kop=net,
        )
        conn.commit()
    finally:
        conn.close()
    disp3 = next(
        d for d in client.get(
            "/api/admin/disputes", headers=admin
        ).json()["disputes"]
        if d["booking_id"] == b3
    )
    resp = client.post(
        f"/api/admin/disputes/{disp3['id']}/resolve",
        json={"resolution": "release", "comment": "второй исполнитель"},
        headers=admin,
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "Холд уже исполнен — решение невозможно"


def test_s16_legacy_price_null_path_untouched(client):
    """TC-S16-041 — легаси-путь (цена NULL): бронь без холда (hold 0,
    транзакций нет), reject/cancel работают 1:1, спора нет (МАЖ-2),
    complete проходит без денег; КОНТРОЛЬ обратной совместимости s5."""
    world = _setup_world(client, email_suffix="null", price_per_hour=None)
    resp = _book(client, world["student_token"], world["slot1"])
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["price_per_hour_rub"] is None
    assert body["hold_amount_kop"] == 0
    booking_id = body["booking_id"]
    row = _booking_row(booking_id)
    assert row["price_per_hour_rub"] is None and row["hold_amount_kop"] == 0
    assert _txs(booking_id) == []
    wallet = _wallet(client, world["student_token"])
    assert (wallet["available_kop"], wallet["frozen_kop"],
            wallet["total_kop"]) == (0, 0, 0)
    # reject → 200 без refund (холда нет — гвард no-op)
    resp = client.post(
        f"/api/instructor/bookings/{booking_id}/reject",
        json={"comment": "окно занято"},
        headers=_headers(world["instr_token"]),
    )
    assert resp.status_code == 200
    assert _txs(booking_id) == []
    # complete + спор → 422 (цену NULL спора не открывают)
    booking_id2 = _book(client, world["student_token"], world["slot2"]).json()[
        "booking_id"
    ]
    _confirm_and_complete(client, world, booking_id2)
    assert _txs(booking_id2) == []   # «проведено» без денег
    resp = client.post(
        f"/api/student/bookings/{booking_id2}/dispute",
        json={"comment": "бесплатное"},
        headers=_headers(world["student_token"]),
    )
    assert resp.status_code == 422
