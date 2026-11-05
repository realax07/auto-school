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




def _route_png(page, server, path: str, requests_log: list | None = None) -> None:
    """Файл документа/фото — PNG (content_type image/png): предпросмотр
    ДОЛЖЕН открываться (ОВ-4); запросы пишутся в requests_log для
    проверки авторизационных заголовков."""
    def _handler(route):
        if requests_log is not None:
            requests_log.append(route.request)
        route.fulfill(status=200, content_type="image/png", body=PNG_1PX)
    page.route(f"{server}{path}", _handler)


def test_s8_my_documents_statuses_versions_and_license_replace(page, server,
                                                               tmp_path):
    """TC-UI-033 (change add-s8-cars-docs-booking, задачи 5.1, FR-70/71/72,
    ОВ-1): «Мои документы» — карточки ВУ и СТС со статусами версий:
    «Действует», «Ожидает проверки замены» (pending), «Отклонено» с ПРИЧИНОЙ
    от администратора; предпросмотр документа открывается (изображение
    загружено, naturalWidth > 0). Замена ВУ — только через диалог FR-71
    с предупреждением и ЯВНОЙ кнопкой «Заменить»: отмена НЕ отправляет файл;
    подтверждение шлет multipart POST /api/instructor/documents/license
    (поле file) и перезагружает список — появляется «Ожидает проверки
    замены». API замокан по контракту design.md (бэкенд-волна параллельна)."""
    _mock_instructor_shell(page, server)
    docs_state = {"license_pending": False}
    license_posts: list = []
    doc_files: list = []

    def _docs(req):
        lic = _doc_license()
        if docs_state["license_pending"]:
            lic["pending"] = {"version": 2,
                              "uploaded_at": "2026-11-02 09:12:00"}
        return 200, {"ok": True, "documents": [
            lic,
            _doc_sts(52, "Škoda", "Rapid", "А 123 АА 777",
                     pending={"version": 2, "uploaded_at": "2026-10-30 18:40:00"}),
            _doc_sts(53, "Lada", "Vesta", "Е 789 ЕЕ 777",
                     last_rejected={
                         "version": 2,
                         "reject_reason": "Фото нечитаемо: номер СТС и VIN "
                                          "размыты — загрузите при дневном свете",
                         "decided_at": "2026-10-30 11:00:00"}),
        ], "license": lic, "license_hint": None}

    def _license_upload(req):
        docs_state["license_pending"] = True
        return 200, {"ok": True, "document": {
            "status": "pending", "version": 2,
            "uploaded_at": "2026-11-02 09:12:00"}}

    _route_json(page, server, "/api/instructor/documents", _docs)
    _route_json(page, server, "/api/instructor/cars", lambda req: (
        200, {"ok": True, "cars": [
            {"id": 52, "brand": "Škoda", "model": "Rapid", "year": 2020,
             "transmission": "automatic", "plate": "А 123 АА 777",
             "status": "validated", "photos": {}, "has_sts": True,
             "sts_url": None, "created_at": "2026-10-02 12:00:00"},
            {"id": 53, "brand": "Lada", "model": "Vesta", "year": 2021,
             "transmission": "manual", "plate": "Е 789 ЕЕ 777",
             "status": "validated", "photos": {}, "has_sts": True,
             "sts_url": None, "created_at": "2026-10-28 12:00:00"},
        ]}))
    _route_json(page, server, "/api/instructor/documents/license",
                _license_upload, method="POST", capture=license_posts)
    _route_png(page, server, "/api/instructor/documents/license-51/file",
               doc_files)
    _route_png(page, server, "/api/instructor/documents/sts-52/file")

    page.goto(f"{server}/instructor/dashboard")
    page.locator('.nav button[data-tab="Профиль и документы"]').click()
    expect(page.locator("#sec-docs")).to_be_visible()

    # --- карточки: ВУ 1 + СТС 2 (по авто), статусы версий (FR-70) ---
    expect(page.locator("#lic-docs .doc")).to_have_count(1)
    expect(page.locator("#sts-docs .doc")).to_have_count(2)
    lic_card = page.locator("#lic-docs .doc").first
    expect(lic_card.locator(".name")).to_have_text("Водительское удостоверение")
    expect(lic_card.locator(".ds-badge")).to_have_text("Действует")
    expect(lic_card.locator(".meta .ver")).to_contain_text("версия 1")

    # pending-замена СТС: бейдж-плашка на миниатюре + блок «Ожидает проверки»
    pend_card = page.locator("#sts-docs .doc", has_text="Škoda Rapid")
    expect(pend_card.locator(".pendtag")).to_have_text("замена на проверке")
    expect(pend_card.locator(".subver.pend b")).to_have_text(
        "Ожидает проверки замены")
    expect(pend_card.locator(".subver.pend")).to_contain_text(
        "действует текущая версия")

    # rejected-замена СТС: причина отказа администратора (ОВ-1) + подсказка
    rej_card = page.locator("#sts-docs .doc", has_text="Lada Vesta")
    expect(rej_card.locator(".subver.rej b")).to_have_text(
        "Причина отказа от администратора")
    expect(rej_card.locator(".subver.rej")).to_contain_text(
        "номер СТС и VIN размыты")
    expect(rej_card.locator(".subver.rej")).to_contain_text(
        "действует предыдущая версия, можно загрузить заново")

    # --- предпросмотр: изображение открывается (ОВ-4) ---
    lic_card.locator(".thumb").click()
    expect(page.locator("#m-view")).to_be_visible()
    img = page.locator("#view-full img")
    expect(img).to_be_visible()
    assert img.evaluate("el => el.naturalWidth") > 0, \
        "файл документа не открылся (ОВ-4)"
    page.keyboard.press("Escape")
    expect(page.locator("#m-view")).to_be_hidden()

    # --- замена ВУ (FR-71): диалог с предупреждением; отмена ничего не шлет ---
    lic_card.locator("button", has_text="Заменить").click()
    expect(page.locator("#m-replace")).to_be_visible()
    expect(page.locator("#rep-sub")).to_have_text("Водительское удостоверение")
    warnbox = page.locator("#m-replace .warnbox")
    expect(warnbox).to_contain_text("Замена не вступает в силу сразу")
    expect(warnbox).to_contain_text("после проверки администратором")
    expect(warnbox).to_contain_text("действует предыдущая версия")
    expect(page.locator("#rep-go")).to_have_text("Заменить")  # явная кнопка
    page.locator("#rep-cancel").click()
    expect(page.locator("#m-replace")).to_be_hidden()
    assert license_posts == [], "отмена диалога отправила файл (FR-71 нарушен)"

    # --- явное «Заменить» → выбор файла → multipart POST (поле file) ---
    png = tmp_path / "license-new.png"
    png.write_bytes(PNG_1PX)
    lic_card.locator("button", has_text="Заменить").click()
    expect(page.locator("#m-replace")).to_be_visible()
    with page.expect_file_chooser() as fc_info:
        page.locator("#rep-go").click()
    fc_info.value.set_files(str(png))
    expect(page.locator("#toast")).to_contain_text(
        "на проверку администратору")
    assert len(license_posts) == 1, "POST замены ВУ не отправлен"
    req = license_posts[0]
    assert req.url.endswith("/api/instructor/documents/license"), req.url
    assert req.method == "POST"
    assert "multipart/form-data" in (req.headers.get("content-type") or "")
    assert b'name="file"' in (req.post_data_buffer or b""), \
        "файл не в поле file контракта"

    # после загрузки список перезагружен: у ВУ «Ожидает проверки замены»,
    # действует предыдущая версия (документ «не мигает»)
    lic_card = page.locator("#lic-docs .doc").first
    expect(lic_card.locator(".subver.pend b")).to_have_text(
        "Ожидает проверки замены")
    expect(lic_card.locator(".ds-badge")).to_have_text("Действует")
    # файл запрошен с сессией владельца
    assert doc_files and doc_files[0].headers.get(
        "x-session-token") == INSTRUCTOR_TOKEN


