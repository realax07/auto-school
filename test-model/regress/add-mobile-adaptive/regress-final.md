# Regress add-mobile-adaptive — regress-final.md

- change: add-mobile-adaptive
- date: 2026-11-17T23:50:38+00:00
- commit: d60d815088b34a8b529f6e917a15b54a3e030c5b
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s18-mobile
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 626.2s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 71
- changed files: 71
  - architecture/map.md
  - code-reviews/add-mobile-adaptive/review-001-consolidated-18.1-18.4.md
  - code-reviews/add-mobile-adaptive/review-002-consolidated-18.1-18.4.md
  - code-reviews/add-mobile-adaptive/review-003-consolidated-18.1-18.4.md
  - code-reviews/add-mobile-adaptive/review-18.1.1-001.md
  - code-reviews/add-mobile-adaptive/review-18.1.2-001.md
  - code-reviews/add-mobile-adaptive/review-18.2.1-001.md
  - code-reviews/add-mobile-adaptive/review-18.2.2-001.md
  - code-reviews/add-mobile-adaptive/review-18.2.3-001.md
  - code-reviews/add-mobile-adaptive/review-18.3.1-001.md
  - code-reviews/add-mobile-adaptive/review-18.3.2-001.md
  - code-reviews/add-mobile-adaptive/review-18.3.3-001.md
  - code-reviews/add-mobile-adaptive/review-18.4.1-001.md
  - code-reviews/add-mobile-adaptive/review-18.4.2-001.md
  - code-reviews/add-mobile-adaptive/review-18.4.3-001.md
  - code-reviews/add-mobile-adaptive/review-mapping.json
  - design/mocks/mobile/mobile-admin.html
  - design/mocks/mobile/mobile-book-slot.html
  - design/mocks/mobile/mobile-bookings.html
  - design/mocks/mobile/mobile-choice.html
  - design/mocks/mobile/mobile-dispute.html
  - design/mocks/mobile/mobile-home.html
  - design/mocks/mobile/mobile-instructor.html
  - design/mocks/mobile/mobile-landing.html
  - design/mocks/mobile/mobile-login.html
  - design/mocks/mobile/mobile-pdd-fines.html
  - design/mocks/mobile/mobile-pdd-rules.html
  - design/mocks/mobile/mobile-pdd-sign-detail.html
  - design/mocks/mobile/mobile-pdd-signs.html
  - design/mocks/mobile/mobile-pdd-tickets.html
  - design/mocks/mobile/mobile-policy.html
  - design/mocks/mobile/mobile-register.html
  - design/mocks/mobile/mobile-registered.html
  - design/mocks/mobile/mobile-rejected.html
  - design/mocks/mobile/mobile-requests.html
  - design/mocks/mobile/mobile-review.html
  - design/mocks/mobile/mobile-wallet.html
  - frontend/vue/src/components/MobileTabBar.vue
  - frontend/vue/src/components/StudentSidebar.vue
  - frontend/vue/src/pages/admin-dashboard/styles.css
  - frontend/vue/src/pages/cabinet/App.vue
  - frontend/vue/src/pages/cabinet/styles.css
  - frontend/vue/src/pages/documents/styles.css
  - frontend/vue/src/pages/instructor-choice/App.vue
  - frontend/vue/src/pages/instructor-choice/styles.css
  - frontend/vue/src/pages/instructor-dashboard/styles.css
  - frontend/vue/src/pages/instructors/styles.css
  - frontend/vue/src/pages/landing/styles.css
  - openspec/changes/add-mobile-adaptive/design.md
  - openspec/changes/add-mobile-adaptive/proposal.md
  - … и еще 21
- suites: tests
- pytest exit code: 0

## Хвост лога (до 50 строк)

```
........................................................................ [ 12%]
........................................................................ [ 24%]
........................................................................ [ 37%]
........................................................................ [ 49%]
........................................................................ [ 61%]
........................................................................ [ 74%]
........................................................................ [ 86%]
........................................................................ [ 98%]
.......                                                                  [100%]
=============================== warnings summary ===============================
../../../../auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

tests/api/test_s9_backend.py::test_tc_s9be_007_parallel_exchanges_exactly_one_200
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2346: UnsupportedFieldAttributeWarning: The 'alias' attribute with value 'filename' was provided to the `Field()` function, which has no effect in the context it was used. 'alias' is field-specific metadata, and can only be attached to a model field using `Annotated` metadata or by assignment. This may have happened because an `Annotated` type alias using the `type` statement was used, or if the `Field()` function was attached to a single member of a union type.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
583 passed, 2 warnings in 624.99s (0:10:24)
```
