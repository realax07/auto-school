# Regress add-calendar-weeks-availability — regress-final.md

- change: add-calendar-weeks-availability
- date: 2026-11-05T15:42:23+00:00
- commit: ac274ffa98bab3ea00a78a1a1cd6776d10917672
- worktree: /home/hermes-bot/auto-school
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 677.1s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 35
- changed files: 35
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
  - tests/test_s10_backend.py
  - tests/test_s3_backend.py
  - tests/test_s5_backend.py
  - tests/test_s7_backend.py
  - tests/test_s8_backend.py
  - tests/test_ui_playwright.py
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

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
430 passed, 1 warning in 674.46s (0:11:14)
```