def test_s8_sts_upload_missing_and_replace_car_modal_422_honest(
        page, server, tmp_path):
    """TC-UI-034 (change add-s8-cars-docs-booking, задачи 5.1/баг 5.2-СТС,
    FR-69/FR-72, ОВ-6): СТС на созданном авто — дозагрузка ОТСУТСТВУЮЩЕГО
    из «Моих документов» (карточка «нет СТС», POST …/cars/{id}/photo/sts)
    и замена действующего из модалки авто (кнопка «Заменить СТС» + диалог
    FR-71); ошибка 422 показывается честно (текст сервера), список не
    меняется. Бэкенд-волна параллельна — API замокан по design.md."""
    _mock_instructor_shell(page, server)
    state = {"sts12_added": False, "fail_next": False}
    sts_posts: list = []
    docs_gets: list = []

    def _docs(req):
        docs_gets.append(req.url)
        docs = [_doc_sts(52, "Škoda", "Rapid", "А 123 АА 777")]
        if state["sts12_added"]:
            docs.append(_doc_sts(53, "Kia", "Rio", "В 456 ВВ 777"))
        return 200, {"ok": True, "documents": docs, "license": None,
                     "license_hint": "Заявка без фото ВУ"}

    def _cars(req):
        cars = [
            {"id": 52, "brand": "Škoda", "model": "Rapid", "year": 2020,
             "transmission": "automatic", "plate": "А 123 АА 777",
             "status": "validated", "photos": {}, "has_sts": True,
             "sts_url": None, "created_at": "2026-10-02 12:00:00"},
            {"id": 53, "brand": "Kia", "model": "Rio", "year": 2022,
             "transmission": "manual", "plate": "В 456 ВВ 777",
             "status": "draft", "photos": {}, "has_sts": state["sts12_added"],
             "sts_url": None, "created_at": "2026-10-05 12:00:00"},
        ]
        return 200, {"ok": True, "cars": cars}

    def _sts_upload(req):
        if state["fail_next"]:
            state["fail_next"] = False
            return 422, {"ok": False,
                         "error": "Фото: допустимы только изображения JPEG или PNG"}
        if req.url.endswith("/cars/53/photo/sts"):
            state["sts12_added"] = True
            return 200, {"ok": True, "url": "/api/instructor/cars/53/photo/sts",
                         "status": "draft",
                         "document": {"status": "verified", "version": 1}}
        return 200, {"ok": True, "url": "/api/instructor/cars/52/photo/sts",
                     "status": "validated",
                     "document": {"status": "pending", "version": 2}}

    _route_json(page, server, "/api/instructor/documents", _docs)
    _route_json(page, server, "/api/instructor/cars", _cars)
    # ВАЖНО: sts-маршрут регистрируется ПОСЛЕ 'cars*' — побеждает последний
    _route_json(page, server, "/api/instructor/cars/53/photo/sts",
                _sts_upload, method="POST", capture=sts_posts)
    _route_json(page, server, "/api/instructor/cars/52/photo/sts",
                _sts_upload, method="POST", capture=sts_posts)
    _route_png(page, server, "/api/instructor/documents/sts-52/file")
    _route_png(page, server, "/api/instructor/documents/sts-53/file")

    page.goto(f"{server}/instructor/dashboard")
    page.locator('.nav button[data-tab="Профиль и документы"]').click()
    expect(page.locator("#sec-docs")).to_be_visible()

    # --- авто БЕЗ СТС: карточка «нет СТС» с кнопкой «Загрузить» (FR-69) ---
    none_card = page.locator("#sts-docs .doc", has_text="Kia Rio")
    expect(none_card.locator(".ds-badge")).to_have_text("нет СТС")
    expect(none_card.locator("button", has_text="Загрузить")).to_be_visible()
    expect(page.locator("#sts-docs .doc")).to_have_count(2)

    # первая загрузка — без диалога FR-71 (предыдущей версии нет)
    png = tmp_path / "sts53.png"
    png.write_bytes(PNG_1PX)
    with page.expect_file_chooser() as fc_info:
        none_card.locator("button", has_text="Загрузить").click()
    fc_info.value.set_files(str(png))
    expect(page.locator("#toast")).to_contain_text("Фото СТС загружено")
    assert len(sts_posts) == 1
    assert sts_posts[0].url.endswith("/api/instructor/cars/53/photo/sts")
    assert b'name="photo"' in (sts_posts[0].post_data_buffer or b"")
    # список перезагружен: у Kia Rio появилась карточка «Действует»
    expect(page.locator("#sts-docs .doc")).to_have_count(2)
    kia = page.locator("#sts-docs .doc", has_text="Kia Rio")
    expect(kia.locator(".ds-badge")).to_have_text("Действует")
    gets_after_add = len(docs_gets)

    # --- замена действующего СТС из модалки авто («Мои автомобили») ---
    page.locator('.nav button[data-tab="Мои автомобили"]').click()
    card = page.locator(".car", has_text="Škoda Rapid")
    expect(card).to_have_count(1)
    card.click()
    expect(page.locator("#m-car")).to_be_visible()
    sts_btn = page.locator("#mc-acts [data-sts-btn]")
    expect(sts_btn).to_have_text("Заменить СТС")
    sts_btn.click()
    expect(page.locator("#m-replace")).to_be_visible()
    expect(page.locator("#m-replace .warnbox")).to_contain_text(
        "Замена не вступает в силу сразу")
    png2 = tmp_path / "sts52-new.png"
    png2.write_bytes(PNG_1PX + b"\x09")
    with page.expect_file_chooser() as fc_info:
        page.locator("#rep-go").click()
    fc_info.value.set_files(str(png2))
    # ОВ-6: замена СТС статус авто НЕ меняет — честный тост об этом
    expect(page.locator("#toast")).to_contain_text("статус авто не изменился")
    assert len(sts_posts) == 2
    assert sts_posts[1].url.endswith("/api/instructor/cars/52/photo/sts")
    # закрыть галерею авто (осталась открыта) перед переходом в «Мои документы»
    page.locator("#m-car .close").click()
    expect(page.locator("#m-car")).to_be_hidden()

    # --- 422: ошибка сервера показывается честно, список не меняется ---
    state["fail_next"] = True
    page.locator('.nav button[data-tab="Профиль и документы"]').click()
    expect(page.locator("#sec-docs")).to_be_visible()
    sts_card = page.locator("#sts-docs .doc", has_text="Škoda Rapid")
    gets_before_fail = len(docs_gets)  # GET от открытия раздела уже учтен
    sts_card.locator("button", has_text="Заменить").click()
    expect(page.locator("#m-replace")).to_be_visible()
    with page.expect_file_chooser() as fc_info:
        page.locator("#rep-go").click()
    fc_info.value.set_files(str(png2))
    expect(page.locator("#toast")).to_contain_text(
        "допустимы только изображения JPEG или PNG")
    # список НЕ перезагружен (безуспешная загрузка не меняет статусы)
    assert len(docs_gets) == gets_before_fail


