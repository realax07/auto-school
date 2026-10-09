# TC-AUTH-001 — Успешный вход ученика, сессионный токен выдан

- ID кейса: TC-AUTH-001
- ID чеклиста: CHK-1
- Источник: CHK-1 → Requirement «Вход ученика» (домен auth) → FR-1; Scenario «Успешный вход ученика»
- Тип: позитивный
- Приоритет: Must
- Статус: automated — tests/test_auth.py::test_login_success_issues_token

## GIVEN / WHEN / THEN
- GIVEN в системе зарегистрирован ученик с email E и паролем P (пароль хранится в виде bcrypt-хэша)
- WHEN POST /api/auth/login с телом {"email": E, "password": P}
- THEN 200 {"ok": true, "token": "<строка>"}; сессионный токен выдан: secrets.token_urlsafe(32) — 43 символа base64url ([A-Za-z0-9_-]), поле token присутствует

## Предусловия
- Сервис собран через create_app() (uvicorn, single-worker); базовый URL http://127.0.0.1:8000; допускается TestClient без сети (паттерн tests/conftest.py).
- Чистая БД (AUTOSCHOOL_DB_PATH в tmp), init_db при старте.
- Env: ADMIN_USER, ADMIN_PASSWORD_HASH (bcrypt), SECRET.
- Контроль живости: GET /api/health → 200 {"ok": true}.

## Шаги
1. POST /api/register с базовым валидным пользователем (см. Тестовые данные) → дождаться 200.
2. POST /api/auth/login с телом {"email": "petrova@example.com", "password": "Qwerty123"}.
3. Зафиксировать статус и тело ответа; проверить формат токена (длина 43, символы base64url).

## Ожидаемый результат
1. 200 {"ok": true}.
2–3. 200; тело {"ok": true, "token": "<43 символа base64url>"}; поле token — непустая строка, token.replace("-","").replace("_","").isalnum() == true.

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
Тело логина: {"email": "petrova@example.com", "password": "Qwerty123"}.
