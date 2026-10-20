# Code Review — BUG-048, итерация 2

- **Ветка:** fix/bug-048-photo-uploads (1467db1) vs main
- **Дифф итерации 2:** git diff c9e3206..1467db1 — только frontend/instructor-apply.html
  (-34/+21) и code-reviews/BUG-048/review-001.md; рабочее дерево чистое (замечание
  итерации 1 про незакоммиченные правки снято)
- **Reviewer-Delegation:** deleg_spawn202610201706599fbf66 — spawned hermes chat session
  (role=code_reviewer, итерация 2)
- **Вердикт: RETURN** (MAJ-1 закрыт; открыты MED-1 — вне скоупа task=3 — и
  гигиена innerHTML admin-карточки)

## Статус находок итерации 1

### MAJ-1. Мёртвый PDF-путь — FIXED

Проверено по всему `frontend/` (`grep -rni 'pdf'` → 0 совпадений):

- `validateLicenseFile()`: okType только `image/jpeg|jpg|png`, okExt только
  `jpg|jpeg|png`; ветка «PDF без растровой миниатюры» и `licensePdf`/`pdfName`
  из JS удалены;
- CSS `#license-pdf` (3 правила + `.has-file.pdf`) удалён;
- `accept="image/jpeg,image/png"` — `image/*` и `.pdf` убраны;
- клиентский текст ошибки `Файл: допустимы только изображения JPEG или PNG`
  == серверному (`backend/uploads.py:45`), включая fallback для 415;
- подпись «JPG или PNG · до 5 МБ» закоммичена.

Противоречие клиент/бэкенд устранено, пункт скоупа «accept JPEG/PNG» выполнен.

### MED-1. Любой 422 показывается как ошибка файла ВУ — NOT-FIXED (вне скоупа task=3)

`instructor-apply.html:113`: условие
`res.status===413||415||422||msg.indexOf('Файл')===0` не изменилось — серверные
422 не про файл («Email: уже зарегистрирован» и т.п.) по-прежнему рисуются у
поля загрузки ВУ. В итерацию 2 не входило; остаётся открытым гейтом до APPROVE
(как и в review-001).

### MIN-1. Расхождение текстов — FIXED

Клиент и сервер: «Файл: допустимы только изображения JPEG или PNG» (все три
места: validateLicenseFile, 415-fallback, подпись формата). Расхождений нет.

### MIN-2. `clearLicenseError(msg)` — unused param — FIXED

Параметр удалён: `function clearLicenseError(){…}`; все 2 вызова без аргументов.
Смесь `const`/`var` в скрипте сохраняется (первая строка — контекст с main),
косметика, не блокирует.

### Гигиена innerHTML admin-карточки — NOT-FIXED

`admin-dashboard.html:330` (`loadLicenseImage`):
`ph.innerHTML='<span>Изображение недоступно'+(res.error?'<br>'+res.error:'')+'</span>'`
— `res.error` из ответа API по-прежнему интерполируется в innerHTML. Файл в
итерации 2 не менялся (в диффе ветки отсутствует). Значение контролируется
сервером, эксплуатация маловероятна, но раз пункт включён в задачу — нужно
заменить на построение через `textContent` (два текстовых узла / `<br>`).

## «Нового не внесено?» — нет

Дифф итерации 2 — чистое удаление PDF-пути и выравнивание текстов; новой
логики, новых innerHTML/eval, новых зависимостей нет. Миниатюры по-прежнему
через `objectURL`→`img.src`, ошибки через `textContent`, revoke-логика не
тронута.

## Прогон

- `export LD_LIBRARY_PATH=~/.cache/pw-libs/… && .venv/bin/python -m pytest
  tests/test_ui_playwright.py -q` → **31 passed** in 70.35s

## Итог

RETURN. MAJ-1, MIN-1, MIN-2 — закрыты, регрессий не внесено, e2e зелёные
(31/31). До APPROVE остаются: MED-1 (422 не про файл — у поля ВУ; не входил в
task=3, требует отдельной итерации) и гигиена `innerHTML` в
`admin-dashboard.html::loadLicenseImage` (textContent вместо интерполяции
`res.error`). MIN-3 (revoke перед редиректом) — опционально, не блокирует.

