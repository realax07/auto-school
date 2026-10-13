<!-- factory-version: a12da342e542 -->

# Code Review (повторное): задача 2.2 change add-instructor-cabinet — wiring модалки входа (route-редирект)

## Вердикт: approve (реворк 0048069; исходный вердикт по 863f575 был возвратным — снят, см. «Реворк (0048069)»)

| Параметр | Значение |
|---|---|
| Ревьюер | Код-ревьюер (изолированная сессия) |
| Reviewer-Delegation: deleg-cr-20261013-external |
| Дата | 2026-10-13 |
| Ревьюемый дифф | 863f575 (feature/s2c-dashboard) — frontend/index.html, +2/−1 |
| Смежный дифф | 764c6e9 — tasks.md чекбоксы 2.2/4.1 (рассматривается в review-002-4.1) |
| Арбитры | sdd.md §15.5, §22; openspec/changes/add-instructor-cabinet/specs/instructor-dashboard/spec.md (Scenario «Переход после входа ведет в кабинет»); tasks.md 2.2; requirements-instructor-cabinet.md FR-18; контекст — add-instructor-flow §15.5/4.5 |
| Прогоны при ревью | `pytest tests/test_login_modal.py tests/test_auth_route.py tests/test_instructor_dashboard.py tests/test_instructor_pages.py` → 39 passed; контроль чтения auth.py §15.5-ветки |
| Blocker | 0 |
| Major | 2 (MAJ-1, MAJ-2) |
| Minor | 1 (MIN-1) |

Вердикт **return**: ключевой сценарий задачи (route='cabinet' → /instructor/dashboard)
реализован корректно, регресс ученика не задет, сессия сохраняется до редиректа.
Однако редирект-выражение декларирует все четыре маршрута §15.5, а фактически
два из них (pending/rejected) недостижимы — код мертв; и «Готовность» 2.2
ссылается на тесты, которых в дереве нет. Спека-арбитр (spec.md
instructor-dashboard) покрывает только scenario route='cabinet' — по нему
замечаний нет; но заявленный в tasks.md 2.2 объем («регресс маршрутов …
статусных экранов») не подтвержден.

## Таблица замечаний

| # | Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|---|
| MAJ-1 | major | frontend/index.html:126–129 | Ветви pending/rejected в тернарнике недостижимы. Редирект находится внутри guard `if(res.status===200&&res.data.ok&&res.data.token)`, а по контракту §15.5 (подтверждено backend/auth.py:219, 225) ответы `route:'pending'` и `route:'rejected'` возвращаются 200 {ok:true} **без токена** — guard никогда не пускает в них управление. Фактически waiting/deny-заявитель, как и до диффа, видит «Неверный email или пароль». Код создает ложное впечатление, что статусный роутинг FR-13 работает. Чекбокс-текст 2.2 при этом утверждает «pending → /instructors/pending, rejected → /instructors/rejected … без изменений», что не соответствует ни диффу (маршруты добавлены, пусть и мертвые), ни дереву (роутинга до диффа не существовало — 4.5 add-instructor-flow не закрыта) | Выбрать один вариант и согласовать с ПМ: (а) довести wiring до контракта §15.5 — вынести разбор route из-под token-guard для pending/rejected (+ запись reason в sessionStorage 'instructor_rejected_reason', которую уже читает instructor-rejected.html:20 — сейчас ключ никто не пишет); либо (б) сузить 2.2 до заявленного минимума — убрать мертвые ветви pending/rejected, оставить только маппинг cabinet/student-cabinet (+fallback), а статусный роутинг явно вернуть в незакрытую 4.5 add-instructor-flow |
| MAJ-2 | major | openspec/changes/add-instructor-cabinet/tasks.md:67–68 («Готовность» 2.2) | Готовность требует: «тесты — вход инструктора уводит на /instructor/dashboard; регресс маршрутов ученика и статусных экранов». В дереве таких фронтовых тестов нет: test_login_modal.py проверяет только фрагмент `location.href='/cabinet'` (строка 31), который после диффа проходит лишь за счет регистрационного обработчика (index.html:109), а не модалки входа; новый тернарник не покрыт ни одним фрагментным/файловым тестом. Регресс маршрутов проверен только на бэкенде (test_auth_route.py — это тесты 3.1, не 2.2) | Добавить wiring-тесты (по паттерну test_login_modal.py, без браузера): фрагменты маппинга в login-обработчике (route==='cabinet'→'/instructor/dashboard', student-cabinet→'/cabinet' и, при варианте (а) MAJ-1, pending/rejected-ветви + запись reason); актуализировать test_login_modal.py, чтобы фрагмент '/cabinet' проверялся в нужном обработчике |
| MIN-1 | minor | frontend/index.html:115 | Устаревший комментарий «Вход: fetch POST /api/auth/login → sessionStorage['session_token'] → /cabinet (sdd §10.1)» — редирект больше не безусловный /cabinet | Привести комментарий к контракту §15.5/§22 |

