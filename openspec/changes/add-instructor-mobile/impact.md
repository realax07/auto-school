# Impact-карта — add-instructor-mobile

## Затронутые сервисы
- Backend: без изменений (только чтение /api/auth/me — существующий контракт).
- Frontend: instructor-dashboard (App.vue, styles.css), новый InstructorTabBar.vue.

## Контракты
- openapi-дельта: отсутствует (IR-01 не задевается).

## Статика (static_v?)
- Vue-бандлы версионированы именами файлов; static_v не трогается (IR-03).

## Deploy-матрица и RUNBOOK
- Новый сервис не вводится (IR-02 не задевается); порядок выкатки — штатный.

## Миграции
- Отсутствуют (IR-04 не задевается).

## Тесты
- Новые: tests/web/test_instructor_tabbar.py; изменённые: test_ui_playwright.py
  (+geometry-носитель С20). Домены регресса: instructor-dashboard e2e.
