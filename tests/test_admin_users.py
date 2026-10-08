"""TC-ADM-005…TC-ADM-012 — GET /api/admin/users и
GET /api/admin/users/export.csv (задачи 3.2, 3.3; sdd.md §3.3, §3.4;
MIN-3 тай-брейк, MIN-4 UTC→локаль, MAJ-2 CSV-санитизация)."""
import sqlite3
from datetime import datetime, timedelta, timezone

from conftest import admin_headers, db_path, register


def csv_rows(resp):
    """Тело CSV → список строк (BOM уже срезан utf-8-sig)."""
    text = resp.content.decode("utf-8-sig")
    return [ln for ln in text.strip().split("\n") if ln]


# --- TC-ADM-005: состав колонок и значения -----------------------------------


def test_tc_adm_005_users_list_columns_and_values(client):
    """TC-ADM-005: Список зарегистрированных пользователей — состав колонок.

    U1 (базовый набор) и U2 (Сидоров Иван Петрович, sidorov@example.com,
    +7 900 111-22-33): обе регистрации 200; GET /api/admin/users с
    токеном → 200 {"count": 2, "users": [...]}; для каждого присутствуют
    fio = «{surname} {name} {patronymic}», email, phone, created_at;
    значения совпадают с введенными (fio U1 = «Петрова-Водкина Анна
    Оттовна»).
    """
    assert register(client).status_code == 200
    assert register(
        client,
        surname="Сидоров",
        name="Иван",
        patronymic="Петрович",
        email="sidorov@example.com",
        phone="+7 900 111-22-33",
        password="Parol9999",
        password_confirm="Parol9999",
    ).status_code == 200

    resp = client.get("/api/admin/users", headers=admin_headers(client))
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    by_email = {u["email"]: u for u in data["users"]}
    u1 = by_email["petrova@example.com"]
    u2 = by_email["sidorov@example.com"]
    for u in (u1, u2):
        assert set(u) == {"id", "fio", "email", "phone", "created_at"}
    assert u1["fio"] == "Петрова-Водкина Анна Оттовна"
    assert u1["phone"] == "+7 (912) 345-67-89"
    assert u2["fio"] == "Сидоров Иван Петрович"
    assert u2["phone"] == "+7 900 111-22-33"
    assert u1["created_at"] and u2["created_at"]


# --- TC-ADM-006: свежие записи сверху (разные created_at) ---------------------


def test_tc_adm_006_fresh_records_first_no_sleep(client):
    """TC-ADM-006: Свежие записи сверху.

    U1 (u1@example.com) и U2 (u2@example.com) с гарантированно разными
    created_at (больше 1 с разницы; time.sleep запрещен — пауза
    эмулируется прямым UPDATE created_at в тестовой БД). GET
    /api/admin/users: users[0].email = u2 (более поздняя), users[1].email
    = u1.
    """
    register(client, email="u1@example.com")
    register(client, email="u2@example.com")
    # без time.sleep: раздвигаем created_at детерминированно
    conn = sqlite3.connect(db_path())
    conn.execute(
        "UPDATE users SET created_at = '2026-10-08 07:00:00'"
        " WHERE email = 'u1@example.com'"
    )
    conn.execute(
        "UPDATE users SET created_at = '2026-10-08 07:00:02'"
        " WHERE email = 'u2@example.com'"
    )
    conn.commit()
    conn.close()

    data = client.get(
        "/api/admin/users", headers=admin_headers(client)
    ).json()
    assert data["users"][0]["email"] == "u2@example.com"
    assert data["users"][1]["email"] == "u1@example.com"


# --- TC-ADM-007: тай-брейк id DESC при совпадении created_at ------------------


def test_tc_adm_007_same_created_at_higher_id_first_deterministic(client):
    """TC-ADM-007: Тай-брейк при совпадении created_at — выше запись с
    бо́льшим id (MIN-3).

    U1 (t1@example.com) и U2 (t2@example.com) подряд; created_at обеих
    выровнены в одну секунду прямым UPDATE (детерминированный аналог шага
    «убедиться, что совпали»); порядок: t2, затем t1; повторный запрос
    дает тот же порядок (детерминирован).
    """
    register(client, email="t1@example.com")
    register(client, email="t2@example.com")
    conn = sqlite3.connect(db_path())
    conn.execute("UPDATE users SET created_at = '2026-10-08 07:00:00'")
    conn.commit()
    conn.close()

    headers = admin_headers(client)
    first = client.get("/api/admin/users", headers=headers).json()
    second = client.get("/api/admin/users", headers=headers).json()
    for data in (first, second):
        assert data["users"][0]["email"] == "t2@example.com"
        assert data["users"][1]["email"] == "t1@example.com"


