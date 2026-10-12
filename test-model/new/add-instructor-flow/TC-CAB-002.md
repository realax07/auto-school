# TC-CAB-002 — Негатив: /instructor/cabinet-stub без сессии → редирект на вход

- ID кейса: TC-CAB-002
- ID чеклиста: CHK-44
- Источник: CHK-44 → Requirement «Заглушка кабинета инструктора» (домен instructor-auth) → FR-13; Scenario «Страница заглушки без сессии отклоняется» (механизм защиты кабинета ученика, §15.6: /api/auth/me 401 → редирект)
- Тип: негативный
- Приоритет: Must
- Статус: automated (wiring) — tests/test_instructor_pages.py::test_cabinet_stub_session_guard_wiring (JS: sessionStorage.session_token → fetch /api/auth/me с X-Session-Token → 401 → location.href='/'). Браузерный редирект и серверный 401 /api/auth/me — automated в test_auth.py::test_me_logout_without_token_401 / test_forged_token_401; полный браузерный сценарий — manual/toBeAutomated

## GIVEN / WHEN / THEN
- GIVEN пользователь не выполнял успешный вход (нет токена; или токен истек/аннулирован — /api/auth/me отвечает 401)
- WHEN он открывает /instructor/cabinet-stub напрямую
- THEN страница не открывается: выполняется редирект на вход (механизм защиты кабинета ученика)

## Предусловия
- Браузер/Playwright с чистым sessionStorage (прогон А); просроченный/поддельный токен в sessionStorage.session_token (прогон Б).
- Сервис запущен; эталон 401: GET /api/auth/me без X-Session-Token → 401 (test_auth.py).

## Шаги
1. (А) В чистом контексте открыть /instructor/cabinet-stub напрямую.
2. Зафиксировать: был ли показ контента, итоговый URL после JS-гварда.
3. (Б) Записать в sessionStorage.session_token значение «forged-token»; повторить шаги 1–2.
4. (API-эталон) GET /api/auth/me без заголовка → статус; GET с forged-токеном → статус.

## Ожидаемый результат
1–2. Контент заглушки не показан (или мгновенно скрыт); редирект на вход — location.href='/' (механика Спринта 1).
3. Аналогично: 401 от /me → редирект на вход.
4. Оба варианта /api/auth/me → 401.

## Тестовые данные
Поддельный токен: forged-token. Реальный токен для контраста — вход instr@example.com / Instr1234 (approved).
