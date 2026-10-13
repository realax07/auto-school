# TC-INS-006 — Истекшая сессия (TTL 12 ч) → 401 + ленивая чистка

- ID кейса: TC-INS-006
- ID чеклиста: CHK-6
- Источник: CHK-6 → Requirement «Доступ к кабинету инструктора» → FR-18 (TTL, MIN-3 review-001-3.1); Scenario «Сессия истекла — редирект на вход»; контроль закрытия MIN-3 (D4)
- Тип: негативный (граничный)
- Приоритет: Must
- Статус: automated — tests/test_instructor_dashboard.py::test_dashboard_401_expired_session_ttl, плановый ID TC-FR18D-002 (референс-тест review-002: test_dashboard_401_expired_session_ttl); запись с истекшим expires кладется в auth._sessions напрямую/сдвигом времени, без sleep

## GIVEN / WHEN / THEN
- GIVEN сессия инструктора выдана, но срок истек (expires в прошлом; TTL 12 ч; запись в реестре кладется напрямую со сдвигом времени — без sleep)
- WHEN выполняется GET /api/instructor/dashboard с этим X-Session-Token
- THEN бэкенд отвечает 401 {"ok": false}; ленивая чистка: токен отсутствует в реестре сессий после отклонения

## Предусловия
- Сервис собран (create_app(), чистая БД); инструктор создан флоу apply → approve → login (фикстура instructor).
- Доступ к внутреннему реестру auth._sessions (monkeypatch — как в существующем тесте).

## Шаги
1. Войти инструктором, зафиксировать токен.
2. Положить в реестр auth._sessions[token] = (time.time() - 1, 1) — expires в прошлом, без sleep.
3. Убедиться, что токен присутствует в реестре до запроса.
4. GET /api/instructor/dashboard с X-Session-Token: <токен>.
5. Проверить реестр после ответа.

## Ожидаемый результат
4. 401, тело точно {"ok": false} (sdd §20.1, п.1: сессия истекла → 401).
5. Токена в auth._sessions нет — истекшая запись вычищена лениво при проверке.

## Тестовые данные
Инструктор: instr@example.com / Instr1234; сдвиг времени: expires = now − 1 c (TTL 12 ч — 43200 c по конфигурации auth).
