# TC-PD-012 — Согласие установлено: пользователь создан с фиксацией даты и версии

- Автотест: `tests/test_policy.py::test_s9_register_success_fixes_consent_at_and_policy_version`
- Приоритет: Must (FR-78, FR-79)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-personal-data-policy (Спринт 9)
- Трассировка:
  - Requirement: Обязательное согласие при регистрации ученика
  - Scenario: Согласие установлено — пользователь создан

## GIVEN / WHEN / THEN
- GIVEN чекбокс установлен, форма заполнена валидно (consent:true); артефакт версии 1.0
- WHEN POST /api/register
- THEN 200 {ok:true, token} — сессия как прежде; пользователь создан (роль student); consent_at — момент сабмита (UTC, 'YYYY-MM-DD HH:MM:SS'), consent_policy_version = «1.0»

## Примечание
- Партия change add-personal-data-policy (Спринт 9, задача 7.1); кейсы
  живут трассировкой TC-ID в docstring автотеста (rule 6); заголовки
  Requirement/Scenario — дословно specs/PersonalData/spec.md.
