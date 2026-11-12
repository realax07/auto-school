"""TC-AUTH — wiring модалки входа на лендинге (задача 2.2, sdd.md §9, §10.1, §10.4)
# Change: add-auth-cabinet
# FR: FR-1, FR-2, FR-4, FR-9

Спринт 12 (change add-vue-s12-landing-apply, задача 4.1): носитель лендинга —
каркас Vue (legacy frontend/index.html + js/landing.js удалены) — перенос
источников чтения (прецедент 2.3 пилота и 3.1 С11): тексты модалки — во
входе frontend/vue/index.html (комментарии-маркеры «Модалка:
Вход/Регистрация» сохранены), wiring — в App.vue + общий клиент
shared/api.js + shared-компоненты модалок. Проверяемые контракты не меняются:
fetch POST /api/auth/login, сохранение токена в sessionStorage['session_token'],
редирект /cabinet при ok, единое сообщение об ошибке под формой при 401;
тексты модалки m-login — дословно по мокапу. Браузерный сабмит (реальный
fetch + редирект) — вне TestClient (как TC-REG-016/017 в test_static.py).
"""
from conftest import ROOT

# Спринт 12 (задача 4.1): вход лендинга каркаса Vue — носитель
# LOGIN_MODAL_TEXTS (статическая разметка входа 1:1)
VUE = ROOT / "frontend" / "vue"
INDEX = VUE / "index.html"


def vue_landing_source() -> str:
    """HTML входа лендинга + wiring-носители из репо (App.vue, общий клиент
    shared/api.js, консолидированный wiring входа shared/loginWiring.js,
    shared-компоненты модалок) — эквивалент легаси-хелпера
    frontend_source("index.html") (HTML + /js/* рекурсивно).
    Спринт 14 (change add-vue-s14-instructor-loop, задача 3.1): doLogin
    вынесен из App.vue в композабл loginWiring.js (консолидация wiring
    входа на живом втором потребителе /instructors) — фрагменты контракта
    дословны в композабле; REGISTER-wiring и LOGIN_MODAL_TEXTS — на
    текущих носителях."""
    return "\n".join([
        INDEX.read_text(encoding="utf-8"),
        (VUE / "src" / "pages" / "landing" / "App.vue").read_text(encoding="utf-8"),
        (VUE / "src" / "shared" / "api.js").read_text(encoding="utf-8"),
        (VUE / "src" / "shared" / "loginWiring.js").read_text(encoding="utf-8"),
        (VUE / "src" / "shared" / "LoginModal.vue").read_text(encoding="utf-8"),
        (VUE / "src" / "shared" / "RegisterModal.vue").read_text(encoding="utf-8"),
    ])


# Ключевые строки мокапа модалки «Вход» (design/mocks) — тексты дословно
LOGIN_MODAL_TEXTS = [
    '<div class="overlay" id="m-login"><button class="login-close" id="login-close" type="button" data-close aria-label="Закрыть" title="Закрыть">×</button><div class="modal" role="dialog" aria-label="Вход">',
    "<h2>Вход</h2><p class=\"sub\">Войдите в личный кабинет</p>",
    "<label>Логин</label>",
    'placeholder="email или телефон"',
    "<label>Пароль</label>",
    "placeholder=\"••••••••\"",
]

# Wiring-обязательства задачи 2.2 (sdd §10.1, §10.4; решение ПМ по 2.1 —
# ключ sessionStorage именно session_token). Спринт 12: wiring — в App.vue
# лендинга; POST и хранение токена — через общий клиент shared/api.js
# (postJSON -> method:'POST'; setToken -> sessionStorage.setItem
# ключа TOKEN_KEY='session_token'). Фрагмент «err.textContent=» — стековый
# legacy: эквивалент Vue проверяется отдельно в
# test_tc_auth_login_wiring_fragments_present (design.md «Границы правок
# тестов»: сообщение ошибки сервера рендерится в #login-error/#reg-error
# из реактивного состояния).
WIRING_FRAGMENTS = [
    "postJSON('/api/auth/login'",                    # POST /api/auth/login
    "method: 'POST'",                                # ...метод POST (shared/api.js)
    "setToken(res.data.token)",                      # токен сессии сохранен
    "sessionStorage.setItem(TOKEN_KEY",              # ...в sessionStorage
    "'session_token'",                               # ...под ключом session_token
    "location.href='/cabinet'",                      # редирект на кабинет
]


def test_tc_auth_login_modal_texts_verbatim():
    """Готовность 2.2 «тексты модалки не изменены»: ключевые строки мокапа
    m-login присутствуют во входе vue/index.html дословно (заголовок,
    подзаголовок, подписи полей, плейсхолдеры, подписи кнопок)."""
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
    причины в самом коде фронтенда). Спринт 12: wiring — в App.vue лендинга
    + общий клиент shared/api.js (носитель из репо — vue_landing_source)."""
    src = vue_landing_source()
    for fragment in WIRING_FRAGMENTS:
        assert fragment in src, fragment
    # единое сообщение: текст ошибки берется из ответа сервера (res.data.error)
    assert "res.data.error" in src
    # эквивалент Vue стекового фрагмента «err.textContent=»: сообщение
    # ошибки сервера рендерится в #login-error/#reg-error из реактивного
    # состояния (интерполяция {{ }} — design.md «Границы правок тестов»)
    assert "loginError.value=(res.data&&res.data.error)" in src
    assert "regError.value=(res.data&&res.data.error)" in src
    assert "{{ error }}" in src
    assert 'id="login-error"' in src and 'id="reg-error"' in src


def test_tc_auth_landing_page_served_with_wiring(client):
    """Статический срез (по образцу test_static.py): GET / → 200 и отдает
    страницу с wiring-фрагментами модалки входа. Спринт 12: страница —
    вход каркаса Vue из dist (маршрут тот же; dist обязателен — CI/образ
    собирают, локально `npm ci && npm run build` перед pytest). Модуль
    /js/landing.js удален — wiring-носитель из репо: вход + App.vue +
    shared/api.js (vue_landing_source)."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "СберАвтошкола" in resp.text
    # вход подключает собранный модуль страницы каркаса (Vite переписывает
    # /src/pages/landing/main.js в хэш-ассет /vue/assets/index-*.js)
    assert '/vue/assets/index-' in resp.text

    src = vue_landing_source()
    assert "postJSON('/api/auth/login'" in src
    assert "setToken(res.data.token)" in src
    assert "location.href='/cabinet'" in src


def test_login_route_mapping_wiring():
    """MAJ-1 rev-002-2.2: route-маппинг вне token-guard — все 4 ветви §15.5
    достижимы; rejected-причина сохраняется для instructor-rejected.html.
    Спринт 12: маппинг — в App.vue лендинга (носитель из репо —
    vue_landing_source)."""
    src = vue_landing_source()
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
