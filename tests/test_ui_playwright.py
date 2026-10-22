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
from html.parser import HTMLParser
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


def api_multipart(path, *, base, fields, files=None, token=None):
    """multipart/form-data POST (urllib, BUG-048): fields — текстовые поля,
    files — {name: (filename, bytes, content_type)}. Возвращает (status, dict).
    Заявка инструктора с файлом ВУ — так ее отправляет фронт (FormData).
    token — X-Session-Token (создание авто с СТС, Спринт 5)."""
    boundary = "----uitest" + uuid.uuid4().hex
    body = bytearray()
    for key, value in fields.items():
        body += (
            f"--{boundary}\r\nContent-Disposition: form-data; "
            f"name=\"{key}\"\r\n\r\n{value}\r\n").encode("utf-8")
    for key, (fname, data, ctype) in (files or {}).items():
        body += (
            f"--{boundary}\r\nContent-Disposition: form-data; "
            f"name=\"{key}\"; filename=\"{fname}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n").encode("utf-8")
        body += data + b"\r\n"
    body += f"--{boundary}--\r\n".encode("utf-8")
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    if token:
        headers["X-Session-Token"] = token
    req = urllib.request.Request(base + path, data=bytes(body), method="POST",
                                 headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:  # контрактные 4xx/5xx
        raw = exc.read()
        return exc.code, (json.loads(raw) if raw else None)


def _raw_get(url: str, *, token: str | None = None,
             admin_token: str | None = None):
    """GET бинарного ответа (фото/СТС/документы): (status, headers, body)."""
    headers = {}
    if token:
        headers["X-Session-Token"] = token
    if admin_token:
        headers["X-Admin-Token"] = admin_token
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.headers, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers, exc.read()


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


def test_back_links_lead_to_role_home(page, server):
    """TC-UI-019 (BUG-047; change add-booking-docs): после встраивания разделов
    в кабинеты — у дашборда инструктора есть разделы «Мои автомобили»,
    «Мои документы», «Бронирования», у кабинета ученика — «Мои заявки» и
    «Мои брони»; standalone-страницы разделов запрещены (директива Заказчика,
    BUG-047-прецедент): my-cars/my-requests удалены, новые страницы Спринта 5
    (documents/booking/instructor-bookings/admin-cars) НЕ создаются;
    целевые страницы (выбор инструктора, форма отзыва) ведут назад в кабинет
    ученика (у отзыва — кнопкой «Назад к заявкам» в форме)."""
    # страницы защищены сессией — проверяем навигацию в разметке (файлы страницы)
    import pathlib
    base = pathlib.Path(__file__).parent.parent / "frontend"
    for standalone in (
        "my-cars.html", "my-requests.html",
        # Спринт 5: разделы ВНУТРИ кабинетов — новых страниц не заводить
        "documents.html", "booking.html", "instructor-bookings.html",
        "admin-cars.html",
    ):
        assert not (base / standalone).exists(), \
            f"BUG-047-прецедент: {standalone} запрещен — раздел внутри кабинета"
    dash = (base / "instructor-dashboard.html").read_text(encoding="utf-8")
    cab = (base / "cabinet.html").read_text(encoding="utf-8")
    assert 'data-tab="Мои автомобили"' in dash, "нет раздела «Мои автомобили» в дашборде"
    assert 'data-tab="Мои документы"' in dash, "нет раздела «Мои документы» в дашборде"
    assert 'data-tab="Бронирования"' in dash, "нет раздела «Бронирования» в дашборде"
    assert 'id="sec-docs"' in dash and 'id="sec-bookings"' in dash, \
        "секции «Мои документы»/«Бронирования» должны быть внутри дашборда"
    assert 'data-tab="Мои заявки"' in cab, "нет раздела «Мои заявки» в кабинете"
    assert 'data-tab="Мои брони"' in cab, "нет раздела «Мои брони» в кабинете"
    assert 'id="sec-bookings"' in cab, "секция «Мои брони» должна быть внутри кабинета"
    choice = (base / "instructor-choice.html").read_text(encoding="utf-8")
    assert 'href="/cabinet"' in choice, "instructor-choice: нет возврата в /cabinet"
    review = (base / "review-form.html").read_text(encoding="utf-8")
    assert 'href="/my-requests"' in review, \
        "review-form: нет кнопки «Назад к заявкам» (/my-requests → 301 в кабинет)"


def test_bug047_mycars_route_redirects_into_dashboard(page, server):
    """BUG-047: /my-cars больше не отдает standalone-страницу — 301 на
    /instructor/dashboard#/my-cars; хеш открывает раздел, сайдбар на месте,
    активный пункт подсвечен."""
    _seed_session(page, "session_token", INSTRUCTOR_TOKEN)
    _route_json(page, server, "/api/auth/me", lambda req: (
        200, {"ok": True, "user": {"surname": "Громов", "name": "Борис"}}))
    _route_json(page, server, "/api/instructor/dashboard", lambda req: (
        200, {"ok": True, "instructor": {"surname": "Громов", "name": "Борис"}}))
    _route_json(page, server, "/api/instructor/cars", lambda req: (
        200, {"ok": True, "cars": []}))

    page.goto(f"{server}/my-cars")
    page.wait_for_url("**/instructor/dashboard#/my-cars")
    expect(page.locator(".sidebar")).to_be_visible()
    expect(page.locator("#sec-cars")).to_be_visible()
    expect(page.locator('.nav button[data-tab="Мои автомобили"]')).to_have_class("active")
    expect(page.locator("#page-title")).to_have_text("Мои автомобили")


def test_bug047_myrequests_route_redirects_into_cabinet(page, server):
    """BUG-047: /my-requests больше не отдает standalone-страницу — 301 на
    /cabinet#/my-requests; хеш открывает раздел «Мои заявки» внутри кабинета
    (сайдбар на месте, активный пункт подсвечен, «Главная» скрыта)."""
    stu_token = _student_token(server)
    _seed_session(page, "session_token", stu_token)
    page.goto(f"{server}/my-requests")
    page.wait_for_url("**/cabinet#/my-requests")
    expect(page.locator(".side")).to_be_visible()
    expect(page.locator("#sec-requests")).to_be_visible()
    expect(page.locator('.snav button[data-tab="Мои заявки"]')).to_have_class("on")
    expect(page.locator("#sec-home")).to_be_hidden()
    expect(page.locator("#sec-requests h1")).to_have_text("Заявки инструкторам")


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


def _sts_photo_file() -> tuple:
    """Валидный PNG для multipart-поля sts_photo (контракт Спринта 5)."""
    return ("sts.png", PNG_1PX, "image/png")


def _add_car(server, token, plate="А123АА777"):
    """Создание авто по НОВОМУ контракту (change add-booking-docs): multipart
    с обязательным sts_photo (FR-44). Возвращает car_id."""
    status, data = api_multipart(
        "/api/instructor/cars", base=server,
        fields={"brand": "Škoda", "model": "Rapid", "year": "2020",
                "plate": plate, "transmission": "automatic"},
        files={"sts_photo": _sts_photo_file()}, token=token)
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


def test_s4_my_cars_add_edit_delete_car(page, server, tmp_path):
    """TC-UI-015 (change add-booking-docs; BUG-047): «Мои автомобили» на живом
    бэкенде — раздел ВНУТРИ дашборда (сайдбар на месте, активный пункт
    подсвечен); создание по НОВОМУ контракту — multipart с ОБЯЗАТЕЛЬНЫМ фото
    СТС (кнопка заблокирована без файла; FR-44): добавил авто → карточка с 5
    пустыми слотами ракурсов, слот СТС «has», комплектность «Не хватает:
    …» (ракурсы); PATCH редактирование отражается; удаление с подтверждением
    (отмена работает, подтверждение удаляет) → в списке и API авто больше нет."""
    token, _ = _approve_instructor(server)
    _seed_session(page, "session_token", token)

    page.goto(f"{server}/instructor/dashboard")
    page.locator('.nav button[data-tab="Мои автомобили"]').click()
    # BUG-047: единый лейаут — сайдбар на месте, активный пункт подсвечен,
    # заголовок шапки дашборда переключился на раздел
    expect(page.locator(".sidebar")).to_be_visible()
    expect(page.locator('.nav button[data-tab="Мои автомобили"]')).to_have_class("active")
    expect(page.locator("#page-title")).to_have_text("Мои автомобили")
    expect(page.locator("#sec-cars")).to_be_visible()
    expect(page.locator("#empty")).to_be_visible()
    expect(page.locator("#count")).to_have_text("Автомобилей: 0")

    # --- добавление: модалка → POST /api/instructor/cars (multipart+СТС) ---
    page.locator("#open-add").click()
    expect(page.locator("#m-add")).to_be_visible()
    page.fill("#f-brand", "Škoda")
    page.fill("#f-model", "Rapid")
    page.fill("#f-year", "2020")
    page.fill("#f-plate", "А123АА777")
    page.locator("#f-trans button[data-v='automatic']").click()
    # FR-44: без файла СТС кнопка сохранения заблокирована
    expect(page.locator("#save-car")).to_be_disabled()
    sts_file = tmp_path / "sts.png"
    sts_file.write_bytes(PNG_1PX)
    page.locator("#f-sts").set_input_files(str(sts_file))
    expect(page.locator("#save-car")).to_be_enabled()
    page.locator("#save-car").click()

    # карточка появилась (пустое состояние ушло): 5 пустых слотов ракурсов,
    # СТС «has» (создан с файлом), комплектность — не хватает 5 ракурсов
    card = page.locator(".car")
    expect(card).to_have_count(1)
    expect(card.locator("b.title")).to_have_text("Škoda Rapid")
    expect(card.locator(".pill.plate")).to_have_text("А123АА777")
    expect(card.locator(".pill.green")).to_have_text("автомат")
    expect(card.locator(".slot")).to_have_count(5)
    expect(card.locator(".slot.empty")).to_have_count(5)
    expect(card.locator(".sts-slot")).to_have_class("sts-slot has")
    expect(card.locator(".car-head .status")).to_have_text(
        "Не хватает: спереди, сзади, слева, справа, салон")
    expect(page.locator("#empty")).to_be_hidden()
    expect(page.locator("#count")).to_have_text("Автомобилей: 1")

    # бэкенд: авто реально создан, СТС на месте, ракурсов нет
    status, data = api("GET", "/api/instructor/cars", base=server, token=token)
    assert status == 200 and len(data["cars"]) == 1, (status, data)
    car = data["cars"][0]
    assert car["brand"] == "Škoda"
    assert car["transmission"] == "automatic"
    assert car["has_sts"] is True and car["sts_url"], car
    assert all(url is None for url in car["photos"].values()), car
    assert car["blocked"] is False
    car_id = car["id"]
    status, hdrs, body = _raw_get(f"{server}{car['sts_url']}", token=token)
    assert status == 200 and hdrs["Content-Type"] == "image/png"
    assert body == PNG_1PX

    # --- редактирование: PATCH /api/instructor/cars/{id} (СТС-поле скрыто) ---
    card.locator(".edit").click()
    expect(page.locator("#add-title")).to_have_text("Редактирование автомобиля")
    expect(page.locator("#f-brand")).to_have_value("Škoda")
    expect(page.locator("#sts-field")).to_be_hidden()
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
    """TC-UI-016 (change add-booking-docs): «Мои автомобили» — слоты ракурсов:
    клик по пустому слоту → выбор файла → POST /api/instructor/cars/{id}/
    photo/{angle} → миниатюра в слоте (баг 5.2), комплектность пересчитана;
    на бэкенде photos.front выдан, остальные ракурсы не тронуты (FR-43);
    замена «спереди» не ломает карточку; выдача фото только по сессии."""
    token, _ = _approve_instructor(server)
    car_id = _add_car(server, token)
    _seed_session(page, "session_token", token)

    # BUG-047: раздел открывается хешем старой ссылки — внутри дашборда
    page.goto(f"{server}/instructor/dashboard#/my-cars")
    expect(page.locator("#sec-cars")).to_be_visible()
    card = page.locator(".car")
    expect(card).to_have_count(1)
    # до загрузки: 5 пустых слотов-плейсхолдеров, без «битых» картинок
    expect(card.locator(".slot")).to_have_count(5)
    expect(card.locator(".slot.empty")).to_have_count(5)
    assert card.locator(".slot img").count() == 0

    # клик по слоту «спереди» → выбор файла → загрузка ракурса
    png_file = tmp_path / "front.png"
    png_file.write_bytes(PNG_1PX)
    with page.expect_file_chooser() as fc_info:
        card.locator(".slot[data-angle='front']").click()
    fc_info.value.set_files(str(png_file))

    # слот стал «has» с миниатюрой; комплектность пересчитана (осталось 4)
    front = card.locator(".slot[data-angle='front']")
    expect(front).to_have_class("slot has")
    expect(front.locator("img")).to_be_visible()
    expect(card.locator(".car-head .status")).to_have_text(
        "Не хватает: сзади, слева, справа, салон")
    expect(card.locator(".slot.empty")).to_have_count(4)

    # бэкенд: photos.front выдан владельцу (image/png), остальные — 404
    status, data = api("GET", "/api/instructor/cars", base=server, token=token)
    photos = data["cars"][0]["photos"]
    assert photos["front"] and all(
        photos[a] is None for a in ("rear", "left", "right", "interior")), photos
    status, hdrs, body = _raw_get(f"{server}{photos['front']}", token=token)
    assert status == 200 and hdrs["Content-Type"] == "image/png"
    assert body == PNG_1PX
    for angle in ("rear", "left", "right", "interior"):
        status, _, _ = _raw_get(
            f"{server}/api/instructor/cars/{car_id}/photo/{angle}", token=token)
        assert status == 404, angle

    # замена «спереди»: другой файл — точечная замена, остальные не тронуты
    png2 = tmp_path / "front2.png"
    png2.write_bytes(PNG_1PX + b"\x00" * 16)  # валидный PNG (magic bytes)
    with page.expect_file_chooser() as fc_info:
        front.click()
    fc_info.value.set_files(str(png2))
    expect(card.locator(".slot[data-angle='front'].has img")).to_be_visible()
    expect(card.locator(".slot.empty")).to_have_count(4)
    status, data = api("GET", "/api/instructor/cars", base=server, token=token)
    photos = data["cars"][0]["photos"]
    assert photos["front"], photos
    status, hdrs, body = _raw_get(f"{server}{photos['front']}", token=token)
    assert status == 200 and body == PNG_1PX + b"\x00" * 16

    # просмотр СТС по клику на слот СТС (загружен при создании) — вьюер открыт
    card.locator(".sts-slot").click()
    expect(page.locator("#m-view")).to_be_visible()
    expect(page.locator("#view-title")).to_contain_text("СТС")
    page.locator("#view-close").click()
    expect(page.locator("#m-view")).to_be_hidden()


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

    # /review без ?instructor= → /my-requests → 301 → /cabinet#/my-requests:
    # раздел «Мои заявки» открывается ВНУТРИ кабинета (BUG-047)
    page.goto(f"{server}/review")
    page.wait_for_url("**/cabinet#/my-requests")
    expect(page.locator("#sec-requests")).to_be_visible()
    expect(page.locator("#sec-requests h1")).to_have_text("Заявки инструкторам")

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

    # BUG-047: «Мои заявки» — раздел кабинета ученика (сайдбар на месте,
    # активный пункт подсвечен); reload (ниже) сохраняет раздел через хеш
    page.goto(f"{server}/cabinet#/my-requests")
    expect(page.locator(".side")).to_be_visible()
    expect(page.locator('.snav button[data-tab="Мои заявки"]')).to_have_class("on")
    expect(page.locator("#sec-requests")).to_be_visible()
    expect(page.locator("#sec-requests h1")).to_have_text("Заявки инструкторам")
    req = page.locator(".req")
    expect(req).to_have_count(1)
    expect(page.locator(".uname")).to_have_text("Смирнова Ольга Павловна")

    # новая заявка: желтый бейдж «На рассмотрении» (#332a14)
    badge = req.locator(".status")
    expect(badge).to_have_text("На рассмотрении")
    assert badge.evaluate(
        "el => getComputedStyle(el).backgroundColor") == "rgb(51, 42, 20)"
    assert "Автомобиль занятий" not in req.inner_text()

    # фильтры (F1 review-001): «Отказанные» при единственной новой заявке —
    # пустой результат: empty-блок виден, карточек НЕТ (раньше рендер
    # игнорировал фильтр и показывал полный список вместе с empty)
    page.locator(".filters button[data-f='denied']").click()
    expect(page.locator("#noreq")).to_be_visible()
    expect(page.locator(".req")).to_have_count(0)
    page.locator(".filters button[data-f='all']").click()
    expect(page.locator("#noreq")).to_be_hidden()
    expect(page.locator(".req")).to_have_count(1)

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

    # фильтры (F1 review-001): «Отказанные» → только отказанная заявка,
    # «Принятые» → только принятая, «Все» → полный список
    page.locator(".filters button[data-f='denied']").click()
    expect(page.locator(".req")).to_have_count(1)
    expect(page.locator(".req .status")).to_have_text("Отказана")
    expect(page.locator("#noreq")).to_be_hidden()
    page.locator(".filters button[data-f='accepted']").click()
    expect(page.locator(".req")).to_have_count(1)
    expect(page.locator(".req .status")).to_have_text("Принята")
    page.locator(".filters button[data-f='all']").click()
    expect(page.locator(".req")).to_have_count(2)

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


# =========================================================================
# BUG-048 (Заказчик 2026-10-21): загрузка фото — ВУ при регистрации,
# отображение в админ-карточке, фото автомобилей. Живой бэкенд.
# =========================================================================

def _fill_apply_form(page, email):
    """Заполнение анкеты инструктора валидными данными (без файла ВУ)."""
    page.fill("#surname", "Смирнова")
    page.fill("#name", "Ольга")
    page.fill("#patronymic", "Павловна")
    page.fill("#phone", "+7 901 222-33-44")
    page.fill("#email", email)
    page.fill("#address", "г. Москва, ул. Полярная, д. 3, кв. 12")
    page.fill("#plate", "А123АА 777")  # формат 'own' по умолчанию
    page.fill("#license-number", "9912345678")
    page.select_option("#license-category", "B")
    page.fill("#password", "Dr1vePass!")
    page.fill("#password-confirm", "Dr1vePass!")
    page.locator(".checkline input").check()


def test_bug048_apply_license_thumbnail_and_submit(page, server, tmp_path):
    """TC-UI-020 (change add-instructor-student-loop, BUG-048): анкета
    инструктора — выбор файла ВУ показывает мгновенную миниатюру ВМЕСТО
    области загрузки (иконка/подпись/кнопка скрыты); сабмит (multipart
    FormData с license_photo) → /instructors/pending; на бэкенде заявка
    создана с файлом, изображение выдается админ-эндпоинтом (image/png)."""
    png_file = tmp_path / "license.png"
    png_file.write_bytes(PNG_1PX)
    page.goto(f"{server}/instructors/apply")
    email = unique_email("bug048doc")
    _fill_apply_form(page, email)

    # до выбора файла: область загрузки видна, миниатюры нет
    expect(page.locator(".upload-icon")).to_be_visible()
    expect(page.locator("#license-thumb")).to_be_hidden()

    page.locator("#license-file").set_input_files(str(png_file))
    # миниатюра вместо области загрузки
    expect(page.locator("#license-thumb")).to_be_visible()
    expect(page.locator(".upload-icon")).to_be_hidden()
    expect(page.locator("#pick-file")).to_be_hidden()
    expect(page.locator("#license-error")).to_be_hidden()

    page.locator("#registration button.submit").click()
    page.wait_for_url("**/instructors/pending")

    # бэкенд: заявка с файлом ВУ; изображение — по админ-эндпоинту
    admin_token = admin_login(server)
    status, listing = api("GET", "/api/admin/instructor-applications",
                          base=server, admin_token=admin_token)
    assert status == 200, (status, listing)
    app_row = next(a for a in listing["applications"] if a["email"] == email)
    status, card = api(
        "GET", f"/api/admin/instructor-applications/{app_row['id']}",
        base=server, admin_token=admin_token)
    assert status == 200 and card["application"]["license_photo_path"], card
    req = urllib.request.Request(
        f"{server}/api/admin/instructor-applications/{app_row['id']}/license-image",
        headers={"X-Admin-Token": admin_token})
    with urllib.request.urlopen(req, timeout=10) as resp:
        assert resp.status == 200
        assert resp.headers["Content-Type"] == "image/png"
        assert resp.read() == PNG_1PX


def test_bug048_apply_license_format_error_visible(page, server, tmp_path):
    """TC-UI-021 (change add-instructor-student-loop, BUG-048): ошибки файла
    ВУ видны и блокируют отправку: 1) >5 МБ отсекается на клиенте (красный
    текст у поля, сабмит не уходит); 2) файл .png с не-изображением проходит
    клиент, сервер отвечает 422 (аналог 415 по формату) → текст ошибки виден
    у поля и под формой, заявка не создается."""
    page.goto(f"{server}/instructors/apply")
    email = unique_email("bug048bad")
    _fill_apply_form(page, email)
    err = page.locator("#license-error")

    # 1) >5 МБ — клиентская валидация: красный текст, миниатюры нет
    big = tmp_path / "big.png"
    big.write_bytes(PNG_1PX + b"\x00" * (5 * 1024 * 1024 + 1))
    page.locator("#license-file").set_input_files(str(big))
    expect(err).to_be_visible()
    expect(err).to_contain_text("больше 5 МБ")
    expect(page.locator("#license-thumb")).to_be_hidden()
    page.locator("#registration button.submit").click()
    # отправка заблокирована: редиректа нет, notice не показывался
    assert page.url.endswith("/instructors/apply")
    expect(page.locator("#notice")).to_be_hidden()

    # 2) не-изображение с расширением .png — серверная 422 у поля
    fake = tmp_path / "fake.png"
    fake.write_bytes(b"this is definitely not an image")
    page.locator("#license-file").set_input_files(str(fake))
    expect(err).to_be_hidden()  # клиентский формат (.png) пройден
    page.locator("#registration button.submit").click()
    expect(err).to_be_visible()
    expect(err).to_contain_text("допустимы только изображения JPEG или PNG")
    expect(page.locator("#notice")).to_contain_text(
        "допустимы только изображения JPEG или PNG")
    assert page.url.endswith("/instructors/apply")

    # заявка с битым файлом НЕ создана (валидация ДО записи, NFR-6)
    admin_token = admin_login(server)
    status, listing = api("GET", "/api/admin/instructor-applications",
                          base=server, admin_token=admin_token)
    assert status == 200
    assert all(a["email"] != email for a in listing["applications"])


def test_bug048_admin_card_license_photo_real_backend(page, server, tmp_path):
    """TC-UI-022 (change add-instructor-student-loop, BUG-048): админ-карточка
    заявки на ЖИВОМ бэкенде — ВУ, приложенное при регистрации (multipart
    license_photo), отображается (GET …/license-image с X-Admin-Token);
    у заявки без ВУ — явный плейсхолдер «Файл ВУ не приложен», не битая
    картинка."""
    base_body = {
        "surname": "Документов", "name": "Дмитрий", "patronymic": "Олегович",
        "phone": "+7 905 111-22-33",
        "address": "г. Москва, ул. Осенняя, д. 9", "work_format": "school",
        "license_number": "9911555444", "license_category": "B",
        "password": "Dr1vePass!", "password_confirm": "Dr1vePass!",
    }
    email_with, email_no = unique_email("bug048yes"), unique_email("bug048no")
    status, data = api_multipart(
        "/api/instructors/apply", base=server,
        fields={**base_body, "email": email_with, "consent": "true"},
        files={"license_photo": ("license.png", PNG_1PX, "image/png")})
    assert status == 200 and data and data["ok"], (status, data)
    status, data = api("POST", "/api/instructors/apply", base=server, body={
        **base_body, "email": email_no, "consent": True})
    assert status == 200 and data and data["ok"], (status, data)

    _seed_session(page, "admin_token", admin_login(server))
    page.goto(f"{server}/admin-dashboard")
    page.locator(".nav button", has_text="Заявки инструкторов").click()

    # заявка С ВУ: изображение отображается в карточке
    page.locator("#app-rows tr", has_text=email_with).click()
    expect(page.locator("#ic-backdrop")).to_be_visible()
    expect(page.locator("#ic-license img")).to_be_visible()
    page.locator("#ic-close").click()
    expect(page.locator("#ic-backdrop")).to_be_hidden()

    # заявка БЕЗ ВУ: явный плейсхолдер, картинки нет
    page.locator("#app-rows tr", has_text=email_no).click()
    expect(page.locator("#ic-backdrop")).to_be_visible()
    expect(page.locator("#ic-license")).to_contain_text("Файл ВУ не приложен")
    assert page.locator("#ic-license img").count() == 0


def test_bug048_mycars_photo_thumbnail_before_send_and_errors(
        page, server, tmp_path):
    """TC-UI-023 (change add-booking-docs, BUG-048): «Мои автомобили» —
    выбранное фото СТС показывает миниатюру ДО отправки; неверный формат
    отсекается на клиенте (красный текст + тост, файл не выбирается, кнопка
    заблокирована — FR-44); битый .png проходит клиент, серверная 422 —
    внятный тост, авто НЕ создается; валидный PNG — авто создан с СТС."""
    token, _ = _approve_instructor(server)
    _seed_session(page, "session_token", token)
    page.goto(f"{server}/instructor/dashboard")
    page.locator('.nav button[data-tab="Мои автомобили"]').click()

    # модалка нового авто: поля заполнены, СТС еще нет — кнопка заблокирована
    page.locator("#open-add").click()
    expect(page.locator("#m-add")).to_be_visible()
    page.fill("#f-brand", "Škoda")
    page.fill("#f-model", "Rapid")
    page.fill("#f-year", "2020")
    page.fill("#f-plate", "А123АА777")
    page.locator("#f-trans button[data-v='automatic']").click()
    expect(page.locator("#save-car")).to_be_disabled()

    # 1) неверный формат (.txt) — клиент: красный текст + тост, без миниатюры
    bad = tmp_path / "note.txt"
    bad.write_bytes(b"hello")
    page.locator("#f-sts").set_input_files(str(bad))
    expect(page.locator("#up-photo-err")).to_be_visible()
    expect(page.locator("#up-photo-err")).to_contain_text("JPEG или PNG")
    expect(page.locator("#toast")).to_contain_text("JPEG или PNG")
    expect(page.locator("#up-zone.has-thumb")).to_have_count(0)
    expect(page.locator("#save-car")).to_be_disabled()  # FR-44: без СТС нельзя

    # 2) битый .png — клиент пройден (миниатюра до отправки), сервер 422,
    #    внятный тост, автомобиль НЕ создан
    fake = tmp_path / "fake.png"
    fake.write_bytes(b"not an image at all")
    page.locator("#f-sts").set_input_files(str(fake))
    expect(page.locator("#up-zone.has-thumb")).to_have_count(1)
    page.locator("#save-car").click()
    expect(page.locator("#toast")).to_contain_text(
        "допустимы только изображения JPEG или PNG")
    status, data = api("GET", "/api/instructor/cars", base=server, token=token)
    assert data["cars"] == [], data  # 422: авто не создается (FR-44)
    expect(page.locator("#m-add")).to_be_visible()  # модалка осталась открытой

    # 3) валидный PNG: миниатюра до отправки → сохранение → авто с СТС
    good = tmp_path / "sts.png"
    good.write_bytes(PNG_1PX)
    page.locator("#f-sts").set_input_files(str(good))
    expect(page.locator("#up-zone.has-thumb")).to_have_count(1)
    expect(page.locator("#save-car")).to_be_enabled()
    page.locator("#save-car").click()
    card = page.locator(".car")
    expect(card).to_have_count(1)
    expect(card.locator(".sts-slot")).to_have_class("sts-slot has")
    status, data = api("GET", "/api/instructor/cars", base=server, token=token)
    assert data["cars"][0]["has_sts"] is True, data


# ---------------------------------------------------------------------------
# Спринт 5 (change add-booking-docs): ИНТЕГРАЦИОННЫЕ e2e новых разделов на
# живом бэкенде — авто (5 ракурсов + СТС + комплектность → каталог ученика),
# документы, бронирование (слоты → запрос → confirm/reject → 409).


def _fresh_page(browser, token):
    """Свежий контекст с сессией token: переключение пользователя внутри
    одного теста (sessionStorage изолирован по контексту; localStorage-guard
    _seed_session повторный сев блокирует — здесь он не нужен)."""
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.add_init_script(
        "sessionStorage.setItem('session_token','%s');" % token)
    return pg, ctx


def test_s5_car_full_kit_completeness_and_student_sees_car(
        browser, server, tmp_path):
    """TC-UI-024 (change add-booking-docs): интеграция «авто». Инструктор
    добавил авто через UI (модалка: СТС обязателен) и загрузил 5 фото
    ракурсов по слотам → комплектность «Комплект полный» (совпадает с
    GET /api/admin/cars/completeness); ученик принятой пары видит авто
    в каталоге (UI /instructor-choice + API), фото ракурсов ему выдаются,
    СТС — НЕ выдаётся (FR-42/FR-44)."""
    instr_token, instructor_id = _approve_instructor(server)
    page, ctx = _fresh_page(browser, instr_token)
    try:
        # --- UI: авто с обязательным СТС ---
        page.goto(f"{server}/instructor/dashboard")
        page.locator('.nav button[data-tab="Мои автомобили"]').click()
        page.locator("#open-add").click()
        page.fill("#f-brand", "Škoda")
        page.fill("#f-model", "Rapid")
        page.fill("#f-year", "2020")
        page.fill("#f-plate", "А123АА777")
        page.locator("#f-trans button[data-v='automatic']").click()
        sts = tmp_path / "sts.png"
        sts.write_bytes(PNG_1PX)
        page.locator("#f-sts").set_input_files(str(sts))
        page.locator("#save-car").click()
        card = page.locator(".car")
        expect(card).to_have_count(1)

        # --- UI: 5 ракурсов по слотам ---
        angles = ["front", "rear", "left", "right", "interior"]
        for i, angle in enumerate(angles):
            f = tmp_path / f"{angle}.png"
            f.write_bytes(PNG_1PX + bytes([i]))  # magic bytes PNG сохранены
            with page.expect_file_chooser() as fc_info:
                card.locator(f".slot[data-angle='{angle}']").click()
            fc_info.value.set_files(str(f))
        # комплектность «полный» после пятого слота
        expect(card.locator(".car-head .status")).to_have_text("Комплект полный")
        expect(card.locator(".slot.empty")).to_have_count(0)
        for angle in angles:
            expect(card.locator(
                f".slot[data-angle='{angle}'].has img")).to_be_visible()
    finally:
        ctx.close()

    # --- API: комплектность инструктора и админ-разрез совпадают ---
    status, data = api("GET", "/api/instructor/cars", base=server,
                       token=instr_token)
    car = data["cars"][0]
    assert car["has_sts"] and all(car["photos"].values()), car
    admin_token = admin_login(server)
    status, data = api("GET", "/api/admin/cars/completeness", base=server,
                       admin_token=admin_token)
    assert status == 200 and data["ok"], (status, data)
    row = next(c for c in data["cars"] if c["id"] == car["id"])
    assert row["has_sts"] and all(row["photos"].values()) and not row["blocked"], row

    # --- пара: ученик подает заявку, инструктор принимает с этим авто ---
    stu_token = _student_token(server)
    status, data = api("POST", "/api/student/requests", base=server,
                       token=stu_token, body={"instructor_id": instructor_id})
    assert status == 200 and data["ok"], (status, data)
    status, data = api("GET", "/api/instructor/requests", base=server,
                       token=instr_token)
    request_id = data["requests"][0]["id"]
    status, data = api(
        "POST", f"/api/instructor/requests/{request_id}/accept",
        base=server, token=instr_token, body={"car_id": car["id"]})
    assert status == 200 and data["ok"], (status, data)

    # --- ученик: авто в каталоге (API + UI), фото видны, СТС НЕ выдается ---
    status, data = api("GET", f"/api/student/instructors/{instructor_id}",
                       base=server, token=stu_token)
    cars = data["instructor"]["cars"]
    assert any(c["brand"] == "Škoda" and c["model"] == "Rapid" for c in cars), cars
    status, hdrs, body = _raw_get(
        f"{server}/api/instructor/cars/{car['id']}/photo/front", token=stu_token)
    assert status == 200 and hdrs["Content-Type"] == "image/png"
    status, _, _ = _raw_get(
        f"{server}/api/instructor/cars/{car['id']}/sts", token=stu_token)
    assert status == 403, "СТС ученику не выдается (FR-44)"

    page, ctx = _fresh_page(browser, stu_token)
    try:
        page.goto(f"{server}/instructor-choice")
        # привязка по data-id (в общей БД тестовой сессии инструкторов много)
        stu_card = page.locator(f".card[data-id='{instructor_id}']")
        expect(stu_card).to_have_count(1)
        expect(stu_card).to_contain_text("Škoda Rapid")
    finally:
        ctx.close()


def test_s5_booking_flow_slots_request_confirm_and_409(browser, server):
    """TC-UI-025 (change add-booking-docs): интеграция «бронирование» на
    живом бэкенде. Ученик принятой пары видит слоты инструктора в разделе
    «Мои брони» (свободные кликабельны) → отправил запрос (слот стал «запрос
    отправлен», в «Моих бронях» — желтый статус); инструктор в разделе
    «Бронирования» видит запрос и подтверждает → бронь в календарях ОБОИХ
    (ученик «Подтверждена», слот инструктора помечен учеником); повторная
    бронь занятого слота → 409 без записи (NFR-8)."""
    instr_token, instructor_id = _approve_instructor(server)
    car_id = _add_car(server, instr_token)
    status, data = api("PUT", "/api/instructor/availability", base=server,
                       token=instr_token,
                       body={"intervals": [
                           {"weekday": 2, "start_time": "10:00", "end_time": "12:00"},
                           {"weekday": 2, "start_time": "12:00", "end_time": "14:00"},
                       ]})
    assert status == 200 and data["ok"], (status, data)
    stu_token = _accepted_request(server, instr_token, instructor_id, car_id)

    # --- ученик: раздел «Мои брони» внутри кабинета — пара и свободные слоты
    page, ctx = _fresh_page(browser, stu_token)
    try:
        page.goto(f"{server}/cabinet#/my-bookings")
        expect(page.locator("#sec-bookings")).to_be_visible()
        expect(page.locator('.snav button[data-tab="Мои брони"]')).to_have_class("on")
        expect(page.locator("#bk-pair-name")).to_have_text("Громов Борис Арсеньевич")
        expect(page.locator(".bk-slot.free")).to_have_count(2)

        # клик по свободному слоту → модалка → отправка запроса
        page.locator(".bk-slot.free").first.click()
        expect(page.locator("#m-book")).to_be_visible()
        expect(page.locator("#bk-time")).to_have_text("10:00–12:00")
        page.locator("#bk-send").click()
        expect(page.locator("#toast")).to_contain_text("Запрос отправлен")
        # слот стал «запрос отправлен» (желтый), в списке броней — статус new
        expect(page.locator(".bk-slot.mine")).to_have_count(1)
        expect(page.locator(".bk-slot.free")).to_have_count(1)
        stu_req = page.locator(".bk-req").first
        expect(stu_req.locator(".bk-status")).to_have_text("Запрос отправлен")
        assert stu_req.locator(".bk-status").evaluate(
            "el => getComputedStyle(el).backgroundColor") == "rgb(42, 32, 16)"
    finally:
        ctx.close()

    # --- инструктор: раздел «Бронирования» — запрос виден, подтверждение
    page, ctx = _fresh_page(browser, instr_token)
    try:
        page.goto(f"{server}/instructor/dashboard")
        page.locator('.nav button[data-tab="Бронирования"]').click()
        expect(page.locator("#sec-bookings")).to_be_visible()
        req = page.locator("#bk-list .req", has_text="Смирнова Ольга Павловна")
        expect(req).to_have_count(1)
        expect(req.locator(".status")).to_have_text("Новый запрос")
        req.locator("[data-confirm]").click()
        expect(page.locator("#toast")).to_contain_text("Бронь подтверждена")
        # календарь инструктора: слот помечен учеником (подтвержденная бронь)
        booked = page.locator("#bk-grid .slot.booked")
        expect(booked).to_have_count(1)
        expect(booked.locator("small")).to_have_text("Смирнова Ольга Павловна")
    finally:
        ctx.close()

    # --- ученик: «Подтверждена» в «Моих бронях» (календарь ученика)
    page, ctx = _fresh_page(browser, stu_token)
    try:
        page.goto(f"{server}/cabinet#/my-bookings")
        expect(page.locator(".bk-req").first.locator(".bk-status")).to_have_text(
            "Подтверждена")
        # подтвержденный слот занят: свободных остался один, своего запроса нет
        expect(page.locator(".bk-slot.free")).to_have_count(1)
        expect(page.locator(".bk-slot.mine")).to_have_count(0)
    finally:
        ctx.close()

    # --- повторная бронь занятого слота → 409, записи нет (NFR-8) ---
    status, data = api("GET",
                       f"/api/student/instructors/{instructor_id}/slots",
                       base=server, token=stu_token)
    booked_slot = [s for s in data["slots"]
                   if (s["weekday"], s["start_time"], s["end_time"])
                   == (2, "10:00", "12:00")]
    slot_id = booked_slot[0]["id"]
    status, data = api("POST", "/api/student/bookings", base=server,
                       token=stu_token, body={"availability_id": slot_id})
    assert status == 409 and data["ok"] is False, (status, data)
    # бронь по-прежнему одна (второй записи нет)
    status, data = api("GET", "/api/student/bookings", base=server,
                       token=stu_token)
    confirmed = [b for b in data["bookings"] if b["status"] == "confirmed"]
    assert len(confirmed) == 1 and confirmed[0]["car"]["id"] == car_id, data


# ------------------------------------------------------------- design-guard
@pytest.mark.parametrize("filename", [
    "instructor-dashboard.html", "cabinet.html",
    "review-form.html", "instructor-choice.html"])
def test_s4_pages_tag_balance(filename):
    """NIT-4 review-001 (change add-s3-frontend-links); BUG-047: баланс тегов
    правленых страниц (my-cars.html/my-requests.html встроены в кабинеты и
    удалены — проверяются их новые носители: дашборд и кабинет ученика).
    Лишний/незакрытый тег роняет тест при любом следующем редактировании."""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}

    class _Balance(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack: list = []
            self.errs: list = []

        def handle_starttag(self, tag, attrs):
            if tag not in VOID:
                self.stack.append((tag, self.getpos()))

        def handle_endtag(self, tag):
            if tag in VOID:
                return
            if not self.stack or self.stack[-1][0] != tag:
                self.errs.append(f"mismatch </{tag}> at {self.getpos()}")
                return
            self.stack.pop()

    p = _Balance()
    p.feed((ROOT / "frontend" / filename).read_text(encoding="utf-8"))
    assert not p.errs and not p.stack, (p.errs, p.stack)
