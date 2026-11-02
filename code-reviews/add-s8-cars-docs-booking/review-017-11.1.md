<!-- reviewer: ПМ (приемка спринта 8, сводка контрольных точек 11.1) | дерево: feat/s8-integration ca30a0c + docs | дата: 2026-11-02 -->

# Code review: задача 11.1 (change add-s8-cars-docs-booking) — приемка

Сводка контрольных точек приемки (все с фактами прогонов на дереве
integration feat/s8-integration):

1. Полный прогон `pytest tests/` — 358 passed, 0 failed (лог ПМ,
   s8-int-fullpytest2.log; до итерации 2 — 352 passed). Регресс
   Спринтов 0–7 + новые матрицы s8 (TC-S8BE-001…009, TC-UI-033…040).
2. NFR-22 матрица доступа — TC-S8BE-005 + независимый смок ownership
   (s8_probe_docfile.py): чужой СТС (verified) → 404, чужое ВУ после
   verify → 404, свой → 200; «Мои ученики» только свои пары (TC-S8BE-009);
   админ-контур только по X-Admin-Token.
3. NFR-24 миграция на старой БД — TC-S8BE-001: у каждого легаси-документа
   ровно одна verified v1, повторный запуск ничего не меняет.
4. ОВ-4 предпросмотр в админке — e2e TC-UI-036 (fetch→blob→objectURL с
   токеном, изображение открывается).
5. NFR-10 — grep по измененным модулям (instructor_documents.py,
   instructor_cars.py, student_requests.py, db.py): 0 SQL-конкатенаций;
   лог-гигиена: файлы/ФИО/токены/причины в логи не пишутся (grep чист).
6. openspec validate add-s8-cars-docs-booking --strict — valid;
   openspec validate --all --strict — 14 passed, 0 failed.
7. `python3 scripts/flow_check.py .` — OK (после тиков + указателей J10).
8. sdd.md дополнен: разделы 30 («Спринт 8»: модель версий, контракты API)
   и 31 («Трассировка (Спринт 8)»).
9. Отчет диагностики 3.1 — openspec/changes/add-s8-cars-docs-booking/
   diagnostics-3.1.md, корень СТС-симптома зафиксирован.
10. Design check — test-model/reviews/add-s8-cars-docs-booking/
    review-001-design.md: вердикт approve (миноры копирайтинга — на
    усмотрение ПМ, переделки не требуют).

## Вердикт: approve

Reviewer-Delegation: deleg-acc-20261102-pm-external

## Замечания

Таймерный TC-NFR-001 (bcrypt <500мс) — предсуществующий флак под
параллельной нагрузкой (флакует и на базовом b473703); изолированный
прогон зеленый. Не является дефектом спринта.
