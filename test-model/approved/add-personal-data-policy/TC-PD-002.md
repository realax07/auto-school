# TC-PD-002 — Подмена артефакта: новая версия/текст в /api/policy и /policy без правки кода

- Автотест: `tests/test_policy.py::test_s9_policy_artifact_swap_new_version_without_code_change`
- Приоритет: Must (FR-76, NFR-25)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-personal-data-policy (Спринт 9)
- Трассировка:
  - Requirement: Публичная страница политики персональных данных (/policy)
  - Scenario: Подмена артефакта меняет текст и версию без правки кода

## GIVEN / WHEN / THEN
- GIVEN сервис работает с артефактом версии 1.0; подготовлен временный файл с policy-version: 2.0 и новым текстом
- WHEN POLICY_FILE переключен на новый файл (замена одного файла, исходники HTML/JS не менялись); GET /api/policy и GET /policy
- THEN /api/policy → 200 {ok:true, version:"2.0", date:"2026-12-01", text:<новый текст>}; /policy — прежняя оболочка, нового текста в HTML по-прежнему нет; ни один файл исходников не менялся

## Примечание
- Партия change add-personal-data-policy (Спринт 9, задача 7.1); кейсы
  живут трассировкой TC-ID в docstring автотеста (rule 6); заголовки
  Requirement/Scenario — дословно specs/PersonalData/spec.md.
