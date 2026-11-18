# Покрытие: add-mobile-adaptive — TC-S18-001…008

Дельта: `openspec/changes/add-mobile-adaptive/specs/mobile-adaptive/spec.md` —
NEW-кейпабилити mobile-adaptive (8 требований, по 1 сценарию на требование).
Сверка состава: spec.md — `#### Scenario:` = 8 (таб-бар, история кошелька,
слоты недели, пополнение, верх контента, тренажер, админ-транзакции,
desktop-регресс); кейс на каждое требование 1:1 (TC-S18-001…008) —
покрытие **8/8**. Источник формулировок — spec.md + proposal.md (мокапы v3
design/mocks/mobile/, согласованы Заказчиком 2026-11-17 «Давай реализуем»).

Принцип партии (Н5): вся поведенческая автоматизация уже существует —
создана волнами 18.1–18.4 (носитель mobile-tabbar, мобильные e2e
TC-UI-077…079 + top-bar initials + geometry, медиа-гарды desktop-фрагментов).
Кейсы фиксируют трассировку «сценарий спеки → автоматизация / ручной
остаток», НОВЫХ тестов партия QA не заводит.

Якоря автоматизации партии (владельцы S18-сценариев):

- носитель таб-бара (18.1, 8): `tests/web/test_mobile_tabbar.py` — 5
  табов/порядок (TABS = Главная/Записи/Обучение/Кошелек/Профиль), SVG-иконки
  дословно из мокапа mobile-home.html, двойная защита видимости
  (matchMedia ≤760px + CSS `min-width:761px{display:none!important}`),
  высота 54px ≤ 64px спеки, wiring bindings setup (регресс BUG-068),
  шиты «Обучение»/«Профиль» с wiring /api/auth/me + /api/auth/logout
  (FR-5/FR-7/FR-8), интеграция в cabinet/instructor-choice БЕЗ дублей
  разметки (`.mtabs` — один источник в репо);
- e2e (18.4.2, +5 к прежним 84 = 89): TC-UI-077
  `test_s18_mobile_login_bottomsheet_tabbar_cabinet` (вход bottom-sheet
  grab 38×4 → кабинет 390×844: сайдбар скрыт, `.mtabs` ровно 54px, табы
  «Записи»/«Обучение»→шит→«Билеты», пополнение bottom-sheet + «Отмена»
  проходит (регресс BUG-069), профиль-шит ФИО+«Выйти»), TC-UI-078
  `test_s18_mobile_tickets_trainer_grid_390` (exam-bar wrap, q-nav ровно
  10 колонок × 32px, ответ → ans good + пояснение + done-g cur), TC-UI-079
  `test_s18_desktop_tabbar_hidden_and_fines_table_intact` (desktop-инвариант
  1440×900: `.mtabs` count 0, сайдбар 9 пунктов, штрафы thead 3 колонки,
  `.zn-grid` > 2 колонок — геометрия, регресс BUG-070),
  `test_mobile_topbar_initials_visible` (MAJ-1: инициалы top-bar),
  `test_s18_mobile_geometry_hit_targets` (MIN-4/CR/MIN-4a: касания ≥44px,
  таб-бар 44–64px, sticky top-bar y=0, scrollWidth instructor-choice ≤390
  (XSS-пейлоад не распирает — card-top ellipsis), контент-пад 20..30px);
- медиа-носители desktop-фрагментов (18.4.1, «дифф = 0»):
  `tests/web/test_cabinet_page.py` (7), `tests/web/test_pdd_sections.py`
  (31), `tests/web/test_sidebar_unified.py` (5 — desktop-сайдбар 9 пунктов,
  wiring ФИО/«Выйти», single-source);
- media-компоновка ≤760px — факты в `frontend/vue/src/pages/cabinet/
  styles.css`: `:435` (.frame 84px = top-bar 58px + отступ лого 26px),
  `:439-441` 18.2.1 Главная/плитки, `:460-462` 18.2.2 заявки,
  `:472-475` 18.2.3 неделя-полоса (слоты списком, состояния
  free/taken/mine), `:501-504` кошелек (wal-table→карточки), `:526`
  модалки bottom-sheet + BUG-069 z-слои (контент 1 < таб-бар 60 <
  модалки 70 < шиты/деталь знака 80), `:548-556` 18.3.1 ПДД (chips/знаки
  2 колонки/штрафы-карточки); instructor-choice: `styles.css:56-58`
  card-top ellipsis (af4dab0, итер.012);
