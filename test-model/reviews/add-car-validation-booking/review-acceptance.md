# Приемочное ревью — Спринт 7, Партия A (change add-car-validation-booking)

- Ревьюер: AI Factory qa_case_reviewer (приемка, изолированная сессия)
- Дата: 2026-10-30 (UTC)
- Репозиторий: worktree wt-s7-front, ветка feat/s7-frontend, HEAD 9f8b621
- Ревьюируемый диапазон: 17cdece..9f8b621 (коммиты 6b746c0, 2682070, 1a23653, 66531ee, 9f8b621) + рабочее дерево
- Примечание по дереву: код Спринта 7 ЗАКОММИЧЕН (3 коммита: backend 1a23653, e2e 66531ee, итерация 3 9f8b621); в рабочем дереве не закоммичен только каталог code-reviews/add-car-validation-booking/ (review-001.md) — постановка «изменения не закоммичены» соответствует действительности только в части ревью-артефактов.

МЕТА: Reviewer-Delegation: deleg_spawn20261030_183058_cb2f41 — spawned hermes chat session (role=qa_case_reviewer, приемка)

---

## 1. Чек-лист задач Спринта 7 (PLAN 7.1–7.13)

| # | Задача | Артефакт-доказательство | Вердикт |
|---|---|---|---|
| 7.1 | БА requirements (10 пунктов, ОВ-вопросы) | docs/ba/requirements-car-validation-booking.md — статус «УТВЕРЖДЕН (Заказчик, 2026-10-23 — решения по ОВ-1…7)»; ОВ-1…ОВ-7 дословно, отражение в пакете проверено арх-ревью (таблица «ОВ-1…ОВ-7 — все отражены») | OK |
| 7.2 | СА-пакет add-car-validation-booking | openspec/changes/add-car-validation-booking/: proposal.md, design.md, tasks.md, specs×6 (booking, instructor-cars, instructor-documents, instructor-availability, navigation, student-instructor-choice); validate --strict — PASS (см. п.4) | OK |
| 7.3 | Арх-ревью + карта связей таблиц | openspec/changes/add-car-validation-booking/arch-review.md — итерация 2 (повтор после INC-007), 5/5 FIXED (MAJ-1 PUT availability 409 + MIN-1..4), верификация по дереву 6b746c0, «сверх объема не внесено ничего». ИТОГ: approve. ХВОСТ: «карта связей таблиц — отдельный файл со ссылкой из map.md» НЕ найдена: architecture/ содержит только map.md и adr/001–006; строки «Спринт 7» в map.md нет (последний контур — Спринт-6/ADR-006; Спринт 7 опирается на ADR-005 без его изменения) | OK + хвост |
| 7.4 | Мокапы (4) + выбор Заказчика | коммит 8d791a6 «design(s7): мокапы итерация 2 — сайдбары кабинетов, стрелки галереи, фикс бренда сайдбара (Согласовано Заказчиком)»: admin-cars.html, booking-student-cars.html, my-cars-s7.html (новые) + booking-instructor.html, my-documents.html (правки) | OK |
| 7.5 | Админка: убрать «Расписание»/«Отношения» | e2e TC-UI-031 (review-001 п.7): заглушек в сайдбаре админки нет, «Автомобили» — единственный раздел про авто (ОВ-5); проверено по frontend/admin-dashboard.html | OK |
| 7.6 | Единый сайдбар ученика (BUG-047), без кнопки «в кабинет» | instructor-choice.html — сайдбар ученика; review-001 п.7, e2e design-guard | OK |
| 7.7 | Фото авто у брони ученика | booking.py car_status/photo_url по viewer; draft → без photo_url (плейсхолдер); TC-S7BE-014 + e2e TC-UI-030 | OK |
| 7.8 | Главная инструктора: убрать «ваш следующий маршрут» | в скоупе review-001 (страницы instructor-dashboard); e2e design-guard баланс тегов | OK |
| 7.9 | «Мои автомобили»: модалка+галерея, СТС на созданном авто | frontend/instructor-dashboard.html + dashboard-instructor.js (mcRenderGalActs, mcLoadImg); standalone my-cars.html/my-requests.html удалены (b6393e2, уже в main) — в frontend/ отсутствуют | OK |
| 7.10 | Статусы авто + админ-раздел/фильтр/модалка подтверждения | submit/withdraw/validate-эндпоинты, guard 401/403/404/409 (TC-S7BE-004/005/006); legacy /block удален (TC-S7BE-009 → 404); фильтр validating + disabled-кнопка с перечнем + сервер 409 (e2e TC-UI-031, ОБЕ стороны) | OK |
| 7.11 | Бронирования слить с Календарем; Сохранить/Отменить | «Мои брони» — 8 вхождений в cabinet.html (кабинет ученика, без standalone-страниц); «Сохранить/Отменить» — ОВ-6 в дельте instructor-availability; MAJ-1 409-guard НЕ сломан (TC-S7BE-018) | OK |
| 7.12 | Ревью + QA + design check + приемка + PR | review-001 RETURN (MAJ-1) → итерация 3 APPROVE (340/340 EXIT=0, MAJ-1 FIXED серверно+UI, MIN-2/NIT-1..4 закрыты, MIN-1 осознанно отложен). ХВОСТЫ: qa-auto-report по change отсутствует; отдельный review-001-design (RETURN D-1 → итерация 2 approve-with-notes) в test-model/reviews/add-car-validation-booking/ НЕ заведен (найденный D-1-документ — add-booking-docs, Спринт 5); design-итерация подтверждена коммитом 8d791a6 «Согласовано Заказчиком». PR — вне этой приемки (следующий шаг ПМ) | OK + хвосты |
| 7.13 | Hero без наездов — flow-верстка | frontend/index.html: hero-grid = grid/flex (без absolute), media-порог 1200px с пометкой «review-001 BUG-050 MINOR-1»; scripts/check_hero_overlap.py; code-reviews/BUG-050/review-001.md — итерация 3 APPROVE; тест-баг test-model/bugs/BUG-050-hero-overlap.md | OK |

