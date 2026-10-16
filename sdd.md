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

---

# SDD (дополнение): Поток инструктора (Спринт 2, часть 1)

> Системный дизайн change `add-instructor-flow`. Источник решений —
> requirements-instructor-flow.md (УТВЕРЖДЕН, FR-10…FR-17 + FR-11.1,
> NFR-2…NFR-4), research.md и design.md пакета
> openspec/changes/add-instructor-flow/, мокапы design/mocks/
> landing-instructors.html, registration-instructor.html,
> dashboard-instructor.html (последний — вне объема, сохранен). Механики
> Спринтов 0–1 переиспользуются без изменения: регистрация (§3.1),
> админ-контур (§3.2–3.5), auth/сессии (§9–10). Спринты 0–1 не меняются.

## 15. API-контракты (Спринт 2, часть 1)

Общие правила §3 и §10 действуют: Content-Type JSON; ошибки
`{"ok": false, "error": "<сообщение>"}`; 401 тело — `{"ok": false}`;
хендлерная валидация (дефолты `str = ""` в моделях, первая ошибка в формате
`"<поле-ру>: <причина>"`, 422). Единое сообщение об отказе входа —
AUTH_FAIL_MESSAGE (§10.1), без изменений.

### 15.1 POST /api/instructors/apply (публичный)

- Request body (JSON):
  `{fio: string, phone: string, email: string, address: string,
  work_format: string ("own"|"sber"), plate: string, license_number: string,
  license_date: string, license_category: string, experience: string,
  password: string, password_confirm: string, consent: boolean}`
  (ФИО анкеты — одним полем; разбор на surname/name/patronymic — задача 1.1;
  фронт шлет ФИО одной строкой как в макете. consent — обязательный чекбокс
  согласия на обработку персональных данных, звездочка макета — FR-11.)
- Порядок проверок (возвращается первая; формат как §3.1):
  1) обязательные поля (отмеченные звездочкой макета + пароль + подтверждение):
     fio, phone, email, address, license_number, license_category, password,
     password_confirm, work_format;
  1a) consent == true (чекбокс обязателен по макету, FR-11; иначе 422
     «Согласие: поле обязательно»);
  2) формат email (как §3.1);
  3) телефон ≥ 10 цифр;
  4) пароль ≥ 8 символов;
  5) password == password_confirm;
  6) plate непуст при work_format='own' (поле макета «если свой»);
  7) license_date при заполнении — валидная дата (YYYY-MM-DD);
  8) email отсутствует в users (SELECT);
  9) email отсутствует в instructor_applications (SELECT) — единое сообщение
     «Email: уже зарегистрирован» на обоих шагах 8–9 (FR-16, допущение
     proposal: дубликат заявки на тот же email тоже отклоняется).
- Вторая линия защиты (шаги 8–9 не атомарны, uvicorn single-worker исполняет
  sync-хендлеры в threadpool — два параллельных сабмита одного email проходят
  SELECT до чужого INSERT): INSERT перехватывает sqlite3.IntegrityError от
  UNIQUE instructor_applications.email и возвращает ту же контрактную
  `422 {"ok": false, "error": "Email: уже зарегистрирован"}` — симметрично
  register.py:104 (механика users). Итог: ровно одна заявка на email.
- Ответы:
  - `200` → `{"ok": true}` — заявка создана (status='waiting')
  - `422` → `{"ok": false, "error": "<поле-ру>: <причина>"}` — заявка НЕ создана
- Хранение: password → bcrypt-хэш cost 12 в instructor_applications.password_hash;
  открытый пароль не сохраняется и не логируется (FR-11.1, NFR-3). Файл ВУ
  в контракте отсутствует (не загружается).
- NFR-2: оба SELECT и INSERT — параметризованные (`?`).

### 15.2 GET /api/admin/instructor-applications

- Заголовок: `X-Admin-Token: <token>` (механизм §3.5, без изменений).
- Ответы:
  - `200` → `{"count": N, "applications": [{"id": int, "surname": string,
    "name": string, "patronymic": string, "email": string, "phone": string,
    "address": string, "work_format": string, "plate": string,
    "license_number": string, "license_date": string,
    "license_category": string, "experience": string,
    "status": string, "review_comment": string,
    "created_at": string}]}`
  - `401` → `{"ok": false}`
- password_hash в ответ НЕ входит: ключ в списке/карточке заявки отсутствует
  (решение Заказчика 2026-10-12-hash-not-rendered — минимизация поверхности
  возражения архитектора по FR-14). Хэш ХРАНИТСЯ в заявке (FR-11.1: перенос
  в users при approve без повторного хэширования), но не выдается API:
  UI админки его не рендерит, ответ GET не логируется (NFR-3). Сортировка
  `created_at DESC, id DESC` (как §3.3).

### 15.3 POST /api/admin/instructor-applications/{id}/approve