- unit (логика С17 не менялась): `tests/unit/test_pdd_tickets_logic.py`
  (fmtClock/decClock/timeUp/fixAnswer — таймер 20:00, фиксация однократная),
  `tests/unit/test_pdd_generator.py` (19 — корпус: билеты 80×20, знаки
  8 групп/321, whitelist изображений 1094);
- гейты приемки (не pytest): `npm run build && npm run check:budgets` —
  budgets 14 страниц (MobileTabBar — в графах cabinet/instructor-choice);
  `openspec validate --all --strict` — 27 passed / 0 failed; flow_check OK.

Трассировка на требования Н1–Н5 (директива QA-партии):

- Н1 (источник и состав кейсов — specs дельты + proposal, состав сверен
  машинно): кейсы составлены по
  `openspec/changes/add-mobile-adaptive/specs/mobile-adaptive/spec.md`
  (8 Requirement / 8 Scenario) + proposal.md; `#### Scenario:` = 8 —
  счетчик дельты подтвержден, расхождений с директивой нет.
- Н2 (coverage-матрица на носители): каждый кейс трассирован на
  именованную автоматизацию — test_mobile_tabbar.py (8),
  test_ui_playwright.py (TC-UI-077/078/079 + top-bar initials + geometry),
  test_sidebar_unified.py (5), медиа-носители test_cabinet_page (7) /
  test_pdd_sections (31), unit (test_pdd_tickets_logic,
  test_pdd_generator); все имена сверены с исходниками носителей на HEAD
  (Н5-трассировка).
- Н3 (формат кейса: шаги ручной проверки + автономер носителя): каждый
  TC-S18-00X содержит GIVEN/WHEN/THEN ручной проверки на 390×844 (и
  1440×900 для desktop-инварианта) + автономер носителя (плановые ID
  TC-UI-077…079 в docstring тестов — rule 6; соответствие плановых и
  approved-ID зафиксировано, прецедент add-wallet-economy/add-pdd-learning).
- Н4 (формат партии): состав и оформление — как в
  `test-model/approved/add-pdd-learning/` (TC-S17-001…008 + coverage.md;
  прецедент формата — партия S16, коммит 2445625).
- Н5 (новых тестов не заводить — трассировка на существующую
  автоматизацию): партия QA автотестов не добавляет; дифф tests/ на
  af4dab0..c62a250 пуст (`git diff --stat -- tests/` — без вывода);
  ручные остатки перечислены по кейсам и сводом ниже.

