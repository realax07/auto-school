# Закрытие задачи: playwright-ui-tests (express)

Задача: закрыть пробел Playwright UI-тестов сервиса auto-school.
Изменён ровно один файл: `tests/test_ui_playwright.py` (прод-код, backend, frontend — не тронуты).

## Что сделано

Каркас `tests/test_ui_playwright.py` переписан в самодостаточный набор из 6 e2e-тестов:

- **Session-фикстура `server`**: поднимает `uvicorn backend.app:app` на `127.0.0.1:<ephemeral port>` (порт выдаёт ядро через bind на :0), `AUTOSCHOOL_DB_PATH` указывает на временный файл (`AUTOSCHOOL_DB_PATH` в tempfile-каталоге, удаляется в teardown вместе с процессом: terminate → wait → kill → rmtree). Обращений к `data/app.db` и прод-порту 8390 нет. Готовность — опрос `/api/health` до дедлайна (без sleep). Админ-env (`ADMIN_USER`/`ADMIN_PASSWORD_HASH` cost 12/`SECRET`) генерируется фикстурой — тесты не зависят от окружения машины. `UI_TESTS` и прежний `skipif` сняты.
- **API-хелпер** на stdlib `urllib` (без внешних зависимостей): заявки инструктора, админ-логин, модерация, `/api/auth/me`.
- **Playwright sync API**, без sleep — только `expect`/`wait_for_url`/`to_be_visible`/`to_have_text`; viewport 1440x900; свежий контекст на тест (изоляция sessionStorage).

### Покрытие (каждый тест — docstring с трассировкой «TC-UI-0NN (change add-instructor-cabinet)»)

| Тест | Сценарий |
|---|---|
| TC-UI-001 | Лендинг ученика: загрузка, «Войти» → модалка входа `#m-login` видима и по центру экрана (допуски 30px X / 80px Y) |
| TC-UI-002 | Регистрация ученика: заполнение `#reg-*`, сабмит, редирект `/cabinet`, `session_token` валиден (`/api/auth/me` = 200, email совпадает), ФИО отрисовано в `.uname` |
| TC-UI-003 | Лендинг инструкторов: бренд `.brand em` = «Сбер», цвет rgb(53, 216, 121), CTA-кнопки шапки рядом (зазор < 40px), в теле нет своего «Войти» |
| TC-UI-004 | Анкета инструктора: ФИО — три поля (`#surname/#name/#patronymic`), валидный сабмит (формат `own` → обязателен госномер) → `/instructors/pending`, h1 «Заявка на рассмотрении» |
| TC-UI-004b | Анкета инструктора: центрирование иконки загрузки ВУ (`.upload` vs `.upload-icon`, вертикальный центр, допуск 6px) — покрытие возвращено из старого TC-UI-002 (F-4 review-001, итерация 2); XFAIL: frontend-баг центрирования (см. «Итерация 2») |
| TC-UI-005 | Вход approved-инструктора → `/instructor/dashboard`: структурная вёрстка — `aside` и `main` существуют как прямые дети `.app` (sibling-проверка), `.app` — grid ровно с 2 колонками (computed style), main правее сайдбара (границы не пересекаются); ФИО «Громов Борис Арсеньевич» из API в шапке (`.user b`) |
| TC-UI-006 | Админ-модерация через API: approve заявки → ok, повторный GET списка показывает `status: waiting → approved` |

Два багфикса против первой ревизии тестов: (1) на `/instructors` бренд размечен `<em>`, а не `<b>` (как на `/instructors/apply`); (2) id заявки для approve берётся из `GET /api/admin/instructor-applications` по email, а не константой — БД общая на session, id не равен 1.

## Как запускается

```
cd ~/auto-school && .venv/bin/python -m pytest tests/test_ui_playwright.py -v
```

На этом хосте системных библиотек chromium нет (нет root для `playwright install-deps`), поэтому они доставлены без рута: нужные .deb скачаны `apt-get download` и распакованы в `~/.cache/pw-libs/root` (вне репозитория). Пользователь-специфичный шаг (не входит в тесты):

```
export LD_LIBRARY_PATH=~/.cache/pw-libs/root/usr/lib/x86_64-linux-gnu
```

Бинарник chromium уже был в `~/.cache/ms-playwright/chromium_headless_shell-1248`; пакет `playwright` доустановлен в `.venv` (1.64.0 — совпадает с ревизией браузера).

## Вердикты прогонов

Прогон 1 (после правок, 6/6):

```
tests/test_ui_playwright.py::test_student_landing_login_modal_centered PASSED [ 16%]
tests/test_ui_playwright.py::test_student_register_redirects_to_cabinet PASSED [ 33%]
tests/test_ui_playwright.py::test_instructors_landing_brand_and_cta PASSED [ 50%]
tests/test_ui_playwright.py::test_instructor_apply_valid_form_goes_pending PASSED [ 66%]
tests/test_ui_playwright.py::test_instructor_login_approved_dashboard_layout PASSED [ 83%]
tests/test_ui_playwright.py::test_admin_moderation_approve_reflects_status PASSED [100%]

============================== 6 passed in 11.78s ==============================
```

