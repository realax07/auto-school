# Regress add-roles-theme-landing — regress-final.md

- change: add-roles-theme-landing
- date: 2026-11-23T15:16:38+00:00
- commit: 36f467b0a6129d40649c4a8ce73658219643058c
- worktree: /home/hermes-bot/auto-school
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 843.3s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 29
- changed files: 29
  - architecture/map.md
  - code-reviews/add-roles-theme-landing/review-21.2.1-21.2.2-21.2.3-21.3.1-21.3.2-21.4.1-21.4.2-001.md
  - code-reviews/add-roles-theme-landing/review-21.2.1-21.2.2-21.2.3-21.3.1-21.3.2-21.4.1-21.4.2-002.md
  - code-reviews/add-roles-theme-landing/review-21.2.1-21.2.2-21.2.3-21.3.1-21.3.2-21.4.1-21.4.2-003.md
  - code-reviews/add-roles-theme-landing/review-21.2.1-21.2.2-21.2.3-21.3.1-21.3.2-21.4.1-21.4.2-004.md
  - design/mocks/mobile/_render/landing-chat.png
  - design/mocks/mobile/_render/theme-toggle.png
  - design/mocks/mobile/landing-chat.html
  - design/mocks/mobile/theme-toggle.html
  - frontend/vue/cabinet.html
  - frontend/vue/index.html
  - frontend/vue/src/components/StudentSidebar.vue
  - frontend/vue/src/pages/cabinet/App.vue
  - frontend/vue/src/pages/cabinet/styles.css
  - frontend/vue/src/pages/landing/App.vue
  - frontend/vue/src/pages/landing/styles.css
  - frontend/vue/src/shared/RegisterModal.vue
  - openspec/changes/add-roles-theme-landing/design.md
  - openspec/changes/add-roles-theme-landing/impact.md
  - openspec/changes/add-roles-theme-landing/proposal.md
  - openspec/changes/add-roles-theme-landing/specs/landing-assistant/spec.md
  - openspec/changes/add-roles-theme-landing/specs/registration/spec.md
  - openspec/changes/add-roles-theme-landing/specs/theme/spec.md
  - openspec/changes/add-roles-theme-landing/tasks.md
  - test-model/impact/add-roles-theme-landing.md
  - test-model/regress/add-roles-theme-landing/regress-final.md
  - tests/web/test_login_modal.py
  - tests/web/test_static.py
  - tests/web/test_ui_playwright.py
- suites: tests
- pytest exit code: 0

## Хвост лога (до 50 строк)

```
........................................................................ [ 11%]
........................................................................ [ 22%]
........................................................................ [ 34%]
........................................................................ [ 45%]
........................................................................ [ 56%]
........................................................................ [ 68%]
........................................................................ [ 79%]
........................................................................ [ 91%]
........................................................                 [100%]
632 passed in 840.85s (0:14:00)
```
