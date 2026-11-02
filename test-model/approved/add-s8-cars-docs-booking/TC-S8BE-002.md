# TC-S8BE-002 — Жизненный цикл версий ВУ: «документ не мигает», reject с обязательной причиной, замещение pending, verify, 409 (ОВ-1/ОВ-7)

- Автотест: `tests/test_s8_backend.py::test_s8_license_version_lifecycle_and_reject_reason`
- Приоритет: Must (FR-70/FR-71/FR-72)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-s8-cars-docs-booking (Спринт 8)
- Трассировка:
  - Requirement: Статусная модель документов (ВУ и СТС)
  - Scenario: Замена создает ожидающую версию, предыдущая действует
  - Scenario: Ожидающая версия одна — повторная загрузка замещает
  - Scenario: Отклонение с обязательной причиной не лишает документа

## GIVEN / WHEN / THEN
- GIVEN approved-инструктор с легаси-ВУ (license_photo_path → файл с содержимым ROOT_JPEG, версий в document_versions нет) и админ-заголовки X-Admin-Token
- WHEN отправляются: загрузка PDF и JPEG >5 МБ; валидная загрузка PNG; reject без тела / с причиной '' / с причиной '   '; reject с причиной «Блик закрывает номер»; повторная загрузка ДВАЖДЫ; verify; повторные verify и reject по решенной версии
- THEN PDF и >5 МБ → 422 (в ошибке «5 МБ»), прежний файл не затронут; валидная загрузка → pending v1, при этом license_photo_path и файл GET /api/instructor/documents/license-{id}/file НЕ меняются («документ не мигает»); reject без тела/пустой/пробелы → 422 (ОВ-1); reject с причиной → rejected, каноническая колонка не меняется, doc-эндпоинт продолжает отдавать прежний файл (предыдущая версия действует); «Мои документы»: active_version = None, pending = None, last_rejected {version: 1, reject_reason: «Блик закрывает номер», decided_at заполнен}; повторная загрузка → НОВАЯ pending v2, повторная при pending замещает ожидающую (version не растет, файл на диске замещен содержимым ROOT_JPEG2); verify → verified + license_photo_path переключен (одна транзакция), doc-эндпоинт отдает новую версию, версии [(1, rejected), (2, verified)], «Мои документы» active_version v2, pending = None; повторные verify/reject по не-pending → 409; админ pending-список больше не содержит решенную версию

## Примечание
- Партия change add-s8-cars-docs-booking (Спринт 8); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); полный прогон
  359 passed (integration, лог ПМ).
