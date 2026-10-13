# TC-APP-016 — Негатив: email существует в users → 422 «Email: уже зарегистрирован»

- ID кейса: TC-APP-016
- ID чеклиста: CHK-16
- Источник: CHK-16 → Requirement «Сохранение заявки со статусом waiting» (домен instructor-application) → FR-16; Scenario «Отклонение анкеты с email существующего пользователя»
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_instructors_apply.py::test_apply_email_taken_in_users (ученик в users → 422 «Email: уже зарегистрирован», заявки нет). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN в users существует запись с email E (ученик или одобренный инструктор)
- WHEN отправляется анкета с email E и корректными остальными данными
- THEN 422 с ЕДИНЫМ сообщением «Email: уже зарегистрирован», заявка НЕ создана, экран ожидания не показывается

## Предусловия
- Сервис собран через create_app() с роутером instructors; TestClient без сети; чистая БД в tmp, init_db.
- Прогон А: ученик создан через POST /api/register (petrova@example.com). Прогон Б: пользователь-инструктор создан прямым INSERT в users (email taken@example.com).

## Шаги
1. (А) POST /api/register с базовым пользователем petrova@example.com → 200.
2. POST /api/instructors/apply с email petrova@example.com → зафиксировать статус/тело.
3. SELECT COUNT(*) FROM instructor_applications WHERE email = 'petrova@example.com'.
4. (Б) Повторить шаги 2–3 для taken@example.com, созданного прямым INSERT в users.

## Ожидаемый результат
2, 4. Оба ответа 422 {"ok": false, "error": "Email: уже зарегистрирован"} — единое сообщение независимо от роли существующего пользователя.
3–4. COUNT = 0 в обоих случаях.

## Тестовые данные
Анкета — базовый валидный набор (TC-APP-005) с подменой email. Пользователи: petrova@example.com / Qwerty123 (регистрация 7 полей, TC-AUTH-001); taken@example.com (прямой INSERT, password_hash 'x'*60).
