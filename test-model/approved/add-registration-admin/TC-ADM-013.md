# TC-ADM-013 — Админ-API отвечает данным при валидном токене

- ID кейса: TC-ADM-013
- ID чеклиста: CHK-31
- Источник: CHK-31 → Requirement «Токен доступа к админ-API» (домен admin) → FR-8; Scenario «Доступ с валидным токеном»
- Тип: позитивный
- Приоритет: Must

## Предусловия
- Сервис запущен (uvicorn, single-worker); базовый URL: http://127.0.0.1:8000.
- БД data/app.db инициализирована (init_db при старте), таблица users пуста (чистое тестовое окружение).
- Окружение .env задано: ADMIN_USER, ADMIN_PASSWORD_HASH (bcrypt), SECRET.
- Контроль живости: GET /api/health -> 200 {"ok": true}.

## Шаги
1. Зарегистрировать пользователя (базовый набор).
2. POST /api/admin/login с корректными учетными данными → token.
3. GET /api/admin/users с заголовком X-Admin-Token: <token>.
4. Сверить count и поля users с данными в БД.

## Ожидаемый результат
2. 200 {"ok": true, "token": "..."}.
3–4. 200 {"count": 1, "users": [...]}; данные возвращаются и совпадают с записью в БД (fio, email, phone, created_at).

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
