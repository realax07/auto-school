# TC-MOD-010 — Негатив: повторный approve → 409, пользователь не дублируется

- ID кейса: TC-MOD-010
- ID чеклиста: CHK-31
- Источник: CHK-31 → Requirement «Одобрение заявки создает пользователя» (домен admin-moderation) → FR-16; Scenario «Одобренная заявка не одобряется повторно»
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_instructor_admin.py::test_approve_creates_user_with_instructor_role_and_same_hash (повторный approve → 409 «Заявка уже одобрена», в users одна запись). UI-часть («кнопка скрыта») — manual/toBeAutomated. Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN заявка в статусе approved (кнопка «Одобрить» в UI скрыта)
- WHEN прямой повторный POST approve с валидным админ-токеном
- THEN 409 «Заявка уже одобрена»; повторного создания пользователя НЕ происходит (в users одна запись email E)

## Предусловия
- Сервис собран через create_app() с роутерами; TestClient без сети; чистая БД в tmp, init_db; существует approved-заявка.

## Шаги
1. Создать заявку → id A; approve {A} → 200 (user_id U1).
2. Повторный POST approve {A} → зафиксировать.
3. SELECT COUNT(*) FROM users WHERE email = E; сверить user_id записи.

## Ожидаемый результат
2. 409 {"ok": false, "error": "Заявка уже одобрена"}.
3. COUNT = 1; единственная запись имеет user_id U1 (дублей нет).
(Браузерная часть: для approved-заявки кнопка «Одобрить» в UI отсутствует.)

## Тестовые данные
Заявка — базовый валидный набор (TC-APP-005): instructor@example.com. Админ: admin / admin-pass-2026.

## Трассировка

### Requirement: Одобрение заявки создает пользователя
#### Scenario: Одобренная заявка не одобряется повторно

