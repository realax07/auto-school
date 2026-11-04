# TC-PD-014 — Смена версии: новый пользователь фиксирует новую версию, прежний сохраняет свою (register)

- Автотест: `tests/test_policy.py::test_s9_register_version_swap_new_user_records_new_version`
- Приоритет: Must (FR-79)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-personal-data-policy (Спринт 9)
- Трассировка:
  - Requirement: Фиксация согласия в данных заявки и регистрации
  - Scenario: Новая версия политики — новые записи фиксируют ее, прежние сохраняют свою

## GIVEN / WHEN / THEN
- GIVEN пользователь создан при артефакте 1.0; артефакт заменен файлом с policy-version: 2.0
- WHEN регистрируется новый пользователь
- THEN новый пользователь фиксирует «2.0» (и свой consent_at); прежний сохраняет «1.0» и свой consent_at — сохраненные значения не переписываются; версия взята сервером из артефакта

## Примечание
- Партия change add-personal-data-policy (Спринт 9, задача 7.1); кейсы
  живут трассировкой TC-ID в docstring автотеста (rule 6); заголовки
  Requirement/Scenario — дословно specs/PersonalData/spec.md.
