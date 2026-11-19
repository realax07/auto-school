# Regress add-ai-chat-home — regress-final.md

- change: add-ai-chat-home
- date: 2026-11-19T19:35:49+00:00
- commit: c93c537f113650a8306575af9dfc9b49911198b5
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-s19-ai-chat
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 741.1s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 72
- changed files: 72
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
  - code-reviews/add-ai-chat-home/review-19.3.5-001.md.provenance.json
  - code-reviews/add-ai-chat-home/review-19.4-001.md
  - code-reviews/add-ai-chat-home/review-19.4-001.md.provenance.json
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
  - test-model/approved/add-ai-chat-home/TC-S19-API-001.md
  - test-model/approved/add-ai-chat-home/TC-S19-MAN-001.md
  - test-model/approved/add-ai-chat-home/TC-S19-REG-001.md
  - test-model/approved/add-ai-chat-home/TC-S19-UNIT-001.md
  - test-model/approved/add-ai-chat-home/TC-S19-WEB-001.md
  - … и еще 22
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
=============================== warnings summary ===============================
tests/api/test_s9_backend.py::test_tc_s9be_007_parallel_exchanges_exactly_one_200
  /home/hermes-bot/.hermes/installs/bc3c7f3f7c048e26/environments/4b83f5f31e1241558bbf5d735879fde0/venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2274: UnsupportedFieldAttributeWarning: The 'alias' attribute with value 'X-Session-Token' was provided to the `Field()` function, which has no effect in the context it was used. 'alias' is field-specific metadata, and can only be attached to a model field using `Annotated` metadata or by assignment. This may have happened because an `Annotated` type alias using the `type` statement was used, or if the `Field()` function was attached to a single member of a union type.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
614 passed, 1 warning in 739.25s (0:12:19)
```
