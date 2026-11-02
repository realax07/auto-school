<!-- reviewer: ПМ (сборка верифицирована оркестратором, приемка спринта 8) | дифф: merges 4ff42d2/228a4e3 + итерация 2 (133447f/ca30a0c) | дата: 2026-11-02 -->

# Code review: задача 10.1 (change add-s8-cars-docs-booking) — сборка

Сверка сборки integration-ветки feat/s8-integration: финальные миграции
document_versions + seed verified v1 подключены через init_db (lifespan),
идемпотентность покрыта TC-S8BE-001; новых роутеров нет — расширения внутри
instructor_documents.py / instructor_cars.py / student_requests.py (design.md,
директива модульности соблюдена); правило префиксов API сверено с design.md
(инструктор/admin/student контуры без смещений); существующие модули
(auth, register, admin, instructors, instructor_admin, reviews, booking,
student_marketplace, instructor_availability, instructor_summary, uploads)
не изменены вне контрактов.

Прогоны на дереве сборки (ПМ, логи в спринт-логе):
- pytest tests/ -q → 352 passed (после итерации 1), 358 passed (после
  итерации 2, вкл. регресс Спринтов 0–7 и матрицы s8) — /api/health зеленый;
- смок ownership (s8_probe_docfile.py): чужой СТС/ВУ → 404, свой → 200;
- openspec validate --strict (change и --all) — зеленые; flow_check — OK.

## Вердикт: approve

Reviewer-Delegation: deleg-acc-20261102-pm-external

## Замечания

Нет. Таймерный TC-NFR-001 (bcrypt <500мс) флакует под параллельной нагрузкой
и на базовом b473703 — предсуществующий шум машины, не сборка (изолированный
прогон зеленый).
