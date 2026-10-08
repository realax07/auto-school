# TC-REG-012 — Регистрация с уже существующим email отклоняется

- ID кейса: TC-REG-012
- ID чеклиста: CHK-12
- Источник: CHK-12 → Requirement «Отклонение некорректной регистрации» (домен registration) → FR-2; Scenario «Email уже зарегистрирован»
- Тип: негативный
- Приоритет: Must

## Предусловия
- Сервис запущен (uvicorn, single-worker); базовый URL: http://127.0.0.1:8000.
- БД data/app.db инициализирована (init_db при старте), таблица users пуста (чистое тестовое окружение).
- Окружение .env задано: ADMIN_USER, ADMIN_PASSWORD_HASH (bcrypt), SECRET.
- Контроль живости: GET /api/health -> 200 {"ok": true}.

## Шаги
1. POST /api/register: пользователь A с email E = "petrova@example.com" (остальные поля базовые) → успешная регистрация.
2. POST /api/register: пользователь B с тем же email E и ДРУГИМИ остальными полями (surname «Сидоров», name «Иван», patronymic «Петрович», телефон «+7 900 111-22-33»).
3. Зафиксировать статус/тело второго ответа.
4. SELECT COUNT(*) FROM users WHERE email = 'petrova@example.com';

## Ожидаемый результат
1. 200 {"ok": true}.
2–3. 422 {"ok": false, "error": "Email: …"} — причина «email уже зарегистрирован» (не 500).
4. COUNT = 1 — второй записи с E нет; всего в users одна запись.

## Тестовые данные
- Пользователь A: базовый набор (email `petrova@example.com`).
- Пользователь B: surname `Сидоров`, name `Иван`, patronymic `Петрович`, email `petrova@example.com`, phone `+7 900 111-22-33`, пароли `Parol9999`.
