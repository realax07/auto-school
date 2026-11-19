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
  tests/web/test_cabinet_page.py (перевод вербатим-гардов на новые макеты),
  tests/web/test_ui_playwright.py (вкл. носитель TC-UI-060), design/mocks
  (правки только при каноне), openspec/changes/add-ai-chat-home/tasks.md.
- 19.4 QA/design/приемка: test-model/**, code-reviews/**, PLAN.md, BACKLOG.md;
  API-носитель tests/api/test_s19_ai_chat.py пишет qa_automation (зона
  tests/api/** — политика ролей текущей фабрики; уточнение ПМ поверх
  arch-review 001/002, процессное: dev-зона = tests/unit/** только).

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
