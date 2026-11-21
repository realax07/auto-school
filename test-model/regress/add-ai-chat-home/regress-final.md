# Regress add-ai-chat-home — regress-final.md

- change: add-ai-chat-home
- date: 2026-11-21T22:21:20+00:00
- commit: 258434dde7af82be6f3ab6b6c918d8aad9b7334c
- worktree: /home/hermes-bot/auto-school
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 823.3s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 8
- changed files: 8
  - .gitignore
  - backend/ai/provider.py
  - code-reviews/add-ai-chat-home/review-19.6-001.md
  - docker-compose.yml
  - openspec/changes/add-ai-chat-home/tasks.md
  - scripts/ai_bridge.py
  - test-model/regress/add-ai-chat-home/regress-final.md
  - tests/api/test_s19_ai_chat.py
- suites: tests
- pytest exit code: 0

## Хвост лога (до 50 строк)

```
........................................................................ [ 11%]
........................................................................ [ 23%]
........................................................................ [ 34%]
........................................................................ [ 46%]
........................................................................ [ 58%]
........................................................................ [ 69%]
........................................................................ [ 81%]
........................................................................ [ 93%]
...........................................                              [100%]
619 passed in 820.61s (0:13:40)
```
