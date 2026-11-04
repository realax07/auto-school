# TC-PD-010 — Поврежденный артефакт при сабмите анкеты: 500, заявка не создается

- Автотест: `tests/test_policy.py::test_s9_apply_broken_artifact_500_no_application`
- Приоритет: Must (FR-79, NFR-25)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-personal-data-policy (Спринт 9)
- Трассировка:
  - Requirement: Заменяемость артефакта политики
  - Scenario: Поврежденный артефакт — записи не создаются

## GIVEN / WHEN / THEN
- GIVEN артефакт отсутствует (POLICY_FILE указывает на несуществующий файл) в момент POST /api/instructors/apply с consent:true
- WHEN POST /api/instructors/apply
- THEN ответ 500 {ok:false, error:"Сервис: политика персональных данных временно недоступна"}; заявка НЕ создана — фиксация версии невозможна

## Примечание
- Партия change add-personal-data-policy (Спринт 9, задача 7.1); кейсы
  живут трассировкой TC-ID в docstring автотеста (rule 6); заголовки
  Requirement/Scenario — дословно specs/PersonalData/spec.md.
