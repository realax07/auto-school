# SDD: Регистрация и админ-контур (Спринт 0)

> Системный дизайн change `add-registration-admin`. Источник решений —
> утвержденный Заказчиком дизайн 2026-10-08
> (docs/superpowers/specs/2026-10-08-registration-admin-design.md) и ТЗ
> requirements.md (УТВЕРЖДЕН). Спеки поведения —
> openspec/changes/add-registration-admin/specs/.

## 1. Стек

| Слой | Выбор | Основание |
|---|---|---|
| Язык | Python ≥ 3.11 | Ограничение ТЗ |
| Фреймворк | FastAPI + uvicorn | Ограничение ТЗ; OpenAPI автогенерируется (паттерн 7 map.md) |
| БД | SQLite, файл data/app.db, режим WAL | Ограничение ТЗ; паттерн 3 (свои данные у сервиса) |
| Хэширование | bcrypt напрямую (cost 12), без passlib | Решение Заказчика (FR-3, FR-5) |
| Авторизация админа | in-memory токен secrets.token_urlsafe(32), TTL 12 ч, single-worker | Решение Заказчика; ограничение задокументировано |
| Фронт | Чистые HTML/CSS/JS из design/mocks, без сборки | Решение Заказчика (FR-9) |
| Зависимости | fastapi, uvicorn, bcrypt; dev: pytest, httpx | Больше ничего |

## 2. Компоненты

```
Браузер ── HTTP ──▶ FastAPI (uvicorn, single-worker)
                      app.py      — create_app(): роутеры, статика, /api/health, init_db (lifespan)
                      config.py   — env: ADMIN_USER, ADMIN_PASSWORD_HASH, SECRET
                      db.py       — get_conn(), init_db()
                      register.py — POST /api/register
                      admin.py    — POST /api/admin/login; GET /api/admin/users[.csv]; require_admin
                    ▼
                  SQLite data/app.db (WAL), таблица users
```

Статика тем же сервисом: `/` → frontend/index.html; `/registered`,
`/admin-login`, `/admin-dashboard` → одноименные html; остальное — из frontend/ по пути.

## 3. API-контракты

Общие правила: Content-Type JSON (кроме CSV); ошибки — `{"ok": false, "error": "<сообщение>"}`;
401 тело — `{"ok": false}`. Точный формат валидационной ошибки — первая ошибка,
`"<поле-ру>: <причина>"`.

### 3.1 POST /api/register

- Request body (JSON, все поля обязательны):
  `{surname: string, name: string, patronymic: string, email: string, phone: string, password: string, password_confirm: string}`
- Порядок проверок (возвращается первая): все поля непусты → email содержит
  «@» и точку в домене → телефон ≥ 10 цифр → len(password) ≥ 8 →
  password == password_confirm → email отсутствует в users (SELECT).
- Ответы:
  - `200` → `{"ok": true}` — запись создана
  - `422` → `{"ok": false, "error": "<поле-ру>: <причина>"}` — запись НЕ создана
- Хранение: password → bcrypt-хэш cost 12 в password_hash; открытый пароль не сохраняется.

Валидация — хендлерная, НЕ Pydantic-required (MAJ-1, решение ПМ): поля модели
запроса объявляются с дефолтами (`str = ""`), обязательность каждого поля
проверяется в обработчике в фиксированном порядке (см. выше). Отсутствующий
ключ JSON при этом НЕ попадает под дефолтную Pydantic-валидацию (иначе
фронт получил бы `422 {detail:[...]}` вместо контрактного формата): он
обрабатывается так же, как пустое поле, — контрактный
`422 {"ok": false, "error": "<поле-ру>: поле обязательно"}`.

### 3.2 POST /api/admin/login

- Request body: `{login: string, password: string}`
- Проверка: login == ADMIN_USER (env) И bcrypt.checkpw(password, ADMIN_PASSWORD_HASH).
- Ответы:
  - `200` → `{"ok": true, "token": "<secrets.token_urlsafe(32)>"}`
  - `401` → `{"ok": false}`
- Токен хранится в памяти процесса `{token: expires}`, TTL 12 ч; после рестарта — пере-вход.

### 3.3 GET /api/admin/users

