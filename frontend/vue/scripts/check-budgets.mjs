// Спринт 9 (change add-vue-framework-pilot, задача 4.1; NFR-26) и
// Спринт 11 (change add-vue-s11-status-forms, задача 1.1): проверка
// бюджетов чанков НА АРТЕФАКТАХ сборки dist/. Запуск: npm run build &&
// npm run check:budgets (повторяется на приемке каждого шага миграции —
// tasks.md 4.1, ADR-008 п.3).
//
// Бюджеты (NFR-26; на КАЖДОЙ мигрированной странице):
//   (а) каждый vendor-чанк ≤ 150 КБ gzip;
//   (б) суммарный JS первого захода КАЖДОЙ страницы (page-чанк +
//       static-import graph: shared + vue и все загружаемые ими чанки)
//       ≤ 200 КБ gzip — отдельно для instructors-pending,
//       instructors-rejected, review-form, index, instructor-apply;
//   (в) в бандле КАЖДОЙ страницы нет чужих page-чанков (multi-entry):
//       замыкание импортов входа состоит только из ее page-чанка,
//       'shared' и vendor-чанков.
//
// Роли чанков — по правилам manualChunks (vite.config.mjs, ADR-008):
// имя чанка до хэша — 'shared' (свой код), имя одного из входов
// (PAGES), остальные имена — vendor-чанки по пакетам ('vue',
// '@vue/*' → 'vue'). gzip-размер — дословно `gzip -c <file> | wc -c`
// (фолбэк zlib level 6, новых зависимостей нет).
import { readdirSync, readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { gzipSync } from 'node:zlib';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const DIST = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'dist');
const VENDOR_MAX = 150 * 1024; // (а) КБ → байты
const FIRST_LOAD_MAX = 200 * 1024; // (б)
const KB = 1024;
// page-чанки — по именам входов vite.config.mjs (задача 2.1 С12:
// +index — лендинг «/», +instructor-apply — анкета; всего 5 страниц)
const PAGES = ['instructors-pending', 'instructors-rejected', 'review-form', 'index', 'instructor-apply'];

function chunkRole(file) {
  // instructors-pending-<hash>.js / shared-<hash>.js / vue-<hash>.js
  const base = path.basename(file, '.js');
  const name = base.replace(/-[A-Za-z0-9_-]{8}$/, '');
  if (name === 'shared') return { name, role: 'shared' };
  if (PAGES.includes(name)) return { name, role: 'page' };
  return { name, role: 'vendor' };
}

function gzipSize(file) {
  // дословно по задаче 4.1: `gzip -c <file> | wc -c` (дефолтный уровень
  // gzip CLI); если утилиты gzip нет — zlib level 6 (то же semantics)
  try {
    const out = execFileSync('gzip', ['-c', file], { maxBuffer: 64 * 1024 * 1024 });
    return out.length;
  } catch (e) {
    return gzipSync(readFileSync(file), { level: 6 }).length;
  }
}

// Static-import graph чанка: Vite пишет относительные импорты внутри
// assets ("./vue-<hash>.js" — from"/import"-форма; relative base '/vue/')
function importedChunks(file, allByName) {
  const src = readFileSync(file, 'utf8');
  const found = new Set();
  const re = /(?:from"|import")\.{0,2}\/?([A-Za-z0-9_-]+\.js)"/g;
  let m;
  while ((m = re.exec(src)) !== null) {
    if (allByName.has(m[1])) found.add(m[1]);
  }
  return found;
}

const failures = [];
const jsFiles = readdirSync(path.join(DIST, 'assets'))
  .filter((f) => f.endsWith('.js'))
  .sort();
if (jsFiles.length === 0) {
  console.error('ОШИБКА: dist/assets пуст — сначала npm run build');
  process.exit(2);
}

const byName = new Map(jsFiles.map((f) => [f, path.join(DIST, 'assets', f)]));
const roles = new Map(jsFiles.map((f) => [f, chunkRole(f)]));
const sizes = new Map();
for (const f of jsFiles) {
  const raw = readFileSync(byName.get(f)).length;
  const gz = gzipSize(byName.get(f));
  sizes.set(f, { raw, gz });
}