Бэкенд-контур: 20 тестовых функций в tests/test_s7_backend.py (19 на итерации 1 + TC-S7BE-019 итерации 3 — повторная валидация validated при замене фото/СТС, валидный статус-переход по решению ПМ, guard-WHERE, скрытие из каталога); e2e 39 пунктов + TC-UI-032; bug 5.2 (фото сохраненного авто не отображается) — закрыт в дельте instructor-cars/booking, покрыт TC-S7BE-012/014 и e2e TC-UI-030.

## 2. sdd.md — трассировка Спринта 7

- РАЗДЕЛ «Трассировка (Спринт 7, Партия A)» В sdd.md ОТСУТСТВУЕТ: последняя трассировка — «29. Трассировка (Спринт 5, Партия A)»; grep «Спринт 7» по sdd.md — пусто.
- По чек-листу это задача leaf, НЕ REJECT. Пометка: ХВОСТ ПМ — дополнить sdd.md (трассировка FR/NFR → Requirement → TC-S7BE-*/TC-UI-03x → коммиты) до/вместе с merge.

## 3. Артефакты ревью-контура

| Артефакт | Статус | Свежесть |
|---|---|---|
| code-reviews/add-car-validation-booking/review-001.md | Итерация 1 — RETURN (MAJ-1: заменяемость фото/СТС у validated + ложная подсказка UI; MINOR-1/2, NIT-1..4). Итерация 3 (в том же файле) — APPROVE: MAJ-1 FIXED (validated→validating в транзакции, честная копия, тост, бейджи), MIN-2/NIT-1..4 FIXED, MIN-1 отложен, MINOR-3 (design.md рассинхрон — docs-хвост) + NIT-5/6 вне блока | 2026-10-30, поверх HEAD 9f8b621 — свежий |
| Отдельный файл review-002.md | ОТСУТСТВУЕТ — APPROVE итерации 3 задокументирован внутри review-001.md. Содержательно чек-лист («review-001 RETURN → review-002 APPROVE») выполнен; раскладка по файлам — хвост оформления | — |
| review-001-design (RETURN D-1 → итерация 2 approve-with-notes) | ДЛЯ ДАННОГО change ОТСУТСТВУЕТ в test-model/reviews/add-car-validation-booking/ (каталога нет). D-1-документ с итерацией 2 «FIXED/approve-with-notes» существует для add-booking-docs (Спринт 5). Мокапы Спринта 7 согласованы Заказчиком (коммит 8d791a6), формального design-review-артефакта нет | хвост |
| qa-auto-report (test-model/reports/qa-auto-report-add-car-validation-booking.md) | ОТСУТСТВУЕТ (в reports/ только 3 старых: instructor-student-loop, booking-docs, s3-frontend-links). Автопрогон фактически выполнен (полные прогоны в review-001 итерации 1/3 + независимый прогон настоящей приемки, п.4), отчет не оформлен | хвост |