- Заголовок: `X-Admin-Token: <token>` (обязателен, см. 3.5).
- Ответы:
  - `200` → `{"count": N, "users": [{"id": int, "fio": string, "email": string, "phone": string, "created_at": string}]}`
  - `401` → `{"ok": false}` — токена нет/неверный/истек
- fio = `"{surname} {name} {patronymic}"`; сортировка `created_at DESC, id DESC`
  (свежие сверху; id — тай-брейк при совпадении created_at в одну секунду, MIN-3).

### 3.4 GET /api/admin/users/export.csv

- Заголовок: `X-Admin-Token: <token>`.
- Ответы:
  - `200` → `text/csv; charset=utf-8`, Content-Disposition: `attachment; filename="users.csv"`
  - `401` → `{"ok": false}`, пустое тело
- Формат: UTF-8 **с BOM** (EF BB BF), разделитель `;`, первая строка — заголовок:
  `ФИО;Email;Телефон;Роль;Дата регистрации`
- Роль — литерал `Ученик` у всех строк; Дата регистрации — `DD.MM.YYYY` из created_at.
- Дата регистрации выводится в локальном времени (UTC→локаль при выводе,
  MIN-4): `datetime('now')` в БД пишет UTC, export-функция пересчитывает в
  локальную зону перед форматированием `DD.MM.YYYY` (регистрация 00:30 МСК
  не должна попадать на предыдущий день).
- CSV-санитизация (MAJ-2, решение ПМ по мандату Заказчика «Реши как лучше»):
  значение ячейки из пользовательских полей (ФИО, email, телефон),
  начинающееся с `=`, `+`, `-`, `@`, получает префикс `'` (одинарная
  кавычка) — Excel/LibreOffice показывают строку, формула не исполняется.
  Санитизация — в export-функции, до записи в CSV.

### 3.5 Механизм авторизации админ-API

- Все методы 3.3–3.4 требуют валидный `X-Admin-Token`.
- Отсутствие заголовка, неизвестный токен, токен с истекшим TTL → `401`.
- Токен выдается ТОЛЬКО успешным `POST /api/admin/login` (FR-8).

### 3.6 GET /api/health

- Ответ: `200 {"ok": true}` (живость, без авторизации).

## 4. Модель данных

SQLite, файл `data/app.db` (в .gitignore), WAL. SQL — только параметризованные запросы (`?`-плейсхолдеры), конкатенация запрещена (NFR-2).

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

- Уникальность email — на уровне БД (UNIQUE) как вторая линия защиты после SELECT-проверки.
- В БД только хранение, без логики (паттерн 5 map.md).
- Логика CSV-роли «Ученик» — в коде, не в данных (инструкторы — следующий спринт).

## 5. Конфигурация и секреты (NFR-3)

- `.env` (в .gitignore): `ADMIN_USER`, `ADMIN_PASSWORD_HASH` (bcrypt-хэш, не открытый пароль), `SECRET`.
- `.env.example` — в репозитории, с инструкцией генерации:
  `python3 -c "import bcrypt; print(bcrypt.hashpw(b'пароль', bcrypt.gensalt()).decode())"`
- Отсутствие обязательной переменной в окружении — явная ошибка при старте/использовании, не тихий дефолт.

## 6. Решения по НФТ

| NFR | Решение | Контроль |
|---|---|---|
| NFR-1: ответ регистрации ≤ 500 мс | Локальный SQLite; bcrypt cost 12 ~250 мс — в бюджете | Тест замера времени POST /api/register |
| NFR-2: параметризованный SQL | Единый db-слой, только `?`-плейсхолдеры | Тест + ревью-запрет конкатенации |
| NFR-3: секреты в .env | .env в .gitignore, .env.example в репо | Проверка git-статуса |

## 7. Трассировка: FR/NFR → Requirement → Задача

| Требование | Requirement (домен) | Задача (tasks.md) |
|---|---|---|
| FR-1 | registration / Сохранение регистрации ученика | 1.2, 2.1 |
| FR-2 | registration / Отклонение некорректной регистрации | 2.1 |
| FR-3 | registration / Хранение пароля в виде bcrypt-хэша | 1.2, 2.1 |
| FR-4 | registration / Страница «Регистрация завершена» | 4.1, 4.2 |
| FR-5 | admin / Вход администратора | 3.1 |
| FR-6 | admin / Список зарегистрированных пользователей | 3.2 |
| FR-7 | admin / Выгрузка CSV | 3.3 |
| FR-8 | admin / Токен доступа к админ-API | 3.1, 3.2, 3.3 |
| FR-9 | registration / Соответствие утвержденным макетам | 4.1, 4.2 |
| NFR-1 | (сквозное) | 2.1, 5.1 |
| NFR-2 | (сквозное) | 1.2, 2.1, 5.1 |
| NFR-3 | (сквозное) | 1.1, 5.1 |

