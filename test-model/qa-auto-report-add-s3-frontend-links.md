# QA-automation отчет — change add-s3-frontend-links (Спринт 4, Партия A, финальный прогон)

- Роль: qa_automation (agents/qa_automation_agent.md)
- Дата прогона: 2026-10-16 (UTC)
- Вход: кейсы Партии A — TC-UI-015…018 (live e2e) + TC-S3BE-040/041 (backend-статика); кейсы живут трассировкой в docstring тестов (перенос test-model не требуется по постановке).
- Автотесты: tests/test_ui_playwright.py (23; из них 5 — TC-UI этого change: 4 целевых + test_s4_pages_tag_balance), tests/test_s3_backend.py (43; из них 2 целевых TC-S3BE-040/041).
- Коммитов нет (по заданию).

## 1. Полный сьют

Команда (дословно):

```
export LD_LIBRARY_PATH=~/.cache/pw-libs/root/usr/lib/x86_64-linux-gnu && .venv/bin/python -m pytest tests/ -q
```

Tail (дословно):

```
........................................................................ [ 26%]
........................................................................ [ 53%]
........................................................................ [ 80%]
......................................................                   [100%]
=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
270 passed, 1 warning in 241.47s (0:04:01)
```

## 2. Вердикты прогонов (backend-сьюит / e2e-сьюит)

Backend-сьюит — `tests/test_s3_backend.py -q`, tail (дословно):

```
...........................................                              [100%]
=============================== warnings summary ===============================
tests/test_s3_backend.py::test_migration_creates_new_tables
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
43 passed, 1 warning in 78.83s (0:01:18)
```

Повторный прогон backend-сьюта после докстринг-правки (раздел 4): `43 passed, 1 warning in 79.12s (0:01:19)` — green, финальное состояние файла верифицировано.

E2E-сьюит — `tests/test_ui_playwright.py -q` (с тем же LD_LIBRARY_PATH), tail (дословно):

```
.......................                                                  [100%]
23 passed in 36.87s
```

Вердикт: оба сьюта и полный сьют зеленые, падений нет, баг-репорты не требуются. Сборка: 43 + 23 = 66 тестов двух целевых файлов; остальные 204 сьюта — Спринты 0–3 (в прошлый прогон 257, сейчас 270 = +13 новых тестов Спринта 4, Партия A).

## 3. Маппинг кейсов → автотесты

### TC-UI (live e2e, tests/test_ui_playwright.py — плановая трассировка в docstring)

| Кейс | Автотест | Покрытие |
|---|---|---|
| TC-UI-015 | test_ui_playwright.py::test_s4_my_cars_add_edit_delete_car | полный: живой бэкенд, добавление авто → в списке (карточка + GET API), PATCH отражается, удаление с подтверждением (отмена работает), авто исчезает из списка и API |
| TC-UI-016 | test_ui_playwright.py::test_s4_my_cars_photo_upload_progress_and_preview | полный: POST multipart …/photo, прогресс в модалке, превью на карточке, has_photo=true, фото только по сессии владельца (чужая сессия → отказ, Content-Type image/png) |
| TC-UI-017 | test_ui_playwright.py::test_s4_review_submit_then_repeat_blocked_409 | полный: контекст инструктора на /review, сабмит 200 → «отправлен», повтор через UI → 409 → «уже оставлен», прямой POST в API → 409 (NFR-5) |
| TC-UI-018 | test_ui_playwright.py::test_s4_my_requests_badges_deny_comment_retry_and_review_link | полный: желтый «На рассмотрении» → красный «Отказана» с комментарием инструктора → «Повторить заявку» (ОВ-2) снова активна → зеленая «Принята», авто занятий, переход на форму отзыва |

### TC-S3BE (backend, tests/test_s3_backend.py — TC-ID в docstring, правило 6)

| Кейс | Автотест | Покрытие |
|---|---|---|
| TC-S3BE-040 | test_s3_backend.py::test_s4_static_routes_new_pages (parametrize: /my-cars, /review, /my-requests) | полный: 200, text/html, маркер заголовка страницы («Мои автомобили», «Оставить отзыв», «Заявки инструкторам») |
| TC-S3BE-041 | test_s3_backend.py::test_s4_pages_wired_to_real_api_shapes | полный: страницы ссылаются на реальные контракты Спринта 3 — /my-cars → api/instructor/cars (+cars/{id}/photo), /review → instructors/{id}/reviews, /my-requests → api/student/requests + instructor_id:r.instructor_id |

Дополнительно, без отдельного TC (служебный): test_ui_playwright.py::test_s4_pages_tag_balance — баланс тегов трех новых страниц (sanity-тест инъекций верстки).

Сводка: 6/6 кейсов партии покрыты автотестами, 6 полных, 0 частичных, 0 без покрытия.

## 4. Известный долг rule 6 на test_s3_backend — проверка актуальности

Было (отчет qa-auto-report-add-instructor-student-loop.md, раздел 4): docstring файла заявлял «TC-трассировка не ведется», тогда как правило 6 ожидает TC-ID в docstring, — расхождение зафиксировано как долг за ПМ/arch-review.

Проверка сейчас: TC-S3BE-040/041 этого change несут TC-ID в docstring (строки 1633, 1643 файла) — правило 6 для новых тестов соблюдено; исключение перестало быть тотальным. Строкa-исключение в шапке docstring оставалась без изменений и стала неточной → по заданию добавлен flow_check хвостом в docstring tests/test_s3_backend.py (строки 11–18): фиксирует, что test_s4_static_routes_new_pages (TC-S3BE-040) и test_s4_pages_wired_to_real_api_shapes (TC-S3BE-041) трассированы, тесты Спринта 3 (TC-S3BE-001…039) остаются без TC-ID с содержательным маппингом в прошлом отчете, решение о полном закрытии исключения — за ПМ/arch-review.

Актуальность долга: частично снят (для новых тестов правило 6 выполняется), остаток долга — TC-ID для 39 backend-тестов Спринта 3 — не блокирует партию, остается на ПМ/arch-review.

## 5. Перенос партии

Не требуется (по заданию): кейсы Партии A — TC-UI, живут трассировкой в тестах; test-model/approved|new/add-s3-frontend-links не создаются.

## 6. Изменения в репозитории

- tests/test_s3_backend.py — только docstring: добавлен блок flow_check (см. раздел 4); код тестов не менялся.
- Коммитов нет (по заданию).
