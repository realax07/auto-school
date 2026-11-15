<!-- Reviewer-Delegation: deleg-s17-dev-external | независимый код-ревьюер (не автор диффа) | ре-ревью CR-фикса f340550 (MAJ-1 + MIN-1/2/3) | дифф: e6f72c6..f340550 | ветка: feat/s17-pdd-learning | дата: 2026-11-15 -->

# Code review (ре-ревью): партия add-pdd-learning — задачи 1.2–1.7 (фикс по review-001)

Ре-ревью после доработки по вердикту return (review-001-1.2-1.3-1.4-1.5-1.6-1.7.md:
MAJ-1 + MIN-1/2/3). Дифф `git diff e6f72c6..f340550` — 3 файла: Dockerfile
(COPY content/ в frontend-builder), generate-pdd-json.mjs (ранние выходы
генератора, чистка out()), PddTickets.vue (индекс билетов из glob в mounted).
Полная версия ре-ревью — append-секция «Ре-ревью 2026-11-15: approve» в
review-001-1.2-1.3-1.4-1.5-1.6-1.7.md (статусы, воспроизведения, гейты).
Настоящий файл — машиночитаемый вердикт итерации (контракт J10:
parse по строке «Вердикт», rev 002 > rev 001).

## Вердикт: approve

Единственный блокер партии (MAJ-1) закрыт и подтвержден воспроизведением;
MIN-2/MIN-3 закрыты; MIN-1 закрыт наполовину — новый MIN-4 (не блокер,
в следующую волну).

## Закрытие замечаний review-001

- **MAJ-1 ЗАКРЫТ** — Dockerfile:27 `COPY content/ /app/content/` в
  frontend-builder перед `RUN npm build`. Layout стейджа (WORKDIR
  /app/frontend/vue + corpus в /app/content) воспроизведен в песочнице:
  генератор EXIT=0 — «26 глав, 8 групп / 321 знаков (fine: 166), 58 строк
  штрафов, 80 билетов × 20 вопросов», 85 pdd-файлов; контроль (без
  content/ — состояние до фикса): EXIT=1.
- **MIN-1: pravila ЗАКРЫТ; znaki НЕ ЗАКРЫТ → MIN-4 (не блокер).**
  pravila — чистый гейт («ГЕЙТ ЦЕЛОСТНОСТИ КОРПУСА ПРОВАЛЕН (pravila)…»,
  EXIT=1). znaki — `return { groups, signs }` (generate-pdd-json.mjs:141)
  стоит до объявления `const groups/signs` (:143–144) → TDZ: на реальном
  генераторе (PDD_CONTENT_DIR без znaki/) — сырой `ReferenceError: Cannot
  access 'groups' before initialization` (:141) вместо штатного сообщения.
  Уровень MIN (exit ненулевой, пропуск невозможен; в сборочных путях ветка
  недостижима — corpus в builder-стейдже после MAJ-1-фикса всегда есть).
  MIN-4: однострочный фикс `return { groups: [], signs: [] };` + опционально
  негативный юнит на ветку — в следующую волну.
- **MIN-2 ЗАКРЫТ** — статический импорт pdd-bilety-index.json удален;
  индекс из TICKET_CHUNKS в mounted(): `npm run build` EXIT=0, warning
  INEFFECTIVE_DYNAMIC_IMPORT НЕТ (0 warning), чанки pdd-bilety-* — 81
  (80 билетов + используемый index 0.5 КБ gzip) — паразитный дубль ушел.
  Гонки mounted→рендер НЕТ: categories=[] до резолва чанка — кнопок выбора
  не существует ⇒ startTicket недостижим; секция монтируется лениво
  (defineAsyncComponent + v-if pddTicketsVisited); e2e TC-UI-074 ждет
  auto-wait expect'ами. Процесс-ноты: шапка PddTickets.vue:7 все еще
  описывает «static import» (доку обновить); у mounted-промиса нет .catch
  (косметика).
- **MIN-3 ЗАКРЫТ** — мертвый тернарник out() удален (`+ '\n'` безусловно);
  детерминизм зелен (юнит-гейт перегенерации).

## Гейты на HEAD f340550

- `npm run build`: EXIT=0; `npm run check:budgets`: OK — (а)–(д),
  «страниц: 14», кабинет первый-заход 42.3 КБ gzip.
- pytest: unit 37 + api 362 + web без playwright 67 = **466 passed**
  (= review-001); точечно генератор/логика/контракт контейнера: 20 passed.
- e2e `tests/web/test_ui_playwright.py`: **84 passed** (вкл. TC-UI-074
  тренажер). Первый прогон (параллельно с api-сюитом) дал 70 ERROR на
  фикстуре браузера — конкуренция трех одновременных pytest-процессов,
  solo-прогон 84/84; к диффу отношения не имеет.
- `openspec validate --all --strict`: 26 passed, 0 failed.

BUG-064/17.7.4: docker build локально невоспроизводим (нет docker.sock —
факт среды не изменился); локальных препятствий для CI docker-build больше
нет — финальное закрытие связки фактом зеленого CI-прогона у ПМ.
