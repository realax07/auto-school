# Regress add-ai-chat-home — regress-final.md

- change: add-ai-chat-home
- date: 2026-11-19T20:26:04+00:00
- commit: 15bac52b94b443185444cc99cc20d3183ca1a70f
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s19-ai-chat
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 806.9s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 77
- changed files: 77
  - BACKLOG.md
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
  - code-reviews/add-ai-chat-home/review-19.2.1-19.2.2-19.2.3-19.2.4-006.md
  - code-reviews/add-ai-chat-home/review-19.2.2-005.md
  - code-reviews/add-ai-chat-home/review-19.2.3-005.md
  - code-reviews/add-ai-chat-home/review-19.2.4-005.md
  - code-reviews/add-ai-chat-home/review-19.3-001.md
  - code-reviews/add-ai-chat-home/review-19.3-001.md.provenance.json
  - code-reviews/add-ai-chat-home/review-19.3-002.md
  - code-reviews/add-ai-chat-home/review-19.3-002.md.provenance.json
  - code-reviews/add-ai-chat-home/review-19.3.1-002.md
  - code-reviews/add-ai-chat-home/review-19.3.1-19.3.2-19.3.3-004.md
  - code-reviews/add-ai-chat-home/review-19.3.2-002.md
  - code-reviews/add-ai-chat-home/review-19.3.3-002.md
  - code-reviews/add-ai-chat-home/review-19.3.5-001.md
  - code-reviews/add-ai-chat-home/review-19.3.5-001.md.provenance.json
  - code-reviews/add-ai-chat-home/review-19.4-001.md
  - code-reviews/add-ai-chat-home/review-19.4-001.md.provenance.json
  - code-reviews/add-ai-chat-home/review-19.4-002.md
  - code-reviews/add-ai-chat-home/review-19.4.1-001.md
  - code-reviews/add-ai-chat-home/review-19.4.3-001.md
  - design/mocks/home-chat-web.html
  - design/mocks/mobile/mobile-home-chat.html
  - frontend/vue/cabinet.html
  - frontend/vue/src/pages/cabinet/App.vue
  - frontend/vue/src/pages/cabinet/styles.css
  - glossary.md
  - incidents.md
  - openspec/changes/add-ai-chat-home/design.md
  - openspec/changes/add-ai-chat-home/proposal.md
  - openspec/changes/add-ai-chat-home/research.md
  - openspec/changes/add-ai-chat-home/specs/ai-chat/spec.md
  - openspec/changes/add-ai-chat-home/specs/cabinet/spec.md
  - openspec/changes/add-ai-chat-home/tasks.md
  - sdd.md
  - … и еще 27
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
614 passed in 805.09s (0:13:25)
```
