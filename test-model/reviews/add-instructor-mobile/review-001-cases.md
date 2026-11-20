<!-- Reviewer-Delegation: deleg-s20-qar-external | независимый qa-case-reviewer (не автор диффа) | ревью кейсов TC-S20-001…004 | ветка: feature/instructor-mobile | дата: 2026-11-19 -->

# QA-review кейсов — add-instructor-mobile

## Вердикт

**одобрить 4/4** (TC-S20-001…004 approved; minor исправлены ревьюером:
ассерт сайдбара переведён с to_have_count(0) на not_to_be_visible —
сайдбар скрыт CSS, но присутствует в DOM; desktop-инвариант — «not True»
(v-if absent); учётные данные test-сервера — ui-admin/ui-admin-pass-2026
из фикстуры server (test_ui_playwright), не глобальный админ).

## Проверка

1. Трассировка: каждый TC → требование спеки instructor-mobile (таб-бар
   ≤760 / top-bar инициалы / hit-targets+переполнение / desktop-инвариант) —
   полная, дыр нет; coverage.md синхронна.
2. Носители: test_instructor_tabbar.py (3 теста) — исполняются на
   390×844; шаги ручной проверки воспроизводимы.
3. Вербатим-цитаты соответствуют коду носителей (строки локаторов/ассертов
   сверены grep'ом).
4. Спека instructor-mobile: 4 требования ADDED, все покрыты.

## Гейт на HEAD

strict 28/28; budgets OK (14 страниц); flow_check — один FLOW-ERROR
(этот review отсутствовал) — данным файлом закрывается.