- Заголовок: `X-Admin-Token` (§3.5).
- Поведение: заявка в статусе waiting → ОДНА транзакция (commit один,
  симметрично register.py; исключает waiting-заявку с существующим
  пользователем при падении между INSERT и UPDATE — иначе повторный approve
  давал бы 409 и операцию нельзя было бы завершить): INSERT INTO users
  (surname, name, patronymic, email, phone, password_hash — значение ИЗ
  ЗАЯВКИ, без повторного хэширования, FR-11.1; role='instructor'), user_id =
  cursor.lastrowid; UPDATE заявки → status='approved'.
- Ответы:
  - `200` → `{"ok": true, "user_id": <int>}`
  - `409` → `{"ok": false, "error": "Заявка уже одобрена"}` — статус не waiting
  - `409` → `{"ok": false, "error": "Email: уже зарегистрирован"}` — гонка
    дубля email (sqlite3.IntegrityError от UNIQUE users.email)
  - `404` → `{"ok": false, "error": "Заявка не найдена"}`
  - `401` → `{"ok": false}` — нет валидного админ-токена

### 15.4 POST /api/admin/instructor-applications/{id}/deny

- Заголовок: `X-Admin-Token` (§3.5).
- Request body: `{"comment": string}`.
- Guard статуса (симметрично §15.3): операция — только над заявкой waiting;
  approved → 409 `{"ok": false, "error": "Заявка уже одобрена"}` (иначе
  прямой POST с валидным токеном отклонял бы approved-заявку при живой
  записи users role='instructor' — рассинхрон); deny → 409 `{"ok": false,
  "error": "Заявка уже отклонена"}` (повтор не меняет сохраненную причину).
- Проверка: comment непуст (пустое/отсутствующее → 422
  `{"ok": false, "error": "Комментарий: поле обязательно"}`, FR-15).
- Поведение: UPDATE заявки → status='deny', review_comment=comment.
- Ответы:
  - `200` → `{"ok": true}`
  - `422` → `{"ok": false, "error": "Комментарий: поле обязательно"}`
  - `409` → `{"ok": false, "error": "Заявка уже одобрена" | "Заявка уже отклонена"}` — guard статуса
  - `404` → `{"ok": false, "error": "Заявка не найдена"}`
  - `401` → `{"ok": false}`

### 15.5 POST /api/auth/login — дополнение ответа (роутинг по статусу, FR-13)

Механизм §10.1 без изменений (валидация, bcrypt.checkpw, единое сообщение,
анти-брутфорс, TTL). Дополняется определение маршрута после входа:

- Успешная проверка против users:
  - `role='instructor'` → `200 {"ok": true, "token": "…", "route": "cabinet"}`
    (фронт → /instructor/cabinet-stub; сессия выдается как §10.1)
  - `role='student'` → `200 {"ok": true, "token": "…",
    "route": "student-cabinet"}` (фронт → /cabinet; регресс Спринта 1)
- Записи users НЕТ, но пароль совпал с password_hash заявки
  (SELECT instructor_applications по email; bcrypt-проверка против хэша
  заявки; фиктивная проверка при отсутствующей заявке — та же схема тайминга,
  что §10.1):
  - `status='waiting'` → `200 {"ok": true, "route": "pending"}` — БЕЗ токена
    (сессию выдавать нечего; FR-13: экран ожидания)
  - `status='deny'` → `200 {"ok": true, "route": "rejected",
    "reason": "<review_comment>"}` — БЕЗ токена (FR-13: экран отказа с
    причиной)
  - заявки нет → `401` единое сообщение (как §10.1)
- Неудачные попытки (против users и против заявок) учитываются анти-брутфорсом
  единообразно (учет по IP, R-BF1…R-BF4 — без изменений).
- Обратная совместимость: добавляется только ключ route/reason — существующий
  фронт Спринта 1 при отсутствии ключа продолжает вести на /cabinet (ключ
  route для учеников все равно приходит; behavior contract учеников не
  меняется).

### 15.6 Статика Спринта 2, часть 1

- `/instructors` → `frontend/instructors.html` (мокап
  landing-instructors.html дословно; wiring: CTA → /instructors/apply; FR-10).
- `/instructors/apply` → `frontend/instructor-apply.html` (мокап
  registration-instructor.html дословно; wiring: POST /api/instructors/apply;
  ok → /instructors/pending; 422 → сообщение; файл ВУ не отправляется; FR-11).
- `/instructors/pending` → `frontend/instructor-pending.html` («заявка на
  рассмотрении»; после сабмита анкеты И после waiting-входа; FR-12, FR-13).
- `/instructors/rejected` → `frontend/instructor-rejected.html` (причина —
  из ответа логина, sessionStorage; FR-13, FR-17: тон по мокапам, тексты
  согласуются при реализации — design check).
