# TC-PD-005 — Ссылка на /policy видна из обоих мест согласия (wiring обоих контуров)

- Автотест: `tests/test_policy.py::test_s9_policy_link_visible_in_both_consent_blocks`
- Приоритет: Must (FR-76)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-personal-data-policy (Спринт 9)
- Трассировка:
  - Requirement: Публичная страница политики персональных данных (/policy)
  - Scenario: Ссылка на политику видна из обоих мест согласия

## GIVEN / WHEN / THEN
- GIVEN блок согласия анкеты инструктора (checkline) и модалка регистрации ученика (reg-check перед кнопками)
- WHEN проверка объединенного источника HTML + ES-модулей (frontend_source)
- THEN в обоих источниках есть href="/policy" target="_blank" внутри блока согласия; apply.js отправляет consent в multipart; landing.js держит #reg-submit disabled до установки #reg-consent и добавляет consent в payload

## Примечание
- Партия change add-personal-data-policy (Спринт 9, задача 7.1); кейсы
  живут трассировкой TC-ID в docstring автотеста (rule 6); заголовки
  Requirement/Scenario — дословно specs/PersonalData/spec.md.
