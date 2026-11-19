# PLAN-add-ai-chat-home — план релиза Спринта 19

Флоу: 1

## Цель

Главный экран кабинета ученика = ИИ-чат (мобилка + вебка, по утвержденным
макетам) + Гига ГАИшник v1 (POST /api/ai/chat, история 14 дней, временный
провайдер — сессия ассистента с системным промптом).

## Зоны записи (по задачам)

- 19.1 СА: openspec/changes/add-ai-chat-home/**, sdd.md — ЗАКРЫТА
  (commit c89c7f4, strict 28/0).
- 19.2 dev-backend: backend/ai/**, backend/app.py (только регистрация
  домена/роутов), backend/core/db.py (только миграция ai_messages),
  tests/unit/test_s19_ai_chat.py (юнит-носитель, TC-трассировка),
  openspec/changes/add-ai-chat-home/tasks.md.
- 19.3 dev-frontend: frontend/vue/src/pages/cabinet/**,
  frontend/vue/cabinet.html (pre-boot разметка — правило двух копий),
  tests/web/test_cabinet_page.py (перевод вербатим-гардов на новые макеты),
  tests/web/test_ui_playwright.py (вкл. носитель TC-UI-060), design/mocks
  (правки только при каноне), openspec/changes/add-ai-chat-home/tasks.md.
- 19.4 QA/design/приемка: test-model/**, code-reviews/**, PLAN.md, BACKLOG.md;
  API-носитель tests/api/test_s19_ai_chat.py пишет qa_automation (зона
  tests/api/** — политика ролей текущей фабрики; уточнение ПМ поверх
  arch-review 001/002, процессное: dev-зона = tests/unit/** только).

## Итог волн (факты, верифицировано ПМ)

- 19.2 backend: 4 коммита (efb46de/9d0bfef/3331c2c/aed2fb3), юнит-носитель
  14 passed (TC-S19-001…012), CR approve (review-19.2-001→фиксы→005).
- 19.3 frontend: 3 коммита (9dafce1/0cc091c/df64d0a), сборка OK,
  скрин-пробы 390/1280 с компьютед-доказательствами, CR approve
  (review-19.3-001→фикс гэпа 18px→002).
- 19.4 QA: кейсы (9 TC, review-001→фикс MAN-001→002 approve → approved
  партия verbatim), носители + API-носитель + отчет маппинга
  (test-model/reports/qa-auto-report-add-ai-chat-home.md), design approve
  (review-001-design), regress-final PASS (перепрогон после T-флака
  nfr001/latency — класс T-4 техраздела BACKLOG).
- Верификация ПМ: юнит 14 passed, браузерные 94 passed (LD_LIBRARY_PATH
  pw-libs), полный сьют 533 passed + regress PASS, strict 28/0.

## Волны

Последовательно: 19.2 (backend) → 19.3 (frontend от backend-коммита,
интеграционные e2e на живом API) → 19.4 (QA, design check, regress, PR).

## Критерий приемки

- Полный pytest зеленый (строка счета в выводе), e2e-носители нового
  экрана + сохраненные носители кабинета без ослаблений.
- openspec validate --all --strict = 0 ошибок; оба flow_check (репо +
  фабрика) без FLOW-ERROR.
- regress-final PASS; review-файлы с approve на каждую задачу; приемка
  [x] с ревью; один PR [add-ai-chat-home] на зеленом CI.

## Решения Заказчика

decision 2026-11-18-s19-ai-chat-home (phase 1, create_change, commit
d936a3e); требования requirements-ai-chat-home.md УТВЕРЖДЕН; макеты
утверждены («Вот теперь отлично. Так и делай», «Все верно, начинай»).
