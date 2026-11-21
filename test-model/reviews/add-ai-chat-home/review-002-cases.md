<!-- Reviewer-Delegation: deleg-s19-qarev2 — spawned hermes chat session (role=qa_case_reviewer); ре-ревью тем же ревьюером | объект: фикс fe90b00 | дата: 2026-11-19 | session: 20261119_165739_193dd6 -->

# Review-002 — ре-ревью TC-кейсов add-ai-chat-home (итерация 002, после фикса)

- Объект: фикс-коммит fe90b00 «qa_case_author: фикс MAN-001 (MAJ-1) и UNIT-001 (MIN-1) по review-001-cases» — дифф ровно по двум файлам с finding'ами: test-model/new/add-ai-chat-home/TC-S19-MAN-001.md, TC-S19-UNIT-001.md (2 files, +4/−4). Периметр ре-ревью = только фикс; остальные 7 кейсов зафиксированы approve-частью review-001 (повторная сверка не требуется).
- Worktree: feature/add-ai-chat-home, HEAD = fe90b00, дерево чистое.

## Проверка 1. MAJ-1 → TC-S19-MAN-001: команда прогона (исполнимость и сверка с provider.py)

- Фикс в кейсе: `hermes chat -Q --query-file - --oneshot --run-budget 25`.
- Сверка с backend/ai/provider.py — argv адаптера (строки 108–117) собирает ровно: `CHAT_EXECUTABLE("hermes"), "chat", "-Q", "--query-file", "-", "--oneshot", "--run-budget", str(_RUN_BUDGET_SECONDS)`. Посимвольное совпадение с командой кейса — PASS.
- Бюджет: `_RUN_BUDGET_SECONDS = 25` (provider.py:42) → `--run-budget 25` в кейсе верен (было 30 — исправлено). Таймаут: `PROVIDER_TIMEOUT_SECONDS = 30` (provider.py:45). NFR ≤30 с в кейсе теперь описан как «бюджет hermes 25 с + таймаут адаптера 30 с» — и в трассировке, и в THEN; двухуровневая модель бюджета/страховки совпадает с комментарием provider.py:39–45 — PASS.
- Исполнимость CLI (факт-чек `hermes chat --help`): usage `[-q QUERY | --query-file PATH]` — строчный `-q` и `--query-file` в одной взаимоисключающей группе (старая команда `-q --query-file -` падала бы на парсинге аргументов — находка review-001 подтверждена). `-Q, --quiet` — отдельный флаг («Quiet mode for programmatic use: … Only output the final response and session info»), с `--query-file` не конфликтует; `--oneshot` легитимен (для -Q подразумевается, но явный вызов не ошибка); `--run-budget SECONDS` существует. Команда исполнима — PASS.

## Проверка 2. MIN-1 → TC-S19-UNIT-001: ссылка на план прогонов

- Фикс в кейсе: «Носитель: tests/unit/test_s19_ai_chat.py (план прогонов №4 — regress-full, полный сьют)» (было «№1»).
- Сверка с openspec/changes/add-ai-chat-home/tasks.md, «План тестовых прогонов (J32-легкий)»: пункт 4 = «regress-full (19.4): полный сьют api+web+smoke, 6–7 мин — фон+notify». Совпадение с фиксом — PASS.
- Перекрестно: checklist.md CHK-31 («Полный regress … план прогонов J32-легкий №4») согласован. Носитель tests/unit/test_s19_ai_chat.py существует в дереве. PASS.

## Гигиена фикс-коммита

- git show fe90b00 --stat: только TC-S19-MAN-001.md и TC-S19-UNIT-001.md — никаких посторонних правок, new/ вне диффа не тронут. PASS.

## Вердикт: approve

Все findings review-001 закрыты корректно, в периметре, с факт-чеком против кода и CLI. Approved-партия перенесена VERBATIM из test-model/new/add-ai-chat-home/ в test-model/approved/add-ai-chat-home/ (9 кейсов + checklist.md): diff -r пуст; git diff --cached -M — 10 файлов, 0 вставок/0 удалений (R100). review-001-cases остается в силе как полный протокол первичного ревью.
