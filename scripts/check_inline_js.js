// Проверка синтаксиса inline-<script> страниц (Спринт 3, задача 7).
// Запуск: node scripts/check_inline_js.js file1.html ...
const fs = require('fs');
const {execFileSync} = require('child_process');
const os = require('os');
const path = require('path');

const files = process.argv.slice(2);
if (!files.length) {
  console.error('usage: node scripts/check_inline_js.js file.html ...');
  process.exit(2);
}
let failed = false;
for (const f of files) {
  const html = fs.readFileSync(f, 'utf8');
  const blocks = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)];
  blocks.forEach((m, i) => {
    const tmp = path.join(os.tmpdir(), `inline-${process.pid}-${i}.js`);
    fs.writeFileSync(tmp, m[1]);
    try {
      execFileSync(process.execPath, ['--check', tmp], {stdio: 'pipe'});
      console.log(`${f} [script ${i}]: OK`);
    } catch (e) {
      failed = true;
      console.log(`${f} [script ${i}]: SYNTAX ERROR\n${e.stderr}`);
    }
    fs.unlinkSync(tmp);
  });
}
process.exit(failed ? 1 : 0);
