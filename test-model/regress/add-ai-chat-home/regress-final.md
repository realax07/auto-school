# Regress add-ai-chat-home — regress-final.md

- change: add-ai-chat-home
- date: 2026-11-21T21:49:45+00:00
- commit: f97d6b9e415f52ca753e29dfb0df83fbec2be62b
- worktree: /home/hermes-bot/auto-school
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 842.9s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 5
- changed files: 5
  - .gitignore
  - backend/ai/provider.py
  - openspec/changes/add-ai-chat-home/tasks.md
  - scripts/ai_bridge.py
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
619 passed in 840.68s (0:14:00)
```
