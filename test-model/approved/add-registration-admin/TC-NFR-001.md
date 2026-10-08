# TC-NFR-001 — Время ответа POST /api/register ≤ 500 мс

- ID кейса: TC-NFR-001
- ID чеклиста: CHK-36
- Источник: CHK-36 → requirements.md NFR-1 (сквозное, домен registration); контроль по design/sdd: bcrypt cost 12 ~250 мс
- Тип: НФТ
- Приоритет: Must

## Предусловия
- Сервис запущен (uvicorn, single-worker); базовый URL: http://127.0.0.1:8000.
- БД data/app.db инициализирована (init_db при старте), таблица users пуста (чистое тестовое окружение).
- Окружение .env задано: ADMIN_USER, ADMIN_PASSWORD_HASH (bcrypt), SECRET.
- Контроль живости: GET /api/health -> 200 {"ok": true}.

## Шаги
1. Замерить время 5 прогонов POST /api/register с типичными данными (уникальные email: perf1@example.com … perf5@example.com), замер по часам вокруг HTTP-запроса (time.perf_counter).
2. Для каждого прогона зафиксировать статус и время ответа в мс.
3. Вычислить максимум и медиану по 5 прогонам.

## Ожидаемый результат
1–2. Каждый прогон: 200 {"ok": true}.
3. Время ответа КАЖДОГО прогона ≤ 500 мс (бюджет с учетом bcrypt cost 12 ~250 мс соблюдается; медиана и max фиксируются в отчете).

## Тестовые данные
- Типичные данные: базовый набор с email `perf1@example.com` … `perf5@example.com`.
