# Regress add-personal-data-policy — regress-final.md

- change: add-personal-data-policy
- date: 2026-11-04T10:56:04+00:00
- commit: 5c6ceb8f217b0ce1bf4d06339352217c9f280d74
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s9-policy
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 650.7s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 83
- changed files: 83
  - architecture/adr/008-policy-artifact-consent.md
  - architecture/map.md
  - backend/app.py
  - backend/db.py
  - backend/instructors.py
  - backend/policy.py
  - backend/register.py
  - code-reviews/add-personal-data-policy/review-001-1.1.md
  - code-reviews/add-personal-data-policy/review-002-2.1.md
  - code-reviews/add-personal-data-policy/review-003-3.1.md
  - code-reviews/add-personal-data-policy/review-004-4.1.md
  - code-reviews/add-personal-data-policy/review-005-5.1.md
  - code-reviews/add-personal-data-policy/review-006-5.2.md
  - code-reviews/add-personal-data-policy/review-007-6.1.md
  - code-reviews/add-personal-data-policy/review-008-7.1.md
  - code-reviews/add-personal-data-policy/review-009-7.2.md
  - code-reviews/add-personal-data-policy/review-010-8.1.md
  - code-reviews/add-personal-data-policy/review-011-6.1.md
  - code-reviews/add-personal-data-policy/review-012-9.1.md
  - deploy/RUNBOOK.md
  - deploy/policy/policy.md
  - docker-compose.yml
  - frontend/index.html
  - frontend/instructor-apply.html
  - frontend/js/apply.js
  - frontend/js/landing.js
  - frontend/js/policy.js
  - frontend/policy.html
  - openspec/changes/add-personal-data-policy/arch-review.md
  - openspec/changes/add-personal-data-policy/design.md
  - openspec/changes/add-personal-data-policy/proposal.md
  - openspec/changes/add-personal-data-policy/specs/PersonalData/spec.md
  - openspec/changes/add-personal-data-policy/tasks.md
  - sdd.md
  - test-model/approved/add-personal-data-policy/TC-PD-001.md
  - test-model/approved/add-personal-data-policy/TC-PD-002.md
  - test-model/approved/add-personal-data-policy/TC-PD-003.md
  - test-model/approved/add-personal-data-policy/TC-PD-004.md
  - test-model/approved/add-personal-data-policy/TC-PD-005.md
  - test-model/approved/add-personal-data-policy/TC-PD-006.md
  - test-model/approved/add-personal-data-policy/TC-PD-007.md
  - test-model/approved/add-personal-data-policy/TC-PD-008.md
  - test-model/approved/add-personal-data-policy/TC-PD-009.md
  - test-model/approved/add-personal-data-policy/TC-PD-010.md
  - test-model/approved/add-personal-data-policy/TC-PD-011.md
  - test-model/approved/add-personal-data-policy/TC-PD-012.md
  - test-model/approved/add-personal-data-policy/TC-PD-013.md
  - test-model/approved/add-personal-data-policy/TC-PD-014.md
  - test-model/approved/add-personal-data-policy/TC-PD-015.md
  - test-model/approved/add-personal-data-policy/TC-PD-016.md
  - … и еще 33
- suites: tests
- pytest exit code: 0

## Хвост лога (до 50 строк)

```
........................................................................ [ 17%]
........................................................................ [ 35%]
........................................................................ [ 53%]
........................................................................ [ 71%]
........................................................................ [ 89%]
...........................................                              [100%]
=============================== warnings summary ===============================
../../../../auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

tests/test_s9_backend.py::test_tc_s9be_007_parallel_exchanges_exactly_one_200
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2346: UnsupportedFieldAttributeWarning: The 'alias' attribute with value 'target' was provided to the `Field()` function, which has no effect in the context it was used. 'alias' is field-specific metadata, and can only be attached to a model field using `Annotated` metadata or by assignment. This may have happened because an `Annotated` type alias using the `type` statement was used, or if the `Field()` function was attached to a single member of a union type.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
403 passed, 2 warnings in 647.66s (0:10:47)
```