// (б)/(в) замыкание импортов входа КАЖДОЙ страницы: entry из dist html
// (регулярка входа /vue/assets/<name>.js не зависит от порядка
// link/script — требует .js; arch-review-001 п.5)
const pageClosures = new Map();
for (const pageName of PAGES) {
  const html = readFileSync(path.join(DIST, pageName + '.html'), 'utf8');
  const entryMatch = html.match(/\/vue\/assets\/([A-Za-z0-9_-]+\.js)/);
  if (!entryMatch || !byName.has(entryMatch[1])) {
    console.error(`ОШИБКА: вход ${pageName} не найден в dist HTML`);
    process.exit(2);
  }
  const closure = new Set([entryMatch[1]]);
  let grew = true;
  while (grew) {
    grew = false;
    for (const f of [...closure]) {
      for (const dep of importedChunks(byName.get(f), byName)) {
        if (!closure.has(dep)) { closure.add(dep); grew = true; }
      }
    }
  }
  pageClosures.set(pageName, closure);
}

const closureOf = new Map();
for (const [pageName, closure] of pageClosures) {
  for (const f of closure) {
    if (!closureOf.has(f)) closureOf.set(f, []);
    closureOf.get(f).push(pageName);
  }
}

console.log('Бюджеты NFR-26 на артефактах dist (gzip CLI, `gzip -c | wc -c`):');
console.log('чанк (роль)                                    raw      gzip');
for (const f of jsFiles) {
  const { role } = roles.get(f);
  const { raw, gz } = sizes.get(f);
  const pages = closureOf.has(f) ? ` [1-й заход: ${closureOf.get(f).join(', ')}]` : '';
  console.log(
    `${f} (${role})${pages}`.padEnd(46) +
      `${String(raw).padStart(7)}  ${String(gz).padStart(6)}`,
  );
}

// (а) vendor-чанки ≤ 150 КБ gzip каждый
for (const f of jsFiles) {
  if (roles.get(f).role !== 'vendor') continue;
  const gz = sizes.get(f).gz;
  if (gz > VENDOR_MAX) {
    failures.push(
      `vendor-чанк ${f}: ${(gz / KB).toFixed(1)} КБ gzip > 150 КБ (NFR-26а)`);
  }
}

// (б) JS первого захода КАЖДОЙ страницы ≤ 200 КБ gzip суммарно
for (const pageName of PAGES) {
  const closure = pageClosures.get(pageName);
  const firstLoad = [...closure].reduce((s, f) => s + sizes.get(f).gz, 0);
  if (firstLoad > FIRST_LOAD_MAX) {
    failures.push(
      `JS первого захода ${pageName}: ${(firstLoad / KB).toFixed(1)} КБ gzip > 200 КБ (NFR-26б)`);
  }
}

// (в) в замыкании входа страницы нет page-чанков других страниц (multi-entry)
for (const pageName of PAGES) {
  for (const f of pageClosures.get(pageName)) {
    const { role, name } = roles.get(f);
    if (role === 'page' && name !== pageName) {
      failures.push(`чужой page-чанк в бандле ${pageName}: ${f} (NFR-26в)`);
    }
  }
}

console.log('');
console.log(
  '(а) vendor-чанки: ' +
    jsFiles
      .filter((f) => roles.get(f).role === 'vendor')
      .map((f) => `${roles.get(f).name}=${(sizes.get(f).gz / KB).toFixed(1)} КБ`)
      .join(', ') +
    ` — бюджет ≤150 КБ каждый`);
for (const pageName of PAGES) {
  const closure = pageClosures.get(pageName);
  const firstLoad = [...closure].reduce((s, f) => s + sizes.get(f).gz, 0);
  console.log(
    `(б) JS первого захода ${pageName} (page+static graph): ` +
      [...closure].map((f) => roles.get(f).name).join(' + ') +
      ` = ${(firstLoad / KB).toFixed(1)} КБ gzip — бюджет ≤200 КБ`);
}
console.log('(в) чужие page-чанки в замыканиях входов: отсутствуют');

if (failures.length > 0) {
  console.error('');
  for (const f of failures) console.error('ПРОВАЛ: ' + f);
  console.error('Бюджеты NFR-26 НЕ соблюдены — сокращать зависимости (без новых библиотек).');
  process.exit(1);
}
console.log('');
console.log('OK: бюджеты NFR-26 соблюдены (страниц: ' + PAGES.length + ').');
