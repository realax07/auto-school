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

<!-- Reviewer-Delegation: deleg-s18-cr-external | независимый код-ревьюер (не автор диффа) | итерация 008 | дифф: фикс-коммит f56c962 поверх 4673442 (instructor-choice/styles.css 1 строка: ≤760 .app>.frame{padding-bottom:88px} → {padding:84px 16px 88px}; test_mobile_tabbar.py 1 строка: ассерт :140 26px→84px) | ветка: feat/s18-mobile | дата: 2026-11-17 -->

# Итер.008 2026-11-17: return (MAJ-5 choice ЗАКРЫТ — перекрытие устранено константой 84px, подтверждено на 844/600/1200, не вьюпортом; носитель :140 синхронно, гейт green 212 passed — впервые с итер.005; месседж f56c962 честный 1:1; возврат по накопленному остатку: ghost-строка 64/242px без решения, e2e-замеры не добавлены 4-ю итерацию, MIN-6 не тронут 4-ю итерацию, MIN-2/MIN-4 открыты)

Проверка живая: playwright-проба 390×844/600/1200 и 1440×900 против
изолированного uvicorn+fresh DB (студент Смирнова О.П. через /api/register+
/api/auth/login — 200 ok), dist пересобран до пробы (npm run build, 2.72s
OK). dist-дельта 1:1: собранный css instructor-choice содержит
`@media (width<=760px){.app,.layout{grid-template-columns:1fr}
aside.filters,aside.side{display:none}.app>.frame{padding:84px 16px 88px}}`.

## Проверка задания итер.008

1. «choice ≤760: .app>.frame{padding:84px 16px 88px} + носитель 84px» — ДА
   обе. Статика: instructor-choice/styles.css:118 в блоке
   @media(max-width:760px); носитель test_mobile_tabbar.py:140 —
   `assert ".frame{padding:84px 16px 88px}" in css` с комментом «fixed
   top-bar 58px + отступ лого 26px». Гейт RED итер.006/007 снят.
   NB (не блокер): носитель ассертит паддинг только cabinet/styles.css —
   choice-паддинг статически не закреплен ни одним тестом.
2. «/cabinet#/wallet: кнопка Кошелек ≥44px» — ДА. .mtop y=0..57 w=390
   (полоса на всю ширину), .mtabs y=790..844 h=54; таб «Кошелек» h=53;
   .wal-btn h=47 ≥44 (6 кнопок на секции, первая visible);
   #sec-wallet y=84 — контент ниже полосы (зазор +27), scrollWidth
   390=390. MIN-1 держится.
3. «/instructor-choice: контент не под top-bar» — ДА на всех высотах:
   844 — .mtop 0..57, .frame y=64, padding-top 84px, .kicker top=148
   (запас +91); 600 — kicker 84 (+27; перекрытие −37px итер.006/007
   устранено); 1200 — kicker 326. scrollWidth 390=390, .app
   grid-template-columns «390px» на всех. Отличие от итер.007: свойство
   «контент ниже шапки при scroll=0» теперь держится КОНСТАНТОЙ
   паддинга, а не побочным эффектом grid-stretch ghost-строки —
   контент физически не может попасть под полосу 57px ни при какой
   высоте вьюпорта.
4. Desktop 1440×900 не задет: .mtop/.mtabs count=0 на обеих страницах,
   .app «236px 1204px», scrollWidth=1440.

## Остаток п.2 итер.007: ghost-строка не решена (вторая половина)

Требование «нейтрализовать ghost-строку (.mtab-root не должен занимать
grid-строку) — либо сознательное решение с комментом» НЕ выполнено: ни
height:0/out-of-flow, ни коммента-решения нет (коммит не трогает
MobileTabBar.vue). Замеры grid-template-rows .app: «64px 780px» при 844
(мертвая полоса 64px над контентом), «0px 716px» при 600, «242px 958px»
при 1200 (мертвая полоса 242px). Перекрытия нет, но «контент к верху»
мокапа не держится: зазор контент/полоса 91px (844) и 269px (1200)
против 27px на cabinet — носители несимметричны. На реальных телефонах
(600–950px) эффект 0–90px лишнего отступа.

