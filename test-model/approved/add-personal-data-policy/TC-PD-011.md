# TC-PD-011 — Прямой POST /api/register без согласия отклоняется сервером

- Автотест: `tests/test_policy.py::test_s9_register_consent_required_422_no_user`
- Приоритет: Must (FR-78)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-personal-data-policy (Спринт 9)
- Трассировка:
  - Requirement: Обязательное согласие при регистрации ученика
  - Scenario: Прямой POST /api/register без согласия отклоняется сервером

## GIVEN / WHEN / THEN
- GIVEN валидные данные регистрации без consent и с consent:false (два кейса параметра)
- WHEN POST /api/register отправлен напрямую
- THEN каждый ответ 422 {ok:false, error:"Согласие: поле обязательно"}; в users 0 строк

## Примечание
- Партия change add-personal-data-policy (Спринт 9, задача 7.1); кейсы
  живут трассировкой TC-ID в docstring автотеста (rule 6); заголовки
  Requirement/Scenario — дословно specs/PersonalData/spec.md.
