# TC-PD-003 — Битый/отсутствующий артефакт: честная 500 {ok:false} без раскрытия содержимого

- Автотест: `tests/test_policy.py::test_s9_policy_broken_or_missing_artifact_500_no_leak`
- Приоритет: Must (FR-76, NFR-10)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-personal-data-policy (Спринт 9)
- Трассировка:
  - Requirement: Публичная страница политики персональных данных (/policy)
  - Scenario: Артефакт поврежден — честная ошибка страницы

## GIVEN / WHEN / THEN
- GIVEN матрица повреждений: файл отсутствует; нет разделителя ---; пустой текст после ---; нет policy-version; policy-date не YYYY-MM-DD; строка шапки без ключа
- WHEN гость вызывает GET /api/policy для каждого варианта
- THEN каждый ответ 500 {ok:false, error:"Политика: временно недоступна"}; содержимое битого артефакта в теле ответа не раскрывается; сервис не падает

## Примечание
- Партия change add-personal-data-policy (Спринт 9, задача 7.1); кейсы
  живут трассировкой TC-ID в docstring автотеста (rule 6); заголовки
  Requirement/Scenario — дословно specs/PersonalData/spec.md.
