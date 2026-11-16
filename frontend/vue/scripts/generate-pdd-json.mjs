// Спринт 17 (change add-pdd-learning, задача 17.2.1): build-time генератор
// контента ПДД — content/pdd/ → frontend/vue/src/pages/cabinet/pdd-data/*.json
// (design.md «Решение 1»: build-time JSON, НЕ runtime-парсинг; корпус —
// единственный источник истины, pdd-data/ в git НЕ коммитится — .gitignore).
//
// Node stdlib, БЕЗ зависимостей (бюджетное правило репозитория). Шаг сборки:
//   "build": "node scripts/generate-pdd-json.mjs && vite build"
// (Dockerfile frontend-builder выполняет npm run build — генератор попадает
// в образ автоматически; bare-metal FR-57: npm ci && npm run build).
//
// ВХОДЫ (два носителя корпуса знаков):
// - content/pdd/znaki/*.md (group-md): 8 групп t1…t8, форматы заголовков
//   `## N.N` (t1…t7) и `## | N.N` (t8, pipe перед номером);
// - content/pdd/znaki-details.json: 321 записи, ключ — slug источника.
//   Join-правило: номер знака парсится из title («Знак 4.4.1 …» → 4.4.1);
//   группа — ТОЛЬКО из group-md (long записи — мусор источника, img пуст);
//   desc → блок описания, fine → блок штрафа (рендер при наличии), img/long —
//   игнорируются.
//
// ВЫХОД (имена с префиксом pdd- — роль чанка в check-budgets тривиальна):
//   pdd-znaki.json, pdd-pravila.json, pdd-shtrafi.json,
//   pdd-bilety-index.json, pdd-bilety-<cat>-<nn>.json (по билету — шардинг
//   «Бюджеты» design.md), pdd-manifest.json (манифест для тестов целостности).
//
// Гейты целостности (провал сборки при нарушении — build fails loudly,
// design «Гейты»; формальная спека — «Целостность контента проверяется
// на сборке»): bilety 80×20/один ✅/2–5 вариантов/ссылки картинок существуют;
// znaki 8 групп/321 знак/<номер>small.png существует; znaki-details 321
// записи/номер из title парсится и множества совпадают в ОБЕ стороны/
// desc пуст ТОЛЬКО у 5.33.1 и 5.34.1/fine опционален (166); pravila 26
// файлов с ровно одним H1; shtrafi заголовок/строки ≥ 1/3 tab-поля.
// Whitelist изображений: инвентарь строится по ссылкам из .md корпуса —
// unreferenced файлы (198 в images/bilety, вкл. crawl-артефакт «none_gray.jpg?»)
// в JSON не попадают.
//
// Для тестов генератора (tests/unit/test_pdd_generator.py, негативный
// мини-фикстурой) каталоги переопределяются env: PDD_CONTENT_DIR /
// PDD_OUT_DIR. Прод-пути — по умолчанию от корня репозитория.
//
// Спринт 17 fix (замечание Заказчика 2026-11-15 №3): strip-лист хвостов
// сайта-источника («Поделиться», «Печатать», «Зарегистрироваться или войти,
// чтобы написать комментарий.», «N комментариев», футер «© 2026 ЭКЗАМЕН
// ПДД … Написать в поддержку», крошки «ГлавнаяПДД»/«Главная», «← Назад к
// оглавлению», блоки комментариев «юзер+дата … Ответить», «↓ N ответ»,
// обрезанные тизеры «…»). Применяется при парсинге pravila/shtrafi —
// повторная выгрузка не притащит мусор в JSON; гейт внизу сборки падает,
// если мусор все же проник в выдачу.
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const VUE_DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const REPO_ROOT = path.join(VUE_DIR, '..', '..');
const CONTENT_DIR = process.env.PDD_CONTENT_DIR || path.join(REPO_ROOT, 'content', 'pdd');
const OUT_DIR = process.env.PDD_OUT_DIR || path.join(VUE_DIR, 'src', 'pages', 'cabinet', 'pdd-data');

// Допуск пустого desc — известные пустоты источника (design «Гейты»).
const DESC_EMPTY_ALLOWED = new Set(['5.33.1', '5.34.1']);
const GROUPS = ['t1', 't2', 't3', 't4', 't5', 't6', 't7', 't8'];
const CATEGORIES = ['abm', 'cd'];
const TICKETS_PER_CATEGORY = 40;
const QUESTIONS_PER_TICKET = 20;
const EXPECTED_SIGNS = 321;
const EXPECTED_CHAPTERS = 26;

