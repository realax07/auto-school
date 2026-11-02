# TC-S8BE-006 — «Мои документы»: active_version/pending/last_rejected на каждый документ, пустые состояния (FR-70)

- Автотест: `tests/test_s8_backend.py::test_s8_my_documents_versions_and_empty_state`
- Приоритет: Must (FR-70)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-s8-cars-docs-booking (Спринт 8)
- Трассировка:
  - Requirement: Раздел «Мои документы» инструктора (openspec/changes/add-s8-cars-docs-booking/specs/instructor-documents/spec.md)
  - Scenario: Анкета без ВУ — корректное пустое состояние (openspec/changes/add-s8-cars-docs-booking/specs/instructor-documents/spec.md)
  - Scenario: Ожидающая замена видна со статусом «Ожидает проверки замены» (openspec/changes/add-s8-cars-docs-booking/specs/instructor-documents/spec.md)
  - Scenario: Список включает ВУ и СТС всех автомобилей (openspec/changes/add-s8-cars-docs-booking/specs/instructor-documents/spec.md)

## GIVEN / WHEN / THEN
- GIVEN approved-инструктор с авто без СТС; версий документов нет
- WHEN GET /api/instructor/documents до загрузок; затем первичная загрузка ВУ (→ pending v1) и повторный GET; затем первичная загрузка СТС авто и повторный GET
- THEN до загрузок: license = None с license_hint, содержащей «ВУ» (подсказка), documents = [] — авто без СТС и версий в список не попадает; после загрузки ВУ: license_hint = None, в documents запись license с active_version = None, pending {version: 1}, last_rejected = None (pending-загрузка делает анкету БЕЗ ВУ видимой); после загрузки СТС: ровно одна запись car_sts с active_version {version: 1}, pending = None, last_rejected = None и привязкой car.id к авто владельца

## Примечание
- Партия change add-s8-cars-docs-booking (Спринт 8); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); полный прогон
  359 passed (integration, лог ПМ).
