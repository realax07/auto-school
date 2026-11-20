# Regress add-instructor-mobile — regress-final.md

- change: add-instructor-mobile
- date: 2026-11-20T09:37:39+00:00
- commit: df6fb7138ddbdfbe385e7a145bb7df8a0cb1aeb6
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-inst-trim
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 737.1s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 4
- changed files: 4
  - frontend/vue/src/components/InstructorTabBar.vue
  - frontend/vue/src/pages/instructor-dashboard/App.vue
  - frontend/vue/src/pages/instructor-dashboard/styles.css
  - tests/web/test_instructor_tabbar.py
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
=============================== warnings summary ===============================
tests/api/test_s9_backend.py::test_tc_s9be_007_parallel_exchanges_exactly_one_200
  /home/hermes-bot/.hermes/installs/bc3c7f3f7c048e26/environments/4b83f5f31e1241558bbf5d735879fde0/venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2274: UnsupportedFieldAttributeWarning: The 'alias' attribute with value 'filename' was provided to the `Field()` function, which has no effect in the context it was used. 'alias' is field-specific metadata, and can only be attached to a model field using `Annotated` metadata or by assignment. This may have happened because an `Annotated` type alias using the `type` statement was used, or if the `Field()` function was attached to a single member of a union type.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
586 passed, 1 warning in 735.60s (0:12:15)
```
