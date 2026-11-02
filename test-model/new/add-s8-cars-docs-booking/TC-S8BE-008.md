# TC-S8BE-008 — Единое правило «пустой СТС»: photo_sts NULL и '' неотличимы (MINOR review-003 #3)

- Автотест: `tests/test_s8_backend.py::test_s8_empty_sts_rule_seed_branch_agree`
- Приоритет: Should (MINOR review-003 #3 — согласованность правила; сами FR-69/FR-70 — Must)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-s8-cars-docs-booking (Спринт 8)
- Трассировка:
  - Requirement: Замена СТС не влияет на статус валидации автомобиля
  - Scenario: Правило «пустой СТС» едино для seed и sts-ветки

## GIVEN / WHEN / THEN
- GIVEN approved-инструктор с авто, у которого в канонической колонке photo_sts записана пустая строка '' (легаси-мусор; в живых данных не встречается — проверяется согласованность правила)
- WHEN выполняется db.init_db(); GET /api/instructor/cars; POST /api/instructor/cars/{id}/photo/sts (загрузка по такому авто); повторный GET списка
- THEN seed не создает document_versions по '' (версии []); флаги списка: has_sts = false, sts_url = None, counters.sts = false ('' — «документа нет»); загрузка идет как ПЕРВИЧНАЯ дозагрузка → document {status: verified, version: 1} (а не «замена» с pending), photo_sts = файл с содержимым ROOT_JPEG, версии [(1, verified, путь)]; после загрузки флаги согласованы: has_sts = true, sts_url заполнен, counters.sts = true

## Примечание
- Партия change add-s8-cars-docs-booking (Спринт 8); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); полный прогон
  359 passed (integration, лог ПМ).
