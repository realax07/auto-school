# Tasks: add-instructor-flow

Правила: задача атомарна (одна сессия = одна задача); `[P]` — независимая
задача (можно параллелить, каждая в своем worktree). Трассировка FR — в
sdd.md, раздел «Трассировка (Спринт 2, часть 1)». Детальные контракты — в
sdd.md, раздел «Спринт 2, часть 1».

## 1. Домен instructor-application (backend/instructors.py)

- [ ] 1.1 [P] backend/instructors.py — POST /api/instructors/apply
      (публичный, без авторизации): Pydantic-модель с дефолтами `str = ""`
      (хендлерная валидация как register.py, MAJ-1); поля: fio (или
      surname/name/patronymic — по разбору ФИО), phone, email, address,
      work_format ('own'|'sber'), plate, license_number, license_date,
      license_category, experience, password, password_confirm, consent
      (обязательный чекбокс согласия, MIN-2). Порядок проверок (первая
      ошибка): обязательные поля (по макету со звездочкой + пароль +
      подтверждение) → consent == true (иначе 422 «Согласие: поле
      обязательно») → формат email → телефон ≥ 10 цифр → пароль ≥ 8 →
      совпадение подтверждения → plate обязателен при work_format='own'
      → license_date при заполнении — валидная дата → email отсутствует в
      users (SELECT) → email отсутствует в instructor_applications (SELECT,
      допущение proposal). Формат ошибок — 422 {"ok": false, "error":
      "<поле-ру>: <причина>"}, единое "Email: уже зарегистрирован" для
      занятого email. Успех: bcrypt.hashpw(password, gensalt(rounds=12))
      (cost ≥ 12, FR-11.1; открытый пароль не сохраняется и не логируется),
      INSERT instructor_applications (status='waiting', password_hash=хэш);
      sqlite3.IntegrityError от UNIQUE instructor_applications.email → та же
      контрактная 422 "Email: уже зарегистрирован" (вторая линия защиты,
      MAJ-1, механика register.py:104), 200 {"ok": true}. Разбор ФИО анкеты
      на фамилию/имя/отчество — деталь реализации задачи (макет хранит ФИО
      одним полем; users требует три). Готовность: тесты — успешная отправка
      создает заявку waiting со всеми полями и хэшем (пароль P в записи и
      логах отсутствует); каждый вариант валидации дает контрактную 422;
      занятый email (users и заявки) — единое сообщение; гонка: два apply
      одного email параллельно → ровно одна заявка, второй получает 422
      (MAJ-1); анкета без consent → 422 (MIN-2); файл ВУ на сервер не
      передается.
      FR: FR-11, FR-11.1, FR-12, FR-16 (email-проверка). NFR: NFR-2, NFR-3.

- [ ] 1.2 [P] backend/db.py — схема: CREATE TABLE instructor_applications
      (полный состав полей — design.md; email TEXT NOT NULL UNIQUE — вторая
      линия защиты apply, MAJ-1) + ALTER TABLE users ADD COLUMN
      role TEXT NOT NULL DEFAULT 'student' (idempotent: проверка
      существования колонки/таблицы — существующие базы Спринтов 0–1
      поднимаются без пересоздания; ученики остаются student).
      Готовность: тесты — init_db на пустой и на унаследованной базе;
      дефолт role='student' у существующих записей; UNIQUE users.email
      сохранен; UNIQUE instructor_applications.email работает: второй INSERT
      того же email → sqlite3.IntegrityError (MAJ-1).
      FR: FR-16 (UNIQUE email — users и заявки), NFR-4. Зависит от: —
      (можно параллельно с 1.1: контракт таблицы зафиксирован в design.md).

## 2. Домен admin-moderation (backend/instructor_admin.py)

