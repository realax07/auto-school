# Code Review — BUG-052 + BUG-053 (ветка bugfix/s8-calendar-photo-modal против main d081bcf)

Reviewer-Delegation: deleg-cr-20261102-151804-external

- Ревьюируемый диапазон: d081bcf..56e39188332980d9cf7c4775c6c583f2b46c774a (HEAD, bugfix/s8-calendar-photo-modal, 9 коммитов)
- Файлы диффа: frontend/instructor-dashboard.html, frontend/js/dashboard-instructor.js, tests/test_ui_playwright.py, decisions/2026-11-02-photo-modal-layout.md (новый), incidents.md. Вне диффа прочитаны записи test-model/bugs/BUG-052/053 (untracked — см. замечание 2).
- Прогон ПМ (спринт-лог): UI-сьют **52 passed**, вкл. TC-UI-041/042; полный прогон — в спринт-логе. Ревьюером полный pytest НЕ запускался (ограничение потока); дешевые смоки ревьюера — см. «Проверено», п.7.

## Вердикт: approve

Замечаний blocker/major нет: 2 minor + 4 наблюдения — не блокируют. Снос bk-блока (BUG-052) полный, без осиротевших стилей и висячих JS-ссылок; слотовый контур календаря и модалка #m-bk не пострадали. Компоновка #m-car (BUG-053) соответствует решению Заказчика, id/обработчики не переименованы, FR-71-путь цел. Нового innerHTML на данных API в диффе нет.

## Замечания

| # | Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|---|
| 1 | minor | tests/test_ui_playwright.py:3734 (TC-UI-041) | Комментарий «запрос РОВНО на слоте Пн 14:00–16:00» неточен: weekday=2 по конвенции сетки CAL_DAYS (0=Пн) — это «Ср». Ассерты верны (data-k='2-14' совпадает с ключом calBookings), неточность только в комментарии (у TC-UI-038:3655 та же формулировка, но это пре-существующее, вне диффа). | Поправить слово в комментарии при следующем касании файла. |
| 2 | minor | test-model/bugs/BUG-052-calendar-legacy-block.md, BUG-053-photo-modal-layout.md | Обе записи баг-реестра untracked (`git status` → `??`) — в ветку не закоммичены; при merge потеряются (в отличие от decisions/ и incidents.md, которые закоммичены). Файлы прочитаны и по содержанию соответствуют коду. | ПМ: включить оба файла в коммит ветки до merge. Git ревьюером не трогался (по ограничению). |

### Наблюдения (вне вердикта)

- Commit 3726c93 в сообщении называет большое окно «gal-big» — это класс; идентификатор элемента mc-big. На код не влияет.
- В документах/коммитах повторяется опечатка «прямива/прямойве» (прямивание Заказчика). Косметика.
- Класс .filters (использовался только bk-filters) CSS-правил в instructor-dashboard.html никогда не имел (упоминается лишь в комментарии BUG-047:246) — после сноса сиротства не появилось. Классы legacy-сетки bk-grid (.dh/.tlabel/.corner/.slot) стилей в этом файле также не имели — снимать было нечего; .legend жив (легенды :438 и :485).
- BUG-052 entry декларирует grep-критерий «0 упоминаний» — проверен дословно, выполнен (см. п.1 «Проверено»).

## Проверено (Scenario)

