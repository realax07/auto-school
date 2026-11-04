# TC-PD-004 — Текст политики отсутствует в исходниках страниц (grep frontend/**)

- Автотест: `tests/test_policy.py::test_s9_policy_text_absent_from_frontend_sources`
- Приоритет: Must (FR-76, NFR-25)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-personal-data-policy (Спринт 9)
- Трассировка:
  - Requirement: Публичная страница политики персональных данных (/policy)
  - Scenario: Текст политики отсутствует в исходниках страниц

## GIVEN / WHEN / THEN
- GIVEN сервис развернут с актуальным артефактом; исходники — frontend/**.html и frontend/**.js (все подключаемые ES-модули; собранных бандлов нет)
- WHEN поиск по исходникам: маркер «152-ФЗ», контакт из раздела «Контакты» и фрагмент середины каждого абзаца текста артефакта
- THEN ни одной строки текста политики ни в одном файле не найдено — текст поступает только из артефакта через API

## Примечание
- Партия change add-personal-data-policy (Спринт 9, задача 7.1); кейсы
  живут трассировкой TC-ID в docstring автотеста (rule 6); заголовки
  Requirement/Scenario — дословно specs/PersonalData/spec.md.
