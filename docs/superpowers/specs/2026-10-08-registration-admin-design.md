# Спека: Регистрация и админ-контур (спринт-0)

> Дизайн утвержден Заказчиком 2026-10-08 (чат-лог): стек FastAPI+SQLite,
> фронт — утвержденные макеты design/mocks. Два решения Заказчика: (1) форма
> регистрации получает пароль + подтверждение; (2) админ-учетка из .env.

## Цель

Минимальный работающий контур: регистрация ученика сохраняется в БД, админ
через прямую ссылку входит и видит записи + выгружает CSV. Фронт — статика,
отдаваемая тем же сервисом.

## Стек

- Python 3.11+, FastAPI, uvicorn
- SQLite (файл `data/app.db`, WAL)
- Стандартная библиотека + fastapi, uvicorn, bcrypt (через passlib не нужно — bcrypt напрямую)
- Фронт: чистые HTML/CSS/JS из design/mocks (без сборки)

## Структура

```
backend/
  app.py        — FastAPI: сборка, статика, health
  db.py         — SQLite: схема, connection
  register.py   — POST /api/register
  admin.py      — POST /api/admin/login, GET /api/admin/users, GET /api/admin/users/export.csv
  config.py     — чтение .env (ADMIN_USER, ADMIN_PASSWORD_HASH, SECRET)
frontend/
  index.html            — лендинг (из design/mocks/landing-students.html)
  registered.html       — после регистрации
  admin-login.html      — вход админки
  admin-dashboard.html  — дашборд админки (реальные данные из API)
  assets/…              — общие стили/скрипты при выделении
tests/
  test_register.py
  test_admin.py
data/           — app.db (в .gitignore)
.env.example    — ADMIN_USER, ADMIN_PASSWORD_HASH, инструкция генерации
```

## API (контракт, OpenAPI автогенерируется)

### POST /api/register
- Body (JSON): `{surname, name, patronymic, email, phone, password, password_confirm}`
- Валидации: все поля обязательны (patronymic опционален? — НЕТ, обязателен по макету);
  email — формат; телефон — маска свободная, min 10 цифр; password min 8 символов;
  password == password_confirm; email уникален.
- 200 → `{ok: true}`; 422 → `{ok: false, error: "<поле>: <причина>"}` (первая ошибка).
- Пароль хранится bcrypt-хэшем.

### POST /api/admin/login
- Body: `{login, password}`
- Сверка с env: ADMIN_USER + bcrypt-проверка ADMIN_PASSWORD_HASH.
- 200 → `{ok: true, token: "<secrets.token_url_safe()>"}`; 401 → `{ok:false}`.
- Токен в памяти процесса (спринт-0, single-worker), TTL 12ч.
- Заголовок `X-Admin-Token` обязателен для admin-API ниже.

### GET /api/admin/users (X-Admin-Token)
- 200 → `{count: N, users: [{id, fio, email, phone, created_at}]}`
- 401 при неверном/просроченном токене.

### GET /api/admin/users/export.csv (X-Admin-Token)
- CSV с BOM, разделитель `;`, колонки: ФИО;Email;Телефон;Роль;Дата регистрации
- Роль у всех «Ученик» (инструкторы появятся в следующем спринте).

### GET /api/health
- 200 `{ok: true}`

## Статика

- `/` → frontend/index.html
- `/registered`, `/admin-login`, `/admin-dashboard` → соответствующие html
- Остальные статические файлы — из frontend/ по пути.
- Модалка регистрации на лендинге: добавлены поля Пароль/Подтверждение (тип
  password), сабмит → fetch POST /api/register → при ok redirect /registered,
  при ошибке — показ текста ошибки под формой.

## Схема БД

```sql
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  surname TEXT NOT NULL,
  name TEXT NOT NULL,
  patronymic TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  phone TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

## Безопасность (спринт-0 уровень)

- Пароли — bcrypt (cost 12)
- Админ-пароль: в .env хранится bcrypt-хэш, не открытый текст
- Токен админа в памяти, теряется при рестарте (приемлемо, задокументировано)
- SQL — только параметризованные запросы
- Секреты не коммитятся: .env в .gitignore, есть .env.example
- **CSV-инъекция (MAJ-2, решение ПМ по мандату Заказчика «Реши как лучше»
  2026-10-08): санитизация ячеек — значение, начинающееся с `=`, `+`, `-`,
  `@`, при экспорте получает префикс `'` (одинарная кавычка) — Excel/LO
  показывают строку, формула не исполняется. Логика в export-функции,
  тест: ячейка `=1+1` в CSV превращается в `'=1+1`**

## Обработка ошибок регистрации (MAJ-1, решение ПМ)

- Pydantic-модель запроса: все поля `str = ""` (дефолты), строгость — в
  хендлере: проверка обязательности в фиксированном порядке (surname, name,
  patronymic, email, phone, password, password_confirm), затем формат email,
  телефон ≥ 10 цифр, пароль ≥ 8, совпадение confirm, дубликат email.
- Любая ошибка → 422 `{ok:false, error:"<поле-ру>: <причина>"}` — контракт
  sdd §3.1 соблюдается и при отсутствующем ключе JSON.
- Тест: тело без поля `email` → 422 с `error`, начинающимся с `email`.


## Не в этом спринте

Личные кабинеты, инструкторы, nginx/контейнеры/деплой, восстановление пароля,
email/SMS-подтверждение, refresh-токены.

## Критерии приемки

1. `pytest tests/` зеленый
2. Ручной сценарий: открыть / → Зарегистрироваться → заполнить (с паролем) →
   на /registered; запись видна в админке и в CSV
3. Админ-вход с неверным паролем — 401, запись в базу не пишется
4. `flow_check` OK, CI зеленый
