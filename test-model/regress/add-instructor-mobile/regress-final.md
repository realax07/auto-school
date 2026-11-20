# Regress add-instructor-mobile — regress-final.md

- change: add-instructor-mobile
- date: 2026-11-20T09:56:58+00:00
- commit: 6f99f167d10c7ea5283977695b4f663eb545c438
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-inst-trim
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 662.0s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 6
- changed files: 6
  - frontend/vue/src/components/InstructorTabBar.vue
  - frontend/vue/src/pages/instructor-dashboard/App.vue
  - frontend/vue/src/pages/instructor-dashboard/styles.css
  - test-model/regress/add-instructor-mobile/regress-final.md
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
586 passed in 660.45s (0:11:00)
```
