# Regress add-vue-s14-instructor-loop — regress-final.md

- change: add-vue-s14-instructor-loop
- date: 2026-11-12T15:10:08+00:00
- commit: b46b22d49afad89be4018f58ce1ecde9cd4b8fc4
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s14-vue
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 570.2s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 49
- changed files: 49
  - backend/app.py
  - code-reviews/add-vue-s14-instructor-loop/review-001-1.1-2.1-3.1-3.2-3.3-4.1-4.2-5.1-6.1.md
  - code-reviews/add-vue-s14-instructor-loop/review-mapping.json
  - decisions/2026-11-09-sprint14-go.md
  - frontend/instructor-cabinet-stub.html
  - frontend/js/instructor/instructor-cabinet-stub.js
  - frontend/js/instructors.js
  - frontend/vue/documents.html
  - frontend/vue/instructor-dashboard.html
  - frontend/vue/instructors.html
  - frontend/vue/scripts/check-budgets.mjs
  - frontend/vue/src/pages/documents/App.vue
  - frontend/vue/src/pages/documents/main.js
  - frontend/vue/src/pages/documents/styles.css
  - frontend/vue/src/pages/instructor-dashboard/App.vue
  - frontend/vue/src/pages/instructor-dashboard/main.js
  - frontend/vue/src/pages/instructor-dashboard/styles.css
  - frontend/vue/src/pages/instructors/App.vue
  - frontend/vue/src/pages/instructors/main.js
  - frontend/vue/src/pages/instructors/styles.css
  - frontend/vue/src/pages/landing/App.vue
  - frontend/vue/src/shared/LoginModal.vue
  - frontend/vue/src/shared/loginWiring.js
  - frontend/vue/src/shared/utils.js
  - frontend/vue/vite.config.mjs
  - openspec/changes/add-vue-s14-instructor-loop/design.md
  - openspec/changes/add-vue-s14-instructor-loop/proposal.md
  - openspec/changes/add-vue-s14-instructor-loop/specs/Frontend/spec.md
  - openspec/changes/add-vue-s14-instructor-loop/specs/instructor-auth/spec.md
  - openspec/changes/add-vue-s14-instructor-loop/tasks.md
  - scripts/check_tag_balance.py
  - test-model/approved/add-vue-s14-instructor-loop/TC-S14-001.md
  - test-model/approved/add-vue-s14-instructor-loop/TC-S14-002.md
  - test-model/approved/add-vue-s14-instructor-loop/TC-S14-003.md
  - test-model/approved/add-vue-s14-instructor-loop/TC-S14-004.md
  - test-model/approved/add-vue-s14-instructor-loop/TC-S14-005.md
  - test-model/approved/add-vue-s14-instructor-loop/TC-S14-006.md
  - test-model/approved/add-vue-s14-instructor-loop/TC-S14-007.md
  - test-model/approved/add-vue-s14-instructor-loop/coverage.md
  - test-model/impact/add-vue-s14-instructor-loop.md
  - test-model/regress/add-vue-s14-instructor-loop/regress-final.md
  - test-model/reviews/add-vue-s14-instructor-loop/review-001-architecture.md
  - test-model/reviews/add-vue-s14-instructor-loop/review-001-cases.md
  - tests/api/test_auth_route.py
  - tests/api/test_instructor_dashboard.py
  - tests/api/test_s3_backend.py
  - tests/web/test_instructor_pages.py
  - tests/web/test_login_modal.py
  - tests/web/test_ui_playwright.py
- suites: tests
- pytest exit code: 0

## Хвост лога (до 50 строк)

```
........................................................................ [ 15%]
........................................................................ [ 31%]
........................................................................ [ 47%]
........................................................................ [ 63%]
........................................................................ [ 78%]
........................................................................ [ 94%]
........................                                                 [100%]
=============================== warnings summary ===============================
../../../../auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

tests/api/test_s9_backend.py::test_tc_s9be_007_parallel_exchanges_exactly_one_200
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2346: UnsupportedFieldAttributeWarning: The 'alias' attribute with value 'x-admin-token' was provided to the `Field()` function, which has no effect in the context it was used. 'alias' is field-specific metadata, and can only be attached to a model field using `Annotated` metadata or by assignment. This may have happened because an `Annotated` type alias using the `type` statement was used, or if the `Field()` function was attached to a single member of a union type.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
456 passed, 2 warnings in 568.42s (0:09:28)
```
