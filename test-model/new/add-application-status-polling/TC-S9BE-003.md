# TC-S9BE-003 — waiting → approved: статус и бесшовный обмен токена на сессию; переходный отказ обмена 409 (FR-81)

- Автотест: `tests/test_s9_backend.py::test_tc_s9be_003_approved_status_and_seamless_exchange`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-application-status-polling (Спринт 9)
- Трассировка:
  - Requirement: Автоопределение статуса заявки на экране ожидания
  - Scenario: waiting → approved: бесшовный переход в кабинет без ввода пароля
  - Scenario: Ошибка обмена оставляет экран в waiting

## GIVEN / WHEN / THEN
- GIVEN заявка waiting с токенами из apply; админ одобряет её штатной модерацией (approve → INSERT users role='instructor' + статус approved одной транзакцией); для отказной ветки — вторая заявка, статус принудительно approved БЕЗ создания строки users (вырожденное «approved без users»)
- WHEN GET статуса по X-Poll-Token; POST /api/instructors/application-exchange с exchange_token; контроль сессии через GET /api/auth/me с выданным token; обмен токеном вырожденной заявки
- THEN статус в опросе — 'approved', reason = null; обмен 200 в форме ответа логина {ok:true, token, route:'cabinet'}; сессия рабочая и привязана к строке users инструктора: /me 200 с email заявителя, в БД users.role == 'instructor' (роль верифицируется по строке users — контракт /api/auth/me БЕЗ ключа role не меняется, sdd.md §20.1, пометка [test-adapted] в тесте); переходный отказ «approved без users» → 409 {ok:false}, exchange_token в заявке СОХРАНЕН (токен не потреблен) — экран остается в waiting, повторный обмен возможен на следующем тике

## Примечание
- Партия change add-application-status-polling (Спринт 9, блок 2 — FR-80…FR-83 + NFR-28); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6).
- Фактический статус: backend реализован (задача 2.1 смержена в ветке);
  backend-матрица tests/test_s9_backend.py — 13 passed (лог ПМ). Полный
  регресс — в работе, светофор не присваивался.
