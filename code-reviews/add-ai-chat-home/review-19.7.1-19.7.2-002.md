<!-- Reviewer-Delegation: deleg-s19-glm-external | дата: 2026-11-23 | внешняя hermes-сессия -->
# Review-19.7.1-19.7.2-002 — ре-ревью фиксов волны 19.7

- Reviewer: code_reviewer (независимый, НЕ автор фиксов; автор фикс-коммита
  3f907e5 — фикс-волна по review-19.7.1-19.7.2-001, вердикт return)
- Диапазон: фикс-коммит 3f907e5 на HEAD (c182ba2), рабочее дерево чистое
- Метод: полный дифф 3f907e5 и текущее состояние файлов; программные
  структурные сверки (заголовки дельты vs мастер-спеки, подсчет символов,
  grep абсолютных путей); pickaxe-поиск имен тестов (-S) по истории;
  побайтовое сравнение восстановленного блока с доудаленной версией
  19.6; прогон pytest в дереве и из git-архива HEAD в отдельный каталог
  (hermetic-изоляция, как в review-001); фикс MIN-4 проверен ИСПОЛНЕНИЕМ
  реальной функции (подмена urlopen, кейсы из review-001);
  `openspec validate add-ai-chat-home` → valid.

## Разбор по пунктам возврата

### MAJ-1 — FIX-CONFIRMED (носители TC-S19-009/010 восстановлены)

- Блок «Волна 19.6: HTTPBridgeProvider (env AI_PROVIDER_URL)» восстановлен
  в tests/api/test_s19_ai_chat.py (+59 строк, только добавления —
  TC-001…008 не тронуты, проверено по диффу).
- Pickaxe (-S по имени test_tc_s19_009_http_bridge_provider_generate):
  добавлены 8db4dda (19.6) → удалены 8a656c2 (волна 19.7) → восстановлены
  3f907e5. Восстановленный блок ПОБАЙТОВО идентичен доудаленной версии
  19.6 (diff извлеченных блоков пуст) — эквивалент 1:1, не «по мотивам».
- Носители тестируют ИМЕННО боевой класс: тест импортирует
  `backend.ai.provider as ai_provider`; TC-S19-009 инстанцирует
  ai_provider.HTTPBridgeProvider (фейк — только на стороне провода), та же
  цепочка build_query → POST {query} → reply; пустой reply → ProviderError.
  TC-S19-010: importlib.reload при env AI_PROVIDER_URL →
  active_provider().name == "http-bridge"; без env → "hermes-session" —
  сверено с фактической активацией в provider.py (env читается на импорте,
  имена классов совпадают). Ровно та механика, что требовал return-001.
- Ложное «носители не ослаблены» устранено: impact §4 теперь утверждает это
  в корректном объеме («TC-S19-001…008 и носители кабинета без изменений»)
  и отдельно фиксирует восстановление 009/010.

### MAJ-2 — FIX-CONFIRMED (MODULE_PATH hermetic)

- MODULE_PATH = str(Path(__file__).resolve().parents[2] / "services" /
  "ai-bridge" / "app.py"), маркер «MAJ-2 (review-19.7.1-19.7.2-001)» в коде.
- grep "/home/" по test_s19_ai_bridge_glm.py и test_s19_ai_chat.py → 0
  совпадений: абсолютных хостовых путей нет.
- Эксперимент (как в review-001): git archive HEAD → /tmp/review197copy;
  из копии glm-тест 3 passed; импорт тест-модуля ИЗ КОПИИ показывает
  MODULE_PATH = /tmp/review197copy/services/ai-bridge/app.py — тест
  проверяет СВОЁ дерево, изоляция подтверждена исполнением, а не чтением.
- Полный suite трех файлов из копии: 22 passed — на CI (ubuntu-latest,
  /home/runner/…) красного пути больше нет.

### MAJ-3 — FIX-CONFIRMED (spec-дельта containerization)

- Новая дельта openspec/changes/add-ai-chat-home/specs/containerization/
  spec.md (36 строк) в изменении add-ai-chat-home — по прецеденту
  add-wallet-economy, как требовал return-001.
- REM-требование «### Requirement: Compose-стек из двух сервисов (app +
  nginx)» байт-в-байт совпадает с заголовком мастер-спеки
  openspec/specs/containerization/spec.md (программная проверка: строка
  присутствует в обоих файлах). В REM — причина удаления (решение
  Заказчика 2026-11-21) и ссылка на замещающее требование.
- ADD «### Requirement: Compose-стек app + nginx + ai-bridge»: MUST в
  тексте; от заголовка до первого Scenario — 426 символов (≤ 500).
- Сценарии: «Данные переживают пересоздание контейнеров» сохранен
  ДОСЛОВНО (программная сверка блока с мастер-спекой → True); новый
  «Сервисы стека — {app, nginx, ai-bridge}, без MinIO»: services ровно
  {app, nginx, ai-bridge}, minio/minio-data нет, у ai-bridge нет ports,
  `docker compose config` валиден — соответствует compose и TC-ADD-004.
