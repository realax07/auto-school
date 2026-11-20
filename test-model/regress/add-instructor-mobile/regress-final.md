# Regress add-instructor-mobile — regress-final.md

- change: add-instructor-mobile
- date: 2026-11-19T21:28:27+00:00
- commit: 30805132ff14b7571915e16bafb19f49064f26c2
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-instructor-mobile
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 657.1s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 17
- changed files: 17
  - frontend/vue/src/components/InstructorTabBar.vue
  - frontend/vue/src/pages/instructor-dashboard/App.vue
  - frontend/vue/src/pages/instructor-dashboard/styles.css
  - openspec/changes/add-instructor-mobile/design.md
  - openspec/changes/add-instructor-mobile/impact.md
  - openspec/changes/add-instructor-mobile/proposal.md
  - openspec/changes/add-instructor-mobile/specs/instructor-mobile/spec.md
  - openspec/changes/add-instructor-mobile/tasks.md
  - test-model/approved/add-instructor-mobile/TC-S20-001.md
  - test-model/approved/add-instructor-mobile/TC-S20-002.md
  - test-model/approved/add-instructor-mobile/TC-S20-003.md
  - test-model/approved/add-instructor-mobile/TC-S20-004.md
  - test-model/approved/add-instructor-mobile/coverage.md
  - test-model/regress/add-instructor-mobile/regress-final.md
  - test-model/reviews/add-instructor-mobile/review-001-cases.md
  - tests/web/test_instructor_tabbar.py
  - tests/web/test_ui_playwright.py
- suites: tests
- pytest exit code: 0

## Хвост лога (до 50 строк)

```
........................................................................ [ 12%]
........................................................................ [ 24%]
........................................................................ [ 36%]
........................................................................ [ 49%]
........................................................................ [ 61%]
........................................................................ [ 73%]
........................................................................ [ 86%]
........................................................................ [ 98%]
..........                                                               [100%]
586 passed in 655.56s (0:10:55)
```
