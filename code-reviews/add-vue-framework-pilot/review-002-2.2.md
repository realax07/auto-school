<!-- reviewer: code_reviewer (изолированная сессия) | дифф: d92b9fb (задача 2.2) | дерево: wt-s9-vue, ветка feat/s9-vue-pilot-package, HEAD 3051d6e | дата: 2026-11-04 -->

# Code review: задача 2.2 (change add-vue-framework-pilot)

Дифф `d92b9fb` — Dockerfile (+node builder-этап frontend-builder), .dockerignore
(+frontend/vue/node_modules/, frontend/vue/dist/). Ревью по трем кругам: (1)
design.md «Доставка сборки в образ/контур» + tasks 2.2 + ADR-008 п.5 + ADR-006 как
закон; (2) практики multi-stage сборки (pinned-базы, layer-cache, чистота runtime);
(3) структурная симуляция builder-этапа исполнением (docker локально недоступен —
нет прав на docker.sock; локальный прогон от ревьюера НЕ требуется, вместо него
ниже — воспроизводимая симуляция и ее результат).

Что корректно (сверено с диффом и деревом):
- `ARG NODE_IMAGE=node:22-slim@sha256:4b150b48…7279da` — pinned digest, как python;
  этап frontend-builder ПЕРЕД python builder — наследование multi-stage ADR-006.
- Layer-cache по манифестам: `COPY frontend/vue/package.json
  frontend/vue/package-lock.json ./` → `npm ci --no-audit --no-fund` → `COPY
  frontend/vue/ .` → `npm run build`.
- Runtime: `USER appuser` / HEALTHCHECK / CMD uvicorn / EXPOSE 8390 — не тронуты;
  venv-перенос и прочие COPY — без изменений.
- `.dockerignore`: node_modules и локальный dist workspace — вне контекста
  (в образе артефакт сборки образа, не хоста; MIN-2 arch-review-002 закрыт по
  построению).
- bare-metal (FR-57): порядок `npm ci && npm run build` перед деплоем зафиксирован
  комментарием в шапке Dockerfile.
- docker-compose.yml и nginx ДАННОЙ волной не менялись (изменение compose в
  merged-дереве — ac5931e, пакет add-personal-data-policy, его ревью; на задачу 2.2
  не относится).

## Вердикт: return

Reviewer-Delegation: deleg-cr-20261103-vue-external

## Замечания

| # | Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|---|
| 1 | **blocker** | Dockerfile:22,49 | Расхождение путей builder/runtime: `COPY frontend/vue/ .` (строка 22) при `WORKDIR /app` кладет СОДЕРЖИМОЕ workspace в корень /app → `vite build` (outDir `dist` относителен root = /app) создает **/app/dist**. Runtime-шаг `COPY --from=frontend-builder /app/frontend/vue/dist ./frontend/vue/dist` (строка 49) ссылается на несуществующий источник — сборка образа падает на этом шаге («not found»). ВОСПРОИЗВЕДЕНО ревьюером без docker: содержимое frontend/vue/ скопировано в чистый каталог (аналог WORKDIR /app), `npm ci && npm run build` → dist создался в корне симуляции; `frontend/vue/dist` НЕ существует. В коммит-месседже дева честно зафиксировано «CI job docker-build (зеленый на других PR)» — на ЭТОМ Dockerfile прогон CI не подтвержден; «pass» относится к другим веткам со старым Dockerfile. Совпадение путей назначения (`./frontend/vue/dist`) с FRONTEND_DIR в app.py — верное; ошибочен только источник --from | Вариант (а), минимальный: источник `COPY --from=frontend-builder /app/dist ./frontend/vue/dist`. Вариант (б), с сохранением документированного layout (design.md): `COPY frontend/vue/ ./frontend/vue/` + `WORKDIR /app/frontend/vue` перед npm ci/build. После правки обязателен фактический прогон docker-build (CI) на этой ветке до повторного ревью |
| 2 | minor | deploy/RUNBOOK.md (файл) | MIN-1 arch-review-002 (перенос) до сих пор не отработан: в RUNBOOK нет node/npm-предусловия bare-metal деплоя (grep по node/npm — пусто) и раздела про `npm ci && npm run build` перед деплоем (FR-57) | Добавить в RUNBOOK к приемке 6.1 (там MIN-1 и контролируется по arch-review-002); версия node на хосте — согласовать с pinned node:22-slim |

Не является замечанием (соответствует контракту/решениям):
- Pinned digest node:22-slim — требование design/ADR-006 выполнено; ARG до первого
  FROM — корректная механика.
- npm ci флаги --no-audit --no-fund — допустимы (скорость/детерминизм, не меняют
  дерево зависимостей против lockfile).
- node_modules/dev-зависимости в прод-образ не попадают: сборка в builder-этапе,
  runtime забирает ТОЛЬКО dist (после фиксации пути); .dockerignore дополнительно
  исключает локальные артефакты из контекста.
- Ограничение верификации дева («docker build локально невозможен — permission
  denied на docker.sock») — реальное ограничение среды, от ревьюера локальный
  docker-прогон не требуется; однако структурная проверка путей обязательна была
  пройти до сдачи — она и вскрывает blocker.

## Проверенные Scenario (tasks 2.2, готовность)

- Структура Dockerfile: этапы/порядок/pinned — соответствует design (кроме пути
  артефакта — blocker-1).
- .dockerignore: workspace-артефакты вне контекста — да.
- compose/nginx не тронуты данной волной — да (проверено git log по файлам).
- `docker build` собирает образ — НЕ ВЫПОЛНЯЕТСЯ: падение на COPY --from
  (blocker-1, воспроизведено симуляцией).
- «в образе есть dist, node_modules отсутствует, контейнер стартует, /api/health
  зеленый» — не проверяемо до устранения blocker-1.

## Что НЕ проверено (честно)

- Фактический docker build/запуск контейнера ревьюером — нет прав на docker.sock
  в среде; CI-прогон на этой ветке не предъявлен (в коммит-месседже — «зеленый на
  других PR»).
- Воспроизводимость digestа node:22-slim в registry (дата фиксации 2026-10-28
  заявлена девом; реестр ревьюером не опрашивался).
- Права/владелец файлов dist в runtime-слое (после COPY от root → чтение appuser)
  — проверится фактическим прогоном контейнера после фикса.
