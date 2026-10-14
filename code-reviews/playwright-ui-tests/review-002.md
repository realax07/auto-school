# Code Review: tests/test_ui_playwright.py + frontend/instructor-apply.html (playwright-ui-tests, итерация 2)

МЕТА: Reviewer-Delegation: spawned hermes chat session (role=code_reviewer, итерация 2)
Дифф итерации 3: tests/test_ui_playwright.py (снят xfail с test_instructor_apply_upload_icon_centered, 7 тестов) + frontend/instructor-apply.html (root-cause CSS-фикс: `label.upload{...}` вместо `.upload{...}`, `.upload span:not(.upload-icon)` вместо `.upload span`).
Проверка прогоном (обязательный): `export LD_LIBRARY_PATH=~/.cache/pw-libs/root/usr/lib/x86_64-linux-gnu && .venv/bin/python -m pytest tests/test_ui_playwright.py -v` → **7 passed in 11.36s** (XFAIL в выводе отсутствует).

---

## Верификация устранения findings review-001

### F-1 (MAJOR, вакуумный `"</aside>" in page.content()`) — FIXED, VERIFIED
Заменён на структурную геометрию, способную упасть (tests/test_ui_playwright.py:366–379):
- `.app > aside` count == 1 и `.app > main` count == 1 — прямые дети-соседи (упадёт при пропаже/переносе любого из элементов);
- computed style: `display == grid` и ровно 2 колонки (фильтр `parseFloat(v) > 0` отсекает named/implicit-треки);
- bounding-box: `aside.x + aside.width <= main.x + 1` — сайдбар физически левее main;
- ФИО из API (`.user b` = «Громов Борис Арсеньевич») — содержательная, а не разметочная проверка.
Ассертов, которые не могут упасть, в тесте не осталось.

### F-3 (MINOR, stderr=DEVNULL при диагностике старта) — FIXED, VERIFIED
stderr uvicorn пишется в `<tmpdir>/uvicorn-stderr.log` (строка 141, 148); `_stderr_tail()` читает последние 20 строк; при `proc.poll() is not None` до готовности RuntimeError содержит `attempt/code/последняя ошибка health/хвост stderr` (строки 172–181). OSError при недоступном логе деградирует в плейсхолдер, не маскируя исходную ошибку. Новичок получит читаемый диагноз.

### F-4 (MINOR, потерянное покрытие центрирования иконки) — FIXED, VERIFIED
Возвращено отдельным тестом `test_instructor_apply_upload_icon_centered` (строки 312–326): `abs(frame_cy - icon_cy) <= 6` на `/instructors/apply`, expect-видимость frame/icon перед замером, диагностичное сообщение с фактическим отклонением. Трассировка: docstring ссылается на старый TC-UI-002 и F-4 review-001; в матрице express_close заведена строка TC-UI-004b.

## Верификация НОВОГО диффа итерации 3

### CSS-фикс (frontend/instructor-apply.html) — root-cause подтверждён, визуальная логика не сломана
Проверка каскада по разметке: `.upload` — это `label class="upload"` внутри `.field` (строка 23 HTML), значит старое `.upload{display:flex}` (0,1,0) действительно перебивалось `.field label{display:block}` (0,1,1). Фикс `label.upload` (0,1,1, позже в таблице) — корректный перебой по порядку, специфичность не завышена. Сопутствующий фикс `.upload span:not(.upload-icon)` (0,2,1) исключает `<span class="upload-icon">` из-под `margin-top:4px`, восстанавливая `margin:auto 0`; текстовая подпись (`<span>JPG, PNG или PDF…` внутри wrapper `style="flex:1"`) под правило по-прежнему попадает — стилистика подписи сохранена 1:1 с исходником.

Эмпирическая верификация (probe ревьюера на живой странице, uvicorn + chromium,desktop 1440px / tablet 820px (mq 850) / mobile 400px (mq 560)):

```
[desktop]     display.upload=flex icon_dev=0.00px caption_in_frame=True btn_in_frame=True horiz_overflow=False
[tablet-850]  display.upload=flex icon_dev=0.00px caption_in_frame=True btn_in_frame=True horiz_overflow=False
[mobile-560]  display.upload=flex icon_dev=0.00px caption_in_frame=True btn_in_frame=True horiz_overflow=False
```

