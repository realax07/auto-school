# TC-APP-017 — Негатив: email существует в заявках (любой статус) → 422

- ID кейса: TC-APP-017
- ID чеклиста: CHK-17
- Источник: CHK-17 → Requirement «Сохранение заявки со статусом waiting» (домен instructor-application) → FR-16; Scenario «Отклонение анкеты с email существующей заявки»
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_instructors_apply.py::test_apply_email_taken_in_applications (дубликат заявки waiting → 422 единое сообщение); статусы approved/deny — manual/toBeAutomated (прямой UPDATE статуса + повторный apply по паттерну test_auth_route.py::_set_status). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN в instructor_applications существует заявка с email E (прогоны: статус waiting, approved, deny)
- WHEN отправляется вторая анкета с email E и корректными остальными данными
- THEN 422 «Email: уже зарегистрирован», заявка НЕ создана (независимо от статуса существующей)

## Предусловия
- Сервис собран через create_app() с роутером instructors; TestClient без сети; чистая БД в tmp, init_db.

## Шаги
1. (waiting) POST /api/instructors/apply с email instructor@example.com → 200. Повторный POST с тем же email → зафиксировать статус/тело.
2. (deny) Создать заявку на dup@example.com, прямым UPDATE установить status='deny', review_comment C. Повторный POST → зафиксировать.
3. (approved) Создать заявку на app@example.com, прямым UPDATE установить status='approved'. Повторный POST → зафиксировать.
4. После каждого прогона SELECT COUNT(*) FROM instructor_applications по соответствующему email.

## Ожидаемый результат
1–3. Все повторные ответы 422 {"ok": false, "error": "Email: уже зарегистрирован"}.
4. COUNT = 1 для каждого email — вторая заявка не создана ни при одном статусе.

## Тестовые данные
Базовый валидный набор (TC-APP-005); email: instructor@example.com (waiting), dup@example.com (deny, комментарий «Не подтверждена квалификация»), app@example.com (approved).

## Трассировка

### Requirement: Сохранение заявки со статусом waiting
#### Scenario: Отклонение анкеты с email существующей заявки

