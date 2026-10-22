# Design: add-instructor-student-loop

Источники решений: research.md (настоящий пакет), механики Спринтов 0–2.2
(require_session, X-Admin-Token, формат ошибок {ok:false}, параметризованный
SQL, idempotent-миграции db.py, статика тем же сервисом). Детальные
контракты — sdd.md, раздел «Спринт 3, Партия A» (§27+, дополняется задачей
приемки). Мокапы разделов — задача 3.3 (утвержденный макет обязателен для
фронтенд-задач).

## Правило префиксов API (закрывает MIN-3 arch-review add-instructor-cabinet)

| Префикс | Назначение | Доступ |
|---|---|---|
| /api/instructors/* | публичная анкета инструктора (существующий POST /api/instructors/apply) | гость; НЕ расширяется новыми кабинетными эндпоинтами |
| /api/instructor/* | кабинет инструктора | сессия (X-Session-Token) + role='instructor' |
| /api/student/* | кабинет ученика | сессия + role='student' |
| /api/admin/* | админ-API | X-Admin-Token (механика Спринта 0) |

Новые эндпоинты этого объема следуют правилу без исключений.

## Компоненты

```
Браузер
  │  статика: существующие /instructor/dashboard, /cabinet, /admin-dashboard
  │  (разделы достраиваются по мокапам задачи 3.3)
  │  fetch JSON API (X-Session-Token / X-Admin-Token)
  ▼
FastAPI (uvicorn, single-worker)
  ├── instructors.py         — РАСШИРЕНИЕ: POST /api/instructors/apply принимает
  │                            multipart с файлом ВУ (домен instructor-documents)
  ├── instructor_admin.py    — РАСШИРЕНИЕ: GET /api/admin/instructor-applications/{id}
  │                            (карточка) + GET …/{id}/license-image (изображение ВУ)
  ├── instructor_cars.py     — НОВЫЙ (домен instructor-cars):
  │                            GET/POST /api/instructor/cars,
  │                            PATCH/DELETE /api/instructor/cars/{id},
  │                            POST+GET /api/instructor/cars/{id}/photo
  ├── instructor_availability.py — НОВЫЙ (домен instructor-availability):
  │                            GET/PUT /api/instructor/availability
  ├── student_marketplace.py — НОВЫЙ (домен student-instructor-choice):
  │                            GET /api/student/instructors (фильтры),
  │                            GET /api/student/instructors/{id}
  ├── reviews.py             — НОВЫЙ (домен reviews):
  │                            POST /api/student/instructors/{id}/reviews
  ├── student_requests.py    — НОВЫЙ (домен student-requests):
  │                            POST/GET /api/student/requests,
  │                            GET /api/instructor/requests,
  │                            POST /api/instructor/requests/{id}/accept|deny,
  │                            PATCH /api/instructor/students/{id}/car
  │                            (перекрепление авто — ОВ-3)
  ├── instructor_summary.py  — НОВЫЙ (виджеты главной кабинета):
  │                            GET /api/instructor/summary
  ├── uploads.py             — НОВЫЙ helper (сохранение/выдача файлов:
  │                            валидация JPEG/PNG ≤5 МБ по содержимому,
  │                            data/uploads/{license,cars}/<uuid>.<ext>)
  ├── db.py                  — РАСШИРЕНИЕ: 4 таблицы + колонки
  │                            license_photo_path/experience_years
  │                            (instructor_applications) + experience_years
  │                            (users; перенос при approve) — миграции
  │                            idempotent, механика users.role
  ├── app.py                 — include роутеров (+ маршруты статики, если мокапы
  │                            задачи 3.3 потребуют отдельных страниц)
  ▼
SQLite data/app.db (WAL) + data/uploads/ (файлы; вне frontend/, статикой
не раздается — NFR-1)
```

## Модель данных (NFR-5; уровень сущностей — DDL уточняет dev в границах)

Существующие таблицы (idempotent-миграции — механика users.role Спринта 2):

- `instructor_applications` (§16): + `license_photo_path TEXT NULL`
  (NULL — заявка без ВУ); + `experience_years INTEGER NULL` — стаж анкеты,
  валидируется при подаче как целое ≥ 0 (закрытие MAJ-3 arch-review);
  NULL — анкеты старого формата. Свободный TEXT `experience` к фильтру
  «стаж ≥ N лет» непригоден и фильтром не используется.
- `users`: + `experience_years INTEGER NOT NULL DEFAULT 0` —
  материализованный стаж инструктора; единственный источник стажа для
  карточки (FR-31) и фильтра `min_experience` (FR-32). Переносится из
  `instructor_applications.experience_years` при approve: список
  копируемых полей переноса (sdd.md §16: surname, name, patronymic, email,
  phone, password_hash) расширяется на `experience_years` — версия
  архитектора (MAJ-3), принята. Анкеты до миграции дают стаж 0
  (DEFAULT); старый TEXT при approve не интерпретируется.

Новые таблицы:

- `instructor_cars` — автомобили; связь **один-ко-многим** к инструктору
  (у инструктора несколько авто, каждое принадлежит ровно одному):
  - `id` PK; `instructor_id` NOT NULL → users(id);
  - `brand` NOT NULL; `model` NOT NULL; `year` NOT NULL (целое в разумном
    диапазоне, валидация по полю); `plate` NOT NULL (госномер, непустой);
    `transmission` NOT NULL CHECK IN ('manual','automatic');
  - `photo_path` NULL (фото — через загрузку после создания, FR-27);
  - `created_at` NOT NULL; индекс по `instructor_id`.
- `availability` — рабочие интервалы недели, привязанные к инструктору:
  - `id` PK; `instructor_id` NOT NULL → users(id);
  - `weekday` NOT NULL CHECK 0..6 (0 = понедельник);
  - `start_time`, `end_time` NOT NULL (HH:MM; валидация start < end);
  - UNIQUE(instructor_id, weekday, start_time, end_time); индекс по
    instructor_id (фильтр «свободное время»).
- `reviews` — отзывы; **уникальная пара** ученик↔инструктор:
  - `id` PK; `instructor_id` NOT NULL → users(id); `student_id` NOT NULL →
    users(id); UNIQUE(instructor_id, student_id);
  - `rating` NOT NULL CHECK 1..5; `text` NOT NULL (непустой, ограничение
    длины — задача dev, ≤1000 знаков); `created_at` NOT NULL.
- `student_requests` — заявки учеников; статусы новая/принята/отказана:
  - `id` PK; `student_id` NOT NULL → users(id); `instructor_id` NOT NULL →
    users(id);
  - `status` NOT NULL CHECK IN ('new','accepted','denied'), DEFAULT 'new';
  - `deny_comment` NULL — **обязателен при 'denied'** (инвариант
    поддерживается кодом: переход в denied без непустого комментария
    невозможен; системный комментарий при автозакрытии — см. ниже);
  - `car_id` NULL → instructor_cars(id) — заполняется при принятии
    (выбор авто на шаге принятия); при удалении авто инструктором
    `car_id` → NULL, `status` остается 'accepted' (ОВ-3);
  - `created_at`, `decided_at` NULL; индексы по (instructor_id, status)
    и (student_id, status).

**Связь «ученик принят инструктором»** = наличие записи student_requests
со статусом 'accepted' (research.md §2; отдельная таблица не заводится).
Проверка отзыва (NFR-2), «Мои ученики» и виджет «Привязанные ученики»
читают эту связь; `car_id` — привязка ученика к автомобилю.

### Жизненный цикл student_requests (решения по ОВ)

```
            submit                accept (car_id)          deny (comment)
  (нет) ────────────▶ new ─────────────▶ accepted ◀──────────── (запрещен)
                       │  ▲                  │
                       │  └── повторная после отказа (ОВ-2, без троттлинга)
                       ▼
                     denied ◀── авто-закрытие при чужом accept (ОВ-1)
```

- Подача: ученик → одобренный инструктор. Активные статусы: new, accepted.
  Дубликат: повторный POST при активной заявке этому же инструктору → 409,
  записи нет (FR-36). Параллельные заявки разным инструкторам — допустимы
  (ОВ-1); повторная после отказа — допустима (ОВ-2).
- Принять: только инструктору-получателю, только из 'new'; требует `car_id`
  — автомобиль этого инструктора (422 при чужом/несуществующем); при 0
  автомобилей инструктора — 409 «заведите автомобиль» (ОВ-4). Побочный
  эффект (ОВ-1, доведен до буквы ТЗ по MAJ-1 arch-review): остальные
  АКТИВНЫЕ заявки этого ученика — и 'new', и 'accepted' → 'denied' с
  системным `deny_comment` = «Заявка закрыта: ученик принят другим
  инструктором» (три статуса NFR-5 сохранены; решение зафиксировано
  в proposal.md как допущение). Разрыв чужой accepted-связи использует
  ТОТ ЖЕ системный текст (решение по пограничному вопросу 1 ревью:
  смысл комментария для ученика идентичен, второй строки не заводим);
  уникальность связи «принят» восстановлена в любом порядке accept'ов.
- Отказать: только инструктору-получателю, только из 'new'; `comment`
  обязателен (пустой/отсутствующий → 422; действие заблокировано).
- Удаление автомобиля (ОВ-3): car_id привязанных заявок → NULL; связь
  «ученик↔инструктор» (статус accepted) сохраняется; инструктор
  перекрепляет авто вручную (механизм перекрепления — правка привязки в
  разделе «Мои ученики», минимально: выбор авто у принятого ученика).

## API-эндпоинты (методы / роли / валидации)

Формат ответов — механика Спринтов 1–2: 200 {ok:true, …}; ошибки
{ok:false, error:"<сообщение по-русски>"}; 401 — нет/неверная сессия
или админ-токен; 403 — сессия валидна, роль не та / нет прав на объект;
404 — объект не найден или чужой (не раскрываем существование);
409 — конфликт состояния; 422 — ошибка валидации полей.
SQL — только параметризованный (NFR-3); токены/заголовки не логируются
(NFR-4).

### Блок 1 — instructor-documents

| Метод и путь | Роль | Валидации / поведение |
|---|---|---|
| POST /api/instructors/apply (РАСШИРЕНИЕ, multipart) | гость | поля анкеты — как Спринт 2; `experience_years` (стаж): целое ≥ 0 → иначе 422, хранится в заявке и переносится в users.experience_years при approve (MAJ-3); `license_photo` (файл, при наличии): тип содержимого JPEG/PNG (проверка magic bytes, не только Content-Type), ≤5 МБ (ОВ-5) → иначе 422; сохранение в data/uploads/license/, заявка хранит license_photo_path (FR-23, NFR-6); отправка без файла — по обязательности макета (задача 3.3) |
| GET /api/admin/instructor-applications/{id} | админ-токен | полные данные заявки + факт/путь ВУ; 404 при отсутствии (FR-25) |
| GET /api/admin/instructor-applications/{id}/license-image | админ-токен | только валидный X-Admin-Token → изображение (Content-Type image/jpeg|image/png); без/с неверным токеном — 401, изображение не возвращается (FR-24, NFR-1); у заявки без ВУ — 404 |

### Блок 2 — instructor-cars

| Метод и путь | Роль | Валидации / поведение |
|---|---|---|
| GET /api/instructor/cars | сессия + instructor | список СВОИХ автомобилей (403 иной роли) |
| POST /api/instructor/cars | сессия + instructor | brand/model/plate непустые, year — число в диапазоне, transmission IN (manual, automatic) → иначе 422 по полю (FR-26) |
| PATCH /api/instructor/cars/{id} | сессия + instructor | только СВОЙ автомобиль (чужой/несуществующий → 404); валидации как POST (FR-28) |
| DELETE /api/instructor/cars/{id} | сессия + instructor | только СВОЙ (иначе 404); удаляет авто; привязки: car_id принятых заявок → NULL, связь с инструктором сохраняется (FR-28, ОВ-3) |
| POST /api/instructor/cars/{id}/photo | владелец | файл: JPEG/PNG (magic bytes), ≤5 МБ → иначе 422; привязка к авто (FR-27, NFR-6) |
| GET /api/instructor/cars/{id}/photo | владелец | матрица кодов (MIN-2 arch-review): гость/без сессии → 401; сессия чужой роли → 403; чужой или несуществующий автомобиль → 404 (не раскрываем существование); свой автомобиль без фото → 404 (NFR-1) |

### Блок 3 — instructor-availability

| Метод и путь | Роль | Валидации / поведение |
|---|---|---|
| GET /api/instructor/availability | сессия + instructor | интервалы текущего графика (FR-30) |
| PUT /api/instructor/availability | сессия + instructor | тело {intervals:[{weekday,start_time,end_time}]}; weekday 0..6, start<end, дубликаты схлопываются → иначе 422; **полная замена** графика инструктора в одной транзакции (FR-29, FR-30) |

### Блок 4 — student-instructor-choice

| Метод и путь | Роль | Валидации / поведение |
|---|---|---|
| GET /api/student/instructors | сессия + student | карточки ТОЛЬКО одобренных (role='instructor' в users — следствие approve, Спринт 2; waiting/deny в users отсутствуют); фильтры- query-параметры: `transmission` (manual/automatic), `min_rating` (0–5), `min_experience` (лет; по users.experience_years — MAJ-3), `free_weekday`+`free_from`+`free_to` (пересечение с availability); пустой результат — 200 с пустым списком (FR-31, FR-32) |
| GET /api/student/instructors/{id} | сессия + student | профиль карточки: ФИО, стаж, автомобили (марка/модель, год, КПП — без фото и госномера), агрегат рейтинга {average, count} или {has_reviews:false} (FR-35), часы работы; несуществующий/неодобренный → 404 |

Семантика `min_rating` при отсутствии отзывов (MIN-1 arch-review,
подтверждена рекомендация ревью): агрегат {has_reviews:false} фильтру
`min_rating > 0` НЕ удовлетворяет (инструктор без отзывов из выборки
выпадает); при `min_rating = 0` или без фильтра — присутствует. Рейтинг —
агрегат AVG/COUNT по reviews на лету, без денормализации (ADR-004 п.3).

### Блок 5 — reviews

| Метод и путь | Роль | Валидации / поведение |
|---|---|---|
| POST /api/student/instructors/{id}/reviews | сессия + student | СЕРВЕРНАЯ проверка: существует student_requests(student_id, instructor_id, status='accepted') → иначе 403, отзыв не создается (FR-34, NFR-2); rating int 1..5, text непустой ≤1000 → иначе 422; повторный отзыв (UNIQUE пара) → 409 (NFR-5) |

Выдача отзывов — в составе GET /api/student/instructors/{id} (агрегат;
перечень текстов отзывов карточке не обязателен — макет задачи 3.3
определяет; агрегат обязателен всегда).

### Блок 6 — student-requests

| Метод и путь | Роль | Валидации / поведение |
|---|---|---|
| POST /api/student/requests | сессия + student | {instructor_id}: цель — одобренный инструктор → иначе 404; активная (new/accepted) заявка этому инструктору → 409 без записи; new → создается (FR-36, ОВ-1, ОВ-2) |
| GET /api/student/requests | сессия + student | СВОИ заявки: статус, дата, инструктор, deny_comment (вкл. системный) (FR-38); ответ включает instructor_id СВОЕЙ заявки — дополнено Спринтом 4, согласовано (пограничный вердикт arch-review-s4: свои заявки ≠ раскрытие чужих данных; инструктор уже раскрыт по имени, id нужен клиенту для «Повторить заявку» ОВ-2) |
| GET /api/instructor/requests | сессия + instructor | заявки ТОЛЬКО этому инструктору: ученик (ФИО, стаж), дата, статус (FR-37) |
| POST /api/instructor/requests/{id}/accept | сессия + instructor | заявка — этому инструктору и в 'new' (иначе 404/409); {car_id}: авто этого инструктора → иначе 422; 0 авто → 409 «заведите автомобиль» (ОВ-4); эффект: статус → accepted, car_id проставлен; остальные АКТИВНЫЕ заявки ученика ('new' И 'accepted' — MAJ-1 arch-review, буква ОВ-1) → denied + системный комментарий (одинаковый для обоих исходов) (FR-39) |
| POST /api/instructor/requests/{id}/deny | сессия + instructor | заявка — этому инструктору и в 'new'; {comment} непустой → иначе 422, действие заблокировано (FR-38); эффект: status='denied', deny_comment=comment |
| PATCH /api/instructor/students/{id}/car | сессия + instructor | перекрепление авто принятого ученика (ОВ-3, MAJ-2 arch-review); {id} — id ученика с принятой заявкой ЭТОМУ инструктору (иначе 404 — не раскрываем); {car_id}: автомобиль этого инструктора → иначе 422; эффект: car_id принятой заявки обновлен; связь ученик↔инструктор не меняется (FR-28, ОВ-3) |
| GET /api/instructor/summary | сессия + instructor | виджеты главной: students (принятые: ФИО, авто, дата принятия), today_lessons — всегда [] (реального расписания нет) (FR-40, FR-41) |

## Безопасность файлов (NFR-1, NFR-6)

- Хранение: `data/uploads/license/<uuid>.<ext>`,
  `data/uploads/cars/<uuid>.<ext>`; имена генерирует сервер (оригинальные
  имена не используются в путях); каталог вне `frontend/` — статикой
  не раздается, прямой URL невозможен.
- Проверка содержимого: magic bytes (JPEG FF D8 FF / PNG 89 50 4E 47) +
  лимит 5 МБ ДО записи на диск; Content-Type клиента не доверенный.
- Выдача: только через эндпоинты с проверкой доступа:
  - изображение ВУ — только X-Admin-Token (никогда ученикам/гостям);
  - фото автомобиля — только владельцу по сессии; на публичной карточке —
    характеристики без фото (допущение proposal);
- Выданные ответы — с Content-Type image/*; содержимое не исполняется
  (не попадает в обрабатываемые сервером пути).

## Безопасность отзывов (NFR-2)

Проверка связи «принят» выполняется на сервере при каждом POST отзыва по
параметризованному SELECT к student_requests; UI-скрытие формы проверкой
не считается. Негативные пути (нет связи; прямой API-вызов мимо UI;
повторный отзыв) — покрыты сценариями specs/reviews/spec.md.

## Обработка ошибок (сводка)

| Ситуация | Ответ | Требование |
|---|---|---|
| Файл не JPEG/PNG или >5 МБ (ВУ, фото авто) | 422 {ok:false, error} | FR-23/27, NFR-6, ОВ-5 |
| Изображение ВУ без/с неверным X-Admin-Token | 401 {ok:false}, изображение не возвращается | FR-24, NFR-1 |
| Изображение ВУ по ученической сессии | 401/403 {ok:false} | NFR-1 |
| Кабинетные эндпоинты без сессии | 401 {ok:false} | FR-26+ |
| Кабинетные эндпоинты с чужой ролью | 403 {ok:false} | ролевая модель ТЗ |
| Чужой объект (авто, заявка) по id | 404 {ok:false} | FR-28/37/38 |
| Дубликат активной заявки | 409 {ok:false} | FR-36 |
| Принятие при 0 авто / чужой car_id | 409 / 422 {ok:false} | FR-39, ОВ-4 |
| Отказ без комментария | 422 {ok:false}, действие заблокировано | FR-38 |
| Отзыв без принятой заявки / повторный | 403 / 409 {ok:false} | FR-34, NFR-2/5 |
| Перекрепление: чужой/несуществующий car_id; ученик не принят этому инструктору | 422 / 404 {ok:false} | ОВ-3, MAJ-2 |
| Пустой результат фильтров каталога | 200 {ok:true, instructors:[]} | FR-32 |
| Виджет «Занятия на сегодня» | 200 {ok:true, today_lessons:[]} | FR-41 |

## Решения по НФТ

- NFR-1: см. «Безопасность файлов»; прямые URL исключены хранением вне
  раздаваемой статики.
- NFR-2: серверная проверка связи при создании отзыва (см. выше).
- NFR-3: все новые запросы — параметризованные (`?`-плейсхолдеры); конкатенация
  запрещена; контроль — задача приемки (grep нового кода).
- NFR-4: токены/заголовки/файлы не логируются; ответы с персональными
  данными (заявки, ФИО учеников) не логируются.
- NFR-5: модель данных — раздел «Модель данных» (1-ко-многим
  instructor_cars; availability — интервалы; reviews — UNIQUE пара;
  student_requests — три статуса + обязательный комментарий при отказе +
  car_id при принятии).
- NFR-6: тип/размер по содержимому до записи; содержимое не исполняется.

## Сознательные ограничения (задокументированы)

- Карта (FR-33) — точка расширения: карточка/фильтры не зависят от гео;
  добавление зоны — будущий change без переделки этого объема.
- Виджет «Занятия на сегодня» — всегда пустой список (заглушка честная:
  «Сегодня занятий нет», без фиктивных данных).
- Авто-закрытие заявок при чужом accept — статус denied + системный
  комментарий (компромисс зафиксирован в proposal.md; механика ОВ-1;
  охват — ВСЕ активные заявки, включая accepted — MAJ-1).
- Файлы-сироты в data/uploads/ (MIN-3 arch-review): DELETE автомобиля и
  обработка заявок (denied/авто-закрытие) НЕ удаляют файлы с диска —
  осознанный техдолг, cleanup вне скоупа этого объема; прямой угрозы нет
  (каталог не раздается статикой, URL недоступен).
- In-memory сессии/admin-токены, single-worker — наследованные ограничения
  Спринтов 0–1, не revisiting в этом объеме.

## Соответствие ADR-004 (архитектурные решения контура)

Ключевые решения дизайна следуют ADR-004 (Принято): (1) ФИО — гранулярные
поля в users, новые таблицы ФИО не дублируют, выдача JOIN/склейкой;
(2) файлы — data/uploads/{license,cars}/ вне frontend/, статикой не
раздаются, выдача только через авторизованные эндпоинты (админ-токен для
ВУ, сессия владельца для фото авто); (3) рейтинг — агрегат AVG/COUNT по
reviews на лету, колонки rating_avg в users нет (фильтр min_rating
вычисляет агрегат при чтении; семантика без отзывов — блок 4);
(4) связь «ученик принят» — статус заявки student_requests, отдельной
сущности нет. Отступлений от ADR-004 в этом пакете нет.
