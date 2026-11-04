# Regress add-vue-framework-pilot — regress-final.md

- change: add-vue-framework-pilot
- date: 2026-11-04T12:05:37+00:00
- commit: a80640bdc37eb7c42f85b6b1c7bf798f237a3e8d
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s9-vue
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 634.4s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 34
- changed files: 34
  - .dockerignore
  - .github/workflows/flow.yml
  - .gitignore
  - Dockerfile
  - architecture/adr/008-vue3-vite-migration.md
  - architecture/adr/009-policy-artifact-consent.md
  - architecture/map.md
  - backend/app.py
  - code-reviews/add-vue-framework-pilot/review-001-2.1.md
  - code-reviews/add-vue-framework-pilot/review-002-2.2.md
  - code-reviews/add-vue-framework-pilot/review-003-2.3.md
  - code-reviews/add-vue-framework-pilot/review-004-3.1.md
  - code-reviews/add-vue-framework-pilot/review-005-4.1.md
  - code-reviews/add-vue-framework-pilot/review-006-5.1.md
  - code-reviews/add-vue-framework-pilot/review-011-2.2.md
  - deploy/RUNBOOK.md
  - frontend/vue/instructors-pending.html
  - frontend/vue/package-lock.json
  - frontend/vue/package.json
  - frontend/vue/scripts/check-budgets.mjs
  - frontend/vue/src/pages/instructor-pending/App.vue
  - frontend/vue/src/pages/instructor-pending/main.js
  - frontend/vue/src/pages/instructor-pending/styles.css
  - frontend/vue/src/shared/api.js
  - frontend/vue/vite.config.mjs
  - openspec/changes/add-vue-framework-pilot/arch-review-002.md
  - openspec/changes/add-vue-framework-pilot/arch-review.md
  - openspec/changes/add-vue-framework-pilot/design.md
  - openspec/changes/add-vue-framework-pilot/proposal.md
  - openspec/changes/add-vue-framework-pilot/research.md
  - openspec/changes/add-vue-framework-pilot/specs/Frontend/spec.md
  - openspec/changes/add-vue-framework-pilot/tasks.md
  - tests/test_instructor_pages.py
  - tests/test_ui_playwright.py
- suites: tests
- pytest exit code: 0

## Хвост лога (до 50 строк)

```
........................................................................ [ 17%]
........................................................................ [ 35%]
........................................................................ [ 52%]
........................................................................ [ 70%]
........................................................................ [ 88%]
.................................................                        [100%]
=============================== warnings summary ===============================
../../../../auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

tests/test_s9_backend.py::test_tc_s9be_007_parallel_exchanges_exactly_one_200
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2346: UnsupportedFieldAttributeWarning: The 'alias' attribute with value 'filename' was provided to the `Field()` function, which has no effect in the context it was used. 'alias' is field-specific metadata, and can only be attached to a model field using `Annotated` metadata or by assignment. This may have happened because an `Annotated` type alias using the `type` statement was used, or if the `Field()` function was attached to a single member of a union type.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
409 passed, 2 warnings in 631.61s (0:10:31)
```
