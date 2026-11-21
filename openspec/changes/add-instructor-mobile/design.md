# Design — add-instructor-mobile

Канон = ученический С18 (MobileTabBar.vue) + мокапы mi-*. Реализация
повторяет проверенные механики: fixed top-bar (sticky), нижний таб-бар
54px (fixed, hit ≥44), Ещё→bottom-sheet (grab-хендл + blur), медиа ≤760.

## Решения

1. InstructorTabBar.vue — самодостаточный компонент (emit('tab') в
   bridge.navTo инструкторского App.vue; props activeTab). Пять позиций:
   День/Неделя/Кошелёк/Профиль + Ещё. Ещё → bottom-sheet: Календарь,
   Мои ученики, Мои автомобили, Материалы и обучение, Выход.
2. Top-bar: бренд «СберАвтошкола · инструктор» + инициалы — GET
   /api/auth/me (тот же паттерн MobileTabBar С18: 401/403/!ok → '/').
3. Сайдбар >760px — без изменений; ≤760px — display:none (media в
   styles.css, как StudentSidebar С18).
4. Контент: .frame padding-top 26px (отступ логотипа, спека С18 MUST),
   снизу резерв 54+12px под таб-бар.
5. Таблицы доходов: card-режим ≤760 уже существует (С16) — сохранить.
6. Хвосты: дублировать pre-boot разметку не требуется — App.vue монтируется
   поверх #app (штатный паттерн).

## Носители (инвентарь)

- InstructorTabBar.vue, instructor-dashboard/App.vue (+styles.css ≤760),
  architecture/map.md.
- tests/web/test_instructor_tabbar.py (новый: таб-бар, Ещё-шит, инициалы),
  tests/web/test_ui_playwright.py: test_s20_instructor_geometry
  (scrollWidth ≤390, hit ≥44, frame pad 20..30).
