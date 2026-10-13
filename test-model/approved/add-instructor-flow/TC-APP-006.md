# TC-APP-006 — Успешная отправка анкеты: заявка waiting, переход на экран ожидания

- ID кейса: TC-APP-006
- ID чеклиста: CHK-6
- Источник: CHK-6 → Requirement «Сохранение заявки со статусом waiting» (домен instructor-application) → FR-12; Scenario «Успешная отправка анкеты»
- Тип: позитивный
- Приоритет: Must
- Статус: automated — tests/test_instructors_apply.py::test_apply_success_creates_waiting_application_with_hash (200 {"ok": true}; заявка waiting со всеми данными, ФИО разобрано, bcrypt-хэш) ; переход на /instructors/pending — wiring-контроль tests/test_instructor_pages.py::test_apply_submit_wiring (location.href='/instructors/pending'), браузерный редирект — manual/toBeAutomated

## GIVEN / WHEN / THEN
- GIVEN анкета заполнена корректно: все обязательные поля, пароли совпадают, email свободен (нет ни в users, ни в заявках)
- WHEN POST /api/instructors/apply с корректным телом
- THEN 200 {"ok": true}; в instructor_applications создана заявка со статусом waiting со всеми введенными данными (ФИО разобрано на surname/name/patronymic); пользователь переводится на /instructors/pending («заявка на рассмотрении»)

## Предусловия
- Сервис собран через create_app(); TestClient без сети; чистая БД в tmp, init_db; /api/health → 200.
- Email instructor@example.com отсутствует в users и instructor_applications.

## Шаги
1. POST /api/instructors/apply с базовым валидным набором → зафиксировать статус и тело.
2. Прямой SELECT из instructor_applications по email.
3. Проверить редирект-проводку фронта (wiring: 200 → location.href='/instructors/pending'); при браузерном прогоне — итоговый URL.

## Ожидаемый результат
1. 200 {"ok": true}.
2. Одна запись: surname «Иванов», name «Иван», patronymic «Иванович», phone/address/work_format/plate/license_*/experience — как введено, status='waiting', review_comment=''.
3. Пользователь на /instructors/pending, экран «Заявка на рассмотрении».

## Тестовые данные
Базовый валидный набор анкеты (TC-APP-005, Тестовые данные): instructor@example.com / Qwerty123, work_format «own».