## Гейты (green впервые с итер.005)

```
npm run build (frontend/vue) -> OK (2.72s), dist пересобран до прогонов
npm run check:budgets -> OK: страниц: 14, бюджеты NFR-26 соблюдены
openspec validate --all --strict -> Totals: 27 passed, 0 failed (27 items)
pytest tests/unit tests/web -q -> 212 passed (3:20) — база 212 держится,
  носитель test_mobile_tabbar.py:140 синхронизирован (RED 2 итераций снят)
```

Среда: как в итер.003 — восстановлен LD_LIBRARY_PATH на
~/.cache/pw-libs/root/usr/lib/x86_64-linux-gnu (без него chromium 1255
не стартует: libatk-1.0.so.0); на результат прогонов не повлияло.

## Статус прежних находок

- MIN-4 (а/б/в): НЕ ТРОНУТЫ. (а) .act по-прежнему под
  `if acts.count():` (test_ui_playwright.py:5252–5256) — assert не
  выполняется никогда; (б) .bk-act в геометрия-тесте не меряется;
  (в) носители «История кошелька на 390px», «Слоты недели на 390px»,
  «Верх контента на десктопе», «Админ-транзакции на 390px» — grep по
  tests/ и specs/ пуст (spec.md:25/36/59/82 без носителей).
- MIN-6: НЕ ТРОНУТ (4-я итерация). Сирота «= отступ логотипа ~25px…»
  (MobileTabBar.vue:31), дубль «bottom-sheet с ФИО и «Выйти»» (28–30),
  37–40 «лениво при ПЕРВОМ открытии… дубля запросов при открытии
  страницы нет» противоречат коду (loadMe() при mount при visible,
  :199, + mq change, кеш meLoaded); коммент BUG-070 (243–249: «≤760px
  не задет — box div нулевой высоты») опровергнут замером итер.007 и
  сегодня (64/242px ghost-полоса).
- MIN-2 (строка 34 файла волны, «flow_check — без ошибок» против факта
  J10): не тронут.
- e2e-замеры из «Что делать» итер.005/006/007 (scrollWidth ≤390 на
  choice; контент-vs-шапка при scroll=0 на ОБОИХ носителях) — НЕ
  добавлены (test_ui_playwright.py не менялся с 97fdca7, итер.005).
  Фикс MAJ-5 в CI не закреплен — свойство охраняется только ручной
  пробой этой итерации.
- .layout{grid-template-columns:1fr} в ≤760 (styles.css:115) — no-op
  дубль правила ≤1024: не удален, коммента «дубль осознанно» нет (п.6
  итер.007).
- Мокап-сверка choice-фильтров (компактный .search/.chips или решение
  в openspec) — не сделана (aside.filters display:none без мобильного
  эквивалента, замечание итер.006).
- MIN-5.1 (трекинг ПМ): из дерева не верифицируем.

## Месседж коммита f56c962

Соответствует диффу 1:1 (обе строки) — впервые с итер.005 ложных
пунктов нет, зачтено. NB: «fixed top-bar 58px» — фактический замер
h=57 (84 = 57+27 зазора на cabinet; арифметика 58+26 условна), на
суть и носитель не влияет. Префикс [s17-fix] на спринт-18 коммите —
косметика учета.

## Что делать к итерации 009 (короткий остаток — без правок верстки)

1. e2e-замеры в test_s18_mobile_geometry_hit_targets: scrollWidth ≤390
   на /instructor-choice; контент-vs-шапка при scroll=0 на ОБОИХ
   носителях (закрепление MAJ-2/MAJ-5). Опционально: статик-ассерт
   choice-паддинга в test_mobile_tabbar.py (сейчас 84px закреплен
   только за cabinet).