- [ ] 2.1 [P] backend/instructor_admin.py — модерация заявок
      (X-Admin-Token, require_admin как admin.py; 401 {"ok": false} без
      валидного токена):
      GET /api/admin/instructor-applications — все заявки со всеми данными
      анкеты, БЕЗ password_hash (ключ в ответе отсутствует — решение
      Заказчика 2026-10-12-hash-not-rendered, MIN-5; хэш хранится в заявке,
      но не выдается API), сортировка created_at DESC, id DESC; ответ
      {"count": N, "applications": [...]}.
      POST /api/admin/instructor-applications/{id}/approve — только заявка в
      статусе waiting (иначе 409 {"ok": false, "error": "Заявка уже
      одобрена"}); ОДНА транзакция (MIN-3): INSERT INTO users (surname, name,
      patronymic, email, phone, password_hash ИЗ ЗАЯВКИ — без повторного
      хэширования, FR-11.1; role='instructor'), user_id = cur.lastrowid
      (research.md §3) + UPDATE статус → approved, commit один (симметрично
      register.py); гонка дубля email — обработка sqlite3.IntegrityError как
      409 (users.email UNIQUE, FR-16).
      POST /api/admin/instructor-applications/{id}/deny — guard статуса
      (MIN-1, симметрично approve): только waiting, approved → 409 «Заявка
      уже одобрена», deny → 409 «Заявка уже отклонена»; комментарий
      обязателен: пустой/отсутствующий → 422 {"ok": false, "error":
      "Комментарий: поле обязательно"} (FR-15); UPDATE статус → deny,
      review_comment = комментарий.
      Готовность: тесты — список заявок без password_hash (ключ отсутствует
      в ответе; только с админ-токеном); approve создает пользователя users
      с тем же хэшем и role='instructor', статус → approved, повторный
      approve → 409; падение между INSERT и UPDATE не оставляет
      waiting-заявку с пользователем (транзакция, MIN-3); вход одобренного
      с паролем анкеты успешен; deny без комментария → 422, с комментарием →
      deny + сохраненная причина; deny approved-заявки → 409 и запись users
      не меняется (MIN-1); повторный deny → 409, причина не меняется;
      все три эндпоинта без токена → 401.
      FR: FR-14, FR-15, FR-16. NFR: NFR-2, NFR-3.
      Зависит от: 1.2 (таблица).

## 3. Домен instructor-auth (backend/auth.py — расширение)

- [ ] 3.1 backend/auth.py — роутинг входа по статусу (FR-13): механизм
      login без изменений (bcrypt.checkpw, единое сообщение, анти-брутфорс,
      фиктивная проверка). Добавка: после проверки пароля против users
      (успех) ответ дополняется {"route": "cabinet"} для role='instructor'
      / {"route": "student-cabinet"} для role='student'; случай «пользователя
      нет, но пароль совпал с password_hash заявки» — SELECT
      instructor_applications по email (параметризованный): waiting →
      200 {"ok": true, "route": "pending"} (сессия НЕ выдается); deny →
      200 {"ok": true, "route": "rejected", "reason": review_comment}
      (сессия НЕ выдается); заявки нет → 401 единое сообщение (без
      изменений). bcrypt-проверка против хэша заявки — только при
      отсутствующей записи users (тайминг: та же схема фиктивной проверки,
      что Спринт 1). Неудачная попытка против заявки — учитывается
      анти-брутфорсом наравне с users (единый учет по IP).
      Готовность: тесты — waiting-инструктор получает route=pending без
      токена; deny — route=rejected с точной причиной; approved — сессия +
      route=cabinet; ученик — route=student-cabinet (регресс Спринта 1);
      неверный пароль/нет заявки — единый 401; анти-брутфорс срабатывает на
      неудачных попытках инструктора тоже.
      FR: FR-13. NFR: NFR-2, NFR-3.
      Зависит от: 1.2 (таблица заявок); контракт ответа — sdd.md §15.

## 4. Статика и фронтенд

- [x] 4.1 [P] frontend/instructors.html — лендинг инструкторов: перенос
      design/mocks/landing-instructors.html дословно (тексты, стили,
      структура); wiring (единственные отличия от мокапа): кнопки CTA
      («Стать инструктором», карточки форматов, нижний CTA) → редирект на
      /instructors/apply (FR-10). Модальное окно «Стать инструктором» мокапа
      (сбор контактов) не используется как отдельная форма — CTA ведет
      на анкету (форма заявки — отдельная страница, FR-10/FR-11); футер без
      входа водителей (out of scope, proposal).
      Готовность: тесты — GET /instructors → 200, тексты совпадают с
      мокапом (кроме wiring), CTA ведут на /instructors/apply.
      FR: FR-10.

- [x] 4.2 [P] frontend/instructor-apply.html — анкета: перенос
      design/mocks/registration-instructor.html дословно; wiring: сабмит →
      POST /api/instructors/apply (поля по контракту sdd.md §15.1, включая
      consent — обязательный чекбокс согласия, MIN-2; без него кнопка
      неактивна/422); 422 →
      сообщение об ошибке под формой (текст из ответа); ok → редирект
      /instructors/pending (FR-12). Поведение мокапа сохраняется: госномер
      активен только при «свой автомобиль»; файл ВУ — только визуал, на
      сервер не отправляется (не входит в тело запроса).
      Готовность: тесты — GET /instructors/apply → 200, тексты совпадают
      с мокапом; успешный сабмит уводит на /instructors/pending; ошибка
      валидации показывается; сабмит без чекбокса согласия не выполняется;
      тело запроса не содержит файла.
      FR: FR-11, FR-12.

- [x] 4.3 [P] frontend/instructor-pending.html + frontend/instructor-rejected.html —
      экраны ожидания и отказа в тоне мокапов Заказчика (тексты согласуются
      при реализации; проверка — design check, FR-17): pending — «заявка на
      рассмотрении»; rejected — показ причины из ответа логина
      (sessionStorage; пусто/нет — без персональной причины, но страница
      без данных заявки не раскрывает чужую причину). Прямое открытие
      rejected без данных логина — без причины (не раскрывать чужую).
      Готовность: тесты — GET /instructors/pending → 200; редирект-сценарий
      после сабмита анкеты; сценарий показа причины C после deny-входа.
      FR: FR-12, FR-13, FR-17.

- [x] 4.4 [P] frontend/instructor-cabinet-stub.html — заглушка «кабинет
      скоро» (БЕЗ функциональных элементов dashboard-макета — он вне
      объема): JS читает токен из sessionStorage, GET /api/auth/me
      (X-Session-Token) → 401 → редирект на вход; 200 → показ заглушки.
      Готовность: тесты — без сессии редирект на вход; с сессией
      одобренного инструктора — заглушка; функциональных блоков кабинета
      нет.
      FR: FR-13 (заглушка). Зависит от контракта /api/auth/me (Спринт 1,
      без изменений).

- [ ] 4.5 Wiring форм входа: страница/модалка входа для инструктора —
      reuse модалки «Вход» (m-login) с лендинга / (единый
      /api/auth/login): ok → разбор route из ответа: cabinet →
      /instructor/cabinet-stub (токен в sessionStorage); student-cabinet →
      /cabinet (регресс Спринта 1); pending → /instructors/pending;
      rejected → /instructors/rejected (+ reason в sessionStorage).
      401 → единое сообщение (как сейчас).
      Готовность: тесты — все четыре маршрута после входа; тексты модалки
      не изменены.
      FR: FR-13. Зависит от: 3.1 (контракт route).

## 5. Сборка

- [ ] 5.1 app.py: подключить роутеры instructors (1.1) и instructor_admin
      (2.1) в create_app(); маршруты статики: /instructors (4.1),
      /instructors/apply (4.2), /instructors/pending +
      /instructors/rejected (4.3), /instructor/cabinet-stub (4.4) — рядом
      с /cabinet. init_db вызывает обновленную схему (1.2). app.py —
      единственная точка правки существующего кода (кроме оговоренного
      расширения auth.py в 3.1); register.py, admin.py, db.py (кроме 1.2),
      config.py не меняются.
      Готовность: тесты — /api/health зеленый; регресс Спринтов 0–1
      (/api/register, /api/auth/*, /api/admin/users) работает; новые
      маршруты отдаются.
      FR: FR-10, FR-12, FR-13. Зависит от: 1.1, 1.2, 2.1, 3.1, 4.1–4.4.

## 6. Приемка

- [ ] 6.1 Полный прогон: `pytest tests/` зеленый (включая регресс
      Спринтов 0–1); NFR-2 — grep-проверка параметризованного SQL в новых
      модулях (0 конкатенаций); NFR-3 — открытый пароль и подтверждение
      отсутствуют в логах/репозитории; password_hash НЕ выдается API:
      ответ GET /api/admin/instructor-applications без ключа password_hash,
      UI админки его не рендерит, ответ GET не логируется (MIN-5, решение
      Заказчика 2026-10-12-hash-not-rendered); NFR-4 — состав полей
      instructor_applications по design.md (email UNIQUE);
      `openspec validate --all --strict` зеленый; `python3
      scripts/flow_check.py .` OK; design check — tone экранов
      waiting/rejected (FR-17).
      Готовность: все проверки пройдены.
      FR: NFR-2, NFR-3, NFR-4, FR-17. Зависит от: 5.1, 4.5.

## Зависимости

- 1.1, 1.2, 2.1*, 3.1*, 4.1, 4.2, 4.3, 4.4 — независимы друг от друга
  ([P]; пишут против контрактов sdd.md §15 и design.md, не против кода
  друг друга; *2.1 и 3.1 зависят только от схемы 1.2 — при параллели
  1.2 стартует первым или мержится первым).
- 4.5 — после 3.1 (нужен контракт route в ответе логина); правит
  frontend/index.html (модалка m-login).
- 5.1 — собирает все (последняя точка правки существующего app.py).
- 6.1 — последняя (полный прогон + валидации + design check).
