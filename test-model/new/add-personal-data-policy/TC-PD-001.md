# TC-PD-001 — GET /api/policy: текст и метаданные из артефакта; страница /policy открыта гостю (оболочка без текста)

- Автотест: `tests/test_policy.py::test_s9_policy_api_and_page_guest`
- Приоритет: Must (FR-76, NFR-25)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-personal-data-policy (Спринт 9)
- Трассировка:
  - Requirement: Публичная страница политики персональных данных (/policy)
  - Scenario: Страница открывается без входа и показывает текст и версию

## GIVEN / WHEN / THEN
- GIVEN сервис развернут с артефактом deploy/policy/policy.md (v1.0); клиент — гость (без сессии)
- WHEN GET /api/policy; затем GET /policy
- THEN /api/policy → 200 {ok:true, version:"1.0", date:"2026-11-10", text:<полный текст артефакта>} — поля посимвольно равны read_policy(); /policy → 200 text/html с #policy-meta, #policy-text и /js/policy.js, при этом версии и текста артефакта в HTML-исходнике НЕТ (оболочка)

## Примечание
- Партия change add-personal-data-policy (Спринт 9, задача 7.1); кейсы
  живут трассировкой TC-ID в docstring автотеста (rule 6); заголовки
  Requirement/Scenario — дословно specs/PersonalData/spec.md.
