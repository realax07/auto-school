# TC-PD-009 — Смена версии: новая заявка фиксирует новую версию, прежняя сохраняет свою (apply)

- Автотест: `tests/test_policy.py::test_s9_apply_version_swap_new_application_records_new_version`
- Приоритет: Must (FR-79)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-personal-data-policy (Спринт 9)
- Трассировка:
  - Requirement: Фиксация согласия в данных заявки и регистрации
  - Scenario: Новая версия политики — новые записи фиксируют ее, прежние сохраняют свою

## GIVEN / WHEN / THEN
- GIVEN заявка создана при артефакте 1.0; артефакт заменен файлом с policy-version: 2.0
- WHEN создается новая заявка (клиент версию не присылает)
- THEN новая заявка фиксирует «2.0», прежняя сохраняет «1.0»; версия прочитана сервером из метаданных артефакта на момент сабмита

## Примечание
- Партия change add-personal-data-policy (Спринт 9, задача 7.1); кейсы
  живут трассировкой TC-ID в docstring автотеста (rule 6); заголовки
  Requirement/Scenario — дословно specs/PersonalData/spec.md.
