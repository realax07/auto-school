"""TC-REG-016…TC-REG-018, TC-NFR-003 — статика, health, макеты, секреты
# Change: add-registration-admin
(задача 4.2, sdd.md §2, §3.5–§3.6).

GET /, /registered, /admin-login, /admin-dashboard → 200;
GET /api/health → 200 {"ok": true}. Браузерная часть TC-REG-016/017
(Playwright) — вне TestClient: здесь API/статический срез кейсов.
"""
import bcrypt
import pytest

from conftest import ROOT, register, valid_body

PAGES = {
    "/": "СберАвтошкола",
    "/registered": "Регистрация завершена",
    "/admin-login": "Админка",
    "/admin-dashboard": "Пользователи",
}


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_USER", "admin")
    monkeypatch.setenv(
        "ADMIN_PASSWORD_HASH",
        bcrypt.hashpw(b"x", bcrypt.gensalt()).decode(),
    )
    monkeypatch.setenv("SECRET", "test-secret")
    monkeypatch.setenv("AUTOSCHOOL_DB_PATH", str(tmp_path / "app.db"))
    monkeypatch.chdir(ROOT)  # статика ищется относительно корня репозитория
    from fastapi.testclient import TestClient

    from backend.app import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize("path,marker", sorted(PAGES.items()))
def test_tc_reg_018_static_pages_return_200_with_mock_texts(client, path, marker):
    """TC-REG-018 (шаг 4, выборочная браузерная сверка через TestClient):
    каждая страница отдает 200 и несет заголовок/текстовку, посимвольно
    совпадающую с design/mocks («СберАвтошкола», «Регистрация завершена»,
    «Админка», «Пользователи»); побайтовый diff с макетами — вне
    автотеста (D9: FR-9 принят как мануальная проверка + wiring)."""
    resp = client.get(path)
    assert resp.status_code == 200, path
    assert marker in resp.text, path


def test_tc_reg_018_register_modal_has_password_fields_wiring(client):
    """TC-REG-018 (шаг 3, контроль wiring): в модалке регистрации
    присутствуют предписанные отличия от макета — поля Пароль/Подтверждение
    (id reg-password / reg-password-confirm)."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'id="reg-password"' in resp.text
    assert 'id="reg-password-confirm"' in resp.text
    assert "Подтверждение" in resp.text


def test_tc_reg_016_health_and_registered_page_available(client):
    """TC-REG-016 (API-срез): после успешной регистрации (200 {ok:true})
    страница /registered доступна и показывает «Регистрация завершена»;
    запись создана в users. Сам переход из модалки (браузерный шаг) —
    Playwright/ручной прогон."""
    assert client.get("/api/health").json() == {"ok": True}
    resp = client.post("/api/register", json=valid_body())
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}

    page = client.get("/registered")
    assert page.status_code == 200
    assert "Регистрация завершена" in page.text

    import os
    import sqlite3

    conn = sqlite3.connect(os.environ["AUTOSCHOOL_DB_PATH"])
    n = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    assert n == 1


def test_tc_reg_017_rejected_registration_no_redirect_target(client):
    """TC-REG-017 (API-срез): отклоненная регистрация (email без «@»)
    возвращает контрактный 422 с текстом причины «Email: …» — редиректа
    на /registered нет (редирект выполняет JS только при {ok:true});
    COUNT(*) = 0. Браузерные шаги (модалка, URL) — Playwright/ручной
    прогон."""
    resp = client.post(
        "/api/register", json=valid_body(email="ivanov.example")
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["ok"] is False
    assert data["error"].startswith("Email")
    assert "detail" not in data

    import os
    import sqlite3

    conn = sqlite3.connect(os.environ["AUTOSCHOOL_DB_PATH"])
    n = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    assert n == 0


def test_tc_reg_018_health_endpoint(client):
    """TC-REG-018 (инфраструктура предусловий): GET /api/health → 200
    {"ok": true} — контроль живости из предусловий approved-кейсов."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_tc_reg_016_lifespan_initializes_db(client):
    """TC-REG-016 (предусловие): init_db через lifespan — таблица users
    существует после старта приложения («БД инициализирована при
    старте»)."""
    import os
    import sqlite3

    conn = sqlite3.connect(os.environ["AUTOSCHOOL_DB_PATH"])
    names = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchall()
    ]
    conn.close()
    assert names == ["users"]


# --- TC-NFR-003: секреты в .env (git только на чтение) -----------------------


def test_tc_nfr_003_env_gitignored_and_example_present():
    """TC-NFR-003: Секреты в .env; .env в .gitignore; .env.example в
    репозитории с ADMIN_USER, ADMIN_PASSWORD_HASH, SECRET и инструкцией
    генерации bcrypt-хэша (git — только чтение: check-ignore / grep)."""
    import subprocess

    # 1. .env игнорируется (если локально существует; в чистой checkout —
    #    правило игнорирования должно быть в .gitignore)
    ignored = subprocess.run(
        ["git", "check-ignore", ".env"], capture_output=True, text=True
    )
    env_exists = (ROOT / ".env").is_file()
    if env_exists:
        assert ignored.returncode == 0, ".env не игнорируется git"
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore

    # 2. .env.example описывает все три переменные + инструкцию генерации
    example = (ROOT / ".env.example").read_text(encoding="utf-8")
    for var in ("ADMIN_USER", "ADMIN_PASSWORD_HASH", "SECRET"):
        assert var in example, var
    assert "bcrypt" in example  # инструкция генерации хэша

    # 3. фактическое значение ADMIN_PASSWORD_HASH из .env не в отслеживаемых
    #    файлах (0 вхождений); имя переменной — только в .env.example и доке
    if env_exists:
        real_hash = ""
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if line.startswith("ADMIN_PASSWORD_HASH="):
                real_hash = line.split("=", 1)[1].strip()
        if real_hash:
            grep = subprocess.run(
                ["git", "grep", "-F", real_hash],
                capture_output=True,
                text=True,
                cwd=ROOT,
            )
            assert grep.returncode != 0, "значение хэша в отслеживаемых файлах"
