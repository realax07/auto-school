# Design check — add-personal-data-policy (Спринт 9, задача 9.1)

- Ревью: review-001-design
- Дата: 2026-11-03
- Валидатор: design_validator (изолированный сабагент)
- Делегирование: Reviewer-Delegation: deleg-dv-20261103-policy-external (плейсхолдер)
- Охват (дельта задачи 9.1): анкета инструктора `frontend/instructor-apply.html` +
  `frontend/js/apply.js`; модалка «Регистрация» ученика `frontend/index.html` +
  `frontend/js/landing.js`; страница политики `frontend/policy.html` +
  `frontend/js/policy.js`
- Эталоны: `docs/ba/requirements-sprint9.md` (FR-76…FR-79, ОВ-1/ОВ-2, NFR-25);
  спека `openspec/changes/add-personal-data-policy/specs/PersonalData/spec.md`;
  мокап `design/mocks/registration-instructor.html` (сноска-заглушка — пункт
  замены); бриф ПМ от 2026-11-03 (форматы осей, тесты не прогонять — cite)
- Ось: соответствие design-дельте (чекбоксы, ссылка на /policy, рендер /policy,
  честные ошибки). Behavior/провода сервера — ось test_validator; тесты
  `tests/test_policy.py` НЕ прогонялись (по брифу ПМ) — только цитирование.
- Git не трогался; стенд не поднимался (browser-прогон не входил в объем этого
  design check — сверка по исходникам + селекторам, как указано брифом).

## 1. Сверка по пунктам брифа

### 1.1 Анкета инструктора — чекбокс согласия + ссылка на /policy (FR-77, ОВ-2)

| Пункт | Ожидалось | Фактически (селектор/источник) | Статус |
|---|---|---|---|
| Чекбокс в анкете | обязательный чекбокс согласия в блоке согласия | `frontend/instructor-apply.html:36` — `.checkline input[type=checkbox][required]`, текст «…Согласен(на) с политикой персональных данных» | OK |
| Ссылка на /policy видна и ведет | `<a href="/policy">` в тексте чекбокса | `instructor-apply.html:36` — `<a href="/policy" target="_blank" rel="noopener">политикой персональных данных</a>` | OK |
| Ссылка не «серая» (видна) | стилизована, не дефолт браузера | `instructor-apply.html:10` — `.checkline a{color:#75e9a4;text-decoration:underline}` (строка добавлена под мокапным CSS, коммент. 7–9; чекбокс — существующее `.checkline input{accent-color:#42df88}`) — DEF-004 нет | OK |
| Заглушка «Перед запуском…» удалена | сноски-заглушки мокапа нет | grep «Перед запуском» по `frontend/` → 0 совпадений (строка осталась только в `design/mocks/registration-instructor.html:23`, docs и code-reviews); в `.checkline` — реальная ссылка вместо сноски | OK |
| Кнопка заблокирована до установки | disabled до чекбокса | `instructor-apply.html:37` — `<button class="submit" type="submit" disabled>` в разметке + `apply.js:40–42` (`updateConsentState(){submitBtn.disabled=!consentInput.checked}` + change-listener + init-вызов); `required` чекбокса — второй рубеж | OK |
| consent в multipart | разрешенная дельта (API-проводка) | `apply.js:77` — `fd.append('consent', …checked?'true':'false')` в POST /api/instructors/apply | OK |

Примечание: строка футера «Защита персональных данных должна быть настроена
до запуска» сохранена — она дословно присутствует в утвержденном мокапе
(`design/mocks/registration-instructor.html:24`), к сноске-заглушке «Перед
запуском…» не относится; замена текстов мокапа вне разрешенных дельт.

### 1.2 Модалка «Регистрация» ученика — чекбокс + disabled-логика (FR-78, ОВ-2)

| Пункт | Ожидалось | Фактически (селектор/источник) | Статус |
|---|---|---|---|
| Чекбокс в модалке | обязательный чекбокс со ссылкой на /policy | `frontend/index.html:87` — `<label class="reg-check"><input type="checkbox" id="reg-consent" required><span>Я согласен(на) с <a href="/policy" target="_blank" rel="noopener">политикой персональных данных</a></span></label>`; размещен перед кнопками (коммент. 83–86) | OK |
| Стили чекбокса/ссылки | не дефолт браузера | `index.html:16` — `.reg-check{…}.reg-check input{accent-color:var(--acc);…}.reg-check a{color:var(--acc2);text-decoration:underline;…}` — токены через CSS-переменные, DEF-004 нет | OK |
| Disabled-логика кнопки | `#reg-submit` недоступен до установки | `frontend/js/landing.js:21–23` — `regSubmit.disabled=!regConsent.checked` + change-listener + init-вызов при загрузке модуля | OK |
| consent в payload | разрешенная дельта (API-проводка) | `landing.js:35` — `consent:regConsent.checked` в POST /api/register (postJSON) | OK |

### 1.3 Страница /policy — рендер версии/даты/текста из API (FR-76, NFR-25, ОВ-1)

