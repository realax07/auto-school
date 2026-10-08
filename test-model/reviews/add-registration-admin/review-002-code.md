# Code review 002: add-registration-admin (повторное, спринт-0)

Ревьюер: code_reviewer (изолированная сессия)
База: review-001-code.md (blocker №1 — stored XSS, frontend/admin-dashboard.html:75)
Проверяемый коммит: HEAD 0d60ff3 «fix(xss): admin-dashboard рендер через textContent»

## Вердикт: approve

Blocker из review-001-code закрыт полностью.

| # | Серьезность | Статус | Где | Комментарий |
|---|---|---|---|---|
| 1 | blocker | ЗАКРЫТ | frontend/admin-dashboard.html:69-81 | fio/email/phone/dateStr рендерятся через createElement+textContent; в innerHTML данные больше не попадают. Бейдж «Ученик» сохранен (span.badge, className задан до appendChild). Таблица функционально не сломана (см. проверки ниже) |

## Что проверено

- git show HEAD (0d60ff3): дифф только frontend/admin-dashboard.html (+5/-1), суть — замена `tr.innerHTML='<td>'+u.fio+...` на сборку DOM: `td()` helper с textContent для fio/email/phone, отдельная сборка бейджа через createElement, dateStr (производная от u.created_at) тоже через td().
- Грепп по frontend/: единственный оставшийся innerHTML — `tb.innerHTML=''` (очистка tbody, без данных) — безопасен. Других точек вставки данных БД в HTML нет.
- Бейдж: `sp.className='badge'; sp.textContent='Ученик'` — визуально и семантически эквивалентно прежнему `<span class="badge">Ученик</span>`.
- Функциональность таблицы: порядок колонок (ФИО, Email, Телефон, Роль, Дата) соответствует thead; счетчик `Записей: N`, пустое состояние `#empty`, 401→редирект на /admin-login, exportCsv() — не затронуты.
- Регресс: pytest -q → 48 passed, 1 warning (19.9s) — прогон ревьюером при этом ревью.

## Minors из review-001-code

Не блокируют (согласовано с ПМ). Контроль перенесен в таблицу ниже — статус на момент review-002:

| # | Где | Суть | Статус |
|---|---|---|---|
| 2 | backend/app.py | «остальное — из frontend/ по пути» (sdd §2) не реализовано | открыт |
| 3 | backend/register.py | IntegrityError→500 вместо 422 (гонка SELECT→INSERT) | открыт |
| 4 | requirements.txt | версии не запинены (arch MIN-5) | открыт |
| 5 | .env.example | MIN-2/MIN-1 (single-worker, SECRET) | открыт |
| 6 | frontend/admin-login.html | подсказка «admin / admin» не соответствует env-учетке | открыт |
| 7 | tests/test_admin_users.py | хардкод UTC+3 (MIN-4) | открыт |
| 8 | tests/test_register.py | мертвые импорты | открыт |

Судьба minors — решение ПМ (в ту же очередь или в бэклог следующего спринта); на вердикт review-002 не влияют.

## Замечание (неблокирующее, на будущее)

`function td(text)` объявлена внутри колбэка forEach — работает, но в следующих спринтах лучше выносить helper на уровень функции loadUsers() (стиль/повторное использование). Не является находкой review-002.