## Проверенные Scenario

- Route='cabinet' → /instructor/dashboard — OK (index.html:129; бэкенд-контракт подтвержден test_auth_route.py::test_login_instructor_approved_route_cabinet, test_instructor_dashboard.py:83; сценарий spec.md «Переход после входа ведет в кабинет» соблюден).
- Регресс учеников: student-cabinet → /cabinet — OK (index.html:129, ветвь fallback; бэкенд — test_login_student_route_student_cabinet; fallback `route||'student-cabinet'` сохраняет поведение Спринта 1 и совместимость со старым бэкендом).
- Сессия до редиректа — OK: sessionStorage.setItem (index.html:127) выполняется до location.href; ключ session_token консистентен с cabinet.html и instructor-dashboard.html (TOKEN_KEY='session_token').
- pending → /instructors/pending — FAIL (MAJ-1: ветвь недостижима, токена в ответе нет).
- rejected → /instructors/rejected — FAIL (MAJ-1; также reason из §15.5 нигде не сохраняется — instructor-rejected.html:20 читает пустой ключ).
- Тексты модалки без изменений — OK (test_tc_auth_login_modal_texts_verbatim зеленый; HTML модалки в дифф не входил).
- 401-ветка (единое сообщение) — OK, не изменена.
- Регистрационная ветка (index.html:103–113) — OK, не задана диффом; register.py выдает токен без route → редирект /cabinet сохранен.

## Что не проверено

- Браузерный сабмит (реальный fetch + редирект) — вне TestClient, конвенция проекта (test_login_modal.py, test_static.py).
- backend/auth.py §15.5-логика целиком — вне диффа задачи; проверена только как арбитр достижимости ветвей (route/token-контракт подтвержден чтением auth.py:200–250).
- instructor-dashboard.html и его wiring (2.1) — отдельная задача/ревью.
- Анти-брутфорс, TTL — покрыты регресс-набором (в составе 201/202 прогонов, см. review-002-4.1).

## Примечание для оркестратора (не замечание к задаче)

Формулировка tasks.md 2.2 «остальные маршруты … без изменений» описывает
несуществующее состояние: до 863f575 разбор route в index.html отсутствовал
(безусловный /cabinet), а владелец статусного роутинга — незакрытая задача 4.5
change add-instructor-flow. Если ПМ выберет вариант (б) MAJ-1 — это дефект
описания задачи, эскалируется отдельно; он не снимает MAJ-2 (тесты «Готовности»
нужны в любом из вариантов).

## Реворк (0048069)

Реворк-дифф: 0048069 (feature/s2c-dashboard, HEAD, дерево чистое) — frontend/index.html (+5/−3), tests/test_login_modal.py (+17). Проверено чтением диффа, кода (frontend/index.html:115–133, backend/auth.py:200–260) и прогонами на этом SHA. Вариант (а) MAJ-1 утвержден ПМ и реализован.