def test_s8_sts_gallery_replace_dialog(page, server, tmp_path):
    """TC-UI-040 (change add-s8-cars-docs-booking, задача 3.1, review-003
    MAJ-2): FR-71 на галерейном пути СТС — рамка sts видна только при
    has_sts, т.е. клик по большому окну галереи модалки авто — это ВСЕГДА
    замена: открывается диалог «Заменить» (тот же, что у явной кнопки),
    файл выбирается только после подтверждения; «Отмена» не отправляет
    POST; подтверждение — POST …/cars/{id}/photo/sts. Бэкенд замокан."""
    _mock_instructor_shell(page, server)
    sts_posts: list = []

    def _docs(req):
        docs = [_doc_sts(52, "Škoda", "Rapid", "А 123 АА 777")]
        return 200, {"ok": True, "documents": docs, "license": None,
                     "license_hint": "Заявка без фото ВУ"}

    def _cars(req):
        cars = [{"id": 52, "brand": "Škoda", "model": "Rapid", "year": 2020,
                 "transmission": "automatic", "plate": "А 123 АА 777",
                 "status": "validated", "photos": {}, "has_sts": True,
                 "sts_url": None, "created_at": "2026-10-02 12:00:00"}]
        return 200, {"ok": True, "cars": cars}

    def _sts_upload(req):
        return 200, {"ok": True, "url": "/api/instructor/cars/52/photo/sts",
                     "status": "validated",
                     "document": {"status": "pending", "version": 2}}

    _route_json(page, server, "/api/instructor/documents", _docs)
    _route_json(page, server, "/api/instructor/cars", _cars)
    # ВАЖНО: sts-маршрут регистрируется ПОСЛЕ 'cars*' — побеждает последний
    _route_json(page, server, "/api/instructor/cars/52/photo/sts",
                _sts_upload, method="POST", capture=sts_posts)
    _route_png(page, server, "/api/instructor/documents/sts-52/file")

    page.goto(f"{server}/instructor/dashboard")
    page.locator('.nav button[data-tab="Мои автомобили"]').click()
    card = page.locator(".car", has_text="Škoda Rapid")
    card.click()
    expect(page.locator("#m-car")).to_be_visible()

    # --- галерейный путь: рамка sts → клик по большому окну → ДИАЛОГ ---
    page.locator("#mc-thumbs .gal-thumb[data-galkey='sts']").click()
    # без fix клик #mc-big открыл бы file chooser (тихая замена мимо FR-71)
    page.locator("#mc-big").click()
    expect(page.locator("#m-replace")).to_be_visible()
    expect(page.locator("#m-replace .warnbox")).to_contain_text(
        "Замена не вступает в силу сразу")
    assert len(sts_posts) == 0  # отмена: ни одного POST не ушло
    page.locator("#rep-cancel").click()
    expect(page.locator("#m-replace")).to_be_hidden()
    assert len(sts_posts) == 0

    # --- подтверждение замены через галерею → POST на контракт ---
    page.locator("#mc-big").click()
    expect(page.locator("#m-replace")).to_be_visible()
    png = tmp_path / "sts52-gal.png"
    png.write_bytes(PNG_1PX + b"\x11")
    with page.expect_file_chooser() as fc_info:
        page.locator("#rep-go").click()
    fc_info.value.set_files(str(png))
    # ОВ-6: честный тост — статус авто не изменился
    expect(page.locator("#toast")).to_contain_text("статус авто не изменился")
    assert len(sts_posts) == 1
    assert sts_posts[0].url.endswith("/api/instructor/cars/52/photo/sts")


# =========================================================================
# TC-UI-042 — BUG-053: компоновка модалки фото авто по прямойве Заказчика
# (decisions/2026-11-02-photo-modal-layout.md): галерея вверху (большое
# окно, миниатюры ПОД ним, крупнее), «Информация»/«Комплектность» — внизу;
# длинный инструктивный текст удален.
# =========================================================================

def test_bug053_car_modal_single_column_photo_layout(page, server):
    """TC-UI-042 (change add-s8-cars-docs-booking, BUG-053): в модалке
    фото авто (#m-car) миниатюры (#mc-thumbs) идут в DOM ПОСЛЕ большого
    окна (#mc-big) и ВЫШЕ панели «Информация» (#mc-info) — низ модалки;
    длинный инструктивный form-note («Клик по миниатюре — открыть в
    большом окне…») ОТСУТСТВУЕТ (замена — короткий title на mc-big);
    большое окно выше миниатюры (boundingBox: min-height 340px против
    ~78px у миниатюры 104×4:3). id/обработчики не переименованы.
    Моки как в TC-UI-040, бэкенд замокан."""
    _mock_instructor_shell(page, server)

    def _docs(req):
        docs = [_doc_sts(52, "Škoda", "Rapid", "А 123 АА 777")]
        return 200, {"ok": True, "documents": docs, "license": None,
                     "license_hint": "Заявка без фото ВУ"}

    def _cars(req):
        cars = [{"id": 52, "brand": "Škoda", "model": "Rapid", "year": 2020,
                 "transmission": "automatic", "plate": "А 123 АА 777",
                 "status": "validated", "photos": {}, "has_sts": True,
                 "sts_url": None, "created_at": "2026-10-02 12:00:00"}]
        return 200, {"ok": True, "cars": cars}

    _route_json(page, server, "/api/instructor/documents", _docs)
    _route_json(page, server, "/api/instructor/cars", _cars)
    _route_png(page, server, "/api/instructor/documents/sts-52/file")

    page.goto(f"{server}/instructor/dashboard")
    page.locator('.nav button[data-tab="Мои автомобили"]').click()
    card = page.locator(".car", has_text="Škoda Rapid")
    card.click()
    expect(page.locator("#m-car")).to_be_visible()
    expect(page.locator("#mc-thumbs .gal-thumb")).to_have_count(6)  # 5 ракурсов + СТС

    # (а)/(б) порядок в DOM: mc-big → mc-thumbs → mc-info (низ модалки)
    order = page.evaluate(
        "() => {"
        " const big = document.getElementById('mc-big');"
        " const thumbs = document.getElementById('mc-thumbs');"
        " const info = document.getElementById('mc-info');"
        " return {"
        "  big_then_thumbs: Boolean(big.compareDocumentPosition(thumbs)"
        "                           & Node.DOCUMENT_POSITION_FOLLOWING),"
        "  thumbs_then_info: Boolean(thumbs.compareDocumentPosition(info)"
        "                            & Node.DOCUMENT_POSITION_FOLLOWING)};"
        "}")
    assert order["big_then_thumbs"], \
        "BUG-053: #mc-thumbs должен идти в DOM ПОСЛЕ #mc-big"
    assert order["thumbs_then_info"], \
        "BUG-053: #mc-info должен идти в DOM ПОСЛЕ #mc-thumbs (низ модалки)"

    # (в) длинный инструктивный form-note удален
    assert page.locator(
        "#m-car :text('открыть в большом окне')").count() == 0, \
        "BUG-053: длинного form-note быть не должно"

    # (г) большое окно крупнее: выше миниатюры (boundingBox-сравнение)
    big_box = page.locator("#mc-big").bounding_box()
    thumb_box = page.locator("#mc-thumbs .gal-thumb").first.bounding_box()
    assert big_box and thumb_box, "модалка отрисована без геометрии"
    assert big_box["height"] > thumb_box["height"], \
        (f"BUG-053: большое окно ({big_box['height']:.0f}px) должно быть "
         f"выше миниатюры ({thumb_box['height']:.0f}px)")
    assert big_box["height"] >= 320, \
        f"BUG-053: большое окно слишком низкое: {big_box['height']:.0f}px"