---

# Итерация 3

- **Ветка:** fix/bug-048-photo-uploads (9f204de) vs 1467db1
- **Дифф итерации 3:** git diff 1467db1..9f204de — только
  frontend/instructor-apply.html (+2/-2) и frontend/admin-dashboard.html
  (+15/-4) плюс этот артефакт; рабочее дерево чистое (`git status` пуст).
- **Reviewer-Delegation:** deleg_spawn20261020171504 — spawned hermes chat
  session (role=code_reviewer, итерация 3)
- **Вердикт: APPROVE** (оба открытых пункта итерации 2 закрыты, нового не
  внесено, e2e 31/31)

## Статус открытых пунктов итерации 2

### MED-1. 422 не про файл рисуются у поля ВУ — FIXED

`instructor-apply.html:113`: условие заменено на
`res.status===413||res.status===415||(res.status===422&&msg.indexOf('Файл')===0)`
— `showLicenseError(msg)` вызывается только для файловых ошибок (413/415 и
422 с серверным текстом, начинающимся с «Файл»); все остальные 422
(«Email: уже зарегистрирован», «Тело запроса: неверный формат», «Пароль: …» и
т.п.) идут только в общий notice (`notice.textContent=msg`, строка 116).

Сверка с сервером (`backend/instructors.py`): у `/api/instructors/apply`
префикс «Файл» имеют ровно два 422 — из `uploads.sniff_image`
(«Файл: изображение больше 5 МБ» / «Файл: допустимы только изображения JPEG
или PNG», `backend/uploads.py:40,45`); полевые и структурные ошибки 422
начинаются с других префиксов («Email», «Телефон», «Тело запроса», …).
Ложных срабатываний условия нет, файловые ошибки не потеряны. Файловые
ошибки по-прежнему дублируются и в notice — сохранение прежнего поведения,
не регресс.

### Гигиена innerHTML admin-карточки — FIXED

`admin-dashboard.html:308-343` (`loadLicenseImage`): введён хелпер
`phText(lines)` — очистка `ph.innerHTML=''` (без данных), затем
`createElement('span')` + `createElement('br')` + `createTextNode(t)` для
каждой строки. Все четыре места прежней интерполяции заменены:

- `!hasPhoto` → `phText(['Файл ВУ не приложен','заявка без изображения'])`;
- «Загрузка…» → `phText(['Загрузка…'])`;
- ошибка API → `phText(res.error?['Изображение недоступно',res.error]:[…])` —
  `res.error` теперь только текстовый узел, интерполяции в innerHTML нет;
- `.catch` → `phText(['Изображение недоступно'])`.

Успешный путь не тронут: `ph.innerHTML=''` (очистка) → `createElement('img')`
→ `objectURL` в `img.src` → `appendChild`; revoke-логика в
`closeInstructorCard` без изменений. `grep -n innerHTML frontend/` —
оставшиеся вхождения либо очистки (`=''`), либо статические строки вне скоупа
задачи (instructor-dashboard/cabinet — вне BUG-048, новыми не являются).

## «Нового не внесено?» — нет

Дифф итерации 3 ограничен двумя целевыми участками: условие строк 113-115 в
instructor-apply.html и тело `loadLicenseImage` в admin-dashboard.html.
Новой логики, новых источником данных в innerHTML, eval, новых зависимостей,
изменений бэкенда/тестов нет. Формат отображения админ-карточки (span + br)
воспроизводит прежний innerHTML-вариант 1:1.

## Прогон (итерация 3)

- `export LD_LIBRARY_PATH=~/.cache/pw-libs/root/usr/lib/x86_64-linux-gnu &&
  .venv/bin/python -m pytest tests/test_ui_playwright.py -q`
  → **31 passed** in 56.87s

## Итог итерации 3

APPROVE. Все находки итераций 1-2 закрыты: MAJ-1, MIN-1, MIN-2 (итерация 2),
MED-1 и гигиена innerHTML admin-карточки (итерация 3) — FIXED; нового не
внесено; e2e зелёные (31/31). MIN-3 (revoke перед редиректом) остаётся
опциональным, не блокирует. Замечаний, блокирующих merge, нет.
