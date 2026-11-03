# TC-S9BE-007 — Потребление exchange_token: повторный обмен 404, обмен при waiting 409, параллельные обмены — ровно один 200 (FR-81, MAJ-1, MIN-1)

- Автотест: `tests/test_s9_backend.py::test_tc_s9be_007_consumed_exchange_repeat_404_and_waiting_409`; `tests/test_s9_backend.py::test_tc_s9be_007_parallel_exchanges_exactly_one_200`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring обоих тестов); кейс партии change add-application-status-polling (Спринт 9)
- Трассировка:
  - Requirement: Автоопределение статуса заявки на экране ожидания
  - Scenario: Обмен вернул 404 (токен потреблен или чужой) — терминальное состояние с подсказкой входа
  - Scenario: Ошибка обмена оставляет экран в waiting
  - Scenario: waiting → approved: бесшовный переход в кабинет без ввода пароля

## GIVEN / WHEN / THEN
- GIVEN (потребление) заявка approved с exchange_token; (waiting-ветка) вторая заявка waiting с токенами; (MIN-1) заявка approved, ОДИН валидный exchange_token и два воркера на отдельных TestClient, синхронизированных threading.Barrier (без time.sleep — спека qa-pipeline)
- WHEN первый обмен 200 и ПОВТОРНЫЙ обмен тем же токеном; опрос статуса; обмен токеном waiting-заявки; ДВА ПАРАЛЛЕЛЬНЫХ POST /api/instructors/application-exchange одним валидным токеном
- THEN после первого обмена exchange_token в БД = NULL; повторный обмен → 404 {ok:false} — триггер терминального состояния экрана (MAJ-1); статус при этом остается 'approved' (терминальный, после выдачи сессии не меняется); обмен при waiting → 409 {ok:false}, токен СОХРАНЕН — повтор возможен на следующем тике; параллельные обмены (условный UPDATE … WHERE exchange_token = ? + rowcount, SQLite сериализует запись): ровно один 200 {ok:true, route:'cabinet'}, второй 404-неразличение; сессия выдана ровно ОДНА — /me с выданным токеном 200, email совпадает, users.role == 'instructor'; exchange_token в БД потреблен ровно один раз (NULL)

## Примечание
- Партия change add-application-status-polling (Спринт 9, блок 2 — FR-80…FR-83 + NFR-28); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6).
- Фактический статус: backend реализован (задача 2.1 смержена в ветке);
  backend-матрица tests/test_s9_backend.py — 13 passed (лог ПМ). Полный
  регресс — в работе, светофор не присваивался.
