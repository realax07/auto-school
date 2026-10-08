# TC-REG-008 — Инвариант: ни одной записи при любом отклонении валидации

- ID кейса: TC-REG-008
- ID чеклиста: CHK-8
- Источник: CHK-8 → Requirement «Отклонение некорректной регистрации» (домен registration) → FR-2; инвариант сценариев «…ни одна запись не создается»
- Тип: негативный
- Приоритет: Must

## Предусловия
- Сервис запущен (uvicorn, single-worker); базовый URL: http://127.0.0.1:8000.
- БД data/app.db инициализирована (init_db при старте), таблица users пуста (чистое тестовое окружение).
- Окружение .env задано: ADMIN_USER, ADMIN_PASSWORD_HASH (bcrypt), SECRET.
- Контроль живости: GET /api/health -> 200 {"ok": true}.

## Шаги
1. POST /api/register с пустым полем email = "" (негатив CHK-4).
2. POST /api/register без ключа surname в JSON (негатив CHK-5).
3. POST /api/register с email = "ivanov.example" (негатив CHK-6).
4. POST /api/register с email = "ivanov@" (негатив CHK-7).
5. POST /api/register с password = "Qwerty1" (7 символов) и совпадающим подтверждением (негатив CHK-9).
6. POST /api/register с password = "Qwerty123" и password_confirm = "Qwerty12A" (несовпадение).
7. После КАЖДОГО из прогонов 1–6: SELECT COUNT(*) FROM users;
8. Контроль работоспособности: POST /api/register с полностью валидными базовыми данными.

## Ожидаемый результат
1–6. Каждый прогон: 422 {"ok": false, "error": "<Поле-ру>: <причина>"}.
7. После каждого негативного прогона COUNT(*) = 0 — в хранилище не появилось ни одной записи.
8. 200 {"ok": true}, COUNT(*) = 1 (сервис продолжает корректно сохранять валидные данные после серии отклонений).

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