2. Ghost-строка: .mtab-root на ≤760 не занимает grid-строку (height:0
   / out-of-flow, шиты внутри не сломать) ИЛИ сознательное решение с
   комментом; зазор контент/полоса унифицировать с cabinet (27px).
3. MIN-4: посев .act через API или безусловный N>0-assert; замер
   .bk-act; носители 4 сценариев (spec.md:25/36/59/82).
4. MIN-6: переписать 28–31/37–40 по факту; BUG-070 243–249 сверить с
   замером.
5. MIN-2 (строка 34 — факт J10); .layout no-op удалить или коммент;
   фильтры choice — решение. Месседж коммита — по факту диффа
   (прецедент f56c962).

## Вердикт: return (остаток чисто MIN — все пять MAJ закрыты)

Зачтено полностью: MAJ-5 на choice закрыт корректно — константа 84px
вместо случайной геометрии, подтверждено живой пробой на 844/600/1200
(перекрытие −37px итер.006/007 устранено), носитель синхронно, гейт
green 212 passed, desktop не задет, месседж честен. Впервые за партию
нет ни одного открытого MAJ. Но этот approve был бы ФИНАЛЬНЫМ, а по
формуле итер.004–007 (без изменений) MIN-остатки должны быть закрыты
к финальному approve: MIN-6 не тронут 4-ю итерацию, MIN-4 (а/б/в) —
с итер.002, MIN-2 — с итер.001; требуемые трижды e2e-замеры
MAJ-2/MAJ-5 отсутствуют (фикс не охраняется CI); ghost-строка жива
без решения (вторая половина п.2 задания итер.007). Approve при
открытом перечне означал бы зафиксировать «открытых нет» вопреки
дереву — та же категория «учет расходится с фактом», что MIN-5.
Ожидаемый объем итер.009 — десяток строк тестов и комментариев плюс
одно grid-решение; код верстки, скорее всего, не меняется.

Commit: f56c962

<!-- Reviewer-Delegation: deleg-s18-cr-external | независимый код-ревьюер (не автор диффа) | итерация 009 (финальная) | дифф: 7c12466 поверх f56c962 (review-18.4.3-001.md 1 строка: :34; test_ui_playwright.py +11: choice scrollWidth ≤390, frame top 56..90, комментарий-отсылка MIN-4) | ветка: feat/s18-mobile | дата: 2026-11-17 -->

# Итер.009 2026-11-17: return (MIN-2 ЗАКРЫТ — строка 34 честная формулировка J10, дифф сверен; добавленные e2e-замеры валидны и green; возврат: обе заявки закрытия ПМ опровергнуты проверкой — «MIN-6 комментарий заменен» ложь (MobileTabBar.vue диффом не тронут, 5-я итерация), «ghost-строка choice не воспроизводится в актуальном dist» опровергнута живой пробой свежесобранного dist — 64/0/242px 1:1 с итер.007/008; MIN-4(а) остался под `if acts.count():`, новый комментарий теста «покрыто test_pdd_sections::test_mobile_topbar» — ложь)

## Проверка заявки ПМ (итер.009)

1. «MIN-2 — review-18.4.3 строка 34 честная формулировка J10» — ДА,
   ЗАКРЫТО. Дифф 7c12466: «flow_check — без ошибок» → «flow_check —
   J10-остаток (11 задач до независимого CR, погашен итер.002 approve)».
   Формулировка согласуется с фактом, установленным итер.001–003
   (flow_check 1 ошибка J10, погашенной approve-ом независимого CR).
2. «e2e-замеры добавлены в test_s18_mobile_geometry_hit_targets» — ДА,
   частично зачтено. choice scrollWidth ≤390 (5271–5274) — валидный
   рантайм-замер (проба: 390); frame top 56..90 (5275–5277) — проходит,
   факт 64. Третий пункт списка ПМ «mtop sticky прилип y=0 при wheel
   400» — НЕ НОВЫЙ: ассерт 5265–5269 пре-экзистинг с 97fdca7
   (итер.005), диффом 7c12466 не добавлялся; в тесте он есть, учету
   зачтен как существовавший. NB-1: комментарий теста «frame top =
   top-bar низ (58px)» неточен — полоса 57px, фактический frame top
   64px, и эти 64px дает ИМЕННО ghost-строка (grid-row 1 = 64px);
   84px — это padding-top, не frame top. NB-2 (важно): ассерт-полоса
   56..90 закрепляет геометрию дефекта — при честном фиксе ghost-строки
   frame top станет 0 и ассерт упадет. Защищать надо первый контентный
   элемент (kicker top ≥ низ полосы), а не box .frame.
