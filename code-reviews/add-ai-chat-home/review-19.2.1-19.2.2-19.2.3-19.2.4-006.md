<!-- Reviewer-Delegation: deleg-40439845192f488fafd5fda610a79191 — flowctl code_reviewer стадия, accepted | дата: 2026-11-19 | session: cli-pid 198228 (spawn-ledger; id CLI-сессии изнутри сессии недоступен) -->

# CR-19.2 финальный binding (review-19.2.1-19.2.2-19.2.3-19.2.4-006) — итоговый вердикт волны 19.2 (backend)

Роль: code_reviewer (финальная верификационная итерация перед PR, flow=1,
task=19.4). Независимая верификация: автором диффа волны не являюсь. Дерево:
worktree wt-s19-ai-chat, ветка feature/add-ai-chat-home, HEAD на момент
ревью 341409ea80d35a4c1597cf80ca8bb4a1152a47ae. Гигиена: писан только этот
артефакт (зона code-reviews/add-ai-chat-home/**); код/тесты/спеки не
правились; push нет.

## Периметр (история ревью волны 19.2)

Периметр волны = review-19.2-001..005 + фикс-коммиты ПМ:

- review-19.2-001 — approve (3 MIN);
- фикс 1615aa6 «?-параметризация retention (без f-string SQL), граничный
  носитель TC-S19-011» (MIN-1/MIN-2) → review-19.2-002 — return (RR-1/RR-2
  флейм носителя: time.sleep keep-строки);
- фикс 025572a «убран time.sleep, докстринг по конвенции файла» →
  review-19.2-003 — approve;
- review-19.2-004 — return (MAJ-1: потерян pytest.raises в TC-S19-010);
- фикс в составе 28de632 (восстановлен pytest.raises returncode=1) →
  review-19.2-005 — approve (ре-ревью автора 004, периметр = только фикс).

Итог истории: approve → фиксы → 005 approve. Финальное состояние волны —
все ревью-находки закрыты, последнее ре-ревью (005) approve.

## Машинная верификация (независимый прогон на HEAD 341409e)

1. Хвост спринта: `git log --oneline dc24970..HEAD` → 40 коммитов, полная
   последовательность волн присутствует: 19.2.1 efb46de (провайдер-адаптер
   backend/ai) → 19.2.2 9d0bfef (миграция ai_messages) → 19.2.3 3331c2c
   (API /api/ai/chat, /api/ai/chat/history) → 19.2.4 aed2fb3 (юнит-носитель)
   → фиксы 1615aa6/025572a/28de632 → волна 19.3 (9dafce1→0cc091c→df64d0a) →
   QA-волна (кейсы 70c4476…ef687c7, носители cb72af4/c6db641/d6e85b5/ca2a8c4)
   → карта 319c336 → regress 9b22ba8/341409e. Фиксы волны подтверждены
   `git show --stat`: 1615aa6 = backend/ai/routes.py +18/−5 и
   tests/unit/test_s19_ai_chat.py +42/−2; 025572a = только тестовый файл
   +5/−6; 28de632 = styles.css 1 строка + тест +2.

2. Тесты (прогон этим ревьюером, строки счетов):
   - `/home/hermes-bot/auto-school/.venv/bin/python -m pytest tests/unit/test_s19_ai_chat.py -q`
     → `14 passed, 1 warning in 12.83s`;
   - `/home/hermes-bot/auto-school/.venv/bin/python -m pytest tests/web/test_cabinet_page.py -q`
     → `7 passed in 0.05s`;
   - полный regress: вердикт в
     test-model/regress/add-ai-chat-home/regress-final.md сверен —
     `verdict: PASS`, «614 passed, 1 warning in 739.25s (0:12:19)»,
     commit прогона c93c537 (HEAD 341409e отличается от него только самим
     артефактным коммитом regress-final.md, прод-код идентичен).

3. Выборочно по диффу dc24970..HEAD:
   - XSS: `grep -nE 'innerHTML|v-html' App.vue` по спринт-диффу — 0
     добавленных строк с innerHTML/v-html. Единственный innerHTML в файле
     (строка 763, `photo.innerHTML = ''`) — pre-existing код спринта 6.2,
     очистка пустой строкой (данные не присваиваются, вектора нет), вне
     периметра волны; конвенция v-if/v-for зафиксирована комментарием
     (строка 33). frontend/vue/cabinet.html — 0 совпадений.
   - SQL: backend/ai/routes.py — все execute() с ?-плейсхолдерами (строки
     83–85, 127, 132, 163, 168–169); значение retention идет ?-параметром
     (фикс 1615aa6); f-string/format SQL — 0 совпадений. Миграция
     backend/core/db.py — CREATE TABLE IF NOT EXISTS + индекс,
     параметризованные запросы (прецедент С16).
   - Сайдбар/таб-бар не тронуты: в диффе dc24970..HEAD 0 строк по паттернам
     sidebar|tab-bar|nav-item (удаление `navTo('Мои заявки')` — мертвый
     wiring, MIN-3 arch-review 002, легитимно обревьюено в review-19.3-001).
   - «+» неактивна: `<button class="ai-plus" id="ai-plus" type="button"
     disabled aria-label="Вложения — скоро">` + бейдж `<span
     class="ai-soon">Скоро</span>` (FR-19.7 соблюден дословно).

4. openspec: `openspec validate --all --strict` → `Totals: 28 passed,
   0 failed (28 items)`.

## Вердикт: approve

Волна 19.2 (19.2.1–19.2.4) подтверждается в финальном состоянии: история
ревью закрыта (005 approve), фиксы 1615aa6/025572a/28de632 (доля волны)
верифицированы, машинные проверки п.1–4 зеленые. Binding подписан по
deleg-40439845192f488fafd5fda610a79191.
