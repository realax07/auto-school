# TC-ADM-001 — Успешный вход администратора

- ID кейса: TC-ADM-001
- ID чеклиста: CHK-19
- Источник: CHK-19 → Requirement «Вход администратора» (домен admin) → FR-5; Scenario «Успешный вход администратора»
- Тип: позитивный
- Приоритет: Must

## Предусловия
- Сервис запущен (uvicorn, single-worker); базовый URL: http://127.0.0.1:8000.
- БД data/app.db инициализирована (init_db при старте), таблица users пуста (чистое тестовое окружение).
- Окружение .env задано: ADMIN_USER, ADMIN_PASSWORD_HASH (bcrypt), SECRET.
- Контроль живости: GET /api/health -> 200 {"ok": true}.
- Значение ADMIN_PASSWORD_HASH в .env соответствует известному тестеру паролю (сгенерирован по инструкции .env.example).

## Шаги
1. POST /api/admin/login с телом {"login": "<ADMIN_USER>", "password": "<пароль, соответствующий ADMIN_PASSWORD_HASH>"}.
2. Зафиксировать статус и тело (наличие token).
3. GET /api/admin/users с заголовком X-Admin-Token: <token> — убедиться, что доступ к админке открыт.

## Ожидаемый результат
1–2. 200 {"ok": true, "token": "<строка>"}; token непуст (secrets.token_urlsafe).
3. 200 {"count": N, "users": [...]} — доступ к админке открыт.

## Тестовые данные
- login: значение ADMIN_USER из .env; password: известный тестеру пароль, bcrypt-хэш которого лежит в ADMIN_PASSWORD_HASH.
