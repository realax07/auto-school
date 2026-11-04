<!-- reviewer: code_reviewer (изолированная сессия) | дифф: e040544 (задача 2.1; + package.json script check:budgets — a77b18e, волна V-2) | дерево: wt-s9-vue, ветка feat/s9-vue-pilot-package, HEAD 3051d6e | дата: 2026-11-04 -->

# Code review: задача 2.1 (change add-vue-framework-pilot)

Дифф `e040544` — frontend/vue/ (package.json + package-lock.json, vite.config.mjs,
instructors-pending.html, src/pages/instructor-pending/{main.js, App.vue, styles.css},
src/shared/api.js), .gitignore. Ревью по трем кругам: (1) спека — design.md
«Каталоги и сборка»/«Архитектура каркаса», tasks 2.1, ADR-008 п.2–3 как закон;
(2) практики сборки (multi-entry vs SPA, vendor-сплит, pinned-версии);
(3) сверка переноса api.js и разметки с legacy-исходниками.

Проверка исполнением (ревьюером, свежий вывод): `npm ci && npm run build` в
frontend/vue — 13 модулей, без ошибок; dist: instructors-pending.html + assets с
хэшами; чанки — `vue-C5F3oPW5.js` 61.43 kB / **24.10 kB gzip (отдельный vendor-чанк)**,
`instructors-pending-BVgyJdhD.js` 4.98 kB / 2.24 kB gzip (page), `shared-DIHBe7D5.js`
0.37 kB / 0.22 kB gzip. Замыкание импортов входа — только page + shared + vue:
вендорного кода в чанке страницы нет (сверено с import-графом артефактов).
`diff` тела api.js: `frontend/vue/src/shared/api.js` от строки 8 посимвольно
идентичен `frontend/js/api.js` от строки 5 (единственное отличие — шапка-комментарий);
`frontend/js/api.js` не тронут. `git ls-files frontend/vue/dist` — пусто (dist в git
не попал; .gitignore дополнен).

## Вердикт: approve

Reviewer-Delegation: deleg-cr-20261103-vue-external

## Замечания

| # | Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|---|
| 1 | minor | frontend/vue/src/pages/instructor-pending/styles.css:4–5 | Комментарий «Изменять синхронно с legacy-исходником до удаления остальных монолитов» устарел: legacy instructor-pending.html удален (8ccc90c, задача 2.3), синхронизировать стили с ним больше не с чем — указание ведет в пустоту и путает следующего дева | Переформулировать на действующий якорь: «держать styles.css синхронным со статической разметкой instructors-pending.html и разметкой App.vue» (как уже сделано в шапке входа) — можно следующей волной, не блокирует |

Не является замечанием (соответствует контракту/решениям):
- **Multi-entry, НЕ SPA (ОВ-3):** `rollupOptions.input` — один вход
  instructors-pending.html; клиентский роутер не вводится; навигация — обычные
  ссылки. Следующие страницы добавляются по одному входу (комментарий в конфиге).
- **Vendor-сплит (ADR-008 п.3):** manualChunks — `vue`/`@vue/*` → чанк `vue`,
  любой иной node_modules → чанк по имени пакета (scoped-пакеты учтены регэкспом
  `@[^/]+/[^/]+`), `src/shared/` → чанк `shared` (свой код, не на бюджете vendor).
  Подтверждено артефактами: vue — отдельный чанк, в page-чанке вендорного кода нет.
- **base `/vue/`, outDir `dist`, хэш-имена** (entry/chunk/assetFileNames) — вне
  коллизий с `/js/*` и html-входами; cache-инвалидность хэшами.
- **Dev-proxy:** `server.proxy '/api' → http://127.0.0.1:8390` — как в tasks 2.1;
  приемка по design идет против dist, не dev-сервера.
- **Pinned-версии:** точные (без `^`/`~`) vue 3.5.44 / vite 8.3.5 /
  @vitejs/plugin-vue 6.0.10 + package-lock.json (1049 строк) — `npm ci`
  воспроизводим; наследование практики ADR-006. pinia/vue-router не введены.
- **api.js — дословный перенос**, контракты вызовов не менялись (diff — проверено);
  немигрированные монолиты продолжают читать frontend/js/api.js.
- **Вход instructors-pending.html:** статическая разметка посимвольно равна legacy
  (шапка/карточка/h1 «Заявка на рассмотрении»/шаги 01–02–03/кнопки/футер) +
  модуль-скрипт — эквивалент legacy до гидрации, как предписано design.
- **.gitignore:** `frontend/vue/dist/`, `frontend/vue/node_modules/` — добавлены;
  dist в git отсутствует (проверено ls-files).

## Проверенные Scenario (tasks 2.1, готовность)

- `npm ci && npm run build` без ошибок — воспроизведено ревьюером (см. выше).
- dist содержит instructors-pending.html + assets с хэшами — да.
- ОТДЕЛЬНЫЙ vendor-чанк `vue` — да (24.10 kB gzip).
- Вендорного кода в чанке страницы нет — да (замыкание импортов входа).
- api.js — перенос без изменения контрактов вызовов — да (посимвольный diff).
- `npm run dev` поднимает страницу — НЕ перепроверялось ревьюером (заявлено девом;
  приемка по design идет против dist, dev не путь приемки).

## Что НЕ проверено (честно)

- `npm run dev` (dev-сервер, proxy /api на uvicorn) — не поднимался ревьюером.
- Визуальная скриншот-сверка 1:1 с legacy-экраном — зона design check (6.1);
  статическое посимвольное сравнение разметки/стилей выполнено.
- Поведение сборки на node < 22 (MIN-1 arch-review-002 — host-prerequisite,
  контролируется на приемке 2.2/6.1, не в этой задаче).