Прогон 2 (повтор, стабильность, 6/6, tail дословно):

```
tests/test_ui_playwright.py::test_instructor_apply_valid_form_goes_pending PASSED [ 66%]
tests/test_ui_playwright.py::test_instructor_login_approved_dashboard_layout PASSED [ 83%]
tests/test_ui_playwright.py::test_admin_moderation_approve_reflects_status PASSED [100%]

============================== 6 passed in 11.11s ==============================
```

## Вердикт

6 тестов, 2 зелёных прогона подряд. Требование Заказчика «должно быть все покрыто ими» закрыто на уровне 6 ключевых e2e-сценариев (ученик: лендинг+вход, регистрация→кабинет; инструктор: лендинг, анкета→ожидание, вход approved→дашборд с проверкой вёрстки; админ: модерация approve). Изменён только `tests/test_ui_playwright.py` (git status: `M tests/test_ui_playwright.py`, прочие записи в статусе — ранее существовавшие untracked-файлы).

## Итерация 2 (по review-001)

Вердикт ревью — RETURN (F-1 MAJOR + F-3/F-4 MINOR). Правки только в `tests/test_ui_playwright.py`; прод-код, backend, frontend не тронуты.

### Исправления

- **F-1 (MAJOR)** — TC-UI-005: вакуумный `assert "</aside>" in page.content()` удалён. Заменён на структурные проверки, способные упасть: `page.locator(".app > aside").count() == 1` и `.app > main == 1` (aside и main — прямые дети-соседи `.app`); grid-проверка (2 колонки, computed style) сохранена; bounding-box-проверка ужесточена до буквальной `aside.x + aside.width <= main.x + 1`.
- **F-3 (MINOR)** — stderr uvicorn больше не девертится: пишется в temp-файл (`<tmpdir>/uvicorn-stderr.log`); при неуспешном старте (процесс умер или health-check не прошёл за дедлайн) в текст `RuntimeError` попадает хвост лога (последние 20 строк, `_stderr_tail`).
- **F-4 (MINOR)** — покрытие «центрирование иконки загрузки» возвращено отдельным тестом `test_instructor_apply_upload_icon_centered` (TC-UI-004b в матрице; трассировка в docstring: TC-UI-004 + указание на старый TC-UI-002): `abs(frame_cy - icon_cy) <= 6` на `/instructors/apply`.
- **F-2 (MINOR)** — TOCTOU порта: при неудачном старте — одна повторная попытка с новым эфемерным портом (`PORT_START_ATTEMPTS = 2`); ограничение задокументировано в docstring фикстуры.
- **F-5 (NIT)** — `mkdtemp`/`Popen` перенесены внутрь `try/finally`: при падении `Popen` tmpdir удаляется.
- **F-6 (NIT)** — `PYTHONPATH` дописывается к унаследованному (`str(ROOT) + os.pathsep + ...`), а не затирает.
- **F-8 (NIT)** — явный `headless=True` в `p.chromium.launch()`.
- F-7 (NIT, API-тест в UI-файле) — не менялся: docstring честно помечает сценарий как API-проверку; перенос в api-набор — решение ПМ, вне этой задачи.

### Находка итерации 2: frontend-баг центрирования иконки (вне скоупа, требует решения ПМ)

