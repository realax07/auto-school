# TC-ADM-003 — Вход с логином, не совпадающим с ADMIN_USER

- ID кейса: TC-ADM-003
- ID чеклиста: CHK-21
- Источник: CHK-21 → Requirement «Вход администратора» (домен admin) → FR-5; Scenario «Вход с неизвестным логином»
- Тип: негативный
- Приоритет: Must

## Предусловия
- Сервис запущен (uvicorn, single-worker); базовый URL: http://127.0.0.1:8000.
- БД data/app.db инициализирована (init_db при старте), таблица users пуста (чистое тестовое окружение).
- Окружение .env задано: ADMIN_USER, ADMIN_PASSWORD_HASH (bcrypt), SECRET.
- Контроль живости: GET /api/health -> 200 {"ok": true}.

## Шаги
1. POST /api/admin/login: login = "root" (≠ ADMIN_USER), password = верный пароль.
2. Зафиксировать статус/тело.
3. POST /api/admin/login: login = "root", password = "WrongPass1" (и неверный пароль) — «при любом пароле».
4. Проверить наличие ключа token в обоих телах.

## Ожидаемый результат
1–2. 401 {"ok": false}; token отсутствует.
3–4. 401 {"ok": false}; token отсутствует в обоих прогонах.

## Тестовые данные
- Прогон 1: login `root`, верный пароль. Прогон 2: login `root`, пароль `WrongPass1`.
