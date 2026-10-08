# TC-REG-013 — Граница дубликата: повторная регистрация того же email

- ID кейса: TC-REG-013
- ID чеклиста: CHK-13
- Источник: CHK-13 → Requirement «Отклонение некорректной регистрации» (домен registration) → FR-2; Scenario «Email уже зарегистрирован»
- Тип: граничный
- Приоритет: Must

## Предусловия
- Сервис запущен (uvicorn, single-worker); базовый URL: http://127.0.0.1:8000.
- БД data/app.db инициализирована (init_db при старте), таблица users пуста (чистое тестовое окружение).
- Окружение .env задано: ADMIN_USER, ADMIN_PASSWORD_HASH (bcrypt), SECRET.
- Контроль живости: GET /api/health -> 200 {"ok": true}.

## Шаги
1. POST /api/register: базовый пользователь (первая регистрация) → успех.
2. POST /api/register: ТОЧНО те же данные повторно.
3. SELECT COUNT(*) FROM users; и SELECT COUNT(*) FROM users WHERE email = 'petrova@example.com';

## Ожидаемый результат
1. 200 {"ok": true}.
2. 422 {"ok": false, "error": "Email: email уже зарегистрирован"}.
3. Всего записей 1; записей с этим email — ровно одна.

## Тестовые данные
Базовый валидный пользователь (все 7 полей):
```json
{
  "surname": "Петрова-Водкина",
  "name": "Анна",
  "patronymic": "Оттовна",
  "email": "petrova@example.com",
  "phone": "+7 (912) 345-67-89",
  "password": "Qwerty123",
  "password_confirm": "Qwerty123"
}
```