| Кейс | Сценарий спеки (Requirement) | Автоматизация |
|---|---|---|
| TC-S18-001 | «Таб-бар на 390px» (Компактный таб-бар на мобильных ширинах) | test_mobile_tabbar: five_tabs_canonical, icons_verbatim_from_mobile_mock, mobile_only_matchmedia_and_css_guard (54px ≤ 64), setup_bindings_exposed (BUG-068), sheets_edu_profile_and_wiring, cabinet_integrates_tabbar_sidebar_hidden_le760, instructor_choice_integrates_tabbar, single_source_across_repo; e2e TC-UI-077 (aside.side none, .mtabs 54px, активный таб, шит «Обучение»), test_mobile_topbar_initials_visible (MAJ-1), geometry (.mtabs 44–64px); test_sidebar_unified (5 — парный desktop-носитель) |
| TC-S18-002 | «История кошелька на 390px» (Одноколоночные карточки вместо таблиц) | styles.css-факты :440/:461/:501 (tiles 1fr, заявки-карточки, wal-table→tbody grid-карточки с переупорядочиванием td); гард test_mobile_tabbar::cabinet_integrates_tabbar_sidebar_hidden_le760 (.frame 84/16/88); e2e TC-UI-077 (#sec-wallet на 390px, пополнение), geometry (.wal-btn ≥44, .act ≥44 на данных); регресс desktop — test_cabinet_page (7) |
| TC-S18-003 | «Слоты недели на 390px» (Календарь-полоса недель бронирования) | styles.css :472 18.2.3 (bk-grid flex-полоса, bk-slot списком min-height:44px, free/taken/mine :after-состояния, bk-slot.off скрыт, bk-nav wrap); e2e TC-UI-077 (таб «Записи» → #sec-bookings + хеш #/my-bookings + подсветка), geometry (bk-act ≥44 — styles.css :499); desktop-инвариант TC-UI-079 |
| TC-S18-004 | «Пополнение кошелька на 390px» (Bottom-sheet модалки сохраняются) | e2e TC-UI-077 (вход: width 390, прижат к низу, grab ::before 38×4, радиусы 18/0; пополнение: bottom-sheet + «Отмена» проходит — BUG-069; профиль-шит ФИО+«Выйти», крестик); test_mobile_tabbar::sheets_edu_profile_and_wiring (.grab 38×4, .mtab-backdrop); styles.css :526 media-блок (z-слои 60/70/80, .frame z-index:auto, grab-паттерн .wal-modal,.bk-modal,.zn-modal) |
| TC-S18-005 | «Верх контента на десктопе» (Контент поднят к верху с отступом логотипа) | test_mobile_tabbar::cabinet_integrates… (styles.css :435 `.frame{padding:84px 16px 88px}` — комментарий «58px + 26px» = MUST ~25–26); e2e geometry (choice paddingTop 20..30 — fix af4dab0 итер.012; sticky .mtop y=0 — MAJ-3); TC-UI-077 (fixed top-bar кабинета), test_mobile_topbar_initials_visible; TC-UI-079 (desktop-грид не сжат — BUG-070) |
| TC-S18-006 | «Тренажер на 390px» (Разделы ПДД адаптивны без изменения логики) | e2e TC-UI-078 (exam-bar wrap, карточка ≤ .frame, q-nav ровно 10 колонок × 32px, ответ → ans good + tip + done-g cur); TC-UI-079 (desktop штрафы thead); styles.css :548 18.3.1 (chips-лента, знаки 2 колонки, штрафы-карточки); unit test_pdd_tickets_logic::pure_functions_harness (таймер/фиксация — логика не менялась), unit test_pdd_generator (корпус 80×20, 321 знак); test_pdd_sections (31 гард С17); шит «Обучение» — test_mobile_tabbar + TC-UI-077 |
| TC-S18-007 | «Админ-транзакции на 390px» (Инструкторские и админские страницы адаптивны) | e2e geometry (scrollWidth instructor-choice ≤390 с изоляцией storage+reload; ассерт называет card-top ellipsis — XSS-пейлоад не распирает; paddingTop 20..30); instructor-choice/styles.css :56-58 (card-top min-width:0/ellipsis — af4dab0); test_mobile_tabbar::instructor_choice_integrates_tabbar_without_duplicate + single_source; админка/инструктор — media-правила 18.3.2/18.3.3 тех же носителей + ручная приемочная проба |
| TC-S18-008 | «Desktop-регресс» (Desktop-версия не изменяется) | e2e TC-UI-079 (1440×900: .mtabs count 0, aside.side видим, .snav 9, штрафы thead 3 колонки, .zn-grid > 2 — регресс BUG-070 геометрией); полный e2e 89 = прежние 84 (NFR-27 — не переписывались) + 5 S18; медиа-носители «дифф = 0»: test_cabinet_page (7), test_pdd_sections (31), test_sidebar_unified (5); test_mobile_tabbar::mobile_only_matchmedia_and_css_guard (страховка min-width:761px); BUG-070.md FIXED (.mtab-root) |

Свод по автоматизации партии: новых автотестов партия QA НЕ добавляет.
Нумерация: approved-ID партии — TC-S18-001…008; e2e-носители носят
плановые ID TC-UI-077…079 в docstring (rule 6); test_mobile_topbar_initials_visible
и test_s18_mobile_geometry_hit_targets — правочные носители ревью-партии
(MAJ-1/MIN-4/MAJ-3), ID TC-UI не имеют, трассируются именами.

Ручные остатки (свод; выполняются на приемке/гейте):
- визуальная сверка таб-бара/шитов с 21 мокапом на живом устройстве
  (иконки машинно дословны — test_mtabs_icons_verbatim_from_mobile_mock);
- целостный вид карточек кошелька/заявок/броней и полосы дней со слотами
  на живых данных (компоновка машинно закрыта фактами styles.css и
  видимостью секций в e2e; статусы «свободно/занято/ваш запрос» —
  content-строки :490-492);
- блюр фона bottom-sheet и шиты «Оспорить»/«деталь знака» с данными
  (единый media-паттерн :526-блока);
- линейная проба «отступ логотипа ~26px на всех ширинах» в кабинете
  (машинно: styles.css:435 + e2e-коридор 20..30 на instructor-choice);
- админ-разделы и инструкторские кабинет/документы/анкета на 390px с
  живыми данными (мобайл-вьюпорт 18.4.2 завел ключевые ученические
  сценарии; scrollWidth-инвариант на админку — кандидат в следующий
  носитель при мобайл-сценарии админ-партии);
- естественный 20-минутный таймер тренажера до 00:00 (тик и timeUp
  автоматизированы — прецедент TC-S17-004);
- целостное скрин-сравнение «до/после» desktop-версии (машинно: e2e-геометрия
  TC-UI-079 + гарды дословности носителей); docker-стенд — CI job
  docker-build на PR (прецедент BUG-064).

Прогоны партии (подтверждение при утверждении):
- полный pytest `python -m pytest tests/ -q` — **574 passed / 0 failed**
  (af4dab0, волна 18.4; независимо воспроизведен ревью на итер.013 за
  10:34 в стенде с браузером); tests/ не менялись af4dab0..c62a250
  (`git diff --stat -- tests/` пуст) — гейт переносится на HEAD c62a250;
- контрольный прогон партии QA на HEAD c62a250 (среда агента):
  **504 passed / 0 failed** (8:21) — вся не-браузерная часть + 14
  браузер-независимых тестов файла e2e; оставшиеся **75 e2e локально
  НЕВОСПРОИЗВОДИМЫ**: chrome-headless-shell не стартует — в среде агента
  нет системной библиотеки libatk-1.0.so.0 (браузеры Playwright
  установлены, OS-зависимости — нет; root-прав нет; прецедент класса
  BUG-064 «невоспроизводимо в среде агента — гейт на CI»); e2e-часть
  подтверждена гейтами партии выше (574/0 с браузером + независимое
  воспроизведение ревью);
- e2e `tests/web/test_ui_playwright.py` — **89 collected/passed**
  (84 прежних не переписывались + TC-UI-077/078/079 + top-bar initials +
  geometry); локально на c62a250: 14 browser-independent passed, 75 —
  блок среды (см. выше);
- `openspec validate --all --strict` — **27 passed / 0 failed**
  (воспроизведено на HEAD c62a250 при составлении партии);
- `npm run build && npm run check:budgets` — green, **OK: бюджеты NFR-26
  соблюдены (страниц: 14)** (воспроизведено на HEAD c62a250 при составлении
  партии: build 2.18s; MobileTabBar в графах cabinet/instructor-choice —
  design.md Решение 4; review-003 итер.003: build OK, budgets OK, 211
  unit+web passed);
- flow_check OK; код-ревью — итер.014 **approve** (c62a250,
  code-reviews/add-mobile-adaptive/review-003-consolidated-18.1-18.4.md);
- история фиксов ревью-партии: af4dab0 (итер.012: choice .frame 84→26px,
  card-top ellipsis — XSS-пейлоад scrollWidth 504→≤390, честная геометрия),
  69d0e6e (итер.013: BUG-070.md/MobileTabBar.vue — модель корня .mtabs
  согласована), c62a250 (итер.014 approve).

Сверка счетчиков дельты: Requirements = 8, Scenarios = 8 (1:1), кейсов 8,
висящих кейсов нет, непокрытых сценариев нет.
