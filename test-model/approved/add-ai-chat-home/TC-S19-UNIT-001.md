# TC-S19-UNIT-001 — Юнит-носитель Спринта 19: TC-S19-001…012 — 401/контракт/история/изоляция/retention (удаление+границы)/ошибки 422+503/адаптер (stdin, бюджет, таймаут)/срез session_id — уже автоматизированы

- Автоматизация: `tests/unit/test_s19_ai_chat.py` — 14 тестов TC-S19-001…TC-S19-012, все автоматизированы. Прогон на merge-кандидате f71838c (2026-11-19): **14 passed in 13.84s**. Провайдер моккится на швах (monkeypatch backend.ai.provider.generate_reply / subprocess.run) — реальных вызовов hermes CLI из юнитов НЕТ (боевой smoke — TC-S19-MAN-001). Клиент — TestClient над create_app() с tmp-БД (conftest.client, без сети); time.sleep запрещен (спека qa-pipeline) — старые записи прямым INSERT с created_at = datetime('now', '-N days').
- Приоритет: Must (FR-19.3/19.5; NFR — доступ, изоляция, ≤30 с, retention-серверная, секреты не в логах)
- Статус: автоматизирован (юнит-носитель dev-волны 19.2; ПМ dc24970: API-носитель tests/api — за qa_automation на 19.4, юнит — dev)
- Трассировка:
  - Requirement: Доступ к чату — только валидная сессия ученика (openspec/changes/add-ai-chat-home/specs/ai-chat/spec.md) — TC-S19-001 (401 {ok:false} POST+GET без/с bogus-токеном, содержимое не возвращается), TC-S19-004 (изоляция: две учетки, чужой user_id недоступен)
  - Requirement: Композер отправляет сообщение и показывает ответ ассистента — TC-S19-002 (контракт POST {message}→200 {ok,reply}; обмен user+assistant в ai_messages), TC-S19-007 (422 пустое/пробельное, провайдер не вызывался), TC-S19-008 (503 человеческий текст без «ProviderError»/«Traceback»/«hermes»/«subprocess»/«503»; обмен НЕ сохранен), TC-S19-009 (адаптер: текст через --query-file '-' (stdin), НЕ argv — MIN-2; --run-budget и таймаут ≤30 с; SYSTEM_PROMPT содержит «ГигаЧат — помощник по обучению ПДД»/«ГИБДД»), TC-S19-010 (таймаут/ненулевой код/пустой ответ → ProviderError без деталей), TC-S19-012 (срез хвоста «session_id: …» провайдера — наблюдение dev-волны 19.3)
  - Requirement: Серверная история чата, подхват и retention 14 дней — TC-S19-003 (shape {ok, messages:[{role,text,created_at}]}, хронопорядок; пусто → []), TC-S19-005 (старше 14 дней — скрыты и удалены физически; DELETE в BEGIN IMMEDIATE с SELECT — ОВ-2 review-001), TC-S19-006 (13 дней — остается), TC-S19-011 (граница ±1 с от 14 дней — MIN-2 CR-19.2)
  - Носитель: tests/unit/test_s19_ai_chat.py (план прогонов №4 — regress-full, полный сьют)

## GIVEN / WHEN / THEN
- GIVEN create_app() над tmp-БД (схема ai_messages создана при старте), провайдер моккится на шве, ученики регистрируются/логинятся базовым набором conftest
- WHEN выполнены запросы POST /api/ai/chat и GET /api/ai/chat/history (без токена, с токеном, валидные, пустые, при сбое провайдера), история засеивается прямым INSERT с контролем created_at, адаптер дергается с мок-stdout (в т.ч. с хвостом session_id)
- THEN контракты и механика соответствуют спецификации: 401 {ok:false} без содержимого; 200 {ok:true, reply}; журнал {role,text,created_at} в хронопорядке; изоляция по user_id; retention удаляет старые строки физически с границей окна ±1 с; ошибки 422/503 человеческим текстом без кодов и без записей в истории; адаптер шлет текст в stdin мимо argv, бюджет ≤30 с, таймаут и пустой ответ → ProviderError без деталей; ответ ученику без служебного хвоста session_id

## Примечание
- Отдельные файлы юнитов НЕ дублируют будущий API-носитель (TC-S19-API-001): 19.2.5 (tests/api/test_s19_ai_chat.py) пишет qa_automation в этой волне с трассировкой TC-S19-NNN в docstring — прецедент test_s16_backend.py; риск дублей/коллизии TC-ID решить на стыке волн (см. вопросы отчета).
- TC-S19-011 — граничный носитель retention по замечанию ревью (MIN-2 CR-19.2); TC-S19-012 — по наблюдению dev-волны 19.3 (хвост hermes chat «session_id: …»).
