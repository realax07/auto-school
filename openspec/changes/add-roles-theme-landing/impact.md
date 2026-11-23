# Impact-карта — add-roles-theme-landing

> Обязательный артефакт СА (J58): заполняется при create_change, до dev-задач.
> Волны: 21.2 роли (dev готов), 21.3 лендинг-блок (dev готов), 21.4 темы (dev готов).

## Затронутые сервисы

- frontend лендинг: vue/index.html (assistant-блок интерактивен — input#ai-input,
  quick data-scenario; статическая регистровая модалка удалена — компонент
  shared/RegisterModal.vue единственный носитель, choice-шаг роли), App.vue
  (wiring: regShowChoice/regShowStudentForm, инструктор → /instructors/apply,
  ai-send/quick → ai_prefill + регистрация/кабинет), styles.css (.reg-choice).
- frontend кабинет: cabinet.html (boot data-theme ДО CSS), App.vue (ai_prefill
  подхват в aiDraft при mount), styles.css (light-инверсионный режим MVP +
  .theme-seg), components/StudentSidebar.vue (theme-seg Тёмная/Светлая/Авто).
- backend: НЕ затронут (RegisterRequest.role контрактный; git diff backend — пуст).

## Контракты

openapi-дельт нет: /api/register (role контрактный) и /api/ai/chat — без
изменений; contracts/openapi.json не перегенерируется.

## Статика (static_v?)

frontend/Vue-страницы (не backend/static) — static_v не трогается; сборка
dist — обязательный шаг перед pytest (наследование С12/С15).

## Deploy-матрица и RUNBOOK

Новый сервис? — нет (ai-bridge из 19.7 остаётся; 21.x — только фронт/сборка).
Порядок выкатки: build --no-cache → up -d (сборка dist в образе —
frontend-builder). Откат — прежний образ.

## Миграции

Миграций нет (theme — localStorage; выбор роли — существующие поля RegisterRequest).

## Тесты

- tests/web/test_ui_playwright.py: TC-S21-001…010 (роли, лендинг-блок, темы).
- tests/web/test_login_modal.py: срез по фактическому маркеру (компонент) —
  адаптация носителя без ослаблений.
- tests/web/test_static.py TC-REG-018: носитель перенесён на
  RegisterModal.vue (+ choice-проверка).
- regress --final полный: 632 passed, exit 0 (артефакт regress-final.md
  последним коммитом; LD_LIBRARY_PATH-среда — воспроизводимость подтверждена
  review-…-004 прогоном ревьюера).
