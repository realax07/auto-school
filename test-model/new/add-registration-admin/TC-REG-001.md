# TC-REG-001 — Успешная регистрация ученика

- ID кейса: TC-REG-001
- ID чеклиста: CHK-1
- Источник: CHK-1 → Requirement «Сохранение регистрации ученика» (домен registration) → FR-1; Scenario «Успешная регистрация ученика»
- Тип: позитивный
- Приоритет: Must

## Предусловия
- Сервис запущен (uvicorn, single-worker); базовый URL: http://127.0.0.1:8000.
- БД data/app.db инициализирована (init_db при старте), таблица users пуста (чистое тестовое окружение).
- Окружение .env задано: ADMIN_USER, ADMIN_PASSWORD_HASH (bcrypt), SECRET.
- Контроль живости: GET /api/health -> 200 {"ok": true}.

## Шаги
1. GET /api/health — убедиться, что сервис жив (200).
2. POST /api/register с телом базового пользователя (все 7 полей корректны).
3. Зафиксировать статус и тело ответа.
4. Прямой просмотр хранилища: выполнить в data/app.db запрос SELECT id, surname, name, patronymic, email, phone FROM users;

## Ожидаемый результат
1. 200 {"ok": true}.
2–3. Ответ 200, тело {"ok": true} (без ошибок, без detail).
4. В таблице users ровно одна запись; значения посимвольно совпадают с введенными: surname = «Петрова-Водкина», name = «Анна», patronymic = «Оттовна», email = «petrova@example.com», phone = «+7 (912) 345-67-89».

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
