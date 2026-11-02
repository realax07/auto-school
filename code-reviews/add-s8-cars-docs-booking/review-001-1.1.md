<!-- reviewer: code_reviewer (изолированная сессия) | дифф: 1d40a46..HEAD, волна b473703 (backend) | дата: 2026-11-02 -->

# Code review: задача 1.1 (change add-s8-cars-docs-booking)

Проверен дифф `1d40a46..HEAD` (backend-волна b473703): backend/db.py — DDL
`document_versions`, seed-миграция; backend/instructor_documents.py —
правила-хелперы версий. Сверено с design.md (машина статусов документа,
ОВ-1/ОВ-7 на уровне схемы, NFR-24 idempotent-seed) и tasks.md 1.1
(критерии готовности). Тесты не запускал (полный прогон на дереве
выполнен ПМ: 352 passed); покрытие сверено по тесту TC-S8BE-001
(tests/test_s8_backend.py:250), который закрывает все критерии готовности
задачи: seed verified v1 (тот же файл, uploaded_at = created_at), пустые
строки без документов, повторный запуск init_db — 0 изменений, частичный
UNIQUE (вторая pending → IntegrityError), UNIQUE(version), CHECK
rejected-без-причины → IntegrityError.

## Вердикт: approve

Reviewer-Delegation: deleg-cr-20261102-094136-external

## Замечания

Нет.

Не является замечанием (соответствует контракту/решениям):
- ОВ-1 на уровне схемы: `CHECK (status <> 'rejected' OR (reject_reason IS
  NOT NULL AND reject_reason <> ''))` (db.py:141–144) — CHECK в SQLite
  применяется и на UPDATE (reject-эндпоинт не сможет обнулить причину).
- ОВ-7 на уровне схемы: частичный `UNIQUE (target_type, target_id) WHERE
  status = 'pending'` (db.py:152–154) — механика uq_booking_active_slot,
  вторая pending невозможна (покрыто тестом).
- Seed (NFR-24): строка ищется по target_type+target_id перед вставкой
  (db.py:199–207) — повторный запуск ничего не меняет; анкета без ВУ /
  авто без СТС строк не создают; seed после _COLUMN_MIGRATIONS.
  decided_at = uploaded_at у seed-строк — design.md decided_at для seed не
  оговаривает, решение безобидно (совпадает с «решили de facto при
  загрузке»).
- Правила-хелперы — все три из tasks.md: document_versions_info
  (действующая = последняя verified, ожидающая, последняя rejected),
  active_version_file, create_or_replace_pending_version (замещение —
  UPDATE той же строки, version не растет — ОВ-7), create_verified_version
  (первичный документ).
- Домен версий — внутри instructor_documents.py (директива модульности);
  app.py не тронут, новых роутеров нет; SQL статический, только
  ?-плейсхолдеры (NFR-10).