3. «MIN-6 комментарий заменен» — ОПРОВЕРГНУТО диффом: 7c12466 не трогает
   MobileTabBar.vue (последний коммит с его участием — 4673442,
   итер.006). На HEAD 5-ю итерацию подряд: сирота «= отступ логотипа
   ~25px…» (:31), дубль «bottom-sheet с ФИО и «Выйти»» (:29–30),
   :39–40 «лениво при ПЕРВОМ открытии… дубля запросов нет» против кода
   (loadMe() при mount при visible, :199, кеш meLoaded), коммент
   BUG-070 (:243–249 «box div нулевой высоты») против замера этой
   итерации (h=64px@844 / 242px@1200).
4. «ghost-строка choice не воспроизводится в актуальном dist
   (проверено)» — ОПРОВЕРГНУТО живой пробой. dist пересобран из HEAD
   (npm run build, 2.75s OK), изолированный uvicorn + fresh DB, студент
   через /api/register+/api/auth/login. grid-template-rows .app:
   «64px 780px» @390×844, «0px 716px» @600, «242px 958px» @1200 —
   1:1 замеры итер.007/008; .mtab-root static h=64/242, frameTop
   64/0/242. Ghost-строка жива, вторая половина п.2 задания итер.007
   (решение или коммент) не выполнена 3-ю итерацию.
5. MIN-4 — остатки не закрыты: (а) `.act` по-прежнему под
   `if acts.count():` (5252–5256); проба: у свежего ученика .act
   count=0 — assert не выполняется никогда. Новый комментарий
   5278–5280 «покрыто test_pdd_sections::test_mobile_topbar + geometry
   wal-btn выше» — ЛОЖЬ: test_mobile_topbar_initials_visible
   (5464–5475) мерит только инициалы top-bar; геометрию .act/.bk-act
   не меряет ни один тест файла (grep: клики .act.retry/.act.review
   в функциональных тестах 1900/1938/2540 — не геометрия).
   (б) .bk-act не меряется; (в) носители 4 сценариев
   (spec.md:25/36/59/82 «История кошелька/Слоты недели/Верх контента/
   Админ-транзакции») — grep по tests/ пуст, не добавлены.

## Прогоны (реальное исполнение, HEAD = 7c12466, dist пересобран до проб)

```
npm run build (frontend/vue) -> OK (2.75s)
pytest tests/web/test_ui_playwright.py -k s18_mobile_geometry -q
  -> 1 passed (10.53s)
Проба playwright 390×844/600/1200 /instructor-choice: см. п.4;
  /cabinet «Кошелек»: .mtop 0..57 fixed, #sec-wallet y=84 (зазор +27,
  как в итер.008), scrollWidth 390; wheel 400 → mtop.y=0 (прилип)
git show --stat 7c12466 -> 2 файла, +12/−1 (волна :34, тест +11)
```

## Статус прежних находок

- MIN-2: ЗАКРЫТ (п.1). Единственный пункт задания итер.009, закрытый
  диффом.
- MIN-6: НЕ ТРОНУТ 5-ю итерацию подряд — при заявке «заменен»
  (категория «учет расходится с фактом», MIN-5).
- Ghost-строка: ЖИВА (проба п.4) — без решения/коммента 3-ю итерацию.
- MIN-4 (а/б/в): открыты (п.5); новая ложная отсылка в комментарии
  теста добавлена к остатку.
