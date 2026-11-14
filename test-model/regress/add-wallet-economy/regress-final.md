# Regress add-wallet-economy — regress-final.md

- change: add-wallet-economy
- date: 2026-11-14T21:48:47+00:00
- commit: dc378fa9301c75f4b2582e7074acc6a255bf1ef1
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s16-economy
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 614.6s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 60
- changed files: 60
  - .env.example
  - .github/workflows/flow.yml
  - BACKLOG.md
  - architecture/adr/006-containerization.md
  - architecture/map.md
  - backend/app.py
  - backend/auth/instructor_admin.py
  - backend/core/db.py
  - backend/student/booking.py
  - backend/wallet/__init__.py
  - backend/wallet/admin_transactions.py
  - backend/wallet/instructor_economy.py
  - backend/wallet/ledger.py
  - backend/wallet/sweeps.py
  - backend/wallet/wallets.py
  - code-reviews/add-wallet-economy/review-001-1.0-1.1-1.2-1.3-1.4-1.5-1.6.md
  - code-reviews/add-wallet-economy/review-001-architecture.md
  - code-reviews/add-wallet-economy/review-mapping.json
  - deploy/container-README.md
  - design/mocks/admin-transactions.html
  - design/mocks/instructor-earnings.html
  - design/mocks/wallet-student.html
  - docker-compose.yml
  - docs/ba/requirements-containerization.md
  - docs/ba/requirements-sprint16.md
  - frontend/vue/admin-dashboard.html
  - frontend/vue/cabinet.html
  - frontend/vue/instructor-dashboard.html
  - frontend/vue/src/pages/admin-dashboard/App.vue
  - frontend/vue/src/pages/admin-dashboard/styles.css
  - frontend/vue/src/pages/cabinet/App.vue
  - frontend/vue/src/pages/cabinet/styles.css
  - frontend/vue/src/pages/instructor-dashboard/App.vue
  - frontend/vue/src/pages/instructor-dashboard/styles.css
  - openspec/changes/add-wallet-economy/design.md
  - openspec/changes/add-wallet-economy/proposal.md
  - openspec/changes/add-wallet-economy/specs/admin-transactions/spec.md
  - openspec/changes/add-wallet-economy/specs/booking/spec.md
  - openspec/changes/add-wallet-economy/specs/containerization/spec.md
  - openspec/changes/add-wallet-economy/specs/instructor-management/spec.md
  - openspec/changes/add-wallet-economy/specs/payouts/spec.md
  - openspec/changes/add-wallet-economy/specs/wallet/spec.md
  - openspec/changes/add-wallet-economy/tasks.md
  - scripts/container_test.sh
  - test-model/approved/add-wallet-economy/TC-S16-001.md
  - test-model/approved/add-wallet-economy/TC-S16-002.md
  - test-model/approved/add-wallet-economy/TC-S16-003.md
  - test-model/approved/add-wallet-economy/TC-S16-004.md
  - test-model/approved/add-wallet-economy/TC-S16-005.md
  - test-model/approved/add-wallet-economy/TC-S16-006.md
  - … и еще 10
- suites: tests
- pytest exit code: 0

## Хвост лога (до 50 строк)

```
........................................................................ [ 14%]
........................................................................ [ 28%]
........................................................................ [ 43%]
........................................................................ [ 57%]
........................................................................ [ 71%]
........................................................................ [ 86%]
.....................................................................    [100%]
=============================== warnings summary ===============================
../../../../auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
501 passed, 1 warning in 612.58s (0:10:12)
```
