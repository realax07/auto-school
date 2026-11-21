<!-- Reviewer-Delegation: deleg-s19-cr193 — spawned hermes chat session (role=code_reviewer); независимый ревьюер | объект: diff 2a16783..df64d0a | дата: 2026-11-19 | session: cli-pid 128439 (spawn-ledger; id CLI-сессии изнутри сессии недоступен) -->

# CR-19.3 (review-19.3-001) — «Главная» = ИИ-чат по макетам, оба носителя

Роль: code_reviewer (независимый ревьюер; автором диффа не являюсь). Ревью
вне flowctl: провениенс — эта шапка + sidecar-запись gate_runner
record-review (делает ПМ). Дерево: worktree wt-s19-ai-chat, ветка
feature/add-ai-chat-home. Объект: дифф 2a16783..df64d0a (коммиты 9dafce1 →
0cc091c → df64d0a), base 2a167836ca7d282218be70f415fdd30432aed4ab, head
df64d0a1979738625666888938220c396647234a. Требования:
requirements-ai-chat-home.md FR-19.1…FR-19.7; design.md Решение 3/4
(в т.ч. удаление мертвого wiring App.vue:1219 — MIN-3 arch-review 002).
Гигиена: писан только этот файл; код/тесты/макеты не правились; push нет.

## Состав диффа

`git diff --stat 2a16783..df64d0a` → ровно 4 файла, +292/−111:

- frontend/vue/src/pages/cabinet/App.vue (+232/−111 область правок):
  разметка #sec-home, ai-* состояние/wiring в setup, navTo display
  block→flex, удаление мертвого wiring плиток/заглушек;
- frontend/vue/cabinet.html: pre-boot-зеркало #sec-home («правило двух
  копий»);
- frontend/vue/src/pages/cabinet/styles.css: +83 строк в конце файла
  (ai-* правила, media ≤760px);
- openspec/changes/add-ai-chat-home/tasks.md: 19.3.1–19.3.3 → [x].

Тестовые файлы и макеты диффом НЕ тронуты (test_cabinet_page.py,
test_ui_playwright.py, test_mobile_tabbar.py, test_sidebar_unified.py —
вне диффа) → ослабления носителей в этом диффе невозможны по составу.

## Машинные проверки (команды + результат)

1. Юнит-носитель: `/home/hermes-bot/auto-school/.venv/bin/python -m pytest
   tests/unit/test_s19_ai_chat.py -v` → **14 passed, 1 warning in 14.86s**
   (warning — StarletteDeprecationWarning из fastapi/testclient, к диффу
   не относится).
2. Спеки: `openspec validate --all --strict` → **Totals: 28 passed,
   0 failed (28 items)**.
3. Дизайн-гарды страницы: `…/python -m pytest tests/web/test_cabinet_page.py
   -q` → **3 failed, 4 passed**: красные ровно три вербатим-гарда старого
   макета — test_cab_page_exists_and_marker_texts (падает на «Гига
   ГАИшник»), test_cab_page_structure_matches_mockup_verbatim,
   test_cab_page_keeps_mockup_stub_alert. Это ожидаемые красные (перевод
   гардов на новые макеты — зона 19.3.4, qa_automation), НЕ ослабления:
   сам файл в диффе отсутствует.
4. Сборка/dist: `git status` → working tree clean; dist/cabinet.html
   содержит ai-greet/ai-composer/ai-empty (pre-boot-копия), бандл
   dist/assets/cabinet-B4sN61Oe.js содержит копию App.vue (ai-spark,
   «Добрый день!») — dist свежий, обе копии в билде.
5. Wiring-шов сессии: token читается из sessionStorage 'session_token'
   в onMounted (App.vue:1176) ДО первого aiLoadHistory (App.vue:1201) —
   порядок корректен; aiApi шлет 'X-Session-Token' (как существующий
   localApi того же файла).

## FR-проверки