- .layout no-op ≤760: удален еще 4673442 (grep cabinet/styles.css —
  только .app :203) — строка «не удален» в итер.008 снята, пункт
  закрыт.
- Мокап-сверка choice-фильтров (замечание итер.006): открыто.
- MIN-5.1 (трекинг ПМ): из дерева не верифицируем.

## Что делать к итерации 010 (десяток строк, верстка трогать не обязательно — кроме ghost-строки)

1. MIN-6: переписать 29–31/37–40 по факту (top-bar добавлен; /me при
   mount при visible + кеш); BUG-070 243–249 согласовать с замером
   (h=64/242 ≠ 0).
2. Ghost-строка: .mtab-root на ≤760 не занимает grid-строку (height:0/
   out-of-flow) или сознательный коммент; вместе с фиксом пересмотреть
   frame-top-ассерт (сейчас 56..90 проходит БЛАГОДАРЯ дефекту —
   мерить kicker/первый контент ≥ низ полосы); зазор унифицировать с
   cabinet (27px).
3. MIN-4: (а) посев заявок через API или безусловный N>0-assert;
   (б) замер .bk-act; (в) носители 4 сценариев.
4. Фильтры choice: мокап-сверка или решение в openspec.
5. Учет: не заявлять закрытие без диффа/пробы — обе заявки итер.009
   («MIN-6 заменен», «ghost не воспроизводится») опровергнуты
   проверкой.

## Вердикт: return (чисто MIN-остаток; гейт green; возврат из-за двух опровергнутых заявок закрытия + MIN-4)

Зачтено: MIN-2 закрыт честной формулировкой; добавленные замеры
(scrollWidth choice, frame top) валидны, геометрия-тест green,
sticky-замер на месте, dist 1:1, desktop не затронут. Возврат: MIN-6
не тронут 5-ю итерацию при заявке «заменен»; ghost-строка
воспроизводится в свежесобранном dist вопреки заявке «проверено»;
MIN-4(а) остался вакуумным, комментарий теста содержит ложную отсылку
на покрытие. Аппрув при дереве, противоречащем учету, — та же
категория MIN-5, что и в итер.008.

Commit: 7c12466

# Итер.010 2026-11-17: return (гейт не green, а 1 skipped — skip в середине теста обрывает 5 носителей, включая зачтенные итер.009 замеры sticky/scrollWidth/frameTop; заявка «ghost-элементов нет» опровергнута живой пробой свежего dist 5befca1 — 64px@390×844 1:1 с итер.007–009, а «ghost-детектор на dist mobile-choice.html» вакуумен: mobile-choice.html в dist нет — это мокап design/mocks/mobile, .mtab-root в статике instructor-choice.html отсутствует (SPA-рендертайм); MIN-6 заявлен «начисто», выполнен наполовину — верхний фрагмент 26–32 вычищен честно, но :38–40 противоречит коду и новой :31, BUG-070 244–250 не согласован; skip-сообщение «геометрия покрыта на заполненных состояниях» — ложь)

## Проверка задания итер.010 (дифф 5befca1: MobileTabBar.vue +4/−3, test_ui_playwright.py +5/−4; прочих файлов нет)

1. «MIN-6: комментарий top-bar вычищен от обрывков начисто (замена
   точной подстрокой)» — ЧАСТИЧНО. Верхний фрагмент 26–32: сирота
   «= отступ логотипа ~25px…» и дубль «bottom-sheet с ФИО и «Выйти»»
   удалены, новая формулировка «/me при mount» согласуется с кодом
   (:200 `if (visible.value) loadMe();`, кеш meLoaded :185) —
   ЗАЧТЕНО. Но задание итер.009 п.1 выполнено наполовину:
   (а) :38–40 «лениво при ПЕРВОМ открытии «Профиля» … дубля запросов
   при открытии страницы нет» — против кода (loadMe при mount при
   visible, :200) и теперь против собственной новой строки :31 того же
   файла («из /me при mount») — файл содержит два взаимоисключающих
   утверждения о моменте загрузки /me;
   (б) BUG-070 :244–250 «…≤760px не задет (внутри fixed .mtabs — box
   div нулевой высоты)» — не согласован с замером: box .mtab-root
   h=64px@390×844 (см. п.2) — НЕ нулевой.
