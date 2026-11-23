# Review-001 — сводный ПМ-review волн 21.2/21.3/21.4 (add-roles-theme-landing)

- Reviewer-Delegation: deleg-s21-external | дата: 2026-11-23 | внешняя hermes-сессия
- Объект: волны 21.2 (выбор роли при регистрации), 21.3 (лендинг-блок
  ГигаЧата интерактивен), 21.4 (темы light/dark/system) —
  код+носители commits 44fc6cc..HEAD (fix/s21-roles-theme-landing).
- Метод: чтение диффа, машинные прогоны носителей
  (TC-S21-001…010: 10 passed; login_modal 5 passed; s19-носители
  15 passed; contract 10 passed), regress --final
  (632 passed, exit 0 — артефакт regress-final.md последним коммитом).

## Периметр

- 21.2.1/21.2.2: RegisterModal.vue — choice-шаг «Я ученик/Я инструктор»
  по мокапу auth-register-choice (утв. 2026-11-19); инструктор →
  /instructors/apply (существующая анкета, модерация); ученик → форма
  (контракт RegisterRequest.role без правок backend — проверено git diff
  backend = пуст). Статические легаси-копии модалок index.html удалены
  (id-дубли ломали choice — подтверждено экспериментом ревьюера-001/002).
- 21.2.3/21.2.4: TC-S21-001…003 (test_ui_playwright.py), test_login_modal
  срез по фактическому маркеру компонента (2 теста, 5 passed),
  architecture/map.md блоки 21.1/21.3/21.4.
- 21.3.1: лендинг-блок assistant интерактивен (index.html + template
  App.vue — правило двух копий): input#ai-input, quick data-scenario;
  send незалогиненному → модалка регистрации с подсказкой + ai_prefill;
  залогиненному → /cabinet чат «Главной» с предзаполнением.
- 21.3.2: TC-S21-004…006 (send-guest, quick-guest, quick-logged).
- 21.4.1: boot data-theme в cabinet.html ДО CSS (localStorage 'theme' |
  prefers-color-scheme → dark); light = инверсионный MVP-режим (задокументировано
  в tasks/impact/design — полноценная палитра следующая волна);
  theme-seg Тёмная/Светлая/Авто в StudentSidebar (setTheme, выше учётки —
  учётка прижата к низу, TC-UI-059 сохранён).
- 21.4.2: TC-S21-007…009 (toggle без reload, persist, auto-дефолт).

## Верификации

- regress --final полный: **632 passed, exit 0** (LD_LIBRARY_PATH-среда;
  воспроизводимость подтверждена независимым прогоном ревьюера-004 —
  632 passed, 778.78s) — артефакт regress-final.md последним коммитом.
- Носители: tc_s21 10 passed; reg/consent/s19-носители 13 passed;
  login_modal 5 passed; contract 10 passed.
- code_reviewer внешние итерации: review-…-001 (return, 3 MAJ + MIN) →
  фикс-коммиты → review-…-002 (return, MAJ-1 NOT-FIXED остальное
  confirmed) → фиксы → **review-…-003 (MAJ-1 FIX-CONFIRMED; return по
  средовым пунктам regress, см. ниже) → review-…-004 (approve,
  воспроизводимость LD-среды подтверждена прогоном ревьюера 632 passed)**.
- Границы тем FR-19.6: кабинет-чат не тронут; лендинг-блок ведёт на
  регистрацию/кабинет (без прямых GLM-вызовов для незалогиненных).

## Findings (учтены в фикс-волнах)

- review-…-001 (return): MAJ-1 легаси-модалки index.html (id-дубли) —
  удалены; MAJ-2 сиротская форма pre-mount — удалена; MAJ-3 alert-заглушки
  — сняты; MAJ-4 quick logged → /cabinet — реализовано; MIN-1 DIAG —
  вычищен; MIN-5 носитель quick+logged — добавлен.
- review-…-002 (return): MAJ-1 test_login_modal срез по фактическому
  маркеру компонента + шапка index.html правдива — исправлено; MIN-2
  спека theme приведена к MVP-инверсии; MIN-4 TypeError/None-guard;
  MIN-5 носитель quick+logged — добавлен.
- MIN-3 (theme-mode отдельный ключ) — следующее касание (зафиксировано
  в review-…-002; не блокирует).

## Итог: одобрить

Все волны 21.2/21.3/21.4 реализованы по утверждённым мокапам; носители
TC-S21-001…010 зелёные; regress-final 632 passed (exit 0) на HEAD;
верификация воспроизводимости LD-среды — review-…-004 approve.