- **FR-19.1 (дословность, оба носителя)** — сверка посимвольно с макетами:
  spark SVG (оба path `M12 2v6M12 16v6M2 12h6M16 12h6` и
  `M4.9 4.9l4.2 4.2M14.9 14.9l4.2 4.2M19.1 4.9l-4.2 4.2M9.1 14.9l-4.2 4.2`,
  stroke #3ddc84, width 1.6) идентичны макетам в App.vue И cabinet.html;
  «Добрый день!»; подсказка «Спроси что угодно про обучение, экзамен или
  ПДД — помогу подготовиться»; плейсхолдер «Спроси что угодно про
  обучение, экзамен или ПДД...» — совпадают во всех четырех источниках.
  Геометрия из макетов: web spark 76 / hello 44 (−.5) / sub 17 (max-w 480)
  / gap 24 / padding 0 48; mobile 64 / 30 (−.3) / 15 (max-w 280) / 20 /
  32. .quick/.services-title/.tiles/.greet удалены в ОБОИХ носителях —
  быстрых кнопок и «СЕРВИСЫ» нет нигде. Отступление по стилям — MIN-1.
- **FR-19.2 (сайдбар/таб-бар не тронуты)** — по составу диффа: ни один
  селектор/файл сайдбара и таб-бара не правился (в styles.css только
  добавленные ai-* правила + #sec-home; StudentSidebar не тронут).
  navTo/routeHash без смысловых правок: единственное изменение — display
  'block'→'flex' для #sec-home (соответствует новому flex-лейауту) и хук
  aiLoadHistory при возврате на «Главную».
- **FR-19.3 (отправка/ожидание/ошибки)** — POST /api/ai/chat {message};
  на время ответа aiBusy: input disabled, send disabled, индикатор
  .ai-typing (aria-label «Ассистент печатает») — не «висит молча».
  Ошибки — человеческим текстом у поля, без кодов: шейп {ok,error} —
  доверенный текст (String-каст), шейп 422 {detail:[…]} / сеть / битый
  JSON → общий человеческий («Не получилось отправить сообщение…»).
  401/403 → handleAuthFail → toLogin, пузырь пользователя снят. Сверено
  с backend/ai/routes.py: при ProviderError сервер возвращает 503
  {ok:false, error: человеческий текст} и НЕ сохраняет обмен — клиентская
  механика «снять пузырь + вернуть текст в поле» согласована с сервером
  (рассинхрона истории нет).
- **FR-19.4 (состояния)** — класс ai-empty/ai-has-msgs на #sec-home из
  aiMessages.length; приветствие v-show="!aiMessages.length"; есть
  история → пузыри user/assistant. В pre-boot статичный ai-empty — до
  гидрации виден пустой чат, корректно.
- **FR-19.5 (подхват истории)** — aiLoadHistory при монтировании и при
  navTo на «Главную» (глубина 14 дней — серверная, клиенту не доверяется:
  клиент берет messages как даны).
- **FR-19.7 («+» и отправка)** — .ai-plus disabled + aria-label «Вложения
  — скоро» + подпись «Скоро»; .ai-send рабочая, disabled только на busy.
- **FR-19.6 (темы)** — вне диффа (промпт провайдера, волна 19.2).

## Adversarial (Саботажник / Новичок / Security)

1. **Stored XSS (Security, MAJ-критерий)** — grep по всему диффу на
   `innerHTML|v-html|insertAdjacentHTML|outerHTML|document.write` → 0
   совпадений. Ответ LLM и тексты ученика попадают в DOM ТОЛЬКО через
   интерполяцию Vue `{{ m.text }}` / `{{ aiError }}` (экранирование) и
   textContent (onMe, null-guard). pre-boot — статичная разметка без
   скриптов. Плейсхолдера/надписи — литералы. Чисто.
2. **Wiring (Новичок)** — токен из sessionStorage (тот же ключ, что у
   всей страницы); оба шейпа ошибок обработаны; невалидный JSON и сеть
   дают {status:0|…, data:null} → общий человеческий текст. Ответ 200 ok
   без reply не бывает по контракту (TC-S19-002); формально пустой
   «пузырь» при нарушении контракта — за пределами риска (не заводится).
3. **Мертвые ссылки на удаленный DOM (Саботажник)** — после удаления
   .greet/.tiles/.quick в App.vue не осталось живых обращений: onMe —
   querySelector('.greet b') с null-guard (осознанный no-op, сайдбар
   эмитит @me всегда), alert-заглушки .tile/.quick/.send удалены вместе с
   разметкой (MIN-3 arch-review 002 закрыт). Остальные ссылки — на
   существующие id.
4. **Hit-targets ≥44px (пересчет по CSS, не по отчету)** — web:
   .ai-plus 48×48, .ai-send 54×54; mobile (media ≤760): .ai-plus 44×44,
   .ai-send 48×48 — все ≥44 ✓ (заявленные 44/48/48/54 подтверждаются).
   Поле ввода — строка 24/26px высотой по геометрии утвержденного макета
   (текстовое поле во всю ширину, не тап-контрол).
5. **Композер прижат** — web: #sec-home height calc(100svh − 142px)
   сходится с фактическими правилами (.frame padding 26/40, footer
   margin-top 40 + ~36 высота): 26+40+40+36 ≈ 142; композер над футером,
   зазор 40px — осознанное отступление от макета (в макете 48px до низа
   вьюпорта), задокументировано в CSS-комментарии, вопрос ПМ заказчику —
   не нахожу дефектом. mobile: calc(100svh − 269px), арифметика
   комментария сходится (84 шапка + 40 margin футера + 57 футер + 88
   резерв таб-бара); композер над зоной таб-бара без перекрытия; min-height
   420/360 страхуют короткие вьюпорты.
6. **Hash-навигация/шина событий** — ветки #/my-requests, #/wallet,
   #/pdd-signs в routeHash не тронуты (дифф касается только display
   #sec-home и хука истории); @me/@tab сайдбара без изменений.
7. **Правило двух копий** — DOM чата присутствует в обоих носителях
   (App.vue-шаблон и cabinet.html pre-boot) и в обоих артефактах сборки
   (бандл + dist/cabinet.html). Различия копий — только динамические узлы
   (.ai-error, .ai-typing, биндинги/обработчики), которых до гидрации не
   существует по определению; статичное зеркало дословное.

## Findings

- **MIN-1** (frontend/vue/src/pages/cabinet/styles.css, правило
  .ai-input-box): web-зазор между полем и кнопками gap:14px против 18px
  в макете home-chat-web.html (мобильный 14px — совпадает). FR-19.1
  требует «стили дословно»; отклонение мелкое, в CSS-комментарии не
  оговорено (в отличие от геометрии композера). Не блокирует; выровнять
  при следующем касании или зафиксировать как осознанное.
- **MIN-2** (openspec/changes/add-ai-chat-home/tasks.md 19.3.3 [x];
  design.md «Решение 3»): документы заявляют отправку «через
  src/shared/api.js», фактически — локальный Promise-хелпер aiApi внутри
  App.vue (в src/shared/api.js есть пригодный apiSend с X-Session-Token,
  но callback-стиль). Код честно документирует выбор в комментарии;
  расхождение — трассировка/формулировка задачи, не поведение. Исправить
  формулировку или перевести на apiSend — решать ПМ вне этого ревью.
- Информационно (не findings): web composer padding-bottom 16px и mobile
  12px против 48/16px макета — осознанная привязка «до низа контентной
  области, а не вьюпорта» (задокументировано; зазор 40px до футера —
  вопрос ПМ заказчику по делегированию); .ai-actions align-items:flex-end
  против center в макете — следствие добавленной подписи «Скоро»
  (FR-19.7, в макете подписи нет — осознанное отличие, требование
  Заказчика).

MAJ не найдены. По прецеденту review-19.2-001 (approve с нумерованными
MIN) — оба MIN не блокируют приемку волны 19.3 в части кода; носители
e2e/design-guard (19.3.4) остаются обязательным условием закрытия спринта.

## Вердикт: approve
