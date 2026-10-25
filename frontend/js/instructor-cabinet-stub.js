/* из instructor-cabinet-stub.html (блок 1) */
// Спринт 6, Партия B: api/getToken — общий клиент js/api.js,
// initials/fioOf — общие хелперы js/utils.js
import { api, getToken } from './api.js';
import { initials, fioOf } from './utils.js';
(function(){
  // Wiring (задача 4.4, sdd §15.6): защита сессией как /cabinet —
  // GET /api/auth/me (X-Session-Token из sessionStorage['session_token']),
  // 401/нет токена -> редирект на вход (на главную, к модалке m-login).
  var TOKEN_KEY = 'session_token';
  function toLogin() {
    try { sessionStorage.removeItem(TOKEN_KEY); } catch (e) {}
    location.href = '/';
  }
  var token = getToken();
  if (!token) {
    toLogin();
  } else {
    api('/api/auth/me', {}, function (res) {
      if (res.status === 0) { return; /* сеть: остаемся на странице */ }
      if (res.status === 401 || !res.data || !res.data.ok) { toLogin(); return; }
      var u = res.data.user || {};
      var fio = fioOf(u) || 'Инструктор';
      document.getElementById('uname').textContent = fio;
      document.getElementById('avatar').textContent = initials(fio, 'ИИ');
    });
  }
})();