1. **BUG-052: bk-block снесен без остатков.** grep по frontend/instructor-dashboard.html и frontend/js/dashboard-instructor.js: bkState/openBookings/bkRenderList/bkBindList/bkRenderGrid/bk-list/bk-grid/bk-cal/bk-filters/bk-hint/bk-none/bk-block — 0 вхождений; вызов openBookings() из openCalendar удален; в HTML остались только bk-slot-* — носители модалки #m-bk (целевая поверхность). Осиротевших .bk-* CSS-правил нет (grep '\.bk-' пуст; снято правило .bk-block, бывш. :156).
2. **Слотовый контур не пострадал.** calBuildGrid (JS:209): data-k='weekday-hour', клик по слоту с запросом/бронью → bkOpenSlot, клик по пустому → toggle calSelected (NPE нет, ветка if(calBookings[k]) защищает). calLoadBookings (:1351)/calMarkBookings (:1364) не тронуты. Модалка #m-bk: все bk-slot-* id на месте (HTML:677-693), биндинги confirm (:1406)/reject-btn (:1417)/reason input — disabled до непустой причины (:1424)/reject-go (:1427)/cancel (:1439)/close×2/backdrop — целы; bkApplied → openCalendar (полный сброс классов+innerHTML ячеек и перезагрузка availability/bookings) + loadSummary. bkWhen/bkCarText сохранены (используются модалкой слота).
3. **Сайдбар/другие разделы не задеты.** Дифф содержит ровно 4 HTML-хунка (CSS .bk-block; CSS галереи :282/:285/:294; снятое media-правило; снос bk-block :490-515; модалка m-car) и 3 JS-хунка (openCalendar, комментарий+calLoadBookings, снос bk-контура). Навигация, «Мои ученики», «Документы», профиль — не тронуты; дубликатов id нет (uniq -d пуст); .cal-grid в HTML ровно 1.
4. **BUG-053: компоновка по решению Заказчика.** .gal-grid → grid-template-columns:1fr, одна колонка; снятое media-правило (max-width:900px) осиротевшим не осталось (удалено вместе с двухколоночностью); .gal-big — aspect-ratio 16/9 сохранен + min-height:340px; .gal-thumbs → repeat(auto-fill,minmax(104px,1fr)). DOM-порядок (HTML:608-626): gal-h → mc-big → mc-thumbs → панель «Информация» (mc-info) → панель «Комплектность». Длинный инструктивный form-note удален — это был div без id; динамический #mc-note (HTML:627, использует mcRenderGalActs JS:981) НЕ задет — висячих ссылок нет.
5. **id/обработчики не переименованы; FR-71-путь цел.** mc-big/mc-thumbs/mc-info/mc-compl-lab/mc-compl-badge/mc-bar/mc-missing/mc-acts/mc-prog/mc-big-hint/mc-title/mc-sub/mc-status — все на месте и уникальны; JS-ссылки сходятся 1:1. mcPickGal (:904) на месте, mc-big.onclick → mcPickGal (:876); замена СТС через docsAskReplace, кнопка СТС с data-sts-btn — без правок; test_s8_sts_gallery_replace_dialog (TC-UI-040) диффом не тронут.
6. **Тесты корректны.** TC-UI-041 (:3691): моки в паттерне TC-UI-038 (_route_json method/capture; reject-роут зарегистрирован последним — приоритет page.route, GET /bookings уходит fallback'ом), «МИШУРА»-ассерты (ровно одна .cal-grid, 4 носителя снесенного блока отсутствуют), payload сверяется json.loads({comment}), освобождение слота — через реальный bkApplied→openCalendar (expect class 'cal-slot on'). TC-UI-042 (:3257): порядок в DOM через compareDocumentPosition (устойчивее индексов), отсутствие form-note через :text, boundingBox mc-big ≥320px и выше миниатюры. Обновление TC-UI-028 (:1221): negated-ассерты вместо прежних видимости. Оставшийся в файле #bk-grid (:3591) — кабинет УЧЕНИКА (cabinet.html, #sec-bookings, свой bk-неймспейс) — другая поверхность, ложный след.
7. **Дешевые смоки ревьюера (полный pytest не запускался).** py_compile tests/test_ui_playwright.py → OK; node --check frontend/js/dashboard-instructor.js → OK; `pytest tests/test_ui_playwright.py --collect-only -q` → **52 tests collected** (сходится с «52 passed» ПМ); time.sleep в диффе нет; docstrings TC-UI-041/042 и обновленного TC-UI-028 несут TC-идентификаторы.
8. **Security/XSS.** Добавленного innerHTML в диффе нет (grep '^+.*innerHTML' по frontend/ пуст). innerHTML calBuildGrid — статический шаблон из констант CAL_DAYS/CAL_HOURS/чисел дат; данные API (student_full_name, бренд/модель и пр.) — только textContent/createTextNode через node()/el() (calMarkBookings, bkOpenSlot, mcRender*); innerHTML='' — только очистка контейнеров. Гигиена сохранена.

## Не проверено

- Полный playwright-прогон ревьюером (ограничение потока; результат ПМ «UI 52 passed» принят из спринт-лога, collect-only подтверждает состав сьюта).
- Визуальный результат в браузере на-eye (композиция, отступы «Информация»/«Комплектность» внизу) — только assertions тестов и статический разбор верстки.
- Поведение auto-fill миниатюр на узких вьюпортах (<520px) не измерялось.
- Backend не задет (дифф backend/ не содержит) — отдельно не ревьюился.
