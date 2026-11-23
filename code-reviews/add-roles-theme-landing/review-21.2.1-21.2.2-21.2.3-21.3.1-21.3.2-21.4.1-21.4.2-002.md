<!-- Reviewer-Delegation: deleg-s21-external | дата: 2026-11-23 | внешняя hermes-сессия -->

# Review-21.2.1-21.2.2-21.2.3-21.3.1-21.3.2-21.4.1-21.4.2-002 — ре-ревью фиксов волны 21.2/21.3/21.4

- Роль: code_reviewer (AI Factory, auto-school); ре-ревью возврата review-…-001 (автор фиксов — не я)
- Объект: фикс-коммит b277be7 ([add-roles-theme-landing] фикс-волна по review-…-001) поверх 3f147c3; 6 файлов, +161/−44
- Метод: все проверки — из КОПИИ репо (`git archive HEAD | tar -x` в scratch), hermetic; канонические прогоны дублированы в основном дереве там, где копия теряет untracked-артефакты

## Прогон тестов (обязательный пункт)

1. `python3 -m pytest tests/web/test_login_modal.py tests/web/test_s21_roles.py -q` → tests/web/test_s21_roles.py **не существует** (как и в ревью-001, MIN-4; фактический носитель — test_login_modal.py). Прогон носителя: **3 failed, 2 passed** — но 3-й фейл (`test_tc_auth_landing_page_served_with_wiring`, 404==200) — артефакт герметичной копии: untracked `frontend/vue/dist/` не попадает в git archive. В основном дереве этот тест **1 passed**. Канонический статус носителя в обоих деревьях: **2 failed, 3 passed** — ровно тот же красный набор, что в ревью-001 (воспроизведено):
   - `test_tc_auth_login_modal_texts_verbatim` → `ValueError: substring not found` (test_login_modal.py:79);
   - `test_tc_auth_login_modal_no_stub_submit` → `ValueError: substring not found` (test_login_modal.py:90).
2. `python3 -m pytest tests/web/test_ui_playwright.py -k "tc_s21 or reg_consent" -q` → **10 errors, 94 deselected** (TC-S21-001…010; селектор `reg_consent` не матчит ни одного имени теста). Блокер среды тот же, что в ревью-001: `chrome-headless-shell: error while loading shared libraries: libatk-1.0.so.0` (playwright install-deps без sudo недоступен). E2E-носители волны (включая новый TC-S21-010) в этой среде не выполнимы — вердикт по коду опирается на статическую верификацию + hermetic-часть.
3. `python3 -m pytest tests/api/test_s19_ai_bridge_glm.py tests/test_container_contract.py -q` → **8 passed** (2.73s).

## Разбор фиксов

### MAJ-1 (тест-носитель LOGIN_MODAL_TEXTS) — NOT-FIXED

Заявлено «переведён» — фактически tests/web/test_login_modal.py **фикс-коммитом не тронут** (последний тач — 90b47ba [s14]; в diffstat b277be7 файла нет). Тест по-прежнему режет index.html по маркерам:

- `start = html.index("<!-- Модалка: Вход (утвержденный мокап) -->")` — есть (index.html:63);
- `end = html.index("<!-- Модалка: Регистрация (утвержденный мокап) -->")` — **маркера больше нет**: в b277be7 он заменён на `<!-- Модалка: Регистрация — компонент shared/RegisterModal.vue… -->` (index.html:76) → `ValueError: substring not found` на строках 79 и 90 обоих тестов.

