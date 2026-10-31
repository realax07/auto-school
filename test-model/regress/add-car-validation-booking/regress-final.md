# Regress add-car-validation-booking — regress-final.md

- change: add-car-validation-booking
- date: 2026-10-31T09:30:05+00:00
- commit: 59670a36ce27746f1dfe26d389e60bb00b8ae1cf
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s7-front
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 444.5s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 75
- changed files: 75
  - .design-check-tmp/app.db
  - backend/booking.py
  - backend/db.py
  - backend/instructor_cars.py
  - backend/instructor_summary.py
  - backend/student_marketplace.py
  - code-reviews/add-car-validation-booking/review-001.md
  - design/mocks/admin-cars.html
  - design/mocks/booking-instructor.html
  - design/mocks/booking-student-cars.html
  - design/mocks/my-cars-s7.html
  - design/mocks/my-documents.html
  - frontend/admin-dashboard.html
  - frontend/cabinet.html
  - frontend/instructor-choice.html
  - frontend/instructor-dashboard.html
  - frontend/instructors.html
  - frontend/js/admin-dashboard.js
  - frontend/js/cabinet.js
  - frontend/js/dashboard-instructor.js
  - openspec/changes/add-car-validation-booking/arch-review.md
  - openspec/changes/add-car-validation-booking/design.md
  - openspec/changes/add-car-validation-booking/proposal.md
  - openspec/changes/add-car-validation-booking/specs/booking/spec.md
  - openspec/changes/add-car-validation-booking/specs/instructor-availability/spec.md
  - openspec/changes/add-car-validation-booking/specs/instructor-cars/spec.md
  - openspec/changes/add-car-validation-booking/specs/instructor-documents/spec.md
  - openspec/changes/add-car-validation-booking/specs/navigation/spec.md
  - openspec/changes/add-car-validation-booking/specs/student-instructor-choice/spec.md
  - openspec/changes/add-car-validation-booking/tasks.md
  - sdd.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-001.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-001b.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-003.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-004.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-005.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-006.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-007.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-008.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-009.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-010.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-011.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-012.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-013.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-014.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-015.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-016.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-017.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-018.md
  - test-model/approved/add-car-validation-booking/TC-S7BE-019-bug52-tiles.md
  - … и еще 25
- suites: tests
- pytest exit code: 0

## Хвост лога (до 50 строк)

```
........................................................................ [ 21%]
........................................................................ [ 42%]
........................................................................ [ 63%]
........................................................................ [ 84%]
....................................................                     [100%]
=============================== warnings summary ===============================
../../../../auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
340 passed, 1 warning in 442.26s (0:07:22)
```
