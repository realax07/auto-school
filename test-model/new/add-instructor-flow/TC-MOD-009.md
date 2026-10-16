# TC-MOD-009 — Approve waiting-заявки: одна транзакция, users + approved

- ID кейса: TC-MOD-009
- ID чеклиста: CHK-30
- Источник: CHK-30 → Requirement «Одобрение заявки создает пользователя» (домен admin-moderation) → FR-16; Scenario «Одобрение заявки waiting»; sdd §15.3 (одна транзакция, commit один)
- Тип: позитивный
- Приоритет: Must
- Статус: automated — tests/test_instructor_admin.py::test_approve_creates_user_with_instructor_role_and_same_hash (users создан с данными заявки и хэшем из заявки, role='instructor', статус approved, user_id) + ::test_approve_transaction_rollback_keeps_consistency (падение между INSERT и UPDATE — откат целиком, waiting без пользователя, MIN-3). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN существует заявка в статусе waiting с email E и bcrypt-хэшем H
- WHEN POST approve с валидным админ-токеном
- THEN ОДНА транзакция (commit один): в users создается запись (ФИО/телефон/email из заявки, password_hash = H из заявки, role='instructor'), статус заявки → approved; падение между INSERT и UPDATE не оставляет waiting-заявку с пользователем (откат целиком)

## Предусловия
- Сервис собран через create_app() с роутерами; TestClient без сети; чистая БД в tmp, init_db; существует waiting-заявка id A.

## Шаги
1. Создать заявку публичным apply → id A; снять снапшот записи A (включая password_hash).
2. POST approve {A} с админ-токеном → зафиксировать.
3. Прочитать users по email заявки; сверить поля с заявкой.
4. Прочитать статус заявки A.
5. Транзакционная часть: создать заявку на dup@example.com; ПОСЛЕ создания вставить в users чужую запись с тем же email (прямой INSERT); повторить approve {dup} → зафиксировать; проверить состояние.

## Ожидаемый результат
2. 200 {"ok": true, "user_id": <int>}.
3. users: surname/name/patronymic/email/phone как в заявке; password_hash == снапшотный H (без повторного хэширования); role = 'instructor'.
4. status = 'approved'.
5. Ответ 409 «Email: уже зарегистрирован»; заявка dup осталась waiting, чужая запись users цела, в users РОВНО одна запись этого email (откат — consistency MIN-3).

## Тестовые данные
Заявка — базовый валидный набор (TC-APP-005): instructor@example.com; транзакционный прогон — dup@example.com. Админ: admin / admin-pass-2026.

## Трассировка

### Requirement: Одобрение заявки создает пользователя
#### Scenario: Одобрение заявки waiting

