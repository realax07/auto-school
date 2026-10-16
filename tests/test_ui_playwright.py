"""Playwright UI-тесты auto-school (Спринт 2, требование Заказчика:
«должно быть все покрыто ими»).

Самодостаточность: session-фикстура `server` поднимает uvicorn
backend.app:app на 127.0.0.1:<ephemeral port> с AUTOSCHOOL_DB_PATH во
временном каталоге (data/app.db и прод-порт 8390 не затрагиваются);
teardown завершает процесс и удаляет временные файлы. Никаких внешних
зависимостей: UI_TESTS не нужен, skipif снят.

Запуск: cd ~/auto-school && .venv/bin/python -m pytest tests/test_ui_playwright.py -v
Требуется playwright chromium (~/.cache/ms-playwright). На хостах без
системных библиотек браузера указать LD_LIBRARY_PATH с каталогом
распакованных .deb (libatk и др.) — сам бинарник chromium уже скачан.

Стиль: синхронный API, без sleep — только expect/wait_for.
"""
import bcrypt
import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

pw = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

ADMIN_LOGIN = "ui-admin"
ADMIN_PASSWORD = "ui-admin-pass-2026"

SERVER_STARTUP_TIMEOUT = 60  # секунды на ожидание /api/health
PORT_START_ATTEMPTS = 2  # retry с новым портом (TOCTOU, F-2 review-001)


def _free_port() -> int:
    """Свободный TCP-порт, отданный ядром (bind :0 → close)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _stderr_tail(path: str, limit: int = 20) -> str:
    """Хвост stderr-лога uvicorn для диагностики упавшего старта (F-3)."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return "".join(f.readlines()[-limit:])
    except OSError:
        return "(stderr-лог недоступен)"


def _terminate(proc: subprocess.Popen) -> None:
    """Гарантированное завершение дочернего процесса: term → kill."""
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)


# ---------------------------------------------------------------- API-хелпер
def api(method: str, path: str, *, base: str, body: dict | None = None,
        token: str | None = None, admin_token: str | None = None):
    """HTTP-вызов API тестового сервера (urllib, без внешних зависимостей).

    Возвращает (status, dict) — dict может быть None при пустом теле.
    """
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["X-Session-Token"] = token
    if admin_token:
        headers["X-Admin-Token"] = admin_token
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:  # контрактные 4xx/5xx
        raw = exc.read()
        return exc.code, (json.loads(raw) if raw else None)


def admin_login(base: str) -> str:
    """Токен админа (POST /api/admin/login) для модерации через API."""
    status, data = api("POST", "/api/admin/login", base=base, body={
        "login": ADMIN_LOGIN, "password": ADMIN_PASSWORD})
    assert status == 200 and data and data.get("ok"), (status, data)
    return data["token"]


def unique_email(prefix: str) -> str:
    """Уникальный email на тест (БД чистая, но стиль — без неявных склеек)."""
    return f"{prefix}-{uuid.uuid4().hex[:10]}@ui-test.example.ru"


# ------------------------------------------------------------- фикстуры
@pytest.fixture(scope="session")
def server():
    """Изолированный сервер: uvicorn backend.app:app на эфемерном порту,
    БД во временном файле. Teardown: terminate → wait → kill → rmtree.

    stderr uvicorn пишется в temp-файл: при неуспешном старте хвост лога
    попадает в текст исключения (F-3 review-001). Порт выдаётся ядром до
    старта uvicorn и в этом окне может быть занят другим процессом, поэтому
    при неудачном старте — одна повторная попытка с новым портом (F-2).
    """
    tmpdir = tempfile.mkdtemp(prefix="autoschool-ui-tests-")
    proc: subprocess.Popen | None = None
    stderr_file = None
    try:
        base = None
        for attempt in range(1, PORT_START_ATTEMPTS + 1):
            port = _free_port()
            base = f"http://127.0.0.1:{port}"
            env = os.environ.copy()
            env.update({
                "AUTOSCHOOL_DB_PATH": os.path.join(tmpdir, "app.db"),
                "ADMIN_USER": ADMIN_LOGIN,
                # bcrypt-хэш тестового пароля (cost 12, как в sdd §5)
                "ADMIN_PASSWORD_HASH": bcrypt.hashpw(
                    ADMIN_PASSWORD.encode(), bcrypt.gensalt(rounds=12)).decode(),
                "SECRET": "ui-tests-secret",
                # дописываем к унаследованному, а не затираем (F-6 review-001)
                "PYTHONPATH": str(ROOT) + os.pathsep + env.get("PYTHONPATH", ""),
            })
            stderr_path = os.path.join(tmpdir, "uvicorn-stderr.log")
            stderr_file = open(stderr_path, "wb")
            try:
                proc = subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "backend.app:app",
                     "--host", "127.0.0.1", "--port", str(port),
                     "--log-level", "warning"],
                    cwd=str(ROOT), env=env,
                    stdout=subprocess.DEVNULL, stderr=stderr_file,
                )
            except Exception:
                stderr_file.close()
                raise  # tmpdir уберёт finally (F-5 review-001)

            # готовность: опрос /api/health до дедлайна (без sleep)
            deadline = time.monotonic() + SERVER_STARTUP_TIMEOUT
            last_error: Exception | None = None
            ready = False
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    break
                try:
                    status, data = api("GET", "/api/health", base=base)
                    if status == 200 and data == {"ok": True}:
                        ready = True
                        break
                except (urllib.error.URLError, ConnectionError, OSError) as exc:
                    last_error = exc  # сервер еще не слушает порт — продолжаем
            if ready:
                break
            # не поднялся: диагностика + retry с новым портом (последняя
            # попытка — пробрасываем ошибку с хвостом stderr)
            diag = (f"попытка {attempt}/{PORT_START_ATTEMPTS}, "
                    f"code={proc.returncode}, последняя ошибка health: {last_error}\n"
                    f"хвост stderr:\n{_stderr_tail(stderr_path)}")
            _terminate(proc)
            proc = None
            stderr_file.close()
            stderr_file = None
            if attempt == PORT_START_ATTEMPTS:
                raise RuntimeError(
                    f"сервер не поднялся за {SERVER_STARTUP_TIMEOUT}s ({diag})")
        yield base
    finally:
        if proc is not None:
            _terminate(proc)
        if stderr_file is not None:
            stderr_file.close()
        shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture(scope="module")