Восстановление статической m-login (index.html:63–74, цела, с overlay-обёрткой и #login-close) тексты m-login действительно возвращает в index.html — но срез обоих тестов **заканчивается** по регистровому маркеру, так что восстановление носитель не спасает. Прогон подтверждает: те же 2 красных, что в ревью-001 (в копии 3 failed — с учётом dist-артефакта, см. выше). Требование ревью-001 («адаптировать тест на новые носители, прогнать зелёным») не выполнено. Минимальный корректный фикс: в обоих тестах заменить `end`-маркер на фактический (`<!-- Модалка: Регистрация — компонент…`) либо резать по `<!-- Модалка: Регистрация` — ассерты LOGIN_MODAL_TEXTS при этом не ослабляются (тексты m-login в index.html теперь есть дословно); либо перенести срез регистровых текстов на RegisterModal.vue по прецеденту vue_landing_source.

Шапка-комментарий index.html — **не правдив** (проверка из задания):
- строки 5–7: «включая модалки m-login/m-register между комментариями-маркерами … — носитель LOGIN_MODAL_TEXTS» — m-register в файле нет;
- строка 11: «заглушки ai-open/quick/to-teachers» — ai-open/quick заглушки в b277be7 удалены (MAJ-3);
- строки 19–20: «Модалки входа/регистрации — дословный носитель LOGIN_MODAL_TEXTS» — регистровая модалка теперь компонент.

### MAJ-2 (reg-остатки в index.html) — FIX-CONFIRMED

- `grep "reg-choice|reg-student-form|reg-surname" frontend/vue/index.html` → **0 вхождений** (проверено в копии b277be7).
- Сиротский фрагмент (#reg-password/#reg-password-confirm, #reg-consent, #reg-error, #reg-submit, #reg-back) и 3 висячих `</div>` удалены (git diff подтверждает: строки-хвост сняты целиком); баланс тегов восстановлен (</main> — стр. 61, m-login сбалансирован — 67–74, закрывающий #app — стр. 80).
- m-login восстановлен целиком внутри #app (виден до гидрации — устоявшийся паттерн каркаса; id-дублей с компонентами post-mount нет, т.к. статика затирается при маунте).
- choice-шаг живёт в shared/RegisterModal.vue: `#reg-choice`, `#reg-role-student`, `#reg-role-instructor`, `#reg-student-form`, `#reg-surname` — все на месте (grep подтверждает), стартово display:none.
- Остаток (учтён в MAJ-1, не в счёт этого пункта): шапка-комментарий не актуализирована.

### MAJ-3 (alert-заглушки #ai-open/.quick) — FIX-CONFIRMED

git diff b277be7 по App.vue: блок «заглушки спринта-0» снят — alert-листенеры на #ai-open и .quick button удалены; остался только to-teachers (`stubTeachers`) с честным комментарием «легаси-заглушка вне скоупа волны (лендинг водителей)» — он и был отдельным, задвоения не создаёт. Двойных листенеров на «интерактивном» блоке больше нет: на #ai-open — один реальный обработчик (App.vue:178–188), на .quick [data-scenario] — один (App.vue:192–205), комментарий на месте старых заглушек актуализирован. TC-S21-004/005 в этой среде не прогонялись (блокер libatk) — подтверждение статическое; замечание ревью-001 о слепоте Playwright к dialog в силе (авто-dismiss), т.е. носитель сам по себе alert-поведение не ловит — гарантия здесь именно в удалении кода, что и сделано.

### MAJ-4 (quick для залогиненных) — FIX-CONFIRMED

App.vue:192–205: обработчик .quick [data-scenario] проверяет sessionStorage session_token (через try/catch, консистентно с #ai-open и shared/api.js TOKEN_KEY); залогиненный → ai_prefill = data-scenario + `window.location.href='/cabinet'` — ветка симметрична #ai-open, дельта спеки landing-assistant («либо в живой чат „Главной“ (для залогиненных)») выполнена. Незалогиненный → aiPrefillAndRegister(сценарий) — прежнее поведение сохранено. Попутно для quick закрыт NOTE-5 ревью-001: prefill ставится только внутри ветвей (у #ai-open prefill по-прежнему ставится до logged-проверки — NOTE уровня, вне объёма этого ре-ревью).

### MIN-1 (DIAG-мусор в TC-S21-001) — FIX-CONFIRMED

git diff: из TC-S21-001 удалены запись `/tmp/diag-page3.html` и все DIAG-принты (4 шт.) — побочных эффектов вне tmp-гигиены проекта больше нет. Остаток того же класса (не заявлен в фиксе и в ревью-001 формально не входил в MIN-1, фиксировать здесь): TC-S21-004 (строки 5861–5862) сохранил `print("DIAG ai-input in content:…")`, `print("DIAG title:…")` и `html = page.content()`, живущий теперь только ради принта — дочистить при следующем касании файла.

### MIN-5 (носитель quick+logged-in) — FIX-CONFIRMED

TC-S21-010 добавлен (test_ui_playwright.py, ~5965): регистрация+логин через API, _seed_session('session_token'), клик по первому .quick [data-scenario] → `wait_for_url("**/cabinet**")` + ассерт `/cabinet` in url. Носитель закрывает ровно ветку MAJ-4. Замечание в дополнение: email фиксированный (`quick-logged@ui-test.example.ru`) — тот же паттерн, что TC-S21-007…009 (терпимо при per-run чистой БД фикстуры, отмечено в ревью-001). Прогон заблокирован средой (libatk) — перед merge выполнить на машине с браузерными зависимостями.

## Вне объёма, но зафиксировано фикс-коммитом

- MIN-2 закрыт в этом же коммите: openspec theme-дельта (specs/theme/spec.md) и test-model/impact синхронизированы с инверсионным MVP (светлый режим — filter-инверсия поверх тёмного канона, палитра — следующая волна) — дифф подтверждает, формулировки «CSS-переменные» убраны.
- MIN-3 (theme-mode отдельным ключом) — отложен на следующее касание, как согласовано; не блокирует.

## Ограничения проверки

- E2E (10 TC-S21, включая новый TC-S21-010) в этой среде не выполнены: libatk отсутствует, права на install-deps нет (воспроизведено, идентично ревью-001). Перед merge — прогон на машине с браузерными зависимостями.
- Третий фейл test_login_modal.py в герметичной копии — артефакт отсутствия untracked dist/ (проверено: в основном дереве тест зелёный); на вердикт не влияет.

## Вердикт: return

Из четырёх MAJ закрыты три (MAJ-2, MAJ-3, MAJ-4 — подтверждены по коду и диффу; MIN-1/MIN-5 — закрыты), но MAJ-1 не тронут: тест-носитель test_login_modal.py не адаптирован, оба теста (`…_texts_verbatim`, `…_no_stub_submit`) падают с тем же `ValueError` на удалённом регистровом маркере — воспроизведено прогоном в обоих деревьях; шапка-комментарий index.html осталась протухшей (m-register как носитель, «заглушки ai-open/quick»). Красный существующий носитель — то же блокирующее нарушение, что и в ревью-001. Замкнутый список на доработку:

1. tests/web/test_login_modal.py: перевести срез обоих упавших тестов на фактические носители (m-login — index.html по маркеру «Вход»/границе комментария RegisterModal; регистровые тексты — RegisterModal.vue через vue_landing_source), без ослабления ассертов; прогон зелёный обязателен.
2. index.html: актуализировать шапку (строки 5–7, 11, 19–20): регистровая модалка — компонент shared/RegisterModal.vue; заглушек ai-open/quick больше нет.
3. Попутно: снять 2 DIAG-принта и `html = page.content()` в TC-S21-004.
4. E2E-прогон TC-S21-001…010 на машине с браузерными зависимостями — перед merge.
