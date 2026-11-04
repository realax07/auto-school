# TC-PD-008 — Согласие установлено: заявка создана с фиксацией даты и версии

- Автотест: `tests/test_policy.py::test_s9_apply_success_fixes_consent_at_and_policy_version`
- Приоритет: Must (FR-77, FR-79)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-personal-data-policy (Спринт 9)
- Трассировка:
  - Requirement: Обязательное согласие при регистрации инструктора
  - Scenario: Согласие установлено — заявка создана

## GIVEN / WHEN / THEN
- GIVEN чекбокс установлен (consent:true), анкета заполнена валидно; артефакт версии 1.0
- WHEN POST /api/instructors/apply
- THEN 200 {ok:true}; заявка создана (status waiting); consent_at — момент сабмита (UTC сервера, формат 'YYYY-MM-DD HH:MM:SS'), consent_policy_version = «1.0» = версии артефакта

## Примечание
- Партия change add-personal-data-policy (Спринт 9, задача 7.1); кейсы
  живут трассировкой TC-ID в docstring автотеста (rule 6); заголовки
  Requirement/Scenario — дословно specs/PersonalData/spec.md.
