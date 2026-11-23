# Approved-кейсы — add-roles-theme-landing (Спринт 21)

- Итог: одобрить
- Кейсы: TC-S21-001…010 (test_ui_playwright.py) — выбор роли при
  регистрации, лендинг-блок ГигаЧата интерактивен, темы light/dark/system.
- Трассировка: impact add-roles-theme-landing (§registration MODIFIED,
  §theme ADDED, §landing-assistant ADDED); review-001-cases.md
  (test-model/reviews/add-roles-theme-landing/) — сводный ПМ-review волн
  21.2/21.3/21.4; regress-final.md — 632 passed, exit 0.

| TC | Носитель | Покрытие |
|---|---|---|
| TC-S21-001 | test_ui_playwright::test_tc_s21_001 | choice-шаг виден, форма скрыта |
| TC-S21-002 | test_ui_playwright::test_tc_s21_002 | ученик-форма + возврат |
| TC-S21-003 | test_ui_playwright::test_tc_s21_003 | инструктор → /instructors/apply |
| TC-S21-004 | test_ui_playwright::test_tc_s21_004 | send-guest → регистрация + ai_prefill |
| TC-S21-005 | test_ui_playwright::test_tc_s21_005 | quick-guest → регистрация + ai_prefill |
| TC-S21-006 | test_ui_playwright::test_tc_s21_006 | send-logged → /cabinet |
| TC-S21-007 | test_ui_playwright::test_tc_s21_007 | тема toggle без reload |
| TC-S21-008 | test_ui_playwright::test_tc_s21_008 | тема persist после reload |
| TC-S21-009 | test_ui_playwright::test_tc_s21_009 | «Авто» снимает ключ (prefers) |
| (chat s19) | test_ui_playwright::test_tc_s19_home_chat_* | кабинет-чат не регрессировал |

«Итог: одобрить» — кейсы approved (qa_case_reviewer-прецедент С19,
контракт 5).
