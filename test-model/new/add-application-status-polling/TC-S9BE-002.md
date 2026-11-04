# TC-S9BE-002 — Статус waiting по X-Poll-Token; чтение без побочных эффектов (FR-80, NFR-28)

- Автотест: `tests/test_s9_backend.py::test_tc_s9be_002_status_waiting_read_only_no_side_effects`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-application-status-polling (Спринт 9)
- Трассировка:
  - Requirement: Автоопределение статуса заявки на экране ожидания
  - Scenario: Экран опрашивает статус по неперебираемому идентификатору

## GIVEN / WHEN / THEN
- GIVEN анкета отправлена успешно (apply 200 → poll_token/exchange_token), заявка waiting; полная строка заявки зафиксирована в БД до опроса
- WHEN GET /api/instructors/application-status с заголовком X-Poll-Token — 3 многократных тика опроса подряд
- THEN каждый ответ 200 {ok:true, status:'waiting', reason:null} (reason — только при rejected); строка заявки в БД после N чтений ПОЛНОСТЬЮ равна строке до опроса (статус, created_at, токены, комментарий не изменились); exchange_token чтением НЕ потреблен — запрос только чтения, без записи и побочных эффектов (NFR-28)

## Примечание
- Партия change add-application-status-polling (Спринт 9, блок 2 — FR-80…FR-83 + NFR-28); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6).
- Фактический статус: backend реализован (задача 2.1 смержена в ветке);
  backend-матрица tests/test_s9_backend.py — 13 passed (лог ПМ). Полный
  регресс — в работе, светофор не присваивался.