def browser():
    """Chromium (headless) на модуль тестов."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)  # headless явно (F-8 review-001)
        yield b
        b.close()


@pytest.fixture()
def page(browser):
    """Свежий контекст на тест (изолированный sessionStorage) + автоскрины."""
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    yield pg
    ctx.close()


# ------------------------------------------------------------------ тесты
def test_student_landing_login_modal_centered(page, server):
    """TC-UI-001 (change add-instructor-cabinet): лендинг ученика загружается,
    «Войти» открывает модалку входа по центру экрана."""
    page.goto(f"{server}/")
    # лендинг загрузился: заголовок hero и кнопки авторизации в шапке
    expect(page.locator(".intro h1")).to_contain_text("Права")
    expect(page.locator('.auth [data-open="login"]')).to_be_visible()

    # клик «Войти» → модалка входа видима и отцентрирована
    page.locator('.auth [data-open="login"]').click()
    overlay = page.locator("#m-login.overlay")
    expect(overlay).to_be_visible()
    box = overlay.bounding_box()
    vp = page.viewport_size
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    assert abs(cx - vp["width"] / 2) < 30, "модалка не по центру по X"
    assert abs(cy - vp["height"] / 2) < 80, "модалка не по центру по Y"


def test_student_register_redirects_to_cabinet(page, server):
    """TC-UI-002 (change add-instructor-cabinet): регистрация ученика —
    заполнение формы, сабмит, редирект в кабинет с валидным токеном."""
    page.goto(f"{server}/")
    page.locator('.auth [data-open="register"]').click()
    expect(page.locator("#m-register.overlay")).to_be_visible()

    email = unique_email("student")
    page.fill("#reg-surname", "Иванов")
    page.fill("#reg-name", "Иван")
    page.fill("#reg-patronymic", "Иванович")
    page.fill("#reg-email", email)
    page.fill("#reg-phone", "+7 900 111-22-33")
    page.fill("#reg-password", "S3cretPass!")
    page.fill("#reg-password-confirm", "S3cretPass!")
    page.locator("#reg-submit").click()

    # редирект в кабинет ученика после успешной регистрации
    page.wait_for_url("**/cabinet")

    # токен сессии сохранен и валиден: GET /api/auth/me отвечает ФИО
    token = page.evaluate("sessionStorage.getItem('session_token')")
    assert token, "session_token не сохранен после регистрации"
    status, data = api("GET", "/api/auth/me", base=server, token=token)
    assert status == 200 and data and data["ok"], (status, data)
    assert data["user"]["email"] == email

    # кабинет отрисовал ФИО из API (подстановка без перезагрузки)
    expect(page.locator(".uname")).to_have_text("Иванов Иван Иванович")


def test_instructors_landing_brand_and_cta(page, server):
    """TC-UI-003 (change add-instructor-cabinet): лендинг инструкторов —
    бренд «Сбер» зелёным, CTA-кнопки шапки рядом, hero-«Войти» отсутствует."""
    page.goto(f"{server}/instructors")
    brand = page.locator(".brand em")
    expect(brand).to_have_text("Сбер")
    assert brand.evaluate(
        "el => getComputedStyle(el).color") == "rgb(53, 216, 121)"  # #35d879

    # CTA-кнопки шапки видимы и стоят рядом (зазор < 40px)
    login = page.locator('.header-cta[data-open-login]')
    apply = page.locator('.header-cta[href="/instructors/apply"]')
    expect(login).to_be_visible()
    expect(apply).to_be_visible()
    lb, ab = login.bounding_box(), apply.bounding_box()
    assert ab["x"] - (lb["x"] + lb["width"]) < 40

    # в теле лендинга нет своей кнопки «Войти» (только в шапке)
    assert page.locator(".actions [data-open-login]").count() == 0


def test_instructor_apply_valid_form_goes_pending(page, server):
    """TC-UI-004 (change add-instructor-cabinet): анкета инструктора — ФИО
    в трёх полях, сабмит валидной анкеты → экран ожидания модерации."""
    page.goto(f"{server}/instructors/apply")
    # ФИО — три отдельных поля (правка Заказчика 2026-10-14)
    for fid in ("surname", "name", "patronymic"):
        expect(page.locator(f"#{fid}")).to_have_count(1)

    page.fill("#surname", "Смирнова")
    page.fill("#name", "Ольга")
    page.fill("#patronymic", "Павловна")
    page.fill("#phone", "+7 901 222-33-44")
    page.fill("#email", unique_email("instructor"))
    page.fill("#address", "г. Москва, ул. Полярная, д. 3, кв. 12")
    # формат работы по умолчанию «own» (свой автомобиль) → госномер обязателен
    page.fill("#plate", "А123АА 777")
    page.fill("#license-number", "9912345678")
    page.select_option("#license-category", "B")
    page.fill("#password", "Dr1vePass!")
    page.fill("#password-confirm", "Dr1vePass!")
    page.locator(".checkline input").check()

    page.locator("#registration button.submit").click()

    # 200 {"ok": true} → редирект на экран ожидания (FR-12)
    page.wait_for_url("**/instructors/pending")
    expect(page.locator("h1")).to_have_text("Заявка на рассмотрении")


def test_instructor_apply_upload_icon_centered(page, server):
    """TC-UI-004 (change add-instructor-cabinet): анкета инструктора —
    центрирование иконки загрузки ВУ по вертикали в upload-фрейме
    (допуск 6px; покрытие возвращено из старого TC-UI-002 по F-4
    review-001)."""
    page.goto(f"{server}/instructors/apply")
    frame = page.locator(".upload")
    icon = page.locator(".upload-icon")
    expect(frame).to_be_visible()
    expect(icon).to_be_visible()
    fb, ib = frame.bounding_box(), icon.bounding_box()
    frame_cy = fb["y"] + fb["height"] / 2
    icon_cy = ib["y"] + ib["height"] / 2
    assert abs(frame_cy - icon_cy) <= 6, (
        f"иконка загрузки не по центру фрейма: {abs(frame_cy - icon_cy):.1f}px > 6px")


def test_instructor_login_approved_dashboard_layout(page, server):
    """TC-UI-005 (change add-instructor-cabinet): вход approved-инструктора
    → /instructor/dashboard: сайдбар слева, main справа (aside и main —
    прямые дети .app, grid ровно 2 колонки), ФИО из API в шапке."""
    # подготовка через API: заявка → approve (поток инструктора §15)
    email, password = unique_email("approved"), "Dr1vePass!"
    status, data = api("POST", "/api/instructors/apply", base=server, body={
        "surname": "Громов", "name": "Борис", "patronymic": "Арсеньевич",
        "phone": "+7 902 333-44-55", "email": email,
        "address": "г. Москва, ул. Летняя, д. 5", "work_format": "school",
        "license_number": "9987654321", "license_category": "B",
        "password": password, "password_confirm": password, "consent": True,
    })
    assert status == 200 and data and data["ok"], (status, data)
    admin_token = admin_login(server)
    status, listing = api("GET", "/api/admin/instructor-applications",
                          base=server, admin_token=admin_token)
    assert status == 200 and listing, (status, listing)
    app_id = next(a["id"] for a in listing["applications"] if a["email"] == email)
    status, data = api(
        "POST", f"/api/admin/instructor-applications/{app_id}/approve",
        base=server, admin_token=admin_token)
    assert status == 200 and data and data["ok"], (status, data)

    # UI-вход с лендинга ученика
    page.goto(f"{server}/")
    page.locator('.auth [data-open="login"]').click()
    page.fill("#login-email", email)
    page.fill("#login-password", password)
    page.locator("#login-submit").click()

    # route='cabinet' (§15.5) → редирект в кабинет инструктора
    page.wait_for_url("**/instructor/dashboard")

    # структурная вёрстка (F-1 review-001: вместо вакуумного "</aside>" in
    # page.content() — проверка, способная упасть): aside и main существуют
    # как прямые дети-соседи .app
    assert page.locator(".app > aside").count() == 1, ".app > aside не найден"
    assert page.locator(".app > main").count() == 1, ".app > main не найден"
    # .app — grid ровно с 2 колонками
    layout = page.evaluate(
        "() => { const s = getComputedStyle(document.querySelector('.app'));"
        " return { display: s.display,"
        " cols: s.gridTemplateColumns.split(' ').filter(v => parseFloat(v) > 0).length }; }")
    assert layout["display"] == "grid", ".app не grid"
    assert layout["cols"] == 2, f".app должен иметь 2 колонки, а не {layout['cols']}"

    # сайдбар слева, main справа: правая граница aside не заходит на main
    aside = page.locator("aside").bounding_box()
    main = page.locator("main").bounding_box()
    assert aside["x"] + aside["width"] <= main["x"] + 1, "main левее сайдбара"

    # ФИО в шапке подставлено из API (инструктор Громов Борис Арсеньевич)
    expect(page.locator(".user b")).to_have_text("Громов Борис Арсеньевич")


def test_admin_moderation_approve_reflects_status(page, server):
    """TC-UI-006 (change add-instructor-student-loop, BUG-046): админ-модерация
    через UI на реальном бэкенде — колонки «Действия» в таблице заявок нет
    (решение Заказчика: действия только в модалке); клик по строке заявки
    waiting открывает модальную карточку, «Одобрить» → статус отражается
    в списке (waiting → approved)."""
    email = unique_email("moderated")
    status, data = api("POST", "/api/instructors/apply", base=server, body={
        "surname": "Кузнецов", "name": "Пётр", "patronymic": "Игнатьевич",
        "phone": "+7 903 444-55-66", "email": email,
        "address": "г. Москва, ул. Зимняя, д. 7", "work_format": "own",
        "plate": "А123АА 777", "license_number": "9911223344",
        "license_category": "B", "password": "Dr1vePass!",
        "password_confirm": "Dr1vePass!", "consent": True,
    })
    assert status == 200 and data and data["ok"], (status, data)

    _seed_session(page, "admin_token", admin_login(server))
    page.goto(f"{server}/admin-dashboard")
    page.locator(".nav button", has_text="Заявки инструкторов").click()

    row = page.locator("#app-rows tr", has_text=email)
    expect(row).to_have_count(1)
    # колонки «Действия» больше нет (BUG-046)
    assert page.locator("th", has_text="Действия").count() == 0
    assert page.locator("#app-rows .btn-export").count() == 0, \
        "inline-кнопки «Одобрить/Отклонить» должны быть убраны из строк"

    # клик по строке → модальная карточка
    row.click()
    expect(page.locator("#ic-backdrop")).to_be_visible()
    expect(page.locator("#ic-name")).to_have_text("Кузнецов Пётр Игнатьевич")

    # «Одобрить» в модалке (confirm-диалог подтверждения — авто-accept)
    page.on("dialog", lambda d: d.accept())
    page.locator("#ic-approve").click()

    # карточка закрылась, список перезагрузился: статус отражен
    expect(page.locator("#ic-backdrop")).to_be_hidden()
    after_row = page.locator("#app-rows tr", has_text=email)
    expect(after_row.locator(".badge")).to_have_text("Одобрена")
    # кнопки действий в модалке для решенной заявки скрыты
    after_row.click()
    expect(page.locator("#ic-backdrop")).to_be_visible()
    expect(page.locator("#ic-approve")).to_be_hidden()
    expect(page.locator("#ic-deny")).to_be_hidden()


def test_admin_deny_modal_locked_until_comment_and_waiting_badge_yellow(
        page, server):
    """TC-UI-013 (change add-instructor-student-loop, BUG-046): строка заявки
    waiting открывает модальную карточку; бейдж «На рассмотрении» — желтый;
    «Отклонить» в модалке открывает панель причины, подтверждение заблокировано
    до непустого комментария (BUG-045-паттерн); отклонение → статус «Отклонена»
    и причина отражены в списке. Реальный бэкенд."""
    email = unique_email("denied")
    status, data = api("POST", "/api/instructors/apply", base=server, body={
        "surname": "Нечаева", "name": "Ольга", "patronymic": "Павловна",
        "phone": "+7 904 555-66-77", "email": email,
        "address": "г. Москва, ул. Осенняя, д. 9", "work_format": "school",
        "license_number": "9955667788", "license_category": "B",
        "password": "Dr1vePass!", "password_confirm": "Dr1vePass!",
        "consent": True,
    })
    assert status == 200 and data and data["ok"], (status, data)

    _seed_session(page, "admin_token", admin_login(server))
    page.goto(f"{server}/admin-dashboard")
    page.locator(".nav button", has_text="Заявки инструкторов").click()

    row = page.locator("#app-rows tr", has_text=email)
    expect(row).to_have_count(1)

    # желтый бейдж waiting: фон #3a2f14, текст #ffc76e, бордер #8a6d1f
    badge = row.locator(".badge")
    expect(badge).to_have_text("На рассмотрении")
    style = badge.evaluate(
        "el => { const s = getComputedStyle(el);"
        " return { bg: s.backgroundColor, color: s.color, border: s.borderColor }; }")
    assert style["bg"] == "rgb(58, 47, 20)", style    # #3a2f14
    assert style["color"] == "rgb(255, 199, 110)", style  # #ffc76e
    assert style["border"] == "rgb(138, 109, 31)", style  # #8a6d1f

    # клик по строке → модалка; «Отклонить» → панель причины в той же модалке
    row.click()
    expect(page.locator("#ic-backdrop")).to_be_visible()
    expect(page.locator("#ic-name")).to_have_text("Нечаева Ольга Павловна")
    page.locator("#ic-deny").click()
    expect(page.locator("#ic-deny-box")).to_be_visible()

    # подтверждение заблокировано до непустого комментария
    confirm = page.locator("#ic-deny-confirm")
    expect(confirm).to_be_disabled()
    page.fill("#ic-deny-comment", " ")  # только пробел — всё еще блокировано
    expect(confirm).to_be_disabled()
    page.fill("#ic-deny-comment", "Не подтверждена квалификация")
    expect(confirm).to_be_enabled()
    confirm.click()

    # карточка закрылась; статус и причина отражены в списке
    expect(page.locator("#ic-backdrop")).to_be_hidden()
    after_row = page.locator("#app-rows tr", has_text=email)
    expect(after_row.locator(".badge")).to_have_text("Отклонена")
    expect(after_row).to_contain_text("Не подтверждена квалификация")


def test_admin_dashboard_bug046_mock_sync_fragments():
    """TC-UI-014 (change add-instructor-student-loop, BUG-046): design-guard —
    фрагменты verbatim frontend/admin-dashboard.html ↔ design/mocks/
    admin-dashboard.html: таблица заявок без колонки «Действия», желтый
    wait-бейдж, клик-подсказка, панель отказа в модалке."""
    page_html = (ROOT / "frontend" / "admin-dashboard.html").read_text(
        encoding="utf-8")
    mock_html = (ROOT / "design" / "mocks" / "admin-dashboard.html").read_text(
        encoding="utf-8")
    fragments = [
        # желтый статус «На рассмотрении»
        ".badge.wait{background:#3a2f14;color:#ffc76e;border:1px solid #8a6d1f}",
        # таблица заявок без колонки «Действия»
        "<thead><tr><th>ФИО</th><th>Email</th><th>Телефон</th><th>Формат</th>"
        "<th>ВУ</th><th>Стаж</th><th>Статус</th><th>Причина отказа</th></tr></thead>",
        # клик-подсказка под таблицей
        '<div class="rowhint">Строка кликабельна — откроется карточка заявки</div>',
        # панель отказа внутри модальной карточки (BUG-045-паттерн)
        '<button class="btn-export" id="ic-deny-confirm" disabled>Отклонить</button>',
    ]
    for fragment in fragments:
        assert fragment in page_html, f"нет во фронте: {fragment!r}"
        assert fragment in mock_html, f"нет в мокапе: {fragment!r}"
    # колонка «Действия» (th) нигде не осталась
    assert "<th>Действия</th>" not in page_html
    assert "<th>Действия</th>" not in mock_html


# =========================================================================
# Спринт 3, Партия A (change add-instructor-student-loop): FRONTEND e2e.
# Бэкенд-задачи параллельны — все новые API мокаются через page.route:
# тесты не зависят от backend/ и от маршрутов статики для новых страниц
# (страница отдается route.fulfill из frontend/).
# =========================================================================

PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAC"
    "hwGA60e6kgAAAABJRU5ErkJggg==")  # валидный PNG 1×1

SESSION_TOKEN = "ui-s3-student-token"
INSTRUCTOR_TOKEN = "ui-s3-instructor-token"
ADMIN_TOKEN = "ui-s3-admin-token"


def _serve_frontend(page, server, path: str, filename: str) -> None:
    """Отдать frontend/<filename> по <server><path>: новая страница не зависит
    от бэкенда (маршрут статики /instructor-choice добавит задача 7.1)."""
    body = (ROOT / "frontend" / filename).read_text(encoding="utf-8")
    page.route(f"{server}{path}", lambda route: route.fulfill(
        status=200, content_type="text/html; charset=utf-8", body=body))


def _route_json(page, server, path: str, respond, *,
                method: str | None = None, capture: list | None = None):
    """page.route на <server><path>: fulfill JSON-ом respond(request).

    respond(request) -> (status, payload). Чужие методы/пути — continue_().
    """
    def _handler(route):
        req = route.request
        if method is not None and req.method != method:
            # fallback (не continue_): передать СЛЕДУЮЩему подходящему
            # обработчику page.route, а не в реальную сеть
            route.fallback()
            return
        if capture is not None:
            capture.append(req)
        status, payload = respond(req)
        route.fulfill(status=status, content_type="application/json",
                      body=json.dumps(payload, ensure_ascii=False))
    # '*' в хвосте: совпадение и с query-string (фильтры каталога и т.п.)
    page.route(f"{server}{path}*", _handler)


def _seed_session(page, key: str, value: str) -> None:
    """Положить токен в sessionStorage до скриптов страницы (page.route +
    add_init_script — без реального логина).

    Сторож в localStorage: init-скрипт переисполняется на каждой навигации
    (например, редирект после logout), а не должен восстанавливать токен,
    очищенный самим logout'ом (проверка очистки сессии в TC-UI-010).
    """
    page.add_init_script(
        f"if(!localStorage.getItem('ui-seeded')){{"
        f"localStorage.setItem('ui-seeded','1');"
        f"sessionStorage.setItem('{key}','{value}');}}")


def _instructor_card(idx: int, *, id: int, exp: int, transmission: str,
                     rating, slots: list) -> dict:
    """Шейп карточки — РЕАЛЬНЫЙ ответ GET /api/student/instructors
    (backend/student_marketplace.py; review-001 #5: моки с вымышленными
    полями fio/experience/slots неспособны поймать расхождение
    фронт↔бэк)."""
    return {
        "id": id,
        "full_name": ["Самойлов Михаил Петрович", "Гордеева Анна Викторовна",
                      "Белов Артём Дмитриевич"][idx],
        "experience_years": exp,
        "cars": [{"id": 51 + idx,
                  "brand": ["Škoda", "Volkswagen", "Lada"][idx],
                  "model": ["Rapid", "Polo", "Granta"][idx],
                  "year": 2020 + idx, "transmission": transmission}],
        "rating": rating,  # {has_reviews:true,average,count} | {has_reviews:false}
        "availability": slots,
    }


def _choice_instructors(params: dict) -> list:
    """Серверная фильтрация каталога (замоканный GET /api/student/instructors)."""
    pool = [
        _instructor_card(0, id=1, exp=11, transmission="manual",
                         rating={"average": 4.8, "count": 14},
                         slots=[{"weekday": 0, "start_time": "10:00",
                                 "end_time": "14:00"}]),
        _instructor_card(1, id=2, exp=6, transmission="automatic",
                         rating={"average": 4.6, "count": 9},
                         slots=[{"weekday": 2, "start_time": "09:00",
                                 "end_time": "13:00"}]),
        _instructor_card(2, id=3, exp=1, transmission="manual",
                         rating={"has_reviews": False},
                         slots=[{"weekday": 5, "start_time": "18:00",
                                 "end_time": "21:00"}]),
    ]
    if params.get("transmission"):
        pool = [i for i in pool
                if any(c["transmission"] == params["transmission"]
                       for c in i["cars"])]
    if params.get("min_experience"):
        pool = [i for i in pool
                if i["experience_years"] >= int(params["min_experience"])]
    return pool


def test_student_choice_filters_narrow_and_apply_request(page, server):
    """TC-UI-007 (change add-instructor-student-loop): «Выбор инструктора» —
    фильтры сужают список (запрос с query-параметрами, серверная фильтрация),
    «Подать заявку» шлёт POST /api/student/requests {instructor_id}.
    Моки — с шейпами РЕАЛЬНОГО бэкенда (review-001 #5)."""
    _serve_frontend(page, server, "/instructor-choice", "instructor-choice.html")
    _seed_session(page, "session_token", SESSION_TOKEN)

    list_queries: list[dict] = []
    post_requests: list = []

    def _respond_list(req):
        params = {k: v[0] for k, v in
                  parse_qs(urlparse(req.url).query).items()}
        list_queries.append(params)
        assert req.headers.get("x-session-token") == SESSION_TOKEN
        return 200, {"ok": True, "instructors": _choice_instructors(params)}

    _route_json(page, server, "/api/auth/me", lambda req: (
        200, {"ok": True, "user": {"surname": "Иванов", "name": "Иван",
                                   "patronymic": "Иванович"}}))
    _route_json(page, server, "/api/student/instructors", _respond_list)
    _route_json(page, server, "/api/student/requests", lambda req: (
        200, {"ok": True, "request_id": 900}), method="POST",
        capture=post_requests)

    page.goto(f"{server}/instructor-choice")
    expect(page.locator(".card")).to_have_count(3)
    expect(page.locator(".uname")).to_have_text("Иванов Иван Иванович")

    # фильтр «Механика» -> query-параметр transmission=manual, список сужен
    page.locator("#f-trans button[data-v='manual']").click()
    expect(page.locator(".card")).to_have_count(2)
    assert list_queries[-1].get("transmission") == "manual"

    # фильтр «Стаж от 5 лет» -> min_experience, остаётся один инструктор
    page.locator("#f-exp button[data-v='5']").click()
    expect(page.locator(".card")).to_have_count(1)
    assert list_queries[-1].get("transmission") == "manual"
    assert list_queries[-1].get("min_experience") == "5"
    expect(page.locator(".card b").first).to_have_text(
        "Самойлов Михаил Петрович")

    # сброс -> снова 3 карточки, фильтров в query нет
    page.locator("#reset").click()
    expect(page.locator(".card")).to_have_count(3)
    assert "transmission" not in list_queries[-1]

    # «Подать заявку» -> POST /api/student/requests {instructor_id}
    page.locator(".card[data-id='2'] .apply").click()
    expect(page.locator(".card[data-id='2'] .apply")).to_have_text(
        "✓ Заявка отправлена")
    assert len(post_requests) == 1
    assert json.loads(post_requests[0].post_data) == {"instructor_id": 2}


def test_instructor_calendar_slot_toggle_and_put_availability(page, server):
    """TC-UI-008 (change add-instructor-student-loop): «Календарь» — клик по
    слоту переключает состояние (вкл/выкл), «Сохранить график» шлёт PUT
    /api/instructor/availability (полная замена: снятый слот удален).
    API замокан через page.route."""
    _seed_session(page, "session_token", INSTRUCTOR_TOKEN)

    put_bodies: list = []
    _route_json(page, server, "/api/auth/me", lambda req: (
        200, {"ok": True, "user": {"surname": "Самойлов", "name": "Михаил"}}))
    _route_json(page, server, "/api/instructor/dashboard", lambda req: (
        200, {"ok": True, "instructor": {"surname": "Самойлов",
                                         "name": "Михаил"}}))
    _route_json(page, server, "/api/instructor/summary", lambda req: (
        200, {"ok": True, "students": [], "today_lessons": []}))
    _route_json(page, server, "/api/instructor/requests", lambda req: (
        200, {"ok": True, "requests": []}))
    _route_json(page, server, "/api/instructor/availability", lambda req: (
        200, {"ok": True, "intervals": [
            {"weekday": 0, "start_time": "10:00", "end_time": "14:00"}]}))
    _route_json(page, server, "/api/instructor/availability", lambda req: (
        200, {"ok": True}), method="PUT", capture=put_bodies)

    page.goto(f"{server}/instructor/dashboard")
    expect(page.locator(".user b")).to_have_text("Самойлов Михаил")

    page.locator('.nav button[data-tab="Календарь"]').click()
    expect(page.locator("#cal-grid")).to_be_visible()

    # восстановление графика GET: Пн 10:00–14:00 -> слоты 0-10 и 0-12 отмечены
    expect(page.locator(".cal-slot[data-k='0-10']")).to_have_class("cal-slot on")
    expect(page.locator(".cal-slot[data-k='0-12']")).to_have_class("cal-slot on")
    # посторонний слот не отмечен
    assert page.locator(".cal-slot[data-k='3-14']").get_attribute(
        "class") == "cal-slot"

    # клик по слоту: снять 0-10 -> отметить 3-14 -> вернуть 0-10
    page.locator(".cal-slot[data-k='0-10']").click()
    expect(page.locator(".cal-slot[data-k='0-10']")).to_have_class("cal-slot")
    expect(page.locator("#cal-changed")).to_be_visible()
    page.locator(".cal-slot[data-k='3-14']").click()
    expect(page.locator(".cal-slot[data-k='3-14']")).to_have_class(
        "cal-slot on")
    page.locator(".cal-slot[data-k='0-10']").click()
    expect(page.locator(".cal-slot[data-k='0-10']")).to_have_class(
        "cal-slot on")

    # сохранение: PUT с полной заменой (снятый 0-12 удален)
    page.locator("#cal-save").click()
    expect(page.locator("#cal-changed")).to_be_hidden()
    assert len(put_bodies) == 1
    body = json.loads(put_bodies[0].post_data)
    got = {(iv["weekday"], iv["start_time"], iv["end_time"])
           for iv in body["intervals"]}
    assert got == {(0, "10:00", "12:00"), (0, "12:00", "14:00"),
                   (3, "14:00", "16:00")}, got


def test_instructor_requests_deny_locked_until_comment_accept_with_car(
        page, server):
    """TC-UI-009 (change add-instructor-student-loop): «Запросы учеников» —
    «Отказать» заблокировано до непустого комментария (FR-38), сабмит шлёт
    POST …/deny {comment}; «Принять» требует выбор авто и шлёт POST …/accept
    {car_id} (FR-39). Мок /api/instructor/requests — шейп РЕАЛЬНОГО бэкенда
    backend/student_requests.py (review-001 #2/#5): student_full_name,
    student_experience_years, car-объект; полей student_fio/comment нет."""
    _seed_session(page, "session_token", INSTRUCTOR_TOKEN)

    reqs = [
        {"id": 301, "status": "new", "created_at": "2026-10-15 09:14:00",
         "decided_at": None, "student_full_name": "Павел Ежов",
         "student_experience_years": 0, "car": None},
        {"id": 302, "status": "new", "created_at": "2026-10-14 19:40:00",
         "decided_at": None, "student_full_name": "Ольга Нечаева",
         "student_experience_years": 2, "car": None},
    ]
    cars = [
        {"id": 11, "brand": "Škoda", "model": "Rapid", "year": 2020,
         "transmission": "automatic", "plate": "А 123 АА 777"},
        {"id": 12, "brand": "Kia", "model": "Rio", "year": 2022,
         "transmission": "manual", "plate": "В 456 ВВ 777"},
    ]
    deny_posts: list = []
    accept_posts: list = []

    def _requests(req):
        return 200, {"ok": True,
                     "requests": [dict(r) for r in reqs]}

    _route_json(page, server, "/api/auth/me", lambda req: (
        200, {"ok": True, "user": {"surname": "Самойлов", "name": "Михаил"}}))
    _route_json(page, server, "/api/instructor/dashboard", lambda req: (
        200, {"ok": True, "instructor": {"surname": "Самойлов",
                                         "name": "Михаил"}}))
    _route_json(page, server, "/api/instructor/summary", lambda req: (
        200, {"ok": True, "students": [], "today_lessons": []}))
    _route_json(page, server, "/api/instructor/requests", _requests)
    _route_json(page, server, "/api/instructor/cars", lambda req: (
        200, {"ok": True, "cars": cars}))
    _route_json(page, server, "/api/instructor/requests/301/deny",
                lambda req: (
                    reqs[0].__setitem__(
                        "status", "denied") or (200, {"ok": True})),
                method="POST", capture=deny_posts)
    _route_json(page, server, "/api/instructor/requests/302/accept",
                lambda req: (
                    reqs[1].__setitem__(
                        "status", "accepted") or (200, {"ok": True})),
                method="POST", capture=accept_posts)

    page.goto(f"{server}/instructor/dashboard")
    expect(page.locator(".user b")).to_have_text("Самойлов Михаил")
    page.locator('.nav button[data-tab="Запросы учеников"]').click()
    expect(page.locator(".rq")).to_have_count(2)
    expect(page.locator(".rq-top b").first).to_have_text("Павел Ежов")

    # --- отказ: кнопка заблокирована до непустого комментария (FR-38) ---
    page.locator("[data-denypanel='301']").click()
    deny_btn = page.locator("[data-deny='301']")
    expect(deny_btn).to_be_disabled()
    page.fill("#rq-ta-301", " ")  # только пробел — всё еще блокировано
    expect(deny_btn).to_be_disabled()
    page.fill("#rq-ta-301", "Не совпадают графики занятий")
    expect(deny_btn).to_be_enabled()
    deny_btn.click()
    assert len(deny_posts) == 1
    assert json.loads(deny_posts[0].post_data) == {
        "comment": "Не совпадают графики занятий"}

    # --- принятие: выбор авто -> POST accept с car_id (FR-39) ---
    page.locator("[data-accept='302']").click()
    panel = page.locator("#rq-accept-302")
    expect(panel).to_be_visible()
    expect(page.locator("input[name='car-302']")).to_have_count(2)
    # по умолчанию выбран первый автомобиль; переключим на второй
    page.locator("input[name='car-302'][value='12']").check()
    page.locator("[data-confirm='302']").click()
    assert len(accept_posts) == 1
    assert json.loads(accept_posts[0].post_data) == {"car_id": 12}
    # статус отрисован: заявка 302 — «Принята»
    expect(page.locator(".rq", has_text="Ольга Нечаева")
           .locator(".rq-status")).to_have_text("Принята")


def test_instructor_accept_flow_real_backend(page, server):
    """Интеграционный e2e на РЕАЛЬНОМ бэкенде, без page.route
    (review-001 #2/#4/#5): подача заявки учеником → кабинет инструктора
    показывает заявку с реальным ФИО/стажем → accept с выбором авто →
    виджет «Привязанные ученики» показывает full_name/car/decided_at;
    статус ученика отражается в /api/student/requests."""
    # --- подготовка через API: инструктор (apply → approve → login) + авто
    email, password = unique_email("flowinstr"), "Dr1vePass!"
    status, data = api("POST", "/api/instructors/apply", base=server, body={
        "surname": "Громов", "name": "Борис", "patronymic": "Арсеньевич",
        "phone": "+7 902 333-44-55", "email": email,
        "address": "г. Москва, ул. Летняя, д. 5", "work_format": "school",
        "license_number": "9987654321", "license_category": "B",
        "experience_years": 9,
        "password": password, "password_confirm": password, "consent": True,
    })
    assert status == 200 and data and data["ok"], (status, data)
    admin_token = admin_login(server)
    status, listing = api("GET", "/api/admin/instructor-applications",
                          base=server, admin_token=admin_token)
    app_id = next(a["id"] for a in listing["applications"]
                  if a["email"] == email)
    status, data = api(
        "POST", f"/api/admin/instructor-applications/{app_id}/approve",
        base=server, admin_token=admin_token)
    assert status == 200 and data and data["ok"], (status, data)
    instructor_id = data["user_id"]
    status, data = api("POST", "/api/auth/login", base=server, body={
        "email": email, "password": password})
    assert status == 200, (status, data)
    instr_token = data["token"]

    status, car = api("POST", "/api/instructor/cars", base=server, token=instr_token,
                      body={"brand": "Škoda", "model": "Rapid", "year": 2020,
                            "plate": "А123АА777", "transmission": "automatic"})
    assert status == 200 and car and car["ok"], (status, car)
    car_id = car["car_id"]

    # --- ученик: регистрация + подача заявки через API
    stu_email = unique_email("flowstu")
    status, data = api("POST", "/api/register", base=server, body={
        "surname": "Смирнова", "name": "Ольга", "patronymic": "Павловна",
        "email": stu_email, "phone": "+7 901 222-33-44",
        "password": "S3cretPass!", "password_confirm": "S3cretPass!",
    })
    assert status == 200 and data and data["ok"], (status, data)
    status, data = api("POST", "/api/auth/login", base=server, body={
        "email": stu_email, "password": "S3cretPass!"})
    stu_token = data["token"]
    status, data = api("POST", "/api/student/requests", base=server,
                       token=stu_token, body={"instructor_id": instructor_id})
    assert status == 200 and data and data["ok"], (status, data)

    # заявка видна инструктору с РЕАЛЬНЫМ контрактом (стаж в ответе — FR-37)
    status, data = api("GET", "/api/instructor/requests", base=server,
                       token=instr_token)
    assert status == 200, (status, data)
    req = data["requests"][0]
    request_id = req["id"]
    assert req["student_full_name"] == "Смирнова Ольга Павловна"
    assert req["student_experience_years"] == 0
    assert req["car"] is None

    # --- UI: вход инструктора → кабинет
    page.goto(f"{server}/")
    page.locator('.auth [data-open="login"]').click()
    page.fill("#login-email", email)
    page.fill("#login-password", password)
    page.locator("#login-submit").click()
    page.wait_for_url("**/instructor/dashboard")
    expect(page.locator(".user b")).to_have_text("Громов Борис Арсеньевич")

    # до принятия виджет «Привязанные ученики» пуст
    expect(page.locator("#w-students-n")).to_have_text("0")

    # раздел «Запросы учеников»: заявка с реальным ФИО и стажем «нет»
    page.locator('.nav button[data-tab="Запросы учеников"]').click()
    expect(page.locator(".rq")).to_have_count(1)
    expect(page.locator(".rq-top b")).to_have_text("Смирнова Ольга Павловна")
    expect(page.locator(".rq-top small")).to_contain_text("Стаж вождения: нет")

    # accept с выбором авто сквозняком
    page.locator(f"[data-accept='{request_id}']").click()
    panel = page.locator(f"#rq-accept-{request_id}")
    expect(panel).to_be_visible()
    expect(page.locator(f"input[name='car-{request_id}']")).to_have_count(1)
    page.locator(f"[data-confirm='{request_id}']").click()
    expect(page.locator(".rq-status").first).to_have_text("Принята")

    # виджет «Привязанные ученики» обновился без перезагрузки:
    # full_name + car (review-001 #4 — фронт читает full_name/decided_at)
    expect(page.locator("#w-students-n")).to_have_text("1")
    expect(page.locator("#w-students-list .w-stu b")).to_have_text(
        "Смирнова Ольга Павловна")
    expect(page.locator("#w-students-list .w-stu .car")).to_have_text(
        "Škoda Rapid 2020")

    # бэкенд: ученик видит accepted + авто в «Моих заявках» (FR-38)
    status, data = api("GET", "/api/student/requests", base=server,
                       token=stu_token)
    mine = data["requests"][0]
    assert mine["status"] == "accepted" and mine["car"]["id"] == car_id, mine
    assert mine["car"]["brand"] == "Škoda" and mine["car"]["model"] == "Rapid"


def test_student_choice_xss_instructor_name_not_executed(page, server):
    """Регресс stored XSS (review-001 #1): инструктор с payload в ФИО
    (свободный текст анкеты → users при approve) не исполняется в сессии
    ученика: карточка строится через createElement/textContent, payload
    виден как текст, window.__xss не определен, img-элементов нет."""
    payload = "<img src=x onerror=window.__xss=1>"
    email, password = unique_email("xssinstr"), "Dr1vePass!"
    status, data = api("POST", "/api/instructors/apply", base=server, body={
        "surname": payload, "name": "Пейлоад", "patronymic": "Оттовна",
        "phone": "+7 904 555-66-77", "email": email,
        "address": "г. Тест, ул. Хакерская, 1", "work_format": "school",
        "license_number": "9911223344", "license_category": "B",
        "experience_years": 3,
        "password": password, "password_confirm": password, "consent": True,
    })
    assert status == 200 and data and data["ok"], (status, data)
    admin_token = admin_login(server)
    status, listing = api("GET", "/api/admin/instructor-applications",
                          base=server, admin_token=admin_token)
    app_id = next(a["id"] for a in listing["applications"]
                  if a["email"] == email)
    status, data = api(
        "POST", f"/api/admin/instructor-applications/{app_id}/approve",
        base=server, admin_token=admin_token)
    assert status == 200 and data and data["ok"], (status, data)

    # ученик входит и открывает каталог (реальный бэкенд, реальная страница)
    stu_email = unique_email("xssstu")
    status, data = api("POST", "/api/register", base=server, body={
        "surname": "Иванов", "name": "Иван", "patronymic": "Иванович",
        "email": stu_email, "phone": "+7 905 888-99-00",
        "password": "S3cretPass!", "password_confirm": "S3cretPass!",
    })
    assert status == 200 and data and data["ok"], (status, data)
    page.goto(f"{server}/")
    page.locator('.auth [data-open="login"]').click()
    page.fill("#login-email", stu_email)
    page.fill("#login-password", "S3cretPass!")
    page.locator("#login-submit").click()
    page.wait_for_url("**/cabinet")

    page.goto(f"{server}/instructor-choice")
    # каталог общий на всю тестовую сессию (server session-scoped) —
    # привязываемся к карточке с payload, а не к общему числу карточек
    payload_card = page.locator(".card", has_text=payload)
    expect(payload_card).to_have_count(1)
    # payload НЕ исполнен: img не вставлен, глобальной переменной нет
    assert page.locator(".cards img").count() == 0
    assert page.evaluate("window.__xss === undefined")
    # payload отображается как текст (textContent)
    expect(payload_card.locator("b").first).to_have_text(
        f"{payload} Пейлоад Оттовна")


def test_instructor_logout_redirects_to_instructors(page, server):
    """TC-UI-010 (change add-instructor-student-loop): выход из кабинета
    инструктора — POST /api/auth/logout, затем редирект на /instructors
    (долг из review-001: не на главную, а на лендинг инструкторов)."""
    _seed_session(page, "session_token", INSTRUCTOR_TOKEN)

    logout_posts: list = []
    _route_json(page, server, "/api/auth/me", lambda req: (
        200, {"ok": True, "user": {"surname": "Самойлов", "name": "Михаил"}}))
    _route_json(page, server, "/api/instructor/dashboard", lambda req: (
        200, {"ok": True, "instructor": {"surname": "Самойлов",
                                         "name": "Михаил"}}))
    _route_json(page, server, "/api/auth/logout", lambda req: (
        200, {"ok": True}), method="POST", capture=logout_posts)

    page.goto(f"{server}/instructor/dashboard")
    expect(page.locator(".user b")).to_have_text("Самойлов Михаил")

    page.locator(".icon-btn[title='Выйти']").click()
    page.wait_for_url("**/instructors")

    # лендинг инструкторов действительно загрузился
    expect(page.locator(".brand em")).to_have_text("Сбер")
    # сессия очищена, logout вызван ровно один раз
    token_left = page.evaluate("sessionStorage.getItem('session_token')")
    assert token_left is None, "sessionStorage не очищен после выхода"
    assert len(logout_posts) == 1


def test_admin_row_click_opens_card_and_loads_license_image(page, server):
    """TC-UI-011 (change add-instructor-student-loop): админка — клик по строке
    заявки открывает карточку инструктора (модально, мокап
    instructor-card-admin); изображение ВУ загружается только с X-Admin-Token
    (FR-24/FR-25); у заявки без ВУ — пустое состояние без «битой» картинки.
    API замокан через page.route."""
    _seed_session(page, "admin_token", ADMIN_TOKEN)

    image_reqs: list = []
    apps = [
        {"id": 1041, "surname": "Самойлов", "name": "Михаил",
         "patronymic": "Петрович", "phone": "+7 912 445-19-08",
         "email": "samoilov@example.com", "experience": 11,
         "car_info": "Škoda Rapid · 2020 · автомат", "status": "waiting",
         "review_comment": None, "license_photo_path": "license/ab.jpg"},
        {"id": 1040, "surname": "Белов", "name": "Артём",
         "patronymic": "Дмитриевич", "phone": "+7 903 208-77-41",
         "email": "belov@example.com", "experience": 1,
         "car_info": "Lada Granta · 2021 · механика", "status": "waiting",
         "review_comment": None, "license_photo_path": None},
    ]

    _route_json(page, server, "/api/admin/users", lambda req: (
        200, {"users": [], "count": 0}))
    _route_json(page, server, "/api/admin/instructor-applications",
                lambda req: (200, {"applications": apps, "count": len(apps)}))
    _route_json(page, server, "/api/admin/instructor-applications/1041",
                lambda req: (
                    assert_admin_token(req) or (200, {"ok": True,
                                                      "application": apps[0]})))
    _route_json(page, server, "/api/admin/instructor-applications/1040",
                lambda req: (200, {"ok": True, "application": apps[1]}))

    def _png(route):
        req = route.request
        image_reqs.append(req)
        route.fulfill(status=200, content_type="image/png", body=PNG_1PX)

    page.route(f"{server}/api/admin/instructor-applications/1041/license-image",
               _png)

    page.goto(f"{server}/admin-dashboard")
    # раздел «Заявки инструкторов» -> таблица заявок
    page.locator(".nav button", has_text="Заявки инструкторов").click()
    expect(page.locator("#app-rows tr")).to_have_count(2)

    # клик по строке заявки с ВУ -> карточка, изображение с админ-токеном
    page.locator("#app-rows tr", has_text="Самойлов").click()
    expect(page.locator("#ic-backdrop")).to_be_visible()
    expect(page.locator("#ic-name")).to_have_text("Самойлов Михаил Петрович")
    expect(page.locator("#ic-last")).to_have_text("Самойлов")
    expect(page.locator("#ic-exp")).to_have_text("11")
    expect(page.locator("#ic-license img")).to_be_visible()
    assert len(image_reqs) == 1
    assert image_reqs[0].headers.get("x-admin-token") == ADMIN_TOKEN, \
        "изображение ВУ запрошено без X-Admin-Token"

    # закрытие -> карточка заявки БЕЗ ВУ: пустое состояние, картинки нет
    page.locator("#ic-close").click()
    expect(page.locator("#ic-backdrop")).to_be_hidden()
    page.locator("#app-rows tr", has_text="Белов").click()
    expect(page.locator("#ic-backdrop")).to_be_visible()
    expect(page.locator("#ic-license")).to_contain_text("Файл ВУ не приложен")
    assert page.locator("#ic-license img").count() == 0
    assert len(image_reqs) == 1  # повторного запроса изображения не было


def assert_admin_token(req):
    """Заглушка-гард: карточка заявки запрашивается только с X-Admin-Token."""
    assert req.headers.get("x-admin-token") == ADMIN_TOKEN
    return None


# =========================================================================
# Спринт 4, Партия A (change add-s3-frontend-links): ИНТЕГРАЦИОННЫЕ e2e
# на ЖИВОМ бэкенде (фикстура server, без page.route) — UI-связки над
# готовым Спринтом 3: /my-cars, /review, /my-requests.
# =========================================================================

def _approve_instructor(server, surname="Громов", name="Борис",
                        patronymic="Арсеньевич"):
    """Реальный флоу инструктора: apply → approve → login.
    Возвращает (token, instructor_id)."""
    email, password = unique_email("s4instr"), "Dr1vePass!"
    status, data = api("POST", "/api/instructors/apply", base=server, body={
        "surname": surname, "name": name, "patronymic": patronymic,
        "phone": "+7 902 333-44-55", "email": email,
        "address": "г. Москва, ул. Летняя, д. 5", "work_format": "school",
        "license_number": "9987654321", "license_category": "B",
        "experience_years": 9,
        "password": password, "password_confirm": password, "consent": True,
    })
    assert status == 200 and data and data["ok"], (status, data)
    admin_token = admin_login(server)
    status, listing = api("GET", "/api/admin/instructor-applications",
                          base=server, admin_token=admin_token)
    app_id = next(a["id"] for a in listing["applications"]
                  if a["email"] == email)
    status, data = api(
        "POST", f"/api/admin/instructor-applications/{app_id}/approve",
        base=server, admin_token=admin_token)
    assert status == 200 and data and data["ok"], (status, data)
    instructor_id = data["user_id"]
    status, data = api("POST", "/api/auth/login", base=server, body={
        "email": email, "password": password})
    assert status == 200 and data and data.get("token"), (status, data)
    return data["token"], instructor_id


def _student_token(server):
    """Регистрация + вход ученика; возвращает токен сессии."""
    email = unique_email("s4stu")
    status, data = api("POST", "/api/register", base=server, body={
        "surname": "Смирнова", "name": "Ольга", "patronymic": "Павловна",
        "email": email, "phone": "+7 901 222-33-44",
        "password": "S3cretPass!", "password_confirm": "S3cretPass!",
    })
    assert status == 200 and data and data["ok"], (status, data)
    status, data = api("POST", "/api/auth/login", base=server, body={
        "email": email, "password": "S3cretPass!"})
    assert status == 200 and data and data.get("token"), (status, data)
    return data["token"]


def _add_car(server, token, plate="А123АА777"):
    status, data = api("POST", "/api/instructor/cars", base=server,
                       token=token,
                       body={"brand": "Škoda", "model": "Rapid", "year": 2020,
                             "plate": plate, "transmission": "automatic"})
    assert status == 200 and data and data["ok"], (status, data)
    return data["car_id"]


def _accepted_request(server, instructor_token, instructor_id, car_id):
    """Ученик подает заявку, инструктор принимает; возвращает токен ученика."""
    stu_token = _student_token(server)
    status, data = api("POST", "/api/student/requests", base=server,
                       token=stu_token, body={"instructor_id": instructor_id})
    assert status == 200 and data and data["ok"], (status, data)
    status, data = api("GET", "/api/instructor/requests", base=server,
                       token=instructor_token)
    request_id = data["requests"][0]["id"]
    status, data = api(
        "POST", f"/api/instructor/requests/{request_id}/accept",
        base=server, token=instructor_token, body={"car_id": car_id})
    assert status == 200 and data and data["ok"], (status, data)
    return stu_token


def test_s4_my_cars_add_edit_delete_car(page, server):
    """TC-UI-015 (change add-s3-frontend-links): «Мои автомобили» на живом
    бэкенде — добавил авто → виден в списке (карточка + GET API); PATCH
    редактирование отражается; удаление с подтверждением (отмена работает,
    подтверждение удаляет) → в списке и API авто больше нет."""
    token, _ = _approve_instructor(server)
    _seed_session(page, "session_token", token)

    page.goto(f"{server}/my-cars")
    expect(page.locator("h1")).to_have_text("Мои автомобили")
    expect(page.locator("#empty")).to_be_visible()
    expect(page.locator("#count")).to_have_text("Автомобилей: 0")

    # --- добавление: модалка → POST /api/instructor/cars ---
    page.locator("#open-add").click()
    expect(page.locator("#m-add")).to_be_visible()
    expect(page.locator("#save-car")).to_be_disabled()
    page.fill("#f-brand", "Škoda")
    page.fill("#f-model", "Rapid")
    page.fill("#f-year", "2020")
    page.fill("#f-plate", "А123АА777")
    page.locator("#f-trans button[data-v='automatic']").click()
    expect(page.locator("#save-car")).to_be_enabled()
    page.locator("#save-car").click()

    # карточка появилась (пустое состояние ушло)
    card = page.locator(".car")
    expect(card).to_have_count(1)
    expect(card.locator("b.title")).to_have_text("Škoda Rapid")
    expect(card.locator(".pill.plate")).to_have_text("А123АА777")
    expect(card.locator(".pill.green")).to_have_text("автомат")
    expect(page.locator("#empty")).to_be_hidden()
    expect(page.locator("#count")).to_have_text("Автомобилей: 1")

    # бэкенд: авто реально создан
    status, data = api("GET", "/api/instructor/cars", base=server, token=token)
    assert status == 200 and len(data["cars"]) == 1, (status, data)
    assert data["cars"][0]["brand"] == "Škoda"
    assert data["cars"][0]["transmission"] == "automatic"
    assert data["cars"][0]["has_photo"] is False
    car_id = data["cars"][0]["id"]

    # --- редактирование: PATCH /api/instructor/cars/{id} ---
    card.locator(".edit").click()
    expect(page.locator("#add-title")).to_have_text("Редактирование автомобиля")
    expect(page.locator("#f-brand")).to_have_value("Škoda")
    page.fill("#f-plate", "В456ВВ777")
    page.locator("#save-car").click()
    expect(card.locator(".pill.plate")).to_have_text("В456ВВ777")
    status, data = api("GET", "/api/instructor/cars", base=server, token=token)
    assert data["cars"][0]["plate"] == "В456ВВ777"

    # --- удаление с подтверждением: отмена → авто на месте ---
    card.locator(".del").click()
    expect(page.locator("#m-del")).to_be_visible()
    expect(page.locator("#del-what")).to_have_text("Škoda Rapid · В456ВВ777")
    page.locator("#del-cancel").click()
    expect(page.locator("#m-del")).to_be_hidden()
    expect(page.locator(".car")).to_have_count(1)

    # --- подтверждение → DELETE, авто исчезает из UI и API ---
    card.locator(".del").click()
    page.locator("#del-confirm").click()
    expect(page.locator(".car")).to_have_count(0)
    expect(page.locator("#empty")).to_be_visible()
    expect(page.locator("#count")).to_have_text("Автомобилей: 0")
    status, data = api("GET", "/api/instructor/cars", base=server, token=token)
    assert status == 200 and data["cars"] == [], (status, data)
    # чужой/несуществующий id больше не отвечает 200 (удаление прошло)
    status, _ = api("DELETE", f"/api/instructor/cars/{car_id}", base=server,
                    token=token)
    assert status == 404, status


def test_s4_my_cars_photo_upload_progress_and_preview(page, server, tmp_path):
    """TC-UI-016 (change add-s3-frontend-links): «Мои автомобили» — загрузка
    фото (POST /api/instructor/cars/{id}/photo, multipart): прогресс в
    модалке, превью-картинка на карточке после сохранения, has_photo=true
    и выдача фото только по сессии владельца (GET …/photo)."""
    token, _ = _approve_instructor(server)
    car_id = _add_car(server, token)
    _seed_session(page, "session_token", token)

    page.goto(f"{server}/my-cars")
    card = page.locator(".car")
    expect(card).to_have_count(1)
    # плейсхолдер до загрузки
    expect(card.locator(".photo")).to_contain_text("Плейсхолдер фото авто")
    assert card.locator(".photo img").count() == 0

    # выбираем файл в модалке и сохраняем
    png_file = tmp_path / "car-photo.png"
    png_file.write_bytes(PNG_1PX)
    card.locator(".edit").click()
    expect(page.locator("#m-add")).to_be_visible()
    page.locator("#f-photo").set_input_files(str(png_file))
    expect(page.locator("#up-lab")).to_contain_text("Файл выбран")
    page.locator("#save-car").click()

    # карточка перерисовалась: превью-картинка вместо плейсхолдера
    expect(card.locator(".photo img")).to_be_visible()

    # бэкенд: has_photo=true; фото отдается владельцу по сессии (image/png)
    status, data = api("GET", "/api/instructor/cars", base=server, token=token)
    assert data["cars"][0]["has_photo"] is True, data
    req = urllib.request.Request(
        f"{server}/api/instructor/cars/{car_id}/photo",
        headers={"X-Session-Token": token})
    with urllib.request.urlopen(req, timeout=10) as resp:
        assert resp.status == 200
        assert resp.headers["Content-Type"] == "image/png"
        assert resp.read() == PNG_1PX


def test_s4_review_submit_then_repeat_blocked_409(page, server):
    """TC-UI-017 (change add-s3-frontend-links): поток «принял заявку ученика →
    оставил отзыв → отзыв виден/повтор 409-блок» на живом бэкенде: контекст
    инструктора на /review, сабмит 200 → состояние «отправлен»; повторный
    сабмит через UI → 409 → состояние «уже оставлен»; прямой повторный
    POST в API → 409 (NFR-5)."""
    instructor_token, instructor_id = _approve_instructor(server)
    car_id = _add_car(server, instructor_token)
    stu_token = _accepted_request(server, instructor_token, instructor_id,
                                  car_id)
    _seed_session(page, "session_token", stu_token)

    page.goto(f"{server}/review?instructor={instructor_id}")

    # контекст: карточка инструктора с реальным ФИО из API
    expect(page.locator("#i-name")).to_have_text("Громов Борис Арсеньевич")
    expect(page.locator("#view-form")).to_be_visible()
    expect(page.locator("#send")).to_be_disabled()

    # валидация: звезда без текста — кнопка все еще заблокирована
    page.locator(".star[data-v='5']").click()
    expect(page.locator("#send")).to_be_disabled()
    page.fill("#review-text", "Спокойный инструктор, объясняет до полного понимания. Первые манёвры уже уверенно!")
    expect(page.locator("#send")).to_be_enabled()
    page.locator("#send").click()

    # 200 → состояние «отправлен», форма скрыта
    expect(page.locator("#view-done")).to_be_visible()
    expect(page.locator("#done-title")).to_have_text("Отзыв отправлен")
    expect(page.locator("#view-form")).to_be_hidden()

    # отзыв виден в агрегате карточки инструктора (FR-35)
    status, data = api("GET", f"/api/student/instructors/{instructor_id}",
                       base=server, token=stu_token)
    assert data["instructor"]["rating"]["count"] == 1, data
    assert abs(data["instructor"]["rating"]["average"] - 5.0) < 1e-9

    # повторный сабмит через UI → сервер 409 → состояние «уже оставлен»
    page.reload()
    expect(page.locator("#view-form")).to_be_visible()
    page.locator(".star[data-v='4']").click()
    page.fill("#review-text", "Попытка второго отзыва")
    page.locator("#send").click()
    expect(page.locator("#view-done")).to_be_visible()
    expect(page.locator("#done-title")).to_have_text("Отзыв уже отправлен")

    # прямой повторный POST мимо UI → 409 (UNIQUE пара, NFR-5)
    status, data = api(
        "POST", f"/api/student/instructors/{instructor_id}/reviews",
        base=server, token=stu_token,
        body={"rating": 4, "text": "еще одна попытка"})
    assert status == 409 and data and data["ok"] is False, (status, data)


def test_s4_my_requests_badges_deny_comment_retry_and_review_link(
        page, server):
    """TC-UI-018 (change add-s3-frontend-links): поток «подал заявку → статус
    в моих заявках» на живом бэкенде: желтый бейдж «На рассмотрении»; после
    отказа — красный «Отказана» с видимым комментарием инструктора;
    «Повторить заявку» (ОВ-2) снова создает активную заявку; после принятия —
    зеленая «Принята», авто занятий и переход на форму отзыва."""
    instructor_token, instructor_id = _approve_instructor(
        server, surname="Самойлов", name="Михаил", patronymic="Петрович")
    car_id = _add_car(server, instructor_token)
    stu_token = _student_token(server)
    status, data = api("POST", "/api/student/requests", base=server,
                       token=stu_token, body={"instructor_id": instructor_id})
    assert status == 200 and data and data["ok"], (status, data)
    _seed_session(page, "session_token", stu_token)

    page.goto(f"{server}/my-requests")
    expect(page.locator("h1")).to_have_text("Заявки инструкторам")
    req = page.locator(".req")
    expect(req).to_have_count(1)
    expect(page.locator(".uname")).to_have_text("Смирнова Ольга Павловна")

    # новая заявка: желтый бейдж «На рассмотрении» (#332a14)
    badge = req.locator(".status")
    expect(badge).to_have_text("На рассмотрении")
    assert badge.evaluate(
        "el => getComputedStyle(el).backgroundColor") == "rgb(51, 42, 20)"
    assert "Автомобиль занятий" not in req.inner_text()

    # инструктор отказывает с комментарием → красный бейдж + комментарий виден
    status, data = api("GET", "/api/instructor/requests", base=server,
                       token=instructor_token)
    request_id = data["requests"][0]["id"]
    status, data = api(
        "POST", f"/api/instructor/requests/{request_id}/deny",
        base=server, token=instructor_token,
        body={"comment": "Извините, группа на этот сезон уже набрана. Напишите в следующем наборе — буду рада!"})
    assert status == 200 and data and data["ok"], (status, data)

    page.reload()
    req = page.locator(".req")
    expect(req.locator(".status")).to_have_text("Отказана")
    comment = req.locator(".comment")
    expect(comment).to_be_visible()
    expect(comment).to_contain_text(
        "Извините, группа на этот сезон уже набрана")
    expect(comment.locator("span")).to_have_text("Комментарий инструктора")

    # «Повторить заявку» (ОВ-2): POST создает НОВУЮ активную заявку,
    # старая отказанная остается в списке
    retry = req.locator(".act.retry")
    expect(retry).to_be_visible()
    retry.click()
    expect(page.locator(".req")).to_have_count(2)
    expect(page.locator(".req .status").first).to_have_text("На рассмотрении")
    expect(page.locator(".req .status").nth(1)).to_have_text("Отказана")

    # инструктор принимает (новую) заявку с авто → зеленый бейдж, авто
    # занятий, ссылка на отзыв
    status, data = api("GET", "/api/instructor/requests", base=server,
                       token=instructor_token)
    request_id = data["requests"][0]["id"]
    status, data = api(
        "POST", f"/api/instructor/requests/{request_id}/accept",
        base=server, token=instructor_token, body={"car_id": car_id})
    assert status == 200 and data and data["ok"], (status, data)

    page.reload()
    req = page.locator(".req").first
    badge = req.locator(".status")
    expect(badge).to_have_text("Принята")
    assert badge.evaluate(
        "el => getComputedStyle(el).backgroundColor") == "rgb(20, 51, 34)"
    expect(req.locator(".pill.car")).to_have_text("🚗 Škoda Rapid 2020 · автомат")

    # переход из «Моих заявок» у принятой заявки → форма отзыва
    review_btn = req.locator(".act.review")
    expect(review_btn).to_be_visible()
    review_btn.click()
    page.wait_for_url(f"**/review?instructor={instructor_id}")
    expect(page.locator("#i-name")).to_have_text("Самойлов Михаил Петрович")

    # бэкенд-срез: статус и авто в контракте GET /api/student/requests
    status, data = api("GET", "/api/student/requests", base=server,
                       token=stu_token)
    mine = data["requests"][0]
    assert mine["status"] == "accepted" and mine["car"]["id"] == car_id, mine
    # комментарий отказа остался виден у старой отказанной заявки
    assert "группа на этот сезон" in (data["requests"][1]["deny_comment"] or "")
