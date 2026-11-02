# TC-UI-040 — FR-71 на галерейном пути СТС: клик по большому окну галереи — всегда диалог замены (FR-71)

- Автотест: `tests/test_ui_playwright.py::test_s8_sts_gallery_replace_dialog`
- Приоритет: Must (FR-71; review-003 MAJ-2)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-s8-cars-docs-booking (Спринт 8)
- Трассировка:
  - Requirement: Загрузка и замена документов инструктором
  - Scenario: Загрузка замены с предупреждением и явной кнопкой
  - Requirement: Замена СТС не влияет на статус валидации автомобиля
  - Scenario: Замена СТС у validated-авто не сбрасывает валидацию

## GIVEN / WHEN / THEN
- GIVEN дашборд инструктора с замоканным API: cars — Škoda Rapid validated с has_sts (рамка sts видна в галерее), documents — СТС этого авто; мок POST /api/instructor/cars/52/photo/sts → 200 {document: {status: pending, version: 2}}
- WHEN «Мои автомобили» → модалка авто; клик миниатюры sts → клик по большому окну #mc-big; отмена диалога (#rep-cancel); повторный клик #mc-big → подтверждение явной кнопкой «Заменить» (#rep-go) → выбор PNG-файла
- THEN клик по большому окну при has_sts открывает ДИАЛОГ замены #m-replace с предупреждением («Замена не вступает в силу сразу»), а НЕ file chooser — тихая замена мимо FR-71 невозможна (review-003 MAJ-2); «Отмена» — ни одного POST (диалог закрыт, файл не отправлен); подтверждение → ровно один POST /api/instructor/cars/52/photo/sts (контракт), честный тост «…статус авто не изменился» (ОВ-6)

## Примечание
- Партия change add-s8-cars-docs-booking (Спринт 8); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); полный прогон
  359 passed (integration, лог ПМ).
