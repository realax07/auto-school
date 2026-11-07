# Покрытие: add-vue-s11-status-forms — TC-S11UI-001…009

Дельта: `openspec/changes/add-vue-s11-status-forms/specs/Frontend/spec.md` —
2 ADDED-требования, 9 сценариев. Покрытие полное: 9/9 (кейс либо группа
кейсов на каждый сценарий; сценарии, уже автоматизированные дословно, —
через существующие e2e без дублирования, NFR-27).

Обозначения: Rej = Requirement «Статусный экран отказа заявки на Vue
(/instructors/rejected)»; Rev = Requirement «Форма отзыва на Vue (/review)».

| Кейс | Сценарий спеки | Автоматизация |
|---|---|---|
| TC-S11UI-001 | Rej: «Экран обслуживается каркасом Vue» (гость, ассеты /vue/, без dist → 404) | частично: `tests/api/test_auth_route.py::test_new_static_routes_served` (200 text/html, без правок); /vue/-вход и 404 без dist — ручные шаги кейса |
| TC-S11UI-002 | Rej: «Причина отказа — из ответа логина, контракт не меняется» | `tests/web/test_ui_playwright.py::test_s9_pilot_rejected_redirects_with_reason` (TC-S9UI-003 — дословно); `tests/web/test_login_modal.py::test_login_route_mapping_wiring`; перенос носителя — `tests/web/test_instructor_pages.py::test_rejected_page_exists_and_reason_wiring` |
| TC-S11UI-003 | Rej: «Без причины — блок скрыт, запросов нет» | ручной (route-capture: 0 запросов к /api/*; ветка sessionStorage недоступен) |
| TC-S11UI-004 | Rej: «Визуальная эквивалентность текущему экрану» | ручной (поблочное сопоставление с эталоном legacy) |
| TC-S11UI-005 | Rev: «Страница обслуживается каркасом Vue» + Rev: «Без ?instructor= — редирект в кабинет» | TC-S3BE-040 `tests/api/test_s3_backend.py::test_s4_static_route_review` (200, «Оставить отзыв»); `tests/api/test_s3_backend.py::test_bug047_old_routes_redirect_301` (301); редирект из формы — TC-UI-017 `tests/web/test_ui_playwright.py::test_s4_review_submit_then_repeat_blocked_409` (goto /review → /cabinet#/my-requests); якорь back-ссылки — TC-UI-019; /vue/-вход — ручной шаг |
| TC-S11UI-006 | Rev: «Контекст инструктора и переход из «Моих заявок»» | TC-UI-018 `tests/web/test_ui_playwright.py::test_s4_my_requests_badges_deny_comment_retry_and_review_link` (переход + #i-name — дословно); агрегат API — TC-UI-017; поля #i-ava/#i-sub/#i-rating (оба варианта) — ручные шаги |
| TC-S11UI-007 | Rev: «Отправка отзыва и повтор 409» | TC-UI-017 (валидация «звезда без текста», сабмит 200 → done, reload → форма, повтор → 409 «Отзыв уже отправлен», прямой POST 409 — дословно); TC-S3BE-041 (needle URL); hover/подпись звёзд, счетчик/переполнение, тосты 200/409, MIN-1 double-submit — ручные шаги |
| TC-S11UI-008 | Rev: «Ошибки формы — тосты как в legacy» | ручной (route-моки 401/403/422/GET not ok/network; server-гварды — backend/reviews.py без изменений) |
| TC-S11UI-009 | Rej + Rev: клауза «legacy html и js … MUST быть удалены» (входит в сценарии «Экран обслуживается каркасом Vue» / «Страница обслуживается каркасом Vue») + NFR-26 | `npm run check:budgets` (ручной приемочный шаг, отчет 4.1); деградация потребителей легаси — TC-UI-019, NIT-4 (`test_s4_pages_tag_balance`), TC-S3BE-041 |

Свод по автоматизации партии: поведенческие якоря TC-S9UI-003, TC-UI-017,
TC-UI-018 — прогон без правок (NFR-27); допустимый дифф test_ui_playwright.py —
только два переноса пути чтения (TC-UI-019, NIT-4) на входы каркаса
(design.md «Границы правок тестов»). Новых автотестов партия не добавляет —
ручные шаги кейсов выполняются на приемке (гейт 5.1) и регрессе.
