# TC-S8BE-005 — Матрица доступа к документам: админ-контур только X-Admin-Token, 404-неразличение, 422 фильтра (NFR-22)

- Автотест: `tests/test_s8_backend.py::test_s8_access_matrix`
- Приоритет: Must (NFR-22)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-s8-cars-docs-booking (Спринт 8)
- Трассировка:
  - Requirement: Раздел «Мои документы» инструктора
  - Scenario: Документы доступны только владельцу
  - Scenario: Верификация доступна только админу
  - Requirement: Раздел «Мои ученики» со счетчиками занятий
  - Scenario: Раздел доступен только владельцу

## GIVEN / WHEN / THEN
- GIVEN три аккаунта: инструктор-владелец (у него verified-ВУ после admin verify и verified-СТС на авто), второй инструктор, ученик; админ с X-Admin-Token
- WHEN GET админ-контур (/api/admin/documents, ?status=verified, /documents/1/file) без токена / с bogus X-Admin-Token / с сессией инструктора; POST /verify и /reject (в т.ч. с телом reason) без токена и с сессией инструктора; GET /api/admin/documents?status=pending|verified|rejected и ?status=bogus с админ-токеном; POST загрузки ВУ и GET «Мои документы» без сессии (гость) и с сессией ученика; GET doc-файлов ВУ и СТС владельцем, другим инструктором и учеником; GET license-999999/file и sts-999999/file; GET/POST/verify/reject по несуществующей версии 999999
- THEN админ-контур: 401 без токена, 401 с bogus-токеном, 401 с сессией инструктора (сессия не заменяет админ-токен); допустимые значения фильтра → 200, bogus → 422; загрузка ВУ и «Мои документы»: гость → 401, ученик → 403, инструктор — свои; владелец получает свои файлы → 200 с содержимым ROOT_PNG/ROOT_JPEG; чужой документ → 404 для другого инструктора (404-неразличение, NFR-22), ученику → 403; несуществующие doc-id → 404; несуществующая версия → 404 на file/verify/reject

## Примечание
- Партия change add-s8-cars-docs-booking (Спринт 8); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); полный прогон
  359 passed (integration, лог ПМ).
