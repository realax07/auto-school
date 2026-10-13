# TC-INS-010 — Инициалы аватара из ФИО + guard пустых значений

- ID кейса: TC-INS-010
- ID чеклиста: CHK-10
- Источник: CHK-10 → Requirement «ФИО инструктора из учетной записи» → FR-20; Scenario «Инициалы аватара из ФИО»; граница — guard MIN-4 review-001-3.1 (закрыт review-002, контроль D4)
- Тип: позитивный (граничный)
- Приоритет: Must
- Статус: automated — wiring-контроль (tests/test_instructor_dashboard.py::test_dashboard_page_wiring_fr18_fr20_fr22: инициалы = первые буквы surname и name, filter(Boolean), запись в .avatar); рендер в браузере с краевыми данными — manual/toBeAutomated (Playwright)

## GIVEN / WHEN / THEN
- GIVEN одобренный инструктор вошел и открыл кабинет
- WHEN страница отображается
- THEN в аватаре показаны инициалы, вычисленные из ФИО («Иванов Иван …» → «ИИ»), не демо-«МС»; граничный guard: при пустых surname/name после trim инициалы не дают undefined/«NAN» — {Петров,Пётр}→«ПП», {'',Пётр}→«П», пустые→пустая строка (filter(Boolean))

## Предусловия
- Для wiring-части: frontend/instructor-dashboard.html доступен.
- Для UI-части: браузер/Playwright; возможность подставить краевые данные (фиктивный ответ API с пустыми surname/name через перехват сети/мок fetch).

## Шаги
1. Проверить JS страницы: вычисление fio = [surname, name, patronymic].filter(Boolean).join(' '); initials из первых букв surname и name с filter(Boolean).
2. (UI) Войти инструктором «Иванов Иван Иванович», открыть кабинет: аватар = «ИИ», демо-«МС» отсутствует.
3. (UI, граница) Перехватить ответ /api/instructor/dashboard, подставить instructor = {"surname": "", "name": "Пётр", "patronymic": ""} → аватар = «П», не «NAN»/«undefined».
4. (UI, граница) Подставить instructor = {"surname": "", "name": "", "patronymic": ""} → аватар = пустая строка.
5. (UI, граница) Подставить instructor = {"surname": "Петров", "name": "Пётр", "patronymic": ""} → аватар = «ПП».

## Ожидаемый результат
1. В коде filter(Boolean) присутствует — пустые компоненты исключаются до join/map.
2–5. Аватар соответственно «ИИ», «П», «» (пусто), «ПП»; ни в одном случае нет строк «NAN», «undefined», «null».

## Тестовые данные
Основной: «Иванов Иван Иванович» → «ИИ». Краевые: {'',Пётр}→«П»; {'',''}→''; {Петров,Пётр}→«ПП».
