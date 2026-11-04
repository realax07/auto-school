# Regress add-application-status-polling — regress-final.md

- change: add-application-status-polling
- date: 2026-11-04T08:43:59+00:00
- commit: 6ba86ecdd05a75cd82f9cb6a050fefcbe69fffa0
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s9-polling
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 504.9s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 34
- changed files: 34
  - backend/app.py
  - backend/application_status.py
  - backend/auth.py
  - backend/db.py
  - backend/instructors.py
  - code-reviews/add-application-status-polling/review-001-1.1.md
  - code-reviews/add-application-status-polling/review-002-2.1.md
  - code-reviews/add-application-status-polling/review-003-3.1.md
  - code-reviews/add-application-status-polling/review-004-5.1.md
  - frontend/js/apply.js
  - openspec/changes/add-application-status-polling/arch-review-002.md
  - openspec/changes/add-application-status-polling/arch-review.md
  - openspec/changes/add-application-status-polling/design.md
  - openspec/changes/add-application-status-polling/proposal.md
  - openspec/changes/add-application-status-polling/specs/StudentFlow/spec.md
  - openspec/changes/add-application-status-polling/tasks.md
  - test-model/approved/add-application-status-polling/TC-S9BE-001.md
  - test-model/approved/add-application-status-polling/TC-S9BE-002.md
  - test-model/approved/add-application-status-polling/TC-S9BE-003.md
  - test-model/approved/add-application-status-polling/TC-S9BE-004.md
  - test-model/approved/add-application-status-polling/TC-S9BE-005.md
  - test-model/approved/add-application-status-polling/TC-S9BE-006.md
  - test-model/approved/add-application-status-polling/TC-S9BE-007.md
  - test-model/new/add-application-status-polling/TC-S9BE-001.md
  - test-model/new/add-application-status-polling/TC-S9BE-002.md
  - test-model/new/add-application-status-polling/TC-S9BE-003.md
  - test-model/new/add-application-status-polling/TC-S9BE-004.md
  - test-model/new/add-application-status-polling/TC-S9BE-005.md
  - test-model/new/add-application-status-polling/TC-S9BE-006.md
  - test-model/new/add-application-status-polling/TC-S9BE-007.md
  - test-model/reviews/add-application-status-polling/review-001-cases.md
  - tests/test_db.py
  - tests/test_instructors_apply.py
  - tests/test_s9_backend.py
- suites: tests
- pytest exit code: 0

## Хвост лога (до 50 строк)

```
........................................................................ [ 19%]
........................................................................ [ 38%]
........................................................................ [ 57%]
........................................................................ [ 77%]
........................................................................ [ 96%]
..............                                                           [100%]
=============================== warnings summary ===============================
../../../../auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
374 passed, 1 warning in 503.07s (0:08:23)
```
