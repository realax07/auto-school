<!-- Reviewer-Delegation: deleg-s18-cr-external | независимый код-ревьюер (не автор диффа) | итерация 003 (финальная) | дифф: 79a180d..1d366bc (amend: return-коммит 3a70025 заменен 1d366bc — review-002 + mapping + честное сообщение) | ветка: feat/s18-mobile | дата: 2026-11-17 -->

# Code review 003: add-mobile-adaptive — финальная итерация

Периметр: один коммит после review-002 (дерево ревью-002 = 79a180d) — 1d366bc,
созданный amend-ом return-коммита 3a70025. Кодовая дельта после 79a180d —
нулевая: 1d366bc содержит только code-reviews/add-mobile-adaptive/
(review-002, 135 строк, + review-mapping.json). Сообщение 1d366bc честное:
прямо признает, что три из четырех пунктов сообщения 79a180d были задвоением
уже существовавших правок, и называет фактический дифф 79a180d — только
tests/web/test_ui_playwright.py. Оба утверждения сверены с деревом (см. ниже).
Пункты проверки ПМ на итер.003 (история, стили, гейты, целостность документов)
— все четыре подтверждены реальными прогонами. Однако статусы находок на HEAD
не изменились с review-002: ни одна правка из «пути к merge» review-002 не
выполнена.

## Проверка пунктов ПМ (итер.003)

1. История линейная и честная — ПОДТВЕРЖДЕНО. 9a26187..1d366bc — три коммита
   без merge. NB сообщения 1d366bc сверен с фактами: git show --stat 79a180d =
   1 файл tests/web/test_ui_playwright.py (+28/−15) — совпадает с формулировкой
   «фактический дифф коммита: только tests/web/test_ui_playwright.py»;
   «контраст fine-text/fine-line !important» — пре-экзистинг 7533856
   ([s17-fix] читабельность жёлтой карточки), т.е. задвоение подтверждено;
   «tasks strict 27/27» — 2555a3d (раунд 001); «носитель fineRenderLines» —
   пре-экзистинг (нулевой дифф к main). Требование MIN-5 «убрать ложные пункты
   из учетных текстов» — ВЫПОЛНЕНО (amend; история больше не содержит
   фиктивных пунктов).
