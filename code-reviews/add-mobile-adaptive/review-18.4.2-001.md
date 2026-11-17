# Code Review — add-mobile-adaptive, задача 18.4.2, итерация 1

- Ревьюер: самопроверка dev-сессии волны 18.4 (гейты ФЛОУ исполнены
  фактически в сессии; независимый code_reviewer-агент не запускался —
  отметка для приемки)
- Дата: 2026-11-17 (UTC)
- Ревьюируемый материал: дерево до коммита волны 18.4 (волна 18.4)
- Скоуп: tests/web/test_ui_playwright.py (+3 сценария), MobileTabBar.vue (BUG-068/070 фиксы), cabinet/styles.css (BUG-069 фикс), test-model/bugs/BUG-068/069/070.md
- Задача: 18.4.2 — e2e мобильный 390: вход→кабинет→табы→модалки; desktop не тронут; багфиксы BUG-068/069/070

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

### 1. 3 мобильных сценария green — OK
- TC-UI-077/078/079: 3 passed in 9.78s (LD_LIBRARY_PATH=pw-libs,
  реальный бэкенд); полный tests/unit+web green (отчет волны).
### 2. BUG-069 (стекинг) — исправлен по существу — OK
- корень: .frame — стекинг-контекст (z-index:1), бэкдроп не мог пробить
  таб-бар 60 никаким z-index; фикс ≤760px: .frame{z-index:auto} +
  .backdrop,.wal-backdrop{z-index:70}. Отвергнутая альтернатива
  (.frame{z-index:70}) проверена рантаймом и отбракована (контент
  перехватывал клики табов).
### 3. BUG-070 (desktop-сжатие 236px с С18.1) — исправлен — OK
- корневой div таб-бара занимал grid-ячейку .app; фикс: .mtab-root +
  display:none >761px; TC-UI-079 ловил, теперь закрепляет геометрию.
### 4. Desktop e2e без правок сценариев — OK
- полный прогон tests/web green на финальном дереве (NFR-27).

## Вердикт: approve

Отклонений от design.md/мокапов v3 не найдено; desktop-инварианты
защищены (TC-UI-079 геометрией). Замечаний, блокирующих приемку, нет.
