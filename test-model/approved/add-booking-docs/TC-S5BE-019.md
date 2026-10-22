# TC-S5BE-019 — Reject: без комментария 422, с комментарием — виден ученику (ОВ-2)

- Автотест: `tests/test_s5_backend.py::test_s5_reject_requires_comment_and_frees_slot`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Решение инструктора по запросу брони (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Отклонение без комментария заблокировано (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Отклонение с комментарием видно ученику (openspec/changes/add-booking-docs/specs/booking/spec.md)
  - Scenario: Чужую бронь решить нельзя (openspec/changes/add-booking-docs/specs/booking/spec.md)

## GIVEN / WHEN / THEN
- GIVEN пара с бронью 'new'; чужой инструктор
- WHEN reject чужим; с пустым/отсутствующим комментарием; с комментарием; повторный reject
- THEN чужой 404; пустой/нет — 422, статус 'new'; с комментарием 200 → 'rejected', reject_comment виден ученику и в инструкторском списке (m-2 review-001); повтор 409

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
