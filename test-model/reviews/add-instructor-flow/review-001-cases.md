# Review-001 — кейсы add-instructor-flow (полный пакет, 52 файла)

- Ревьюер: qa_case_reviewer
- Дата: 2026-10-12
- Источники: test-model/checklists/add-instructor-flow.md (CHK-1…52), openspec/changes/add-instructor-flow/specs/** (instructor-application, admin-moderation, instructor-auth), sdd.md §15–19, contracts/artifact_contract.md (контракт 5), agents/qa_case_reviewer_agent.md
- Полный список файлов пакета (52, покрытие 52→52): TC-APP-001…TC-APP-021, TC-MOD-001…TC-MOD-013, TC-AUTH-001…TC-AUTH-011, TC-CAB-001…TC-CAB-003, TC-INT-001, TC-NFR-001…TC-NFR-003.
- Условия входа (контракт 5): один файл = один кейс, имя = ID — ок; CHK-ID указан в каждом — ок; GIVEN/WHEN/THEN, предусловия, шаги, ожидаемый результат, тестовые данные присутствуют во всех 52 — ок.
- Сверка automated-пометок: тесты tests/test_instructors_apply.py, test_instructor_admin.py, test_auth_route.py, test_instructor_pages.py (плюс эталоны test_auth.py, test_db.py) прочитаны полностью; прогон `pytest tests/test_instructors_apply.py tests/test_instructor_admin.py tests/test_auth_route.py tests/test_instructor_pages.py tests/test_db.py -q` → **77 passed**.

## Вердикты

| Кейс | CHK | Вердикт | Замечания |
|---|---|---|---|
| TC-APP-001 | CHK-1 | approve | Без замечаний. Ссылки на test_new_static_routes_served и test_instructors_landing_texts_verbatim подтверждены; допуск «только wiring» соответствует sdd §15.6. |
| TC-APP-002 | CHK-2 | approve | Замечание (minor): подписи кнопок в WHEN отличаются от фактических текстов лендинга (hero-CTA — «Выбрать формат работы ↗», «Стать инструктором ↗» — шапка и низ; подтверждено test_instructors_cta_wiring_to_apply). Требование CHK-2 (переход каждой CTA на /instructors/apply) проверяемо полностью; рекомендация автоматизатору — синхронизировать подписи при Playwright-прогоне. |
| TC-APP-003 | CHK-3 | approve | Без замечаний. Состав полей, id и required-семантика совпадают с test_apply_page_texts_verbatim/test_apply_password_fields_added; отказ от HTML5 required у согласия согласован с CHK-8/решением review-001-4.2 #1. |
| TC-APP-004 | CHK-4 | approve | Без замечаний. Пометка manual честная; wiring-автоконтроль test_apply_work_format_toggles_plate (disabled + очистка значения) подтвержден. |
| TC-APP-005 | CHK-5 | approve | Без замечаний. Обе части (нет в теле POST, нет в записи заявки) покрыты: test_apply_submit_wiring (FormData/license-file отсутствуют) + контрактный тест создания заявки. |
| TC-APP-006 | CHK-6 | approve | Без замечаний. Ожидаемые значения SELECT (разбор ФИО, status, review_comment='') дословно совпадают с assertions теста; браузерный редирект честно оставлен manual. |
| TC-APP-007 | CHK-7 | approve | Без замечаний. 9 обязательных полей и тексты сообщений — дословное совпадение с параметризацией test_apply_validation_contract_422; исключение plate корректно (CHK-13). |
| TC-APP-008 | CHK-8 | approve | Без замечаний. Серверный 422 автоматизирован ({consent: false} → «Согласие: поле обязательно»), клиентская блокировка опциональна по риску review-001-4.2 #1 — расхождений с CHK нет. |
| TC-APP-009 | CHK-9 | approve | Без замечаний. Оба варианта (not-an-email, a@b) в параметризации. |
| TC-APP-010 | CHK-10 | approve | Без замечаний. Текст «Телефон: укажите не менее 10 цифр» подтвержден. |
| TC-APP-011 | CHK-11 | approve | Без замечаний. |
| TC-APP-012 | CHK-12 | approve | Без замечаний. |
| TC-APP-013 | CHK-13 | approve | Без замечаний. Контрольная грань sber+plate='' → 200 автоматизирована (test_apply_sber_format_allows_empty_plate). |
| TC-APP-014 | CHK-14 | approve | Без замечаний. Оба невалидных формата в параметризации. |
| TC-APP-015 | CHK-15 | approve | Без замечаний. Порядок §15.1 воспроизведен шагами 1–8; automated-пометка честная (только пара consent→email — test_apply_order_consent_checked_before_email_format, остальное toBeAutomated той же параметризацией). |
| TC-APP-016 | CHK-16 | approve | Замечание (minor): автоматизирован прогон Б (прямой INSERT taken@example.com — механика теста); прогон А (ученик через /api/register) в цитируемом тесте не воспроизводится — пометка «(ученик в users)» неточна. Функционально users-ветка CHK-16 покрыта; прогон А рекомендуется довести в qa_automation (тривиально через /api/register). |
| TC-APP-017 | CHK-17 | approve | Без замечаний. waiting-вариант автоматизирован; approved/deny честно помечены toBeAutomated (паттерн _set_status). |
| TC-APP-018 | CHK-18 | approve | Без замечаний по существу. Расстановка честная: дубликат→422 и «не 500» автоматизированы (test_apply_race…, test_apply_integrityerror…), честное исполнение IntegrityError-ветки (monkeypatch, D8) — toBeAutomated; отмечу, что комментарий в test_apply_integrityerror_second_line_of_defense сам признает отсечение SELECT-ом — механика D8 не закрыта тестом, что кейс корректно отражает. |
| TC-APP-019 | CHK-19 | approve | Без замечаний. $2b$12$/checkpw и строгое равенство хэшей users↔заявка подтверждены тестами. |
| TC-APP-020 | CHK-20 | approve | Без замечаний. caplog-перехват и отсутствие P в записи подтверждены. |
| TC-APP-021 | CHK-21 | approve | Замечание (minor): в данных кейса P=«Qwerty123», цитируемый login-тест использует набор instr@example.com/Instr1234 — расхождение некритично (тест самодостаточен, кейс воспроизводим своим набором), но автоматизатору выбрать один набор, чтобы трассировка была буквальной. |
| TC-MOD-001 | CHK-22 | approve | Без замечаний. Сортировка и состав полей подтверждены; три статуса в одном списке честно помечены toBeAutomated (расширение test_list_sorted через _set_status). |
| TC-MOD-002 | CHK-23 | approve | Без замечаний. Сторож test_list_without_hash_key закрывает риск review-001-2.1 #2; UI/логи честно manual. |
| TC-MOD-003 | CHK-24 | approve | Без замечаний. Браузерный клик — manual/toBeAutomated; API-часть действий покрыта соседними кейсами. |
| TC-MOD-004 | CHK-25 | approve | Без замечаний. Три эндпоинта × (нет заголовка/неизвестный токен) автоматизированы; истекший токен не заявлен как automated (эталон test_auth.py::test_expired_token_401 указан как паттерн) — корректно. |
| TC-MOD-005 | CHK-26 | approve | Без замечаний. Три варианта пустого комментария (None/''/'   ') подтверждены; UI-часть manual. |
| TC-MOD-006 | CHK-27 | approve | Без замечаний. |
| TC-MOD-007 | CHK-28 | approve | Без замечаний. Сохранение причины C при повторном deny подтверждено. |
| TC-MOD-008 | CHK-29 | approve | Без замечаний. Снапшот users + побайтовое сравнение — сильная проверяемость. |
| TC-MOD-009 | CHK-30 | approve | Без замечаний. Транзакционная часть (rollback, MIN-3) автоматизирована test_approve_transaction_rollback_keeps_consistency — заявление CHK-30 «падение между INSERT и UPDATE» покрыто. |
| TC-MOD-010 | CHK-31 | approve | Без замечаний. Повторный approve→409 + COUNT=1 подтверждены; UI-скрытие кнопки manual. |
| TC-MOD-011 | CHK-32 | approve | Без замечаний. Гонка эмулируется честно (чужой INSERT после создания заявки), ожидания 409/waiting/COUNT=1 совпадают с тестом. |
| TC-MOD-012 | CHK-33 | approve | Без замечаний. Роли + миграционные тесты test_db.py подтверждены. |
| TC-MOD-013 | CHK-34 | approve | Без замечаний. /api/auth/me-контроль сессии усиливает кейс. |
| TC-AUTH-001 | CHK-35 | approve | Без замечаний. route=cabinet + выданный токен + /me — дословно по тесту. |
| TC-AUTH-002 | CHK-36 | approve | Без замечаний. Единое сообщение сверяется с AUTH_FAIL_MESSAGE; цепочка «идентично ученическому отказу» замкнута эталоном test_login_failures_identical_message. |
| TC-AUTH-003 | CHK-37 | approve | Замечание (minor): вариант «approved-инструктор в users + неверный пароль» напрямую не автоматизирован — цитируемые тесты покрывают users-путь (ученик) и заявочный путь; кейс честно пишет «users-вариант инструктора — тот же контракт», но qa_automation стоит добавить прямой прогон (apply+approve+wrong password), чтобы CHK-37 был покрыт буквально. |
| TC-AUTH-004 | CHK-38 | approve | Без замечаний. Отсутствие ключа token — точная проверяемость §15.5. |
| TC-AUTH-005 | CHK-39 | approve | Без замечаний. reason дословно, без token. |
| TC-AUTH-006 | CHK-40 | approve | Замечание (minor): deny-вариант шага 4 не входит в цитируемый тест (test_login_wrong_password_against_application_401 прогоняет только waiting) — automated-пометка должна уточнять «waiting только»; deny-вариант довести в qa_automation (тривиально через _set_status). |
| TC-AUTH-007 | CHK-41 | approve | Без замечаний. Wiring (sessionStorage-ключ, скрытие reason-block) подтвержден; прямое открытие — manual; класс D4 (живая вкладка) корректно исключен до решения ПМ, не обойден. |
| TC-AUTH-008 | CHK-42 | approve | Без замечаний. Регресс route=student-cabinet подтвержден. |
| TC-AUTH-009 | CHK-45 | approve | Без замечаний. Порог параметрически к _BF_MAX_FAILURES=5 (D1 задокументирован, не обойден); 6-я попытка с верным паролем — ровно по тесту. |
| TC-AUTH-010 | CHK-46 | approve | Без замечаний. Единый учет для заявок автоматизирован; сброс при статусном входе честно toBeAutomated (эталон users-пути указан). |
| TC-AUTH-011 | CHK-47 | approve | Без замечаний. Изоляция по IP — эталон; инструктор-вариант и «нераскрытие блокировки» manual/toBeAutomated — расстановка корректна. |
| TC-CAB-001 | CHK-43 | approve | Без замечаний. Запрещенные фрагменты dashboard перечислены дословно как в тесте; браузерная часть manual. |
| TC-CAB-002 | CHK-44 | approve | Без замечаний. Wiring-гвард + 401-эталоны /me подтверждены; полный браузерный сценарий manual. |
| TC-CAB-003 | CHK-48 | approve | Без замечаний. Автоматизируемая часть (тексты/маршруты) + design check 6.1 по D6 — корректное разделение; риски review-001-4.2 #2 и 4.3 #2 включены в шаг 4. |
| TC-INT-001 | CHK-49 | approve | Без замечаний. health/монтирование/статика/регресс автоматизированы; полный pytest — этапная проверка. |
| TC-NFR-001 | CHK-50 | **return (major)** | **Major:** automated-пометка «динамическая проба» не подтверждается цитируемыми тестами: в параметризации test_apply_validation_contract_422 НЕТ email с метасимволами (только «not-an-email», «a@b»), а test_login_unknown_credentials_unified_401 использует ghost@example.com без инъекции. Фактический login-тест инъекции существует в tests/test_qa_sprint1.py (строка 118, эталон Спринта 1), но кейсом не цитируется; apply-проба `' OR 1=1 --` не автоматизирована нигде. Неверная пометка маскирует незакрытую часть CHK-50 (динамическая проба против apply). Рекомендация: добавить в параметризацию test_apply_validation_contract_422 вариант {"email": "' OR 1=1 --"} → «Email: неверный формат» (инъекция не содержит @ и отсекается валидатором формата) и цитировать test_qa_sprint1 для login-пробы; после этого пометить пробу automated честно. Статическая инспекция (manual/toBeAutomated) помечена корректно. Остальное по кейсу (GIVEN/WHEN/THEN, шаги, данные) — без замечаний. |
| TC-NFR-002 | CHK-51 | approve | Без замечаний. Четыре автоматизированных фрагмента (пароль не в ответе/логах, хэш не в API, reason только после верного пароля) подтверждены; .env/git — честно manual. |
| TC-NFR-003 | CHK-52 | approve | Без замечаний. Все шесть test_db-тестов существуют; idempotent-доводка повторным init_db (сигнал review-001-1.2 #1) включена. |

## Итог review-001 по пакету (52 кейса)

- **Вердикт: изменения требуются (changes-required), по 1 кейсу из 52.**
- **Одобрить (approve): 51 кейс** — TC-APP-001…021, TC-MOD-001…013, TC-AUTH-001…011, TC-CAB-001…003, TC-INT-001, TC-NFR-002, TC-NFR-003 — переносятся в `test-model/approved/add-instructor-flow/`.
- **Вернуть (return): TC-NFR-001** (CHK-50) с major-замечанием о неподтвержденной automated-пометке динамической пробы; остается в `test-model/new/add-instructor-flow/` до исправления автором (повторная итерация — review-002).
- Статистика замечаний: **blocker — 0; major — 1 (TC-NFR-001); minor — 5** (TC-APP-002, TC-APP-016, TC-APP-021, TC-AUTH-003, TC-AUTH-006 — не блокируют, переданы автоматизатору); без замечаний — 46.
- Валидация авторства пометок: все прочие automated-ссылки сверены с исходниками тестов пофамильно — существуют и покрывают заявленное (77 passed при контрольном прогоне). Плановые ID (TC-FR11-*, TC-FR13-*, TC-FR14-*, …) в docstring действуют до утверждения кейсов (rule 6) — после утверждения рекомендуется обновить docstring на финальные TC-ID (не блокер, зона qa_automation).
- Трассировка CHK → TC полная, 52→52, биекция без дублей: CHK-1…21 → TC-APP-001…021; CHK-22…34 → TC-MOD-001…013; CHK-35…42 → TC-AUTH-001…008; CHK-43 → TC-CAB-001; CHK-44 → TC-CAB-002; CHK-45…47 → TC-AUTH-009…011; CHK-48 → TC-CAB-003; CHK-49 → TC-INT-001; CHK-50…52 → TC-NFR-001…003. Лишних кейсов без источника нет.
- Соответствие спеке: коды и тела ответов кейсов сверены с sdd §15.1–15.6 (422-сообщения валидации, 401 {"ok": false}, 409-гварды, route/reason §15.5, сортировка §15.2) — противоречий нет; расхождений со Scenario дельт не найдено.
- Дефекты спеки D1–D8 в кейсах не обходятся, а зафиксированы в примечаниях (D1/D4/D6/D8 — явно; остальные вне объема чеклиста) — рамка чеклиста соблюдена.
- Границы соблюдены: записи — только `test-model/reviews/add-instructor-flow/review-001-cases.md` и перенос 51 файла в `test-model/approved/add-instructor-flow/`; кейсы не правились; git не затронут.
