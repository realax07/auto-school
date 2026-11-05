# Regress add-calendar-weeks-availability — regress-final.md

- change: add-calendar-weeks-availability
- date: 2026-11-05T17:08:20+00:00
- commit: 4c573dee5ea0291146e88170351cd368312ae569
- worktree: /home/hermes-bot/auto-school
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 701.3s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 76
- changed files: 76
  - .github/workflows/flow.yml
  - Dockerfile
  - architecture/adr/010-calendar-recurring-availability.md
  - architecture/map.md
  - backend/booking.py
  - backend/db.py
  - backend/instructor_availability.py
  - code-reviews/add-calendar-weeks-availability/review-001-1.1.md
  - code-reviews/add-calendar-weeks-availability/review-002-2.1.md
  - code-reviews/add-calendar-weeks-availability/review-003-3.1.md
  - code-reviews/add-calendar-weeks-availability/review-004-4.1.md
  - code-reviews/add-calendar-weeks-availability/review-005-5.1.md
  - code-reviews/add-calendar-weeks-availability/review-006-6.1.md
  - code-reviews/add-calendar-weeks-availability/review-011-3.1.md
  - code-reviews/add-calendar-weeks-availability/review-012-4.1.md
  - decisions/2026-11-04-s10-calendar-sa-go.md
  - docker-compose.yml
  - frontend/cabinet.html
  - frontend/instructor-dashboard.html
  - frontend/js/cabinet.js
  - frontend/js/dashboard-instructor.js
  - openspec/changes/add-calendar-weeks-availability/arch-review-002.md
  - openspec/changes/add-calendar-weeks-availability/arch-review.md
  - openspec/changes/add-calendar-weeks-availability/design.md
  - openspec/changes/add-calendar-weeks-availability/proposal.md
  - openspec/changes/add-calendar-weeks-availability/research.md
  - openspec/changes/add-calendar-weeks-availability/specs/booking/spec.md
  - openspec/changes/add-calendar-weeks-availability/specs/instructor-availability/spec.md
  - openspec/changes/add-calendar-weeks-availability/tasks.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-001.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-002.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-003.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-004.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-005.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-006.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-007.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-008.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-009.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-010.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-011.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-012.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-013.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-014.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-015.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-016.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-017.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-018.md
  - test-model/approved/add-calendar-weeks-availability/TC-S10BE-019.md
  - test-model/new/add-calendar-weeks-availability/TC-S10BE-001.md
  - test-model/new/add-calendar-weeks-availability/TC-S10BE-002.md
  - … и еще 26
- suites: tests
- pytest exit code: 0

## Хвост лога (до 50 строк)

```
........................................................................ [ 16%]
........................................................................ [ 33%]
........................................................................ [ 50%]
........................................................................ [ 66%]
........................................................................ [ 83%]
......................................................................   [100%]
=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

tests/test_s9_backend.py::test_tc_s9be_007_parallel_exchanges_exactly_one_200
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2346: UnsupportedFieldAttributeWarning: The 'alias' attribute with value 'filename' was provided to the `Field()` function, which has no effect in the context it was used. 'alias' is field-specific metadata, and can only be attached to a model field using `Annotated` metadata or by assignment. This may have happened because an `Annotated` type alias using the `type` statement was used, or if the `Field()` function was attached to a single member of a union type.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
430 passed, 2 warnings in 698.30s (0:11:38)
```
