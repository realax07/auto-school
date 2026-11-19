# Regress add-ai-chat-home — regress-final.md

- change: add-ai-chat-home
- date: 2026-11-19T19:09:51+00:00
- commit: 712e2c1ca7d3b4070b1949af1218e6eb0aa78465
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s19-ai-chat
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 791.9s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 66
- changed files: 66
  - PLAN-add-ai-chat-home.md
  - PLAN.md
  - architecture/map.md
  - backend/ai/__init__.py
  - backend/ai/provider.py
  - backend/ai/routes.py
  - backend/app.py
  - backend/core/db.py
  - code-reviews/add-ai-chat-home/review-19.2-001.md
  - code-reviews/add-ai-chat-home/review-19.2-002.md
  - code-reviews/add-ai-chat-home/review-19.2-003.md
  - code-reviews/add-ai-chat-home/review-19.2-003.md.provenance.json
  - code-reviews/add-ai-chat-home/review-19.2-004.md
  - code-reviews/add-ai-chat-home/review-19.2-005.md
  - code-reviews/add-ai-chat-home/review-19.2-005.md.provenance.json
  - code-reviews/add-ai-chat-home/review-19.2.1-005.md
  - code-reviews/add-ai-chat-home/review-19.2.2-005.md
  - code-reviews/add-ai-chat-home/review-19.2.3-005.md
  - code-reviews/add-ai-chat-home/review-19.2.4-005.md
  - code-reviews/add-ai-chat-home/review-19.3-001.md
  - code-reviews/add-ai-chat-home/review-19.3-001.md.provenance.json
  - code-reviews/add-ai-chat-home/review-19.3-002.md
  - code-reviews/add-ai-chat-home/review-19.3-002.md.provenance.json
  - code-reviews/add-ai-chat-home/review-19.3.1-002.md
  - code-reviews/add-ai-chat-home/review-19.3.2-002.md
  - code-reviews/add-ai-chat-home/review-19.3.3-002.md
  - code-reviews/add-ai-chat-home/review-19.3.5-001.md
  - design/mocks/home-chat-web.html
  - design/mocks/mobile/mobile-home-chat.html
  - frontend/vue/cabinet.html
  - frontend/vue/src/pages/cabinet/App.vue
  - frontend/vue/src/pages/cabinet/styles.css
  - glossary.md
  - openspec/changes/add-ai-chat-home/design.md
  - openspec/changes/add-ai-chat-home/proposal.md
  - openspec/changes/add-ai-chat-home/research.md
  - openspec/changes/add-ai-chat-home/specs/ai-chat/spec.md
  - openspec/changes/add-ai-chat-home/specs/cabinet/spec.md
  - openspec/changes/add-ai-chat-home/tasks.md
  - sdd.md
  - test-model/approved/add-ai-chat-home/TC-S19-API-001.md
  - test-model/approved/add-ai-chat-home/TC-S19-MAN-001.md
  - test-model/approved/add-ai-chat-home/TC-S19-REG-001.md
  - test-model/approved/add-ai-chat-home/TC-S19-UNIT-001.md
  - test-model/approved/add-ai-chat-home/TC-S19-WEB-001.md
  - test-model/approved/add-ai-chat-home/TC-S19-WEB-002.md
  - test-model/approved/add-ai-chat-home/TC-S19-WEB-003.md
  - test-model/approved/add-ai-chat-home/TC-S19-WEB-004.md
  - test-model/approved/add-ai-chat-home/TC-S19-WEB-005.md
  - test-model/approved/add-ai-chat-home/checklist.md
  - … и еще 16
- suites: tests
- pytest exit code: 0

## Хвост лога (до 50 строк)

```
........................................................................ [ 11%]
........................................................................ [ 23%]
........................................................................ [ 35%]
........................................................................ [ 46%]
........................................................................ [ 58%]
........................................................................ [ 70%]
........................................................................ [ 82%]
........................................................................ [ 93%]
......................................                                   [100%]
614 passed in 789.38s (0:13:09)
```
