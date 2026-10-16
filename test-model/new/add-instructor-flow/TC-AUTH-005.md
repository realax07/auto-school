# TC-AUTH-005 — Негатив: deny-заявка → route=rejected с причиной, БЕЗ сессии

- ID кейса: TC-AUTH-005
- ID чеклиста: CHK-39
- Источник: CHK-39 → Requirement «Роутинг после входа по статусу» (домен instructor-auth) → FR-13; Scenario «Заявка deny — экран отказа с причиной»; sdd §15.5
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_auth_route.py::test_login_denied_application_rejected_with_reason (плановый ID TC-FR13-003): 200 {ok, route:'rejected', reason}, ключа token нет. До утверждения кейсов (rule 6)

## GIVEN / WHEN / THEN
- GIVEN существует заявка в статусе deny с комментарием C (review_comment); пароль из анкеты верный
- WHEN POST /api/auth/login {"email": E, "password": P}
- THEN 200 {"ok": true, "route": "rejected", "reason": C}; сессия НЕ выдается; фронт ведет на /instructors/rejected, на экране видна точная причина C

## Предусловия
- Сервис собран через create_app(); TestClient без сети; чистая БД в tmp, init_db; состояние анти-брутфорса чистое.

## Шаги
1. POST /api/instructors/apply (instr@example.com / Instr1234) → 200.
2. Перевести заявку в deny: комментарий «Опыт работы не подтвержден» (прямой UPDATE — детерминизм, либо deny через админ-API).
3. POST /api/auth/login {"email": "instr@example.com", "password": "Instr1234"}.
4. Зафиксировать статус/тело; проверить отсутствие token.
5. (браузерная часть, manual) Проверить: фронт на /instructors/rejected, показан текст «Опыт работы не подтвержден».

## Ожидаемый результат
3. 200 {"ok": true, "route": "rejected", "reason": "Опыт работы не подтвержден"}; ключа token НЕТ.
5. Экран отказа открыт, причина показана дословно.

## Тестовые данные
Анкета: instr@example.com / Instr1234. Комментарий C: «Опыт работы не подтвержден».

## Трассировка

### Requirement: Роутинг после входа по статусу
#### Scenario: Заявка deny — экран отказа с причиной

