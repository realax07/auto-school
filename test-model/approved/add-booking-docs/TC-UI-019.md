# TC-UI-019 — Back-ссылки и запрет standalone-страниц разделов (BUG-047)

- Автотест: `tests/test_ui_playwright.py::test_back_links_lead_to_role_home`
- Приоритет: Must
- Статус: автоматизирован (правится rule 6 — TC-ID в docstring теста);
  кейс партии change add-booking-docs, e2e — на живом сервере
  (репликация session-фикстуры server/broker tests/test_ui_playwright.py).
- Трассировка:
  - Requirement: Раздел «Мои документы» инструктора (openspec/changes/add-booking-docs/specs/instructor-documents/spec.md) — кабинет MUST содержать раздел; директива Заказчика: разделы встроены в кабинеты, standalone-страницы (my-cars/my-requests) удалены, новые НЕ создаются

## GIVEN / WHEN / THEN
- GIVEN разметка страниц (файлы) + целевые страницы
- WHEN проверка разделов дашборда инструктора («Мои автомобили», «Мои документы», «Бронирования») и кабинета ученика («Мои заявки», «Мои брони»); навигация назад
- THEN разделы есть, standalone-страниц нет; выбор инструктора и форма отзыва ведут назад в кабинет ученика

## Примечание
- Партия change add-booking-docs (Спринт 5, Партия A); кейсы живут трассировкой
  TC-ID в docstring автотеста (схема Спринтов 4–5, см.
  test-model/reports/qa-auto-report-add-booking-docs.md, раздел 5).
- Ссылочный прогон: 307 passed (qa-auto-report-add-booking-docs.md, 2026-10-22).
