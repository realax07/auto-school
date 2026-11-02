# TC-S8BE-001 — Миграция document_versions: seed verified v1 из legacy-БД, идемпотентность, schema-гарды (ОВ-1/ОВ-7)

- Автотест: `tests/test_s8_backend.py::test_s8_migration_legacy_seed_and_schema_guards`
- Приоритет: Must (FR-70, NFR-24)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-s8-cars-docs-booking (Спринт 8)
- Трассировка:
  - Requirement: Статусная модель документов (ВУ и СТС) (openspec/changes/add-s8-cars-docs-booking/specs/instructor-documents/spec.md)
  - Scenario: Существующие документы мигрируют в verified (openspec/changes/add-s8-cars-docs-booking/specs/instructor-documents/spec.md)
  - Scenario: Ожидающая версия одна — повторная загрузка замещает — ОВ-7, частичный UNIQUE на уровне схемы (openspec/changes/add-s8-cars-docs-booking/specs/instructor-documents/spec.md)
  - Scenario: Отклонение с обязательной причиной не лишает документа — ОВ-1, CHECK-гард на уровне схемы (openspec/changes/add-s8-cars-docs-booking/specs/instructor-documents/spec.md)

## GIVEN / WHEN / THEN
- GIVEN предсозданная legacy-БД (DDL Спринта 7: users / instructor_applications / instructor_cars, таблицы document_versions нет) со строками: анкета с ВУ (license_photo_path = 'data/uploads/license/old1.jpg', created_at = '2026-01-01 10:00:00'), анкета без ВУ, авто с photo_sts = 'data/uploads/car_photo/old-sts.jpg' (created_at = '2026-01-02 12:00:00'), авто без СТС
- WHEN выполняется db.init_db() ДВАЖДЫ; затем прямые INSERT в document_versions: вторая pending по (license, 1), дубль (license, 1, version=1), rejected с reject_reason = None и reject_reason = '', rejected с причиной «нечитаемо»
- THEN засеяны ровно 2 строки — (license, 1) и (car_sts, 1): version = 1, status = 'verified', reject_reason = None, decided_at = uploaded_at = created_at исходной строки, file_path = исходный канонический путь; для анкеты без ВУ и авто без СТС версий не создано; повторный init_db ничего не меняет (COUNT = 2 — идемпотентно, NFR-24); вторая pending на документ → sqlite3.IntegrityError (частичный UNIQUE, ОВ-7); дубль (target_type, target_id, version) → IntegrityError; rejected без причины и с пустой причиной → IntegrityError (CHECK, ОВ-1); rejected с причиной «нечитаемо» вставляется (после чего rollback)

## Примечание
- Партия change add-s8-cars-docs-booking (Спринт 8); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); полный прогон
  359 passed (integration, лог ПМ).