- `/instructor/cabinet-stub` → `frontend/instructor-cabinet-stub.html`
  (заглушка «кабинет скоро»; защита сессией как /cabinet: GET
  /api/auth/me, 401 → редирект на вход; FR-13). Функциональные элементы
  dashboard-макета отсутствуют (вне объема).
- Вход инструктора — существующая модалка m-login на `/`: сабмит →
  POST /api/auth/login; ok → разбор route (§15.5) и редирект; 401 → единое
  сообщение (без изменений).

## 16. Модель данных (Спринт 2, часть 1)

SQLite data/app.db (WAL), только параметризованные запросы (NFR-2). Схема —
в db.py (_SCHEMA), миграция idempotent (CREATE IF NOT EXISTS; ALTER с
проверкой существования колонки — унаследованные базы Спринтов 0–1
поднимаются без пересоздания).

```sql
-- users: + колонка роли (additive; дефолт покрывает существующих учеников)
-- ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'student';

CREATE TABLE IF NOT EXISTS instructor_applications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  surname TEXT NOT NULL,
  name TEXT NOT NULL,
  patronymic TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,             -- вторая линия защиты apply (FR-16)
  phone TEXT NOT NULL,
  address TEXT NOT NULL,
  work_format TEXT NOT NULL,              -- 'own' | 'sber'
  plate TEXT NOT NULL DEFAULT '',
  license_number TEXT NOT NULL,
  license_date TEXT NOT NULL DEFAULT '',
  license_category TEXT NOT NULL,
  experience TEXT NOT NULL DEFAULT '',
  password_hash TEXT NOT NULL,            -- bcrypt cost 12 (FR-11.1)
  status TEXT NOT NULL DEFAULT 'waiting', -- waiting | approved | deny (NFR-4)
  review_comment TEXT NOT NULL DEFAULT '',-- причина отказа (FR-15)
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

- users (§4) + role: 'student' (дефолт) | 'instructor' (ставится approve).
  users.email остается UNIQUE — вторая линия защиты (§4, FR-16).
- instructor_applications.email — UNIQUE: вторая линия защиты apply, симметрично
  users (MAJ-1 ревью): SELECT-проверки §15.1 (шаги 8–9) не атомарны, INSERT
  перехватывает sqlite3.IntegrityError и возвращает ту же 422
  «Email: уже зарегистрирован»; гонка параллельных сабмитов дает ровно одну
  заявку на email (детерминированный вход §15.5 — SELECT по email).
- approve копирует в users: surname, name, patronymic, email, phone из
  заявки + password_hash как есть + role='instructor' (FR-16, FR-11.1).
- password_hash хранится в instructor_applications (FR-11.1), но НЕ выдается
  API (§15.2): UI админки не рендерит, ответ GET не логируется (решение
  Заказчика 2026-10-12-hash-not-rendered, NFR-3).
- В БД только хранение, без логики (паттерн 5 map.md).

## 17. Решения по НФТ (Спринт 2, часть 1)

| NFR | Решение | Контроль |
|---|---|---|
| NFR-2: параметризованный SQL | Все новые запросы (§15.1–15.4, §15.5 SELECT заявок) — `?`-плейсхолдеры через db-слой | Тест + ревью новых модулей |
| NFR-3: пароли/секреты не в логах и репо | Открытый пароль — только в теле запроса apply и памяти bcrypt-хэширования; password_hash хранится в заявке (FR-11.1/FR-14), но НЕ выдается API (§15.2 — без ключа password_hash), UI админки не рендерит, ответ GET заявок не логируется (решение Заказчика 2026-10-12-hash-not-rendered); лог-вызовы в новых модулях не пишут учетные данные | Тест логов + проверка git-статуса |
| NFR-4: состав instructor_applications | Полные данные анкеты + status(waiting/approved/deny) + review_comment + created_at (§16) | Тест схемы |

## 18. Трассировка (Спринт 2, часть 1)

| Требование | Requirement (домен) | Задача (tasks.md) |
|---|---|---|
| FR-10 | instructor-application / Лендинг инструкторов по прямой ссылке | 4.1, 5.1 |
| FR-11 | instructor-application / Анкета заявки инструктора + instructor-application / Данные ВУ-файла не сохраняются | 1.1, 4.2 |
| FR-11.1 | instructor-application / Хранение пароля заявки только в виде bcrypt-хэша | 1.1, 2.1 |
| FR-12 | instructor-application / Сохранение заявки со статусом waiting | 1.1, 4.2, 4.3 |
| FR-13 | instructor-auth / Вход инструктора через общий механизм авторизации + instructor-auth / Роутинг после входа по статусу + instructor-auth / Заглушка кабинета инструктора | 3.1, 4.3, 4.4, 4.5 |
| FR-14 | admin-moderation / Раздел заявок инструкторов в админке | 2.1 |
| FR-15 | admin-moderation / Отклонение заявки с обязательным комментарием | 2.1 |
| FR-16 | admin-moderation / Одобрение заявки создает пользователя + admin-moderation / Созданный пользователь получает роль инструктора | 1.1 (email-проверка), 1.2, 2.1 |
| FR-17 | instructor-auth / Роутинг (экран отказа) + instructor-application / Сохранение заявки (экран ожидания); тон — design check | 4.3, 6.1 |
| NFR-2 | (сквозное) | 1.1, 2.1, 3.1, 6.1 |
| NFR-3 | (сквозное) | 1.1, 2.1, 3.1, 6.1 |
| NFR-4 | (сквозное) | 1.2, 6.1 |

Правило полноты: нет Requirement без источника в ТЗ; нет Must-требования
без Requirement (контракт 2/7).

## 19. Вне спринта 2, часть 1 (зафиксировано)

Кабинет инструктора (dashboard-instructor.html — следующий объем), загрузка
файла ВУ, вход водителей через футер лендинга, поток водителей, восстановление/
смена пароля, email/SMS-уведомления о статусе заявки.

---

# SDD (дополнение): Кабинет инструктора (Спринт 2, часть 2)

> Системный дизайн change `add-instructor-cabinet`. Источник решений —
> requirements-instructor-cabinet.md (УТВЕРЖДЕН, FR-18…FR-22, NFR-2/3),
> research.md и design.md пакета openspec/changes/add-instructor-cabinet/,
> утвержденный макет design/mocks/dashboard-instructor.html. Механики
> Спринтов 0–2.1 переиспользуются без изменения: сессии/require_session (§9),
> /api/auth/me (§10.3), logout (§10.2), route-механика (§15.5). Спринты 0–2.1
> не меняются (контракты не затронуты; схема БД не меняется).

## 20. API-контракты (Спринт 2, часть 2)

Общие правила §3/§10 действуют: Content-Type JSON; 401 тело —
`{"ok": false}`.

### 20.1 GET /api/instructor/dashboard

> Синхронизировано с реализацией (коммит 018baae, review-001-3.1 MAJ-1,
> арбитраж ПМ: реализация функционально корректна и безопасна; контракты
> приведены к коду). Модуль — `backend/dashboard.py`.

- Заголовок: `X-Session-Token: <token>` (механика require_session, §10.3;
  в реализации — auth._session_user_id, то же поведение 401; переход на
  публичный helper — доработка MIN-1 review-001-3.1).
- Порядок проверок:
  1) сессия отсутствует / неверна / истекла / аннулирована →
     `401 {"ok": false}`;
  2) SELECT users по user_id сессии (`?`-плейсхолдер) — записи нет →
     `401 {"ok": false}` (вырожденный случай);
  3) `role != 'instructor'` → `403 {"ok": false}` (сессия валидна, роль не
     та — FR-18; distinct от 401 «нет сессии»);
  4) ok → `200 {"ok": true, "instructor": {"surname": string,
     "name": string, "patronymic": string, "email": string}, "demo": true,
     "stats": [...], "schedule": {...}, "appointments": [...],
     "next_lesson": {...}, "vehicle": {...}, "operations": [...]}`.
- Ключ пользователя — `instructor` (не `user`); поля `id` в ответе нет —
  уникальный идентификатор учетки для кабинета — email (состав полей —
  как §10.3 без id; FR-20).
- `demo: true` + демо-данные макета константами модуля (_DEMO_STATS,
  _DEMO_SCHEDULE, _DEMO_APPOINTMENTS, _DEMO_NEXT_LESSON, _DEMO_VEHICLE,
  _DEMO_OPERATIONS): содержимое кабинета — демонстрационное («Все данные
  вымышлены», FR-19/FR-21); фронт рендерит статику мокапа и читает из
  ответа `instructor.*`, демо-блоки — полезная нагрузка будущих объемов.
  Реальные данные БД кабинету не выдаются (design.md, «Сознательные
  ограничения»).
- Назначение: единая точка данных + серверной проверки роли кабинета
  (FR-18, FR-20). Закрывает техдолг design.md add-instructor-flow (поток 4:
  «при реальном кабинете — обязательная серверная проверка роли
  (require_session + role)»).
- Контракт /api/auth/me (§10.3) НЕ меняется (без ключа role — нет регресса
  Спринтов 1–2.1).

### 20.2 Существующие контракты — без изменений

- POST /api/auth/login (§15.5): route='cabinet' для role='instructor' —
  как есть. Меняется только фронт-назначение (§22): route 'cabinet' →
  /instructor/dashboard.
- POST /api/auth/logout (§10.2): без изменений; фронт кабинета использует
  как есть (FR-22).

## 21. Компоненты (Спринт 2, часть 2)

```
Браузер
  │  статика: /instructor/dashboard
  │  fetch JSON API (X-Session-Token)
  ▼
