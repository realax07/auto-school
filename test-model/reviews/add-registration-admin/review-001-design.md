# Review 001 — Design (design_validator)

Дата: 2026-10-08
Охват: frontend/index.html, frontend/registered.html, frontend/admin-login.html, frontend/admin-dashboard.html
Эталон: design/mocks/landing-students.html, login-modal.html, register-modal.html, registered.html, admin-login.html, admin-dashboard.html

## Вердикт: approve

Метод: построчный diff mock ↔ frontend (в т.ч. длинные CSS-строки, которые при обычном чтении обрезаются). Структура, классы/токены, стили и текстовки совпадают дословно; все найденные отличия попадают в разрешенные категории (wiring, поля Пароль/Подтверждение, XSS-fix) либо являются следствием wiring.

## Разрешенные отличия (не дефекты)

| # | Файл / место | Отличие | Категория |
|---|---|---|---|
| R1 | index.html — модалка регистрации: input'ы получили id (reg-surname, reg-name, reg-patronymic, reg-email, reg-phone) | Добавлены id для wiring | wiring — разрешено |
| R2 | index.html — модалка регистрации: новые поля «Пароль» / «Подтверждение» (reg-password, reg-password-confirm) + скрытый <p class="err" id="reg-error"> | Новые поля по решению Заказчика; стили поля повторяют токены мокапа (.row/.field/.field input), плейсхолдеры ••••••••; err-строка инлайн-стили #ff9c9c совпадает с палитрой ошибки admin-login мокапа | Поля Пароль/Подтверждение — разрешено |
| R3 | index.html — script: fetch POST /api/register, редирект /registered, показ ошибки через err.textContent | wiring — разрешено (XSS-безопасно: textContent) |
| R4 | registered.html:23 — href="landing-students.html" → href="/" | wiring (роутинг через бэкенд) — разрешено |
| R5 | admin-login.html — script: локальная проверка admin/admin заменена на fetch POST /api/admin/login + sessionStorage token | wiring — разрешено; текст ошибки «Неверный логин или пароль» и все стили сохранены |
| R6 | admin-dashboard.html:46 — onclick «Выйти»: location.href='admin-login.html' → sessionStorage.removeItem + href='/admin-login' | wiring — разрешено |
| R7 | admin-dashboard.html — script: демо-массив users → fetch /api/admin/users (loadUsers), export.csv через API | wiring — разрешено |
| R8 | admin-dashboard.html — innerHTML с данными users → createElement/textContent (sp.textContent='Ученик' — hardcoded, роль инструктора в API-версии не выводится) | XSS-fix — разрешено; см. minor D1 |

## Таблица расхождений

| ID | Элемент | Селектор / место | Ожидалось (источник) | Фактически | Серьезность |
|---|---|---|---|---|---|
| D1 | admin-dashboard — колонка «Роль» | frontend/admin-dashboard.html, loadUsers() | design/mocks/admin-dashboard.html: роль из данных (u.role, бывает «Инструктор») | XSS-fix-версия выводит hardcoded textContent='Ученик' для всех строк | minor (следствие разрешенного wiring: API в текущем виде возвращает учеников; при появлении инструкторов в выдаче роль будет неверной — вернуть u.role из API c textContent) |
| D2 | admin-dashboard — колонка «Дата регистрации» | frontend/admin-dashboard.html, loadUsers() | мокап: дата в данных, формат дд.мм.гггг | форматирование перенесено на клиент (created_at → дд.мм.гггг) | minor (визуально идентично, часть wiring) |

Blocker: нет. Major: нет.

## Проверено дословное совпадение

- landing: CSS-блоки (base, модалки, media-queries) — байт-в-байт (diff rc=0 по строкам 1–15, включая весь CSS); body-разметка hero/steps/assistant/footer — дословно; текстовки (заголовок, шаги, «Гига ГАИшник», футер, модалки «Вход»/«Регистрация») — дословно.
- Модалка «Вход» (в составе index.html) — поля, плейсхолдеры, кнопки, «Нет аккаунта? Зарегистрироваться» — дословно по login-modal.html.
- Модалка «Регистрация» — состав полей ФИО/Email/Телефон + hint — дословно по register-modal.html (плюс разрешенные Пароль/Подтверждение).
- registered.html — тексты карточки, note, кнопки — дословно (кроме R4).
- admin-login.html — разметка карточки, поле ошибки, hint «admin / admin», CSS — дословно (кроме R5).
- admin-dashboard.html — сайдбар, навигация, таблица, badge, пустое состояние, CSS — дословно (кроме R6–R8).

Браузерных дефолтов не обнаружено: все интерактивные элементы охвата покрыты стилями из утвержденных мокапов (.login, .btn, .field input, .nav button, .logout, .btn-export).
