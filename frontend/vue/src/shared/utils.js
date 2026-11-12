// Спринт 11 (change add-vue-s11-status-forms, задача 1.1): перенос общих
// UI-хелперов из frontend/js/utils.js (Спринт 6, Партия B) в shared-чанк
// каркаса Vue (ADR-008, manualChunks → 'shared'). Переносятся ТОЛЬКО те
// хелперы, которые нужны мигрированным страницам (toast — единый #toast
// с ms-параметром, expWord — стаж словами); frontend/js/*.js НЕ трогаются —
// ими продолжают пользоваться немигрированные монолиты. Это СВОЙ код в
// чанке shared, не библиотека (новых npm-зависимостей нет — NFR-26).
// Правило XSS (code-review review-001): пользовательские строки — только
// через textContent; на Vue-страницах эквивалент — интерполяция {{ }}.

// Тост #toast (единый на всех кабинетах); ms — длительность показа
// (review-form вызывает с 3200 мс — как legacy baseToast).
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
// Спринт 14 (change add-vue-s14-instructor-loop, задача 3.2): дословный
// перенос из frontend/js/shared/utils.js — потребитель кабинет на Vue
// (календарь С10: «сегодня» на реальной дате МСК, единая точка с сервером).
export function nowMoscow() {
  return new Date(new Date().toLocaleString('en-US', { timeZone: 'Europe/Moscow' }));
}

// Стаж словами: 1 год / 2 года / 5 лет (карточка инструктора, отзыв).
export function expWord(n) {
  n = +n || 0;
  return n % 10 === 1 && n % 100 !== 11 ? 'год'
    : (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? 'года' : 'лет');
}