# --- TC-ADM-008: формат CSV — BOM, «;», заголовок, роль ----------------------


def test_tc_adm_008_csv_format_bom_delimiter_header_role(client):
    """TC-ADM-008: Формат CSV — BOM (EF BB BF), разделитель «;», заголовок
    «ФИО;Email;Телефон;Роль;Дата регистрации», строка на каждого
    пользователя, Content-Disposition attachment (filename users.csv),
    Content-Type text/csv; charset=utf-8; в колонке «Роль» — «Ученик» у
    каждой строки.
    """
    register(client)
    register(
        client,
        email="sidorov@example.com",
        surname="Сидоров",
        password="Parol9999",
        password_confirm="Parol9999",
    )
    resp = client.get(
        "/api/admin/users/export.csv", headers=admin_headers(client)
    )
    assert resp.status_code == 200
    body = resp.content
    assert body.startswith(b"\xef\xbb\xbf")  # BOM: EF BB BF
    assert resp.headers["content-type"].startswith("text/csv")
    assert "charset=utf-8" in resp.headers["content-type"]
    assert (
        resp.headers["content-disposition"]
        == 'attachment; filename="users.csv"'
    )

    lines = csv_rows(resp)
    assert lines[0] == "ФИО;Email;Телефон;Роль;Дата регистрации"
    assert len(lines) == 3  # заголовок + 2 пользователя
    for line in lines[1:]:
        cells = line.split(";")
        assert cells[3] == "Ученик"


# --- TC-ADM-009: санитизация опасных префиксов = + - @ -----------------------


def test_tc_adm_009_csv_sanitizes_dangerous_prefixes(client):
    """TC-ADM-009: CSV-санитизация (MAJ-2): ячейка пользовательского поля
    (ФИО, email, телефон), начинающаяся с = + - @, получает префикс «'».

    A: surname "=1+1" → «'=1+1 …»; B: phone "+7 (999) 000-11-22" →
    «'+7 (999) 000-11-22»; C: surname "-Тестов" → «'-Тестов …»;
    D: surname "@dmin" → «'@dmin …». D3: пример спеки «email =1+1»
    невоспроизводим (не проходит валидацию FR-2) — проверка на ФИО и
    телефоне; шаг 5 (ручной контроль Excel) вне автотеста.
    """
    register(client, surname="=1+1", email="a1@example.com")
    register(client, phone="+7 (999) 000-11-22", email="b1@example.com")
    register(client, surname="-Тестов", email="c1@example.com")
    register(client, surname="@dmin", email="d1@example.com")

    resp = client.get(
        "/api/admin/users/export.csv", headers=admin_headers(client)
    )
    rows = {ln.split(";")[1]: ln for ln in csv_rows(resp)[1:]}

    assert rows["a1@example.com"].split(";")[0] == "'=1+1 Анна Оттовна"
    assert rows["b1@example.com"].split(";")[2] == "'+7 (999) 000-11-22"
    assert rows["c1@example.com"].split(";")[0].startswith("'-Тестов ")
    assert rows["d1@example.com"].split(";")[0].startswith("'@dmin ")
    # ни одна ячейка пользовательского поля не начинается с опасного префикса
    for email, line in rows.items():
        cells = line.split(";")
        for cell in (cells[0], cells[1], cells[2]):
            assert not cell.startswith(("=", "+", "-", "@")), line


# --- TC-ADM-010: безопасные значения не искажаются ----------------------------


def test_tc_adm_010_csv_safe_values_untouched(client):
    """TC-ADM-010: CSV-санитизация не искажает безопасные значения.

    surname "Петров", phone "8 (999) 123-45-67" (без «+», D4): ни одна
    ячейка ФИО/Email/Телефон не начинается с «'»; значения в CSV в
    точности равны введенным.
    """
    register(
        client,
        surname="Петров",
        patronymic="Ивановна",
        email="petrov@example.com",
        phone="8 (999) 123-45-67",
        password="Parol9999",
        password_confirm="Parol9999",
    )
    resp = client.get(
        "/api/admin/users/export.csv", headers=admin_headers(client)
    )
    line = csv_rows(resp)[1]
    cells = line.split(";")
    assert cells[:4] == [
        "Петров Анна Ивановна",
        "petrov@example.com",
        "8 (999) 123-45-67",
        "Ученик",
    ]


