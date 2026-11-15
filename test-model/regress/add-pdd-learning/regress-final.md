# Regress add-pdd-learning — regress-final.md

- change: add-pdd-learning
- date: 2026-11-15T18:07:43+00:00
- commit: 6fed728f9a775e6d2582e5aabfda19ff9d5bba6a
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s17-pdd
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 721.6s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 44
- changed files: 44
  - .dockerignore
  - .gitignore
  - Dockerfile
  - architecture/map.md
  - backend/app.py
  - code-reviews/add-pdd-learning/review-001-1.2-1.3-1.4-1.5-1.6-1.7.md
  - code-reviews/add-pdd-learning/review-001-architecture.md
  - code-reviews/add-pdd-learning/review-002-1.2-1.3-1.4-1.5-1.6-1.7.md
  - code-reviews/add-pdd-learning/review-mapping.json
  - content/pdd/README.md
  - content/pdd/znaki-details.json
  - decisions/2026-11-15-sprint17-go.md
  - frontend/vue/cabinet.html
  - frontend/vue/package.json
  - frontend/vue/scripts/check-budgets.mjs
  - frontend/vue/scripts/generate-pdd-json.mjs
  - frontend/vue/src/pages/cabinet/App.vue
  - frontend/vue/src/pages/cabinet/sections/PddFines.vue
  - frontend/vue/src/pages/cabinet/sections/PddRules.vue
  - frontend/vue/src/pages/cabinet/sections/PddSigns.vue
  - frontend/vue/src/pages/cabinet/sections/PddTickets.vue
  - frontend/vue/src/pages/cabinet/sections/pdd-logic.mjs
  - frontend/vue/src/pages/cabinet/styles.css
  - openspec/changes/add-pdd-learning/design.md
  - openspec/changes/add-pdd-learning/proposal.md
  - openspec/changes/add-pdd-learning/specs/learning/spec.md
  - openspec/changes/add-pdd-learning/tasks.md
  - test-model/approved/add-pdd-learning/TC-S17-001.md
  - test-model/approved/add-pdd-learning/TC-S17-002.md
  - test-model/approved/add-pdd-learning/TC-S17-003.md
  - test-model/approved/add-pdd-learning/TC-S17-004.md
  - test-model/approved/add-pdd-learning/TC-S17-005.md
  - test-model/approved/add-pdd-learning/TC-S17-006.md
  - test-model/approved/add-pdd-learning/TC-S17-007.md
  - test-model/approved/add-pdd-learning/TC-S17-008.md
  - test-model/approved/add-pdd-learning/coverage.md
  - test-model/bugs/BUG-064.md
  - test-model/regress/add-pdd-learning/regress-final.md
  - test-model/reviews/add-pdd-learning/review-001-cases.md
  - tests/unit/fixtures/pdd_logic_harness.mjs
  - tests/unit/test_pdd_generator.py
  - tests/unit/test_pdd_tickets_logic.py
  - tests/web/test_pdd_sections.py
  - tests/web/test_ui_playwright.py
- suites: tests
- pytest exit code: 0

## Хвост лога (до 50 строк)

```
........................................................................ [ 12%]
........................................................................ [ 25%]
........................................................................ [ 38%]
........................................................................ [ 51%]
........................................................................ [ 64%]
........................................................................ [ 77%]
........................................................................ [ 90%]
...................................................                      [100%]
=============================== warnings summary ===============================
../../../../auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
555 passed, 1 warning in 719.44s (0:11:59)
```
