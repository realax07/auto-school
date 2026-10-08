# TC-REG-009 — Граница длины пароля снизу: 7 и 1 символ

- ID кейса: TC-REG-009
- ID чеклиста: CHK-9
- Источник: CHK-9 → Requirement «Отклонение некорректной регистрации» (домен registration) → FR-2; Scenario «Пароль короче 8 символов»
- Тип: граничный
- Приоритет: Must

## Предусловия
- Сервис запущен (uvicorn, single-worker); базовый URL: http://127.0.0.1:8000.
- БД data/app.db инициализирована (init_db при старте), таблица users пуста (чистое тестовое окружение).
- Окружение .env задано: ADMIN_USER, ADMIN_PASSWORD_HASH (bcrypt), SECRET.
- Контроль живости: GET /api/health -> 200 {"ok": true}.

## Шаги
1. POST /api/register: password = "Qwerty1" (7 символов), password_confirm = "Qwerty1", остальные поля валидны.
2. Зафиксировать статус/тело; SELECT COUNT(*) FROM users;
3. POST /api/register: password = "a" (1 символ), password_confirm = "a", остальные поля валидны.
4. Зафиксировать статус/тело; SELECT COUNT(*) FROM users;

## Ожидаемый результат
1–2. 422 {"ok": false, "error": "Пароль: …"} — причина «пароль должен быть не короче 8 символов»; COUNT(*) = 0.
3–4. 422 {"ok": false, "error": "Пароль: …"}; COUNT(*) = 0.

## Тестовые данные
- Прогон 1: пароль и подтверждение `Qwerty1` (7 символов); Прогон 2: `a` (1 символ).
- Остальные поля — из базового набора (email каждый раз уникальный: p7@example.com, p1@example.com).