| Замечание | Вердикт |
|---|---|
| MAJ-1 | ЗАКРЫТО |
| MAJ-2 | ЗАКРЫТО |
| MIN-1 | ЗАКРЫТО |

### MAJ-1 — ЗАКРЫТО (approve, вариант (а))

- route-разбор вынесен из-под token-guard: условие смягчено до `res.status===200&&res.data.ok` (index.html:126), token-set стал опциональным (`if(res.data.token)`, :127), маппинг — цепочка if/else по всем четырем ветвям §15.5 (:129–132). Достижимость pending/rejected сверена с контрактом бэкенда: auth.py:219–227 возвращает `{ok:true, route:'pending'}` / `{ok:true, route:'rejected', reason}` без токена — теперь обе ветви реально выполняются.
- rejected-причина пишется до редиректа: `sessionStorage.setItem('instructor_rejected_reason', res.data.reason||'')` (index.html:132) — ключ читается instructor-rejected.html:20, разрыв устранен. Пустой fallback (`||''`) согласован с дефолтным текстом страницы отказа.
- Сценарий «cabinet → /instructor/dashboard» не изменен; регресс ученика (student-cabinet → /cabinet, fallback) сохранен (:133); сессия по-прежнему пишется до редиректа.
- Примечание из прошлого ревью снято за нерелевантностью: выбран вариант (а), мертвых ветвей больше нет, эскалация формулировки tasks.md не требуется.

### MAJ-2 — ЗАКРЫТО (approve)

- Добавлен test_login_route_mapping_wiring (tests/test_login_modal.py:89–103): фрагменты всех четырех ветвей маппинга, факт записи `instructor_rejected_reason` и позиционный контроль `0 < idx_ok < idx_route` (route-разбор после `res.data.ok`, т.е. вне token-guard) — рекомендация закрыта полностью, включая pending/rejected-фрагменты и запись reason.
- Фрагмент `location.href='/cabinet'` (теперь :84) корректен: после реворка он и правда в login-обработчике (fallback-ветвь), а не только в регистрационном, — актуализация, которую требовало замечание.
- Тест выполнялся: `pytest tests/test_login_modal.py tests/test_auth_route.py tests/test_instructor_dashboard.py tests/test_instructor_pages.py` → 40 passed на 0048069 (было 39).

### MIN-1 — ЗАКРЫТО (approve)

- Комментарий (index.html:115–116) актуализирован: «Вход: POST /api/auth/login → route (§15.5): cabinet → /instructor/dashboard, student-cabinet → /cabinet, pending → /instructors/pending, rejected → /instructors/rejected» — соответствует контракту §15.5 и фактическому коду.

### Верификация на SHA 0048069 (реворк-прогоны)

- `pytest tests/` (полный, на 0048069) → **202 passed**, 0 failed (128s; flaky-тест NFR-1 из rev-002-4.1 зеленый в обоих прогонах). Внимание: запись «201 passed» в tasks.md:143 относится к прогону до реворк-коммита; фактический счетчик на этом SHA — 202 (в 0048069 добавлен 1 тест). Существенности не имеет (запись стала консервативнее факта), но при следующей актуализации «Приемки» число стоит синхронизировать.
- `pytest tests/test_login_modal.py …` (профиль 2.2) → 40 passed.
- Воспроизводимость исходного MAJ-1/MAJ-2 rev-002-4.1 подтверждена на 863f575 (worktree): 200 passed + 1 failed (тот же flaky timing-тест) — диагнозы прошлого ревью верны, снимаются настоящим approve.

## Итоговый вердикт: approve

Все три замечания (MAJ-1, MAJ-2, MIN-1) закрыты в 0048069 ровно по выбранному
ПМ варианту (а), без расширения объема и без регресса. Вердикт действителен для
SHA 0048069 (и потомков без изменений в затронутых файлах). Оставшаяся ошибка
flow_check (J10 по 2.2/4.1) — та самая, что зафиксирована в rev-002-4.1 —
снимается этим approve.
