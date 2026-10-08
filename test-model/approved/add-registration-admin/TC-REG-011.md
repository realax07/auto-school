# TC-REG-011 — Пароль и подтверждение не совпадают

- ID кейса: TC-REG-011
- ID чеклиста: CHK-11
- Источник: CHK-11 → Requirement «Отклонение некорректной регистрации» (домен registration) → FR-2; Scenario «Пароль и подтверждение не совпадают»
- Тип: негативный
- Приоритет: Must

## Предусловия
- Сервис запущен (uvicorn, single-worker); базовый URL: http://127.0.0.1:8000.
- БД data/app.db инициализирована (init_db при старте), таблица users пуста (чистое тестовое окружение).
- Окружение .env задано: ADMIN_USER, ADMIN_PASSWORD_HASH (bcrypt), SECRET.
- Контроль живости: GET /api/health -> 200 {"ok": true}.

## Шаги
1. POST /api/register: password = "Qwerty123" (корректный, 8+), password_confirm = "Qwerty12A" (отличается одним символом), остальные поля валидны.
2. Зафиксировать статус/тело.
3. SELECT COUNT(*) FROM users;

## Ожидаемый результат
1–2. 422 {"ok": false, "error": "…"} — причина «пароль и подтверждение не совпадают».
3. COUNT(*) = 0 — запись не создана.

## Тестовые данные
- password: `Qwerty123`; password_confirm: `Qwerty12A`; остальные поля — из базового набора.
