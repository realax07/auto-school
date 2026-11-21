<!-- Reviewer-Delegation: deleg-s19-bridge-external | дата: 2026-11-21 | внешняя hermes-сессия -->

# Review-19.6-001 — волна 19.6 (add-ai-chat-home)

Роль: code_reviewer (независимая проверка; автором диффа волны не являюсь).
Объект: коммит 8db4dda (HTTPBridgeProvider + env-активация _provider,
scripts/ai_bridge.py, TC-S19-009/010, tasks.md +19.6), коммит f97d6b9
(.gitignore += docker-compose.override.yml), файл вне репо
~/.config/systemd/user/ai-bridge.service. Дерево: /home/hermes-bot/auto-school,
ветка fix/ai-bridge, HEAD на момент ревью 336f6c0. Гигиена: писан только
этот артефакт; код/тесты/спеки не правились; push нет.

## Машинная верификация (собственные прогоны и пробы на HEAD 336f6c0)

1. `pytest tests/api/test_s19_ai_chat.py tests/unit/test_s19_ai_chat.py` →
   **28 passed** (25.3s) — новое (api) и старое (unit) носители зелёные вместе.
2. Живой мост: `systemctl --user status ai-bridge` → active (running),
   enabled; `ss -tlnp` → LISTEN 172.19.0.1:8790 (python3).
3. Пробы протокола моста (без запуска hermes, curl): POST /nope → 404;
   POST /chat не-JSON → 400; POST {"query":"  "} → 400; GET /chat → 501.
4. Юнит-проба HTTPBridgeProvider против локальных фейков: HTTP 400 от моста
   → ProviderError ✓; тело 200 с JSON-массивом вместо dict → AttributeError
   МИМО except (основание [MIN-1]).
5. env-гигиена: в окружении ревью нет AI_PROVIDER_URL/AI_BRIDGE_* —
   env-активация безопасна для тестов/CI (подтверждено зелёным прогоном п.1:
   без переменной работает v1-путь).
6. `git check-ignore -v docker-compose.override.yml` → .gitignore:242 ✓;
   tracked-файла с таким именем нет (`git ls-files`) — ничего нужного
   не скрыто.
7. grep по deploy/, docs/ на 172.19/AI_PROVIDER_URL/ai_bridge — упоминаний
   нет (только tasks.md): инвариант подсети нигде не задокументирован
   (основание [MAJ-1]).

## Файл-разбор

### backend/ai/provider.py (8db4dda)

+ Контракт generate(messages) -> reply не сломан: routes.py в диффе волны
  отсутствует (git show 8db4dda --stat); роутер по-прежнему ловит только
  provider.ProviderError → 503 _PROVIDER_DOWN («Ассистент сейчас не
  отвечает…»). Шов set_provider/active_provider/generate_reply не тронут.
+ env-активация _provider при импорте: тернарник по
  os.environ.get("AI_PROVIDER_URL") — без переменной (и при пустой строке)
  v1 HermesSessionProvider; app.py/импорты ничего не меняют.
+ NFR-3: модуль не логирует; сеть/таймаут/не-JSON/HTTP != 200 → ProviderError
  без деталей (HTTPError ⊂ OSError ⊂ перехват; 400 от моста → ProviderError
  подтверждено пробой п.4).
+ NFR ≤30s: urlopen(timeout=PROVIDER_TIMEOUT_SECONDS=30); цепочка бюджетов
  25 (CLI --run-budget) < 28 (мост) < 30 (провайдер) — слоёная, практическая
  граница держится мостом (subprocess timeout 28s), urlopen — страховка.

[MIN-1] HTTPBridgeProvider.generate: если мост вернул 200 с валидным JSON,
  не являющимся dict (массив/строка/число) — payload.get бросает
  AttributeError, который НЕ покрыт except (OSError, ValueError). Контракт
  docstring «ошибки любого рода → ProviderError» нарушается: наверх уйдёт
  сырое исключение, FastAPI отдаст 500 вместо человеческого 503.
  Подтверждено пробой п.4. Практический риск низкий (единственный клиент —
  собственный мост, всегда dict), фикс дешёвый: isinstance(payload, dict) →
  ProviderError и/или добавить http.client.HTTPException в except (обрыв
  соединения при чтении тела даёт IncompleteRead ⊄ OSError — код-инспекция).

### scripts/ai_bridge.py (8db4dda, новый файл)

