# Design: add-instructor-flow

Источники решений: research.md (настоящий пакет), механики Спринтов 0–1
(backend/register.py — хендлерная валидация и bcrypt cost 12;
backend/auth.py — сессии {token: (expires, user_id)} TTL 12 ч, единое
сообщение об отказе, анти-брутфорс; backend/admin.py — X-Admin-Token).
Детальные контракты API — в `sdd.md` (раздел «Спринт 2, часть 1»).

## Компоненты

```
Браузер
  │  статика: /instructors, /instructors/apply, /instructors/pending,
  │  /instructors/rejected, /instructor/cabinet-stub
  │  fetch JSON API (X-Session-Token — только для cabinet-stub;
  │  X-Admin-Token — для модерации)
  ▼
FastAPI (uvicorn, single-worker)
  ├── instructors.py      — НОВЫЙ модуль (домен instructor-application):
  │                         POST /api/instructors/apply (публичный)
  ├── instructor_admin.py — НОВЫЙ модуль (домен admin-moderation):
  │                         GET /api/admin/instructor-applications,
  │                         POST /api/admin/instructor-applications/{id}/approve,
  │                         POST /api/admin/instructor-applications/{id}/deny
  ├── auth.py             — РАСШИРЕНИЕ (домен instructor-auth): ответ
  │                         /api/auth/login дополняется маршрутом по статусу
  │                         (cabinet/pending/rejected + причина)
  ├── register.py, admin.py, db.py, config.py — без изменений
  ▼
SQLite data/app.db (WAL) — users (+role) и instructor_applications
```

## Модель данных

```sql
-- изменение (additive, NULL/дефолт — существующие записи остаются учениками):
ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'student';

-- новое:
CREATE TABLE IF NOT EXISTS instructor_applications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  surname TEXT NOT NULL,          -- из поля ФИО анкеты (разбор: фамилия/имя/отчество)
  name TEXT NOT NULL,
  patronymic TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,     -- вторая линия защиты apply (см. ниже)
  phone TEXT NOT NULL,
  address TEXT NOT NULL,          -- адрес фактического проживания
  work_format TEXT NOT NULL,      -- 'own' | 'sber'
  plate TEXT NOT NULL DEFAULT '', -- госномер; обязателен только при work_format='own'
  license_number TEXT NOT NULL,   -- номер ВУ
  license_date TEXT NOT NULL DEFAULT '',  -- дата выдачи ВУ (необязательное поле макета)
  license_category TEXT NOT NULL, -- категория прав
  experience TEXT NOT NULL DEFAULT '',    -- стаж (необязательное поле макета)
  password_hash TEXT NOT NULL,    -- bcrypt cost 12, переносится в users при approve (FR-11.1)
  status TEXT NOT NULL DEFAULT 'waiting', -- waiting | approved | deny
  review_comment TEXT NOT NULL DEFAULT '',-- причина отказа (FR-15)
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

- Схема задается в db.py (_SCHEMA, CREATE/ALTER с проверкой существования —
  миграция idempotent для существующих баз Спринтов 0–1).
- users.email остается UNIQUE — вторая линия защиты после SELECT-проверки
  (та же механика register.py). Аналогично instructor_applications.email
  UNIQUE: INSERT заявки перехватывает sqlite3.IntegrityError и возвращает ту
  же контрактную 422 «Email: уже зарегистрирован» (симметрично
  register.py:104). Это закрывает гонку параллельных сабмитов одной анкеты
  (uvicorn single-worker исполняет sync-хендлеры в threadpool): оба проходят
  SELECT до чужого INSERT, но UNIQUE допускает ровно одну заявку на email.
- Пароль открытым видом не хранится нигде (FR-11.1, NFR-3); в API
  пароль/подтверждение не возвращаются никогда. password_hash хранится в
  заявке (FR-11.1, FR-14) и переносится в users при approve, но НЕ выдается
  ни одним API: GET /api/admin/instructor-applications отвечает без
  password_hash, UI админки его не рендерит, ответ не логируется
  (решение Заказчика 2026-10-12-hash-not-rendered).
- Роль в users: 'student' (дефолт) / 'instructor' (ставится при approve).
  Существующая регистрация учеников не меняется (дефолт покрывает).

## Потоки

### Поток 1: отправка анкеты (FR-10…FR-12, FR-11.1)

```
/instructors (мокап landing-instructors.html, CTA → /instructors/apply)
/instructors/apply → POST /api/instructors/apply
  хендлерная валидация (формат Спринта 0, 422 {"ok": false, "error": "<поле-ру>: …"}),
  порядок — первая ошибка:
    обязательные поля (по макету со звездочкой + пароль + подтверждение)
    → согласие на обработку персональных данных (чекбокс обязателен —
      звездочка макета, FR-11; без него 422 «Согласие: поле обязательно»)
    → формат email → телефон ≥ 10 цифр → пароль ≥ 8 → совпадение подтверждения
    → license_date: при заполнении — валидная дата
    → email не существует в users (SELECT)
    → email не существует в instructor_applications (SELECT, см. proposal)
  ok: bcrypt.hashpw(password, gensalt(rounds=12)) → INSERT instructor_applications
      (status='waiting', password_hash=хэш; открытый пароль не сохраняется);
      IntegrityError от UNIQUE instructor_applications.email (гонка параллельных
      сабмитов) → та же контрактная 422 «Email: уже зарегистрирован»
      (вторая линия защиты, механика register.py:104)
      → 200 {"ok": true} → фронт: редирект /instructors/pending
