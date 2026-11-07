# Regress add-vue-s11-status-forms — regress-final.md

- change: add-vue-s11-status-forms
- date: 2026-11-07T14:21:08+00:00
- commit: 438afc95c289e04b94740232733bd56973453d57
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s11-vue
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 724.7s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 37
- changed files: 37
  - backend/app.py
  - code-reviews/add-vue-s11-status-forms/review-001-3.1-2.1-2.2.md
  - code-reviews/add-vue-s11-status-forms/review-002-3.1-2.1-2.2.md
  - code-reviews/add-vue-s11-status-forms/review-mapping.json
  - frontend/js/instructor-rejected.js
  - frontend/js/review-form.js
  - frontend/review-form.html
  - frontend/vue/instructors-rejected.html
  - frontend/vue/review-form.html
  - frontend/vue/scripts/check-budgets.mjs
  - frontend/vue/src/pages/instructor-rejected/App.vue
  - frontend/vue/src/pages/instructor-rejected/main.js
  - frontend/vue/src/pages/instructor-rejected/styles.css
  - frontend/vue/src/pages/review-form/App.vue
  - frontend/vue/src/pages/review-form/main.js
  - frontend/vue/src/pages/review-form/styles.css
  - frontend/vue/src/shared/utils.js
  - frontend/vue/vite.config.mjs
  - openspec/changes/add-vue-s11-status-forms/design.md
  - openspec/changes/add-vue-s11-status-forms/proposal.md
  - openspec/changes/add-vue-s11-status-forms/specs/Frontend/spec.md
  - openspec/changes/add-vue-s11-status-forms/tasks.md
  - test-model/approved/add-vue-s11-status-forms/TC-S11UI-001.md
  - test-model/approved/add-vue-s11-status-forms/TC-S11UI-002.md
  - test-model/approved/add-vue-s11-status-forms/TC-S11UI-003.md
  - test-model/approved/add-vue-s11-status-forms/TC-S11UI-004.md
  - test-model/approved/add-vue-s11-status-forms/TC-S11UI-005.md
  - test-model/approved/add-vue-s11-status-forms/TC-S11UI-006.md
  - test-model/approved/add-vue-s11-status-forms/TC-S11UI-007.md
  - test-model/approved/add-vue-s11-status-forms/TC-S11UI-008.md
  - test-model/approved/add-vue-s11-status-forms/TC-S11UI-009.md
  - test-model/approved/add-vue-s11-status-forms/coverage.md
  - test-model/reviews/add-vue-s11-status-forms/review-001-architecture.md
  - test-model/reviews/add-vue-s11-status-forms/review-001-cases.md
  - tests/api/test_s3_backend.py
  - tests/web/test_instructor_pages.py
  - tests/web/test_ui_playwright.py
- suites: tests
- pytest exit code: 0

## Хвост лога (до 50 строк)

```
........................................................................ [ 15%]
........................................................................ [ 31%]
........................................................................ [ 47%]
........................................................................ [ 63%]
........................................................................ [ 79%]
........................................................................ [ 95%]
....................                                                     [100%]
=============================== warnings summary ===============================
../../../../auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
452 passed, 1 warning in 721.14s (0:12:01)
```
