// Спринт 6, Партия B (PLAN, директива Заказчика 2026-10-16: модульная
// архитектура фронтенда). Общие UI-хелперы всех страниц.
// Правило XSS (code-review review-001): пользовательские строки — только
// через textContent (el), innerHTML с данными запрещен.

// DOM-хелпер: создать элемент, класс и текст (textContent — защита от XSS).
export function el(tag, cls, text) {
  var n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

// Тост #toast (единый на всех кабинетах); ms — длительность показа.
export function toast(msg, ms) {
  ms = ms || 3000;
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(function () { t.classList.remove('show'); }, ms);
}

// «Сейчас» по деловым датам — Europe/Moscow (GMT+3), локаль ru
// (Спринт 3: даты кабинета — актуальные, TimeZone Europe/Moscow).
export function nowMoscow() {
  return new Date(new Date().toLocaleString('en-US', { timeZone: 'Europe/Moscow' }));
}

// ФИО из учетной записи (FR-5/FR-20): {surname, name, patronymic} -> строка.
export function fioOf(u) {
  u = u || {};
  return [u.surname, u.name, u.patronymic].filter(Boolean).join(' ');
}

// Инициалы из ФИО (аватар): первые буквы первых двух слов, запасной вариант.
export function initials(fio, fallback) {
  var parts = String(fio || '').trim().split(/\s+/).filter(Boolean);
  return parts.slice(0, 2).map(function (p) { return p[0].toUpperCase(); }).join('') || (fallback || '');
}

// '2026-10-16 10:22:00' -> '16.10.2026' (строки Created_at из БД).
export function fmtDate(s) {
  if (!s) return '';
  var m = String(s).match(/^(\d{4})-(\d{2})-(\d{2})/);
  return m ? (m[3] + '.' + m[2] + '.' + m[1]) : String(s);
}

// Стаж словами: 1 год / 2 года / 5 лет (карточка инструктора, отзыв).
export function expWord(n) {
  n = +n || 0;
  return n % 10 === 1 && n % 100 !== 11 ? 'год'
    : (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? 'года' : 'лет');
}
