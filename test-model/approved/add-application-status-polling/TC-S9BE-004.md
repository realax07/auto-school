# TC-S9BE-004 — waiting → rejected: причина отказа без входа; историческая пустая причина → нейтральный текст (FR-82)

- Автотест: `tests/test_s9_backend.py::test_tc_s9be_004_rejected_with_reason_and_without`
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-application-status-polling (Спринт 9)
- Трассировка:
  - Requirement: Автоопределение статуса заявки на экране ожидания
  - Scenario: waiting → rejected: причина отказа без входа

## GIVEN / WHEN / THEN
- GIVEN заявка waiting с poll_token; админ отклонил её штатным deny с обязательным непустым комментарием «нечитаемое фото ВУ» (контур Спринта 2); вторая (историческая) заявка: deny, затем прямой UPDATE status='deny', review_comment='' — симуляция исторической строки с пустым комментарием
- WHEN GET /api/instructors/application-status по X-Poll-Token каждой из заявок
- THEN первая: 200, status:'rejected' (внутренний 'deny' маппится), reason == 'нечитаемое фото ВУ' — причина видна без входа и перелогина; вторая (историческая): 200, status:'rejected', reason == '' (пустой/исторический комментарий → нейтральный текст отказа на экране)

## Примечание
- Партия change add-application-status-polling (Спринт 9, блок 2 — FR-80…FR-83 + NFR-28); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6).
- Фактический статус: backend реализован (задача 2.1 смержена в ветке);
  backend-матрица tests/test_s9_backend.py — 13 passed (лог ПМ). Полный
  регресс — в работе, светофор не присваивался.
