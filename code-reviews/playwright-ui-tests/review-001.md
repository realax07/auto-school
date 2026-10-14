# Code Review: tests/test_ui_playwright.py (playwright-ui-tests, task=2)

МЕТА: Reviewer-Delegation: spawned hermes chat session (role=code_reviewer, персональный прогон)
Дифф: +320 / −58, 6 новых e2e Playwright-тестов с session-фикстурой self-hosted uvicorn.
Проверка прогоном: `LD_LIBRARY_PATH=~/.cache/pw-libs/root/usr/lib/x86_64-linux-gnu .venv/bin/python -m pytest tests/test_ui_playwright.py -q` → **6 passed in 12.40s**.

---

## Проверка по чек-листу

### (1) Изоляция от прода — PASS
- `AUTOSCHOOL_DB_PATH` указывает в `tempfile.mkdtemp`; `backend/db.py:64` читает переменную на каждый вызов — прод-БД `data/app.db` не затрагивается. Эмпирически: mtime `data/app.db` (12:17:22 UTC) на ~10ч старше прогонов ревью, `git status data/` чист.
- Порт эфемерный (`bind(("127.0.0.1", 0))`), 8390 нигде в файле не упоминается; после прогона `ss -ltn` — порт 8390 свободен, leftover tmpdir = 0.
- Teardown гарантирован: `try/finally` вокруг `yield`, `terminate → wait(10) → kill → wait(10)` — покрывает и падение теста, и RuntimeError при неготовности сервера. Хороший паттерн.

### (2) Детерминизм — PASS
- Sleep нет; опрос готовности через `time.monotonic()` + `/api/health` с дедлайном 60s, с ранним выходом если `proc.poll()` не None.
- Порядок тестов не важен: session-scoped БД общая, но все сущности с `unique_email()` (uuid), фильтрация списков по email/id. Проверено: прогон зелёный.

### (3) Портативность — PASS
- `ROOT = Path(__file__).resolve().parent.parent`, cwd и PYTHONPATH для uvicorn от ROOT — жестких путей нет.
- LD_LIBRARY_PATH-зависимость задокументирована в docstring модуля (каталог распакованных .deb, chromium уже в ~/.cache/ms-playwright).

### (4) Assertions — в основном осмысленные, один тест-заглушка (см. F-1)
- Сильные места: кросс-проверка UI через API (`/api/auth/me` = 200 + email совпадает), статусная транзиция `waiting → approved`, computed-style проверка grid-колонок, геометрия модалки/сайдбара, expect/wait_for вместо голых assert на гонках.

### (5) TC-трассировка — PASS
- Каждый из 6 тестов имеет docstring с «TC-UI-0NN (change add-instructor-cabinet)»; матрица в test-model/express/playwright-ui-tests-express_close.md совпадает 1:1 с тестами.

---

## Findings

### F-1. MAJOR — вакуумная проверка `"</aside>" in page.content()` (TC-UI-005) — тест-заглушка
`assert "</aside>" in content` не может упасть никогда: Chromium парсит разметку в DOM и сериализует его заново, закрывающие теги дописываются парсером даже если их не было в исходнике. Проверено прямым экспериментом (probe в scratch): `set_content("<div class='app'><aside><b>sidebar</b><main>x</main></div>")` — закрывающий `</aside>` в исходнике отсутствует, но `"</aside>" in page.content()` → **True**. То есть назначение проверки («aside закрыт в разметке») не выполняется в принципе. Заменить на структурную проверку DOM, например: `page.evaluate("() => { const a = document.querySelector('aside'); const m = document.querySelector('main'); return m && a && a.compareDocumentPosition(m) & Node.DOCUMENT_POSITION_FOLLOWING; }")` — или просто удалить строку, т.к. соседние grid/bounding-box проверки уже покрывают макет.

