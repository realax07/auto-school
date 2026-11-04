<!-- reviewer: ПМ (ре-ревью задачи 2.2 по факту CI-прогона; append-only после review-002-2.2 return) | дифф: 326048c (fix Dockerfile + RUNBOOK) | дата: 2026-11-04 -->

# Code review: задача 2.2 (change add-vue-framework-pilot) — ре-ревью после фикса

Закрытие двух замечаний review-002-2.2 (blocker MAJ-1, minor MIN-1):

1. **MAJ-1 (расхождение путей builder/runtime)** — исправлено вариантом (б)
   ревьюера (сохранение документированного layout): `WORKDIR
   /app/frontend/vue` + `COPY frontend/vue/ ./` → dist =
   `/app/frontend/vue/dist` — путь источника runtime
   `COPY --from=frontend-builder /app/frontend/vue/dist ./frontend/vue/dist`
   теперь существует. Коммит 326048c.
2. **Фактический прогон docker-build (CI) на ЭТОЙ ветке** — требование
   ревьюера выполнено: PR#107, run 41821707247 (после фикса ПЕРВОЙ правки)
   и последующие прогоны — job docker-build: PASS 4m20s
   (https://github.com/realax07/auto-school/actions/runs/41821707247);
   test-flow-control: PASS (3m39s) — включая pytest по dist-маршруту
   (/instructors/pending 200 в test_auth_route).
3. **MIN-1 (node/npm предусловие bare-metal, FR-57)** — добавлено в
   deploy/RUNBOOK.md (раздел «Предусловие bare-metal деплоя»: node 22 =
   pinned node:22-slim; `cd frontend/vue && npm ci && npm run build` перед
   деплоем; контейнерный деплой собирает сам). Коммит 326048c.

Полный сьют ветки: 380 passed, 0 failed (тихая машина; таймерный NFR-001
зеленый в наборе).

## Вердикт: approve

Reviewer-Delegation: deleg-cr-20261103-vue22-external

## Замечания

Нет. CI-прогоны — факты из Actions этой ветки (PR#107).
