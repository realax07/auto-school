# add-instructor-mobile — мобильная адаптивность кабинета инструктора

## Почему

Кабинет инструктора на ≤760px использует legacy-подход (сайдбар сверху
горизонтальной лентой, нет таб-бара, нет top-bar) — раскладка разваливается
на 390×844. Ученический контур получил канон С18 (top-bar + нижний
таб-бар + скрытие сайдбара); инструкторский — без него. Мокапы
design/mocks/mobile-instructor/ (12 экранов, mi-index.html) согласованы
Заказчиком в Telegram 2026-11-18, PR#152 merged.

## Что

Единый канон ≤760px для instructor-dashboard: липкий top-bar (бренд +
инициалы инструктора из /me), нижний таб-бар 5 позиций (День / Неделя /
Кошелёк / Профиль / Ещё→bottom-sheet со остальными разделами), скрытие
десктопного сайдбара, контент у верха с отступом логотипа (~26px),
scrollWidth ≤390 на reference-вьюпорте, hit-targets ≥44px. Desktop >760px
не меняется.

## Границы

- Только presentation-слой: контракты/API/БД не меняются.
- Instructor-choice, instructors (каталог), admin — вне скоупа.
- Волны 20.0–20.5 (см. tasks.md); носители e2e 390×844 + regress.

## Impact

- **Specs**: instructor-mobile — NEW кейпабилити (ADDED). Другие спеки
  не правятся: NFR-26 бюджеты пересчитываются автоматикой (страница
  instructor-dashboard); booking/wallet — только презентационный слой.
- **Носители**: frontend/vue/src/components/InstructorTabBar.vue (новый),
  src/pages/instructor-dashboard/App.vue (top-bar-инициалы, Ещё-шит),
  styles.css (media ≤760 канон), architecture/map.md (карта).
- **Тесты**: tests/web/test_instructor_tabbar.py (новый),
  test_ui_playwright.py (geometry-носитель 390×844), e2e regress.
- **Статика**: static_v не требуется (Vue-бандлы версионированы именами).
- **Deploy**: новый сервис не вводится; миграций нет.
