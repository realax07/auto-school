"""TC-AUTH — wiring модалки входа на лендинге (задача 2.2, sdd.md §9, §10.1, §10.4)
# Change: add-auth-cabinet
# FR: FR-1, FR-2, FR-4, FR-9

Маршрут /api/auth/login в app.py на момент 2.2 еще не подключен (задача 3.1),
поэтому проверяется статика и wiring-фрагменты frontend/index.html:
fetch POST /api/auth/login, сохранение токена в sessionStorage['session_token'],
редирект /cabinet при ok, единое сообщение об ошибке под формой при 401;
тексты модалки m-login — дословно по мокапу. Браузерный сабмит (реальный
fetch + редирект) — вне TestClient (как TC-REG-016/017 в test_static.py).
"""
from conftest import ROOT

INDEX = ROOT / "frontend" / "index.html"

# Ключевые строки мокапа модалки «Вход» (design/mocks) — тексты дословно
LOGIN_MODAL_TEXTS = [
    '<div class="overlay" id="m-login"><div class="modal" role="dialog" aria-label="Вход">',
    "<h2>Вход</h2><p class=\"sub\">Войдите в личный кабинет</p>",
    "<label>Логин</label>",
    'placeholder="email или телефон"',
    "<label>Пароль</label>",
    "placeholder=\"••••••••\"",
]

# Wiring-обязательства задачи 2.2 (sdd §10.1, §10.4; решение ПМ по 2.1 —
# ключ sessionStorage именно session_token)
WIRING_FRAGMENTS = [
    "fetch('/api/auth/login'",                       # POST /api/auth/login
    "sessionStorage.setItem('session_token'",        # ключ session_token
    "location.href='/cabinet'",                      # редирект на кабинет
    "err.textContent=",                              # вывод ошибки под формой
]


def test_tc_auth_login_modal_texts_verbatim():
    """Готовность 2.2 «тексты модалки не изменены»: ключевые строки мокапа
    m-login присутствуют в index.html дословно (заголовок, подзаголовок,
    подписи полей, плейсхолдеры, подписи кнопок)."""
    html = INDEX.read_text(encoding="utf-8")
    start = html.index("<!-- Модалка: Вход (утвержденный мокап) -->")
    end = html.index("<!-- Модалка: Регистрация (утвержденный мокап) -->")
    modal = html[start:end]
    for text in LOGIN_MODAL_TEXTS:
        assert text in modal, text


def test_tc_auth_login_modal_no_stub_submit():
    """Wiring заменяет заглушку: onclick alert('Заглушка: бэкенд не
    подключен') у кнопки «Войти» отсутствует, сабмит — через id="login-submit"."""
    html = INDEX.read_text(encoding="utf-8")
    start = html.index("<!-- Модалка: Вход (утвержденный мокап) -->")
    end = html.index("<!-- Модалка: Регистрация (утвержденный мокап) -->")
    modal = html[start:end]
    assert "Заглушка: бэкенд не подключен" not in modal
    assert 'id="login-submit"' in modal
    assert 'id="login-email"' in modal
    assert 'id="login-password"' in modal
    assert 'id="login-error"' in modal


def test_tc_auth_login_wiring_fragments_present():
    """Готовность 2.2 «вход из модалки уводит на /cabinet» + «неверные
    учетные данные показывают единое сообщение» — wiring-фрагменты:
    POST /api/auth/login, токен в sessionStorage['session_token'] (консистентно
    с cabinet.html, решение ПМ по 2.1), редирект location.href='/cabinet',
    вывод единого сообщения об ошибке из ответа под формой (без деталей
    причины в самом коде фронтенда)."""
    html = INDEX.read_text(encoding="utf-8")
    for fragment in WIRING_FRAGMENTS:
        assert fragment in html, fragment
    # единое сообщение: текст ошибки берется из ответа сервера (res.data.error)
    assert "res.data.error" in html


def test_tc_auth_landing_page_served_with_wiring(client):
    """Статический срез (по образцу test_static.py): GET / → 200 и отдает
    страницу с wiring-фрагментами модалки входа."""
    from fastapi.testclient import TestClient  # noqa: F401 (client в conftest)

    resp = client.get("/")
    assert resp.status_code == 200
    assert "СберАвтошкола" in resp.text
    assert "fetch('/api/auth/login'" in resp.text
    assert "sessionStorage.setItem('session_token'" in resp.text
    assert "location.href='/cabinet'" in resp.text
