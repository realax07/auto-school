# TC-CAB-004 — Logout из кабинета: токен аннулирован, очистка sessionStorage, редирект на главную

- ID кейса: TC-CAB-004
- ID чеклиста: CHK-4 (фронт-часть)
- Источник: CHK-4 → Requirement «Выход ученика» (домен auth) → FR-8; Scenario «Успешный выход» (браузерная часть); sdd §10.2 («после любого ответа фронт очищает sessionStorage и делает редирект на /»)
- Тип: позитивный
- Приоритет: Must
- Статус: manual/toBeAutomated (браузерный сценарий; косвенный автоконтроль wiring — tests/test_cabinet_page.py::test_cab_wiring_logout_flow; серверная часть — TC-AUTH-009, automated)

## GIVEN / WHEN / THEN
- GIVEN ученик вошел в систему и находится в кабинете
- WHEN он нажимает «Выйти» (POST /api/auth/logout с X-Session-Token)
- THEN сессионный токен аннулируется (200 {"ok": true}), sessionStorage очищен, пользователь попадает на главную страницу (лендинг /)

## Предусловия
- Браузер/Playwright; пользователь вошел и находится в /cabinet.

## Шаги
1. Войти, открыть /cabinet (как TC-CAB-001); зафиксировать sessionStorage.session_token.
2. Нажать кнопку «Выйти» в шапке кабинета.
3. Перехватить POST /api/auth/logout; зафиксировать итоговый URL и состояние sessionStorage.
4. Попытка вернуться на /cabinet кнопкой «назад» браузера.

## Ожидаемый результат
3. POST /api/auth/logout → 200 {"ok": true}; итоговый URL «/»; sessionStorage.session_token отсутствует.
4. Возврат на /cabinet без токена снова уводит на вход (модалка m-login) — кабинет не открывается по «назад».

## Тестовые данные
Базовый пользователь TC-AUTH-001.
