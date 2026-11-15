// Спринт 17 (change add-pdd-learning, задачи 17.5.1/17.5.2): ЧИСТЫЕ функции
// тренажёра «Билеты» и поиска «Штрафов» — без Vue и DOM (unit-носитель
// tests/unit/test_pdd_tickets_logic.py гоняет их через node). Компоненты
// секций импортируют этот модуль статически — инлайнится в свой lazy-чанк.
//
// Состояние тренажера — Vue ref в PddTickets.vue (решение Заказчика:
// персистентность НЕ нужна); здесь только арифметика: часы, статусы
// вопросов, счёт, фильтр таблицы штрафов.

// Таймер 20:00 (обратный отсчет, шаг 1с): 1200 → '20:00', 0 → '00:00'.
export function fmtClock(sec) {
  var s = Math.max(0, Number(sec) | 0);
  var m = Math.floor(s / 60);
  var r = s % 60;
  return (m < 10 ? '0' : '') + m + ':' + (r < 10 ? '0' : '') + r;
}

// Шаг обратного отсчета: не уходит ниже нуля (авто-финиш по timeUp).
export function decClock(sec) {
  return Math.max(0, (Number(sec) | 0) - 1);
}

// Ноль секунд — экзамен закончен (авто-«сдать» с подсчетом отвеченного).
export function timeUp(sec) {
  return (Number(sec) | 0) <= 0;
}

// Индекс верного варианта вопроса (в JSON ровно один correct — гейт
// генератора 17.2.1); -1 не встречается на валидном корпусе.
export function correctIndex(q) {
  return q.options.findIndex(function (o) { return o.correct; });
}

// Ответ НЕ выбран (выбор для вопроса еще не фиксировался).
export function isAnswered(picked) {
  return picked !== null && picked !== undefined;
}

// ФИКСАЦИЯ ОДНОКРАТНАЯ: повторный вызов с уже отвеченным вопросом
// возвращает тот же выбор — ответ не меняется (статус навигации честный).
export function fixAnswer(picked, choice) {
  return isAnswered(picked) ? picked : choice;
}

// Статус вопроса для сетки q-nav по мокапу: верный (done-g), неверный
// (done-r), не отвечен ('').
export function answerStatus(picked, correctIdx) {
  if (!isAnswered(picked)) return '';
  return picked === correctIdx ? 'done-g' : 'done-r';
}

// Статусы всех вопросов билета (выборка answers — те же done-g/done-r).
export function statusesOf(questions, pickedArr) {
  return questions.map(function (q, i) {
    return answerStatus(pickedArr[i], correctIndex(q));
  });
}

// Счёт тренажера: верные/ошибочные из ОТВЕЧЕННЫХ (неотвеченные — ни туда,
// ни сюда: «Верных: X · Ошибок: Y» экзамен-бара и итог).
export function scoreOf(statuses) {
  var good = 0, wrong = 0;
  statuses.forEach(function (st) {
    if (st === 'done-g') good++;
    else if (st === 'done-r') wrong++;
  });
  return { good: good, wrong: wrong, answered: good + wrong };
}

// «Штрафы» (17.6.1): клиентская фильтрация-подстрока по статье/нарушению/
// наказанию, без учета регистра; пустой запрос — все строки.
export function filterFines(rows, query) {
  var q = String(query || '').trim().toLowerCase();
  if (!q) return rows;
  return rows.filter(function (r) {
    return (r.article + '\n' + r.violation + '\n' + r.penalty).toLowerCase().indexOf(q) !== -1;
  });
}
