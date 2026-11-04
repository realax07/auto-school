# TC-PD-007 — Прямой POST /api/instructors/apply без согласия отклоняется сервером

- Автотест: `tests/test_policy.py::test_s9_apply_without_consent_422_no_application`
- Приоритет: Must (FR-77, регресс MIN-2)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-personal-data-policy (Спринт 9)
- Трассировка:
  - Requirement: Обязательное согласие при регистрации инструктора
  - Scenario: Прямой POST без согласия отклоняется сервером

## GIVEN / WHEN / THEN
- GIVEN валидные данные анкеты без флага согласия (ключ consent отсутствует)
- WHEN POST /api/instructors/apply отправлен напрямую
- THEN ответ 422 {ok:false, error:"Согласие: поле обязательно"}; в instructor_applications 0 строк

## Примечание
- Партия change add-personal-data-policy (Спринт 9, задача 7.1); кейсы
  живут трассировкой TC-ID в docstring автотеста (rule 6); заголовки
  Requirement/Scenario — дословно specs/PersonalData/spec.md.
