// Спринт 9 (change add-vue-framework-pilot, задача 2.1): перенос
// fetch-обертки frontend/js/api.js (Спринт 6, Партия B) в shared-чанк
// каркаса Vue (ADR-008). Контракты вызовов НЕ меняются — это дословный
// перенос; немигрированные монолиты продолжают читать frontend/js/api.js.
// Общий код страниц (api-клиент, утилиты) собирается в чанк 'shared'
// (vite.config.mjs manualChunks). Потребитель на пилотной странице —
// блок 2 (задача 3.1, контракт change add-application-status-polling).
export var TOKEN_KEY = 'session_token';

export function getToken() {
  try { return sessionStorage.getItem(TOKEN_KEY); } catch (e) { return null; }
}

export function setToken(t) {
  try { sessionStorage.setItem(TOKEN_KEY, t); } catch (e) {}
}

// Полная очистка сессии (единый паттерн кабинетов: sessionStorage.clear()).
export function clearSession() {
  try { sessionStorage.clear(); } catch (e) {}
}

// 401/403 или нет токена -> редирект на главную, к модалке входа (FR-7).
export function toLogin() {
  clearSession();
  location.href = '/';
}

// JSON-запрос с инструкторской/ученической сессией; cb получает
// {status, data} (network-ошибка -> {status:0, data:null}).
export function api(path, opts, cb) {
  opts = opts || {};
  opts.headers = Object.assign({ 'X-Session-Token': getToken() || '' }, opts.headers || {});
  if (opts.body) opts.headers['Content-Type'] = 'application/json';
  fetch(path, opts).then(function (r) {
    r.json().then(function (d) { cb({ status: r.status, data: d }); },
      function () { cb({ status: r.status, data: null }); });
  }, function () { cb({ status: 0, data: null }); });
}

// 401/403 -> toLogin(); возвращает true, если ответ обработан как auth-fail.
export function handleAuthFail(res) {
  if (res.status === 401 || res.status === 403) { toLogin(); return true; }
  return false;
}

// JSON-GET с сессией; cb получает {ok,...} при 200/ok, иначе null
// (паттерн дашборда инструктора).
export function apiGet(path, cb) {
  fetch(path, { headers: { 'X-Session-Token': getToken() || '' } })
    .then(function (r) {
      if (r.status === 401 || r.status === 403) { cb(null); return; }
      return r.json().then(function (d) { cb(r.status === 200 && d && d.ok ? d : null); });
    })
    .catch(function () { cb(null); });
}

// JSON-POST/PUT/DELETE с сессией; cb получает {status, data}.
export function apiSend(method, path, body, cb) {
  fetch(path, {
    method: method,
    headers: { 'X-Session-Token': getToken() || '', 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {})
  })
    .then(function (r) {
      r.json().then(function (d) { cb({ status: r.status, data: d }); },
        function () { cb({ status: r.status, data: null }); });
    })
    .catch(function () { cb({ status: 0, data: null }); });
}

// Публичный JSON POST (без токена: регистрация, вход, админ-логин);
// Promise -> {status, data}, network-ошибка -> {status:0, data:null}.
export function postJSON(path, payload) {
  return fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  }).then(function (r) {
    return r.json().then(function (d) { return { status: r.status, data: d }; },
      function () { return { status: r.status, data: null }; });
  }, function () { return { status: 0, data: null }; });
}
