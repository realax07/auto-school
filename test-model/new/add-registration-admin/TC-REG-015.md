# TC-REG-015 — Хэш обратимо проверяем bcrypt.checkpw

- ID кейса: TC-REG-015
- ID чеклиста: CHK-15
- Источник: CHK-15 → Requirement «Хранение пароля в виде bcrypt-хэша» (домен registration) → FR-3; Scenario «Хэш вместо открытого пароля»
- Тип: позитивный
- Приоритет: Must

## Предусловия
- Сервис запущен (uvicorn, single-worker); базовый URL: http://127.0.0.1:8000.
- БД data/app.db инициализирована (init_db при старте), таблица users пуста (чистое тестовое окружение).
- Окружение .env задано: ADMIN_USER, ADMIN_PASSWORD_HASH (bcrypt), SECRET.
- Контроль живости: GET /api/health -> 200 {"ok": true}.

## Шаги
1. POST /api/register с базовым пользователем (пароль P = «Qwerty123») → 200.
2. Взять password_hash из БД и выполнить: python3 -c "import bcrypt; h=open('hash.txt','rb').read(); print(bcrypt.checkpw(b'Qwerty123', h))".
3. Контроль: bcrypt.checkpw(b'WrongPass1', h) — с заведомо неверным паролем.

## Ожидаемый результат
1. 200 {"ok": true}.
2. checkpw(P, hash) → True — хэш соответствует введенному паролю (не мусор).
3. checkpw с неверным паролем → False.

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