def test_s8_cars_and_docs_screens_have_no_widgets(page, server):
    """TC-UI-035 (change add-s8-cars-docs-booking, задача 6.1, FR-73):
    экраны «Мои автомобили» и «Мои документы» НЕ содержат ни одного из
    трех виджетов («привязанные ученики», «запросы учеников», «занятия
    на сегодня») — все скрыты при открытии раздела; главная «Мой день» —
    виджеты на месте (явные исключения Заказчика)."""
    _mock_instructor_shell(page, server)
    _route_json(page, server, "/api/instructor/cars", lambda req: (
        200, {"ok": True, "cars": []}))
    _route_json(page, server, "/api/instructor/documents", lambda req: (
        200, {"ok": True, "documents": [], "license": None,
              "license_hint": None}))

    page.goto(f"{server}/instructor/dashboard")
    widgets = page.locator(".widgets")
    # главная: виджеты видимы (grid)
    expect(widgets.locator("#w-students")).to_be_visible()
    expect(widgets.locator("#w-requests")).to_be_visible()
    expect(widgets.locator("#w-today")).to_be_visible()

    def _hidden(loc) -> bool:
        return loc.evaluate("el => getComputedStyle(el).display") == "none"

    # «Мои автомобили»: ни один из трех виджетов не отображен
    page.locator('.nav button[data-tab="Мои автомобили"]').click()
    expect(page.locator("#sec-cars")).to_be_visible()
    assert _hidden(widgets), "виджеты видны на экране «Мои автомобили» (FR-73)"

    # «Мои документы»: аналогично без виджетов
    page.locator('.nav button[data-tab="Профиль и документы"]').click()
    expect(page.locator("#sec-docs")).to_be_visible()
    assert _hidden(widgets), "виджеты видны на экране «Мои документы» (FR-73)"

    # главная кабинета — без изменений: виджеты вернулись
    page.locator('.nav button[data-tab="Мой день"]').click()
    expect(widgets.locator("#w-students")).to_be_visible()


def test_s8_admin_documents_verify_reject_preview_history(page, server):
    """TC-UI-036 (change add-s8-cars-docs-booking, задача 7.1, ОВ-1/ОВ-4;
    мокап admin-documents.html): админ-раздел «Документы» — ожидающие
    версии (ВУ с ФИО инструктора, СТС с авто+госномером и владельцем),
    фильтр по типу, ПРЕДПРОСМОТР — изображение открывается (naturalWidth > 0,
    запрос с X-Admin-Token), «Подтвердить» убирает строку (POST …/verify,
    строка в «Истории»), «Отклонить» — кнопка заблокирована без причины
    (ОВ-1), POST …/reject {reason}; серверная 422 показывается честно.
    API замокан по контракту design.md блок C (бэкенд-волна параллельна)."""
    _seed_session(page, "admin_token", ADMIN_TOKEN)
    _route_json(page, server, "/api/admin/users", lambda req: (
        200, {"users": [], "count": 0}))

    store = {
        "pending": [
            {"id": 61, "type": "license", "version": 2, "status": "pending",
             "uploaded_at": "2026-11-01 09:12:00", "decided_at": None,
             "reject_reason": None,
             "instructor_full_name": "Мищенко Светлана Андреевна"},
            {"id": 62, "type": "car_sts", "version": 2, "status": "pending",
             "uploaded_at": "2026-10-31 18:40:00", "decided_at": None,
             "reject_reason": None,
             "instructor_full_name": "Гордеева Анна Викторовна",
             "car": {"id": 33, "brand": "Kia", "model": "Rio",
                     "plate": "В 456 ВВ 777"}},
        ],
        "verified": [
            {"id": 71, "type": "license", "version": 1, "status": "verified",
             "uploaded_at": "2026-10-20 10:00:00",
             "decided_at": "2026-10-21 09:00:00", "reject_reason": None,
             "instructor_full_name": "Мищенко Светлана Андреевна"},
        ],
        "rejected": [
            {"id": 73, "type": "car_sts", "version": 2, "status": "rejected",
             "uploaded_at": "2026-10-28 10:00:00",
             "decided_at": "2026-10-29 09:00:00",
             "reject_reason": "Нечитаемый VIN",
             "instructor_full_name": "Белов Артём Дмитриевич",
             "car": {"id": 34, "brand": "Lada", "model": "Vesta",
                     "plate": "Е 789 ЕЕ 777"}},
        ],
    }
    verify_posts: list = []
    reject_posts: list = []
    preview_reqs: list = []
    reject_calls = {"n": 0}

    def _list(req):
        status = parse_qs(urlparse(req.url).query).get(
            "status", ["pending"])[0]
        return 200, {"ok": True, "documents": store.get(status, [])}

    def _verify(req):
        assert req.headers.get("x-admin-token") == ADMIN_TOKEN
        store["pending"] = [d for d in store["pending"] if d["id"] != 61]
        store["verified"].insert(0, dict(
            store["verified"][0], id=61, version=2, status="verified",
            uploaded_at="2026-11-01 09:12:00",
            decided_at="2026-11-02 10:00:00"))
        return 200, {"ok": True}

    def _reject(req):
        assert req.headers.get("x-admin-token") == ADMIN_TOKEN
        body = json.loads(req.post_data or "{}")
        reject_calls["n"] += 1
        if reject_calls["n"] == 1:
            # серверная страховка ОВ-1: 422 (фронт-флаг чинится текстом)
            return 422, {"ok": False, "error": "Причина отказа обязательна"}
        assert body.get("reason"), "reject без reason"
        store["pending"] = [d for d in store["pending"] if d["id"] != 62]
        store["rejected"].insert(0, {
            "id": 62, "type": "car_sts", "version": 2, "status": "rejected",
            "uploaded_at": "2026-10-31 18:40:00",
            "decided_at": "2026-11-02 10:05:00",
            "reject_reason": body["reason"],
            "instructor_full_name": "Гордеева Анна Викторовна",
            "car": {"id": 33, "brand": "Kia", "model": "Rio",
                    "plate": "В 456 ВВ 777"}})
        return 200, {"ok": True}

    _route_json(page, server, "/api/admin/documents", _list)
    _route_json(page, server, "/api/admin/documents/61/verify", _verify,
                method="POST", capture=verify_posts)
    _route_json(page, server, "/api/admin/documents/62/reject", _reject,
                method="POST", capture=reject_posts)
    _route_png(page, server, "/api/admin/documents/61/file", preview_reqs)
    _route_png(page, server, "/api/admin/documents/62/file")

    page.goto(f"{server}/admin-dashboard")
    page.locator(".nav button", has_text="Документы").click()
    expect(page.locator("#sec-documents")).to_be_visible()

    # --- ожидающие версии: тип, ФИО (ВУ) / авто+госномер и владелец (СТС) ---
    lic_row = page.locator("#dc-list .dc-row", has_text="Мищенко")
    sts_row = page.locator("#dc-list .dc-row", has_text="В 456 ВВ 777")
    expect(lic_row).to_have_count(1)
    expect(sts_row).to_have_count(1)
    expect(lic_row.locator(".dc-type")).to_have_text("ВУ")
    expect(sts_row.locator(".dc-type")).to_have_text("СТС")
    expect(sts_row).to_contain_text("Kia Rio · В 456 ВВ 777")
    expect(sts_row).to_contain_text("Гордеева Анна Викторовна")
    expect(page.locator("#dc-count")).to_contain_text("Ожидающих версий: 2")

    # --- фильтр по типу: только СТС ---
    page.locator('#dc-filters button[data-f="sts"]').click()
    expect(page.locator("#dc-list .dc-row")).to_have_count(1)
    expect(page.locator("#dc-count")).to_contain_text("Ожидающих версий: 1")
    page.locator('#dc-filters button[data-f="all"]').click()
    expect(page.locator("#dc-list .dc-row")).to_have_count(2)

    # --- предпросмотр: изображение ОТКРЫВАЕТСЯ (ОВ-4) ---
    lic_row.locator(".dc-thumb").click()
    expect(page.locator("#dc-view")).to_be_visible()
    pv = page.locator("#dc-view-full img")
    expect(pv).to_be_visible()
    assert pv.evaluate("el => el.naturalWidth") > 0, \
        "предпросмотр документа не открылся (ОВ-4)"
    assert preview_reqs and preview_reqs[0].headers.get(
        "x-admin-token") == ADMIN_TOKEN
    page.locator("#dc-view-close").click()
    expect(page.locator("#dc-view")).to_be_hidden()

    # --- Подтвердить: POST verify, строка уходит, история пополняется ---
    lic_row.locator("[data-approve]").click()
    expect(page.locator("#ac-toast")).to_contain_text("подтверждена")
    assert len(verify_posts) == 1
    assert verify_posts[0].url.endswith("/api/admin/documents/61/verify")
    assert verify_posts[0].method == "POST"
    expect(page.locator("#dc-list .dc-row", has_text="Мищенко")).to_have_count(0)
    expect(page.locator("#dc-count")).to_contain_text("Ожидающих версий: 1")
    page.locator('#dc-tabs button[data-tab="history"]').click()
    # в истории теперь обе версии Мищенко (v1 из seed + подтвержденная v2)
    hist_61 = page.locator("#dc-list .dc-row", has_text="Мищенко")
    expect(hist_61).to_have_count(2)
    # свежая сверху (sorted by decided_at desc) — подтвержденная замена
    expect(hist_61.first.locator(".dc-badge")).to_have_text("Подтверждено")

    # --- Отклонить: причина ОБЯЗАТЕЛЬНА (ОВ-1), 422-страховка честно ---
    page.locator('#dc-tabs button[data-tab="pending"]').click()
    sts_row = page.locator("#dc-list .dc-row", has_text="В 456 ВВ 777")
    sts_row.locator("[data-opendeny]").click()
    expect(page.locator("#dc-deny")).to_be_visible()
    deny_go = page.locator("#dc-deny-go")
    expect(deny_go).to_be_disabled()
    page.fill("#dc-reason", "   ")  # только пробелы — всё еще блокировано
    expect(deny_go).to_be_disabled()
    page.fill("#dc-reason", "Фото нечитаемо: VIN размыт")
    expect(deny_go).to_be_enabled()
    deny_go.click()
    # первая попытка: сервер вернул 422 — текст показан честно, модалка открыта
    expect(page.locator("#ac-toast")).to_contain_text(
        "Причина отказа обязательна")
    expect(page.locator("#dc-deny")).to_be_visible()
    assert reject_calls["n"] == 1 and len(reject_posts) == 1
    # повторный клик с той же причиной — сервер принял
    deny_go.click()
    expect(page.locator("#dc-deny")).to_be_hidden()
    assert reject_calls["n"] == 2
    assert json.loads(reject_posts[1].post_data) == {
        "reason": "Фото нечитаемо: VIN размыт"}
    # строка ушла из ожидающих; в истории — с причиной отказа
    expect(page.locator("#dc-count")).to_contain_text("Ожидающих версий: 0")
    expect(page.locator("#dc-empty")).to_be_visible()
    page.locator('#dc-tabs button[data-tab="history"]').click()
    hist_62 = page.locator("#dc-list .dc-row", has_text="В 456 ВВ 777")
    expect(hist_62).to_have_count(1)
    expect(hist_62.locator(".dc-badge")).to_have_text("Отклонено")
    expect(hist_62).to_contain_text("Фото нечитаемо: VIN размыт")


