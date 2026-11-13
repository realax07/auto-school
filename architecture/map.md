# Архитектурная карта — Auto School

> Паттерны, вокруг которых строится сервис. Источник — решения Заказчика
> (чат-лог 2026-10-06, дополняется). Уточнения и последствия фиксятся по мере
> проработки СА (sdd.md) и ревью архитектора.

## Архитектурные паттерны (решения Заказчика)

| # | Паттерн | Решение | Следствия / допущения (не проверено) |
|---|---|---|---|
| 1 | Веб-фронт | **Nginx + TLS по IP**, самоподписанный сертификат — Заказчик принимает риски | Нет домена/CA на старте; клиенты увидят warning браузера. Возможно появление домена позже |
| 2 | Фасад | **API Gateway** как единая точка входа для клиентов | Маршрутизация к сервисам, место для auth/лимитов; выбор реализации — на этапе СА |
| 3 | Декомпозиция | **Сервисы и модули независимые**, чем атомарнее тем лучше, но без фанатизма | Границы сервисов определяет СА на спеке; «без фанатизма» = не дробим ради дробления |
| 4 | Среда исполнения | **Сервисы в контейнерах** | Нужен docker/compose на целевой машине; деплой через образы |
| 5 | Разделение ответственности | **В БД только хранение данных, на фронте только визуальная логика** | Бизнес-логика — в сервисах; без хранимых процедур/логики в БД, без логики на клиенте |
| 6 | Состояние окружений | **У девопса своё состояние as is — после первого релиза** | До Релиза 1 окружение/инфраструктура в стадии становления; после Релиза 1 состояние инфры фиксируется как факт (RUNBOOK devops, актуальная конфигурация), без самодеятельных изменений |
| 7 | Взаимодействие | **Контракты на вызовы сервисов между собой** | Межсервисные вызовы только по зафиксированным контрактам (OpenAPI/аналог); изменение контракта = отдельная дельта спеки |
| 8 | — | Список будет дополняться Заказчиком | — |
| 9 | Языковой зонинг | Агентский слой (промпты, контракты, шаблоны, ворота) — EN; артефакты для человека и **сам сервис (UI/тексты/домен)** — RU (решение 2026-10-06, CONSTITUTION VIII) | Экономия ~41% токенов на промптах; сервис русскоязычный |
| 10 | Спринт-0 контур (CAD-001) | **FastAPI-сервис + статика тем же сервисом, SQLite WAL, bcrypt (cost 12), in-memory admin-токен, секреты в .env** — ADR-001 | Допущения не проверены на проде: bcrypt ~250 мс на целевой машине (контроль — тест замера), WAL покрывает конкурентность спринта-0, single-worker обязателен для in-memory токенов |
| 11 | Спринт-1 контур (CAD-002) | **Авторизация — отдельный модуль backend/auth.py (роуты /api/auth/*), одна таблица users (email UNIQUE + bcrypt), in-memory сессии {token: (expires, user_id)} TTL 12 ч, вход email-only** — ADR-002 | Тот же single-worker-инвариант (сессии учеников тоже в памяти); нет анти-брутфорса на публичном /api/auth/login — принятый техдолг; «отдельный сервис» = отдельная граница модуля, выделение в процесс — опция Релиза 1 |
| 12 | Спринт-2 контур, часть 1 (CAD-003) | **Поток инструктора: заявка (instructor_applications, bcrypt-хэш пароля в заявке) → модерация админом (approve переносит хэш в users) → вход через общий /api/auth/login; роли — флаг role в users ('student'/'instructor')** — ADR-003 | bcrypt-хэш хранится и в заявке, и в users (две копии до архивации заявок — решение Заказчика FR-11.1/FR-14); login при отсутствующей записи users делает bcrypt-проверку против хэша заявки (второй bcrypt-вызов в худшем пути); single-worker-инвариант без изменений |
| 13 | Спринт-2 контур, часть 2 (add-instructor-cabinet, arch-review approved-with-notes) | **Кабинет инструктора — демо-визуал по утвержденному макету; доступ — через новый защищенный эндпоинт GET /api/instructor/me (require_session + серверная проверка role='instructor', 403 при иной роли); содержимое — статика макета, из данных только ФИО/инициалы учетки; схема БД и существующие контракты не меняются** | Реального расписания/доходов/учеников нет — все цифры кабинета фиктивны (макет «Все данные вымышлены»); страница (HTML) по-прежнему доставляется всем — защита на уровне API + клиентский редирект (паттерн статики без сборки, спринт-1) |
| 14 | Спринт-3 контур, Партия A (add-instructor-student-loop; MAJ-1…3 закрыты в реализации) | **Контур «инструктор ↔ ученик»: профиль инструктора (авто 1-ко-многим instructor_cars + интервалы availability) → каталог одобренных для ученика (карточки + фильтры) → заявки student_requests (new/accepted/denied) → принять (с car_id) / отказать (обязательный комментарий) → отзывы reviews (UNIQUE пара, рейтинг агрегатом AVG/COUNT на лету); ФИО — только в users (JOIN по id, без дублирования); файлы — data/uploads/ вне статики, выдача авторизованными эндпоинтами (ВУ — X-Admin-Token, фото авто — владельцу)** — ADR-004 | Авто-закрытие заявок при чужом accept → denied + системный комментарий (допущение proposal; объем закрытия — MAJ-1 ревью); стаж для карточки/фильтра — MAJ-3 (материализация в схеме не завершена); правило префиксов /api/instructors|instructor|student|admin — закрытие MIN-3 ревью 2.2 |
| 15 | Спринт-5 контур (add-booking-docs; MAJ-1 закрыт Спринтом 10 — ADR-010) | **Бронирование ПОВЕРХ сущностей Спринта 3: таблица booking (student_id, instructor_id, availability_id — слот ЦЕЛИКОМ, ОВ-3; lesson_date материализован; статусы new/confirmed/rejected) с частичным UNIQUE-индексом по availability_id WHERE status IN ('new','confirmed') + BEGIN IMMEDIATE — «один слот = одна активная/подтвержденная бронь» гарантией хранилища (NFR-8), проигравший в гонке получает 409; ракурсы фото и СТС — kinds существующего uploads.py (car_photo/car_sts, механика magic bytes/5 МБ/uuid без изменений) + фиксированные колонки instructor_cars; комплектность фотонабора валидирует ЧЕЛОВЕК в админке (ОВ-1: completeness + block, флаг blocked); домены booking и «Мои документы» — отдельные модули booking.py/instructor_documents.py (директива Заказчика: существующие не раздувать); пара = student_requests.status='accepted' без новой сущности** — ADR-005 | Повторение слота по неделям/завершение занятия — точки расширения (слот с подтвержденной бронью закрыт в объеме); lesson_date не следует за заменой графика — взаимодействие PUT availability с активными бронями доопределяет СА (MAJ-1 ревью); блокировка авто необратима в объеме (разблокировка — точка расширения) |
| 16 | Спринт-6 контур (add-containerization; MAJ-1 закрыт — tests/ read-only mount) | **Контейнеризация сервисного контура: multi-stage Dockerfile (pinned python:3.12-slim, .venv из builder-этапа, non-root appuser, HEALTHCHECK по /api/health средствами python stdlib); compose-стек app + nginx (reverse proxy, TLS-файлы монтируются) + MinIO (контур под S3-адаптер uploads.py — задача 6.3); две сети (frontend nginx↔app, backend app↔MinIO), наружу только 80/443; named volumes db/uploads/minio-data; секреты — только env_file/монтирования вне образов (.dockerignore: .env*, deploy/tls/, data/); bare-metal systemd-режим сохраняется — переключение окружением без правок кода (env-изоляция config.py/db.py/uploads.py, FR-57); тесты — внутри того же образа (один digest), CI собирает образ и гоняет pytest на каждый PR** — ADR-006 | Механика доставки tests/ в контейнер (mount vs COPY) — MAJ-1 ревью; nginx в сети backend (лишняя достижимость MinIO) и процедура переключения режимов/переноса data/ в тома — MIN-1/MIN-2 ревью; dev-зависимости в прод-образе и root-обслуживание томов на хосте — принятый техдолг (ADR-006) |
| 17 | Спринт-8 контур (add-s8-cars-docs-booking, arch-review approve) | **Версии документов ВУ/СТС: таблица document_versions (target_type license/car_sts + target_id, status pending/verified/rejected; частичный UNIQUE по pending — одна ожидающая на документ, ОВ-7; CHECK — rejected только с причиной, ОВ-1); канонические колонки license_photo_path/photo_sts ОСТАЮТСЯ указателями файла действующей версии (все существующие потребители без переделки, NFR-23); seed-миграция verified v1 — idempotent, init_db через lifespan (NFR-24); асимметрия первичной загрузки — СТС у авто без СТС → verified v1 сразу (гейт человека Спринта 7), ВУ у анкеты без ВУ → pending; машины состояний документа и авто НЕЗАВИСИМЫ — замена СТС не сбрасывает validated (ОВ-6), правило MAJ-1 «validated → validating» — только 5 ракурсов; админ-верификация замен — X-Admin-Token, reject с обязательной причиной (ОВ-1), предпросмотр открывается (ОВ-4)** — ADR-007 | Файлы-сироты версий — расширение унаследованного техдолга; асимметрия первичной загрузки — особый случай эксплуатации (первичное СТС не в админской очереди); влияние статусов документов на активность инструктора — точка расширения (ОВ-3 «пока что»); атомарность «замещающая загрузка × verify/reject» — условный UPDATE/BEGIN IMMEDIATE + тесты (MIN-1 ревью); расхождение дословной цитаты п.6 с записью ОВ-6 — подтверждение ПМ/БА (MIN-4 ревью) |
| 18 | Спринт-9 контур, каркас Vue (add-vue-framework-pilot; MAJ-1…2 закрыты в реализации — пилот в проде) | **Миграция фронта на Vue 3 + Vite — ПОСТРАНИЧНО: страница = отдельная точка входа Vite и свой чанк (multi-entry MPA), SPA-монолит/vue-router/pinia запрещены (ОВ-3); workspace frontend/vue/, base /vue/, vendor-чанки по пакетам (runtime vue — свой чанк, вендор не инлайнится в страницы) + shared-чанк общего кода страниц; бюджеты NFR-26 — каждый vendor-чанк ≤150 КБ gzip, JS первого захода страницы ≤200 КБ gzip, проверка на артефактах dist на приемке каждого шага; мигрированная страница заменяет HTML-монолит ЦЕЛИКОМ (маршрут _PAGE_ROUTES отдаёт frontend/vue/dist, legacy-файл удаляется), план: С9 пилот /instructors/pending — ВЫПОЛНЕН (PR#107, 2026-11-04) → С11 статусные экраны/простые формы → далее лендинги/анкета/кабинеты (С10 занял календарь — ADR-010); доставка — node builder-этап в Dockerfile (pinned, наследование ADR-006), runtime забирает dist COPY --from, compose/nginx БЕЗ ИЗМЕНЕНИЙ (статика тем же сервисом — ADR-001), bare-metal FR-57 — npm ci && npm run build перед деплоем; критерий приема шага — полный e2e (49) зелеными без правок сценариев (NFR-27), прогон против собранного dist** — ADR-008 | Сборка перед e2e — новый обязательный шаг контура (забытая сборка = 404 мигрированного маршрута, красный прогон с ясной причиной); второй pinned образ node + удорожание docker build (npm ci); bare-metal требует Node.js на хосте сборки (MIN-1 ревью); app.py остается точкой статики и для собранных страниц (revisit — Релиз 1); дубли шапки/футера legacy×Vue до конца С10–С11 — временное состояние; контроль бюджетов ручной на приемке (CI-автоматизации нет); зависимость пилота от контракта add-application-status-polling — слияние на приемке 9.5 (MAJ-2 ревью) |
| 19 | Спринт-9 контур (add-personal-data-policy, arch-review approve) | **Домен PersonalData: текст политики — ЕДИНЫЙ заменяемый артефакт `deploy/policy/policy.md` (шапка policy-version/policy-date + plain-text; env POLICY_FILE; bind-mount :ro в backend-контур по механике nginx.conf/TLS — ADR-006; Dockerfile артефакт НЕ копирует) — подмена = замена файла на хосте (+ рестарт-страховка), чтение с диска на каждый запрос: ≤ 15 мин без разработчика/правки кода/пересборки (NFR-25); раздача — НОВЫЙ модуль backend/policy.py (единственный парсер read_policy): GET /api/policy публичный (механика /api/health) + страница /policy (оболочка policy.html в _PAGE_ROUTES, текст — fetch, рендер текстовыми узлами, в HTML/JS текста нет — grep-контроль); фиксация согласия: consent_at (UTC сервера) + consent_policy_version (из артефакта на момент сабмита, клиентской не доверять) в users и instructor_applications — 4 NULL-able колонки idempotent-миграцией _COLUMN_MIGRATIONS, легаси NULL без backfill; consent в /api/register — НОВОЕ обязательное поле (422, механика MIN-2 Спринта 3), в apply — проверка без изменений; битый артефакт → 500 {ok:false} и записи НЕ создаются (fail-closed, FR-79)** — ADR-009 | Битый/отсутствующий артефакт блокирует ОБЕ регистрации и /policy при зеленом /api/health (HEALTHCHECK артефакт не проверяет — техдолг спринта-9); текст версии не архивируется (consent_policy_version — ссылка на строку; после подмены текст прежней версии невосстановим — точка расширения при требовании аудита); повторное согласие/консент-журнал/PDF/футеры — точки расширения; строгость формата policy-date в парсере — MIN-3 ревью |
| 20 | Спринт-10 контур (add-calendar-weeks-availability, arch-review-002 approve — 2026-11-05) | **Календарь реальных недель (инструктор и ученик): модель слотов recurring/one_off на сущности availability — колонки slot_type/slot_date + CHECK-пара, UNIQUE расширен до (instructor_id, weekday, start_time, end_time, slot_date); легаси-строки → recurring через DEFAULT без перезаписи (FR-97) — guarded rebuild одной транзакцией с сохранением id/created_at (ссылки booking.availability_id валидны, FK нет), миграция idempotent по guard-колонке (NFR-30); экземпляр = (availability_id, дата), серии НЕ материализуются — инструктор разворачивает локально из полного GET (листание без сети, NFR-32), ученику экземпляры недели с состояниями free/busy/pending по (id, date) выдает сервер GET slots?date=; занятость/бронь/MAJ-1 — на уровне экземпляра (совпадение one_off с экземпляром серии = две строки допустимо, FR-90): частичный UNIQUE uq_booking_active_slot → (availability_id, lesson_date) WHERE active ВНУТРИ строки + КРОСС-СТРОЧНАЯ проверка экземпляра в create_booking внутри BEGIN IMMEDIATE (активная бронь любой покрывающей строки → 409; single-writer сериализует с PUT; точное совпадение интервалов), дедупликация instances в GET slots?date= (приоритет one_off, state агрегируется); PUT availability — дифф-запись (id строк сохраняются, booking.availability_id перепривязывается на строку-носитель при покрытой замене), lesson_date = точная дата экземпляра (POST bookings + опциональная date; легаси-вызов — ближайшая дата серии, MIN-1), 409 с перечнем, содержащим дату (закон MAJ-1 Спринта 5, перенос с интервала на экземпляры — FR-92); PUT/GET /api/instructor/availability расширяются обратно-совместимо (slot_type/date аддитивны, легаси-тело = recurring из тела + сохранение существующих one_off без изменений — MAJ-2; NFR-29, тесты s3/s7 без правок), новых роутеров/страниц нет; запрет правки прошлого (FR-93: правка ≥ начала слота) и бронирования прошедших/начавшихся (FR-96: строго >) — серверные проверки каждого PUT/POST (422), граница по началу слота, время — серверное МСК (наследование nowMoscow/MIN-1), клиентская блокировка — только UX; попап-редактор — оверлей НАД ячейкой поверх страницы, тип индивидуален ячейке, применяется по подтверждению в несохраненные правки (контур «Сохранить/Отменить» FR-68); реальный календарь — 7 дат от понедельника, подпись диапазона с обеими частями месяца/года, «сегодня» на реальной дате МСК; горизонт навигации ±12 месяцев — клиентский лимит; история состояний серий не хранится (факты истории — брони с lesson_date)** — ADR-010 | Риски ревью-001 сняты доработкой СА (f4a162b, arch-review-002 approve 2026-11-05): «один экземпляр — одна активная бронь» закреплена кросс-строчно (проверка create_booking в BEGIN IMMEDIATE + дедупликация slots?date=; ADR-010 «Уточнение»); семантика легаси-тела единая (recurring из тела + one_off сохраняются — MAJ-2); TZ=Europe/Moscow + МСК-хелпер закреплены в design/tasks (фактический контроль — задача 4.1); следствие Д8 зафиксировано в «Сознательные ограничения». Остаются: частичное пересечение интервалов разных строк одним экземпляром не считается (точное совпадение дата+start+end) — точка расширения, наследует техдолг спринта-5 «уникальность слота, а не даты»; MIN-5 ревью — свод устаревших формулировок дельты Спринта 8 СА ПРИ АРХИВАЦИИ 7→8→10 (proposal «Отслеживание»); карта данных — задача архитектора при приемке 10.3 |
| 21 | Спринт-15 контур (add-vue-s15-final-migration — ФИНАЛ миграции; arch-review approve-with-notes) | **Миграция ADR-008 ЗАВЕРШЕНА: последние 6 страниц (/cabinet, /instructor-choice, /admin-login, /admin-dashboard, /registered, /policy) — входы каркаса Vue, замена монолитов ЦЕЛИКОМ; каркас — 14 входов (8 + 6), бюджеты NFR-26 на ВСЕ page-чанки (пороги 150/200 КБ gzip без изменений); frontend/ БЕЗ легаси-HTML — 6 html-монолитов и каталог js/ (7 модулей) удалены ЦЕЛИКОМ, хендлер GET /js/{path} удален (потребителей нет); _PAGE_ROUTES — ТОЛЬКО значения «vue:» (13 маршрутов; /instructors/pending — вне карты), ассеты — /vue/assets тем же сервисом (ADR-001); дубли шапок/модалок легаси×Vue — временное состояние ADR-008 — исчезли; контракты /api/*, sessionStorage-ключи, хеш-навигация кабинета (#/my-requests, #/my-bookings), _PAGE_REDIRECTS, BUG-047 — без изменений; NFR-27 — e2e без правок сценариев (допустимый дифф — 4 переноса design-guard)** — ADR-008 (финал) | Verbatim-мокапы (FR-9 cabinet, BUG-046 admin) НЕ синхронизируются — перенос носителей чтения тестов на вход+App.vue+styles.css (прецедент С14); NFR-25 grep-контроль политики не расширяется на .vue (состояние с С9; оболочка без текста по построению); контроль бюджетов — ручной на приемке (наследование пилота); сборка dist перед pytest — обязательный шаг (наследование С12) |

Паттерны 1, 2 в спринте-0 не задействованы: nginx/TLS, gateway
**отложены Заказчиком** (решение 2026-10-06 — оба
вопроса решаются параллельно с первым этапом, когда поступит первое ТЗ на
сервис). Это отложенные, НЕ решенные вопросы (см. «Долг / открытые вопросы»).
Паттерн 4 (контейнеры) отложенного статуса больше не имеет: контур
контейнеризации реализуется Спринтом 6 (add-containerization, ADR-006) —
compose-режим встает рядом с действующим bare-metal systemd-деплоем.

## Контейнерный контур (Спринт 6, ADR-006; arch-review закрыт — MAJ-1/MIN устранены в реализации)

```
Клиент (браузер)
   │ HTTP → 443 (TLS self-signed, файлы хоста — монтирование, вне образов)
   ▼
nginx (контейнер, pinned образ; ports 80/443 — ЕДИНСТВЕННЫЕ публикуемые)
   │  сеть frontend (nginx ↔ app)
   ▼
app (образ из Dockerfile: pinned python:3.12-slim, multi-stage, non-root appuser)
   │  uvicorn backend.app:app --host 0.0.0.0 --port 8390 (single-worker —
   │  наследованный инвариант ADR-001/002); CMD, не entrypoint-скрипт
   │  HEALTHCHECK → GET /api/health (python stdlib; compose: depends_on
   │  nginx → app service_healthy); init_db через lifespan (FR-53, без новой
   │  механики); env_file .env (секреты вне образа и git — INC-006/NFR-3)
   │  named volume db     ← AUTOSCHOOL_DB_PATH=/data/db/app.db
   │  named volume uploads← AUTOSCHOOL_UPLOADS_DIR=/data/uploads
   │  bind (хост) deploy/policy → :ro POLICY_FILE=/app/deploy/policy/policy.md
   │  (Спринт-9, ADR-009: артефакт политики вне образа — подмена файла
   │  без пересборки; подмена = замена на хосте + рестарт, NFR-25)
   │  сеть backend (app ↔ MinIO)
   ▼
minio (pinned образ; S3-совместимое хранилище — контур под задачу 6.3)
   │  named volume minio-data; порты 9000/9001 НЕ публикуются
   ▼  (S3-адаптер uploads.py — отдельная дельта; файловый интерфейс
       изолирован: AUTOSCHOOL_UPLOADS_DIR — единственная точка путей)

Bare-metal режим (без изменений, FR-57): deploy/autoschool.service
(uvicorn 127.0.0.1:8390, .venv репо) + nginx хоста + data/ — продолжают
работать; переключение compose ↔ systemd — окружением, код один и тот же.
```

Тесты — внутри того же образа (один digest, pytest с временной БД /tmp вне
томов); CI — сборка образа + pytest в контейнере на каждый PR. Механика
MAJ-1 ЗАКРЫТА: tests/ доставляются read-only монтированием при прогоне
(scripts/container_test.sh: -v ./tests:/app/tests:ro).

## Компоненты (спринт-0 контур + спринт-1 auth//cabinet + спринт-2 поток инструктора + спринт-2.2 кабинет инструктора + спринт-3A контур инструктор↔ученик + спринт-5 бронирование и документы + спринт-8 версии документов + спринт-9 политика ПД, статус-опрос, Vue-пилот + спринт-10 календарь недель)

```
Клиент (браузер)
   │ HTTP (без TLS — спринт-0; TLS-стенд — см. deploy/)
   ▼
FastAPI-сервис (uvicorn, single-worker)          ← единственная точка входа
   ├── app.py      — create_app(): роутеры, статика, /api/health, init_db (lifespan)
   ├── config.py   — окружение: ADMIN_USER, ADMIN_PASSWORD_HASH, SECRET (из .env)
   ├── db.py       — SQLite data/app.db (WAL, Row), init_db(): таблицы users,
   │                 instructor_applications; миграция users.role (idempotent);
   │                 СПРИНТ-8 (ADR-007): таблица document_versions + seed
   │                 verified v1 из существующих license_photo_path/photo_sts
   │                 (idempotent, NFR-24); СПРИНТ-9 (ADR-009): +4 колонки
   │                 consent_at / consent_policy_version (users,
   │                 instructor_applications) — idempotent _COLUMN_MIGRATIONS,
   │                 легаси-строки NULL без seed/backfill;
   │                 СПРИНТ-10 (ADR-010): миграция availability —
   │                 slot_type/slot_date + CHECK, UNIQUE расширен до
   │                 (instructor_id, weekday, start_time, end_time, slot_date),
   │                 легаси-строки → recurring (guarded rebuild одной
   │                 транзакцией с сохранением id/created_at, idempotent NFR-30)
   ├── register.py — POST /api/register (валидация → bcrypt → INSERT);
   │                 СПРИНТ-9 (ADR-009): +обязательное поле consent
   │                 (bool=False, MAJ-1; позиция 1a → 422) + фиксация
   │                 consent_at/consent_policy_version при успехе
   ├── admin.py    — POST /api/admin/login; GET /api/admin/users[.csv]; require_admin
   │                 (in-memory реестр токенов {token: expires}, TTL 12 ч)
   ├── auth.py     — СПРИНТ-1 (ADR-002): POST /api/auth/login (SELECT по email
   │                 + bcrypt.checkpw, единое сообщение отказа), POST /api/auth/logout,
   │                 GET /api/auth/me; require_session; in-memory реестр
   │                 {token: (expires, user_id)}, TTL 12 ч; учетные данные —
   │                 таблица users; СПРИНТ-2 (ADR-003): ответ login дополняется
   │                 route/reason — роутинг по role (cabinet/student-cabinet)
   │                 и по статусу заявки без выдачи сессии (pending/rejected)
   ├── instructors.py     — СПРИНТ-2 (ADR-003): POST /api/instructors/apply
   │                        (публичная анкета: валидация → bcrypt → INSERT заявки);
   │                        СПРИНТ-9 (ADR-009): при успехе INSERT +
   │                        consent_at/consent_policy_version (проверка
   │                        consent — позиция 1a MIN-2, без изменений)
   ├── instructor_admin.py — СПРИНТ-2 (ADR-003): GET /api/admin/instructor-applications;
   │                        POST …/{id}/approve (INSERT users из заявки, перенос
   │                        хэша, role='instructor') и …/{id}/deny (обязательный
   │                        комментарий); require_admin
   ├── instructor_dashboard.py — СПРИНТ-2.2 (add-instructor-cabinet):
   │                        GET /api/instructor/me — require_session + SELECT
   │                        users по id + role='instructor' (403 при иной
   │                        роли) → {id, surname, name, patronymic, email};
   │                        серверная проверка роли кабинета (закрывает
   │                        техдолг 2.1)
   ├── dashboard.py        — СПРИНТ-2.2: GET /api/instructor/dashboard —
   │                        единая точка данных кабинета (та же серверная
   │                        проверка роли; демо-цифры заменяются реальными
   │                        по мере появления доменов)
   ├── guards.py           — СПРИНТ-3A: общий ролевой guard новых
   │                        кабинетных эндпоинтов (15+) — require_session
   │                        + SELECT users + проверка роли, 401/403;
   │                        вынесен в helper, auth.py/admin.py
   │                        не изменяются (задача 7.1)
   ├── uploads.py          — СПРИНТ-3A (add-instructor-student-loop): helper
   │                        файлов — magic bytes JPEG/PNG + ≤5 МБ до записи,
   │                        data/uploads/{license,cars}/<uuid>.<ext>;
   │                        СПРИНТ-5 (ADR-005): расширение перечня kinds —
   │                        car_photo (ракурсы) → data/uploads/car_photo/,
   │                        car_sts (СТС) → data/uploads/car_sts/, механика
   │                        без изменений
   ├── instructor_documents.py — СПРИНТ-5 (ADR-005, новый модуль): GET
   │                        /api/instructor/documents (ВУ из анкеты + СТС
   │                        всех своих авто — «Мои документы», FR-45) +
   │                        GET …/{doc_id}/file (просмотр/скачивание,
   │                        только владелец);
   │                        СПРИНТ-8 (ADR-007, РАСШИРЕНИЕ): таблица
   │                        document_versions и правила версий (действует —
   │                        последняя verified, pending одна, ОВ-7);
   │                        POST /api/instructor/documents/license
   │                        (загрузка/замена ВУ → pending, FR-71/72);
   │                        GET /api/instructor/documents — + версии/
   │                        статусы (active/pending/last_rejected, ОВ-1);
   │                        админ-контур: GET /api/admin/documents
   │                        ?status=pending (ВУ — ФИО, СТС — авто/госномер),
   │                        GET …/{version_id}/file (предпросмотр, ОВ-4),
   │                        POST …/verify (переключение канонической
   │                        колонки), POST …/reject (причина обязательна,
   │                        422 без нее — ОВ-1; не-pending → 409)
   ├── booking.py          — СПРИНТ-5 (ADR-005, новый модуль): GET
   │                        /api/student/instructors/{id}/slots (серверная
   │                        проверка пары — FR-46), POST/GET
   │                        /api/student/bookings, GET
   │                        /api/instructor/bookings, POST
   │                        …/{id}/confirm|reject (reject — комментарий
   │                        обязателен, ОВ-2); частичный UNIQUE +
   │                        BEGIN IMMEDIATE (NFR-8), занятый слот → 409;
   │                        СПРИНТ-10 (ADR-010, РАСШИРЕНИЕ): GET
   │                        slots?date= — экземпляры недели с состояниями
   │                        free/busy/pending + дедупликация (приоритет
   │                        one_off, state агрегируется); POST bookings
   │                        + опциональная date — lesson_date = точная
   │                        дата экземпляра (легаси-вызов — ближайшая
   │                        дата серии); UNIQUE → (availability_id,
   │                        lesson_date) + КРОСС-СТРОЧНАЯ проверка
   │                        экземпляра в BEGIN IMMEDIATE (409 с датой
   │                        в перечне — FR-92); бронирование только
   │                        будущих — строго > NOW МСК (FR-96/NFR-31)
   ├── instructors.py /    — СПРИНТ-3A РАСШИРЕНИЯ: apply принимает multipart
   │   instructor_admin.py   с ВУ; admin-API — карточка заявки +
   │                        GET …/{id}/license-image (только X-Admin-Token)
   ├── instructor_cars.py  — СПРИНТ-3A: GET/POST /api/instructor/cars,
   │                        PATCH/DELETE …/{id}, POST+GET …/{id}/photo
   │                        (владелец; ОВ-3: DELETE снимает car_id принятых
   │                        заявок, связь сохраняется);
   │                        СПРИНТ-5 (add-booking-docs, ADR-005): POST
   │                        /api/instructor/cars → multipart с обязательным
   │                        sts_photo (без СТС → 422, авто не создается);
   │                        POST+GET …/{id}/photo/{angle} (5 ракурсов,
   │                        владелец + ученики пары); GET …/{id}/sts
   │                        (только владелец); GET
   │                        /api/admin/cars/completeness + POST
   │                        /api/admin/cars/{id}/block (X-Admin-Token,
   │                        ОВ-1 — комплектность валидирует человек);
   │                        СПРИНТ-8 (ADR-007, sts-ветка): POST
   │                        …/{id}/photo/sts — первичная дозагрузка →
   │                        photo_sts + verified v1; ЗАМЕНА → pending-
   │                        версия документа, photo_sts не перезаписывается,
   │                        статус авто НЕ меняется (ОВ-6: validated
   │                        остается validated); ветки 5 ракурсов — без
   │                        изменений (MAJ-1: validated → validating)
   ├── instructor_availability.py — СПРИНТ-3A: GET/PUT
   │                        /api/instructor/availability; СПРИНТ-10
   │                        (ADR-010, РАСШИРЕНИЕ): слоты recurring/
   │                        one_off (slot_type/slot_date, аддитивно);
   │                        PUT — дифф-запись с сохранением id строк
   │                        и перепривязкой booking.availability_id
   │                        при покрытой замене носителя; легаси-тело =
   │                        recurring из тела + сохранение существующих
   │                        one_off (MAJ-2); запрет правки прошлого —
   │                        серверно (422, FR-93/NFR-31)
   ├── student_marketplace.py — СПРИНТ-3A: GET /api/student/instructors
   │                        (одобренные + фильтры КПП/рейтинг/стаж/время),
   │                        GET …/{id} (карточка: ФИО из users, авто без
   │                        фото/госномера, агрегат рейтинга, часы работы)
   ├── reviews.py          — СПРИНТ-3A: POST
   │                        /api/student/instructors/{id}/reviews — серверная
   │                        проверка связи accepted (NFR-2), UNIQUE пара
   ├── student_requests.py — СПРИНТ-3A: POST/GET /api/student/requests,
   │                        GET /api/instructor/requests, POST
   │                        …/{id}/accept|deny (accept: car_id своего авто,
   │                        0 авто → 409, авто-закрытие остальных активных
   │                        заявок ученика → denied + системный комментарий,
   │                        ОВ-1; deny: комментарий обязателен);
   │                        СПРИНТ-8 (РАСШИРЕНИЕ, ОВ-5): GET
   │                        /api/instructor/students — «Мои ученики»:
   │                        карточки пар accepted + next_lesson (ближайшая
   │                        confirmed ≥ сегодня, локальная дата сервера,
   │                        MIN-1) + счетчики planned/completed — ТОЛЬКО
   │                        confirmed (запросы new не участвуют); чтение
   │                        поверх booking/student_requests, новых
   │                        сущностей нет
   ├── instructor_summary.py — СПРИНТ-3A: GET /api/instructor/summary
   │                        («Привязанные ученики», today_lessons = [] —
   │                        честная заглушка FR-41); СПРИНТ-5: today_lessons
   │                        из реальных подтвержденных броней на текущую
   │                        дату (пусто → прежнее «Сегодня занятий нет»,
   │                        FR-49)
   ├── application_status.py — СПРИНТ-9 (add-application-status-polling,
   │                        НОВЫЙ МОДУЛЬ): до-сессионный контур заявителя
   │                        под /api/instructors/* (правило префиксов) —
   │                        GET application-status (X-Poll-Token —
   │                        многоразовый неперебираемый токен; ТОЛЬКО
   │                        чтение: одиночный параметризованный SELECT по
   │                        частичному UNIQUE, ≤5 запросов/мин — NFR-28;
   │                        внутренний deny → rejected) + POST
   │                        application-exchange (обмен токена на сессию
   │                        АТОМАРНО — условный UPDATE + rowcount;
   │                        потребленный/чужой токен → терминальный 404
   │                        без различения, MAJ-1 arch-review-002)
   ├── policy.py           — СПРИНТ-9 (ADR-009, НОВЫЙ МОДУЛЬ, домен
   │                        PersonalData): read_policy() — единственный
   │                        парсер артефакта deploy/policy/policy.md
   │                        (POLICY_FILE, чтение с диска на каждый запрос,
   │                        без кэша; шапка policy-version/policy-date до
   │                        '---' + plain-text; поврежден → ошибка без
   │                        раскрытия содержимого, NFR-10); GET /api/policy
   │                        — публичный (механика /api/health): 200
   │                        {ok:true, version, date, text} / 500 {ok:false};
   │                        хелпер версии для фиксации согласия
   │                        (register.py/instructors.py); артефакт недоступен
   │                        при сабмите → 500 и запись НЕ создается (FR-79)
   └── frontend/   — статика из design/mocks (/, /registered, /admin-login,
                     /admin-dashboard) + спринт-1: /cabinet → cabinet.html
                     (модалка «Вход» m-login на /, wiring: X-Session-Token
                     в sessionStorage, 401 → редирект на вход)
                     + спринт-2: /instructors (лендинг), /instructors/apply
                     (анкета), /instructors/pending, /instructors/rejected,
                     /instructor/cabinet-stub (сессия как /cabinet)
                     + спринт-2.2: /instructor/dashboard →
                     instructor-dashboard.html (кабинет по макету, демо-данные;
                     wiring: GET /api/instructor/me до отрисовки — 401/403 →
                     редирект на `/`; route='cabinet' логина ведет сюда,
                     было /instructor/cabinet-stub) — отдается
                     тем же сервисом (ADR-001)
                     + спринт-5: /instructor/documents → documents.html
                     («Мои документы»), /booking → booking.html (слоты +
                     запрос брони + календарь ученика),
                     /instructor/bookings → instructor-bookings.html
                     (запросы брони + календарь инструктора),
                     /admin/cars → admin-cars.html (комплектность +
                     блокировка) — дашборды не раздуваем, новые разделы
                     на новых страницах (ADR-005)
                     + спринт-9 (ADR-009): /policy → policy.html (политика
                     ПД — оболочка БЕЗ текста: текст и версия — fetch GET
                     /api/policy при загрузке, рендер текстовыми узлами)
                     + спринт-9 (ADR-008, ПИЛОТ VUE): /instructors/pending —
                     страница из frontend/vue/dist (multi-entry MPA,
                     бюджеты NFR-26; legacy HTML удален — маршрут _PAGE_ROUTES
                     отдаёт dist); статус-опрос 12с, обмен токена на сессию,
                     терминальный 404 (NFR-28)
                     + спринт-10 (ADR-010): календарь реальных недель в
                     /instructor/bookings и /booking — листание ‹ ›,
                     попап-редактор слота (разово/повторяющееся), у
                     инструктора разворот серий локально (без сети),
                     у ученика экземпляры free/busy/pending; запрет
                     прошлого на сервере
                     + спринт-3A: /instructor-choice (каталог одобренных),
                     /review-form (форма отзыва)
                     + СПРИНТ-11…15 (ADR-008, постранично; ФИНАЛ —
                     спринт-15): ВСЕ страницы — входы каркаса Vue из
                     frontend/vue/dist (14 входов; 13 маршрутов
                     _PAGE_ROUTES со значением «vue:» + пилотный
                     /instructors/pending вне карты); последние 6
                     legacy-монолитов (cabinet, instructor-choice,
                     admin-login, admin-dashboard, registered, policy)
                     и каталог frontend/js/ удалены ЦЕЛИКОМ, хендлер
                     GET /js/{path} удален (потребителей нет) — ассеты
                     страниц: статика /vue/assets тем же сервисом
                     (ADR-001); дубли шапок/модалок легаси×Vue исчезли
                     (техдолг ADR-008 закрыт); строки диаграммы выше
                     (спринт-0…3A: legacy-файлы booking/admin-cars/
                     кабинет-stub) — ИСТОРИЧЕСКИЕ носители (файлы
                     умерли в С5/С8/С13/С14)
   ▼
SQLite data/app.db (WAL, в .gitignore) — только хранение (паттерн 5);
учетные данные — таблица users (email UNIQUE + role), заявки инструкторов —
instructor_applications (email UNIQUE, password_hash, status), сессии — НЕ в БД
```

При Релизе 1 сервис встает за Nginx + Gateway (паттерны 1, 2); статика может
перейти под веб-сервер — API-контракты (sdd.md §3, OpenAPI) не меняются.

## Принятые решения (ADR)

| ADR | Решение | Статус |
|---|---|---|
| [001-add-registration-admin-stack](adr/001-add-registration-admin-stack.md) | Стек и контур спринта-0: FastAPI+SQLite WAL+bcrypt, статика тем же сервисом, in-memory admin-токен, .env-секреты | Принято (Заказчик, 2026-10-08) |
| [002-auth-service](adr/002-auth-service.md) | Авторизация учеников (Спринт 1): отдельный модуль-сервис backend/auth.py, одна таблица users (bcrypt), in-memory сессии TTL 12 ч, email-only логин (телефон — атрибут) | Принято (Заказчик, 2026-10-09; допущения подтверждены — 2294a4a) |
| [003-instructor-flow](adr/003-instructor-flow.md) | Поток инструктора (Спринт 2, часть 1): bcrypt-хэш пароля хранится в заявке, approve переносит его в users без повторного хэширования, вход — общий /api/auth/login, роли — флаг role в users | Принято (Заказчик, 2026-10-12; ревью — arch-review add-instructor-flow, changes-required: MAJ-1 UNIQUE email заявок) |
| [004-instructor-student-loop](adr/004-instructor-student-loop.md) | Контур «инструктор ↔ ученик» (Спринт 3, Партия A): ФИО — гранулярно в users, новые таблицы не дублируют; файлы — data/uploads/ вне статики, выдача только авторизованными эндпоинтами; рейтинг — агрегат AVG/COUNT на лету без денормализации; связь «принят» = статус accepted заявки | Принято (Заказчик — «Дефолты принимаю», 2026-10-15; ревью — arch-review add-instructor-student-loop, needs-rework: MAJ-1…3 — не касаются решений ADR) |
| [005-booking-slots](adr/005-booking-slots.md) | Бронирование и документы (Спринт 5): booking поверх availability (слот целиком) с частичным UNIQUE + BEGIN IMMEDIATE против гонок NFR-8; ракурсы фото/СТС — kinds uploads.py + фиксированные колонки instructor_cars; комплектность фотонабора валидирует человек в админке (флаг blocked); домены booking/«Мои документы» — отдельные модули по директиве Заказчика | Принято (Заказчик — дословная цитата ОВ-1…ОВ-6, 2026-10-22; ревью — arch-review add-booking-docs, needs-rework: MAJ-1 согласование PUT availability с бронями — не касается решений ADR) |
| [006-containerization](adr/006-containerization.md) | Контейнеризация (Спринт 6): multi-stage образ (pinned python:3.12-slim, .venv, non-root); compose app+nginx+MinIO, две сети, наружу только 80/443; состояние — named volumes (db/uploads/minio-data); секреты — env_file/монтирования вне образов (наследование NFR-3/INC-006); bare-metal systemd сохраняется — переключение окружением без правок кода (INC-001/FR-57); MinIO в стеке сразу, S3-адаптер uploads.py — задача 6.3 | Принято (Заказчик — «контейнеризация + модульный JS», 2026-10-23; решения-дефолты утверждены составом Спринта 6; ревью — arch-review add-containerization, needs-rework: MAJ-1 механика доставки тестов в контейнер — не касается решений ADR) |
| [007-document-versions](adr/007-document-versions.md) | Версии документов ВУ/СТС (Спринт 8): таблица document_versions pending/verified/rejected — частичный UNIQUE (одна ожидающая на документ, ОВ-7) и CHECK (rejected только с причиной, ОВ-1) на уровне схемы; канонические колонки license_photo_path/photo_sts остаются указателями действующей версии (потребители Спринтов 3–7 без переделки, NFR-23); seed-миграция verified v1, idempotent (NFR-24); асимметрия первичной загрузки — СТС → verified сразу (гейт Спринта 7), ВУ → pending; машины состояний документа и авто независимы — замена СТС не сбрасывает validated (ОВ-6), MAJ-1 — только 5 ракурсов | Принято (Заказчик — решения ОВ-1…ОВ-7, 2026-11-01; ревью — arch-review add-s8-cars-docs-booking, approve: MIN-1…MIN-4 — вне решений ADR) |
| [008-vue3-vite-migration](adr/008-vue3-vite-migration.md) | Миграция фронта на Vue 3 + Vite (Спринт 9, старт): multi-entry MPA — страница = отдельная точка входа, SPA-монолит и vue-router запрещены (ОВ-3); vendor-сплит библиотек отдельными чанками с бюджетами NFR-26 (150/200 КБ gzip, проверка на артефактах dist); постраничная замена HTML-монолитов ЦЕЛИКОМ, план Спринты 9–11 (С9 — пилот /instructors/pending, ОВ-4); доставка dist — node builder-этап Dockerfile (pinned), статика тем же сервисом (ADR-001), compose/nginx без изменений; критерий приема шага — 49 e2e зелеными без правок (NFR-27), прогон против собранного dist | Принято (Заказчик — ОВ-3/ОВ-4 дословно, telegram:144324141, 2026-11-02; ревью — arch-review add-vue-framework-pilot, доработка: MAJ-1…2 — не касаются решений ADR) |
| [009-policy-artifact-consent](adr/009-policy-artifact-consent.md) | Политика ПД (Спринт 9, ОВ-1/ОВ-2): текст — единый заменяемый артефакт deploy/policy/policy.md в контуре деплоя (шапка policy-version/policy-date + plain-text, POLICY_FILE, bind-mount :ro — механика ADR-006, в образ не входит; чтение на каждый запрос — подмена ≤ 15 мин без разработчика/пересборки, NFR-25); домен PersonalData — отдельный модуль backend/policy.py (парсер + публичный GET /api/policy + хелпер версии); страница /policy — оболочка без текста (fetch + текстовые узлы); фиксация согласия — consent_at + consent_policy_version (версия из артефакта на момент сабмита) в users/instructor_applications — 4 NULL-able колонки idempotent-миграцией, легаси NULL без backfill; consent в /api/register — обязательное поле (422, механика MIN-2 Спринта 3); битый артефакт → 500 и записи не создаются (fail-closed, FR-79) | Принято (Заказчик — «1 пиши стандартный пока, но держи его отдельно для замены. 2 да.», 2026-11-02; ревью — arch-review add-personal-data-policy, approve: MIN-1…MIN-5 — вне решений ADR) |
| [010-calendar-recurring-availability](adr/010-calendar-recurring-availability.md) | Календарь недель и типы слотов (Спринт 10, ОВ дословно telegram:144324141): тип слота — атрибут записи availability (slot_type/slot_date + CHECK, UNIQUE расширен до 5 колонок), легаси-строки → recurring через DEFAULT без перезаписи — guarded rebuild одной транзакцией (id/created_at сохранены, ссылки броней валидны), idempotent (NFR-30); экземпляр = (availability_id, дата), серии не материализуются — разворот при выдаче/рендере (инструктор локально, ученику сервер GET slots?date=); занятость/бронь/MAJ-1 — на уровне экземпляра: uq_booking_active_slot → (availability_id, lesson_date), lesson_date — точная дата экземпляра (POST + date, легаси — ближайшая), 409 с датой в перечне (усиление ADR-005/MAJ-1, не пересмотр); PUT/GET availability расширяются обратно-совместимо (легаси-тело = recurring, NFR-29), запрет прошлого — серверная валидация каждого PUT (422), бронирование только будущих — каждого POST (NFR-31) | Принято (Заказчик — дословная цитата 2026-11-04; ревью — arch-review add-calendar-weeks-availability, доработка: MAJ-1…2 — граница решений 3/4 ADR (политика совпадения one_off×серия, семантика легаси-тела), сами решения 1–5 в силе) |

## Долг / открытые вопросы

- [x] ~~Уточнить пункт 6~~ — «девопс»: состояние инфры as is фиксируется после Релиза 1 (RUNBOOK devops)
- [ ] Выбор реализации API Gateway (nginx-роутинг / отдельный сервис / готовый шлюз) — СА, Релиз 1. Решение Заказчика 2026-10-06: все три вопроса (gateway, схема БД, оркестрация) решаются параллельно с первым этапом, когда поступит первое ТЗ на сервис. **Статус: отложено Заказчиком, НЕ решено** (спринт-0 работает без gateway)
- [ ] БД: одна на сервис или общая (паттерн 3 намекает на свои данные у сервиса) — СА. **Статус: для спринта-0 де-факто решено** (SQLite у единственного сервиса, ADR-001), финальное решение по схеме БД для последующих сервисов — по-прежнему за первым ТЗ
- [ ] Оркестрация контейнеров (compose / systemd + docker) — devops, Релиз 1. **Статус: для сервисного контура де-факто решено Спринтом 6** (compose выбран — ADR-006, add-containerization; systemd-режим сохраняется, FR-57); оркестрация поверх compose (k8s/swarm) — по-прежнему вне скоупа

## Техдолг спринта-0 (принят осознанно, зафиксирован ADR-001 и дизайном)

- In-memory admin-токен: потеря при рестарте (пере-вход), только single-worker.
- Нет rate-limit/анти-брутфорса на /api/admin/login.
- Плейн HTTP без TLS (паттерн 1 отложен).
- CSV-роль «Ученик» — литерал в коде (колонки role в БД нет).
- CSV-инъекция (Excel-формулы из пользовательских полей) — решение Заказчика
  (санитизация или принятый риск), см. review-001-architecture MAJ-2.
- Времена UTC (datetime('now')) vs локальная дата в выдаче — см. review-001 MIN-4.

## Техдолг спринта-1 (принят осознанно, ADR-002 + arch-review add-auth-cabinet)

- In-memory сессии учеников: потеря при рестарте (пере-вход всех), тот же
  single-worker-инвариант, что у admin-токена.
- Нет rate-limit/анти-брутфорса на публичном /api/auth/login (MAJ-3
  arch-review; поверхность шире админской — вернуться при первых признаках
  перебора или в Релизе 1 за Gateway).
- Фиктивная bcrypt-проверка при отсутствующей записи (тайминг-выравнивание,
  MIN-1 arch-review) — обязательность подтверждается тестом на этапе реализации.
- /cabinet — статика: разметка доставляется всем, данные защищены через API
  (401 от /api/auth/me → редирект) — осознанный паттерн статики без сборки.

## Техдолг спринта-2, часть 1 (принят осознанно, ADR-003 + arch-review add-instructor-flow)

- bcrypt-хэш пароля в двух местах (заявка + users), хэш обработанных заявок
  не обнуляется (уснувший credential-материал) — решение Заказчика FR-11.1/FR-14;
  password_hash заявок выдается только админ-API, в UI не рендерится как
  обычное поле, в логи не пишется (MIN-5 arch-review).
- Роутинг ученик/инструктор — по role из ответа login на фронте; серверной
  проверки роли на /instructor/cabinet-stub нет (сессия есть — заглушка
  открывается, данных нет). При реальном кабинете инструктора — обязательная
  серверная проверка role (require_session + role) и role в /api/auth/me
  (MIN-4 arch-review). **Закрыто в 2.2 (add-instructor-cabinet): серверная
  проверка роли реализована эндпоинтом GET /api/instructor/me; ключ role в
  /api/auth/me признан избыточным — фронт различает роли по 403 от
  /api/instructor/me (см. arch-review add-instructor-cabinet §1.1).**
- deny без статусного guard на бэкенде (approved → deny через прямой API-вызов
  с админ-токеном возможен, рассинхрон с users) — MIN-1 arch-review.
- Статусные экраны /instructors/pending, /instructors/rejected —
  статика без защиты; причина отказа доставляется в ответе login и хранится
  в sessionStorage (повторное открытие после закрытия вкладки — повторный
  вход), тот же компромисс, что у /cabinet.
- deny-ветка login при нескольких заявках на один email недетерминирована —
  предотвращается UNIQUE instructor_applications.email (MAJ-1 arch-review,
  закрыть до разработки).

## Техдолг спринта-2, часть 2 (принят осознанно, add-instructor-cabinet + arch-review)

- /instructor/dashboard — статика без серверной защиты страницы: HTML
  доставляется всем, доступ контролируется на уровне API (GET
  /api/instructor/me — 401/403 → клиентский редирект на `/` до отрисовки);
  в разметке только демо-данные — тот же паттерн статики без сборки, что
  /cabinet (спринт-1).
- Демо-данные в статике кабинета: при будущих реальных объемах
  (расписание/доходы/ученики) весь демо-контент и пометки «демо» подлежат
  замене — контент лежит в HTML вперемешку с каркасом (наследие
  «дословность макета», FR-19).
- Двойной неймсейс API: /api/instructors/* (анкета, мн. число) и
  /api/instructor/me (кабинет, ед. число) — правило выбора префикса
  зафиксировать до следующих эндпоинтов кабинета (MIN-3 arch-review
  add-instructor-cabinet).
- /instructor/cabinet-stub остается страницей при недостижимости из флоу
  (route='cabinet' ведет на /instructor/dashboard) — удалить вместе с
  архивацией instructor-auth или оставить как техническую страницу
  (решение при архивации спринта 2.1).
- Главное демо-вид «Мой день» без пометки «демо» при реальном ФИО в шапке —
  MIN-1 arch-review add-instructor-cabinet (пометка или явное решение
  Заказчика — до/в задаче 2.1).

## Техдолг спринта-3, Партия A (контур инструктор↔ученик; MAJ-1…3 ЗАКРЫТЫ в реализации Спринта 3 — остались принятые миноры и точки расширения)

- MAJ ревью add-instructor-student-loop — ЗАКРЫТЫ в реализации: MAJ-1 —
  авто-закрытие охватывает ВСЕ активные заявки ученика (new и accepted)
  → denied + системный комментарий (ОВ-1); MAJ-2 — перекрепление авто
  принятого ученика — PATCH /api/instructor/cars/{id}; MAJ-3 — стаж
  материализован в профиле, фильтр min_experience и карточка работают.
  История формулировок:
- Файлы-сироты в data/uploads/ (DELETE авто / обработка заявок не удаляют
  файлы с диска) — принять как осознанный техдолг (MIN-3 ревью; cleanup
  вне объема).
- Семантика фильтра min_rating при отсутствии отзывов (MIN-1 ревью) и
  матрица кодов GET фото авто (MIN-2 ревью) — дофиксировать в design.md.
- answers-файл раунда ОВ-1…ОВ-6 (docs/ba/answers_roundN.md, контракт 1)
  отсутствует — БА дописать (MIN-4 ревью; решения процитированы в ТЗ).
- Наследуются без изменений: single-worker + in-memory сессии/токены
  (ADR-001/002), статика без серверной защиты страниц (спринт-1 паттерн),
  нет rate-limit на публичных эндпоинтах (публичная анкета теперь multipart
  с файлом — поверхность выросла; анти-брутфорс/лимиты — Релиз 1 за Gateway).

## Техдолг спринта-5 (контур бронирования и документы; MAJ-1 ЗАКРЫТ Спринтом 10 — согласование PUT×booking на уровне экземпляров, ADR-010)

- MAJ-1 ревью add-booking-docs — ЗАКРЫТ Спринтом 10 (ADR-010, доработка
  f4a162b): PUT availability — дифф-запись с перепривязкой
  booking.availability_id; 409 с перечнем, содержащим дату, на уровне
  ЭКЗЕМПЛЯРОВ (кросс-строчная проверка в BEGIN IMMEDIATE). История
  формулировок (стратегия «запрет 409 vs каскадный reject»):
- Minor ревью: MIN-1 — часовой пояс/правило даты для lesson_date и
  «Занятия на сегодня» (наследует MIN-4 review-001: UTC vs локальная дата);
  MIN-2 — blocked-автомобиль × отображение в существующих бронях; MIN-3 —
  пустое состояние «автомобиль» в календарях при car_id NULL (авто удален);
  MIN-4 — судьба устаревшего /photo-маршрута и photo_path Спринта 3.
- Слот с подтвержденной бронью закрыт навсегда в этом объеме (повторение
  по неделям/завершение занятия — точки расширения; уникальность слота,
  а не даты — по букве NFR-8/ОВ-4); блокировка авто необратима в объеме
  (разблокировка — точка расширения); колонка instructor_cars.photo_path
  устаревает без миграции данных (файлы-сироты — унаследованный техдолг
  MIN-3 ревью 3A).
- Наследуются без изменений: single-worker + in-memory сессии/токены
  (ADR-001/002), статика без серверной защиты страниц (спринт-1 паттерн),
  нет rate-limit на публичных эндпоинтах, файлы-сироты в data/uploads/
  (cleanup вне объема).

## Техдолг спринта-6 (контейнеризация; MAJ-1 ЗАКРЫТ в реализации — tests/ read-only mount, CI гоняет pytest в образе)

- MAJ-1 ревью add-containerization — ЗАКРЫТ: механизм доставки тестов —
  read-only mount при прогоне (scripts/container_test.sh:
  -v ./tests:/app/tests:ro; CI-джоб docker-build «Run backend tests
  inside the built image»). История формулировок:
- Minor ревью: MIN-1 — nginx подключен «к обеим» сетям вопреки диаграмме
  контура (лишняя достижимость MinIO из nginx; рекомендовано — только
  frontend); MIN-2 — процедура переключения режимов (конфликт портов 80/443/
  8390) и судьба существующей data/app.db при первом переходе bare-metal →
  compose не описаны в контракте README 2.1; MIN-3 — unhealthy-сценарий
  («процесс завершен аварийно» → контейнер exited, unhealthy недостижим;
  переформулировать на зависание); MIN-4 — параметры HEALTHCHECK
  (start_period на init_db) не зафиксированы.
- Принятый техдолг (ADR-006): dev-зависимости (pytest, httpx) в прод-образе —
  цена «одного digest»; файлы на named volumes принадлежат uid appuser —
  обслуживание тома на хосте требует root/docker; Docker HEALTHCHECK сам
  контейнер не рестартует (живость чинит restart: unless-stopped и nginx);
  теги вместо digest у базового образа и образов nginx/minio (NFR-12 «в
  идеале digest» — задача dev).
- Наследуются без изменений: single-worker + in-memory сессии/токены
  (ADR-001/002), статика тем же сервисом (ADR-001), SQLite WAL, нет
  rate-limit на публичных эндпоинтах, файлы-сироты в data/uploads/
  (cleanup вне объема), отсутствующие внешние ключи в схеме (фикс ревью 3A).

## Техдолг спринта-8 (документ-версии, «Мои ученики», календарь; arch-review add-s8-cars-docs-booking — approve, 2026-11-01)

- MIN-1 ревью: атомарность «замещающая загрузка × verify/reject» одной
  pending-строки document_versions — механизм (условный UPDATE … WHERE
  status='pending' / BEGIN IMMEDIATE, паттерн NFR-8) не назван в пакете;
  контроль — тесты задач 2.1/3.1/4.1.
- MIN-2 ревью: состав списка «Мои документы» после первичной загрузки ВУ
  (pending есть, active_version=null) — не pinned; контроль — задача 2.1.
- Файлы-сироты версий: замещение ожидающей версии (ОВ-7) и rejected-версии
  оставляют файлы в data/uploads/ без cleanup — расширение унаследованного
  техдолга MIN-3 ревью 3A (ADR-004); cleanup вне объема.
- MIN-4 ревью (вне пакета): расхождение дословной цитаты Заказчика п.6
  («Да, сбрасывает») с записью решения ОВ-6 («НЕ сбрасывает») в
  requirements-sprint8.md; пакет следует оперативной записи (не сбрасывать,
  ADR-007) — подтверждение ПМ/БА у Заказчика + правка транскрипции.
- Асимметрия первичной загрузки (ADR-007, решение 3): первичное СТС не
  попадает в админскую очередь «Документы» (verified v1 сразу) — особый
  случай для эксплуатации; «отозвать pending», история версий с архивом,
  пакетное подтверждение, влияние статусов на активность инструктора
  (ОВ-3 «пока что») — точки расширения.
- Наследуются без изменений: single-worker + in-memory сессии/токены
  (ADR-001/002), статика без серверной защиты страниц (спринт-1 паттерн),
  нет rate-limit на публичных эндпоинтах, файлы-сироты uploads (cleanup
  вне объема).

## Техдолг спринта-9 (каркас Vue и пилот; MAJ-1…2 ревью ЗАКРЫТЫ в реализации — пилот в проде, PR#107)

- MAJ-1 ревью: tests/test_instructor_pages.py (test_pending_page_exists_and_text,
  helper page(), строки 24/256–268) читает legacy instructor-pending.html
  напрямую — удаление файла (задача 2.3 пакета) ломает тест; правка теста
  в пакете не запланирована, утверждение design «ссылок на файл нет» не
  соответствует репо. Контроль — доработка tasks 2.3/design; в приемке
  разграничить: правка test_instructor_pages.py разрешена, «0 правок»
  NFR-27 касается только tests/test_ui_playwright.py.
- MAJ-2 ревью: зависимость пилота от add-application-status-polling
  декларирована по всем слоям, но предусловие старта 3.1 (контракт/design.md
  polling-пакета в дереве — пакета в openspec/changes/ пока нет) и условие
  сетевого смоука блока 2 (нужна серверная часть polling) не зафиксированы;
  точка слияния — приемка 9.5 (за ПМ).
- Сборка перед e2e — новый обязательный шаг контура (npm ci && npm run
  build → pytest); забытая сборка = 404 /instructors/pending и красный
  прогон (принято осознанно, ADR-008 «Последствия»).
- Bare-metal FR-57: сборка фронта требует Node.js на хосте деплоя — новый
  prerequisite, отражение в deploy-доке не названо (MIN-1 ревью; контроль —
  задача 2.2 пакета).
- Контроль бюджетов NFR-26 — ручной на приемке (задача 4.1 пакета),
  CI-автоматизации нет (принято, ADR-008).
- Дубли шапки/футера и стилей: legacy-монолиты × Vue-компоненты до
  завершения миграции С10–С11 — временное состояние постраничной миграции
  (ADR-008); статические экраны спринта-2/паттерн 13 устаревают по мере
  миграции — пересмотр карты на приемках шагов (ВЫПОЛНЕН: строка 21 карты
  + диаграмма «Компоненты», финал С15 — легаси-монолитов и каталога js/
  больше нет, все маршруты «vue:»).
- Наследуются без изменений: single-worker + in-memory сессии/токены
  (ADR-001/002), статика тем же сервисом (ADR-001 — теперь и для
  собранных страниц), нет rate-limit на публичных эндпоинтах (опрос
  NFR-28 — read-only SELECT, ≤5 запросов/мин с экрана, остановка при
  уходе, таймер не переживает страницу).

## Техдолг спринта-9 (политика ПД; arch-review add-personal-data-policy — approve, 2026-11-03)
- MIN-1 ревью: артефакт политики — Tier-1 зависимость эксплуатации: битый/
  отсутствующий deploy/policy/policy.md блокирует ОБЕ регистрации и /policy
  (500 {ok:false}) при ЗЕЛЕНОМ /api/health — HEALTHCHECK артефакт не
  проверяет; периодического контроля нет. Контроль — RUNBOOK (задача 6.1):
  операция «Подмена политики» обязана заканчиваться проверкой GET /api/policy;
  проверка артефакта в health — точка расширения (вне объема).
- MIN-2 ревью: consent_policy_version — ссылка на строку без архива текста:
  после подмены артефакта текст прежней версии невосстановим, «на что
  согласился» владелец легаси-записи прошлой версии — только строка версии.
  Принято сознательно (design «Сознательные ограничения»); архив текстов
  версий — точка расширения при появлении требования аудита 152-ФЗ.
- MIN-3 ревью: строгость парсера к policy-date не pinned (перечень
  «поврежденного» артефакта в design не включает неверный формат даты;
  дата объявлена документальной) — закрепить правило в границах задачи 2.1
  (рекомендация: version непустая обязателен, date — наличие обязателен,
  формат документальный) + тесты парсера.
- MIN-4 ревью: права на bind-mount для non-root appuser (:ro — чтение
  хостовых файлов чужого uid): дефолтные 644/755 работают, ограничительный
  umask на хосте молча дает 500 на все чтения артефакта. Контроль — RUNBOOK
  (задача 6.1): права доступа — шаг операции подмены.
- MIN-5 ревью (нарезка, ПМ): формулировка задачи 8.1 («финальная сборка:
  include роутера…, миграция…») читается как правка app.py/db.py, тогда как
  раздел «Рекомендации к нарезке» отдаёт эти файлы задачам 2.1/3.1, а 8.1 —
  «только сверяет»; задачи последовательны (зависимость 8.1 от 2.1/3.1/4.1),
  коллизии worktree нет — свести формулировку 8.1 к «сверка» во избежание
  дубль-правок.
- Наследуются без изменений: single-worker + in-memory сессии/токены
  (ADR-001/002), статика тем же сервисом (ADR-001), SQLite WAL, нет
  rate-limit на публичных эндпоинтах (теперь и на GET /api/policy — полный
  текст на каждый запрос; чтение десятков КБ — незначительная нагрузка),
  файлы-сироты uploads (cleanup вне объема). Отсутствие rate-limit на
  /api/policy — то же принятое решение, что и для остальных публичных
  эндпоинтов (Релиз 1 за Gateway).

## Техдолг спринта-10 (календарь недель; arch-review-002 approve — ре-ревью доработки f4a162b, 2026-11-05)

- MAJ-1 ревью — ЗАКРЫТО доработкой (f4a162b): политика закреплена ОДНА —
  обе строки допустимы (FR-90), «один экземпляр — одна активная бронь»
  кросс-строчно: проверка активных броней ВСЕХ покрывающих строк в
  create_booking внутри BEGIN IMMEDIATE (409) + дедупликация instances
  slots?date= (приоритет one_off, state агрегируется); частичный индекс —
  гарантия внутри строки; PUT — дифф с сохранением id строк и
  перепривязкой booking.availability_id при покрытой замене носителя
  (без нее бронь-сирота выпадала бы из проверки); тесты 2.1/3.1
  (TC-S10BE-004/006), сценарий в specs/booking, ADR-010 «Уточнение».
- MAJ-2 ревью — ЗАКРЫТО доработкой (f4a162b): семантика легаси-тела
  ЕДИНАЯ — recurring из тела + ВСЕ существующие one_off сохраняются без
  изменений (прошедшие и будущие, research R7); правило запрета прошлого
  (б) — только для тел нового формата; сценарий specs/instructor-availability,
  тест 3.1 и таблица ошибок сведены.
- MIN-1 ревью — ЗАКРЫТО: единая граница «прошедший = начало < NOW»
  (инструктор правит ≥ NOW, ученик бронирует строго > NOW) — design
  PUT/клиентский контракт/таблица ошибок; тесты границы 2.1/3.1, приемка 7.1.
- MIN-2 ревью — ЗАКРЫТО в design/tasks: NOW одним МСК-хелпером (не наивный
  now()/today()), TZ=Europe/Moscow в образе/compose, тесты с фиктивным NOW;
  фактический контроль контейнера — задача 4.1 (стенд: date = МСК).
- MIN-3 ревью — ЗАКРЫТО: следствие Д8 зафиксировано в design «Сознательные
  ограничения» (время прошедших броней — JOIN к ТЕКУЩЕЙ строке; заморозка
  start/end и убранная строка-носитель — точки расширения).
- MIN-4 ревью — ЗАКРЫТО: некорректный ?date= (не ISO/несуществующая) → 422
  до приведения (design «Обработка ошибок», TC-S10BE-007).
- MIN-5 ревью — ОТКРЫТО ДО АРХИВАЦИИ (СА): дельта Спринта 8 (ADDED FR-74)
  пакетом С10 не поглощается — после архивации 7→8→10 унесет в master
  устаревшее «контракты booking/availability не меняются»; свод при
  архивации, обязанность зафиксирована в proposal «Отслеживание»/«Impact».
- Горизонт навигации ±12 месяцев — клиентский лимит без серверного
  (сервер принимает one_off на любые даты) — дефолт открытого вопроса
  (ПМ может пересмотреть); серверный лимит — точка расширения.
- История состояний серий не хранится, исключение отдельного экземпляра
  серии, копирование недели/шаблоны, уведомления об изменениях графика,
  «повторения раз в N недель», связывание частично пересекающихся
  интервалов разных строк одним экземпляром (кросс-строчная проверка —
  точное совпадение дата+start+end; сознательное ограничение доработки
  f4a162b) — точки расширения (вне Must Спринта 10).
- Наследуются без изменений: single-worker + in-memory сессии/токены
  (ADR-001/002), статика без серверной защиты страниц (спринт-1 паттерн),
  нет rate-limit на публичных эндпоинтах, файлы-сироты uploads (cleanup
  вне объема).
