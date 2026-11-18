# Regress add-mobile-adaptive — regress-final.md

- change: add-mobile-adaptive
- date: 2026-11-18T10:04:05+00:00
- commit: 933efeea6d43a11a35a6a7bf5efb639f0d3c0ac5
- worktree: /home/hermes-bot/auto-school
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 698.0s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 5
- changed files: 5
  - frontend/vue/index.html
  - frontend/vue/src/pages/landing/App.vue
  - frontend/vue/src/pages/landing/styles.css
  - test-model/regress/add-mobile-adaptive/regress-final.md
  - tests/web/test_ui_playwright.py
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
=============================== warnings summary ===============================
tests/api/test_s9_backend.py::test_tc_s9be_007_parallel_exchanges_exactly_one_200
  /home/hermes-bot/.hermes/installs/bc3c7f3f7c048e26/environments/4b83f5f31e1241558bbf5d735879fde0/venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2274: UnsupportedFieldAttributeWarning: The 'alias' attribute with value 'filename' was provided to the `Field()` function, which has no effect in the context it was used. 'alias' is field-specific metadata, and can only be attached to a model field using `Annotated` metadata or by assignment. This may have happened because an `Annotated` type alias using the `type` statement was used, or if the `Field()` function was attached to a single member of a union type.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
583 passed, 1 warning in 696.43s (0:11:36)
```
