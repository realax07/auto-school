<!--
Reviewer-Delegation: deleg-cr-bug0547-external
Reviewer: code_reviewer (AI Factory, независимая сессия; плейсхолдер id — ПМ заменит)
Дифф: bugfix/s9-ui-followup-2 vs main. Коммит задачи: 4ccda45 (fix BUG-055/056, часть instructors.html/instructors.js),
тесты/доки 62c0cf0/22108a2. Диапазон из задания d081bcf..HEAD шире скоупа (содержит влитый Спринт 9);
ревьюировался дельта-дифф ветки main..HEAD (merge-base = 42367e1).
Дата ревью: 2026-11-04
-->

# Code Review — BUG-055 (логин-модалка на месте, поверх замутненной страницы)

## Что проверено (Scenario)

1. **Модалка на странице instructors.html** — разметка #m-login с теми же id, что в index.html: login-email/login-password/login-error/login-submit, крестик #login-close (дифф 4ccda45, instructors.html:18-32); локальный CSS .overlay (z-index 60 выше header z-index 2 и apply-бэкдропа 10).
2. **data-open-login без редиректа** — instructors.js:7-9: preventDefault + openLogin() ЛОКАЛЬНО; старая запись open_login/open_login_from + location.href='/' удалены. Смок ревьюера (реальный браузер + реальный uvicorn): клик «Войти» → URL остался /instructors, sessionStorage open_login не ставится.
3. **Замутнение страницы под модалкой** — instructors.html:9 и index.html:12: `background:rgba(1,7,11,.72)` + `backdrop-filter:blur(8px)` (+webkit-префикс); computed backdrop-filter в смоке — `blur(8px)` на ОБОИХ контурах.
4. **Сабмит postJSON /api/auth/login + роутинг по роли** — instructors.js:36-49: `route==='cabinet'`→/instructor/dashboard, pending→/instructors/pending, rejected→/instructors/rejected (причина — в sessionStorage до редиректа), else→/cabinet. Сверено с backend/auth.py:249 (`route = "cabinet" if role=="instructor" else "student-cabinet"`, pending/rejected :219/:225) и с эталонным landing.js:68-71 — расхождений нет.
5. **Реальный логин** — смок: approved-инструктор (apply+approve через API) → вход через модалку на /instructors → редирект /instructor/dashboard (wait_for_url, реальный бэкенд). Неверный пароль → #login-error виден, честный текст сервера «Неверный email или пароль».
6. **XSS-гигиена вставки ошибки** — instructors.js:51-52: только `err.textContent=…` (в т.ч. для res.data.error с сервера) — инъекция невозможна; innerHTML не используется.
7. **Фокус и скролл** — openLogin фокусирует #login-email (:14), body overflow hidden при открытой модалке, восстановление при закрытии.
8. **Регресс** — tests/test_instructor_pages.py адаптирован (62c0cf0): позитивные assert'ы `data-open-login` в src, `postJSON('/api/auth/login'` в src, отсутствие `location.href='/';`. Прогон ревьюера: tests/test_login_modal.py + test_instructor_pages.py + test_instructor_dashboard.py → **30 passed**; e2e login-контура (TC-UI-001/002/005) → **3 passed**.

## Вердикт: approve

## Замечания

| # | Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|---|
| 1 | minor | frontend/js/instructors.js:29-31 | Комментарий искажает контракт: «instructor-cabinet → /instructor/dashboard» — фактическое значение route для инструктора — `'cabinet'` (backend/auth.py:249, как и в landing.js:54-55). Код (:43 `route==='cabinet'`) верен; неточный комментарий — приманка для будущей «правки» в сломанное состояние. | Поправить комментарий: `cabinet → /instructor/dashboard, student-cabinet → /cabinet`. |
| 2 | minor | frontend/js/instructors.js:33-53 | Сабмит-логика (payload + postJSON + 4-ветвевой роутинг + обработка ошибки) — построчный copy-paste из landing.js:56-76 (~20 строк). Два независимых контура будут расползаться при первой правке контракта логина. | Вынести в общий модуль (например js/login-common.js: `wireLogin(submitId, errorId)`) и импортировать в обоих landing.js/instructors.js. |

## Не проверено

- Логин УЧЕНИКА через модалку на /instructors (else-ветка → /cabinet): код идентичен проверенному landing.js и ветке инструктора, но сам переход не прогонялся (смок ревьюера вел инструктора; ученический контур '/' покрыт e2e сьюта — 3 passed).
- Визуальный результат на-eye (степень «замутнения» воспринимается глазами) — только computed backdrop-filter/rgba.
- Полный pytest-сьют не запускался (указание ПМ: 409 passed).