Правило полноты: нет Requirement без источника в ТЗ; нет Must-требования без Requirement (контракт 2/7).

## 8. Вне спринта (зафиксировано дизайном)

Личные кабинеты, инструкторы, восстановление пароля, email/SMS-подтверждение,
refresh-токены, nginx/TLS, контейнеры, оркестрация, деплой.

---

# SDD (дополнение): Авторизация и кабинет ученика (Спринт 1)

> Системный дизайн change `add-auth-cabinet`. Источник решений —
> requirements.md (УТВЕРЖДЕН, Спринт 1), research.md и design.md пакета
> openspec/changes/add-auth-cabinet/, утвержденный мокап
> design/mocks/cabinet-student.html. Спринт 0 не меняется: регистрация
> (§3.1), админ-контур (§3.2–3.5), схема users (§4) — как есть.

## 9. Компоненты (Спринт 1)

```
Браузер
  │  статика: / (модалка «Вход» m-login), /cabinet
  │  fetch JSON API, заголовок X-Session-Token
  ▼
FastAPI (uvicorn, single-worker)
  auth.py   — НОВЫЙ: POST /api/auth/login, POST /api/auth/logout,
              GET /api/auth/me; реестр сессий {token: (expires, user_id)} TTL 12ч;
              зависимость require_session
  app.py    — + роутер auth, + маршрут /cabinet (единственная правка
              существующего кода)
  register.py, admin.py, db.py, config.py — БЕЗ ИЗМЕНЕНИЙ
  ▼
SQLite data/app.db (WAL) — таблица users (как в §4)
```

- Авторизация — отдельный модуль `backend/auth.py` (ограничение ТЗ), не в
  register.py.
- Учетные данные: таблица users Спринта 0 — логин = email (UNIQUE), проверка
  пароля = `bcrypt.checkpw(password, password_hash)` (интерпретация FR-3,
  зафиксирована в proposal пакета).
- Сессии: in-memory `{token: (expires, user_id)}`, TTL 12 ч, single-worker —
  тот же механизм и те же документированные ограничения, что у admin-токена
  (§3.2); user_id в записи — источник данных GET /api/auth/me (§10.3).
- Фронт: `frontend/cabinet.html` — копия мокапа дословно + wiring;
  `frontend/index.html` — wiring модалки m-login; токен в sessionStorage,
  передача в заголовке `X-Session-Token` (единый паттерн с X-Admin-Token).

## 10. API-контракты (Спринт 1)

Общие правила §3 действуют. Единое сообщение об отказе входа (FR-2) —
одна константная строка для всех причин:

```
AUTH_FAIL_MESSAGE = "Неверный email или пароль"
```

### 10.1 POST /api/auth/login

- Request body (JSON): `{email: string, password: string}`
- Порядок проверки (хендлерная валидация как §3.1): оба поля непусты
  (пустое/отсутствующее поле → `422 {"ok": false, "error": "<поле-ру>: поле
  обязательно"}`) → SELECT по email → bcrypt.checkpw. Отсутствие записи и
  несовпадение хэша — одинаковый ответ (FR-2).
- Ответы:
  - `200` → `{"ok": true, "token": "<secrets.token_urlsafe(32)>"}`
  - `401` → `{"ok": false, "error": "Неверный email или пароль"}` — для
    неверного email, неверного пароля и отсутствующей учетной записи
  - `422` → `{"ok": false, "error": "<поле-ру>: поле обязательно"}`
- Пароль в логи не пишется (NFR-3). Для выравнивания времени ответа
  допускается фиктивная bcrypt-проверка при отсутствующей записи.