```

Загрузка файла ВУ — не реализуется (визуал макета; файл на сервер не
отправляется). Экран /instructors/pending — «заявка на рассмотрении».

### Поток 2: модерация (FR-14…FR-16)

```
Админка (существующий вход POST /api/admin/login, X-Admin-Token)
  → GET /api/admin/instructor-applications — все заявки, данные анкеты,
    сортировка created_at DESC, id DESC. Хранится в заявке (FR-11.1/FR-14),
    но в ответе НЕ возвращается: password_hash в списке/карточке отсутствует,
    UI админки его не рендерит, ответ GET не логируется
    (решение Заказчика 2026-10-12-hash-not-rendered).
  → клик по строке → «Одобрить»/«Отклонить»:
  approve: одна транзакция (commit один, симметрично register.py):
           INSERT INTO users (…, email, password_hash из заявки, role='instructor')
           [lastrowid — research.md §3] + UPDATE status='approved'; при падении
           между INSERT и UPDATE осталась бы waiting-заявка с существующим
           пользователем и повторный approve давал бы 409 — транзакция
           исключает рассинхрон.
           Гонки: users.email UNIQUE → sqlite3.IntegrityError → 409
           «Email: уже зарегистрирован»; повторный approve отсечен статусом
           approved (кнопка скрыта + проверка статуса на бэкенде).
  deny:    guard статуса — только waiting, иначе 409 (симметрично approve):
           approved → 409 «Заявка уже одобрена» (рассинхрон с записью users
           исключен), deny → 409 «Заявка уже отклонена» (повтор не меняет
           сохраненную причину).
           Комментарий обязателен (пустой → 422 "<поле-ру>: поле обязательно",
           кнопка подтверждения неактивна без текста); UPDATE status='deny',
           review_comment=комментарий
```

### Поток 3: вход инструктора и роутинг (FR-13)

```
/api/auth/login (существующий механизм: bcrypt.checkpw, единое сообщение,
анти-брутфорс — без изменений):
  SELECT users по email → нет записи ИЛИ пароль неверен → 401 единое сообщение
  (как у учеников; проверка заявки НЕ выполняется — отсутствие пользователя
  при верном пароле заявки является отдельным случаем, см. ниже)
  запись есть → сессия (как Спринт 1) → ответ дополняется полем маршрута:
    role='instructor' → {route: "cabinet"} → /instructor/cabinet-stub
    role='student'    → {route: "student-cabinet"} → /cabinet (без изменений)
  Особый случай: пароль совпал с password_hash заявки waiting/deny, но записи
  в users НЕТ → 401 НЕ возвращается (FR-13: waiting → экран ожидания,
  deny → экран отказа): SELECT instructor_applications по email →
    status='waiting' → 200 {ok, route: "pending"} (сессия НЕ выдается)
    status='deny'    → 200 {ok, route: "rejected", reason: review_comment}
    заявки нет       → 401 единое сообщение (как у учеников)