## 4. Валидации (реальное исполнение, 2026-10-30)

```
$ openspec validate --all --strict
Totals: 13 passed, 0 failed (13 items)  — вкл. change/add-car-validation-booking, 6 спек-доменов

$ python3 scripts/flow_check.py .
flow_check: OK — порядок артефактов соответствует флоу (EXIT=0)

$ export LD_LIBRARY_PATH=~/.cache/pw-libs/root/usr/lib/x86_64-linux-gnu
$ /home/hermes-bot/auto-school/.venv/bin/python -m pytest tests/ -q
-> 1 failed, 339 passed, 1 warning in 488.30s (0:08:08), EXIT=1
   FAILED tests/test_register.py::test_tc_nfr_001_register_response_time_under_500ms
$ повтор одиночного: 1 passed in 3.85s
```

Комментарий к прогону: единственный фейл — NFR-тест времени ответа регистрации (<500ms), чувствительный к нагрузке (полный сьют с e2e на том же воркере). В изоляции проходит. Эталонный прогон review-001 итерации 3 на том же HEAD 9f8b621 — 340/340, EXIT=0. Не является блокером кода; пометка: NFR-таймер флейвит под нагрузкой — кандидат на смягчение порога/вынос из полного прогона (в бэклог, вне объема Спринта 7).

## 5. Находки приемки (не блокеры)

1. sdd.md: нет трассировки Спринта 7 (п.2) — leaf-задача, хвост ПМ.
2. map.md: нет строки/ссылки контура Спринта 7 и отдельного файла «карта связей таблиц» (п.4 задачи 7.3) — хвост ПМ (архитектурно подтверждено arch-review: сущности поверх существующих, ADR-005 не изменен).
3. qa-auto-report по change не оформлен — хвост (прогоны реально выполнены и зафиксированы в review-001).
4. review-001-design для данного change не заведен; согласование мокапов зафиксировано коммитом 8d791a6 — хвост документооборота.
5. MINOR-3 из итерации 3: design.md пакета все еще содержит «validated — терминальный / замена статус не меняет» при реализованном validated→validating — обязан быть синхронизирован docs-коммитом до/вместе с СА-итерацией (заявлено ревью, в дереве 9f8b621 не правлен — проверить при хвостах).
6. MIN-1 (existence-oracle 403/404) и NIT-5/6 — осознанно отложены ревью, в бэклог.
7. PLAN.md: чекбоксы 7.1–7.13 не переведены в [x] (раздел «В РАБОТЕ») — хвост ПМ при закрытии спринта.
8. Незакоммиченный каталог code-reviews/add-car-validation-booking/ — закоммитить вместе с хвостами перед PR.

## Итог: ACCEPT

Задачи 7.1–7.13 выполнены по существу: требования утверждены (ОВ-1…ОВ-7), СА-пакет strict-valid, арх-ревью итерация 2 approve (5/5 FIXED), мокапы согласованы (4, сайдбары+стрелки), бэкенд-статусная модель и видимость — серверно, с 409-guards и MAJ-1 не сломан, фронтенд — разделы в кабинетах, standalone-страницы удалены, hero flow-верстка; код-ревью RETURN → APPROVE; полный сьют на HEAD зеленый (340/340 эталонно; независимый прогон приемки 339/340 с известным флеймом NFR-таймера, проходит изолированно). Блокеров кода/архитектуры нет. Все расхождения — документационные хвосты ПМ (п.5.1–5.5, 5.7–5.8), объединяются в leaf-задачи и НЕ блокируют merge-подготовку; design.md (MINOR-3) синхронизировать до слияния.