- центрирование иконки: фактическое отклонение 0.00px на всех трёх вьюпортах (допуск 6px выполнен с запасом, не «на грани»);
- подпись «Прикрепить фото или скан» (`.upload strong#file-name`) видима, внутри фрейма, не перекрывает иконку;
- кнопка «Выбрать файл» (`#pick-file`, `.upload button{margin-left:auto}`) на месте, в границах фрейма;
- мобильные media-queries (850px/560px) диффом не затронуты (context-строки), правил для `.upload` в них и не было — на 400px горизонтального переполнения нет.

### Снятие xfail — VERIFIED, допуск НЕ расширялся
`grep xfail tests/test_ui_playwright.py` → 0 совпадений; маркер удалён. Допуск в ассерте остался `<= 6` (строка 325) — расширения допуска нет, требование соблюдено. Тест проходит зелёным в составе полного набора (7 passed), в матрице итерация 3 зафиксирована («Снят xfail … без расширения допуска», 2 зелёных прогона подряд).

### Побочно: F-2/F-5/F-6/F-8 из review-001 — тоже закрыты
F-2: retry с новым портом (`PORT_START_ATTEMPTS = 2`) + документирование в docstring фикстуры. F-5: Popen обёрнут в try/except, tmpdir убирает finally. F-6: PYTHONPATH дописывается через `os.pathsep`. F-8: `launch(headless=True)` явно. F-7 (API-тест TC-UI-006 в UI-файле) остаётся как есть — NIT, матрица честно помечает «через API», не блокер.

## Новые findings итерации 3

### N-1. NIT — устаревшая строка матрицы TC-UI-004b
В таблице «Покрытие» express_close строка TC-UI-004b всё ещё содержит «XFAIL: frontend-баг центрирования (см. «Итерация 2»)», при том что ниже в том же документе итерация 3 фиксирует снятие xfail. Читатель таблицы (единственный вход для трассировки) получит противоречивое состояние. Поправить строку: «покрытие активно, xfail снят в итерации 3 (root-cause CSS-фикс)». Неблокер: документ явно суперсидится разделом «Итерация 3» и финальной строкой «без xfail/XFAIL».

### N-2. NIT — расхождение ID в docstring и матрице
Docstring теста иконки называет его «TC-UI-004», в матрице он заведён как TC-UI-004b (TC-UI-004 — тест валидной анкеты). Формальная трассировка 1:1 чуть размыта. Неблокер.

### N-3. NIT — неточность в CSS-комментарии
Комментарий в instructor-apply.html говорит «margin-top:auto у .upload-icon», фактическое правило — `margin:auto 0`. На поведение не влияет (по горизонтали auto-отступы в flex-контейнере с `justify-content:center` нейтральны, проверено probe'ом: icon_dev=0.00px). Косметика.

## Вердикты per-finding

| Finding | Было | Стало |
|---|---|---|
| F-1 вакуумный `</aside>` (TC-UI-005) | MAJOR | FIXED/VERIFIED — структурная геометрия, падоспособна |
| F-3 stderr=DEVNULL при диагностике старта | MINOR | FIXED/VERIFIED — stderr-файл + хвост в RuntimeError |
| F-4 потерянное покрытие иконки | MINOR | FIXED/VERIFIED — TC-UI-004b, допуск 6px, в матрице |
| F-2 TOCTOU порта | MINOR | FIXED (retry-once + docstring) |
| F-5/F-6/F-8 | NIT | FIXED |
| F-7 API-тест в UI-файле | NIT | открыт (осознанно, помечен в матрице) — не блокер |
| N-1 устаревшая XFAIL-строка матрицы | — | NIT (новый) |
| N-2 TC-UI-004 vs TC-UI-004b в docstring | — | NIT (новый) |
| N-3 неточность CSS-комментария | — | NIT (новый) |

## Итоговый вердикт: **APPROVE**

Все три блокирующих finding'а review-001 (F-1 MAJOR, F-3 MINOR, F-4 MINOR) устранены и верифицированы прогоном; дифф итерации 3 — корректный root-cause фикс (а не обход ассерта): каскадная причина подтверждена анализом специфичности по живой разметке, визуальная логика (подпись, кнопка, подпись-описание, мобильные media-queries) не задета — probe на трёх вьюпортах дал отклонение иконки 0.00px без горизонтального переполнения. xfail снят без расширения допуска (остался `<= 6px`), факт подтверждён обязательным прогоном: 7 passed. Остались три NIT (N-1/N-2/N-3) — в бэклог, возврата не требуют.

Тесты и прод-код при ревью не правились; всё, что менялось, — этот артефакт и probe-скрипт вне репозитория (~/.hermes/cache/scratch/probe_upload_css.py).