+ MIN-2 (arch-review 001) выдержан: текст запроса — в stdin
  (`--query-file -`), argv чистый; subprocess list-argv без shell=True →
  инъекций нет; SQL в файле нет.
+ Ошибки CLI (returncode != 0, TimeoutExpired 28s, OSError) → reply = "" →
  200 {"reply":""} → провайдер даст ProviderError → роутер отдаст
  человеческий текст: заявленный контракт волны выполнен.
+ NFR-3: log_message подавлен; секреты/argv/тексты в логи не пишутся;
  ошибочные ответы без тел.
+ Bind 172.19.0.1 — с интернета приватный адрес не маршрутизируется; живой
  стенд подтверждает LISTEN (п.2).

[MAJ-1] Инвариант «шлюз frontend-сети docker == 172.19.0.1» нигде не
  закреплён: docker-compose.yml НЕ пинует ipam-подсеть (networks.frontend
  пуст), юнит хардкодит AI_BRIDGE_HOST=172.19.0.1, скрипт дефолтит на тот
  же IP, а docker раздаёт подсети 172.17…172.31 по порядку создания сетей.
  Пересоздание сети (network prune, переезд хоста, чужие сети, созданные
  раньше) → мост молча деградирует до симптома «Ассистент сейчас не
  отвечает» (bind fail → Restart-луп, либо контейнер стучится в другой
  шлюз) — ровно то, что волна чинит, и никакая проверка этого не заметит.
  Хук AI_BRIDGE_HOST есть, но никто его не выставляет; deploy/RUNBOOK молчат
  (п.7 верификации). Сегодня на бою работает (ПДД-проверка 23.5s записана в
  tasks.md; bind на стенде живой) — волну не блокирует, но требует
  follow-up: (а) pin ipam subnet+gateway 172.19.0.0/16 + 172.19.0.1 в
  tracked docker-compose.yml (конфликт подсетей станет fail-loud «Pool
  overlaps» вместо тихой деградации), (б) пункт в deploy/RUNBOOK.md,
  (в) опционально — healthcheck-проба моста.
[MIN-2] do_POST: тело-не-словарь JSON (массив/число вместо
  {"query": …}) → payload.get → AttributeError мимо except
  (ValueError, UnicodeDecodeError) → соединение рвётся без ответа, traceback
  уходит в stderr/journal. Тот же класс, что [MIN-1]; фикс — isinstance.
[NOTE-1] Docstring «прочие пути/методы → 404»: фактически GET /chat → 501
  (дефолт BaseHTTPRequestHandler) — проверено curl (п.3). Либо докстринг
  уточнить, либо добавить do_GET → 404.
[NOTE-2] Content-Length без верхней границы — память под один запрос не
  ограничена (контур внутренний, приемлемо). Отрицательное значение
  безопасно: BufferedReader.read(-5) → ValueError («read length must be
  non-negative or -1») → 400 (семантика io проверена).
[NOTE-3] _SESSION_TAIL_RE — ручная копия правила из provider.py (наблюдение
  волны 19.3): при правке оригинала правила разъедутся. Импорт из скрипта
  хоста неудобен (sys.path) — трейд-офф разумен, оставить комментарий
  «держать синхронно с provider.py».
[NOTE-4] Мост без аутентификации; host-IP 172.19.0.1 в принципе достижим
  любому контейнеру любой docker-сети хоста, не только app. В собственной
  инфре без чужих контейнеров — приемлемо, но «снаружи недоступен» точнее
  читать как «недоступен из интернета».
[NOTE-5] ThreadingHTTPServer × subprocess hermes без лимита параллелизма:
  каждый запрос — отдельный agent-процесс (после одного прогона на стенде
  peak RSS моста 607M). design.md MIN-3 сознательно параллелизм не
  ограничивает — согласуется, но помнить при росте нагрузки.

### ~/.config/systemd/user/ai-bridge.service (вне репо)

+ PATH=/home/hermes-bot/.local/bin:/usr/local/bin:/usr/bin:/bin —
  FileNotFoundError на hermes закрыт (which hermes → ~/.local/bin,
  arch-review 001 п.8).
+ Restart=always + RestartSec=3 — самоподъём до появления docker-сети
  (bind fail → retry): подтверждено active/enabled на стенде; Linger=yes
  проверен через loginctl — юнит переживёт ребут без логина пользователя.
