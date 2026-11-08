# Regress add-vue-s12-landing-apply — regress-final.md

- change: add-vue-s12-landing-apply
- date: 2026-11-08T09:14:15+00:00
- commit: 406c381da1895a1c362a6096dd71ab88ba295ea7
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s12-vue
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 558.9s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 46
- changed files: 46
  - backend/app.py
  - code-reviews/add-vue-s12-landing-apply/review-001-1.1-2.1-3.1-3.2-4.1-4.2-5.1-6.1.md
  - code-reviews/add-vue-s12-landing-apply/review-mapping.json
  - decisions/2026-11-08-sprint12-go.md
  - design/mocks/choice-instructor-a.html
  - design/mocks/choice-instructor-b.html
  - frontend/instructor-choice.html
  - frontend/js/apply.js
  - frontend/js/instructor-choice.js
  - frontend/js/landing.js
  - frontend/vue/index.html
  - frontend/vue/instructor-apply.html
  - frontend/vue/scripts/check-budgets.mjs
  - frontend/vue/src/pages/instructor-apply/App.vue
  - frontend/vue/src/pages/instructor-apply/main.js
  - frontend/vue/src/pages/instructor-apply/styles.css
  - frontend/vue/src/pages/landing/App.vue
  - frontend/vue/src/pages/landing/main.js
  - frontend/vue/src/pages/landing/styles.css
  - frontend/vue/src/shared/LoginModal.vue
  - frontend/vue/src/shared/RegisterModal.vue
  - frontend/vue/vite.config.mjs
  - openspec/changes/add-vue-s12-landing-apply/design.md
  - openspec/changes/add-vue-s12-landing-apply/proposal.md
  - openspec/changes/add-vue-s12-landing-apply/specs/Frontend/spec.md
  - openspec/changes/add-vue-s12-landing-apply/specs/student-instructor-choice/spec.md
  - openspec/changes/add-vue-s12-landing-apply/tasks.md
  - scripts/check_hero_overlap.py
  - test-model/approved/add-vue-s12-landing-apply/TC-S12UI-001.md
  - test-model/approved/add-vue-s12-landing-apply/TC-S12UI-002.md
  - test-model/approved/add-vue-s12-landing-apply/TC-S12UI-003.md
  - test-model/approved/add-vue-s12-landing-apply/TC-S12UI-004.md
  - test-model/approved/add-vue-s12-landing-apply/TC-S12UI-005.md
  - test-model/approved/add-vue-s12-landing-apply/TC-S12UI-006.md
  - test-model/approved/add-vue-s12-landing-apply/TC-S12UI-007.md
  - test-model/approved/add-vue-s12-landing-apply/TC-S12UI-008.md
  - test-model/approved/add-vue-s12-landing-apply/TC-S12UI-009.md
  - test-model/approved/add-vue-s12-landing-apply/TC-S12UI-010.md
  - test-model/approved/add-vue-s12-landing-apply/coverage.md
  - test-model/reviews/add-vue-s12-landing-apply/review-001-architecture.md
  - test-model/reviews/add-vue-s12-landing-apply/review-001-cases.md
  - tests/api/test_policy.py
  - tests/web/test_bug001.py
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

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
456 passed, 1 warning in 557.41s (0:09:17)
```
