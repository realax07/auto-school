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


def test_admin_moderation_approve_reflects_status(server):
    """TC-UI-006 (change add-instructor-cabinet): админ-модерация через API —
    approve заявки, статус отражается в списке заявок."""
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

    token = admin_login(server)

    # заявка в списке со статусом waiting
    status, data = api("GET", "/api/admin/instructor-applications",
                       base=server, admin_token=token)
    assert status == 200 and data, (status, data)
    found = [a for a in data["applications"] if a["email"] == email]
    assert len(found) == 1, "заявка не найдена в списке админа"
    app_id, status_before = found[0]["id"], found[0]["status"]
    assert status_before == "waiting", status_before

    # approve → ok
    status, data = api(
        "POST", f"/api/admin/instructor-applications/{app_id}/approve",
        base=server, admin_token=token)
    assert status == 200 and data and data.get("ok") is True, (status, data)

    # статус отражается в списке: waiting → approved
    status, data = api("GET", "/api/admin/instructor-applications",
                       base=server, admin_token=token)
    assert status == 200 and data, (status, data)
    after = [a for a in data["applications"] if a["id"] == app_id][0]
    assert after["status"] == "approved", after["status"]