```

Порядок проверок сохраняет единообразие отказа: отсутствующая запись и
неверный пароль против users дополнительно проверяются против заявок, чтобы
waiting-инструктор видел экран ожидания; во всех остальных случаях отказа —
одна и та же строка 401 (анти-брутфорс и фиктивная bcrypt-проверка — без
изменений).

Статусные экраны /instructors/pending и /instructors/rejected доступны только
через редирект после успешной проверки логина/пароля в /api/auth/login
(причина отказа передается в ответе логина и хранится у фронта в
sessionStorage на время показа; прямой открытие страницы без данных логина —
без персональной причины). Заглушка /instructor/cabinet-stub защищена
сессией (как /cabinet ученика): без X-Session-Token — редирект на вход.

### Поток 4: заглушка кабинета

```
/instructor/cabinet-stub → frontend/instructor-cabinet-stub.html
  JS: GET /api/auth/me (X-Session-Token) → 401 → редирект на вход;
  200 → показ заглушки «кабинет скоро» (без функциональных элементов
  dashboard-макета — он вне объема).
```

Осознанное решение (техдолг за пределами объема): роль серверно НЕ
проверяется — роутинг по role только на фронте (§15.5), /api/auth/me
(§10.3) ключ role не возвращает, поэтому сессия ученика проходит 401-проверку
и на /instructor/cabinet-stub. Для заглушки без данных — приемлемо. При
реальном кабинете инструктора — обязательная серверная проверка роли
(require_session + role) и ключ role в /api/auth/me (зафиксировать в
architecture/map.md как техдолг).

## Обработка ошибок

| Ситуация | Ответ/поведение | Требование |
|---|---|---|
| Анкета: пустое обязательное поле / нет согласия / неверный email / телефон < 10 цифр / пароль < 8 / несовпадение подтверждения | 422 `{"ok": false, "error": "<поле-ру>: <причина>"}` (первая ошибка, хендлерная валидация) | FR-11 |
| Анкета: email уже в users ИЛИ уже в заявках (SELECT или IntegrityError от UNIQUE при гонке) | 422 `{"ok": false, "error": "Email: уже зарегистрирован"}` — единое сообщение | FR-16 |
| Модерация: нет/неверный/истекший X-Admin-Token | 401 `{"ok": false}` | FR-14 |
| deny без комментария | 422 `{"ok": false, "error": "Комментарий: поле обязательно"}`; кнопка неактивна | FR-15 |
| approve уже approved | 409 `{"ok": false, "error": "Заявка уже одобрена"}` | FR-16 |
| deny не-waiting (approved или deny) | 409 `{"ok": false, "error": "Заявка уже одобрена"}` / `{"ok": false, "error": "Заявка уже отклонена"}` — guard статуса, симметрично approve | FR-15, FR-16 |
| login: нет пользователя и нет заявки / неверный пароль пользователя | 401 единое сообщение (анти-брутфорс — без изменений) | FR-13 |
| cabinet-stub без сессии | редирект на вход | FR-13 |

## Решения по НФТ

- NFR-2 (параметризованный SQL): все новые запросы (INSERT заявки, SELECT
  заявок, UPDATE статусов, INSERT users при approve) — только `?`-плейсхолдеры
  через db-слой; конкатенация запрещена.
- NFR-3 (секреты/пароли не в логах и репозитории): открытый пароль существует
  только в теле запроса анкеты и в памяти процесса хэширования; не пишется в
  логи; password_hash возвращается только админ-API; .env-механика не меняется.
- NFR-4 (таблица instructor_applications): полные данные анкеты + статус
  waiting/approved/deny + review_comment + created_at — см. модель данных.

## Сознательные ограничения (задокументированы)

- Кабинет инструктора (dashboard) — заглушка; макет dashboard-instructor.html
  — следующий объем.
- Файл ВУ не сохраняется (визуал макета).
- Причина отказа на /instructors/rejected — из ответа логина (sessionStorage);
  повторное открытие страницы после закрытия вкладки требует повторного входа
  (тот же компромисс, что sessionStorage Спринта 1).
- Сессии/анти-брутфорс — in-memory, single-worker (наследованные ограничения
  Спринтов 0–1).
