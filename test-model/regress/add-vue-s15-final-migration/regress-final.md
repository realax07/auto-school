# Regress add-vue-s15-final-migration — regress-final.md

- change: add-vue-s15-final-migration
- date: 2026-11-13T14:12:26+00:00
- commit: d10d3aba45b7435fbb8cce68104bd5b4040b759a
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s15-final
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 551.2s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 59
- changed files: 59
  - architecture/map.md
  - backend/app.py
  - code-reviews/add-vue-s15-final-migration/review-001-1.1-2.1-2.2-3.1-4.1-4.2-5.1-6.1-7.1.md
  - code-reviews/add-vue-s15-final-migration/review-mapping.json
  - decisions/2026-11-12-sprint15-go.md
  - frontend/js/admin/admin-dashboard.js
  - frontend/js/admin/admin-login.js
  - frontend/js/policy.js
  - frontend/js/shared/api.js
  - frontend/js/shared/utils.js
  - frontend/js/student/cabinet.js
  - frontend/js/student/instructor-choice.js
  - frontend/vue/admin-dashboard.html
  - frontend/vue/admin-login.html
  - frontend/vue/cabinet.html
  - frontend/vue/instructor-choice.html
  - frontend/vue/policy.html
  - frontend/vue/registered.html
  - frontend/vue/scripts/check-budgets.mjs
  - frontend/vue/src/pages/admin-dashboard/App.vue
  - frontend/vue/src/pages/admin-dashboard/main.js
  - frontend/vue/src/pages/admin-dashboard/styles.css
  - frontend/vue/src/pages/admin-login/App.vue
  - frontend/vue/src/pages/admin-login/main.js
  - frontend/vue/src/pages/admin-login/styles.css
  - frontend/vue/src/pages/cabinet/App.vue
  - frontend/vue/src/pages/cabinet/main.js
  - frontend/vue/src/pages/cabinet/styles.css
  - frontend/vue/src/pages/instructor-choice/App.vue
  - frontend/vue/src/pages/instructor-choice/main.js
  - frontend/vue/src/pages/instructor-choice/styles.css
  - frontend/vue/src/pages/policy/App.vue
  - frontend/vue/src/pages/policy/main.js
  - frontend/vue/src/pages/policy/styles.css
  - frontend/vue/src/pages/registered/App.vue
  - frontend/vue/src/pages/registered/main.js
  - frontend/vue/src/pages/registered/styles.css
  - frontend/vue/src/shared/utils.js
  - frontend/vue/vite.config.mjs
  - openspec/changes/add-vue-s15-final-migration/design.md
  - openspec/changes/add-vue-s15-final-migration/proposal.md
  - openspec/changes/add-vue-s15-final-migration/specs/Frontend/spec.md
  - openspec/changes/add-vue-s15-final-migration/tasks.md
  - scripts/check_tag_balance.py
  - test-model/approved/add-vue-s15-final-migration/TC-S15-001.md
  - test-model/approved/add-vue-s15-final-migration/TC-S15-002.md
  - test-model/approved/add-vue-s15-final-migration/TC-S15-003.md
  - test-model/approved/add-vue-s15-final-migration/TC-S15-004.md
  - test-model/approved/add-vue-s15-final-migration/TC-S15-005.md
  - test-model/approved/add-vue-s15-final-migration/TC-S15-006.md
  - … и еще 9
- suites: tests
- pytest exit code: 0

## Хвост лога (до 50 строк)

```
........................................................................ [ 15%]
........................................................................ [ 31%]
........................................................................ [ 46%]
........................................................................ [ 62%]
........................................................................ [ 78%]
........................................................................ [ 93%]
............................                                             [100%]
=============================== warnings summary ===============================
../../../../auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

tests/api/test_s9_backend.py::test_tc_s9be_007_parallel_exchanges_exactly_one_200
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2346: UnsupportedFieldAttributeWarning: The 'alias' attribute with value 'filename' was provided to the `Field()` function, which has no effect in the context it was used. 'alias' is field-specific metadata, and can only be attached to a model field using `Annotated` metadata or by assignment. This may have happened because an `Annotated` type alias using the `type` statement was used, or if the `Field()` function was attached to a single member of a union type.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
460 passed, 2 warnings in 549.51s (0:09:09)
```
