# Regress add-mobile-adaptive — regress-final.md

- change: add-mobile-adaptive
- date: 2026-11-18T00:13:11+00:00
- commit: 86d530cb52c9682788de44f2ff6251e354ba1560
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s18-mobile
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 637.8s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 61
- changed files: 61
  - architecture/map.md
  - code-reviews/add-mobile-adaptive/review-001-consolidated-18.1-18.4.md
  - code-reviews/add-mobile-adaptive/review-002-consolidated-18.1-18.4.md
  - code-reviews/add-mobile-adaptive/review-003-consolidated-18.1-18.4.md
  - code-reviews/add-mobile-adaptive/review-mapping.json
  - design/mocks/mobile/mobile-admin.html
  - design/mocks/mobile/mobile-book-slot.html
  - design/mocks/mobile/mobile-bookings.html
  - design/mocks/mobile/mobile-choice.html
  - design/mocks/mobile/mobile-dispute.html
  - design/mocks/mobile/mobile-home.html
  - design/mocks/mobile/mobile-instructor.html
  - design/mocks/mobile/mobile-landing.html
  - design/mocks/mobile/mobile-login.html
  - design/mocks/mobile/mobile-pdd-fines.html
  - design/mocks/mobile/mobile-pdd-rules.html
  - design/mocks/mobile/mobile-pdd-sign-detail.html
  - design/mocks/mobile/mobile-pdd-signs.html
  - design/mocks/mobile/mobile-pdd-tickets.html
  - design/mocks/mobile/mobile-policy.html
  - design/mocks/mobile/mobile-register.html
  - design/mocks/mobile/mobile-registered.html
  - design/mocks/mobile/mobile-rejected.html
  - design/mocks/mobile/mobile-requests.html
  - design/mocks/mobile/mobile-review.html
  - design/mocks/mobile/mobile-wallet.html
  - frontend/vue/src/components/MobileTabBar.vue
  - frontend/vue/src/components/StudentSidebar.vue
  - frontend/vue/src/pages/admin-dashboard/styles.css
  - frontend/vue/src/pages/cabinet/App.vue
  - frontend/vue/src/pages/cabinet/styles.css
  - frontend/vue/src/pages/documents/styles.css
  - frontend/vue/src/pages/instructor-choice/App.vue
  - frontend/vue/src/pages/instructor-choice/styles.css
  - frontend/vue/src/pages/instructor-dashboard/styles.css
  - frontend/vue/src/pages/instructors/styles.css
  - frontend/vue/src/pages/landing/styles.css
  - openspec/changes/add-mobile-adaptive/design.md
  - openspec/changes/add-mobile-adaptive/proposal.md
  - openspec/changes/add-mobile-adaptive/specs/mobile-adaptive/spec.md
  - openspec/changes/add-mobile-adaptive/tasks.md
  - test-model/approved/add-mobile-adaptive/TC-S18-001.md
  - test-model/approved/add-mobile-adaptive/TC-S18-002.md
  - test-model/approved/add-mobile-adaptive/TC-S18-003.md
  - test-model/approved/add-mobile-adaptive/TC-S18-004.md
  - test-model/approved/add-mobile-adaptive/TC-S18-005.md
  - test-model/approved/add-mobile-adaptive/TC-S18-006.md
  - test-model/approved/add-mobile-adaptive/TC-S18-007.md
  - test-model/approved/add-mobile-adaptive/TC-S18-008.md
  - test-model/approved/add-mobile-adaptive/coverage.md
  - … и еще 11
- suites: tests
- pytest exit code: 0

## Хвост лога (до 50 строк)

```
........................................................................ [ 12%]
........................................................................ [ 24%]
........................................................................ [ 37%]
........................................................................ [ 49%]
........................................................................ [ 61%]
........................................................................ [ 74%]
........................................................................ [ 86%]
........................................................................ [ 98%]
.......                                                                  [100%]
583 passed in 636.51s (0:10:36)
```