- Анти-брутфорс (решение Заказчика, вариант (б), MAJ-3): после превышения
  порога неудачных попыток подряд с одного IP — временная блокировка входа
  с нарастающей длительностью; заблокированный запрос возвращает тот же 401
  с единой строкой ошибки. Требования R-BF1…R-BF4 — design.md «Минимальная
  анти-брутфорс защита /api/auth/login»; сценарии — спека auth,
  Requirement «Ограничение попыток входа (анти-брутфорс)».

### 10.2 POST /api/auth/logout

- Заголовок: `X-Session-Token: <token>`.
- Ответы:
  - `200` → `{"ok": true}` — токен удален из реестра
  - `401` → `{"ok": false}` — токена нет/неверный/истек (аннулировать нечего)
- После любого ответа фронт очищает sessionStorage и делает редирект на `/`.

### 10.3 GET /api/auth/me

- Заголовок: `X-Session-Token: <token>` (обязателен; механизм аналогичен §3.5).
- Ответы:
  - `200` → `{"ok": true, "user": {"id": int, "surname": string, "name": string, "patronymic": string, "email": string}}`
  - `401` → `{"ok": false}` — токена нет/неверный/истек/аннулирован logout'ом
- Источник — запись users по id, привязанному к сессии; ФИО фронт собирает:
  uname = `"{surname} {name} {patronymic}"`, greet = `"Добро пожаловать, {name}!"`.

### 10.4 Статика Спринта 1

- `/cabinet` → `frontend/cabinet.html` (перенос
  design/mocks/cabinet-student.html дословно; wiring: /api/auth/me,
  401-редирект на вход, logout-редирект на `/`, подстановка ФИО; плитки и
  чат-бар — визуал-заглушки, FR-6).
- Модалка «Вход» (m-login) на `/`: сабмит → POST /api/auth/login; ok →
  sessionStorage + редирект `/cabinet`; 401 → единое сообщение под формой.
- Остальная статика — без изменений (§2).

## 11. Модель данных (Спринт 1)

Без изменений схемы: таблица `users` (§4) уже содержит email (UNIQUE) и
password_hash. Сессии — только в памяти процесса (не в БД). Новый SQL
домена — один параметризованный SELECT по email (NFR-2).

## 12. Решения по НФТ (Спринт 1)

| NFR | Решение | Контроль |
|---|---|---|
| NFR-1: ответ авторизации ≤ 500 мс | bcrypt cost 12 ~250 мс + SELECT по UNIQUE email — в бюджете | Тест замера времени POST /api/auth/login |
| NFR-2: параметризованный SQL | SELECT через db-слой с `?`-плейсхолдером | Тест + ревью auth.py |
| NFR-3: токены/секреты не в репо и логах | Токен — sessionStorage + память процесса; пароли не логируются; .env-механика §5 без изменений | Тест логов + проверка git-статуса |

## 13. Трассировка (Спринт 1)

| Требование | Requirement (домен) | Задача (tasks.md) |
|---|---|---|
| FR-1 | auth / Вход ученика | 1.1, 2.2 |
| FR-2 | auth / Единое сообщение об отказе входа + auth / Ограничение попыток входа (анти-брутфорс) | 1.1, 2.2 |
| FR-3 | auth / Хранение учетных данных | 1.1 |
| FR-4 | auth / Вход ученика (сценарий «После входа открыт кабинет») + cabinet / Доступ к кабинету | 2.1, 2.2, 3.1 |
| FR-5 | cabinet / Отображение ФИО ученика | 2.1 |
| FR-6 | cabinet / Чат-бар и плитки-сервисы как визуал-заглушки | 2.1 |
| FR-7 | cabinet / Доступ к кабинету по сессионному токену + auth / Сессии с ограниченным сроком действия | 1.1, 2.1 |
| FR-8 | auth / Выход ученика | 1.1, 2.1 |
| FR-9 | cabinet / Соответствие утвержденному мокапу кабинета | 2.1, 2.2 |
| NFR-1 | (сквозное) | 1.1, 4.1 |
| NFR-2 | (сквозное) | 1.1, 4.1 |
| NFR-3 | (сквозное) | 1.1, 4.1 |

Правило полноты: нет Requirement без источника в ТЗ; нет Must-требования
без Requirement (контракт 2/7).

## 14. Вне спринта 1 (зафиксировано)

Водители (вторая учетка — «Пока не трогай водил»), реальные сервисы за
плитками и работающий чат, восстановление/смена пароля, email-подтверждение,
refresh-токены, вход по телефону.
