# TC-S9BE-001 — apply выдает ОБА токена, сохраняет в заявку, ветки IntegrityError разведены (FR-80, NFR-27, NFR-28, MIN-2)

- Автотест: `tests/test_s9_backend.py::TestTCS9BE001ApplyIssuesTokens::test_apply_200_contains_both_tokens_and_saves_them`; `…::test_tokens_of_two_applications_differ`; `…::test_apply_422_issues_no_tokens_and_creates_nothing`; `…::test_email_race_contract_422_single_application_no_regen_loop`; `…::test_token_collision_regenerated_application_created_no_422`; `…::test_integrity_branches_classified_by_real_sqlite_messages` (6 тестов класса)
- Приоритет: Must
- Статус: автоматизирован (rule 6 — TC-ID в docstring класса TestTCS9BE001ApplyIssuesTokens); кейс партии change add-application-status-polling (Спринт 9)
- Трассировка:
  - Requirement: Автоопределение статуса заявки на экране ожидания
  - Scenario: Экран опрашивает статус по неперебираемому идентификатору

## GIVEN / WHEN / THEN
- GIVEN валидная анкета (контракт apply, sdd §15.1); для ветки коллизии — в БД заявка с занятым poll_token, secrets.token_urlsafe подменен monkeypatch-ом (первый вызов возвращает чужой токен); для ветки классификации — сырые INSERT-строки и РЕАЛЬНЫЕ сообщения IntegrityError SQLite
- WHEN POST /api/instructors/apply — успешный сабмит, второй сабмит с тем же email, сабмит с пустым обязательным полем, сабмит с заведомой коллизией poll_token; прямые INSERT с дублем email / дублем poll_token / дублем exchange_token и разбор сообщений через instructors._integrity_kind
- THEN apply 200 несет poll_token И exchange_token: оба 43 символа base64url ([A-Za-z0-9_-]{43} — 256 бит, неперебираемость NFR-28), poll ≠ exchange, оба сохранены в строке заявки той же транзакцией, заявка waiting, review_comment = '' (обратно-совместимость NFR-27); токены двух заявок и внутри пары — попарно различны; 422 — в теле НЕТ ключей poll_token/exchange_token и строки в БД нет; гонка дубля email → контрактная 422 «Email: уже зарегистрирован», заявка в БД ровно одна, цикла регенерации нет; коллизия poll_token → регенерация и повторная вставка БЕЗ 422 (apply 200, сохраненный токен ≠ коллизионный); классификатор веток: email → 'email', poll/exchange → 'token' (ветки разведены MIN-2)

## Примечание
- Партия change add-application-status-polling (Спринт 9, блок 2 — FR-80…FR-83 + NFR-28); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6).
- Фактический статус: backend реализован (задача 2.1 смержена в ветке);
  backend-матрица tests/test_s9_backend.py — 13 passed (лог ПМ). Полный
  регресс — в работе, светофор не присваивался.
