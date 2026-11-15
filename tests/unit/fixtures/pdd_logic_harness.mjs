// Unit-носитель чистой логики секций ПДД (Спринт 17, 17.5.2/17.6.2):
// harness запускается pytest-ом (tests/unit/test_pdd_tickets_logic.py)
// как `node pdd_logic_harness.mjs <путь-к-pdd-logic.mjs>` — новые
// зависимости НЕ вводятся (бюджетное правило репозитория), Node stdlib.
// Любая упавшая проверка — ненулевой exit + сообщение в stdout.
import assert from 'node:assert/strict';

const logic = await import(process.argv[2]);
const {
  fmtClock, decClock, timeUp, correctIndex, isAnswered,
  fixAnswer, answerStatus, statusesOf, scoreOf, filterFines,
} = logic;

// --- таймер 20:00 (обратный отсчет, авто-финиш по нулям) --------------------
assert.equal(fmtClock(20 * 60), '20:00', 'старт тренажера — 20:00');
assert.equal(fmtClock(0), '00:00', 'финиш — 00:00');
assert.equal(fmtClock(605), '10:05', 'формат MM:SS с ведущими нулями');
assert.equal(decClock(1200), 1199, 'шаг отсчета −1с');
assert.equal(decClock(0), 0, 'ниже нуля не уходит');
assert.equal(timeUp(1), false, '1с — еще идет');
assert.equal(timeUp(0), true, '0с — авто-финиш');
assert.equal(timeUp(-3), true, 'отрицательные часы — финиш');
// сценарий авто-финиша: 2 → 1 → 0 → timeUp
let clock = 2;
clock = decClock(clock); assert.equal(timeUp(clock), false);
clock = decClock(clock); assert.equal(timeUp(clock), true, 'дошли до 00:00 за 2 шага');

// --- вопросы: верный вариант, статусы, СЧЁТ ---------------------------------
const q = {
  text: 'q', image: null, explanation: 'e',
  options: [{ text: 'a', correct: false }, { text: 'b', correct: true }, { text: 'c', correct: false }],
};
assert.equal(correctIndex(q), 1, 'верный вариант — ровно один correct (гейт генератора)');

// фиксация ОДНОКРАТНАЯ: первый выбор фиксируется, повторный/иной — нет
assert.equal(isAnswered(null), false, 'выбор не сделан');
assert.equal(isAnswered(0), true, 'индекс 0 — валидный выбор (не «не отвечено»)');
assert.equal(fixAnswer(null, 2), 2, 'первый клик фиксирует выбор');
assert.equal(fixAnswer(2, 0), 2, 'повторный клик ответ НЕ меняет');
assert.equal(fixAnswer(2, 1), 2, 'клик по другому варианту ответ НЕ меняет');

assert.equal(answerStatus(null, 1), '', 'не отвечен — нейтральный');
assert.equal(answerStatus(1, 1), 'done-g', 'верный — done-g');
assert.equal(answerStatus(2, 1), 'done-r', 'неверный — done-r');

// сценарий билета: 5 вопросов, отвечены 1-4, пятый не отвечен
const questions = Array.from({ length: 5 }, () => q);
const picked = [1, 2, null, 1, null];
const statuses = statusesOf(questions, picked);
assert.deepEqual(statuses, ['done-g', 'done-r', '', 'done-g', ''], 'статусы сетки 1–N');
const score = scoreOf(statuses);
assert.deepEqual(score, { good: 2, wrong: 1, answered: 3 }, 'счёт верных/ошибок из отвеченных');
// авто-финиш по нулям: неотвеченные не попадают ни в верные, ни в ошибки
assert.equal(scoreOf(questions.map(() => '')).good, 0, 'ничья не отвечена — нулевой счёт');

// --- «Штрафы»: клиентский поиск-подстрока без учета регистра -----------------
const rows = [
  { article: 'Ст. 12.9.1', violation: 'Превышение более 20 км/ч', penalty: 'Штраф: 750 рублей' },
  { article: 'Ст. 12.29', violation: 'Нарушение ПДД пешеходом', penalty: 'Штраф от 500 до 800 рублей' },
  { article: 'Ст. 12.8', violation: 'Управление в состоянии опьянения', penalty: 'Штраф 45000 рублей' },
];
assert.equal(filterFines(rows, '').length, 3, 'пустой запрос — все строки');
assert.equal(filterFines(rows, '   ').length, 3, 'пробельный запрос — все строки');
assert.deepEqual(
  filterFines(rows, 'ПЕШЕХОД').map((r) => r.article),
  ['Ст. 12.29'], 'регистр не учитывается, поле violation',
);
assert.deepEqual(
  filterFines(rows, '12.9').map((r) => r.article),
  ['Ст. 12.9.1'], 'поиск по номеру статьи',
);
assert.deepEqual(
  filterFines(rows, '750').map((r) => r.article),
  ['Ст. 12.9.1'], 'поиск по наказанию (penalty)',
);
assert.deepEqual(filterFines(rows, 'если-бы-была-море-слов'), [], 'нет совпадений — пустой результат');

console.log('pdd-logic: все проверки пройдены');
process.exit(0);
