# TC-APP-012 — Негатив: подтверждение не совпадает с паролем → 422

- ID кейса: TC-APP-012
- ID чеклиста: CHK-12
- Источник: CHK-12 → Requirement «Сохранение заявки со статусом waiting» (домен instructor-application) → FR-11; Scenario «Отклонение некорректно заполненной анкеты»
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_instructors_apply.py::test_apply_validation_contract_422 (вариант {"password_confirm": "OtherPass123"} → «Подтверждение пароля: пароли не совпадают», COUNT=0). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN анкета заполнена базовым валидным набором
- WHEN в подтверждение пароля подставляется значение, отличное от пароля, и анкета отправляется
- THEN 422, заявка НЕ создана

## Предусловия
- Сервис собран через create_app() с роутером instructors; TestClient без сети; чистая БД в tmp, init_db.

## Шаги
1. POST /api/instructors/apply с password «Qwerty123», password_confirm «OtherPass123».
2. Зафиксировать статус и тело.
3. SELECT COUNT(*) FROM instructor_applications.

## Ожидаемый результат
1–2. 422 {"ok": false, "error": "Подтверждение пароля: пароли не совпадают"}.
3. COUNT = 0.

## Тестовые данные
Базовый валидный набор (TC-APP-005); password «Qwerty123», password_confirm «OtherPass123».