def test_s8_student_my_bookings_car_card_with_photo(browser, server):
    """TC-UI-037 (change add-s8-cars-docs-booking, «Мои брони» ученика):
    карточка авто инструктора с ФОТО РЯДОМ СО СЛОТАМИ (контракт Спринта 7/8:
    photo_url брони/пары загружается авторизованно с X-Session-Token,
    изображение реально открыто — naturalWidth > 0; карточка выше сетки
    слотов; бейдж статуса авто «Проверено»). API замокан через page.route
    (бэкенд-волна параллельна) — шейпы backend/student_marketplace.py и
    backend/booking.py."""
    stu_ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = stu_ctx.new_page()
    page.add_init_script(
        "sessionStorage.setItem('session_token','%s');" % "ui-s8-stu-token")
    photo_reqs: list = []
    car = {"id": 11, "brand": "Škoda", "model": "Rapid", "year": 2020,
           "transmission": "automatic", "car_status": "validated",
           "photo_url": "/api/instructor/cars/11/photo/front"}

    _route_json(page, server, "/api/auth/me", lambda req: (
        200, {"ok": True, "user": {"surname": "Смирнова", "name": "Ольга"}}))
    _route_json(page, server, "/api/student/requests", lambda req: (
        200, {"ok": True, "requests": [
            {"id": 301, "status": "accepted",
             "created_at": "2026-10-02 10:00:00",
             "decided_at": "2026-10-03 10:00:00", "instructor_id": 7,
             "instructor_full_name": "Громов Борис Арсеньевич",
             "deny_comment": None, "car": car},
        ]}))
    _route_json(page, server, "/api/student/instructors/7/slots",
                lambda req: (
                    200, {"ok": True, "slots": [
                        {"id": 55, "weekday": 3, "start_time": "14:00",
                         "end_time": "16:00", "state": "free"}]}))
    _route_json(page, server, "/api/student/bookings", lambda req: (
        200, {"ok": True, "bookings": [
            {"id": 71, "status": "confirmed", "weekday": 3,
             "lesson_date": "2026-11-05", "start_time": "14:00",
             "end_time": "16:00",
             "instructor_full_name": "Громов Борис Арсеньевич",
             "reject_comment": None, "car": car},
        ]}))
    _route_png(page, server, "/api/instructor/cars/11/photo/front",
               photo_reqs)

    try:
        page.goto(f"{server}/cabinet#/my-bookings")
        expect(page.locator("#sec-bookings")).to_be_visible()
        # карточка авто инструктора с фото рядом со слотами
        card = page.locator("#bk-car-card")
        expect(card).to_be_visible()
        expect(page.locator("#bk-car-name")).to_have_text(
            "Škoda Rapid 2020 · автомат")
        expect(card.locator(".car-badge")).to_have_text("Проверено")
        img = card.locator(".bk-car-photo img")
        expect(img).to_be_visible()
        assert img.evaluate("el => el.naturalWidth") > 0, \
            "фото авто не открылось (карточка у слотов)"
        assert photo_reqs and photo_reqs[0].headers.get(
            "x-session-token"), "фото запрошено без сессии ученика"
        # РЯДОМ СО СЛОТАМИ: карточка — первый блок календаря, выше сетки слотов
        cal = page.locator("#bk-grid")
        expect(cal).to_be_visible()
        card_box, cal_box = card.bounding_box(), cal.bounding_box()
        assert card_box["y"] + card_box["height"] <= cal_box["y"] + 1, \
            "карточка авто не рядом со слотами"
        # брони: подтвержденная с авто
        bk = page.locator(".bk-req").first
        expect(bk.locator(".bk-status")).to_have_text("Подтверждена")
        expect(bk).to_contain_text("Škoda Rapid")
    finally:
        stu_ctx.close()


