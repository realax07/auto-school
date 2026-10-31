# Regress add-car-validation-booking — regress-final.md

- change: add-car-validation-booking
- date: 2026-10-31T09:14:48+00:00
- commit: 3ccd71b5c68ca0131f001f7dbd781b8831b87597
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s7-front
- verdict: FAIL
- tier: domain (эшелон 1: доменный regress)
- duration: 462.8s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 48
- changed files: 48
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
  - test-model/reviews/add-car-validation-booking/review-002-design.md
  - test-model/reviews/add-car-validation-booking/review-acceptance.md
  - test-model/reviews/add-car-validation-booking/shots/front-admin-cars-modal.png
  - test-model/reviews/add-car-validation-booking/shots/front-admin-cars.png
  - test-model/reviews/add-car-validation-booking/shots/front-booking-student-validating.png
  - test-model/reviews/add-car-validation-booking/shots/front-booking-student.png
  - test-model/reviews/add-car-validation-booking/shots/front-my-cars-modal.png
  - test-model/reviews/add-car-validation-booking/shots/front-my-cars.png
  - test-model/reviews/add-car-validation-booking/shots/front-my-documents.png
  - test-model/reviews/add-car-validation-booking/shots/mock-admin-cars.png
  - test-model/reviews/add-car-validation-booking/shots/mock-booking-student-cars.png
  - test-model/reviews/add-car-validation-booking/shots/mock-my-cars-s7.png
  - test-model/reviews/add-car-validation-booking/shots/mock-my-documents.png
  - tests/test_s3_backend.py
  - tests/test_s5_backend.py
  - tests/test_s7_backend.py
  - tests/test_ui_playwright.py
- suites: tests
- pytest exit code: 1

## Хвост лога (до 50 строк)

```
........................................................................ [ 21%]
........................................................................ [ 42%]
...............................F........................................ [ 63%]
........................................................................ [ 84%]
....................................................                     [100%]
=================================== FAILURES ===================================
____________________ test_nfr001_login_latency_under_500ms _____________________

client = <starlette.testclient.TestClient object at 0x71c442669480>
no_bf = None

    def test_nfr001_login_latency_under_500ms(client, no_bf):
        """TC-NFR-001: 5 прогонов POST /api/auth/login с корректными данными;
        время каждого прогона ≤ 500 мс (NFR-1, бюджет с bcrypt cost 12).
        Замер time.perf_counter вокруг HTTP-вызова TestClient (полный стек
        запроса; сетевой слой исключен по предусловию кейса «допускается
        TestClient без сети»)."""
        _register_one(client)
    
        durations_ms = []
        for _ in range(5):
            start = _time.perf_counter()
            resp = _login(client)
            elapsed_ms = (_time.perf_counter() - start) * 1000.0
            assert resp.status_code == 200, resp.text
            assert resp.json()["ok"] is True
            durations_ms.append(elapsed_ms)
    
        for i, ms in enumerate(durations_ms, 1):
>           assert ms <= 500.0, f"прогон {i}: {ms:.1f} мс > 500 мс"
E           AssertionError: прогон 2: 510.2 мс > 500 мс
E           assert 510.21510967984796 <= 500.0

tests/test_qa_sprint1.py:86: AssertionError
=============================== warnings summary ===============================
../../../../auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/hermes-bot/auto-school/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/test_qa_sprint1.py::test_nfr001_login_latency_under_500ms - Asse...
1 failed, 339 passed, 1 warning in 460.62s (0:07:40)
```


## Перепрогон флака (2026-10-31, правило 3 прогонов)

Единственный FAIL прогона — test_nfr001_login_latency_under_500ms
(известный флак T-4/INC: бюджет 500мс при bcrypt cost 12, выбросы на
нагруженном хосте). 3 последовательных одиночных прогона: **3 passed**
(4.41/4.76/4.13s). Классификация: environment/нагрузка, не регресс —
решение ПМ, завершение не блокирует.