### F-2. MINOR — TOCTOU-гонка эфемерного порта
Порт выбирается bind(0)→close, затем uvicorn биндит его повторно: в окне между close и стартом uvicorn порт может занять другой процесс → тест упадёт с невнятной ошибкой. Вероятность низкая (одиночный раннер), но при CI-параллелизме реальна. Вариант: передавать `--port 0`... uvicorn этого не поддерживает для отчета наверх — тогда хотя бы retry-once с новым портом при ConnectionRefused старта, либо документировать ограничение в docstring фикстуры.

### F-3. MINOR — диагностика старта сервера: stderr=DEVNULL
При падении uvicorn до готовности `RuntimeError` содержит только returncode; stderr девернут, и Новичок останется без единого лога. Дешёвое исправление: `stderr=subprocess.PIPE` и в ветке `proc.poll() is not None` приложить последние строки вывода к тексту исключения (читать неблокирующе или после wait).

### F-4. MINOR — потерянное покрытие из старых тестов без трассировки
Старый TC-UI-002 проверял центрирование иконки загрузки на анкете (`abs(frame_cy - icon_cy) <= 6`); в новом TC-UI-004 эта проверка отсутствует, и в матрице express_close про неё ни слова. Либо вернуть assertion в TC-UI-004, либо зафиксировать в матрице решение о снятии проверки — сейчас это молчаливая регрессия покрытия, которую Саботажник любит эксплуатировать.

### F-5. NIT — утечка tmpdir при падении Popen
Если `subprocess.Popen` бросит (например, нет uvicorn), `finally` еще не входит — `tmpdir` останется на диске. Перенести `mkdtemp` внутрь try или обернуть Popen в собственный try/except с rmtree.

### F-6. NIT — PYTHONPATH перетирается
`env.update({"PYTHONPATH": str(ROOT)})` затирает унаследованный PYTHONPATH родителя. Работает (cwd=ROOT), но безопаснее `env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")`.

### F-7. NIT — TC-UI-006 не UI-тест
`test_admin_moderation_approve_reflects_status` не принимает `page`/`browser` — это чисто API-тест в файле Playwright UI-тестов (и он не требует установки браузера). Не блокер (docstring честно говорит «через API», и это осмысленный smoke админ-потока), но место ему в api-наборе или с пометкой в матрице.

### F-8. NIT — явный headless
`p.chromium.launch()` полагается на дефолт headless=True. Для инструмента, который «сам поднимает сервер», явный `headless=True` снимает вопрос при будущих апгрейдах playwright.

## Security-персона
- Тестовый админ `ui-admin` / `ui-admin-pass-2026` и `SECRET=ui-tests-secret` живут только в env subprocess с tmp-БД и эфемерным портом на 127.0.0.1 — в прод не просачиваются; хардкод плейтестовых паролей в тесте — норма.
- `admin_login()` и админ-токены не пишутся в логи/скрины; `page.screenshot` в тестах не вызывается.
- Деструктивных действий нет: rmtree только по собственному mkdtemp-каталогу (`ignore_errors=True`).

## Вердикты per-finding
| Finding | Severity |
|---|---|
| F-1 vacuous `</aside>` check | MAJOR |
| F-2 ephemeral port TOCTOU | MINOR |
| F-3 stderr=DEVNULL при диагностике старта | MINOR |
| F-4 потерянное покрытие (иконка загрузки) | MINOR |
| F-5 tmpdir leak при Popen-fail | NIT |
| F-6 PYTHONPATH перетирается | NIT |
| F-7 API-тест в UI-файле | NIT |
| F-8 явный headless | NIT |

## Итоговый вердикт: **RETURN**

Блокируют возврат два MINOR + один MAJOR:
- F-1 — ассерт, который физически не может упасть, это тест-заглушка в TC-UI-005 (по критерию (4) чек-листа — прямое попадание);
- F-3 — без stderr диагностика упавшего старта сервера превращается в гадание (критерий «надежность» для Новичка);
- F-4 — молчаливо снятое покрытие без трассировки в матрице.

Изоляция, детерминизм, портативность и TC-трассировка — в порядке; после точечных правок F-1/F-3/F-4 (плюс желательны F-2) — повторное ревью, ожидаю APPROVE. Тесты при ревью не правились; всё, что менялось, — этот артефакт.