# =========================================================================
# TC-UI-038 — задача 8.1 (FR-74): «Бронирования» удалены, запросы/брони
# и решения — на слотах календаря, #/bookings — редирект в календарь.
# =========================================================================

def test_s8_bookings_section_removed_redirect_and_slot_reject(page, server):
    """TC-UI-038 (change add-s8-cars-docs-booking, задача 8.1, FR-74):
    раздел «Бронирования» удален БЕЗ остатков — пункта меню нет, секции
    #sec-bookings в DOM нет; старая ссылка #/bookings редиректит в раздел
    «Календарь» (механика BUG-047: хеш очищен, «Календарь» активен). Запрос
    ученика виден РОВНО на выбранном им слоте (Ср 14:00–16:00; соседние слоты
    чистые) с кнопками решений на слоте; отклонение требует комментария
    (кнопка заблокирована без него) и шлет POST …/reject {comment} — слот
    освобождается. API замокан через page.route (бэкенд не задействован)."""
    _mock_instructor_shell(page, server)
    state = {"bookings": [{
        "id": 91, "status": "new", "weekday": 2,
        "lesson_date": "2026-11-02", "start_time": "14:00",
        "end_time": "16:00", "student_full_name": "Крылова Дарья Игоревна",
        "reject_comment": None,
        "car": {"id": 52, "brand": "Škoda", "model": "Rapid", "year": 2020,
                "transmission": "automatic"},
    }]}
    reject_posts: list = []

    def _bookings(req):
        return 200, {"ok": True, "bookings": list(state["bookings"])}

    _route_json(page, server, "/api/instructor/availability", lambda req: (
        200, {"ok": True, "intervals": [
            {"weekday": 2, "start_time": "14:00", "end_time": "16:00"},
            {"weekday": 2, "start_time": "16:00", "end_time": "18:00"}]}))
    _route_json(page, server, "/api/instructor/bookings", _bookings)
    _route_json(page, server, "/api/instructor/bookings/91/reject",
                lambda req: (
                    state["bookings"].clear() or (200, {"ok": True})),
                method="POST", capture=reject_posts)

    # --- старая ссылка #/bookings: редирект в календарь, остатков нет ---
    page.goto(f"{server}/instructor/dashboard#/bookings")
    expect(page.locator("#sec-calendar")).to_be_visible()
    assert page.locator("#sec-bookings").count() == 0, \
        "FR-74: секции «Бронирования» не должно быть в DOM"
    assert page.locator('.nav button[data-tab="Бронирования"]').count() == 0, \
        "FR-74: пункта меню «Бронирования» не должно быть в сайдбаре"
    expect(page.locator('.nav button[data-tab="Календарь"]')).to_have_class(
        "active")
    expect(page.locator("#page-title")).to_have_text("Календарь")
    assert page.url.endswith("/instructor/dashboard"), \
        f"хеш #/bookings не очищен редиректом: {page.url}"

    # --- запрос РОВНО на слоте Ср 14:00–16:00 (соседний 16:00–18:00 чист) ---
    req = page.locator("#cal-grid .cal-slot.reqslot")
    expect(req).to_have_count(1)
    assert req.get_attribute("data-k") == "2-14", req.get_attribute("data-k")
    expect(req.locator("small")).to_have_text("Крылова Дарья Игоревна")
    assert page.locator("#cal-grid .cal-slot[data-k='2-16']").get_attribute(
        "class") == "cal-slot on", "соседний слот помечен чужим запросом"

    # --- решение на слоте: отклонение требует комментария (ОВ-2) ---
    req.click()
    expect(page.locator("#m-bk")).to_be_visible()
    expect(page.locator("#bk-slot-who")).to_have_text("Крылова Дарья Игоревна")
    page.locator("#bk-slot-reject-btn").click()
    expect(page.locator("#bk-slot-reject-go")).to_be_disabled()
    page.fill("#bk-slot-reason", "   ")  # только пробелы — всё еще блокировано
    expect(page.locator("#bk-slot-reject-go")).to_be_disabled()
    page.fill("#bk-slot-reason", "В это время пересдача экзамена в ГИБДД")
    expect(page.locator("#bk-slot-reject-go")).to_be_enabled()
    page.locator("#bk-slot-reject-go").click()
    expect(page.locator("#toast")).to_contain_text("Запрос отклонён")
    assert len(reject_posts) == 1
    assert reject_posts[0].url.endswith("/api/instructor/bookings/91/reject")
    assert json.loads(reject_posts[0].post_data) == {
        "comment": "В это время пересдача экзамена в ГИБДД"}
    # календарь перезагружен: метки запроса нет, слот снова в графике
    expect(page.locator("#cal-grid .cal-slot.reqslot")).to_have_count(0)
    expect(page.locator("#cal-grid .cal-slot[data-k='2-14']")).to_have_class(
        "cal-slot on")


# =========================================================================
# TC-UI-041 — BUG-052: после сноса унаследованного bk-block в «Календаре»
# ровно одна сетка (.cal-grid), единственная поверхность решений — слот
# календаря + модалка #m-bk (отклонение с обязательной причиной).
# =========================================================================

