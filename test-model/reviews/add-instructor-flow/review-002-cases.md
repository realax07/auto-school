# Review-002 — кейс add-instructor-flow (повторная итерация, партия: TC-NFR-001)

- Ревьюер: qa_case_reviewer
- Дата: 2026-10-12
- Reviewer-Delegation: deleg-qr-20261012-external
- Партия (H3, явный список из задачи ПМ): test-model/new/add-instructor-flow/TC-NFR-001.md — единственный файл партии; остальные кейсы пакета не открывались.
- Вход: review-001-cases.md (строка TC-NFR-001, major-замечание), обновленный кейс TC-NFR-001.md (commit 1f7a43f), tests/test_instructors_apply.py, tests/test_qa_sprint1.py.

## TC-NFR-001 (CHK-50) — проверка закрытия return review-001

Major-замечание review-001: automated-пометка «динамическая проба» не подтверждена — в параметризации test_apply_validation_contract_422 не было email с метасимволами, apply-проба `' OR 1=1 --` не автоматизирована нигде, login-эталон test_qa_sprint1 кейсом не цитировался.

Проверка по существу (файл за файлом, партия из одного кейса):

1. **Apply-проба автоматизирована**: tests/test_instructors_apply.py, строка 170 — параметризация test_apply_validation_contract_422 дополнена вариантом `({"email": "' OR 1=1 --"}, "Email: неверный формат")` (добавлено в commit 1f7a43f, комментарий в коде ссылается на TC-NFR-001 / rev-001-cases). Тест проверяет 422 `{"ok": false, "error": "Email: неверный формат"}` дословно + `COUNT(*) FROM instructor_applications == 0` после пробы — ровно ожидаемый результат 2–4 кейса (литерал, заявка не создана). Контрольный прогон: `pytest tests/test_instructors_apply.py::test_apply_validation_contract_422 -q` → **19 passed** (все варианты параметризации, включая инъекцию-пробу).
2. **Login-проба процитирована**: статус-строка кейса теперь ссылается на test_qa_sprint1.py (эталон Спринта 1); тест test_nfr002_sql_is_parameterized_no_injection действительно содержит динамическую пробу `' OR 1=1 --` и вариант `' OR '1'='1` → единый 401 AUTH_FAIL, token не выдан, записи не затронуты (строки 118–127), что закрывает ожидаемый результат 3–4. Прогон домена `pytest tests/test_instructors_apply.py tests/test_qa_sprint1.py tests/test_auth_route.py -q` → **43 passed**.
3. **Пометка честная**: automated заявлен только для динамических проб (apply + login); статическая инспекция исходников (?-плейсхолдеры, 0 конкатенаций) честно помечена manual/toBeAutomated — расхождений с фактами нет, замечание review-001 устранено по обоим пунктам рекомендации.
4. Остальное по кейсу (GIVEN/WHEN/THEN, шаги, данные, CHK-ID) — без изменений и без замечаний.

| Кейс | CHK | Вердикт | Замечания |
|---|---|---|---|
| TC-NFR-001 | CHK-50 | approve | Без замечаний. Return review-001 закрыт: инъекция-проба `' OR 1=1 --` добавлена в параметризацию test_apply_validation_contract_422 → «Email: неверный формат» + COUNT=0 (строка 170, commit 1f7a43f, 19 passed); login-проба процитирована на test_qa_sprint1.py (строка 118, единый 401, обхода нет); статическая инспекция честно manual/toBeAutomated. Пометка automated теперь подтверждается исходниками и прогоном. |

## Итог review-002

- **Вердикт: approve** (по TC-NFR-001; партия = 1 кейс, замечаний нет).
- TC-NFR-001 перенесен в `test-model/approved/add-instructor-flow/` — пакет полностью одобрен: **52/52 approved** (51 из review-001 + TC-NFR-001).
- Границы соблюдены: записи — только `test-model/reviews/add-instructor-flow/review-002-cases.md` и перенос `test-model/new/add-instructor-flow/TC-NFR-001.md` → `test-model/approved/add-instructor-flow/TC-NFR-001.md`; кейсы не правились.
