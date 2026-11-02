<!-- reviewer: code_reviewer (изолированная сессия) | дифф: 1d40a46..HEAD, волна b473703 (backend) | дата: 2026-11-02 -->

# Code review: задача 2.1 (change add-s8-cars-docs-booking)

Проверен дифф `1d40a46..HEAD` (backend-волна b473703): POST
/api/instructor/documents/license, расширение GET /api/instructor/documents
(active_version/pending/last_rejected), GET …/{doc_id}/file. Сверено с
design.md блок A (pending-версия, «документ не мигает», ОВ-7 замещение,
404-неразличение) и tasks.md 2.1. Позитив подтвержден тестами TC-S8BE-002/006
(замена: pending создана, license_photo_path не изменился; повторная загрузка
заменила ожидающую — version не вырос; PDF/6 МБ → 422; гость 401 / ученик 403;
первичная pending делает анкету без ВУ видимой). Обнаружен дефект в выдаче
файла — проверено отдельным смоком ревьюера (TestClient на этом дереве,
вне сьюта), вывод приведен в замечании 1.

## Вердикт: return

Reviewer-Delegation: deleg-cr-20261102-094136-external

## Замечания

| # | Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|---|
| 1 | blocker | backend/instructor_documents.py:330 (document_file) | `path = active_version_file(conn, target_type, entity_id)` выполняется ДО и БЕЗ проверки владельца: у документа с verified-версией файл отдается ЛЮБОЙ instructor-сессии по чужому doc_id. После seed-миграции verified v1 есть у всех существующих документов → нарушены NFR-22/design-матрица («файл действующей версии — только владельцу», чужой → 404-неразличение). Проверено смоком ревьюера: инструктор B получает `200` с контентом файла A по `GET /api/instructor/documents/sts-1/file` и `…/license-1/file` (после verify ВУ). Ownership-запросы из старого кода (WHERE id=? AND email=? / instructor_id=?) остались только в fallback-ветке `path is None` | Проверять владение ПЕРЕД выборкой версии: license — анкета по email сессии, sts — авто по instructor_id; чужой/несуществующий → 404 (без изменений формата); только потом active_version_file + канонический fallback |
| 2 | major | tests/test_s8_backend.py:766–774 (TC-S8BE-005) | Проверка «чужой документ → 404-неразличение» обернута в `if license_doc is not None`, но `create_instructor` создает анкету БЕЗ ВУ и без версий → guard всегда ложен и проверка фактически пропускается. Критерий готовности «чужая сессия → 404» не покрыт ровно для кейса с verified-версией — поэтому полный прогон (352 passed) не поймал blocker #1 | Убрать условный guard: в тесте создать документ с версией (upload + verify, либо seed-сценарий на legacy-БД) и asserting 404 для чужой сессии именно по нему |
| 3 | minor | backend/instructor_documents.py:358 (_read_upload) | Дублирование: `_read_upload` повторяет `_read_form_file` instructor_cars.py:545 почти дословно (~20 строк: multipart-проверка, form.get, sniff_image). Директива «существующие модули не раздуваются» — про модули, но дубль в двух доменах разойдется при следующей правке валидации | Вынести общий helper в backend/uploads.py (там уже живет sniff_image/save_image) и импортировать в обоих модулях |
| 4 | minor | backend/instructor_documents.py:107–125 (create_or_replace_pending_version) | При замещении ожидающей (UPDATE file_path) прежний файл pending-версии остается на диске data/uploads без сборки мусора (orphan-файлы). Спекой не запрещено (файлы вне статики, выдачи нет) — гигиена хранилища | Перед UPDATE читать старый file_path и unlink после успешного commit (симметрично NIT-4) |

Не является замечанием (соответствует контракту):
- «Документ не мигает»: license_photo_path и файл эндпоинта не меняются до
  verify (pending живет только в document_versions) — тест TC-S8BE-002.
- ОВ-7: повторная загрузка при pending — UPDATE той же строки, version не
  растет, файл новый (тест).
- 422 без записи при PDF/6 МБ: валидация до save_image (magic bytes,
  ≤5 МБ — механика uploads.py без изменений, NFR-9).
- Асимметрия «ВУ всегда pending» (первичная — досыл FR-72) — design.md
  «Первичная загрузка vs замена», задокументировано.
- Файл при сбое INSERT удаляется (NIT-4), commit/rollback — корректны.
