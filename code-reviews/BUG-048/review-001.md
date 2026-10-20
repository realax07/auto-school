# Code Review — BUG-048, итерация 1

- **Ветка:** fix/bug-048-photo-uploads (c9e3206) vs main
- **Дифф:** git diff main...HEAD --stat → frontend/instructor-apply.html (+119/-x),
  frontend/instructor-dashboard.html (my-cars, +48), tests/test_instructor_pages.py,
  tests/test_ui_playwright.py (+231), test-model/plans/PLAN-BUG-046.md
- **Reviewer-Delegation:** deleg_spawn144324141 — spawned hermes chat session
  (role=code_reviewer, BUG-048)
- **Вердикт: RETURN** (1 major, 1 medium, 3 minor)

## Проверка по чек-листу задачи

1. **XSS** — ОК. Миниатюры везде через `URL.createObjectURL` → `img.src`
   (instructor-apply: `licenseThumb.src`, my-cars: `thumb.src`), тексты ошибок —
   через `textContent` (`showLicenseError`, `mcShowPhotoError`, `pdfName`).
   `innerHTML` в диффе отсутствует.
2. **FormData — полнота** — ОК. Все 15 контрактных полей sdd §15.1
   (`fd.append('surname'…'consent')`) + `license_photo` — ровно тот же набор, что
   был в JSON payload; ничего не потеряно при переходе. `consent:'true'/'false'`
   корректно разбирается бэкендом (backend/instructors.py `_parse_request`:
   str → lower in true/1/on/да). `experience`/`experience_years` совместимы.
3. **422 у поля** — ОК с оговоркой (см. MED-1): ошибки файла (413/415/422 с
   «Файл: …») показываются у поля загрузки (`#license-error`, role=alert) и под
   формой (`#notice`); в my-cars — `#up-photo-err` + тост. Подтверждено e2e.
4. **admin-фото: токен, 404-плейсхолдер** — ОК (код до-диффовый, на main —
   PLAN-BUG-046 это фиксирует). `fetch(…license-image, {X-Admin-Token})` → blob →
   objectURL; 404/401 → «Изображение недоступно», без ВУ → плейсхолдер
   «Файл ВУ не приложен», не битая картинка. Покрыто TC-UI-022 на живом бэкенде.
5. **e2e не вакуумные** — ОК. TC-UI-020 сверяет байты файла на бэкенде через
   админ-эндпоинт (resp.read() == PNG_1PX, Content-Type image/png);
   TC-UI-021 проверяет, что заявка с битым файлом НЕ создана (NFR-6);
   TC-UI-023 сверяет `has_photo` через GET /api/instructor/cars. Не моки.
6. **Memory leaks objectURL** — ОК. apply: `resetLicensePreview()` revoke при
   каждой смене файла; my-cars: revoke в `mcResetUpload` и в `change`-хендлере;
   admin-карточка: revoke в `closeInstructorCard` (вкл. Escape/backdrop).

## Прогон

- `export LD_LIBRARY_PATH=~/.cache/pw-libs/… && .venv/bin/python -m pytest
  tests/test_ui_playwright.py -q` → **31 passed** in 64s
- `tests/test_instructor_pages.py -q` → **13 passed**

## Findings

### MAJ-1. Мёртвый PDF-путь: клиент пропускает PDF, бэкенд принимает только JPEG/PNG — гарантированный 422 после «успешной» валидации

`frontend/instructor-apply.html` (commit c9e3206):
- `validateLicenseFile()` пропускает `application/pdf` и расширение `.pdf`;
- есть выделенный UI «карточки PDF» (`#license-pdf` с `pdfName`);
- `accept="image/jpeg,image/png,image/*,.pdf"` — плюс `image/*` впускает
  webp/gif/bmp.

Бэкенд жёстко JPEG/PNG по magic bytes: `backend/uploads.py::sniff_image` →
422 «Файл: допустимы только изображения JPEG или PNG». Итог: пользователь
выбирает валидный PDF, видит «карточку файла» (миниатюра валидна), жмёт
«Продолжить» — и получает ошибку формата. Ветка не выполняет требование задачи
«accept-атрибут JPEG/PNG».

Усугубляет: в working tree есть **незакоммиченное** изменение подписи
«JPG, PNG или PDF · до 5 МБ» → «JPG или PNG · до 5 МБ» — полумера (JS-валидация,
`accept` и `#license-pdf` по-прежнему PDF пропускают), и в PR оно не попадет.

**Fix (на выбор, но последовательно):** либо убрать PDF из клиента —
`accept="image/jpeg,image/png"`, `validateLicenseFile` только jpeg/png, удалить
`#license-pdf`-блок, закоммитить правку подписи; либо расширить `sniff_image`
до PDF (отдельная задача, контракта на PDF нет). Рекомендую первое.

### MED-1. Любой 422 показывается как ошибка файла ВУ

`instructor-apply.html`: `if(res.status===413||res.status===415||res.status===422||msg.indexOf('Файл')===0){showLicenseError(msg);}`
— серверные 422 не про файл («Email: уже зарегистрирован», «Стаж: …», «Тело
запроса: неверный формат полей анкеты») отрисуются красным текстом у поля
загрузки ВУ. Пользователю с дублем email показывают ошибку не в том поле;
эвристика по префиксу строки «Файл» хрупка. Показывать у поля только 413/415 и
422 с `error`, начинающимся с «Файл».

### MIN-1. Расхождение текстов ошибок формата

Клиент: «Файл: допустимы только изображения JPEG, PNG **или PDF**»; сервер:
«Файл: допустимы только изображения JPEG или PNG». После фикса MAJ-1 привести
клиентский текст к серверному (тексты контракта, e2e ассертит именно серверный).

### MIN-2. `clearLicenseError(msg)` — параметр не используется; смесь `var` и `const` в одном скрипте. Косметика.

### MIN-3. При успешном сабмите анкеты последний objectURL не revoked перед `location.href` — освобождается навигацией, утечки нет; для симметрии можно revoke в ветке 200.

## Замечания вне диффа (не блокируют, зафиксировать)

- `admin-dashboard.html::loadLicenseImage` вставляет `res.error` из ответа API
  через `innerHTML` (строка «Изображение недоступно…»). Значение контролируется
  сервером, риск низкий, но по гигиене — `textContent`.
- Незакоммиченный файл в working tree — см. MAJ-1; на итерацию 2: рабочая
  ветка должна быть чистой перед ревью.

## Итог

RETURN: MAJ-1 (противоречие клиент/бэкенд по формату файла + невыполненный
пункт скоупа «accept JPEG/PNG») и MED-1 (ошибки не у своих полей) должны быть
исправлены до APPROVE. Остальное — архитектурно корректно: multipart-переход
полный, миниатюры без innerHTML, objectURL ревокаются, e2e проверяют реальное
состояние бэкенда, 31/31 + 13/13 зелёные.