[NOTE-6] After=network.target docker.service в user-юните не разрешается
  (это системные юниты чужого менеджера — имена не резолвятся), реальный
  порядок обеспечивает Restart-луп. Строки безвредны, но вводят в
  заблуждение — убрать или заменить комментарием.
[NOTE-7] Харденинг юнита отсутствует (NoNewPrivileges=yes,
  ProtectSystem=strict, PrivateTmp=yes) — опционально; процесс исполняет
  агентный CLI с сетевым доступом.

### tests/api/test_s19_ai_chat.py (8db4dda)

+ Дифф только добавляет тесты — существующие носители не ослаблены; полное
  s19-дерево api+unit зелёное (п.1 верификации).
+ TC-S19-009: фейковый мост на 127.0.0.1:0 без внешних зависимостей,
  daemon-поток, server.shutdown() в finally; проверены happy-path
  (содержимое {"query": …} перехвачено), пустой reply → ProviderError.
[MIN-3] TC-ID-коллизия: TC-S19-009/010 уже заняты юнит-тестами v1
  (tests/unit/test_s19_ai_chat.py:348 и :392 — механика 19.2.1), волна
  добавила тесты с теми же ID в api-файл; шапка самого api-файла (строка 8)
  прямо говорит, что TC-S19-009/010 «остаются юнит-ногой» в tests/unit.
  Один ID → два разных теста в двух файлах; spec.md TC-ID не
  перечисляет — трассировка мутнеет. Фикс: переименовать новые в
  TC-S19-013/014 (или развести ID) и не править шапку задним числом.
[MIN-4] TC-S19-010: importlib.reload без try/finally — при падении первого
  assert модуль остаётся перезагруженным с env-переменной (monkeypatch
  удалит переменную при teardown, но reload не случится) → все последующие
  API-тесты сессии ходят в http-bridge на 127.0.0.1:1 и получают 503 —
  каскад ложных красных. Сегодня зелёный; гигиена: finally/fixture с
  reload без переменной.
[NOTE-8] Docstring TC-S19-009 заявляет «не-JSON / сеть → ProviderError»,
  но в тесте проверен только пустой reply; не-JSON/сетевую ветку добавить
  веткой фейка (дёшево).

### openspec/changes/add-ai-chat-home/tasks.md (+19.6)

+ 19.6.1–19.6.3 соответствуют диффу по фактам (env-активация, stdin/MIN-2,
  bind, PATH юнита, ПДД-проверка 23.5s, TC-ID) — расхождений с кодом не
  нашёл, кроме уже отражённой [MIN-3] (TC-ID).
[NOTE-9] После фикса [MAJ-1] добавить follow-up-пункт (19.6.4: pin ipam +
  RUNBOOK), чтобы инвариант подсети не остался только в этом ревью.

### .gitignore (f97d6b9)

+ Запись точечная, в хвосте файла; check-ignore подтверждает ровно
  docker-compose.override.yml; tracked-файла с таким именем нет — ничего
  нужного не скрыто. Локальный env боя (AI_PROVIDER_URL в override)
  осознанно вне git — согласуется с «секреты не в репо».

## Вердикт: approve

Волна выполняет заявленный контракт: generate(messages) -> reply и роутер
не тронуты; env-активация без переменной безопасна для тестов/CI (28 s19
тестов зелёные на HEAD 336f6c0, окружение без AI_*); NFR-3 (секреты/argv/
тексты не логируются, наружу без деталей) и NFR ≤30s (цепочка 25<28<30)
выдержаны; ошибки моста → 200 с пустым reply → человеческий текст роутера;
инъекций нет (stdin-канал, list-argv без shell); .gitignore точечный;
юнит самоподъёмный (Restart + Linger проверены живым стендом).

Обязательный follow-up (волну не блокирует, закрыть отдельным пунктом/волной):
1. [MAJ-1] Закрепить инвариант подсети: ipam subnet/gateway
   172.19.0.0/16 + 172.19.0.1 в tracked docker-compose.yml + запись в
   deploy/RUNBOOK.md (+ опционально healthcheck-проба моста).
2. [MIN-1/2] isinstance(payload, dict) → ProviderError (+ учесть
   http.client.HTTPException) в HTTPBridgeProvider.generate и в do_POST
   моста.
3. [MIN-3/4] Развести TC-ID (новые → TC-S19-013/014) и обернуть reload
   TC-S19-010 в finally; [NOTE-8] — докрыть ветки не-JSON/сеть.