# --- TC-ADM-011: дата регистрации в CSV — локальный день (DD.MM.YYYY) --------


def test_tc_adm_011_csv_date_is_local_calendar_day(client):
    """TC-ADM-011: Дата регистрации в CSV — ЛОКАЛЬНЫЙ календарный день
    (MIN-4: UTC→локаль перед форматированием DD.MM.YYYY).

    created_at выставлен прямым UPDATE в «опасное» окно: UTC-время, при
    котором локальная дата != UTC-дата (вчерашний день 23:40 UTC →
    локально следующий день при положительном смещении зоны). Ожидается
    DD.MM.YYYY локального дня; формат даты — строго DD.MM.YYYY.
    """
    register(client, email="tz@example.com")
    # «опасное» окно строится от фактической зоны: нужен момент, где
    # локальная дата != UTC-дата. При положительном смещении зоны +offset
    # берем 00:30 UTC текущего UTC-дня: локально это уже 00:30+offset
    # следующего дня (пример спеки: 21:30 UTC при Europe/Moscow = 00:30
    # локального следующего дня). При TZ=UTC окно недостижимо — проверяем
    # только формат DD.MM.YYYY (локальный день = UTC дню).
    from datetime import datetime as dt, timedelta as td, timezone as tz

    local_now = dt.now().astimezone()
    offset = local_now.utcoffset() or td(0)
    offset_minutes = offset.total_seconds() / 60
    days_differ = offset_minutes != 0
    if days_differ:
        # «опасное» окно: для положительной зоны — конец UTC-дня (23:40 UTC,
        # локально уже следующий день; пример спеки: 21:30 UTC при
        # Europe/Moscow = 00:30 локального следующего дня); для отрицательной
        # зоны — начало UTC-дня (00:30 UTC, локально еще предыдущий день).
        utc_now = dt.now(tz.utc)
        edge = (23, 40) if offset_minutes > 0 else (0, 30)
        danger_moment = utc_now.replace(
            hour=edge[0], minute=edge[1], second=0, microsecond=0
        )
        if danger_moment > utc_now:
            danger_moment -= td(days=1)
    else:
        # TZ=UTC: окно разных дней недостижимо — просто текущий момент.
        danger_moment = local_now.astimezone(tz.utc)
    danger_utc = danger_moment.strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(db_path())
    conn.execute("UPDATE users SET created_at = ?", (danger_utc,))
    conn.commit()
    conn.close()

    resp = client.get(
        "/api/admin/users/export.csv", headers=admin_headers(client)
    )
    row = csv_rows(resp)[1]
    cells = row.split(";")
    date_str = cells[4]
    # формат DD.MM.YYYY
    datetime.strptime(date_str, "%d.%m.%Y")
    expected_local = (
        datetime.strptime(danger_utc, "%Y-%m-%d %H:%M:%S")
        .replace(tzinfo=timezone.utc)
        .astimezone()
        .strftime("%d.%m.%Y")
    )
    assert date_str == expected_local
    # GIVEN: локальный день отличается от UTC-дня (окно разных дней);
    # недостижимо только при TZ=UTC
    utc_day = danger_utc[:10].split("-")
    utc_ddmmyyyy = f"{utc_day[2]}.{utc_day[1]}.{utc_day[0]}"
    if days_differ:
        assert date_str != utc_ddmmyyyy


# --- TC-ADM-012: пустой CSV при отсутствии пользователей ---------------------


def test_tc_adm_012_csv_empty_with_no_users(client):
    """TC-ADM-012: Пустой CSV при отсутствии пользователей.

    users пуст (fixture дает чистую БД): 200; тело начинается с BOM;
    после декодирования ровно одна строка — заголовок
    «ФИО;Email;Телефон;Роль;Дата регистрации»; строк данных нет.
    """
    resp = client.get(
        "/api/admin/users/export.csv", headers=admin_headers(client)
    )
    assert resp.status_code == 200
    assert resp.content.startswith(b"\xef\xbb\xbf")
    assert csv_rows(resp) == ["ФИО;Email;Телефон;Роль;Дата регистрации"]
