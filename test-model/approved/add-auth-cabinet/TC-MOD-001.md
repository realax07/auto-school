# TC-MOD-001 — Сквозной вход через модалку m-login лендинга

- ID кейса: TC-MOD-001
- ID чеклиста: CHK-27
- Источник: CHK-27 → Requirement «Вход ученика» (домен auth) → FR-1, FR-4; Scenario «Успешный вход ученика» + «После входа открыт кабинет»; sdd §10.4
- Тип: позитивный
- Приоритет: Must
- Статус: manual/toBeAutomated (браузерный сабмит с реальным fetch/редиректом — вне TestClient; косвенный автоконтроль wiring — tests/test_login_modal.py::test_tc_auth_login_wiring_fragments_present, test_tc_auth_landing_page_served_with_wiring; API-часть — TC-AUTH-001, automated)

## GIVEN / WHEN / THEN
- GIVEN в системе зарегистрирован ученик с email E и паролем P; открыта модалка входа m-login на лендинге /
- WHEN пользователь вводит E и P и нажимает «Войти» (сабмит → POST /api/auth/login → 200)
- THEN токен сохраняется в sessionStorage (ключ session_token), выполняется редирект на /cabinet, кабинет открыт

## Предусловия
- Браузер/Playwright с перехватом сети; ученик зарегистрирован (базовый пользователь).

## Шаги
1. Открыть /; убедиться, что модалка m-login доступна.
2. Ввести email petrova@example.com и пароль Qwerty123 в поля формы.
3. Нажать «Войти»; перехватить POST /api/auth/login.
4. Зафиксировать: статус ответа, sessionStorage.session_token, итоговый URL.
5. Зафиксировать состояние кабинета (заголовки, отсутствие ошибки).

## Ожидаемый результат
3. POST /api/auth/login → 200 {"ok": true, "token": "..."}.
4. sessionStorage.session_token == token из ответа; итоговый URL «/cabinet».
5. Кабинет открыт: приветствие с именем пользователя, ошибок нет.

## Тестовые данные
Базовый пользователь TC-AUTH-001 (petrova@example.com / Qwerty123).
