# TC-APP-005 — Негатив: файл ВУ не сохраняется и не входит в заявку

- ID кейса: TC-APP-005
- ID чеклиста: CHK-5
- Источник: CHK-5 → Requirement «Данные ВУ-файла не сохраняются» (домен instructor-application) → FR-11 (ограничение ТЗ); Scenario «Файл не загружается на сервер»
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_instructor_pages.py::test_apply_submit_wiring (FormData отсутствует, license-file не входит в payload; поле файла — только визуальное «макет без реальной загрузки») + tests/test_instructors_apply.py::test_apply_success_creates_waiting_application_with_hash (заявка создается; контракт §15.1 не содержит поля файла). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN открыта анкета /instructors/apply, заполненная корректными данными; пользователь выбрал файл ВУ в элементе «Прикрепить фото или скан»
- WHEN анкета отправляется (POST /api/instructors/apply)
- THEN файл НЕ сохраняется системой: элемент визуальный, файл отсутствует в теле POST и в данных созданной заявки (в контракте §15.1 поля файла нет); заявка создается со статусом waiting без него; система не запрашивает, не принимает и не хранит файл ВУ

## Предусловия
- Сервис собран через create_app(); TestClient без сети; чистая БД (AUTOSCHOOL_DB_PATH в tmp), init_db.
- GET /api/health → 200.

## Шаги
1. Заполнить анкету базовым валидным набором (см. Тестовые данные); в элементе «Прикрепить фото или скан» выбрать произвольный файл license.pdf.
2. Отправить анкету; перехватить тело POST /api/instructors/apply.
3. Прочитать запись заявки из instructor_applications по email.
4. Проверить файловую систему/БД на отсутствие сохраненного файла.

## Ожидаемый результат
2. Тело POST — JSON контракта §15.1 (13 полей); ключа файла (license-file/FormData) нет.
3. Заявка создана, status='waiting'; колонки записи соответствуют §16 — поля файла нет.
4. Сохраненного файла не существует нигде; заявка создана без него.

## Тестовые данные
Базовый валидный набор анкеты (контракт §15.1): fio «Иванов Иван Иванович», phone «+7 (912) 345-67-89», email instructor@example.com, address «Москва, Тверская 1, кв. 2», work_format «own», plate «А123АА 777», license_number «1234 567890», license_date «2020-05-01», license_category «B», experience «5–9 лет», password/password_confirm «Qwerty123», consent true. Файл: license.pdf (любое непустое содержимое).
