# Regress add-instructor-mobile — regress-final.md

- change: add-instructor-mobile
- date: 2026-11-19T20:53:49+00:00
- commit: 5c85017daad2ef329b30f9ad08a52daec19ef3c5
- worktree: /home/hermes-bot/.hermes/cache/scratch/wt-instructor-mobile
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 702.5s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 10
- changed files: 10
  - frontend/vue/src/components/InstructorTabBar.vue
  - frontend/vue/src/pages/instructor-dashboard/App.vue
  - frontend/vue/src/pages/instructor-dashboard/styles.css
  - openspec/changes/add-instructor-mobile/design.md
  - openspec/changes/add-instructor-mobile/impact.md
  - openspec/changes/add-instructor-mobile/proposal.md
  - openspec/changes/add-instructor-mobile/specs/instructor-mobile/spec.md
  - openspec/changes/add-instructor-mobile/tasks.md
  - tests/web/test_instructor_tabbar.py
  - tests/web/test_ui_playwright.py
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
586 passed, 1 warning in 700.39s (0:11:40)
```