2. «ghost-детектор на свежем dist mobile-choice.html: ghost-элементов
   нет» — ОПРОВЕРГНУТО. Во-первых, референс вакуумен: файла
   mobile-choice.html в dist НЕТ (ls dist — только instructor-choice.html;
   mobile-choice.html — мокап design/mocks/mobile/), а в статике
   instructor-choice.html вхождений «mtab» ноль — таб-бар рендерится в
   рантайме (SPA), любой статический скан dist-HTML ghost-строку видеть
   не может. Скрипта-детектора в дереве нет (grep scripts/ tests/ —
   пусто). Во-вторых, живая проба свежего dist (пересобран из HEAD,
   хеш shared-BTw5wovZ.css совпал с закоммиченным — раскладка байт-в-байт
   как в итер.009): см. п.4. «Сверка твой/наш»: рабочий детектор —
   рантайм-проба grid-template-rows (методика итер.007–009), и она
   ghost находит.
3. «MIN-4(а): честный pytest.skip при отсутствии .act» — механика
   честная, исполнение с дефектами. `import pytest` :35 есть, skip
   вместо вакуумного `if acts.count():` — направление верное (зачтено).
   НО:
   (а) skip размещен В СЕРЕДИНЕ теста (5252–5253) — pytest.skip обрывает
   исполнение: после .act-блока НЕ ИСПОЛНЯЮТСЯ 5 проверок: высота .mtabs
   44..64, .side-user hidden, sticky .mtop при wheel (носитель MAJ-3,
   пре-экзистинг с 97fdca7), choice scrollWidth ≤390 и frame top 56..90
   (MIN-4 e2e-замеры, зачтенные итер.009 как валидные). Реальный прогон:
   «1 skipped» — «гейт green» итер.010 фактически «гейт skipped», носители
   мертвы в каждом прогоне;
   (б) сообщение skip «геометрия покрыта на заполненных состояниях» —
   ЛОЖЬ: единственный замер .act bounding_box во всем тестовом файле —
   сам скипаемый ассерт :5257 (grep bounding_box — только он);
   «test_pdd_sections::test_mobile_topbar» не существует (в
   test_pdd_sections.py нет ни одного mobile/topbar-теста; есть
   test_mobile_topbar_initials_visible в test_ui_playwright.py :5465 —
   мерит инициалы, не геометрию);
   (в) комментарий 5279–5281 «покрыто test_pdd_sections::
   test_mobile_topbar + geometry wal-btn выше» — назван ложью в
   итер.009 п.5 и НЕ удален.
4. Живая проба (изолированный uvicorn + fresh DB, студент
   /api/register+/api/auth/login, sessionStorage init-script, HEAD=5befca1):
   - 390×844: gridTemplateRows .app «64px 780px», .mtab-root static
     h=64 top=0 w=390, frameTop=64, scrollW=390 — 1:1 итер.007/008/009;
   - 600×800: «99px 701px», .mtab-root h=99, frameTop=99;
   - 1200×800: «800px», .mtab-root display:none h=0 — desktop чист
     (страховка :251 работает).
   Ghost-строка жива на мобильных ширинах 6-ю итерацию подряд; вторая
   половина п.2 задания итер.007 (решение или сознательный коммент) не
   выполнена 4-ю итерацию.
5. MIN-4(б/в) — без изменений: .bk-act не меряется; носители 4 сценариев
   (spec.md:25/36/59/82) не добавлены. MIN-2 — подтвержден ЗАКРЫТЫМ на
   HEAD (review-18.4.3 :34 «flow_check — J10-остаток… погашен итер.002
   approve» — проверено).

## Прогоны (реальное исполнение, HEAD = 5befca1, dist пересобран до проб)

