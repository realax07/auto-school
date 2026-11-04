// Спринт 9 (change add-vue-framework-pilot, задача 4.1; NFR-26): проверка
// бюджетов чанков НА АРТЕФАКТАХ сборки dist/. Запуск: npm run build &&
// npm run check:budgets (повторяется на приемке каждого шага миграции —
// tasks.md 4.1, ADR-008 п.3).
//
// Бюджеты (requirements-sprint9.md NFR-26):
//   (а) каждый vendor-чанк ≤ 150 КБ gzip;
//   (б) суммарный JS первого захода пилотной страницы (page-чанк +
//       static-import graph: shared + vue и все загружаемые ими чанки)
//       ≤ 200 КБ gzip;
//   (в) в бандле пилота нет кода немигрированных страниц (multi-entry):
//       замыкание импортов входа состоит только из его page-чанка,
//       'shared' и vendor-чанков — чужих page-чанков нет.
//
// Роли чанков — по правилам manualChunks (vite.config.mjs, ADR-008):
// имя чанка до хэша — 'shared' (свой код), имя входа ('instructors-
// pending'), остальные имена — vendor-чанки по пакетам ('vue',
// '@vue/*' → 'vue'). gzip-размер — дословно `gzip -c <file> | wc -c`
// (задача 4.1; фолбэк zlib level 6, новых зависимостей нет).
import { readdirSync, readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { gzipSync } from 'node:zlib';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const DIST = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'dist');
const VENDOR_MAX = 150 * 1024; // (а) КБ → байты
const FIRST_LOAD_MAX = 200 * 1024; // (б)
const KB = 1024;

function chunkRole(file) {
  // instructors-pending-<hash>.js / shared-<hash>.js / vue-<hash>.js
  const base = path.basename(file, '.js');
  const name = base.replace(/-[A-Za-z0-9_-]{8}$/, '');
  if (name === 'shared') return { name, role: 'shared' };
  if (name === 'instructors-pending') return { name, role: 'page' };
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

// (в) замыкание импортов входа пилотной страницы: entry из dist html
const html = readFileSync(path.join(DIST, 'instructors-pending.html'), 'utf8');
const entryMatch = html.match(/\/vue\/assets\/([A-Za-z0-9_-]+\.js)/);
if (!entryMatch || !byName.has(entryMatch[1])) {
  console.error('ОШИБКА: вход pilot-страницы не найден в dist HTML');
  process.exit(2);
}
const entry = entryMatch[1];
const closure = new Set([entry]);
let grew = true;
while (grew) {
  grew = false;
  for (const f of [...closure]) {
    for (const dep of importedChunks(byName.get(f), byName)) {
      if (!closure.has(dep)) { closure.add(dep); grew = true; }
    }
  }
}

console.log('Бюджеты NFR-26 на артефактах dist (gzip CLI, `gzip -c | wc -c`):');
console.log('чанк (роль)                                    raw      gzip');
const sizes = new Map();
for (const f of jsFiles) {
  const raw = readFileSync(byName.get(f)).length;
  const gz = gzipSize(byName.get(f));
  sizes.set(f, gz);
  const { role } = roles.get(f);
  const inClosure = closure.has(f) ? ' [1-й заход]' : '';
  console.log(
    `${f} (${role})${inClosure}`.padEnd(46) +
      `${String(raw).padStart(7)}  ${String(gz).padStart(6)}`,
  );
}

// (а) vendor-чанки ≤ 150 КБ gzip каждый
for (const f of jsFiles) {
  if (roles.get(f).role !== 'vendor') continue;
  const gz = sizes.get(f);
  if (gz > VENDOR_MAX) {
    failures.push(
      `vendor-чанк ${f}: ${(gz / KB).toFixed(1)} КБ gzip > 150 КБ (NFR-26а)`);
  }
}

// (б) JS первого захода ≤ 200 КБ gzip суммарно
const firstLoad = [...closure].reduce((s, f) => s + sizes.get(f), 0);
if (firstLoad > FIRST_LOAD_MAX) {
  failures.push(
    `JS первого захода: ${(firstLoad / KB).toFixed(1)} КБ gzip > 200 КБ (NFR-26б)`);
}

// (в) в замыкании входа нет page-чанков других страниц (multi-entry)
for (const f of closure) {
  const { role, name } = roles.get(f);
  if (role === 'page' && name !== 'instructors-pending') {
    failures.push(`чужой page-чанк в бандле пилота: ${f} (NFR-26в)`);
  }
}

console.log('');
console.log(
  `(а) vendor-чанки: ` +
    jsFiles
      .filter((f) => roles.get(f).role === 'vendor')
      .map((f) => `${roles.get(f).name}=${(sizes.get(f) / KB).toFixed(1)} КБ`)
      .join(', ') +
    ` — бюджет ≤150 КБ каждый`);
console.log(
  `(б) JS первого захода (page+static graph): ` +
    [...closure].map((f) => roles.get(f).name).join(' + ') +
    ` = ${(firstLoad / KB).toFixed(1)} КБ gzip — бюджет ≤200 КБ`);
console.log('(в) чужие page-чанки в замыкании входа: отсутствуют');

if (failures.length > 0) {
  console.error('');
  for (const f of failures) console.error('ПРОВАЛ: ' + f);
  console.error('Бюджеты NFR-26 НЕ соблюдены — сокращать зависимости (без новых библиотек).');
  process.exit(1);
}
console.log('');
console.log('OK: бюджеты NFR-26 соблюдены.');
