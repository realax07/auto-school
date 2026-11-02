# TC-UI-039 — «Мои ученики»: карточки со счетчиками, подраздел «Запросы учеников», принятие (ОВ-5)

- Автотест: `tests/test_ui_playwright.py::test_s8_my_students_cards_counters_and_requests_subtab`
- Приоритет: Must (FR-75, ОВ-5)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-s8-cars-docs-booking (Спринт 8)
- Трассировка:
  - Requirement: Раздел «Мои ученики» со счетчиками занятий (openspec/changes/add-s8-cars-docs-booking/specs/student-requests/spec.md)
  - Scenario: Карточка ученика с занятями показывает счетчики (openspec/changes/add-s8-cars-docs-booking/specs/student-requests/spec.md)
  - Scenario: Пара без броней — корректное пустое состояние (openspec/changes/add-s8-cars-docs-booking/specs/student-requests/spec.md)
  - Scenario: Запросы — подраздел по требованию внутри раздела — ОВ-5 (openspec/changes/add-s8-cars-docs-booking/specs/student-requests/spec.md)

## GIVEN / WHEN / THEN
- GIVEN дашборд инструктора с замоканным API (бэкенд-волна 9.1 параллельна): GET /api/instructor/students — Ежов Павел Дмитриевич (next_lesson 03.11.2026 14:00, planned 2, completed 5) и Титова с XSS-payload в ФИО (next_lesson None, 0/0); GET /api/instructor/requests — new-запрос Сафина Артура Кирилловича; accept 301 → добавляет Сафина в students
- WHEN открыт раздел «Мои ученики»; проверяются карточки и навигация; клик вкладки «Запросы учеников» и обратно-логика подраздела; принятие запроса (выбор авто → подтвердить)
- THEN пункта сайдбара «Запросы учеников» НЕТ (ОВ-5 — подраздел, не отдельный пункт); карточек 2, счетчик раздела «·2»; Ежов: «03.11.2026 · 14:00», счетчики «2» плановых занятий дальше / «5» проведено; Титова: «нет — подтверждённых броней впереди не запланировано», 0/0; XSS-гигиена: img в карточках нет, window.__xss undefined (ФИО с тегом отрисовано текстом — createElement/textContent); подраздел «Запросы учеников» открывается по требованию (#stu-tab-requests виден, основной список скрыт), запрос Сафина виден («·1», «·1» new); после принятия — toast «Заявка принята», карточек 3, Сафин первый в основном списке, «·3»

## Примечание
- Партия change add-s8-cars-docs-booking (Спринт 8); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); полный прогон
  359 passed (integration, лог ПМ).
- В этом же тест-файле есть автоматизированный TC-UI-039b
  (test_s8_my_students_missing_backend_honest_error — честная ошибка при
  404 от GET /api/instructor/students); он вне диапазона партии
  TC-UI-033…040, отдельный кейс не заказан — noted для ПМ.
