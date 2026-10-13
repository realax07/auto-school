# TC-APP-013 — Негатив: work_format='own' с пустым госномером → 422

- ID кейса: TC-APP-013
- ID чеклиста: CHK-13
- Источник: CHK-13 → Requirement «Сохранение заявки со статусом waiting» (домен instructor-application) → FR-11; Scenario «Отклонение некорректно заполненной анкеты»
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_instructors_apply.py::test_apply_validation_contract_422 (вариант {"work_format": "own", "plate": ""} → «Госномер: поле обязательно», COUNT=0) + граничное допущение ::test_apply_sber_format_allows_empty_plate (sber — plate не обязателен). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN анкета заполнена базовым валидным набором с work_format='own'
- WHEN поле госномера опустошается и анкета отправляется
- THEN 422 (plate обязателен при own), заявка НЕ создана

## Предусловия
- Сервис собран через create_app() с роутером instructors; TestClient без сети; чистая БД в tmp, init_db.

## Шаги
1. POST /api/instructors/apply с work_format='own', plate=''.
2. Зафиксировать статус и тело.
3. SELECT COUNT(*) FROM instructor_applications.

## Ожидаемый результат
1–2. 422 {"ok": false, "error": "Госномер: поле обязательно"}.
3. COUNT = 0.
Контрольная грань: тот же набор с work_format='sber', plate='' → 200 (поле «если свой»).

## Тестовые данные
Базовый валидный набор (TC-APP-005); вариации: (own, plate=''), (sber, plate='').
