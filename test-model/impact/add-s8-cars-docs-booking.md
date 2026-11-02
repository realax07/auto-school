# Impact-анализ — change add-s8-cars-docs-booking (Спринт 8)

- Роль: qa_impact_analyst (H5); составлено ПМ по фактическим дельтам
- Дата: 2026-11-02 (UTC)
- Вход: дельты `openspec/changes/add-s8-cars-docs-booking/specs/`
  (instructor-documents — MODIFIED+ADDED, student-requests — MODIFIED+ADDED,
  instructor-cars — ADDED, instructor-availability — ADDED); тестовый набор
  `tests/`; трассировка TC-ID в docstring (rule 6).
- Связанные артефакты:
  - `code-reviews/add-s8-cars-docs-booking/review-001..017` (код-ревью
    итерации 1/2 + указатели J10; 5 return итерации 1 закрыты, ре-ревью
    5/5 approve);
  - `test-model/reviews/add-s8-cars-docs-booking/review-001-design.md`
    (design check — approve, миноры копирайтинга на усмотрение ПМ);
  - `test-model/reviews/add-s8-cars-docs-booking/review-001-cases.md`
    (ревью кейсов — approve, 17/17 перенесены в approved/);
  - `openspec/changes/add-s8-cars-docs-booking/diagnostics-3.1.md`
    (диагностика СТС-симптома, корень зафиксирован);
  - `sdd.md` §30–31 («Спринт 8»: модель версий, контракты API, трассировка).

## 1. MODIFIED / REMOVED дельты

### MODIFIED `instructor-documents` — «Раздел «Мои документы» инструктора»

- База: мастер-спека после change add-booking-docs (ВУ из анкеты + СТС по
  авто, авторизованный просмотр полного размера).
- Семантика Спринта 8: список дополняется версиями/статусами на каждый
  документ (active_version / pending / last_rejected с причиной — ОВ-1);
  выдача файла — ДЕЙСТВУЮЩЕЙ версии, добавлена проверка владельца до выдачи
  (NFR-22, 404-неразличение; BLOCKER review-002 закрыт в итерации 2).
- Воздействие на эндпоинты: GET /api/instructor/documents (расширение
  ответа), GET /api/instructor/documents/{doc_id}/file (ownership-гвард).
- Регресс-зона: тесты Спринтов 5 (documents-контур) — tests/test_s5_backend.py
  НЕ изменялись и остаются зелеными (полные прогоны 352/358/359 passed);
  покрытие новых контрактов — tests/test_s8_backend.py (TC-S8BE-001…009),
  e2e TC-UI-033/034/036/040.

### MODIFIED `student-requests` — «Виджет «Привязанные ученики»» и «Виджет «Занятия на сегодня» — честная заглушка»

- База: мастер-спека Спринта 3 (виджеты на главной «Мой день»).
- Семантика Спринта 8: виджеты остаются ТОЛЬКО на главной (FR-73 — явные
  исключения Заказчика); «Запросы учеников» переезжают подразделом-вкладкой
  в новый раздел «Мои ученики» (ОВ-5), счетчики — только по confirmed.
- Воздействие на фронт: instructor-dashboard.html (сайдбар/разделы),
  js/dashboard-instructor.js; на API-контур requests не влияет
  (GET …/requests + accept/deny — контракт Спринта 3 без изменений).
- Регресс-зона: e2e TC-UI-035 (отсутствие виджетов на «Мои автомобили»/
  «Мои документы» + их наличие на главной), TC-UI-009 и accept-flow
  переведены на подраздел (коммит 501c904); регресс Спринта 3 —
  tests/test_s3_backend.py без изменений, зеленый.

## 2. REMOVED дельты

Отсутствуют (REMOVED-сценариев в дельтах нет; удаление раздела
«Бронирования» оформлено сценарием «Раздел «Бронирования» удален без
остатков» внутри ADDED-требования «Запросы и брони учеников на слотах
календаря», e2e TC-UI-038).

## 3. ADDED дельты (сводно)

- `instructor-documents`: статусная модель document_versions (ОВ-1/ОВ-7,
  NFR-24 seed), загрузка/замена ВУ/СТС, админ-верификация (ОВ-4) —
  TC-S8BE-001…004/006/008, TC-UI-033…036/040;
- `instructor-cars`: СТС-фикс + ОВ-6, выдача фото через photo-эндпоинты
  (баг 5.2) — TC-S8BE-003/004/007/008, TC-UI-034/037/040;
- `instructor-availability`: запросы/брони на слотах календаря, снос
  «Бронирований» — TC-UI-038 (регресс TC-UI-019/025/026);
- `student-requests` (ADDED): GET /api/instructor/students + «Мои ученики» —
  TC-S8BE-009, TC-UI-039/039b.

## 4. Итог

- Полный регресс на integration: 359 passed, 0 failed (лог ПМ; финальный
  сериальный прогон — test-model/regress/add-s8-cars-docs-booking/
  regress-final.md, verdict PASS);
-Измененные контуры (documents выдача/версии, виджеты) покрыты новыми
  матрицами + регрессом прежних спринтов; деградаций не зафиксировано.