Восстановленная проверка F-4 **не вакуумная — она падает**: на текущем `/instructors/apply` иконка прижата к верху upload-фрейма, отклонение **28.5px > 6px**. Причина (проверено probe'ом на chromium): правило `.upload span { margin-top:4px }` (специфичность 0,1,1) перебивает центрирующий `margin:auto 0` у `.upload-icon` (0,1,0); auto-отступ снизу впитывает всё свободное место и прижимает иконку к верху. Воспроизводится с первого коммита анкеты (`12446b8`, «фикс центрирования» `14d19ac` де-факто не работал) и в дизайн-мокапе `design/mocks/registration-instructor.html` — то есть это не регрессия итерации 2, а давно существующий дефект: старая проверка жила за skipif `UI_TESTS` и ни разу не запускалась с браузером. Прод-код в этой задаче не трогался; тест помечен `xfail(strict=False)` с точной причиной в reason — после правки frontend станет зелёным без изменений теста.

### Хвосты прогонов (7 тестов, `LD_LIBRARY_PATH=~/.cache/pw-libs/...` задан)

Прогон 1:

```
tests/test_ui_playwright.py::test_student_landing_login_modal_centered PASSED [ 14%]
tests/test_ui_playwright.py::test_student_register_redirects_to_cabinet PASSED [ 28%]
tests/test_ui_playwright.py::test_instructors_landing_brand_and_cta PASSED [ 42%]
tests/test_ui_playwright.py::test_instructor_apply_valid_form_goes_pending PASSED [ 57%]
tests/test_ui_playwright.py::test_instructor_apply_upload_icon_centered XFAIL [ 71%]
tests/test_ui_playwright.py::test_instructor_login_approved_dashboard_layout PASSED [ 85%]
tests/test_ui_playwright.py::test_admin_moderation_approve_reflects_status PASSED [100%]

======================== 6 passed, 1 xfailed in 14.67s =========================
```

Прогон 2 (повтор, стабильность):

```
tests/test_ui_playwright.py::test_student_landing_login_modal_centered PASSED [ 14%]
tests/test_ui_playwright.py::test_student_register_redirects_to_cabinet PASSED [ 28%]
tests/test_ui_playwright.py::test_instructors_landing_brand_and_cta PASSED [ 42%]
tests/test_ui_playwright.py::test_instructor_apply_valid_form_goes_pending PASSED [ 57%]
tests/test_ui_playwright.py::test_instructor_apply_upload_icon_centered XFAIL [ 71%]
tests/test_ui_playwright.py::test_instructor_login_approved_dashboard_layout PASSED [ 85%]
tests/test_ui_playwright.py::test_admin_moderation_approve_reflects_status PASSED [100%]

======================== 6 passed, 1 xfailed in 11.85s =========================
```

## Итерация 3 (root-cause фикс)

Снят xfail с `test_instructor_apply_upload_icon_centered` — тест проходит ЗЕЛЁНЫМ без расширения допуска (остался `<= 6px`). Правки: `frontend/instructor-apply.html` (CSS) + `tests/test_ui_playwright.py` (только снят маркер).

### Что исправлено в CSS и почему

Диагноз из итерации 2 (`.upload span{margin-top:4px}` перебивает `margin:auto 0` у `.upload-icon`) был верен лишь частично — probe на живой странице после исключения иконки из-под правила `.upload span` показал отклонение **30.5px > 6px**. Реальная первопричина — двойной проигрыш каскада по специфичности:

1. **Главная причина**: `.upload` — это `label` внутри `.field`, поэтому правило `.field label{display:block;...}` (специфичность **0,1,1**) перебивало `display:flex` у `.upload` (**0,1,0**). Upload-фрейм фактически рендерился block-контейнером, а не flex: `align-items:center` и `margin:auto 0` иконки не работали вовсе, иконка лежала в block-flow у верха фрейма.
2. **Сопутствующая**: `.upload span{...;margin-top:4px}` (0,1,1) соответствовала и самому `<span class="upload-icon">`, перебивая его `margin-top:auto` (0,1,0). Правило задумано для текстовой подписи, а не для иконки.

Точечные фиксы (минимальный дифф, разметка и стилистика не менялись, подпись осталась под иконкой):

- селектор контейнера поднят до `label.upload{...}` (0,1,1, идёт позже в таблице → перебивает `.field label`, flex-центрирование включилось);
- селектор подписи сужен до `.upload span:not(.upload-icon){...}` — иконка исключена из-под правила, `margin:auto 0` восстановлен.

### Хвосты прогонов (2 раза подряд, дословно)

Команда: `export LD_LIBRARY_PATH=~/.cache/pw-libs/root/usr/lib/x86_64-linux-gnu && .venv/bin/python -m pytest tests/test_ui_playwright.py -v`

Прогон 1:

```
tests/test_ui_playwright.py::test_student_landing_login_modal_centered PASSED [ 14%]
tests/test_ui_playwright.py::test_student_register_redirects_to_cabinet PASSED [ 28%]
tests/test_ui_playwright.py::test_instructors_landing_brand_and_cta PASSED [ 42%]
tests/test_ui_playwright.py::test_instructor_apply_valid_form_goes_pending PASSED [ 57%]
tests/test_ui_playwright.py::test_instructor_apply_upload_icon_centered PASSED [ 71%]
tests/test_ui_playwright.py::test_instructor_login_approved_dashboard_layout PASSED [ 85%]
tests/test_ui_playwright.py::test_admin_moderation_approve_reflects_status PASSED [100%]

============================== 7 passed in 12.56s ==============================
```

Прогон 2 (повтор, стабильность):

```
tests/test_ui_playwright.py::test_student_landing_login_modal_centered PASSED [ 14%]
tests/test_ui_playwright.py::test_student_register_redirects_to_cabinet PASSED [ 28%]
tests/test_ui_playwright.py::test_instructors_landing_brand_and_cta PASSED [ 42%]
tests/test_ui_playwright.py::test_instructor_apply_valid_form_goes_pending PASSED [ 57%]
tests/test_ui_playwright.py::test_instructor_apply_upload_icon_centered PASSED [ 71%]
tests/test_ui_playwright.py::test_instructor_login_approved_dashboard_layout PASSED [ 85%]
tests/test_ui_playwright.py::test_admin_moderation_approve_reflects_status PASSED [100%]

============================== 7 passed in 11.99s ==============================
```

7 тестов, 2 зелёных прогона подряд, без xfail/XFAIL.
