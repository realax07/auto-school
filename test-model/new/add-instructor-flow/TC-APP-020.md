# TC-APP-020 — Негатив: открытый пароль отсутствует в записи заявки и в логах

- ID кейса: TC-APP-020
- ID чеклиста: CHK-20
- Источник: CHK-20 → Requirement «Хранение пароля заявки только в виде bcrypt-хэша» (домен instructor-application) → FR-11.1; Scenario «В заявке хранится только хэш»
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_instructors_apply.py::test_apply_no_password_in_logs_or_response (пароль отсутствует в JSON-ответе и в захваченных логах, caplog) + ::test_apply_success_creates_waiting_application_with_hash (в записи нет ключей password/password_confirm, значение P отсутствует среди значений записи). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN анкета отправлена с паролем P
- WHEN инспектируются запись заявки и журналы сервиса (логи apply)
- THEN строка P отсутствует и в записи заявки (только bcrypt-хэш), и в логах; ключей password/password_confirm в записи нет

## Предусловия
- Сервис собран через create_app() с роутером instructors; TestClient без сети; чистая БД в tmp, init_db; перехват логов уровня INFO+ (caplog).

## Шаги
1. POST /api/instructors/apply с базовым набором (P = «Qwerty123») → 200.
2. Прочитать всю запись заявки (SELECT *) по email; проверить все значения и ключи.
3. Пройти по захваченным записям логов (сообщения apply): найти вхождение P.
4. Проверить JSON-ответ на вхождение P.

## Ожидаемый результат
2. В значениях записи P отсутствует; ключей «password» и «password_confirm» нет; есть только password_hash (валидный bcrypt).
3–4. Ни одна лог-запись и ни один фрагмент ответа не содержат P.

## Тестовые данные
Базовый валидный набор (TC-APP-005): instructor@example.com / Qwerty123.
