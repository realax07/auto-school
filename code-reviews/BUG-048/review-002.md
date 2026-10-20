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