| Пункт | Ожидалось | Фактически (источник) | Статус |
|---|---|---|---|
| Оболочка с местами под версию/дату/текст | пустые контейнеры + модуль рендера | `frontend/policy.html:32–35` — `<p class="meta" id="policy-meta"></p>`, `<div class="policy-text" id="policy-text"></div>`, `<script type="module" src="/js/policy.js">`; шапка-коммент 1–11 фиксирует «оболочка БЕЗ текста» | OK |
| Версия+дата в шапке страницы | из метаданных API | `frontend/js/policy.js:35` — `metaEl.textContent='Версия: '+res.data.version+' от '+res.data.date` (из ответа GET /api/policy, строки 22–34) | OK |
| Текст политики — текстовыми узлами | НЕ innerHTML | `policy.js:36–42` — split по пустой строке, `document.createElement('p')` + `el.textContent=chunk` (коммент. «только текстовые узлы — без HTML-инъекций») | OK |
| Честная ошибка | не пустая страница, не имитация текста | `policy.js:11–20,31–32,44` — при не-200/не-ok/пустом text/битом JSON/сетевой ошибке `showError()` → `p.policy-error` с текстом «Политика временно недоступна. Попробуйте позже» (spec.md: «Артефакт поврежден — честная ошибка страницы») | OK |
| Текста политики в исходниках НЕТ | только из API | grep игл из артефакта («152-ФЗ», «Роскомнадзор», «Оператором обработки», «настоящая Политика», фрагмент шапки текста) по `frontend/` → 0 совпадений; `policy.html` (35 строк) и `policy.js` (44 строки) прочитаны полностью — текста не содержат. Программный эквивалент — TC-PD-004 (`tests/test_policy.py:259–286`: тот же grep по frontend/**.html/**.js с иглами из `read_policy()`) | OK |
| Артефакт вне исходников страниц | отдельный заменяемый файл | `deploy/policy/policy.md` — шапка `policy-version: 1.0` / `policy-date: 2026-11-10` + `---`, затем текст; вне `frontend/` (подмена без правки кода — ОВ-1) | OK |

### 1.4 Фиксация согласия — по тестам test_policy.py (не прогонялись, cite)

По брифу ПМ тесты не прогонялись — трассировка по исходнику матрицы
`tests/test_policy.py` (задача 7.1, волна 3; behavior-ось — test_validator):

- TC-PD-008 (`test_policy.py:365–391`): заявка инструктора создается с
  `consent_at` (UTC сервера, формат created_at) и `consent_policy_version` = «1.0»
  из метаданных артефакта — Req «Заявка инструктора содержит дату и версию политики».
- TC-PD-012 (`:477–495`): запись ученика (роль student) — те же поля
  (`consent_at`, `consent_policy_version`) — Req «Запись ученика содержит дату
  и версию политики».
- TC-PD-009/014 (`:394–430`, `:514–557`): подмена артефакта 1.0→2.0 — новые
  записи фиксируют «2.0», прежние сохраняют «1.0» и свой consent_at
  (не переписываются); версию читает сервер, клиент ее не присылает.
- TC-PD-016/017 (`:582–664`): миграция добавляет 4 колонки idempotent,
  легаси-записи остаются NULL без seed/backfill.
- Серверные ворота контекста: TC-PD-007/011 — POST без согласия →
  422 {ok:false, error:"Согласие: поле обязательно"}, записи не созданы;
  TC-PD-010/015 — битый/отсутствующий артефакт в момент сабмита → 500, записи
  не создаются (spec.md: «Поврежденный артефакт — записи не создаются»).
- Клиентская проводка согласия в запрос — пп. 1.1/1.2 выше (`apply.js:77`,
  `landing.js:35`); поведение на стенде — TC-UI-002/043/044/045 (e2e, задача
  7.2), на момент design check не заявлены как прогнанные.

## Вердикт: approve

Расхождений с дельтой спецификации нет: оба контура согласия (анкета
инструктора, модалка ученика) содержат обязательные чекбоксы с видимыми
ссылками на /policy, кнопки блокированы до установки, страница /policy —
оболочка с рендером версии/даты из API текстовыми узлами и честной ошибкой;
текст политики в исходниках frontend отсутствует; заглушка «Перед запуском…»
удалена. Замечание в разделе «Замечания» — minor, приемке не мешает.

Reviewer-Delegation: deleg-dv-20261103-policy-external

## Замечания

| # | Серьезность | Где | Суть | Рекомендация |
|---|---|---|---|---|
| 1 | minor | `frontend/index.html:89` (`#reg-submit`) | В отличие от анкеты инструктора (в разметке кнопки стоит атрибут `disabled`, `instructor-apply.html:37`), у кнопки модалки атрибута `disabled` в HTML нет — начальная блокировка гарантируется только init-вызовом `updateRegConsentState()` при загрузке `landing.js:23`. Поведенческого расхождения нет (сабмит модалки — целиком JS-обработчик, кнопка вне `<form>`), но паритет защитных рубежей с FR-77-контуром неполный | Добавить атрибут `disabled` в разметку `#reg-submit` (одна строка, в границах дельты чекбокса) — можно в рамках текущей задачи или в мелкую доработку без отдельного change |
| 2 | info | ось проверки | Тесты `tests/test_policy.py` и e2e TC-UI-002/043/044/045 не прогонялись (бриф ПМ: design check — без прогона, cite; прогон и behavior-вердикт — за test_validator/QA на стенде) | Прогон матрицы и e2e — на следующей оси конвейера |
