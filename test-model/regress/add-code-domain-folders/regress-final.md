# Regress add-code-domain-folders — regress-final.md

- change: add-code-domain-folders
- date: 2026-11-09T13:38:42+00:00
- commit: 397fb8f68f93ba7d44252a22c4eb7abc693f44e1
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s13-folders
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 571.8s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 77
- changed files: 77
  - backend/app.py
  - backend/auth/__init__.py
  - backend/auth/admin.py
  - backend/auth/application_status.py
  - backend/auth/auth.py
  - backend/auth/instructor_admin.py
  - backend/auth/register.py
  - backend/core/__init__.py
  - backend/core/config.py
  - backend/core/db.py
  - backend/core/guards.py
  - backend/core/uploads.py
  - backend/instructor/__init__.py
  - backend/instructor/dashboard.py
  - backend/instructor/instructor_availability.py
  - backend/instructor/instructor_cars.py
  - backend/instructor/instructor_documents.py
  - backend/instructor/instructor_summary.py
  - backend/instructor/instructors.py
  - backend/policy/__init__.py
  - backend/policy/policy.py
  - backend/student/__init__.py
  - backend/student/booking.py
  - backend/student/reviews.py
  - backend/student/student_marketplace.py
  - backend/student/student_requests.py
  - code-reviews/add-code-domain-folders/review-001-1.1-1.2-1.3-1.4-2.1-2.2-2.3-2.4-3.1-3.2-3.3-3.4.md
  - code-reviews/add-code-domain-folders/review-mapping.json
  - decisions/2026-11-08-sprint13-go.md
  - frontend/admin-dashboard.html
  - frontend/admin-login.html
  - frontend/cabinet.html
  - frontend/instructor-cabinet-stub.html
  - frontend/instructor-choice.html
  - frontend/instructor-dashboard.html
  - frontend/js/admin/admin-dashboard.js
  - frontend/js/admin/admin-login.js
  - frontend/js/instructor/dashboard-instructor.js
  - frontend/js/instructor/instructor-cabinet-stub.js
  - frontend/js/instructors.js
  - frontend/js/shared/api.js
  - frontend/js/shared/utils.js
  - frontend/js/student/cabinet.js
  - frontend/js/student/instructor-choice.js
  - openspec/changes/add-code-domain-folders/design.md
  - openspec/changes/add-code-domain-folders/proposal.md
  - openspec/changes/add-code-domain-folders/specs/codebase-structure/spec.md
  - openspec/changes/add-code-domain-folders/tasks.md
  - test-model/approved/add-code-domain-folders/TC-S13-001.md
  - test-model/approved/add-code-domain-folders/TC-S13-002.md
  - … и еще 27
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
456 passed, 1 warning in 570.20s (0:09:30)
```
