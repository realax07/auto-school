# TC-PD-013 — Порядок проверок 1 → 1a: пустая фамилия при consent:true → «Фамилия: поле обязательно»

- Автотест: `tests/test_policy.py::test_s9_register_empty_surname_checked_before_consent`
- Приоритет: Must (FR-78, design MIN-2)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-personal-data-policy (Спринт 9)
- Трассировка:
  - Requirement: Обязательное согласие при регистрации ученика
  - Scenario: Прямой POST /api/register без согласия отклоняется сервером

## GIVEN / WHEN / THEN
- GIVEN форма с пустой фамилией и consent:true (согласие стоит)
- WHEN POST /api/register
- THEN 422 {ok:false, error:"Фамилия: поле обязательно"} — обязательные поля проверяются ДО проверки согласия (позиция 1a после позиции 1); пользователь не создан

## Примечание
- Партия change add-personal-data-policy (Спринт 9, задача 7.1); кейсы
  живут трассировкой TC-ID в docstring автотеста (rule 6); заголовки
  Requirement/Scenario — дословно specs/PersonalData/spec.md.