def test_bug052_calendar_single_grid_slot_reject_via_modal(page, server):
    """TC-UI-041 (BUG-052): в #sec-calendar РОВНО ОДНА сетка (.cal-grid) —
    унаследованный bk-block (#bk-list/#bk-grid/#bk-filters/.bk-block)
    отсутствует. Решение по запросу ученика — клик по слоту с запросом:
    открывается #m-bk, «✕ Отклонить…» → обязательный комментарий →
    «✕ Отклонить запрос» → тост «Запрос отклонён», POST …/reject {comment},
    слот освобождается (метка запроса снята, слот снова в графике). Моки
    как в TC-UI-038 (API замокан через page.route, бэкенд не задействован)."""
    _mock_instructor_shell(page, server)
    state = {"bookings": [{
        "id": 91, "status": "new", "weekday": 2,
        "lesson_date": "2026-11-02", "start_time": "14:00",
        "end_time": "16:00", "student_full_name": "Крылова Дарья Игоревна",
        "reject_comment": None,
        "car": {"id": 52, "brand": "Škoda", "model": "Rapid", "year": 2020,
                "transmission": "automatic"},
    }]}
    reject_posts: list = []

    def _bookings(req):
        return 200, {"ok": True, "bookings": list(state["bookings"])}

    _route_json(page, server, "/api/instructor/availability", lambda req: (
        200, {"ok": True, "intervals": [
            {"weekday": 2, "start_time": "14:00", "end_time": "16:00"},
            {"weekday": 2, "start_time": "16:00", "end_time": "18:00"}]}))
    _route_json(page, server, "/api/instructor/bookings", _bookings)
    _route_json(page, server, "/api/instructor/bookings/91/reject",
                lambda req: (
                    state["bookings"].clear() or (200, {"ok": True})),
                method="POST", capture=reject_posts)

    page.goto(f"{server}/instructor/dashboard")
    page.locator('.nav button[data-tab="Календарь"]').click()
    expect(page.locator("#sec-calendar")).to_be_visible()

    # --- МИШУРА: ровно одна сетка, bk-block снесен без остатков ---
    assert page.locator("#sec-calendar .cal-grid").count() == 1, \
        "BUG-052: в #sec-calendar ровно одна (слотовая) сетка .cal-grid"
    for dead in ("#bk-list", "#bk-grid", "#bk-filters", ".bk-block"):
        assert page.locator(f"#sec-calendar {dead}").count() == 0, \
            f"BUG-052: {dead} не должен остаться в #sec-calendar"

    # --- запрос РОВНО на слоте Ср 14:00–16:00 ---
    req = page.locator("#cal-grid .cal-slot.reqslot")
    expect(req).to_have_count(1)
    assert req.get_attribute("data-k") == "2-14", req.get_attribute("data-k")
    expect(req.locator("small")).to_have_text("Крылова Дарья Игоревна")

    # --- решение: клик по слоту → #m-bk → отклонение с причиной ---
    req.click()
    expect(page.locator("#m-bk")).to_be_visible()
    expect(page.locator("#bk-slot-who")).to_have_text("Крылова Дарья Игоревна")
    page.locator("#bk-slot-reject-btn").click()
    expect(page.locator("#bk-slot-reject-go")).to_be_disabled()  # без причины
    page.fill("#bk-slot-reason", "В это время пересдача экзамена в ГИБДД")
    expect(page.locator("#bk-slot-reject-go")).to_be_enabled()
    page.locator("#bk-slot-reject-go").click()
    expect(page.locator("#toast")).to_contain_text("Запрос отклонён")
    assert len(reject_posts) == 1
    assert reject_posts[0].url.endswith("/api/instructor/bookings/91/reject")
    assert json.loads(reject_posts[0].post_data) == {
        "comment": "В это время пересдача экзамена в ГИБДД"}
    # слот освобожден: метки запроса нет, слот снова в графике
    expect(page.locator("#cal-grid .cal-slot.reqslot")).to_have_count(0)
    expect(page.locator("#cal-grid .cal-slot[data-k='2-14']")).to_have_class(
        "cal-slot on")


# =========================================================================
# TC-UI-039 — задача 9.2 (FR-75/ОВ-5): «Мои ученики» — карточки со
# счетчиками (данные GET /api/instructor/students, задача 9.1 — мок),
# «Запросы учеников» — подраздел-вкладка внутри раздела.
# =========================================================================

def test_s8_my_students_cards_counters_and_requests_subtab(page, server):
    """TC-UI-039 (change add-s8-cars-docs-booking, задача 9.2, FR-75/ОВ-5;
    мокап my-students.html): раздел «Мои ученики» — карточки принятых пар по
    контракту GET /api/instructor/students (задача 9.1): ФИО, следующее
    плановое занятие (или «нет»), счетчики «плановых занятий дальше /
    проведено» — ТОЛЬКО confirmed; пустые состояния (нет пар; пара без
    броней — «нет», 0/0). «Запросы учеников» — подраздел-ВКЛАДКА внутри
    раздела, отдельного пункта сайдбара нет; после принятия запроса ученик
    появляется в основном списке. XSS-гигиена: данные API — createElement +
    textContent (теги в ФИО не исполняются). API замокан через page.route
    (бэкенд-волна 9.1 параллельна)."""
    _mock_instructor_shell(page, server)
    state = {"students": [
        {"student_id": 701, "full_name": "Ежов Павел Дмитриевич",
         "next_lesson": {"date": "2026-11-03", "time": "14:00"},
         "planned_count": 2, "completed_count": 5},
        {"student_id": 702, "full_name": 'Титова <img src=x onerror="window.__xss=1">',
         "next_lesson": None, "planned_count": 0, "completed_count": 0},
    ]}

    def _students(req):
        return 200, {"ok": True, "students": list(state["students"])}

    _route_json(page, server, "/api/instructor/students", _students)
    _route_json(page, server, "/api/instructor/requests", lambda req: (
        200, {"ok": True, "requests": [
            {"id": 301, "status": "new", "created_at": "2026-10-15 09:14:00",
             "decided_at": None, "student_full_name": "Сафин Артур Кириллович",
             "student_experience_years": 0, "car": None}]}))
    _route_json(page, server, "/api/instructor/cars", lambda req: (
        200, {"ok": True, "cars": [
            {"id": 52, "brand": "Škoda", "model": "Rapid", "year": 2020,
             "transmission": "automatic", "plate": "А 123 АА 777"}]}))
    _route_json(page, server, "/api/instructor/requests/301/accept",
                lambda req: (
                    state["students"].insert(0, {
                        "student_id": 703,
                        "full_name": "Сафин Артур Кириллович",
                        "next_lesson": None,
                        "planned_count": 0, "completed_count": 0})
                    or (200, {"ok": True})),
                method="POST")

    page.goto(f"{server}/instructor/dashboard")
    page.locator('.nav button[data-tab="Мои ученики"]').click()
    expect(page.locator("#sec-students")).to_be_visible()
    assert page.locator('.nav button[data-tab="Запросы учеников"]').count() == 0, \
        "ОВ-5: отдельного пункта сайдбара «Запросы учеников» быть не должно"

    # --- карточки: следующее занятие, счетчики, пустое состояние пары ---
    cards = page.locator("#stu-cards .student")
    expect(cards).to_have_count(2)
    expect(page.locator("#stu-n")).to_have_text("·2")
    c1 = page.locator("#stu-cards .student", has_text="Ежов Павел Дмитриевич")
    expect(c1.locator(".stu-next")).to_contain_text("03.11.2026 · 14:00")
    expect(c1.locator(".stu-cnt b").nth(0)).to_have_text("2")
    expect(c1.locator(".stu-cnt span").nth(0)).to_have_text(
        "плановых занятий дальше")
    expect(c1.locator(".stu-cnt b").nth(1)).to_have_text("5")
    expect(c1.locator(".stu-cnt span").nth(1)).to_have_text("проведено")
    c2 = page.locator("#stu-cards .student", has_text="Титова")
    expect(c2.locator(".stu-next.none")).to_contain_text(
        "нет — подтверждённых броней впереди не запланировано")
    expect(c2.locator(".stu-cnt b").nth(0)).to_have_text("0")
    expect(c2.locator(".stu-cnt b").nth(1)).to_have_text("0")
    # XSS-гигиена: ФИО с тегом отрисовано текстом — img не создан, скрипт не был
    assert page.locator("#stu-cards img").count() == 0, \
        "данные API попали в HTML (XSS-гигиена нарушена)"
    assert page.evaluate("window.__xss === undefined"), "onerror исполнился"

    # --- подраздел «Запросы учеников» — вкладка по требованию (ОВ-5) ---
    page.locator('#stu-tabs button[data-stu="requests"]').click()
    expect(page.locator("#stu-tab-requests")).to_be_visible()
    expect(page.locator("#stu-tab-students")).to_be_hidden()
    expect(page.locator(".rq")).to_have_count(1)
    expect(page.locator("#stu-req-n")).to_have_text("·1")
    expect(page.locator("#rq-new-n")).to_have_text("·1")

    # --- принятие запроса: ученик появляется в основном списке (9.2) ---
    page.locator("[data-accept='301']").click()
    expect(page.locator("#rq-accept-301")).to_be_visible()
    page.locator("[data-confirm='301']").click()
    expect(page.locator("#toast")).to_contain_text("Заявка принята")
    expect(page.locator("#stu-cards .student")).to_have_count(3)
    expect(page.locator("#stu-cards .student").first).to_contain_text(
        "Сафин Артур Кириллович")
    expect(page.locator("#stu-n")).to_have_text("·3")


