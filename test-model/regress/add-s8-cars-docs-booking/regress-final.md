# Regress add-s8-cars-docs-booking — regress-final.md

- change: add-s8-cars-docs-booking
- date: 2026-11-02T14:04:13+00:00
- commit: 0c950262977f58c686e966172809e602b13a86b3
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s8-int
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 549.1s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 83
- changed files: 83
  - architecture/adr/007-document-versions.md
  - architecture/map.md
  - backend/db.py
  - backend/instructor_cars.py
  - backend/instructor_documents.py
  - backend/student_requests.py
  - code-reviews/add-s8-cars-docs-booking/review-001-1.1.md
  - code-reviews/add-s8-cars-docs-booking/review-002-2.1.md
  - code-reviews/add-s8-cars-docs-booking/review-003-3.1.md
  - code-reviews/add-s8-cars-docs-booking/review-004-4.1.md
  - code-reviews/add-s8-cars-docs-booking/review-005-5.1.md
  - code-reviews/add-s8-cars-docs-booking/review-006-6.1.md
  - code-reviews/add-s8-cars-docs-booking/review-007-7.1.md
  - code-reviews/add-s8-cars-docs-booking/review-008-8.1.md
  - code-reviews/add-s8-cars-docs-booking/review-009-9.1.md
  - code-reviews/add-s8-cars-docs-booking/review-010-9.2.md
  - code-reviews/add-s8-cars-docs-booking/review-011-2.1.md
  - code-reviews/add-s8-cars-docs-booking/review-012-3.1.md
  - code-reviews/add-s8-cars-docs-booking/review-013-8.1.md
  - code-reviews/add-s8-cars-docs-booking/review-014-9.1.md
  - code-reviews/add-s8-cars-docs-booking/review-015-9.2.md
  - code-reviews/add-s8-cars-docs-booking/review-016-10.1.md
  - code-reviews/add-s8-cars-docs-booking/review-017-11.1.md
  - decisions/2026-11-01-sprint8-go.md
  - design/mocks/admin-documents.html
  - design/mocks/calendar-booking-s8.html
  - design/mocks/my-documents-s8.html
  - design/mocks/my-students.html
  - frontend/admin-dashboard.html
  - frontend/instructor-dashboard.html
  - frontend/js/admin-dashboard.js
  - frontend/js/dashboard-instructor.js
  - openspec/changes/add-s8-cars-docs-booking/arch-review.md
  - openspec/changes/add-s8-cars-docs-booking/design.md
  - openspec/changes/add-s8-cars-docs-booking/diagnostics-3.1.md
  - openspec/changes/add-s8-cars-docs-booking/proposal.md
  - openspec/changes/add-s8-cars-docs-booking/specs/instructor-availability/spec.md
  - openspec/changes/add-s8-cars-docs-booking/specs/instructor-cars/spec.md
  - openspec/changes/add-s8-cars-docs-booking/specs/instructor-documents/spec.md
  - openspec/changes/add-s8-cars-docs-booking/specs/student-requests/spec.md
  - openspec/changes/add-s8-cars-docs-booking/tasks.md
  - sdd.md
  - test-model/approved/add-s8-cars-docs-booking/TC-S8BE-001.md
  - test-model/approved/add-s8-cars-docs-booking/TC-S8BE-002.md
  - test-model/approved/add-s8-cars-docs-booking/TC-S8BE-003.md
  - test-model/approved/add-s8-cars-docs-booking/TC-S8BE-004.md
  - test-model/approved/add-s8-cars-docs-booking/TC-S8BE-005.md
  - test-model/approved/add-s8-cars-docs-booking/TC-S8BE-006.md
  - test-model/approved/add-s8-cars-docs-booking/TC-S8BE-007.md
  - test-model/approved/add-s8-cars-docs-booking/TC-S8BE-008.md
  - … и еще 33
- suites: tests
- pytest exit code: 0

## Хвост лога (до 50 строк)

```
........................................................................ [ 20%]
........................................................................ [ 40%]
........................................................................ [ 60%]
........................................................................ [ 80%]
.......................................................................  [100%]
=============================== warnings summary ===============================
../../../../auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
359 passed, 1 warning in 546.96s (0:09:06)
```
