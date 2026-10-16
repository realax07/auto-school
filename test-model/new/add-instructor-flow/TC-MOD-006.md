# TC-MOD-006 — Deny waiting-заявки с комментарием: статус deny, комментарий сохранен

- ID кейса: TC-MOD-006
- ID чеклиста: CHK-27
- Источник: CHK-27 → Requirement «Отклонение заявки с обязательным комментарием» (домен admin-moderation) → FR-15; Scenario «Отклонение с комментарием»; sdd §15.4
- Тип: позитивный
- Приоритет: Must
- Статус: automated — tests/test_instructor_admin.py::test_deny_with_comment_saves_reason (статус deny, review_comment = C). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN существует заявка в статусе waiting; администратор с валидным админ-токеном
- WHEN POST deny с телом {"comment": C}
- THEN 200 {"ok": true}; статус заявки становится deny, комментарий C сохраняется в заявке (review_comment = C)

## Предусловия
- Сервис собран через create_app() с роутерами; TestClient без сети; чистая БД в tmp, init_db; существует waiting-заявка id A.

## Шаги
1. Создать заявку публичным apply → id A.
2. POST /api/admin/instructor-applications/{A}/deny с телом {"comment": "Не подтверждена квалификация"} и админ-токеном.
3. Прочитать запись заявки A.

## Ожидаемый результат
2. 200 {"ok": true}.
3. status = 'deny'; review_comment = «Не подтверждена квалификация».

## Тестовые данные
Заявка — базовый валидный набор (TC-APP-005). Комментарий C: «Не подтверждена квалификация». Админ: admin / admin-pass-2026.

## Трассировка

### Requirement: Отклонение заявки с обязательным комментарием
#### Scenario: Отклонение с комментарием

