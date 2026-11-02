# TC-UI-034 — СТС: дозагрузка отсутствующего из «Моих документов», замена из модалки авто, 422 честно (ОВ-6)

- Автотест: `tests/test_ui_playwright.py::test_s8_sts_upload_missing_and_replace_car_modal_422_honest`
- Приоритет: Must (FR-69/FR-72)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-s8-cars-docs-booking (Спринт 8)
- Трассировка:
  - Requirement: Раздел «Мои документы» инструктора (openspec/changes/add-s8-cars-docs-booking/specs/instructor-documents/spec.md)
  - Scenario: Дозагрузка СТС существующему авто обновляет раздел (openspec/changes/add-s8-cars-docs-booking/specs/instructor-documents/spec.md)
  - Scenario: Кнопки загрузки/замены в разделе (openspec/changes/add-s8-cars-docs-booking/specs/instructor-documents/spec.md)
  - Requirement: Загрузка и замена документов инструктором (openspec/changes/add-s8-cars-docs-booking/specs/instructor-documents/spec.md)
  - Scenario: Дозагрузка СТС авто без действующего СТС (openspec/changes/add-s8-cars-docs-booking/specs/instructor-documents/spec.md)
  - Scenario: Недопустимый файл отклоняется без последствий (openspec/changes/add-s8-cars-docs-booking/specs/instructor-documents/spec.md)
  - Requirement: Замена СТС не влияет на статус валидации автомобиля (openspec/changes/add-s8-cars-docs-booking/specs/instructor-cars/spec.md)
  - Scenario: Замена СТС у validated-авто не сбрасывает валидацию — ОВ-6 (openspec/changes/add-s8-cars-docs-booking/specs/instructor-cars/spec.md)

## GIVEN / WHEN / THEN
- GIVEN дашборд инструктора с API, замоканным по design.md: documents — только СТС Škoda Rapid; cars — Škoda Rapid validated (has_sts) и Kia Rio draft без СТС; мок sts-загрузки умеет вернуть 422 (флаг fail_next)
- WHEN в «Профиль и документы»: карточка Kia Rio «нет СТС» → кнопка «Загрузить» → выбор PNG; в «Мои автомобили»: модалка Škoda → кнопка «Заменить СТС» → диалог → подтверждение (#rep-go) → PNG; затем в «Профиль и документы»: замена СТС Škoda при fail_next (сервер вернет 422)
- THEN Kia Rio: карточка с бейджем «нет СТС» и кнопкой «Загрузить»; первичная загрузка БЕЗ диалога FR-71 (предыдущей версии нет) — POST /api/instructor/cars/53/photo/sts с файлом в поле photo, toast «Фото СТС загружено», список перезагружен — Kia «Действует» (document verified v1); замена Škoda из модалки — диалог с предупреждением («Замена не вступает в силу сразу»), POST /api/instructor/cars/52/photo/sts, честный тост «…статус авто не изменился» (ОВ-6); 422 → toast с текстом сервера «допустимы только изображения JPEG или PNG» (ошибка показывается честно), список НЕ перезагружен (безуспешная загрузка не меняет статусы)

## Примечание
- Партия change add-s8-cars-docs-booking (Спринт 8); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); полный прогон
  359 passed (integration, лог ПМ).
