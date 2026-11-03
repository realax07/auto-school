# TC-PD-015 — Поврежденный артефакт при регистрации: 500, пользователь не создается

- Автотест: `tests/test_policy.py::test_s9_register_broken_artifact_500_no_user`
- Приоритет: Must (FR-79, NFR-25)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-personal-data-policy (Спринт 9)
- Трассировка:
  - Requirement: Заменяемость артефакта политики
  - Scenario: Поврежденный артефакт — записи не создаются

## GIVEN / WHEN / THEN
- GIVEN артефакт отсутствует в момент POST /api/register с consent:true
- WHEN POST /api/register
- THEN ответ 500 {ok:false, error:"Сервис: политика персональных данных временно недоступна"}; пользователь НЕ создан

## Примечание
- Партия change add-personal-data-policy (Спринт 9, задача 7.1); кейсы
  живут трассировкой TC-ID в docstring автотеста (rule 6); заголовки
  Requirement/Scenario — дословно specs/PersonalData/spec.md.