const failures = [];
function fail(message) {
  failures.push(message);
}
function dieIfFailed(stage) {
  if (failures.length > 0) {
    console.error(`ГЕЙТ ЦЕЛОСТНОСТИ КОРПУСА ПРОВАЛЕН (${stage}):`);
    for (const f of failures) console.error('  - ' + f);
    console.error('Сборка прервана: content/pdd правится только перегенерацией (вне S17).');
    process.exit(1);
  }
}

// --- strip-лист хвостов сайта-источника (замечание Заказчика 2026-11-15 №3) ---
const STRIP_EXACT = new Set([
  'ГлавнаяПДД',
  'Главная',
  '← Назад к оглавлению',
  'Поделиться',
  'Печатать',
  'Зарегистрироваться или войти, чтобы написать комментарий.',
  '© 2026 ЭКЗАМЕН ПДД',
  'Политика конфиденциальности',
  'Пользовательское соглашение',
  'Для автошкол',
  'Контакты:',
  'Написать в поддержку',
]);
const STRIP_RES = [
  // NB: \w в JS не матчит кириллицу — только \S (прецедент: «комментариев»)
  /^\d+\s+комментари\S*\s*$/,           // «0 комментариев», «1 комментарий»
  /^↓\s*\d+\s+ответ\S*\s*$/,            // сворачивалка ветки ответов
  /^\S+\d{2}\.\d{2}\.\d{2} в \d{2}:\d{2}$/, // автор комментария + дата
  /support@экзамен-пдд\.рф/,            // почта поддержки в любой строке
];
// обрезанный тизер источника («…движение пешеходов р...») — многоточие в конце
const STRIP_TEASER = (l) => l.trimEnd().endsWith('...');
const STRIP_NEEDLES = [...STRIP_EXACT].filter((s) => s !== 'Главная');

function isSiteChromeLine(line) {
  const s = line.trim();
  if (!s) return false;
  if (STRIP_EXACT.has(s)) return true;
  if (STRIP_TEASER(line)) return true;
  return STRIP_RES.some((re) => re.test(s));
}

// Построчный strip + блоки комментариев (автор+дата → до «Ответить» включительно).
function stripSiteChrome(lines) {
  const out = [];
  let inComment = false;
  for (const line of lines) {
    if (inComment) {
      if (line.trim() === 'Ответить') inComment = false;
      continue;
    }
    if (/^\S+\d{2}\.\d{2}\.\d{2} в \d{2}:\d{2}$/.test(line.trim())) {
      inComment = true;
      continue;
    }
    if (!isSiteChromeLine(line)) out.push(line);
  }
  return out;
}

// Гейт: мусор источника не должен проникнуть в выдачу (pravila html + shtrafi).
function gateNoSiteChrome(pravilaChapters, shtrafiRows) {
  const hits = [];
  for (const c of pravilaChapters) {
    for (const block of c.html) {
      for (const needle of STRIP_NEEDLES) {
        if (block.includes(needle)) hits.push(`pravila/${c.id}: «${needle}»`);
      }
    }
  }
  for (const r of shtrafiRows) {
    for (const needle of STRIP_NEEDLES) {
      if (`${r.article} ${r.violation} ${r.penalty}`.includes(needle)) {
        hits.push(`shtrafi ${r.article}: «${needle}»`);
      }
    }
  }
  if (hits.length) fail(`хвосты сайта-источника в выдаче: ${hits.join('; ')}`);
}

