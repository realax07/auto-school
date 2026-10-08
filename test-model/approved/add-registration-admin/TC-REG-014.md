# TC-REG-014 — В хранилище bcrypt-хэш cost 12, открытого пароля нет

- ID кейса: TC-REG-014
- ID чеклиста: CHK-14
- Источник: CHK-14 → Requirement «Хранение пароля в виде bcrypt-хэша» (домен registration) → FR-3; Scenario «Хэш вместо открытого пароля»
- Тип: позитивный
- Приоритет: Must

## Предусловия
- Сервис запущен (uvicorn, single-worker); базовый URL: http://127.0.0.1:8000.
- БД data/app.db инициализирована (init_db при старте), таблица users пуста (чистое тестовое окружение).
- Окружение .env задано: ADMIN_USER, ADMIN_PASSWORD_HASH (bcrypt), SECRET.
- Контроль живости: GET /api/health -> 200 {"ok": true}.

## Шаги
1. POST /api/register с базовым пользователем (пароль «Qwerty123») → 200.
2. Прямой просмотр хранилища: SELECT password_hash FROM users WHERE email = 'petrova@example.com';
3. Проверить префикс хэша и длину; выполнить поиск подстроки «Qwerty123» в значении password_hash и во всех остальных колонках записи.

## Ожидаемый результат
1. 200 {"ok": true}.
2. password_hash начинается с `$2b$12$` или `$2a$12$` (bcrypt, cost 12), длина 60 символов.
3. Открытая строка «Qwerty123» в хранилище отсутствует (ни в password_hash, ни в какой другой колонке).

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