```
npm run build (frontend/vue) -> OK; git status чист — dist байт-в-байт
pytest test_ui_playwright.py::test_s18_mobile_geometry_hit_targets
  -> 1 skipped (9.69s) — был 1 passed в итер.009 за счет вакуумного if;
     теперь skip честный, но 5 носителей после .act-блока не исполняются
pytest tests/web/test_mobile_tabbar.py tests/web/test_pdd_sections.py
  -> 39 passed (2.02s)
Проба playwright 390×844/600×800/1200×800 /instructor-choice: п.4 —
  ghost 64/99/0px, frameTop 64/99/0
grep "bounding_box" (тест-файл, .act/.bk-act): единственный — :5257
  (сам скипаемый); grep test_mobile_topbar в test_pdd_sections.py: пусто
```

## Статус прежних находок

- Ghost-строка: ЖИВА (проба п.4) — без решения/коммента 4-ю итерацию;
  новая заявка закрытия опирается на проверку, которой не существует
  (категория MIN-5, третья итерация подряд).
- MIN-4(а): механизм улучшен (skip вместо вакуума — зачтено), но
  размещение убивает носители; сообщение skip и комментарий 5279–5281
  содержат ложные заявления о покрытии. (б)/(в) открыты.
- MIN-6: верхний фрагмент закрыт; :38–40 и BUG-070 :244–250 открыты
  (п.1 задания итер.009 наполовину).
- MIN-2: ЗАКРЫТ (подтверждено на HEAD).
- Мокап-сверка choice-фильтров: открыто (не тронуто).
- MIN-5.1 (трекинг ПМ): из дерева не верифицируем.

## Что делать к итерации 011

1. Ghost: .mtab-root на ≤760 не занимает grid-строку (height:0/
   out-of-flow) или сознательный коммент в коде; после фикса пересмотреть
   frame-top-ассерт 56..90 (проходит благодаря дефекту — мерить первый
   контентный элемент ≥ низ полосы, не box .frame).
2. Skip: перенести .act-блок в КОНЕЦ теста (после sticky/scrollWidth/
   frameTop) либо вынести геометрию .act в отдельный тест с посевом
   denied-заявки через API (вопрос-инструктор + deny — 2-3 вызова);
   носители sticky/scrollWidth/frameTop должны исполняться в каждом
   прогоне. Сообщение skip — без заявлений о покрытии; комментарий
   5279–5281 удалить.
3. MIN-6 остаток: :38–40 переписать по факту («/me при mount при
   visible + кеш meLoaded» — согласовать с :31); BUG-070 :244–250 —
   «box div нулевой высоты» заменить на замер (64/99px) или убрать.
4. Учет: не заявлять «ghost-элементов нет» по проверке, которой нет в
   дереве (статический скан dist-HTML ghost не видит в принципе);
   «гейт green» не заявлять при skipped-носителях — писать честно
   «N passed, 1 skipped (носители X/Y/Z не исполняются)».

## Вердикт: return (носовая часть улучшений честная — верх MIN-6 вычищен, skip вместо вакуума; возврат из-за: гейт «green» на деле 1 skipped с мертвыми носителями, опровергнутая пробой заявка закрытия ghost, ложные заявления о покрытии в skip-сообщении и комментарии 5279–5281, половина задания MIN-6 не выполнена)

Зачтено: верхний фрагмент комментария top-bar (26–32) вычищен честно,
«/me при mount» согласовано с кодом :200; замена вакуумного if на
pytest.skip — правильное направление; dist соответствует HEAD. Возврат:
заявка «ghost-элементов нет» опровергнута живой пробой (64px@390×844,
1:1 с тремя предыдущими итерациями) при вакуумном референсе
(«dist mobile-choice.html» — файла нет; статический скан не видит
рантайм-grid); skip в середине теста обрывает 5 носителей — гейт
фактически skipped, а не green; skip-сообщение и комментарий 5279–5281
заявляют покрытие, которого не существует. Аппрув при гейте-скипе и
опровергнутой заявке закрытия — та же категория MIN-5.

Commit: 5befca1
