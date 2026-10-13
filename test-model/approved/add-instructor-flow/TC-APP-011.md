# TC-APP-011 — Негатив: пароль короче 8 символов → 422

- ID кейса: TC-APP-011
- ID чеклиста: CHK-11
- Источник: CHK-11 → Requirement «Сохранение заявки со статусом waiting» (домен instructor-application) → FR-11; Scenario «Отклонение некорректно заполненной анкеты»
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_instructors_apply.py::test_apply_validation_contract_422 (вариант {"password": "short", "password_confirm": "short"} → «Пароль: не менее 8 символов», COUNT=0). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN анкета заполнена базовым валидным набором
- WHEN в пароль и подтверждение подставляется строка короче 8 символов и анкета отправляется
- THEN 422, заявка НЕ создана

## Предусловия
- Сервис собран через create_app() с роутером instructors; TestClient без сети; чистая БД в tmp, init_db.

## Шаги
1. POST /api/instructors/apply с password=password_confirm=«short» (5 символов).
2. Зафиксировать статус и тело.
3. SELECT COUNT(*) FROM instructor_applications.

## Ожидаемый результат
1–2. 422 {"ok": false, "error": "Пароль: не менее 8 символов"}.
3. COUNT = 0.

## Тестовые данные
Базовый валидный набор (TC-APP-005); password/password_confirm «short».