FastAPI (uvicorn, single-worker)
  dashboard.py          — НОВЫЙ: GET /api/instructor/dashboard (§20.1)
  app.py                — + маршрут /instructor/dashboard, + include роутера
                          (единственная правка существующего бэка)
  auth.py, instructors.py, instructor_admin.py, register.py, admin.py,
  db.py, config.py — БЕЗ ИЗМЕНЕНИЙ
  ▼
SQLite data/app.db (WAL) — users (§4 + role §16): схема НЕ меняется
```

## 22. Статика Спринта 2, часть 2

- `/instructor/dashboard` → `frontend/instructor-dashboard.html` (мокап
  dashboard-instructor.html дословно; wiring: GET /api/instructor/dashboard
  до
  отрисовки — 401/403 → редирект `/` (к модалке входа); ФИО шапки =
  «{surname} {name} {patronymic}», инициалы аватара — первые буквы фамилии
  и имени (FR-20); сайдбар достраивается nav-кнопками по перечню FR-19 на
  готовых .nav-стилях и navTo мокапа (допущение proposal: в исходном HTML
  кнопки отсутствуют, стили/механика заданы); у разделов (кроме «Мой день»)
  пометка «демо» (FR-21); выход — элемент в «Профиль и документы» + прямая
  кнопка → POST /api/auth/logout → очистка sessionStorage → редирект `/`
  (FR-22); интерактив мокапа сохраняется; демо-строка «Инструктор ·
  Категория B» не подменяется (допущение proposal)).
- `frontend/index.html` — модалка входа: route 'cabinet' →
  /instructor/dashboard (было /instructor/cabinet-stub); остальные маршруты
  и тексты — без изменений.
- `/instructor/cabinet-stub` — остается страницей (спека instructor-auth
  Спринта 2.1 в силе).

## 23. Модель данных (Спринт 2, часть 2)

Без изменений: users (§4 + role §16) достаточна. Новый SQL домена — один
параметризованный SELECT users по id (§20.1, NFR-2). Демо-данные кабинета —
константы модуля backend/dashboard.py (§20.1), в БД не хранятся.

## 24. Решения по НФТ (Спринт 2, часть 2)

| NFR | Решение | Контроль |
|---|---|---|
| NFR-2: параметризованный SQL | Единственный новый запрос (§20.1 SELECT по id) — `?`-плейсхолдер через db-слой | Тест + grep-ревью backend/dashboard.py |
| NFR-3: токены/секреты не в логах | Токен — sessionStorage + память процесса (как Спринт 1); /api/instructor/dashboard не логирует заголовки и ответ; .env-механика §5 без изменений | Тест логов + проверка git-статуса |

## 25. Трассировка (Спринт 2, часть 2)

| Требование | Requirement (домен) | Задача (tasks.md) |
|---|---|---|
| FR-18 | instructor-dashboard / Доступ к кабинету инструктора | 1.1, 2.1, 3.1 |
| FR-19 | instructor-dashboard / Соответствие утвержденному макету кабинета | 2.1, 4.1 (design check) |
| FR-20 | instructor-dashboard / ФИО инструктора из учетной записи | 1.1, 2.1 |
| FR-21 | instructor-dashboard / Разделы сайдбара — визуальное переключение на демо-данных | 2.1, 4.1 (design check) |
| FR-22 | instructor-dashboard / Выход из кабинета | 2.1 |
| NFR-2 | (сквозное) | 1.1, 4.1 |
| NFR-3 | (сквозное) | 1.1, 4.1 |

Правило полноты: нет Requirement без источника в ТЗ; нет Must-требования
без Requirement (контракт 2/7).

## 26. Вне спринта 2, часть 2 (зафиксировано)

Реальное расписание, доходы/выплаты, ученики, материалы, автомобиль,
профиль-документы (разделы — демо-заглушки, FR-21), загрузка файлов,
реальная категория ВУ в шапке, refresh-токены, multi-worker сессии.

---

# SDD (дополнение): Трассировка (Спринт 3, Партия A)

> Источники: requirements-instructor-student-loop.md (УТВЕРЖДЕН,
> FR-23…FR-41, NFR-1…NFR-6), design.md пакета
> openspec/changes/add-instructor-student-loop/. Колонка тестов — по
> маппингу test-model/qa-auto-report-add-instructor-student-loop.md
> (backend-тесты test_s3_backend.py без TC-ID в docstring — трассировка
> post-hoc, §4 отчета; UI-тесты TC-UI-007…011 — плановая).

## 27. Трассировка (Спринт 3, Партия A)

| Требование | Реализация (файл / эндпоинт / функция) | Тесты |
|---|---|---|
| FR-23 | backend/instructors.py POST /api/instructors/apply, multipart (instructor_apply, _parse_request, _validate_experience_years — стаж ≥ 0, MAJ-3) + backend/uploads.py (save_image → data/uploads/license/) + backend/db.py (instructor_applications.license_photo_path/experience_years) + frontend/instructor-apply.html (multipart) | tests/test_s3_backend.py::test_apply_multipart_saves_license_image, ::test_apply_experience_years_validation_and_transfer |
| FR-24 | backend/instructor_admin.py GET /api/admin/instructor-applications/{id}/license-image (instructor_application_license_image; только X-Admin-Token) | tests/test_s3_backend.py::test_admin_card_and_license_image (без токена/неверный токен/ученическая сессия → 401) |
| FR-25 | backend/instructor_admin.py GET /api/admin/instructor-applications/{id} (instructor_application_card) + frontend/admin-dashboard.html (карточка по клику на строку) | tests/test_s3_backend.py::test_admin_card_and_license_image + tests/test_ui_playwright.py::test_admin_row_click_opens_card_and_loads_license_image (TC-UI-011) |
| FR-26 | backend/instructor_cars.py GET/POST /api/instructor/cars (list_cars, create_car; связь 1-ко-многим) + backend/db.py (instructor_cars) | tests/test_s3_backend.py::test_cars_crud_happy_path, ::test_cars_validation_422_per_field, ::test_cars_access_401_403, ::test_car_not_visible_to_other_instructor_and_foreign_404 |
| FR-27 | backend/instructor_cars.py POST/GET /api/instructor/cars/{id}/photo (upload_car_photo, get_car_photo — матрица 401/403/404) + backend/uploads.py | tests/test_s3_backend.py::test_car_photo_upload_and_owner_only |
| FR-28 | backend/instructor_cars.py PATCH/DELETE /api/instructor/cars/{id} (patch_car, delete_car — ОВ-3: car_id → NULL, связь сохраняется) + backend/student_requests.py PATCH /api/instructor/students/{id}/car (assign_student_car — перекрепление, MAJ-2) | tests/test_s3_backend.py::test_cars_crud_happy_path, ::test_car_delete_unbinds_student_keeps_link, ::test_car_not_visible_to_other_instructor_and_foreign_404, ::test_assign_student_car_rebind_and_guards |
| FR-29 | backend/instructor_availability.py PUT /api/instructor/availability (put_availability — полная замена, дедуп, в одной транзакции) + frontend/instructor-dashboard.html (сетка календаря) | tests/test_s3_backend.py::test_availability_save_and_readback, ::test_availability_full_replace_and_dedup, ::test_availability_validation_422 + tests/test_ui_playwright.py::test_instructor_calendar_slot_toggle_and_put_availability (TC-UI-008) |
| FR-30 | backend/instructor_availability.py GET /api/instructor/availability (get_availability) + PUT (восстановление графика) | tests/test_s3_backend.py::test_availability_save_and_readback, ::test_availability_access_401_403 |
| FR-31 | backend/student_marketplace.py GET /api/student/instructors + GET …/{id} (list_instructors, instructor_card — только одобренные) + frontend/instructor-choice.html («Выбор инструктора» из cabinet.html) | tests/test_s3_backend.py::test_marketplace_lists_only_approved, ::test_marketplace_access_401_403 |
| FR-32 | backend/student_marketplace.py (_parse_filters, _passes_filters — transmission/min_rating/min_experience/free_*) + фильтры frontend/instructor-choice.html | tests/test_s3_backend.py::test_marketplace_filters + tests/test_ui_playwright.py::test_student_choice_filters_narrow_and_apply_request (TC-UI-007) |
| FR-33 | Вне скоупа (точка расширения, design.md «Сознательные ограничения») — карточка/фильтры без гео | Ручная инспекция отсутствия карт-вызовов (QA-отчет §3 п.4); де-факто — TestClient без сети (::test_marketplace_filters) |
| FR-34 | backend/reviews.py POST /api/student/instructors/{id}/reviews (create_review — серверная проверка accepted-связи) | tests/test_s3_backend.py::test_review_happy_duplicate_and_validation, ::test_review_requires_accepted_link_server_side |
| FR-35 | backend/student_marketplace.py (_rating_aggregate — AVG/COUNT; has_reviews:false) в GET …/{id} | tests/test_s3_backend.py::test_marketplace_card_detail_and_aggregate, ::test_marketplace_lists_only_approved |
| FR-36 | backend/student_requests.py POST /api/student/requests (create_request — 409 дубликат, 404 неодобренный) + GET /api/instructor/requests + подача из UI | tests/test_s3_backend.py::test_request_submit_duplicate_parallel_and_repeat, ::test_active_request_unique_index_blocks_duplicate_at_db_level, ::test_request_to_unapproved_instructor_404 + tests/test_ui_playwright.py::test_student_choice_filters_narrow_and_apply_request (TC-UI-007) |
| FR-37 | backend/student_requests.py GET /api/instructor/requests (incoming_requests — только этому инструктору, ФИО/стаж/дата) | tests/test_s3_backend.py::test_instructor_sees_only_own_requests, ::test_instructor_requests_contract_shape |
| FR-38 | backend/student_requests.py GET /api/student/requests (my_requests — deny_comment виден) + POST …/{id}/deny (deny_request — comment обязателен, иначе 422) | tests/test_s3_backend.py::test_deny_requires_comment_and_visible_to_student, ::test_deny_and_accept_of_foreign_request_404_and_double_409 + tests/test_ui_playwright.py::test_instructor_requests_deny_locked_until_comment_accept_with_car (TC-UI-009) |
| FR-39 | backend/student_requests.py POST …/{id}/accept (accept_request — car_id, ОВ-1 авто-закрытие, ОВ-4: 0 авто → 409) | tests/test_s3_backend.py::test_live_request_flow_submit_accept_closes_others, ::test_accept_requires_car_zero_cars_409_foreign_car_422, ::test_accept_closes_other_active_requests_new_and_accepted, ::test_accept_401_403 + tests/test_ui_playwright.py::test_instructor_requests_deny_locked_until_comment_accept_with_car (TC-UI-009), ::test_instructor_accept_flow_real_backend |
| FR-40 | backend/instructor_summary.py GET /api/instructor/summary (instructor_summary — виджет students) | tests/test_s3_backend.py::test_summary_widgets, ::test_summary_access_401_403, ::test_car_delete_unbinds_student_keeps_link |
| FR-41 | backend/instructor_summary.py GET /api/instructor/summary (today_lessons — всегда [], честная заглушка) | tests/test_s3_backend.py::test_summary_widgets |
| NFR-1 | backend/uploads.py (uploads_dir — data/uploads/ вне frontend/, статикой не раздаются); выдача только через license-image (X-Admin-Token) и car photo (сессия владельца) | tests/test_s3_backend.py::test_license_image_direct_url_not_served, ::test_admin_card_and_license_image, ::test_car_photo_upload_and_owner_only |
| NFR-2 | backend/reviews.py create_review — параметризованный SELECT к student_requests при каждом POST | tests/test_s3_backend.py::test_review_requires_accepted_link_server_side |
| NFR-3 | Все новые модули (instructor_cars, instructor_availability, student_marketplace, reviews, student_requests, instructor_summary) — `?`-плейсхолдеры | tests/test_s3_backend.py::test_new_modules_no_sql_concatenation |
| NFR-4 | (сквозное) токены/заголовки/персональные данные не логируются — новые модули без логирования ответов | Прямых автотестов нет — контроль ручной (QA-отчет §3) |
| NFR-5 | backend/db.py — idempotent-миграции: instructor_cars (1-ко-многим), availability (интервалы, UNIQUE), reviews (UNIQUE пара), student_requests (3 статуса + deny_comment + car_id) | tests/test_s3_backend.py::test_migration_creates_new_tables, ::test_migration_is_idempotent, ::test_migration_of_legacy_db_without_new_columns, ::test_active_request_unique_index_blocks_duplicate_at_db_level, ::test_availability_full_replace_and_dedup |
| NFR-6 | backend/uploads.py (sniff_image — magic bytes JPEG/PNG; лимит 5 МБ до записи; содержимое не исполняется) | tests/test_s3_backend.py::test_apply_rejects_bad_file_type_and_size, ::test_car_photo_upload_and_owner_only (граница «ровно 5 МБ» — ручной шаг, QA-отчет §3 п.3) |

Правило полноты: нет Requirement без источника в ТЗ; нет Must-требования
без Requirement (контракт 2/7). FR-23…FR-41 и NFR-1…NFR-6 покрыты
полностью; известные ручные хвосты — QA-отчет §3 (визуальный рендер
календаря, граница 5 МБ, инспекция карт-вызовов, эксплуатационные
проверки стенда).

---

# SDD (дополнение): Трассировка (Спринт 4, Партия A)

> Источники: design.md пакета openspec/changes/add-instructor-student-loop/
> (сущности Спринта 3 — instructor_cars, reviews, student_requests — и их
> UI-связки; Блок 6, строка GET /api/student/requests с пометкой
> «дополнено Спринтом 4, согласовано») и согласованные Заказчиком мокапы
> design/mocks/{my-cars,my-requests,review-form}.html (задача 4.1,
> 2026-10-16; отклонения F2–F4/NIT-1 закрыты design-guard-строками в
> шапках страниц, итерация 2). Change: add-s3-frontend-links
> (ветка feature/s4-links). Пограничное решение по instructor_id —
> openspec/changes/add-instructor-student-loop/arch-review-s4.md,
> вердикт «ДОПУСТИТЬ» (2026-10-16). Колонка тестов: TC-UI-015…018 —
> tests/test_ui_playwright.py (docstring, плановая, живой сервер);
> TC-S3BE-040/041 — tests/test_s3_backend.py (docstring, правило 6).

## 28. Трассировка (Спринт 4, Партия A)

| Требование / сценарий | Реализация (файл / эндпоинт / функция) | Тесты |
|---|---|---|
| Сценарий «Мои автомобили» (сущность instructor_cars, UI-связка): список/добавление/PATCH/удаление авто с подтверждением — мокап design/mocks/my-cars.html | frontend/my-cars.html (CRUD-карточки против GET/POST/PATCH/DELETE /api/instructor/cars Спринта 3) + маршрут /my-cars → my-cars.html (backend/app.py _PAGE_ROUTES) + пункт навигации «Мои автомобили» в frontend/instructor-dashboard.html → /my-cars | tests/test_ui_playwright.py::test_s4_my_cars_add_edit_delete_car (TC-UI-015); tests/test_s3_backend.py::test_s4_static_routes_new_pages[/my-cars] (TC-S3BE-040), ::test_s4_pages_wired_to_real_api_shapes (TC-S3BE-041) |
| Сценарий «Фото автомобиля» (instructor_cars.photo): загрузка multipart с прогрессом, превью на карточке, выдача только по сессии владельца | frontend/my-cars.html (POST /api/instructor/cars/{id}/photo) + backend/instructor_cars.py upload_car_photo/get_car_photo (Спринт 3) | tests/test_ui_playwright.py::test_s4_my_cars_photo_upload_progress_and_preview (TC-UI-016) |
| Сценарий «Оставить отзыв» (сущность reviews, UI-связка): контекст инструктора, сабмит, повтор 409-блок — мокап design/mocks/review-form.html | frontend/review-form.html (POST /api/student/instructors/{id}/reviews Спринта 3) + маршрут /review → review-form.html (backend/app.py _PAGE_ROUTES) + связка frontend/my-requests.html → /review?instructor=<id> по instructor_id | tests/test_ui_playwright.py::test_s4_review_submit_then_repeat_blocked_409 (TC-UI-017); tests/test_s3_backend.py::test_s4_pages_wired_to_real_api_shapes (TC-S3BE-041) |
| Сценарий «Мои заявки» (сущность student_requests, UI-связка): бейджи статусов, deny_comment, «Повторить заявку» (ОВ-2), переход к отзыву — мокап design/mocks/my-requests.html | frontend/my-requests.html (GET/POST /api/student/requests Спринта 3) + маршрут /my-requests → my-requests.html (backend/app.py _PAGE_ROUTES) + переход из frontend/cabinet.html (плитка «Мои заявки» → /my-requests) | tests/test_ui_playwright.py::test_s4_my_requests_badges_deny_comment_retry_and_review_link (TC-UI-018); tests/test_s3_backend.py::test_s4_static_routes_new_pages[/my-requests] (TC-S3BE-040) |
| Пограничное дополнение контракта: instructor_id в ответе GET /api/student/requests (design.md, Блок 6 — пометка «дополнено Спринтом 4, согласовано»; arch-review-s4.md — ДОПУСТИТЬ: свои заявки ≠ раскрытие чужих данных, instructor_id нужен клиенту для «Повторить заявку» ОВ-2) | backend/student_requests.py my_requests (+4 строки: `"instructor_id": row["instructor_id"]` в элементе ответа; параметризованный SELECT, выборка только СВОИХ заявок по сессии) + frontend/my-requests.html (использование instructor_id для /review?instructor= и повтора) | tests/test_ui_playwright.py::test_s4_my_requests_badges_deny_comment_retry_and_review_link (TC-UI-018); tests/test_s3_backend.py::test_s4_pages_wired_to_real_api_shapes (TC-S3BE-041 — проверка «instructor_id:r.instructor_id» в my-requests.html) |
| Статические маршруты страниц-разделов отдаются бэкендом с маркерами заголовков | backend/app.py _PAGE_ROUTES: /my-cars → my-cars.html, /review → review-form.html, /my-requests → my-requests.html | tests/test_s3_backend.py::test_s4_static_routes_new_pages (TC-S3BE-040, параметризованный); ::test_s4_pages_tag_balance (sanity-баланс тегов 3 страниц, без TC-ID) |

Примечания:

1. Полное покрытие связки «страница ↔ реальный контракт» (без вымышленных
   путей) закреплено TC-S3BE-041: my-cars.html → api/instructor/cars (+фото),
   review-form.html → instructors/{id}/reviews, my-requests.html →
   api/student/requests + instructor_id.
2. Диапазон TC-UI-012…014 из task-постановки относится к итерации BUG-046
   change add-instructor-student-loop (Спринт 3: модалка действий админ-карточки
   и design-guard, tests/test_ui_playwright.py::test_admin_row_click… /
   TC-UI-013, TC-UI-014) — в Партию A Спринта 4 не входит; трассировка
   Партии A — TC-UI-015…018 и TC-S3BE-040/041 (сверено с приемкой:
   test-model/reviews/add-s3-frontend-links/review-acceptance.md).
3. Полнота: все артефакты Партии A (3 страницы + 3 маршрута + 3 навигационные
   связки + 1 пограничное дополнение контракта) имеют строки трассировки
   выше; ни одна строка не ссылается на отсутствующие файлы/тесты.