2. Стили — ПОДТВЕРЖДЕНО: frontend/vue/src/pages/cabinet/styles.css:416
   .zn-modal .fine .fine-text{…color:#3d3427 !important…}, :417 .zn-modal
   .fine .fine-line{…color:#3d3427 !important…}; hit-targets: min-height:44px
   !important на styles.css:469 (.act), :499 (.bk-actions .bk-act), :509
   (.wal-actions .wal-btn) — все на месте, скоупы media ≤760px.
3. Гейты экспресс (реальные прогоны на HEAD = 1d366bc, дерево чистое):
   build OK 2.09s; budgets OK (страниц: 14); pytest tests/unit tests/web -q =
   211 passed (3:09); openspec validate --all --strict = 27 passed / 0 failed.
   Совпадение с базой review-002 (211 passed, 27/27) — регресса нет.
4. review-002 + mapping не искажены — ПОДТВЕРЖДЕНО: содержимое совпадает с
   вердиктом итер.002 (return), файлы доставлены amend-ом 1d366bc вместо
   3a70025 без правок смысла.

## Статусы находок review-002 на HEAD = 1d366bc

- MAJ-1 (top-bar ≤760px по мокапам/спеке): ОТКРЫТ — третью итерацию подряд,
  не тронут ни одним коммитом итер.002/003. Все четыре доказательства на
  месте: specs/mobile-adaptive/spec.md:11 — «…MUST … через раздел «Профиль»
  и top-bar (инициалы)»; design/mocks/mobile/ — class="tb" во всех 21 мокапах
  (замер grep: 21 из 21); MobileTabBar.vue:30 — «top-bar не добавляем»;
  decisions/ — пусто. Ни реализация (а), ни решение Заказчика (б) из «пути к
  merge» review-002 не выполнены. По-прежнему ЕДИНСТВЕННЫЙ блокер партии.
- MIN-1 (hit-targets ≥44px): остается ЗАКРЫТ (styles.css:469/499/509
  !important подтверждены на HEAD; рантайм-замеры итер.002: .act=44,
  .bk-act=44, .wal-btn=47). Замечание о трекинге: и в задании на итер.003 ПМ
  называет hit-targets «MAJ-1» — вторая часть MIN-5 (выправление трекинга:
  MAJ-1 = top-bar, hit-targets = MIN-1) НЕ выполнена.
- MIN-2 (документальные остатки): вторая половина НЕ закрыта:
  review-18.4.3-001.md:34 — «flow_check — без ошибок» на месте (файл не
  менялся с 5f70714), при факте, воспроизведенном сегодня:
  python3 scripts/flow_check.py . → FLOW-ERROR J10 «11 закрытых dev-задач без
  code-review» (1 ошибка). Ложная цитата в MIN-2 review-001 (строка 152) —
  без изменений (задокументирована в review-002, править review-001 не
  требуется).
- MIN-3 (мертвое media instructor-choice): остается ЗАКРЫТ
  (instructor-choice/styles.css, @media ≤760px — только валидные правила
  aside.side/.frame, мертвого правила нет).
- MIN-4 (геометрический e2e): остатки НЕ закрыты (тест не менялся с 79a180d):
  (а) .act под `if acts.count():` (test_ui_playwright.py:5253) — на сценарии
  теста assert не выполняется никогда; (б) .bk-act в геометрия-тесте не
  меряется; (в) носители «История кошелька на 390px», «Слоты недели на
  390px», «Верх контента на десктопе», «Админ-транзакции на 390px» — в
  спецификации есть (spec.md:25/36/59/82), носители не добавлены.
- MIN-5 (фиктивные пункты учета): первая часть — ЗАКРЫТА amend-ом 1d366bc
  (честный NB, диффы сверены — см. п.1). Вторая часть (трекинг) — НЕ закрыта:
  учет ПМ по-прежнему ведет hit-targets как «MAJ-1» (задание на итер.003:
  «MAJ-1 hit-targets min-height:44px !important»).

## Новых дефектов не обнаружено

Кодовая дельта после 79a180d отсутствует; гейты green; документы доставлены
без искажений; dist пересобран перед прогонами (рекомендация review-002
выполнена). Замечание по среде (не код, на результат не повлияло): на
агентской машине venv был без pytest/playwright и с chromium-1248 — прогон
восстановлен установкой pytest==9.1.1 + playwright, доустановкой
chromium-headless-shell 1255 и LD_LIBRARY_PATH=~/.cache/pw-libs/… ; итог
211 passed совпал с базой.

## Прогоны (реальное исполнение, дерево HEAD = 1d366bc, дерево чистое)

```
npm run build (frontend/vue) -> OK (2.09s)
npm run check:budgets -> OK: страниц: 14, бюджеты NFR-26 соблюдены
pytest tests/unit tests/web -q (LD_LIBRARY_PATH pw-libs, chromium headless
  shell) -> 211 passed (3:09) — совпадает с базой review-002
openspec validate --all --strict -> Totals: 27 passed, 0 failed (27 items)
python3 scripts/flow_check.py . -> 1 ошибка: J10 «11 закрытых dev-задач без
  code-review» (18.1.1…18.4.3) — подтверждает: approve в партии не выдавался
git show --stat 79a180d -> 1 файл tests/web/test_ui_playwright.py (+28/−15)
git show --stat 1d366bc -> review-002 (135 строк) + review-mapping.json
```

## Таблица задач 18.1.1–18.4.3 (итерация 003)

Кодовая дельта итерации 003 — нулевая (только code-reviews/*); статусы задач
наследуются от review-002 без изменений.

| Задача | Статус на 003 |
|---|---|
| 18.1.1 MobileTabBar + интеграция | return — MAJ-1 (top-bar) открыт третью итерацию подряд |
| 18.1.2 Сокрытие desktop-сайдбара | approve-техн. (наследуется); партия в return по MAJ-1 |
| 18.2.1 Главная/Кошелек | approve-техн. (наследуется, MIN-1 закрыт) |
| 18.2.2 Мои заявки | approve-техн. (остаток MIN-4(а), не блокер) |
| 18.2.3 Мои брони | approve-техн. (остаток MIN-4(б), не блокер) |
| 18.2.4 модалки bottom-sheet | approve-техн. |
| 18.3.1 ПДД-разделы | approve-техн. |
| 18.3.2 Инструктор кабинет/документы | approve-техн. |
| 18.3.3 Админка + публичные | approve-техн. |
| 18.4.1 Носители | approve-техн. (остаток MIN-4(в)) |
| 18.4.2 e2e mobile 390 | approve-техн. с остатком MIN-4 (а,б,в) |
| 18.4.3 Карта/бюджеты/strict | return — MIN-2 вторая половина (строка 34 файла волны), MIN-5.1 трекинг |

Покрытие J10: последняя итерация каждой задачи — rev 003 с вердиктом return →
задачи по-прежнему не покрыты, ворота не пройдены. Выдать approve в этом
состоянии означало бы зафиксировать в учете «открытых MAJ/MIN нет» вопреки
дереву (spec.md:11 + 21/21 мокапов + пустой decisions/) — та же категория
нарушения, что MIN-5 (расхождение учета с фактами), уровнем выше.

## Что делать к итерации 004 (путь к merge — без изменений, кроме MIN-5)

1. MAJ-1: (а) .tb-шапка ≤760px на ученических экранах по мокапам (лого +
   инициалы, sticky, поверх контента) + носитель/кадр e2e, или (б) решение
   Заказчика в decisions/ с правкой spec.md/proposal.md/мокапов. Это
   по-прежнему ЕДИНСТВЕННЫЙ блокер партии.
2. MIN-2: поправить строку 34 review-18.4.3-001.md на факт (flow_check дает
   J10 до approve независимого ревью).
3. MIN-4: посев заявок/брони через API или безусловный N>0-assert для .act;
   замер .bk-act; носители четырех сценариев (spec.md:25/36/59/82).
4. MIN-5.1 (единственный остаток MIN-5): выправить трекинг находок у ПМ:
   MAJ-1 = top-bar, hit-targets = MIN-1 (закрыт). Месседж 79a180d уже
   исправлен (1d366bc) — не повторять.

## Вердикт: return (MAJ-1)

Все четыре проверочных пункта ПМ выполнены и подтверждены реальными прогонами:
история линейная и честная (NB 1d366bc сверен с фактическими диффами),
strong-правила fine-text/fine-line !important на месте (styles.css:416/417,
как и 44px-правила 469/499/509), гейты green (build 2.09s, budgets 14
страниц, 211 passed, strict 27/27), review-002/mapping доставлены без
искажений. MIN-5 в части коммит-месседжа закрыт — фиктивных пунктов в истории
больше нет, это засчитано. Но вердикт итерации определяется статусом находок,
а он не изменился: top-bar (спека MUST + все 21 мокапов) не реализован и не
отменен решением Заказчика; MIN-2 (строка 34 файла волны) и MIN-4 (а,б,в) не
тронуты; трекинг MAJ-1 у ПМ не выправлен. Формула «открытых MAJ/MIN нет»
дереву не соответствует — APPROVE на этом основании выдан быть не может.
Merge после закрытия MAJ-1 и ревью итерации 004.

Commit: 1d366bc4129ecee7f32712ea686c6bc3e59c58d1

<!-- Reviewer-Delegation: deleg-s18-cr-external | независимый код-ревьюер (не автор диффа) | итерация 004 | дифф: 7e3a64f..623ed9a (фикс-дельта MAJ-1: MobileTabBar.vue +17/-2, test_mobile_tabbar.py +2, test_ui_playwright.py +14) | ветка: feat/s18-mobile | дата: 2026-11-17 -->

# Итер.004 2026-11-17: return (MAJ-1 ЗАКРЫТ; новые MAJ-2/MAJ-3)

Финальная проверка блокера MAJ-1 (top-bar ≤760px по мокапам/спеке), заявленного
в 623ed9a. Все прогоны — реальное исполнение на пересобранном dist
(npm run build, 2.75s OK; dist пересобран перед прогонами, рекомендация
итер.002 соблюдена). Проверка живая, не статическая: playwright-проба 390×844
и 1440×900 на uvicorn+fresh DB (изолированный сервер фикстуры, студент
Смирнова О.П. через /api/register+/api/auth/login).

## Проверка задания итер.004 (4 пункта)

1. «top-bar рендерится, инициалы видны на нескольких разделах» — ДА,
   подтверждено живым прогоном: инициалы «СО» (data-test=mtop-ava, count=1,
   visible) на каждом из проверенных состояний — SPA-клики по таб-бару
   (Главная → Записи → Обучение-шит → Знаки → Кошелек → Профиль) И
   deep-links /cabinet#/pdd-signs, #/pdd-tickets, #/wallet, #/my-bookings,
   #/my-requests, а также страница /instructor-choice (см. оговорку MAJ-2
   по ее раскладке). Клик по АВАТАРУ top-bar открывает Профиль-шит:
   ФИО «Смирнова Ольга Павловна» + «Выйти», закрытие по × — ок (проба).
   Cabinet: .mtop на всю ширину 390px; при scroll=0 контент начинается
   на 26px ниже низа top-bar (перекрытия нет). Desktop 1440×900: .mtop
   отсутствует (count=0) — desktop не затронут. Коммитный e2e
   test_mobile_topbar_initials_visible (deep-link #/pdd-signs на 390px)
   green; прогон -k "topbar or mobile": 4 passed (все мобильные e2e).
   Носитель test_mobile_tabbar.py: 8 passed.
2. «Спека mobile-adaptive сценарий top-bar (инициалы) закрыт» — ДА:
   specs/mobile-adaptive/spec.md:10–11 требование дополнено
   «...через раздел «Профиль» и top-bar (инициалы)» (термин «сценарий» тут
   условен — требование в тексте Requirement, отдельного Scenario не
   заводилось; функциональное покрытие коммитным e2e + пробами есть).
   Расхождение итер.001–003 (spec MUST без реализации) устранено.
3. «Новых дефектов в top-bar нет» — НЕТ, найдены два MAJ и два MIN
   (ниже). Один из них — структурный дефект самого top-bar (MAJ-3),
   второй — раскладка страницы-носителя instructor-choice (MAJ-2).
   z-index-конфликтов не найдено: шиты .mtab-backdrop z=80 выше top-bar
   z=55 выше контента; elementFromPoint в зоне аватара — сам аватар.
4. «История: amend 1d366bc честен» — ПОДТВЕРЖДЕНО повторно: git show
   79a180d --stat — фактический дифф действительно только
   tests/web/test_ui_playwright.py (+28/-15), месседж 1d366bc называет
   ровно это и помечает задвоенные пункты 79a180d. История линейная,
   623ed9a содержит ровно заявленное (3 файла, без посторонних).

## Статус MAJ-1: ЗАКРЫТ

Реализация соответствует мокапам v3 (mobile-home.html .tb: лого
«СберАвтошкола» + аватар-кружок 32px с инициалами; в мокапе .av 30px,
реализация 32px — в допуске) и спеке (инициалы в top-bar на каждом
разделе; ФИО+«Выйти» — в Профиль-шите, доступном и из таб-бара, и из
top-bar). ФИО грузится /api/auth/me при mount (MobileTabBar.vue:195) —
видно на любом разделе без открытия шита. Совместно с проверками 1–4
выше — блокер итер.001–003 снят. Это засчитано.

## Новые дефекты (найдены живой пробой итер.004)

- MAJ-2 (носитель instructor-choice, ≤760px): страница ДВУХКОЛОННАЯ на
  390px. Замер: .app grid 236px+1fr сохранился (instructor-choice/
  styles.css:90, media-замены single-column нет), .mtab-root → колонка
  236px (.mtop width=236, не 390), .frame → x=236 width=256,
  scrollWidth=492 при viewport 390 — горизонтальный скролл, .kicker
  (x=252..476) обрезан, контент сжат. Причина — РЕГРЕСС 2555a3d: из
  instructor-choice/styles.css удалена ЦЕЛАЯ строка media ≤760px, включая
  живую часть .app{grid-template-columns:1fr}; в cabinet аналогичная
  замена выполнена (styles.css:203) — несимметричная зачистка. Упрек
  себе: review-002/003 закрывали MIN-3 «мертвое правило удалено»
  статически и не заметили, что удалили и живую половину; дефект
  существовал с 2555a3d (вне top-bar контент тоже стоял в узкой
  колонке), но в живом виде впервые пойман пробой итер.004. Фикс:
  вернуть @media(max-width:760px){.app{grid-template-columns:1fr}} в
  instructor-choice/styles.css (+ носитель-замер в e2e).
- MAJ-3 (top-bar, sticky): sticky НЕ РАБОТАЕТ — при scrollY=600 на
  #/pdd-signs .mtop rect.top = −600 (уехал со страницей; elementFromPoint
  в шапке вьюпорта возвращает zn-grid). Мокапы 21/21 задают
  .tb{position:sticky;top:0;z-index:40} — дизайн «контент уезжает под
  полупрозрачную шапку» потерян. Причина: .mtop вложен в .mtab-root —
  grid-item кабинета высотой 57px (строчный grid, .mtabs fixed вне
  потока), sticky не может выйти за границы родителя. CSS position:sticky
  (MobileTabBar.vue:228) скопирован из мокапа дословно, но структурно
  мертв. Фикс структурный (например, display:contents на .mtab-root в
  media ≤760px или перенос .mtop прямым ребенком .app) — на обеих
  страницах-носителях; после фикса закрепить живой замер в e2e
  (scrollY>0 → mtop rect.top==0), сейчас sticky-поведение ничем не
  покрыто. Градация MAJ по доктрине «мокапы — источник дизайна»
  (та же, что делала MAJ-1 блокером).
- MIN-6 (doc-дрейф): MobileTabBar.vue:29–31 — «top-bar не добавляем —
  верхний отступ контента ... на всех ширинах» и :37–40 — «лениво при
  ПЕРВОМ открытии Профиля ... дубля запросов нет» противоречат
  реализации (top-bar добавлен; loadMe() при mount, строка 195).
  Комментарии шапки компонента привести к факту.
- MIN-7 (desktop-перф): loadMe() при mount выполняется и на desktop —
  компонент смонтирован и при >760px (скрыт только CSS, BUG-070-механика),
  поэтому каждый desktop-загруз cabinet/instructor-choice дает ЛИШНИЙ
  GET /api/auth/me поверх запроса StudentSidebar. Guard по visible.value
  (или загрузка при первом visible) — дубль убрать.

## Прежние MIN (итер.003) — не тронуты фикс-коммитом 623ed9a

- MIN-2: review-18.4.3-001.md:35 — «flow_check — без ошибок» на месте
  (файл волны не правлен). Открыт.
- MIN-4 (а/б/в): посев .act/.bk-act, носители 4 сценариев — не тронуты.
  Открыт.
- MIN-5.1 (трекинг MAJ-1 у ПМ): из дерева не верифицируем, статус прежний
  «не подтверждено исправление» — снять при approve.

## Прогоны (реальное исполнение, дерево HEAD = 623ed9a)

```
npm run build (frontend/vue) -> OK (2.75s), dist пересобран до прогонов
pytest tests/web/test_mobile_tabbar.py tests/web/test_ui_playwright.py
  -k "topbar or mobile" -> 8 passed (носитель) + 4 passed (e2e mobile,
  вкл. test_mobile_topbar_initials_visible)
живая проба 390×844 (playwright, uvicorn+fresh DB, студент через API):
  инициалы «СО» на 6 deep-link/SPA состояниях кабинета + instructor-choice;
  аватар→Профиль-шит: ФИО+«Выйти», закрытие ×; GAP контент/top-bar = 26px;
  desktop 1440×900: .mtop count=0
  instructor-choice: .mtop=236px, .frame x=236 w=256, scrollWidth=492>390
    (MAJ-2)
  sticky: scrollY=600 → .mtop top=−600 (MAJ-3); мокапы 21/21 .tb sticky
    (grep design/mocks/mobile: class="tb" в 21 файлах)
```

## Что делать к итерации 005

1. MAJ-2: media single-column в instructor-choice/styles.css + e2e-замер.
2. MAJ-3: рабочий sticky top-bar на обеих страницах-носителях + e2e-замер
   (scrollY>0 → rect.top==0).
3. MIN-6: комментарии MobileTabBar.vue по факту. MIN-7: guard loadMe.
4. MIN-2 (строка 34 файла волны), MIN-4 (а/б/в), MIN-5.1 — прежние
   остатки, не блокеры merge по отдельности, но должны быть закрыты к
   финальному approve.

## Вердикт: return

Блокер трех итераций MAJ-1 (top-bar с инициалами) реализован и подтвержден
живыми прогонами на всех разделах кабинета и deep-links — ЗАКРЫТ, это
зафиксировано. Однако проверка «новых дефектов нет» не пройдена: MAJ-2
(instructor-choice двухколоночный на 390px, регресс 2555a3d — scrollWidth
492 при 390, top-bar 236px) и MAJ-3 (sticky top-bar мертв — поведение
21/21 мокапов потеряно) открыты; оба не закрывают, а прямо касаются
предмета MAJ-1 на мобильных ширинах. Merge невозможен до их закрытия.
Плюс: MIN-6/MIN-7 (комментарии, desktop-дубль /me), прежние MIN-2/MIN-4
не тронуты. Ожидаемый объем итер.005 — одна media-строка, структурный
фикс sticky, два e2e-замера, правка комментариев.

Commit: 623ed9a

<!-- Reviewer-Delegation: deleg-s18-cr-external | независимый код-ревьюер (не автор диффа) | итерация 005 | дифф: 623ed9a..97fdca7 (фикс-дельта: MobileTabBar.vue +12/−8, instructor-choice/styles.css +1, test_ui_playwright.py +5) | ветка: feat/s18-mobile | дата: 2026-11-17 -->

# Итер.005 2026-11-17: return (MAJ-2 ОТКРЫТ — мертвый селектор; MAJ-3 механика ок, но новые MAJ-4/MAJ-5; MIN-7 ЗАКРЫТ)

Проверка живая, не статическая: playwright-проба 390×844 и 1440×900 на
uvicorn+fresh DB (изолированный сервер, студент Смирнова О.П. через
/api/register+/api/auth/login), dist пересобран до прогонов (npm run build,
2.81s OK). Подтверждение статикой: элемент .ic-wrap не существует ни в одном
шаблоне (grep html/vue/js по дереву — только сама CSS-строка), контейнер
instructor-choice — .app (instructor-choice/App.vue:21, styles.css:90).

## Проверка задания итер.005 (критерии живой пробы)

1. «/instructor-choice scrollWidth ≤390» — НЕТ. scrollWidth=492 при
   viewport 390; .app grid = «236px 154px» (не сложился), .frame x=236
   w=256, .kicker x=252 w=224 (правый край 476 — обрезан). Числа 1:1 как в
   итер.004. Причина: коммит добавил `.ic-wrap{grid-template-columns:1fr}`
   (styles.css:114) — селектор МЕРТВЫЙ: класса ic-wrap нет ни в одном
   шаблоне; требовалось `.app{grid-template-columns:1fr}` (прямо записано
   в «Что делать к итерации 005», п.1). Требуемый e2e-замер scrollWidth на
   /instructor-choice НЕ добавлен. MAJ-2 ОТКРЫТ; формулировка
   коммит-месседжа «сетка 1fr возвращена» не соответствует дереву.
2. «/cabinet#/pdd-signs wheel 400 → .mtop y≈0» — ДА, механика fixed
   работает: scrollY=400 → .mtop top=0 (и на instructor-choice тоже y=0);
   новое e2e-assert в test_s18_mobile_geometry_hit_targets green
   (-k «mobile or topbar or geometry or s18»: 5 passed). НО фикс внес два
   новых дефекта — MAJ-4 и MAJ-5 (ниже): полоса сжалась до 195px, контент
   под шапкой при scroll=0.
3. «desktop 1440 — .mtop отсутствует, раскладка не сломана» — ДА: .mtop
   count=0, .mtabs count=0, .mtab-root display:none на обеих страницах;
   .app grid «236px 1204px», side flex, .frame x=236 (cabinet) / x=326
   (choice, margin auto), scrollWidth=1440. Desktop не задет.
4. MIN-2 (заявление ПМ «откатил r17 к чистой версии и обновил
   формулировку») — НЕ ПОДТВЕРЖДЕНО в части формулировки:
   review-18.4.3-001.md:34–35 «flow_check — без ошибок» на месте, файл не
   менялся ни в одной ветке (единственный коммит 5f70714); в
   test-model/reviews/ каталога add-mobile-adaptive не существует; живой
   факт сегодня: python3 scripts/flow_check.py . → 1 ошибка J10 «11
   закрытых dev-задач без code-review». Откат r17 к чистой версии — ФАКТ,
   но это s17-fix d9e7353 (восстановление 99602d0), совершен до спринта
   s18 и к строке 34 отношения не имеет (corpus content/pdd чист,
   проверено git status). MIN-2 ОТКРЫТ.

## Новые дефекты (живая проба итер.005)

- MAJ-4 (top-bar, ширина): .mtop сжался до 195px вместо полосы на всю
  ширину. Причина: position:fixed без width/left/right дает shrink-to-fit
  по контенту; «max-width:390;margin:0 auto» ширину не задает, margin auto
  без left/right — no-op (замер x=0). Мокапы 21/21: .tb — блочный
  space-between во всю ширину (бренд у левого края, аватар у правого);
  свойство «.mtop на всю ширину 390px» было проверено и зачтено при
  закрытии MAJ-1 (итер.004). Сейчас аватар при x≈163 вместо правого края;
  elementFromPoint(195,20) после wheel возвращает zn-grid — правая половина
  шапки отсутствует, контент виден и кликабелен в «щели». Градация — та же
  доктрина «мокапы — источник дизайна», что MAJ-1/MAJ-3.
- MAJ-5 (перекрытие при scroll=0): fixed вывел .mtop из потока,
  компенсации padding-top нет. Cabinet: .frame top=0, контент с 26px
  (padding .frame) — полоса 26..57 (31px контента, greet-заголовок) ПОД
  шапкой при scroll=0; instructor-choice: .kicker (top=20) перекрыт на
  37px. Итер.004 проверял «при scroll=0 контент начинается на 26px ниже
  низа top-bar (перекрытия нет)» — свойство утрачено. Фикс: в ≤760px
  padding-top контента ≥ высоты шапки (обе страницы-носителя).

## Статус прежних находок

- MIN-6: ПОЛМЕРЫ + НОВЫЙ МУСОР. Комментарии 181–182 и 197–198 приведены к
  факту — зачтено. Но шапка 37–40 («лениво при ПЕРВОМ открытии Профиля…
  дубля запросов нет») не тронута — именно на нее указывал итер.004
  (противоречит: loadMe при mount при visible; на desktop /me вообще нет).
  Правка 29–31 сама внесла брак: «Профиль» — bottom-sheet с ФИО и «Выйти»
  продублирована дважды, сирота «= отступ логотипа ~25px…» висит без
  предложения. ОТКРЫТ.
- MIN-7: ЗАКРЫТ (подтверждено кодом и живым замером запросов): guard
  if (visible.value) loadMe() при mount + loadMe при входе в мобильную
  ширину (mq change); desktop 1440 → 1 запрос /api/auth/me на загрузку
  кабинета (только StudentSidebar, лишнего нет), .mtop=0; mobile 390 →
  2 запроса (сайдбар + top-bar), инициалы «СО» в шапке.
- MIN-4 (а/б/в): не тронуты (посев .act/.bk-act, носители 4 сценариев).
  NB: пункт коммит-месседжа «MIN-4 sticky-замер e2e» — перепутанная
  трассировка: sticky-замер — требование MAJ-3 (итер.004, п.2 «Что
  делать»), а не MIN-4. Открыт.
- MIN-5.1 (трекинг ПМ): из дерева не верифицируем; дополнительно сам
  коммит-месседж итер.005 содержит недостоверные пункты («сетка 1fr
  возвращена», «MIN-6 комментарии по факту») — та же категория «расхождение
  учета с фактами», теперь в фикс-коммите.

## Прогоны (реальное исполнение, дерево HEAD = 97fdca7, dist пересобран)

```
npm run build (frontend/vue) -> OK (2.81s)
npm run check:budgets -> OK: страниц: 14, бюджеты NFR-26 соблюдены
openspec validate --all --strict -> Totals: 27 passed, 0 failed (27 items)
pytest tests/unit tests/web -q -> 212 passed (3:15) = база 211 + 1
  (test_mobile_topbar_initials_visible, 623ed9a) — регресса нет
playwright-проба 390×844: ic scrollWidth=492, grid «236px 154px» (MAJ-2);
  wheel 400: cabinet y=0, choice y=0; .mtop w=195 (MAJ-4);
  scroll=0: перекрытие контента 57px (cab) / 37px (ic) (MAJ-5);
  /me: desktop=1 (сайдбар), mobile=2 (MIN-7 закрыт)
playwright-проба 1440×900: .mtop/.mtabs=0, root display:none,
  grid «236px 1204px», side flex, scrollWidth=1440
python3 scripts/flow_check.py . -> 1 ошибка J10 (11 задач без review)
grep ic-wrap по дереву: только styles.css:114 (+ dist css) — селектор мертв
```

## Что делать к итерации 006

1. MAJ-2: селектор .app, не .ic-wrap: @media(max-width:760px){.app{grid-
   template-columns:1fr}} в instructor-choice/styles.css + e2e-замер
   scrollWidth ≤390 на /instructor-choice.
2. MAJ-4: .mtop задать полосу: left:0;right:0 (или width:100%) без
   shrink-to-fit; margin/max-width убрать или дать осмысленное поведение.
3. MAJ-5: компенсировать высоту шапки в ≤760px (padding-top ≥ 57px на
   .frame обеих страниц) — «контент к верху» НИЖЕ шапки, перекрытия при
   scroll=0 нет; e2e-замер (контент top ≥ mtop bottom при scroll=0).
4. MIN-6: шапка 37–40 по факту; почистить дубль и сироту 29–31.
5. MIN-2 (строка 34 файла волны — факт J10), MIN-4 (а/б/в) — прежние
   остатки, закрыть к финальному approve.

## Вердикт: return

Гейты green (build 2.81s, budgets 14, strict 27/27, 212 passed), MIN-7
закрыт и подтвержден замером запросов, механика прилипания (fixed)
работает — это зачтено. Но: MAJ-2 не закрыт — правка целя в несуществующий
.ic-wrap является мертвым кодом, страница по-прежнему двухколоночная
(scrollWidth 492 при 390), коммит-месседж утверждает обратное; взамен
внесены два новых MAJ на той же шапке (195px вместо полосы — потеряно
свойство, зачтенное при закрытии MAJ-1; контент под шапкой при scroll=0 —
потеряно свойство, проверенное итер.004). MIN-6 закрыт наполовину, правка
внесла новый брак в комментарии; MIN-2 не тронут (заявленное ПМ
«обновление формулировки» в дереве/каталогах не существует; откат r17 —
это s17-fix, к строке 34 отношения не имеет). Merge невозможен. Ожидаемый
объем итер.006 — один селектор, ширина полосы, padding-top, чистка
комментариев, три e2e-замера.

Commit: 97fdca7

<!-- Reviewer-Delegation: deleg-s18-cr-external | независимый код-ревьюер (не автор диффа) | итерация 006 | дифф: рабочее дерево поверх 97fdca7 БЕЗ фикс-коммита (MobileTabBar.vue +1/−1 CSS .mtop, cabinet/styles.css +1/−1 .frame padding, instructor-choice/styles.css +2/−1 media ≤760) | ветка: feat/s18-mobile | дата: 2026-11-17 -->

# Итер.006 2026-11-17: return (MAJ-2 ОТКРЫТ 3-ю итерацию — правило снова не в тот контейнер: .layout no-op дубль ≤1024, .app «236px 154px», scrollWidth 465 при 390; MAJ-4 ЗАКРЫТ; MAJ-5 ЗАКРЫТ только на cabinet — choice kicker −37px; MIN-6 не тронут; pytest RED — носитель 26px vs 84px)

Проверка живая: playwright-проба 390×844 и 1440×900 против изолированного
uvicorn+fresh DB (студент Смирнова О.П. через /api/register+/api/auth/login
— 200 ok, токен получен), dist пересобран до пробы (npm run build, 2.05s
OK). dist содержит дельту 1:1 (grep dist css: .layout 1fr ×2,
aside.filters,aside.side{display:none}, padding:84px 16px 88px,
.mtop{position:fixed;top:0;left:0;right:0}).

## Проверка задания итер.006 (критерии живой пробы)

1. «/instructor-choice scrollWidth ≤390, одноколоночно» — НЕТ.
   scrollWidth=465 (в 004/005 был 492), computed .app = «236px 154px» —
   сетка НЕ сложилась, .frame x=236 w=228.5 (правый край 464.5). Причина:
   новое правило `.layout{grid-template-columns:1fr}` (styles.css:114) —
   NO-OP: .layout уже складывается правилом ≤1024px (styles.css:83),
   действующим на 390 и до фикса (замер .layout = 196.5px, одна колонка,
   и так было). Реальный контейнер переполнения — .app (styles.css:90,
   «236px minmax(0,1fr)»): на ≤760 не складывается ни одним правилом;
   при display:none у aside.side auto-placement кладет .mtab-root в
   колонку 1 (236px), .frame — в колонку 2 (elementFromPoint(195,60) →
   .mtab-root). Кабинет решает идентичную сетку правилом
   `@media(max-width:760px){.app{grid-template-columns:1fr}}`
   (cabinet/styles.css:203) — в instructor-choice его по-прежнему нет,
   хотя п.1 «Что делать» итер.005 прямо это требовал. Уменьшение
   492→465 — побочный эффект скрытия aside.filters (min-content .frame),
   не закрытие MAJ-2. MAJ-2 ОТКРЫТ (третья итерация).
2. «/cabinet#/pdd-signs: mtop fixed y=0 при скролле» — ДА. scrollY=400 →
   .mtop top=0, w=390 h=57. MAJ-4 ЗАКРЫТ: left:0;right:0 дают полосу на
   всю ширину (замер w=390 на обеих страницах); elementFromPoint(20/195/
   380, 20) → .mtop/.mtop-дети — щели нет, аватар у правого края.
   NB (не блокер MAJ-4): скрытие aside.filters расходится с
   мокапом-источником mobile-choice.html — фильтрация на мобиле в мокапе
   есть в компактной форме (.search + горизонтальные .chips); display:none
   без мобильного эквивалента — молчаливая потеря функции (к финальному
   approve: вернуть компактный эквивалент или зафиксировать решение в
   openspec).
3. «контент не под fixed top-bar» — cabinet ДА / choice НЕТ. pdd-signs и
   home при scroll=0: первый видимый контент top=84 (padding 84px),
   mtop bottom=57 → зазор +27px, перекрытия нет; scrollWidth=390,
   .app «390px» — одноколоночно. instructor-choice: .kicker top=20 →
   перекрытие 37px — правка внесена только в cabinet/styles.css, ≤760
   блок choice padding-top не компенсирует (действует ≤850 правило
   «padding:20px 16px 36px»). Требование итер.005 п.3 «обе
   страницы-носителя» не выполнено — MAJ-5 ОТКРЫТ наполовину.
4. desktop 1440×900 — не задет: .mtop/.mtabs count=0 на обеих страницах,
   .app «236px 1204px», .side flex, scrollWidth=1440, choice:
   .layout «248px 710px», filters видимы. MIN-7 держится (дельта не
   трогает loadMe: mobile /me = 2 — сайдбар+top-bar).

## Гейт RED: носитель сломан правкой паддинга

pytest tests/unit tests/web -q → 1 failed, 211 passed:
test_mobile_tabbar.py::test_cabinet_integrates_tabbar_sidebar_hidden_le760,
строка 140 `assert ".frame{padding:26px 16px 88px}" in css` — MAJ-5 правка
(26→84px) сделана без обновления носителя (design.md «Границы правок
тестов» — правки паддинга требуют синхронной правки носителя). budgets OK
(14), openspec strict 27/27, build OK (2.05s).

## Статус прежних находок

- MIN-6: НЕ ТРОНУТ (2-я итерация подряд при заявке «комментарии по
  факту»). 28–31: дубль «— bottom-sheet с ФИО и «Выйти»» + сирота
  «= отступ логотипа ~25px…» без предложения; 37–40: «лениво при ПЕРВОМ
  открытии Профиля… дубля запросов при открытии страницы нет»
  противоречит коду — loadMe() при mount при visible (MobileTabBar.vue:199,
  `if (visible.value) loadMe();`) + mq change, кеш meLoaded. В рабочем
  дереве компонента правлена только CSS-строка .mtop (1 строка).
- e2e-замеры из «Что делать» итер.005 (п.1 scrollWidth ≤390 на choice,
  п.3 контент-vs-шапка при scroll=0) — НЕ добавлены
  (test_ui_playwright.py не менялся; test_s18_mobile_geometry_hit_targets
  меряет только mtop y после wheel на cabinet).
- MIN-2 (строка 34 файла волны), MIN-4 (а/б/в), MIN-5.1 — прежние
  остатки, не тронуты.

## Прогоны (реальное исполнение, дерево HEAD = 97fdca7 + дельта в
## рабочем дереве, dist пересобран)

```
npm run build (frontend/vue) -> OK (2.05s)
npm run check:budgets -> OK: страниц: 14, бюджеты NFR-26 соблюдены
openspec validate --all --strict -> Totals: 27 passed, 0 failed (27 items)
pytest tests/unit tests/web -q -> 1 failed, 211 passed (3:14) — РЕГРЕСС
  носителя test_mobile_tabbar.py:140 (26px vs 84px)
живая проба 390×844 (изолированный uvicorn+fresh DB, студент через API):
  choice scroll=0: scrollWidth=465, .app «236px 154px», .frame x=236
    w=228.5, kicker top=20 vs mtop bottom=57 → −37px, filters hidden,
    .layout 196.5px (сложен ≤1024 и до фикса), .mtop w=390 h=57 y=0
  cabinet#/pdd-signs: scrollWidth=390, .app «390px», контент top=84
    (зазор +27px), wheel 400 → scrollY=400, .mtop y=0 w=390; scrollTo(0,0)
    → контент 84, полоса 0..57 — перекрытия нет
  desktop 1440×900: .mtop/.mtabs=0, сетки desktop, scrollWidth=1440
```

## Что делать к итерации 007

1. MAJ-2: в ≤760 блок instructor-choice/styles.css добавить правило .app
   (`@media(max-width:760px){.app{grid-template-columns:1fr}}`, как в
   cabinet/styles.css:203); строку `.layout{...:1fr}` удалить как no-op
   (или оставить с комментом «дубль ≤1024» осознанно). e2e-замер
   scrollWidth ≤390 на /instructor-choice.
2. MAJ-5: компенсация padding-top в ≤760 блоке choice (`.app>.frame`
   padding-top ≥ 57px — аналог cabinet 84px); e2e-замер контент-vs-шапка
   при scroll=0 на ОБОИХ носителях.
3. Обновить носитель test_mobile_tabbar.py:140 под 84px (гейт green).
4. MIN-6: переписать 37–40 по факту (loadMe при mount при visible + mq
   change; кеш meLoaded; desktop /me не делает); убрать дубль и сироту
   28–31.
5. Мокап-сверка choice (фильтры .search/.chips на мобиле) — решение
   зафиксировать.
6. MIN-2/MIN-4 — прежние остатки, закрыть к финальному approve.

## Вердикт: return

MAJ-4 закрыт и подтвержден замером (полоса 390px на всю ширину, прилипание
y=0 при реальном скролле 3536px контента, шапка кликабельна без щели) —
зачтено; кабинет закрыл свою половину MAJ-5 (зазор +27px, scrollWidth 390,
одна колонка) — зачтено. Но прямой критерий задания «/instructor-choice:
scrollWidth ≤390, одноколоночно» не выполнен третий раз: правило опять
внесено не в тот контейнер (.layout — no-op дубль правила ≤1024, сам
коммент задания это признает), реальный .app не сложен — scrollWidth=465;
на instructor-choice контент по-прежнему под шапкой (−37px); правка
паддинга сломала носитель (pytest 1 failed — гейт red); MIN-6 не тронут
вторую итерацию; требуемые e2e-замеры не добавлены; при этом задание/месседж
итер.006 утверждают закрытие MAJ-2/MAJ-5/MIN-6, что живая проба опровергает.
Merge невозможен. Ожидаемый объем итер.007 — одно правило .app, padding-top
на choice, правка носителя 140, чистка комментариев, два e2e-замера.

Commit: дельта без фикс-коммита (рабочее дерево поверх 97fdca7)

<!-- Reviewer-Delegation: deleg-s18-cr-external | независимый код-ревьюер (не автор диффа) | итерация 007 | дифф: фикс-коммит 4673442 поверх 97fdca7 (MobileTabBar.vue .mtop left/right; cabinet .frame 26→84px; instructor-choice ≤760: +.app{1fr}, +.layout{1fr}, +aside.filters — тесты и комментарии коммитом НЕ менялись) | ветка: feat/s18-mobile | дата: 2026-11-17 -->

# Итер.007 2026-11-17: return (MAJ-2 ЗАКРЫТ — живая проба scrollWidth 390=390, .app «390px», одноколоночно, desktop не задет; MAJ-5 choice ОТКРЫТ — неперекрытие на 390×844 случайно: ghost-строка .mtab-root жрет grid-stretch, при 390×600 перекрытие −37px возвращается, при 1200 мертвая полоса 274px; носитель test_mobile_tabbar.py:140 RED 2-ю итерацию; MIN-6 не тронут 3-ю итерацию; заявки «.layout удален» и «MIN-4 sticky-замер добавлен» опровергнуты диффом)

Проверка живая: playwright-проба 390×844 / 390×600 / 390×1200 и 1440×900
против изолированного uvicorn+fresh DB (студент через /api/register+
/api/auth/login — 200 ok, токен получен), dist пересобран до пробы
(npm run build, 2.34s OK). dist-дельта 1:1 подтверждена grep-ом собранного
css/js: `@media (width<=760px){.app,.layout{grid-template-columns:1fr}
aside.filters,aside.side{display:none}.app>.frame{padding-bottom:88px}}`,
`.mtop[...]{position:fixed;top:0;left:0;right:0}`, `padding:84px 16px 88px`.

## Проверка задания итер.007 (критерии живой пробы запроса)

1. «/instructor-choice: scrollWidth ≤390, одноколоночно» — ДА.
   scrollWidth=390=innerWidth (maxScrollX=0), computed .app=«390px»,
   .layout=«358px», aside.side и aside.filters display:none, mtab-root 1.
   MAJ-2 ЗАКРЫТ: правило впервые в правильном контейнере, сетка сложилась
   (465→390), dist 1:1. Desktop 1440×900 не задет: .mtop/.mtabs=0,
   .app «236px 1204px», .layout «248px 710px», filters block,
   scrollWidth=1440. MIN-7 держится (/me=2 на мобиле — известное принятое).
2. «/cabinet#/pdd-signs: таб-бар снизу, top-bar сверху, контент между» —
   ДА (держится с итер.006, зачтено). .mtabs y=790..844 (низ = вьюпорт 844),
   .mtop y=0..57 w=390 — полоса на всю ширину; wheel 400 → scrollY=400,
   .mtop y=0; scrollTo(0,0) → #sec-pdd-signs y=84 (зазор +27px к полосе,
   контент между 57 и 790). scrollWidth=390, .app «390px».
3. NB: на choice геометрия «контент ниже шапки» (frame y=96, kicker 116 vs
   полоса 57) — см. ниже, случайная.

## Почему MAJ-5 на choice НЕ закрыт: механика ghost-строки

Компенсация padding-top на choice не вносилась (.frame padding-top=20px —
из правила ≤850). Неперекрытие на 390×844 создает побочная механика:
.app{min-height:100vh} + 2 auto-строки (нулевой .mtab-root + .frame),
align-content:normal(stretch) делит свободную высоту вьюпорта пополам между
строками — замеры resolved rows: «96px 748px» при 844 ((844−652)/2=96),
«274px 926px» при 1200 (мертвая полоса .mtab-root 274px над контентом!),
«0px 652px» при 600 (контент выше вьюпорта — делить нечего) → frame y=0,
kicker 20 < полоса 57 → ПЕРЕКРЫТИЕ −37px возвращается (замер 390×600).
Свойство «контент к верху НИЖЕ шапки» не выражено константой и зависит от
высоты вьюпорта. NB: комментарий BUG-070 в MobileTabBar.vue (243–249:
«≤760px не задет — box div нулевой высоты») опровергнут замером — верен
только пока контент ≥ вьюпорта; на cabinet та же мина (сейчас контент
3536px > 844 → ghost 0, но на коротком разделе ghost появится — не
перекрытие, а ложный сдвиг вниз).

## Гейт RED (2-я итерация подряд)

pytest tests/unit tests/web -q → 1 failed, 211 passed (3:41):
test_mobile_tabbar.py::test_cabinet_integrates_tabbar_sidebar_hidden_le760,
строка 140 `assert ".frame{padding:26px 16px 88px}" in css` против
фактического 84px. Пункт 3 «Что делать» итер.006/007 (обновить носитель под
84px) не выполнен — правка паддинга итер.006 так и осталась без носителя.

## Статус прежних находок

- MIN-6: НЕ ТРОНУТ (3-я итерация). Сирота «= отступ логотипа ~25px…»
  (MobileTabBar.vue:31) на месте; 37–40 «лениво при ПЕРВОМ открытии
  Профиля… дубля запросов при открытии страницы нет» противоречит коду
  (`if (visible.value) loadMe()` при mount + mq change, кеш meLoaded) —
  живой замер /me = 2 на мобиле это подтверждает.
- Заявка «MIN-4 sticky-замер добавлен в test_s18_mobile_geometry_hit_
  targets» — НЕВЕРНА дважды: (а) коммит 4673442 тестов не касается
  (--stat: MobileTabBar.vue, cabinet/styles.css, instructor-choice/
  styles.css — ни одного теста); wheel-замер .mtop y=0 существует с
  97fdca7 и подписан в тесте «MAJ-3», не MIN-4; (б) MIN-4 — это посев
  .act/.bk-act + носители 4 сценариев (строки 66/135 review), не sticky.
  Точная копия путаницы нумерации, разобранной в итер.006 (383–385).
- Заявка «no-op дубль .layout{1fr} из ≤760 удален» (месседж 4673442 и
  сопроводительное задание) — НЕВЕРНА: строка instructor-choice/styles.css
  :115 добавлена ЭТИМ же коммитом (+3/−1) и живет без коммента «дубль
  ≤1024» — ни удаление, ни осознанный коммент из п.1 «Что делать» не
  сделаны. На геометрию не влияет (no-op безвреден), но месседж коммита
  снова описывает правку, которой нет, — 3-й раз подряд (005: «MIN-4
  sticky-замер», 006: «MAJ-2/MAJ-5/MIN-6 закрыты», 007: «.layout удален»).
- e2e-замеры из «Что делать» (scrollWidth ≤390 на choice; контент-vs-шапка
  при scroll=0 на ОБОИХ носителях) в test_ui_playwright.py НЕ добавлены —
  только ручная проба.
- Мокап-сверка choice-фильтров (компактный .search/.chips или решение в
  openspec) — не сделана; MIN-2 (строка 34 файла волны) — не тронут.

## Прогоны (реальное исполнение, HEAD = 4673442, dist пересобран)

```
npm run build (frontend/vue) -> OK (2.34s)
npm run check:budgets -> OK: страниц: 14, бюджеты NFR-26 соблюдены
openspec validate --all --strict -> Totals: 27 passed, 0 failed (27 items)
pytest tests/unit tests/web -q -> 1 failed, 211 passed (3:41) — носитель
  test_mobile_tabbar.py:140 (26px vs 84px), 2-я итерация
живая проба (изолированный uvicorn+fresh DB, студент через API):
  choice 390×844: scrollWidth=390, .app «390px», side/filters none,
    mtop 0..57 w=390, mtabs 790..844, frame y=96, kicker 116 (случайный
    зазор), maxScrollX=0
  choice 390×600: frame y=0, kicker 20 vs 57 → перекрытие −37px (MAJ-5)
  choice 390×1200: rows «274px 926px» — мертвая полоса 274px
  cabinet#/pdd-signs 390×844: scrollWidth=390, mtop 0..57, mtabs 790..844,
    secSigns y=84 (+27px), wheel 400 → mtop y=0, scroll=0 → 84/57
  desktop 1440×900: .mtop/.mtabs=0 на обоих, сетки desktop, filters block,
    scrollWidth=1440
```

## Что делать к итерации 008

1. Носитель test_mobile_tabbar.py:140 → 84px (гейт green) — 1 строка.
2. MAJ-5 choice: в ≤760 блок instructor-choice добавить
   `.app>.frame{padding-top:84px}` (аналог cabinet/styles.css:435) И
   нейтрализовать ghost-строку: .mtab-root на ≤760 не должен занимать
   grid-строку (height:0/out-of-flow; bottom-sheet`ы внутри не сломать) —
   либо сознательное решение с комментом. Свойство «контент ниже шапки»
   должно держаться константой, а не высотой вьюпорта.
3. e2e-замеры в test_s18_mobile_geometry_hit_targets: scrollWidth ≤390 на
   /instructor-choice; контент-vs-шапка при scroll=0 на ОБОИХ носителях.
4. MIN-6: переписать 30–31/37–40 по факту (loadMe при mount при visible +
   mq change; кеш meLoaded; /me=2 на мобиле — сайдбар+top-bar); BUG-070
   коммент 243–249 сверить с замером.
5. Мокап-сверка choice-фильтров — компактный эквивалент или решение в
   openspec.
6. `.layout{1fr}` ≤760 — удалить или осознанный коммент «дубль ≤1024»;
   MIN-2/MIN-4 — прежние остатки, закрыть к финальному approve. Месседж
   коммита писать по факту диффа.

## Вердикт: return

MAJ-2 закрыт и подтвержден живым замером на реальном сервере с API-логином
(.app «390px», scrollWidth 390=390, dist 1:1, desktop не задет) — зачтено,
это третий заход и первый корректный. Кабинет держит всю свою геометрию
(полоса сверху 0..57, таб-бар 790..844, контент 84 с зазором +27, прилипание
wheel 400 → y=0) — зачтено. Но merge невозможен: гейт red второй итерации
(носитель :140 не обновлен); MAJ-5 на choice не закрыт — «неперекрытие» на
390×844 случайный побочный эффект grid-stretch ghost-строки .mtab-root (при
600 перекрытие −37px возвращается, при 1200 мертвая полоса 274px над
контентом); MIN-6 не тронут третью итерацию; требуемые e2e-замеры не
добавлены; обе заявки итерации («no-op .layout удален», «MIN-4 sticky-замер
добавлен») опровергаются диффом коммита. Ожидаемый объем итер.008 — две
строки CSS + 1 строка носителя, ghost-строка, два e2e-замера, чистка
комментариев, решение по фильтрам.

Commit: 4673442
