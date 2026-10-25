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
# ключ sessionStorage именно session_token). Спринт 6 Партия B: wiring —
# в модуле js/landing.js; POST и хранение токена — через общий клиент
# js/api.js (postJSON -> method:'POST'; setToken -> sessionStorage.setItem
# ключа TOKEN_KEY='session_token').
WIRING_FRAGMENTS = [
    "postJSON('/api/auth/login'",                    # POST /api/auth/login
    "method: 'POST'",                                # ...метод POST (js/api.js)
    "setToken(res.data.token)",                      # токен сессии сохранен
    "sessionStorage.setItem(TOKEN_KEY",              # ...в sessionStorage
    "'session_token'",                               # ...под ключом session_token
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
    причины в самом коде фронтенда). Спринт 6 Партия B: wiring — в модуле
    js/landing.js + общий клиент js/api.js (проверяем HTML + модуль
    с его импортами, frontend_source)."""
    from conftest import frontend_source

    src = frontend_source("index.html")
    for fragment in WIRING_FRAGMENTS:
        assert fragment in src, fragment
    # единое сообщение: текст ошибки берется из ответа сервера (res.data.error)
    assert "res.data.error" in src


def test_tc_auth_landing_page_served_with_wiring(client):
    """Статический срез (по образцу test_static.py): GET / → 200 и отдает
    страницу с wiring-фрагментами модалки входа. Спринт 6 Партия B: wiring —
    в ES-модулях, поэтому единица проверки — страница + отдаваемые ею
    модули: GET /js/landing.js и GET /js/api.js (транзитивный импорт)."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "СберАвтошкола" in resp.text

    js_landing = client.get("/js/landing.js")
    js_api = client.get("/js/api.js")
    assert js_landing.status_code == 200
    assert js_api.status_code == 200
    # страница подключает модуль входа, модуль — общий клиент
    assert 'src="/js/landing.js"' in resp.text
    assert "from './api.js'" in js_landing.text

    served = "\n".join((resp.text, js_landing.text, js_api.text))
    assert "postJSON('/api/auth/login'" in served
    assert "setToken(res.data.token)" in served
    assert "location.href='/cabinet'" in served


def test_login_route_mapping_wiring():
    """MAJ-1 rev-002-2.2: route-маппинг вне token-guard — все 4 ветви §15.5
    достижимы; rejected-причина сохраняется для instructor-rejected.html.
    Спринт 6 Партия B: маппинг — в модуле js/landing.js (проверяем
    HTML + модуль с его импортами, frontend_source)."""
    from conftest import frontend_source

    src = frontend_source("index.html")
    # все 4 ветви маппинга
    assert "route==='cabinet'" in src and "/instructor/dashboard" in src
    assert "route==='pending'" in src and "/instructors/pending" in src
    assert "route==='rejected'" in src and "/instructors/rejected" in src
    assert "route||'student-cabinet'" in src or "else{location.href='/cabinet'" in src
    # reason пишется в sessionStorage до редиректа на rejected
    assert "instructor_rejected_reason" in src
    # route-разбор стоит ДО безусловного token-guard: порядок if(route...) после res.data.ok
    idx_ok = src.find("res.status===200&&res.data.ok")
    idx_route = src.find("route==='cabinet'")
    assert 0 < idx_ok < idx_route
