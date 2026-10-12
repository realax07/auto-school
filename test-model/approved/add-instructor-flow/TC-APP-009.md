# TC-APP-009 — Негатив: неверный формат email → 422

- ID кейса: TC-APP-009
- ID чеклиста: CHK-9
- Источник: CHK-9 → Requirement «Сохранение заявки со статусом waiting» (домен instructor-application) → FR-11; Scenario «Отклонение некорректно заполненной анкеты»
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_instructors_apply.py::test_apply_validation_contract_422 (варианты {"email": "not-an-email"} и {"email": "a@b"} → «Email: неверный формат», COUNT=0). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN анкета заполнена базовым валидным набором
- WHEN в поле email подставляется значение в неверном формате и анкета отправляется (отдельный прогон на значение)
- THEN 422 с указанием поля («Email: неверный формат»), заявка НЕ создана

## Предусловия
- Сервис собран через create_app() с роутером instructors; TestClient без сети; чистая БД в tmp, init_db.

## Шаги
1. POST /api/instructors/apply с email «not-an-email».
2. POST /api/instructors/apply с email «a@b» (без доменной части).
3. Зафиксировать статусы и тела; после каждого — SELECT COUNT(*).

## Ожидаемый результат
1–2. Оба ответа 422 {"ok": false, "error": "Email: неверный формат"}.
3. После каждого запроса COUNT = 0.

## Тестовые данные
Базовый валидный набор (TC-APP-005); email-вариации: «not-an-email», «a@b».
