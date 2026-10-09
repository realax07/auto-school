# TC-MOD-003 — Тексты модалки входа m-login дословно по мокапу

- ID кейса: TC-MOD-003
- ID чеклиста: CHK-29
- Источник: CHK-29 → Requirement «Соответствие утвержденным макетам» (домен cabinet) → FR-9; мокап design/mocks/login-modal.html; sdd §10.4
- Тип: позитивный
- Приоритет: Must
- Статус: automated — tests/test_login_modal.py::test_tc_auth_login_modal_texts_verbatim, test_tc_auth_login_modal_no_stub_submit

## GIVEN / WHEN / THEN
- GIVEN открыт лендинг / с модалкой входа m-login
- WHEN выполняется текстовое сравнение модалки с design/mocks/login-modal.html
- THEN заголовок, подзаголовок, плейсхолдеры, кнопки и alt-строка регистрации совпадают дословно; отличия — только wiring (id полей: login-email/login-password/login-submit/login-error, место вывода ошибки)

## Предусловия
- frontend/index.html содержит блок модалки «Вход (утвержденный мокап)»; мокап design/mocks/login-modal.html существует.

## Шаги
1. Вырезать из frontend/index.html секцию между комментариями «Модалка: Вход (утвержденный мокап)» и «Модалка: Регистрация (утвержденный мокап)».
2. Проверить дословные строки: overlay id="m-login", «<h2>Вход</h2>», «Войдите в личный кабинет», «<label>Логин</label>», placeholder="email или телефон", «<label>Пароль</label>», placeholder="••••••••".
3. Проверить wiring: id="login-submit" присутствует, alert-заглушка «Заглушка: бэкенд не подключен» отсутствует; alt-строка перехода на регистрацию — текст из мокапа.

## Ожидаемый результат
2. Все текстовые строки присутствуют дословно.
3. Заглушка заменена сабмитом; id-атрибуты и место ошибки — единственные отличия; alt-строка регистрации дословно из мокапа.

## Тестовые данные
Страница: frontend/index.html (отдается GET /); мокап: design/mocks/login-modal.html.
