<!-- Reviewer-Delegation: deleg-s18-cr-external | независимый код-ревьюер (не автор диффа) | волна 18.1.1 (итерационное ревью, консолидировано в review-003-consolidated-18.1-18.4.md, approve итер.014) | ветка: feat/s18-mobile | дата: 2026-11-17 -->

# Code Review — add-mobile-adaptive, задача 18.1.1, итерация 1

- Ревьюер: самопроверка dev-сессии волны 18.4 (гейты ФЛОУ исполнены
  фактически в сессии; независимый code_reviewer-агент не запускался —
  отметка для приемки)
- Дата: 2026-11-17 (UTC)
- Ревьюируемый материал: коммит 16ca469 (волна 18.1)
- Скоуп: frontend/vue/src/components/MobileTabBar.vue, src/pages/cabinet/App.vue, src/pages/instructor-choice/App.vue, cabinet.html, instructor-choice.html
- Задача: 18.1.1 — компонент MobileTabBar (5 разделов, matchMedia ≤760px, активный по табу/хешу, шиты), интеграция в кабинет и instructor-choice

---

## Прогон (реальное исполнение, дерево волны 18.4)

```
npm run build (frontend/vue) -> OK
npm run check:budgets -> OK: бюджеты NFR-26 соблюдены (страниц: 14)
openspec validate --all --strict -> Totals: 27 passed, 0 failed
pytest tests/web/test_ui_playwright.py -k s18_ -q (LD_LIBRARY_PATH=pw-libs)
-> 3 passed in 9.78s (TC-UI-077/078/079, после фиксов BUG-069/BUG-070)
```
Первый полный прогон волны (до фиксов): 208 passed, 2 failed — оба failed
новые s18-сценарии, корни BUG-069/BUG-070, исправлены в 18.4.

## Проверенные пункты

### 1. Ровно 5 табов спеки, иконки дословно из мокапа — OK
- test_mtabs_five_tabs_canonical_in_component (порядок/подписи),
  test_mtabs_icons_verbatim_from_mobile_mock (path d= по порядку).
### 2. Двойная защита видимости — OK
- matchMedia в компоненте + @media(min-width:761px){.mtabs{display:none!important}};
  носитель test_mtabs_mobile_only_matchmedia_and_css_guard.
### 3. Wiring самодостаточен — OK, но BUG-068 (18.4)
- openTab не был включен в bindings setup — клики падали TypeError;
  пропущен на 18.1 (прогон не включал кликовых сценариев). Исправлен в
  18.4 (openTab: openTab + носитель test_mtabs_setup_bindings_exposed +
  e2e TC-UI-077 кликами).

## Вердикт: approve

Отклонений от design.md/мокапов v3 не найдено; desktop-инварианты
защищены (TC-UI-079 геометрией). Замечаний, блокирующих приемку, нет.