def test_s8_my_students_missing_backend_honest_error(page, server):
    """TC-UI-039b (change add-s8-cars-docs-booking, задача 9.2): бэкенд 9.1
    недоступен (GET /api/instructor/students → 404) — раздел «Мои ученики»
    показывает ЧЕСТНУЮ ошибку (блок + тост), НЕ подменяя ее пустым списком
    («Учеников пока нет» скрыт, карточек нет)."""
    _mock_instructor_shell(page, server)
    _route_json(page, server, "/api/instructor/students", lambda req: (
        404, {"ok": False, "error": "Not Found"}))

    page.goto(f"{server}/instructor/dashboard")
    page.locator('.nav button[data-tab="Мои ученики"]').click()
    expect(page.locator("#sec-students")).to_be_visible()
    err = page.locator("#stu-error")
    expect(err).to_be_visible()
    expect(err).to_contain_text("Не удалось загрузить учеников")
    expect(page.locator("#stu-empty")).to_be_hidden()
    assert page.locator("#stu-cards .student").count() == 0


# --------- Спринт 9: пилот Vue /instructors/pending + polling (задача 5.1,
# change add-vue-framework-pilot; контракт опроса — change
# add-application-status-polling, design.md «Машина состояний экрана»).
# Смоук network-инспекцией: page.route-моки API + capture-счетчики запросов;
# интервал/остановка таймера — page.clock (виртуальные таймеры: детерминно,
# без реальных 12-с ожиданий). time.sleep запрещен — паузы через
# page.wait_for_timeout (qa-pipeline). Схема интервалов — детерминированная:
# clock.install(time=BASE) + pause_at(BASE+11с) (тиков быть не должно) +
# run_for(2000) (пересекаем 12-ю секунду — ровно один следующий тик);
# сразу после тика даем цепочке ответа (r.json → armTimer) завершиться
# реальным сеттлом, прежде чем двигать виртуальное время (гонка
# run_for-драйвера с ответом в полете недетерминированна).

import datetime

CLOCK_BASE = datetime.datetime(2024, 1, 1, 10, 0, 0)

POLL_SEED_TOKEN = "ui-poll-token-0f1e2d3c4b5a6978"
EXCH_SEED_TOKEN = "ui-exch-token-9a8b7c6d5e4f3210"


def _seed_application_tokens(page) -> None:
    """Положить application_poll_token / application_exchange_token в
    localStorage ДО скриптов страницы (как их оставляет apply.js после
    сабмита анкеты, frontend/js/apply.js:84-85).

    Сторож в sessionStorage: init-скрипт переисполняется на каждой
    навигации (редирект кабинета, back-навигация) и НЕ должен
    восстанавливать токены, удаленные самой страницей (MAJ-1) — иначе
    проверка «возврат → STATIC, 0 запросов» была бы ложной.
    """
    page.add_init_script(
        "if(!sessionStorage.getItem('ui-app-tokens-seeded')){"
        f"localStorage.setItem('application_poll_token','{POLL_SEED_TOKEN}');"
        f"localStorage.setItem('application_exchange_token','{EXCH_SEED_TOKEN}');"
        "sessionStorage.setItem('ui-app-tokens-seeded','1');}")


def _wait_until(page, predicate, timeout_s: float = 6.0) -> bool:
    """Дождаться условия через события браузера. time.sleep запрещен
    (qa-pipeline): пауза — page.wait_for_timeout, она же прокачивает
    event-loop sync-API (доставка route-событий без нее не происходит)."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if predicate():
            return True
        page.wait_for_timeout(25)
    return predicate()


def _assert_stable(page, getter, expected, settle_s: float = 1.5) -> None:
    """Негативная проверка «дальше запросов нет»: в течение settle_s
    значение не меняется (rogue-тик проявился бы за миллисекунды)."""
    deadline = time.monotonic() + settle_s
    while time.monotonic() < deadline:
        assert getter() == expected, (
            f"ожидалось стабильно {expected}, фактически {getter()}")
        page.wait_for_timeout(30)
    assert getter() == expected


def _route_dashboard_ok(page, server) -> None:
    """Заглушки сессионного контура кабинета после бесшовного обмена:
    /api/auth/me → {ok:true} (иначе dashboard-instructor.js:21 делает
    location.href='/' на 401 — редирект ломает проверку состояния), а
    /api/instructor/** → {ok:true} (рендер кабинета вне объема смоука —
    достаточно, чтобы не было toLogin). Конкретные моки статуса/обмена
    регистрируются ПОСЛЕ и перекрывают по правилу «последний важнее»."""
    page.route(
        f"{server}/api/auth/me*",
        lambda route: route.fulfill(
            status=200, content_type="application/json",
            body='{"ok": true, "user": {"role": "instructor"}}'))
    page.route(
        f"{server}/api/instructor/**",
        lambda route: route.fulfill(
            status=200, content_type="application/json", body='{"ok": true}'))




def test_zz_modal_reopen_on_section_return(page, server):
    _seed_session(page, "session_token", INSTRUCTOR_TOKEN)
    def _docs(req):
        docs = [_doc_sts(52, "Škoda", "Rapid", "А 123 АА 777")]
        return 200, {"ok": True, "documents": docs, "license": None, "license_hint": None}
    def _cars(req):
        cars = [{"id": 52, "brand": "Škoda", "model": "Rapid", "year": 2020,
                 "transmission": "automatic", "plate": "А 123 АА 777",
                 "status": "validated", "photos": {}, "has_sts": True,
                 "sts_url": None, "created_at": "2026-10-02 12:00:00"}]
        return 200, {"ok": True, "cars": cars}
    _route_json(page, server, "/api/instructor/documents", _docs)
    _route_json(page, server, "/api/instructor/cars", _cars)
    for a in ("front","rear","left","right","interior","sts"):
        _route_png(page, server, f"/api/instructor/cars/52/photo/{a}")
    _route_png(page, server, "/api/instructor/documents/sts-52/file")

    page.goto(f"{server}/instructor/dashboard")
    page.locator('.nav button[data-tab="Мои автомобили"]').click()
    page.locator(".car", has_text="Škoda Rapid").click()
    expect(page.locator("#m-car")).to_be_visible()
    st1 = page.locator("#m-car").evaluate("el => ({cls: el.className, vis: getComputedStyle(el).display})")
    print(f"\n1) модалка открыта: {st1}")

    # шаг 3: уйти в другой раздел (Календарь)
    page.locator('.nav button[data-tab="Календарь"]').click()
    page.wait_for_timeout(400)
    st2 = page.locator("#m-car").evaluate("el => ({cls: el.className, vis: getComputedStyle(el).display})")
    print(f"2) после ухода в «Календарь»: {st2}")

    # шаг 4: вернуться в «Мои автомобили»
    page.locator('.nav button[data-tab="Мои автомобили"]').click()
    page.wait_for_timeout(400)
    st3 = page.locator("#m-car").evaluate("el => ({cls: el.className, vis: getComputedStyle(el).display})")
    sec = page.locator("#sec-cars").evaluate("el => getComputedStyle(el).display")
    print(f"3) после возврата в «Мои автомобили»: модалка {st3}, секция display={sec}")