// --- экранирование HTML для сгенерированных полей (v-html ТОЛЬКО для них) ---
function escHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ===========================================================================
// 1. ПРАВИЛА: 26 глав r1_…r26_ — H1-блок → заголовок; тело → html-абзацы
// ===========================================================================
function buildPravila() {
  const dir = path.join(CONTENT_DIR, 'pravila');
  if (!existsSync(dir)) {
    fail('content/pdd/pravila отсутствует');
    return [];
  }
  const files = readdirSync(dir).filter((f) => f.endsWith('.md'));
  // порядок глав — по числовому префиксу r<N>_ (design «Решение 5»)
  files.sort((a, b) => {
    const na = parseInt(a.slice(1), 10);
    const nb = parseInt(b.slice(1), 10);
    return na - nb;
  });
  if (files.length !== EXPECTED_CHAPTERS) {
    fail(`pravila: файлов ${files.length}, ожидается ${EXPECTED_CHAPTERS}`);
  }
  const chapters = [];
  for (const name of files) {
    // strip хвостов сайта-источника ДО парсинга (замечание 2026-11-15 №3)
    const lines = stripSiteChrome(readFileSync(path.join(dir, name), 'utf8').split('\n'));
    const h1Idxs = lines.reduce((acc, l, i) => (l.startsWith('# ') ? acc.concat(i) : acc), []);
    if (h1Idxs.length !== 1) {
      fail(`pravila/${name}: строк H1 ${h1Idxs.length}, ожидается ровно одна`);
      continue;
    }
    // H1-блок: строка «# …» и следующие подряд непустые строки (r1 —
    // двухстрочный заголовок «Правила Дорожного Движения 2026. / Общие положения.»)
    let end = h1Idxs[0] + 1;
    while (end < lines.length && lines[end].trim() !== '') end += 1;
    const title = [lines[h1Idxs[0]].slice(2), ...lines.slice(h1Idxs[0] + 1, end)]
      .join(' ')
      .trim();
    // тело → блоки по пустой строке → минимальная белая конвертация в html:
    // экранирование спецсимволов, внутренние переводы строки → <br>
    const blocks = [];
    let cur = [];
    for (let i = end; i < lines.length; i += 1) {
      if (lines[i].trim() === '') {
        if (cur.length) { blocks.push(cur); cur = []; }
      } else {
        cur.push(lines[i].trim());
      }
    }
    if (cur.length) blocks.push(cur);
    const html = blocks.map((b) => {
      const inner = b
        .map((line) => {
          const t = escHtml(line);
          // «(в ред. …)» — служебная строка редакции, приглушенно
          if (/^\(в ред\./.test(line)) return `<span class="amend">${t}</span>`;
          // «10.1 текст…» — номер пункта как визуальный якорь
          return t.replace(/^(\d+(?:\.\d+)*)\s/, '<b class="pnum">$1</b> ');
        })
        .join('<br>');
      return `<p>${inner}</p>`;
    });
    chapters.push({ id: parseInt(name.slice(1), 10), title, html });
  }
  return chapters;
}

// ===========================================================================
// 2. ЗНАКИ: 8 group-md (оба формата «## N.N» и «## | N.N») + znaki-details
// ===========================================================================
const NUM_RE = /^##\s+\|?\s*(\d+(?:\.\d+)*)\s*$/;

function buildZnaki() {
  const dir = path.join(CONTENT_DIR, 'znaki');
  if (!existsSync(dir)) {
    fail('content/pdd/znaki отсутствует');
    return { groups, signs };
  }
  const groups = [];
  const signs = [];
  for (const g of GROUPS) {
    const mdFiles = readdirSync(dir).filter((f) => f.startsWith(g + '_') && f.endsWith('.md'));
    if (mdFiles.length !== 1) {
      fail(`znaki: для группы ${g} найдено файлов ${mdFiles.length}, ожидается 1`);
      continue;
    }
    const lines = readFileSync(path.join(dir, mdFiles[0]), 'utf8').split('\n');
    const name = (lines.find((l) => l.startsWith('# ')) || '').slice(2).trim();
    if (!name) fail(`znaki/${mdFiles[0]}: заголовок группы (H1) не найден`);
    const groupId = g;
    let count = 0;
    let current = null;
    const flush = () => {
      if (!current) return;
      const imageName = `${current.number}small.png`;
      const imagePath = path.join(CONTENT_DIR, 'images', 'znaki', imageName);
      if (!existsSync(imagePath)) {
        fail(`znaki: для знака ${current.number} нет images/znaki/${imageName}`);
      } else {
        signs.push({
          number: current.number,
          name: current.name,
          group: groupId,
          image: `/pdd-assets/znaki/${imageName}`,
          desc: '',
          fine: null,
        });
        count += 1;
      }
      current = null;
    };
    for (const line of lines) {
      const m = line.match(NUM_RE);
      if (m) {
        flush();
        current = { number: m[1], name: '' };
      } else if (current && line.trim() && !line.startsWith('#')) {
        current.name = current.name ? `${current.name} ${line.trim()}` : line.trim();
      }
    }
    flush();
    groups.push({ id: groupId, name, count });
  }
  if (groups.length !== 8) fail(`znaki: групп ${groups.length}, ожидается 8`);

  // --- znaki-details.json: join по номеру из title (slug — НЕ ключ join) ---
  const detailsPath = path.join(CONTENT_DIR, 'znaki-details.json');
  let details;
  try {
    details = JSON.parse(readFileSync(detailsPath, 'utf8'));
  } catch (e) {
    fail(`znaki-details.json: не читается (${e.message})`);
    details = {};
  }
  const detailEntries = Object.entries(details);
  if (detailEntries.length !== EXPECTED_SIGNS) {
    fail(`znaki-details: записей ${detailEntries.length}, ожидается ${EXPECTED_SIGNS}`);
  }
  const byNumber = new Map(signs.map((s) => [s.number, s]));
  const detailNumbers = new Set();
  for (const [slug, rec] of detailEntries) {
    const m = String(rec.title || '').match(/^Знак\s+(\d+(?:\.\d+)*)\b/);
    if (!m) {
      fail(`znaki-details: номер из title не парсится — ${slug} (${rec.title})`);
      continue;
    }
    const num = m[1];
    detailNumbers.add(num);
    const sign = byNumber.get(num);
    if (!sign) {
      fail(`znaki-details: запись ${slug} (номер ${num}) без пары в group-md`);
      continue;
    }
    const desc = String(rec.desc || '').trim();
    if (desc === '' && !DESC_EMPTY_ALLOWED.has(num)) {
      fail(`znaki-details: пустой desc у ${num} (${slug}) — допуск только 5.33.1/5.34.1`);
    }
    const fine = String(rec.fine || '').trim();
    sign.desc = desc;
    // замечание Заказчика 2026-11-15 («сплошным текстом… сделать более
    // читабельным»): абзацы источника — отдельными элементами массива
    sign.descParas = desc.split(/\n{2,}/).map((x) => x.trim()).filter(Boolean);
    sign.fine = fine === '' ? null : fine;
    // замечание Заказчика 2026-11-15 («сплошной текст» в жёлтой карточке):
    // строки штрафа отдельно — вводный абзац + перечни а)/б)/в) табуляцией
    sign.fineLines = fine === '' ? [] : fine.split('\n').map((x) => x.trim()).filter(Boolean);
    // img/long записи ИГНОРИРУЮТСЯ (img пуст у всех 321, long — мусор источника)
  }
  // биекция в ОБЕ стороны: номера group-md == номера details
  for (const s of signs) {
    if (!detailNumbers.has(s.number)) {
      fail(`znaki: знак ${s.number} из group-md без записи в znaki-details`);
    }
  }
  if (signs.length !== EXPECTED_SIGNS) {
    fail(`znaki: знаков ${signs.length}, ожидается ${EXPECTED_SIGNS}`);
  }
  return { groups, signs };
}

// ===========================================================================
// 3. БИЛЕТЫ: abm|cd × bilet-01…40 — 20 вопросов, один ✅, 2–5 вариантов,
//    ссылки ../images/bilety/* существуют (whitelist ссылок из .md)
// ===========================================================================
function parseTicket(cat, n, text, relName) {
  const qSplit = text.split(/^##\s+/m).filter((b) => b.startsWith('Вопрос'));
  const questions = [];
  for (const block of qSplit) {
    const lines = block.split('\n');
    const qn = parseInt((lines[0].match(/^Вопрос\s+(\d+)/) || [])[1], 10);
    if (!qn) {
      fail(`${relName}: заголовок вопроса не парсится`);
      continue;
    }
    let imgPath = null;
    const options = [];
    let explanation = '';
    let explanationStarted = false;
    for (const raw of lines.slice(1)) {
      const line = raw.trim();
      if (!line || line.startsWith('**Варианты ответа:**')) continue;
      const img = line.match(/^!\[[^\]]*\]\(\.\.\/images\/bilety\/([^)]+)\)$/);
      if (img) {
        imgPath = img[1];
        continue;
      }
      const opt = line.match(/^-\s+\d+\.\s+(.*)$/);
      if (opt && !explanationStarted) {
        const correct = /\s*✅\s*$/.test(opt[1]);
        options.push({ text: opt[1].replace(/\s*✅\s*$/, '').trim(), correct });
        continue;
      }
      const exp = line.match(/^\*\*Пояснение:\*\*\s*(.*)$/);
      if (exp) {
        explanationStarted = true;
        explanation = exp[1].trim();
        continue;
      }
      if (explanationStarted && line) {
        explanation = explanation ? `${explanation} ${line}` : line;
      }
    }
    const correctCount = options.filter((o) => o.correct).length;
    if (correctCount !== 1) {
      fail(`${relName} вопрос ${qn}: пометок ✅ ${correctCount}, ожидается ровно одна`);
    }
    if (options.length < 2 || options.length > 5) {
      fail(`${relName} вопрос ${qn}: вариантов ${options.length}, ожидается 2–5`);
    }
    if (imgPath !== null) {
      const imgOnDisk = path.join(CONTENT_DIR, 'images', 'bilety', imgPath);
      if (!existsSync(imgOnDisk)) {
        fail(`${relName} вопрос ${qn}: ссылка ../images/bilety/${imgPath} не существует на диске`);
      }
    }
    questions.push({ text: '', image: imgPath === null ? null : `/pdd-assets/bilety/${imgPath}`, options, explanation, _qn: qn });
    // текст вопроса — абзацы до картинки/вариантов/пояснения; собирается ниже
  }
  // текст вопроса: строки блока до изображения/вариантов/пояснения
  // (пере-проход по тем же блокам для четкого отделения)
  const blocks = text.split(/^##\s+/m).filter((b) => b.startsWith('Вопрос'));
  blocks.forEach((block, i) => {
    if (!questions[i]) return;
    const qText = [];
    for (const raw of block.split('\n').slice(1)) {
      const line = raw.trim();
      if (!line) continue;
      if (/^!\[/.test(line) || /^\*\*Варианты ответа:\*\*/.test(line) || /^\*\*Пояснение:\*\*/.test(line)) break;
      if (/^-\s+\d+\.\s+/.test(line)) break;
      qText.push(line);
    }
    questions[i].text = qText.join(' ');
  });
  questions.sort((a, b) => a._qn - b._qn);
  const qns = questions.map((q) => q._qn);
  if (questions.length !== QUESTIONS_PER_TICKET) {
    fail(`${relName}: вопросов ${questions.length}, ожидается ${QUESTIONS_PER_TICKET}`);
  }
  if (qns.join(',') !== Array.from({ length: QUESTIONS_PER_TICKET }, (_, i) => i + 1).join(',')) {
    fail(`${relName}: нумерация вопросов нарушена (${qns.join(',')})`);
  }
  for (const q of questions) delete q._qn;
  return questions;
}

function buildBilety() {
  const index = { categories: [] };
  let ticketCount = 0;
  let questionCount = 0;
  const tickets = {};
  for (const cat of CATEGORIES) {
    const catTickets = [];
    for (let n = 1; n <= TICKETS_PER_CATEGORY; n += 1) {
      const nn = String(n).padStart(2, '0');
      const relName = `bilety/${cat}/bilet-${nn}.md`;
      const file = path.join(CONTENT_DIR, 'bilety', cat, `bilet-${nn}.md`);
      if (!existsSync(file)) {
        fail(`${relName}: файл не найден`);
        continue;
      }
      const questions = parseTicket(cat, n, readFileSync(file, 'utf8'), relName);
      const id = `${cat}-${nn}`;
      catTickets.push({
        id,
        number: n,
        questions: questions.length,
        hasImages: questions.some((q) => q.image !== null),
      });
      tickets[id] = {
        id,
        category: cat,
        number: n,
        questions,
      };
      ticketCount += 1;
      questionCount += questions.length;
    }
    index.categories.push({ id: cat, tickets: catTickets });
  }
  if (ticketCount !== CATEGORIES.length * TICKETS_PER_CATEGORY) {
    fail(`bilety: билетов ${ticketCount}, ожидается ${CATEGORIES.length * TICKETS_PER_CATEGORY}`);
  }
  if (questionCount !== ticketCount * QUESTIONS_PER_TICKET) {
    fail(`bilety: вопросов всего ${questionCount}, ожидается ${ticketCount * QUESTIONS_PER_TICKET}`);
  }
  return { index, tickets };
}

// ===========================================================================
// 4. ШТРАФЫ: tab-таблица после заголовка «Пункт КоАП…»
// ===========================================================================
function buildShtrafi() {
  const dir = path.join(CONTENT_DIR, 'shtrafi');
  const files = existsSync(dir) ? readdirSync(dir).filter((f) => f.endsWith('.md')) : [];
  if (files.length !== 1) {
    fail(`shtrafi: файлов ${files.length}, ожидается 1`);
    return [];
  }
  const lines = stripSiteChrome(readFileSync(path.join(dir, files[0]), 'utf8').split('\n'));
  const headerIdx = lines.findIndex((l) => l.replace(/\r$/, '') === 'Пункт КоАП\tНарушение\tНаказание');
  if (headerIdx === -1) {
    fail('shtrafi: заголовок таблицы «Пункт КоАП\\tНарушение\\tНаказание» не найден');
    return [];
  }
  const rows = [];
  for (const line of lines.slice(headerIdx + 1)) {
    const trimmed = line.replace(/\r$/, '');
    if (trimmed === '') continue;
    if (!trimmed.includes('\t')) break; // конец таблицы (футер сайта-источника)
    const parts = trimmed.split('\t');
    if (parts.length !== 3) {
      fail(`shtrafi: строка с ${parts.length} tab-полями (ожидается 3): ${trimmed.slice(0, 40)}…`);
      continue;
    }
    rows.push({ article: parts[0].trim(), violation: parts[1].trim(), penalty: parts[2].trim() });
  }
  if (rows.length < 1) fail('shtrafi: строк таблицы 0, ожидается ≥ 1');
  return rows;
}

// ===========================================================================
// сборка + запись (идемпотентная: полная перезапись каталога OUT_DIR)
// ===========================================================================
const pravila = buildPravila();
dieIfFailed('pravila');
const znaki = buildZnaki();
dieIfFailed('znaki');
const shtrafi = buildShtrafi();
dieIfFailed('shtrafi');
const bilety = buildBilety();
dieIfFailed('bilety');
// strip-гейт (замечание 2026-11-15 №3): хвосты источника не в выдаче
gateNoSiteChrome(pravila, shtrafi);
dieIfFailed('strip-gate');

rmSync(OUT_DIR, { recursive: true, force: true });
mkdirSync(OUT_DIR, { recursive: true });

const out = (name, data, pretty = false) => {
  writeFileSync(path.join(OUT_DIR, name), JSON.stringify(data, null, pretty ? 2 : 0) + '\n');
};

out('pdd-pravila.json', pravila);
out('pdd-znaki.json', znaki);
out('pdd-shtrafi.json', shtrafi);
out('pdd-bilety-index.json', bilety.index);
for (const [id, ticket] of Object.entries(bilety.tickets)) {
  out(`pdd-bilety-${id}.json`, ticket);
}
const manifest = {
  source: 'content/pdd',
  pravila: { chapters: pravila.length },
  znaki: {
    groups: znaki.groups.length,
    signs: znaki.signs.length,
    withFine: znaki.signs.filter((s) => s.fine !== null).length,
    descEmptyAllowed: [...DESC_EMPTY_ALLOWED],
  },
  shtrafi: { rows: shtrafi.length },
  bilety: {
    categories: bilety.index.categories.length,
    tickets: Object.keys(bilety.tickets).length,
    questionsPerTicket: QUESTIONS_PER_TICKET,
  },
  files: [
    'pdd-pravila.json',
    'pdd-znaki.json',
    'pdd-shtrafi.json',
    'pdd-bilety-index.json',
    ...Object.keys(bilety.tickets).map((id) => `pdd-bilety-${id}.json`),
    'pdd-manifest.json',
  ],
};
out('pdd-manifest.json', manifest, true);

console.log(
  `generate-pdd-json: OK — ${pravila.length} глав, ${znaki.groups.length} групп / ${znaki.signs.length} знаков ` +
    `(fine: ${manifest.znaki.withFine}), ${shtrafi.length} строк штрафов, ` +
    `${manifest.bilety.tickets} билетов × ${QUESTIONS_PER_TICKET} вопросов → ${OUT_DIR}`,
);
