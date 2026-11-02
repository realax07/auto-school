# TC-S8BE-003 — СТС: первичная дозагрузка → verified v1, замена → pending, админ pending-список/предпросмотр/verify (ОВ-2/ОВ-4/ОВ-7)

- Автотест: `tests/test_s8_backend.py::test_s8_sts_primary_replacement_and_admin_flow`
- Приоритет: Must (FR-69/FR-70)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-s8-cars-docs-booking (Спринт 8)
- Трассировка:
  - Requirement: Загрузка и замена документов инструктором
  - Scenario: Дозагрузка СТС авто без действующего СТС
  - Requirement: Верификация документов администратором
  - Scenario: Подтверждение переключает действующую версию
  - Scenario: Отклонение требует причину и сохраняет действующую версию

## GIVEN / WHEN / THEN
- GIVEN approved-инструктор с авто, созданным JSON-путем без СТС (Škoda Rapid, А123АА777), и админ-заголовки X-Admin-Token
- WHEN POST /api/instructor/cars/{id}/photo/sts: первичная загрузка; затем замена (PNG) и повторная замена (JPEG2) при ожидающей; GET /api/admin/documents?status=pending; GET /api/admin/documents/{version_id}/file; POST verify; GET «Мои документы» и doc-файл sts-{car_id} владельцем
- THEN первичная загрузка → document {status: verified, version: 1}, статус авто в ответе draft (первичная загрузка статус не меняет), photo_sts = файл с содержимым ROOT_JPEG, версии [(1, verified, путь)]; замена → pending v2, повторная замещает ожидающую (version не растет — ОВ-7), photo_sts не перезаписан (файл прежний); админ pending-список содержит car_sts v2 с car {brand Škoda, model Rapid, plate А123АА777} и ФИО владельца («Иванов»), uploaded_at заполнен; предпросмотр → 200, content-type image/*, содержимое ИМЕННО pending-версии (ROOT_JPEG2) — ОВ-4; verify → photo_sts переключен на файл новой версии (ROOT_JPEG2), версии [(1, verified), (2, verified)]; «Мои документы»: active_version v2, pending = None; doc-файл sts-{car_id} отдает владельцу новую версию (ROOT_JPEG2)

## Примечание
- Партия change add-s8-cars-docs-booking (Спринт 8); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); полный прогон
  359 passed (integration, лог ПМ).
