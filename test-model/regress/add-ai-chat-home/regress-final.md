# Regress add-ai-chat-home — regress-final.md

- change: add-ai-chat-home
- date: 2026-11-23T10:05:44+00:00
- commit: 2773b1f0dffcf871fa6d73356abafd75753a27fa
- worktree: /home/hermes-bot/auto-school
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 755.2s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 11
- changed files: 11
  - .gitignore
  - docker-compose.yml
  - openspec/changes/add-ai-chat-home/tasks.md
  - scripts/ai_bridge.py
  - services/ai-bridge/Dockerfile
  - services/ai-bridge/app.py
  - test-model/impact/add-ai-chat-home.md
  - test-model/regress/add-ai-chat-home/regress-final.md
  - tests/api/test_s19_ai_bridge_glm.py
  - tests/api/test_s19_ai_chat.py
  - tests/test_container_contract.py
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
........................................................................ [ 92%]
............................................                             [100%]
=============================== warnings summary ===============================
tests/api/test_s9_backend.py::test_tc_s9be_007_parallel_exchanges_exactly_one_200
  /home/hermes-bot/.hermes/installs/bc3c7f3f7c048e26/environments/4b83f5f31e1241558bbf5d735879fde0/venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2274: UnsupportedFieldAttributeWarning: The 'alias' attribute with value 'filename' was provided to the `Field()` function, which has no effect in the context it was used. 'alias' is field-specific metadata, and can only be attached to a model field using `Annotated` metadata or by assignment. This may have happened because an `Annotated` type alias using the `type` statement was used, or if the `Field()` function was attached to a single member of a union type.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
620 passed, 1 warning in 753.39s (0:12:33)
```
