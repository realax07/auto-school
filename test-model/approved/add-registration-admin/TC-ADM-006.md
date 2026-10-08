# TC-ADM-006 — Свежие записи сверху

- ID кейса: TC-ADM-006
- ID чеклиста: CHK-24
- Источник: CHK-24 → Requirement «Список зарегистрированных пользователей» (домен admin) → FR-6; Scenario «Свежие записи сверху»
- Тип: позитивный
- Приоритет: Must

## Предусловия
- Сервис запущен (uvicorn, single-worker); базовый URL: http://127.0.0.1:8000.
- БД data/app.db инициализирована (init_db при старте), таблица users пуста (чистое тестовое окружение).
- Окружение .env задано: ADMIN_USER, ADMIN_PASSWORD_HASH (bcrypt), SECRET.
- Контроль живости: GET /api/health -> 200 {"ok": true}.

## Шаги
1. Зарегистрировать U1 (email "u1@example.com").
2. Подождать не менее 2 секунд (гарантированно другой created_at).
3. Зарегистрировать U2 (email "u2@example.com").
4. Войти администратором, GET /api/admin/users с токеном.
5. Проверить порядок email в users.

## Ожидаемый результат
1, 3. Обе регистрации: 200.
4–5. users[0].email = "u2@example.com" (более поздняя запись), users[1].email = "u1@example.com" — свежая запись выше.

## Тестовые данные
- U1: email `u1@example.com`; U2: email `u2@example.com`; остальные поля — из базового набора.