- `openspec validate add-ai-chat-home` → «Change 'add-ai-chat-home'
  is valid».

### MIN-1 — FIX-CONFIRMED (трассировка по факту)

- tasks.md 19.7.1/19.7.2 переписаны: services/ai-bridge (app.py +
  Dockerfile), конфиг ai-bridge.json — единственный источник параметров
  (ключ вне репо и вне env app), compose AI_PROVIDER_URL, фактическое имя
  файла tests/api/test_s19_ai_bridge_glm.py, TC-S19-013 = «404/пустой
  query/не-dict» (сверено с фактическим test_tc_s19_013_bridge_bad_
  requests), TC-S19-012 = «ошибки GLM → пустой reply» (сверено),
  восстановление 009/010 зафиксировано. Несуществующий test_s19_ai_glm.py
  и GLMProvider-в-backend из трассировки убраны.
- impact §4 переписан: боевой путь — HTTPBridgeProvider (env
  AI_PROVIDER_URL), без переменной — hermes-session (dev); восстановленные
  носители и spec-дельта упомянуты; live-цифра приведена к 9.2s (согласована
  с протоколом ПМ, замечание review-001 снято); отложенные MIN-2/3/6
  честно названы «следующее касание»; chmod 600 конфига подтвержден на
  хосте (права rw------- проверены).
- Пункт «commit-сообщение-память»: следующий регресс-коммит c182ba2 в
  заголовке пишет «620 passed: 619 − 2 старых мостовых + 3 GLM» —
  противоречие 619/620 устранено.

### MIN-4 — FIX-CONFIRMED (TypeError + None-guard, проверено исполнением)

- В _generate: except-кортеж расширен TypeError, добавлен
  isinstance(choice, str) guard; маркеры «MIN-4» в коде. Внешний except
  do_POST (OSError/ValueError/KeyError/IndexError) не тронут.
- Проверено ИСПОЛНЕНИЕМ реальной функции (модуль, загруженный из
  git-копии, urlopen подменен фейком):
  {"choices":[{"message":"str"}]} — точный кейс-баг review-001 → reply ""
  (раньше: TypeError покидал do_POST, traceback в stderr); payload=[] →
  ""; payload="x" → ""; content=None → "" (раньше: «None» ученику);
  content=42 → ""; нет choices → ""; норма «  Знак 3.20  » → «Знак 3.20»
  (strip сохранен). Исключения не покидают _generate ни в одном кейсе;
  контракт «любая ошибка GLM → 200 {"reply": ""}» не нарушен.

### MIN-5 — FIX-CONFIRMED (.dockerignore)

- .dockerignore дополнен строкой ai-bridge-config/ — конфиг с ключом
  больше не отправляется в build-context `build: .` (канон заголовка
  «секреты вне контекста сборки», NFR-14/INC-006 — соблюден).
- Нано-замечание (не блокирует): маркер «MIN-5 review-…» на строке
  отсутствует (маркеры в коде есть у MAJ-2/MIN-4; в .dockerignore и
  spec-дельте — нет). На суть фикса не влияет.

## Прогоны тестов

- В дереве (HEAD c182ba2, чистое): `python3 -m pytest
  tests/api/test_s19_ai_bridge_glm.py tests/api/test_s19_ai_chat.py
  tests/test_container_contract.py -q` → 22 passed.
- Распределение: glm 3 + chat 14 + contract 5 = 22; collect-only по
  каждому файлу совпадает с passed — ничего не потеряно и не скипнуто.
- О «ожидай 25» в брифе делегации: для этих трех файлов 25 арифметически
  недостижим; 22 согласуется с записью review-001 (20 passed на тех же
  файлах до фикса) + ровно 2 восстановленных носителя. «25» — неточность
  брифа, не недоделка фиксов.
- Из копии репо (git archive HEAD → /tmp/review197copy): glm 3 passed;
  полный suite 22 passed; MODULE_PATH резолвится внутрь копии (проверено
  импортом тест-модуля из копии). Гигиена: репо при ревью не правилось,
  push нет.

## Не входит в этот ре-ревью

MIN-2/MIN-3/MIN-6 и NOTE-1…6 — по return-001 не блокировали переволну,
отложены на следующее касание (так и зафиксировано в impact §4).

## Вердикт: approve

Все шесть позиций возврата (MAJ-1, MAJ-2, MAJ-3, MIN-1, MIN-4, MIN-5)
закрыты с инструментальными доказательствами: восстановленные носители
байт-в-байт равны удаленным и гоняют боевой HTTPBridgeProvider; путь
теста hermetic (проверено прогоном из копии); spec-дельта согласована
с мастер-спекой программно (имя REM, MUST, ≤500, сценарии); трассировка
описывает построенное; фикс TypeError/None-guard подтвержден исполнением;
секретная директория вне build-context. Регресс: 22 passed в дереве и
22 passed из копии; openspec validate — valid. Остаток MIN-2/3/6/NOTE-* —
в следующее касание.
