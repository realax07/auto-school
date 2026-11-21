<!-- Reviewer-Delegation: deleg-40439845192f488fafd5fda610a79191 — flowctl code_reviewer стадия, accepted | дата: 2026-11-19 | session: cli-pid 198228 (spawn-ledger; id CLI-сессии изнутри сессии недоступен) -->

# Review-19.4-002 — финальная приемка волны 19.4/QA (Спринт 19, add-ai-chat-home)

Роль: code_reviewer (финальная верификационная итерация перед PR, flow=1,
task=19.4). Независимая верификация приемочного состояния спринта; автором
артефактов волны не являюсь. Дерево: worktree wt-s19-ai-chat, ветка
feature/add-ai-chat-home, HEAD на момент ревью
341409ea80d35a4c1597cf80ca8bb4a1152a47ae. Гигиена: писан только этот
артефакт (зона code-reviews/add-ai-chat-home/**); код/тесты/спеки не
правились; push нет.

## Периметр приемки

База — review-19.4-001 (приемка ПМ, verdict approve, провениенс
hermes:20261119_170213_c31bed, reviewed_commit cd5afed). Носители
верифицируемого состояния волны:

- Кейсы: qa_case_reviewer review-001-cases — return (MAJ-1 MAN-001 команда
  прогона, MIN-1 UNIT-001 план прогонов; approved-партия НЕ переносилась) →
  фикс qa_case_author fe90b00 → review-002-cases — approve + approved
  партия verbatim (ef687c7) + «одобрить» запись review-003-cases (de3d29a,
  контракт 5). Итог: кейс-база approve, approved-партия переносится.
- Автоматизация/носители: чек-лист и TC-кейсы 70c4476; юнит-носитель
  aed2fb3; UI-носители кабинета cb72af4; TC-UI-060 навигация c6db641;
  API-носитель 19.2.5 d6e85b5; носители-соседи regress ca2a8c4; отчет
  маппинга TC→носители 9cbcec9
  (test-model/reports/qa-auto-report-add-ai-chat-home.md).
- Design: review-001-design — approve (cfca542): «Главная» в обеих версиях
  против макетов дословно, spark/приветствие/подсказка/плейсхолдер/композер,
  «+» видима/неактивна с честной подписью «Скоро» (FR-19.7), сайдбар/таб-бар
  не задеты.
- Regress: test-model/regress/add-ai-chat-home/regress-final.md.

## Машинная верификация (независимый прогон на HEAD 341409e)

1. Хвост спринта: `git log --oneline dc24970..HEAD` → 40 коммитов; QA-волна
   присутствует полностью (70c4476, 76c66c2, fe90b00, ef687c7, de3d29a,
   cb72af4, c6db641, d6e85b5, ca2a8c4, 9cbcec9), приемка cd5afed, карта
   319c336, зафиксированные regress-прогоны 9b22ba8 и 341409e (последний —
   только regress-final.md, прод-код = c93c537).

2. Тесты (строки счетов прогона этим ревьюером):
   - `/home/hermes-bot/auto-school/.venv/bin/python -m pytest tests/unit/test_s19_ai_chat.py -q`
     → `14 passed, 1 warning in 12.83s`;
   - `/home/hermes-bot/auto-school/.venv/bin/python -m pytest tests/web/test_cabinet_page.py -q`
     → `7 passed in 0.05s`.
   Полный regress: regress-final.md сверен — `verdict: PASS`,
   «614 passed, 1 warning in 739.25s (0:12:19)», pytest exit code 0,
   commit прогона c93c537f113650a8306575af9dfc9b49911198b5, tier domain,
   changed files 72. Флейк-история прозрачна: первый прогон — T-флак
   nfr001/latency (класс T-4 техраздела), перепрогон PASS (9b22ba8),
   финальный прогон PASS (341409e).

3. Выборочно по диффу dc24970..HEAD:
   - XSS: App.vue — 0 добавленных строк с innerHTML/v-html; cabinet.html —
     0 совпадений (pre-existing `innerHTML = ''` строки 763 — очистка без
     данных, спринт 6.2, вне спринта).
   - SQL backend/ai/routes.py: все execute() с ?-плейсхолдерами, retention
     ?-параметром (1615aa6), f-string/format SQL — 0.
   - Сайдбар/таб-бар: 0 строк диффа по паттернам sidebar|tab-bar|nav-item.
   - «+» disabled: ai-plus disabled + «Скоро» (FR-19.7) — подтверждено в
     App.vue на HEAD.

4. openspec: `openspec validate --all --strict` → `Totals: 28 passed,
   0 failed (28 items)`.

## Наблюдения (не блокирующие)

- В рабочем дереве есть незакоммиченное изменение
  openspec/changes/add-ai-chat-home/tasks.md (чекбоксы 19.4.1–19.4.4
  `[x]`→`[ ]`) — вне зоны ревью, данным артефактом не тронуто; состояние
  чекбоксов — зона ПМ перед PR.
- Прод-код не менялся после regress-прогона: коммиты после c93c537 —
  только артефактные (341409e = regress-final.md); вердикт PASS валиден
  для HEAD.

## Вердикт: approve

Приемка волны 19.4/QA подтверждается: кейс-база approve (review-001 →
фикс → review-002 + approved партия), носители и маппинг зафиксированы,
design approve, regress-final PASS (614 passed), машинные проверки п.1–4
зеленые. Binding подписан по deleg-40439845192f488fafd5fda610a79191.
