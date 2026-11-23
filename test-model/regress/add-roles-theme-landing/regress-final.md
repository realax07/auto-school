# Regress add-roles-theme-landing — regress-final.md

- change: add-roles-theme-landing
- date: 2026-11-23T15:32:04+00:00
- commit: 2cfb5dbe3c54863eef82a77e0584aca1f8ae87a4
- worktree: /home/hermes-bot/auto-school
- verdict: PASS
- tier: domain (эшелон 1: доменный regress)
- duration: 828.7s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 31
- changed files: 31
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
  - test-model/approved/add-roles-theme-landing/review-001-cases.md
  - test-model/impact/add-roles-theme-landing.md
  - test-model/regress/add-roles-theme-landing/regress-final.md
  - test-model/reviews/add-roles-theme-landing/review-001-cases.md
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
=============================== warnings summary ===============================
tests/api/test_s9_backend.py::test_tc_s9be_007_parallel_exchanges_exactly_one_200
  /home/hermes-bot/.hermes/installs/bc3c7f3f7c048e26/environments/4b83f5f31e1241558bbf5d735879fde0/venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2274: UnsupportedFieldAttributeWarning: The 'alias' attribute with value 'filename' was provided to the `Field()` function, which has no effect in the context it was used. 'alias' is field-specific metadata, and can only be attached to a model field using `Annotated` metadata or by assignment. This may have happened because an `Annotated` type alias using the `type` statement was used, or if the `Field()` function was attached to a single member of a union type.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
632 passed, 1 warning in 826.70s (0:13:46)
```
