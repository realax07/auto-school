# TC-APP-010 — Негатив: телефон менее 10 цифр → 422

- ID кейса: TC-APP-010
- ID чеклиста: CHK-10
- Источник: CHK-10 → Requirement «Сохранение заявки со статусом waiting» (домен instructor-application) → FR-11; Scenario «Отклонение некорректно заполненной анкеты»
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_instructors_apply.py::test_apply_validation_contract_422 (вариант {"phone": "+7 123 456"} → «Телефон: укажите не менее 10 цифр», COUNT=0). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN анкета заполнена базовым валидным набором
- WHEN в поле телефона подставляется значение с менее чем 10 цифрами и анкета отправляется
- THEN 422, заявка НЕ создана

## Предусловия
- Сервис собран через create_app() с роутером instructors; TestClient без сети; чистая БД в tmp, init_db.

## Шаги
1. POST /api/instructors/apply с phone «+7 123 456» (6 цифр).
2. Зафиксировать статус и тело.
3. SELECT COUNT(*) FROM instructor_applications.

## Ожидаемый результат
1–2. 422 {"ok": false, "error": "Телефон: укажите не менее 10 цифр"}.
3. COUNT = 0.

## Тестовые данные
Базовый валидный набор (TC-APP-005); phone «+7 123 456».

## Трассировка

### Requirement: Сохранение заявки со статусом waiting
#### Scenario: Отклонение некорректно заполненной анкеты

