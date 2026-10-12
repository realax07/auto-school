# TC-APP-014 — Негатив: невалидная дата выдачи ВУ → 422

- ID кейса: TC-APP-014
- ID чеклиста: CHK-14
- Источник: CHK-14 → Requirement «Сохранение заявки со статусом waiting» (домен instructor-application) → FR-11; Scenario «Отклонение некорректно заполненной анкеты»
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_instructors_apply.py::test_apply_validation_contract_422 (варианты license_date «01.05.2020» и «not-a-date» → «Дата выдачи ВУ: неверный формат», COUNT=0). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN анкета заполнена базовым валидным набором
- WHEN в дату выдачи ВУ подставляется невалидное значение (не YYYY-MM-DD) и анкета отправляется
- THEN 422, заявка НЕ создана

## Предусловия
- Сервис собран через create_app() с роутером instructors; TestClient без сети; чистая БД в tmp, init_db.

## Шаги
1. POST /api/instructors/apply с license_date «01.05.2020» (не тот формат).
2. POST /api/instructors/apply с license_date «not-a-date».
3. Зафиксировать статусы и тела; после каждого — SELECT COUNT(*).

## Ожидаемый результат
1–2. Оба ответа 422 {"ok": false, "error": "Дата выдачи ВУ: неверный формат"}.
3. После каждого запроса COUNT = 0.

## Тестовые данные
Базовый валидный набор (TC-APP-005); license_date-вариации: «01.05.2020», «not-a-date»; валидный референс — «2020-05-01».
