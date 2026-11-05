<!--
Reviewer-Delegation: deleg-cr-bug0547-external
Reviewer: code_reviewer (AI Factory, независимая сессия; плейсхолдер id — ПМ заменит)
Дифф: bugfix/s9-ui-followup-2 vs main. Коммит задачи: 361453f (fix BUG-057) + синхронная правка мокапа в 62c0cf0.
Диапазон из задания d081bcf..HEAD шире скоупа (содержит влитый Спринт 9);
ревьюировался дельта-дифф ветки main..HEAD (merge-base = 42367e1).
Дата ревью: 2026-11-04
-->

# Code Review — BUG-057 (кабинет инструктора: контент секций от ВЕРХА)

## Что проверено (Scenario)

1. **CSS-правка по существу** — instructor-dashboard.html:14: `main{...;margin:auto}` → `margin:0 auto`. Корень верен: у grid `.app` (min-height:100vh) auto-маргины грид-элемента поглощают свободное место ДО stretch — короткий main центрировался по вертикали; `0 auto` убирает вертикальное авто-центрирование, сохраняя горизонтальное (max-width:1600px). Комментарий с разбором корня добавлен (:9-13). Дифф — ровно одна CSS-строка + комментарий, лейаут сайдбара/секций не задет.
2. **Мокап синхронно** — design/mocks/dashboard-instructor.html:9: идентичная строка `main{padding:28px clamp(20px,3vw,44px) 45px;max-width:1600px;width:100%;margin:0 auto}` — needle-сравнение ревьюера: строка дословно совпадает в странице и мокапе (design-guard не разорван).
3. **Вербатим-тест зеленый** — test_dashboard_page_mockup_texts_verbatim (tests/test_instructor_dashboard.py, сверяет тексты И все CSS-строки мокапа): прогон ревьюера tests/test_login_modal.py + test_instructor_pages.py + test_instructor_dashboard.py → **30 passed**.
4. **Вычисленные стили в реальном браузере** (смок ревьюера: реальный uvicorn, моки shell по образцу TC-UI-033, /instructor/dashboard): computed margin-top=0px и margin-bottom=0px у main; bounding box main y=0 (прижат к верху вьюпорта); первый контентный блок .topbar на 28px от верха main — «сверху с небольшим отступом» выполнено дословно.
5. **Пересечений нет** — margin:auto на main больше нигде в файле не используется; на других страницах (cabinet.html и пр.) правка не отразилась (файл один, селектор локальный).

## Вердикт: approve

## Замечания

Замечаний blocker/major/minor нет.

### Наблюдение (вне вердикта)

- Вертикальное поведение теперь определяется дефолтным stretch у `.app` (align-items не задан явно). Сейчас это ровно то, что нужно; если однажды у .app появится align-items, поведение снова изменится неявно. Явно зафиксировать `align-items:start` у `.app` можно в будущем спринте — не замечание.

## Не проверено

- Визуальный результат на-eye на коротких секциях (проверено computed-геометрией на секции по умолчанию «Мой день»).
- Полный pytest-сьют не запускался (указание ПМ: 409 passed); точечный регресс ревьюера — см. отчет.
