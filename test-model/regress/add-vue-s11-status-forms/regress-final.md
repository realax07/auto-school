# Regress add-vue-s11-status-forms — regress-final.md

- change: add-vue-s11-status-forms
- date: 2026-11-07T15:05:17+00:00
- commit: ca237063904b49cc670c78f68c4b634393169ad3
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s11-vue
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 699.8s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 39
- changed files: 39
  - backend/app.py
  - code-reviews/add-vue-s11-status-forms/review-001-3.1-2.1-2.2.md
  - code-reviews/add-vue-s11-status-forms/review-002-3.1-2.1-2.2.md
  - code-reviews/add-vue-s11-status-forms/review-003-1.1-3.2-4.1-5.1.md
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
  - test-model/regress/add-vue-s11-status-forms/regress-final.md
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
......................                                                   [100%]
=============================== warnings summary ===============================
../../../../auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

tests/api/test_s9_backend.py::test_tc_s9be_007_parallel_exchanges_exactly_one_200
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2346: UnsupportedFieldAttributeWarning: The 'alias' attribute with value 'status' was provided to the `Field()` function, which has no effect in the context it was used. 'alias' is field-specific metadata, and can only be attached to a model field using `Annotated` metadata or by assignment. This may have happened because an `Annotated` type alias using the `type` statement was used, or if the `Field()` function was attached to a single member of a union type.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
454 passed, 2 warnings in 697.03s (0:11:37)
```
