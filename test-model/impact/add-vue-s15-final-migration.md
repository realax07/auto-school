# Impact-анализ — change add-vue-s15-final-migration (Спринт 15)

- Роль: qa_impact_analyst (H5); составлено ПМ по фактическим дельтам
- Дата: 2026-11-13
- Вход: дельты `openspec/changes/add-vue-s15-final-migration/specs/`
  (Frontend — MODIFIED ×6 страниц + REMOVED легаси-маршрутов и каталога
  /js по факту диффа); тестовый набор `tests/`; трассировка
  TC-S15-001…006.

## 1. MODIFIED дельты (Frontend — 6 страниц переведены на Vue)

### admin-dashboard (+ admin-login) — админ-контур на Vue

- База: легаси admin-dashboard.html + admin-login.html + js/admin/*
  (Спринты 2/5/8: заявки, пользователи+CSV, авто, документы).
- Семантика С15: 4 раздела одной Vue-страницей; X-Admin-Token вход
  (admin-login → #err.show реактивный эквивалент); CSV blob (BOM +
  санитизация формул — test_admin_users инъекции); BUG-046/045-паттерны
  (thead, ic-deny-confirm, rowhint) дословно;Comment в App.vue без
  литерала password_hash (TC-MOD-002 гард).
- Воздействие на эндпоинты: НЕТ (админ-API контракты 1:1).
- Регресс-зона: test_admin_users (CSV), test_admin (логин), e2e
  admin-сценарии — без правок (данные/токены через фикстуры).

### cabinet (ученический) — кабинет на Vue

- База: легаси cabinet.html + js/student/cabinet.js (Спринты 1/5/10).
- Семантика С15: чат-бар/плитки СЕРВИСЫ (без тегов — TC-UI-060),
  разделы «Мои заявки»/«Мои брони» (хеш-навигация #/my-requests),
  календарь ученика С10 (недели/разворот recurring) — 1:1;
  TC-UI-059 (один логотип/без крошек) — инвариант сохранен.
- Регресс-зона: test_cabinet_page (7 переносов носителей FR-9),
  test_integration_sprint1 (MAJ-1 byte-equality → признак входа
  каркаса), e2e кабинет-кластер (регистрация→кабинет, заявки, брони,
  BUG-047/049 — 69→73 passed после фикса реактивного порта).

### instructor-choice — каталог на Vue

- База: легаси instructor-choice.html + js/student/instructor-choice.js
  (Спринт 3/7: каталог, фильтры, заявки, отзывы-переход).
- Семантика С15: фильтры/fetchSeq, рейтинг, sent-кэш, 409 без
  кэширования — 1:1; XSS-интерполяция сохранена (прецедент С11).
- Регресс-зона: test_qa_instructor_flow (password_hash-носитель),
  e2e выбор/заявка (TC-UI-007) — без правок сценариев.

### registered + policy — мелкие страницы

- registered: заглушка С0 дословно; policy: оболочка NFR-25 — рендер
  текстовыми узлами, текст НЕ в HTML/JS (grep-контроль сохранен,
  '.vue-ограничение' — состояние с С9).
- Регресс-зона: test_policy (носитель /js/policy.js → /vue/assets/),
  test_register (registered-редирект) — без правок сценариев.

## 2. REMOVED дельты

- Легаси-HTML ×6 (в т.ч. admin-cars/admin-documents — исторически
  разделы admin-dashboard, отдельными файлами не существовали с С8);
- каталог frontend/js/ целиком (shared/api.js — дословный дубликат
  vue/src/shared/api.js, тела равны — MIN-2 арх-ревью; utils —
  fioOf/fmtDate перенесены);
- хендлер /js/{filepath:path} — маршрут снят (потребители удалены тем
  же коммитом; исторические упоминания — комментарии/docstring).

## 3. Итог

- Полный e2e ветки: 73 passed, 0 failed (сценарии не переписывались);
  полный pytest-набор: 387 passed (плюс playwright 73 — вне этого
  числа); regress-final change: PASS (failed_tests: []).
- Ломающих изменений контрактов API нет (админ/ученические/политика
  эндпоинты 1:1); REMOVED — только легаси-носители, заменные Vue-
  страницами в том же PR.
