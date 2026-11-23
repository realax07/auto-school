# Regress add-roles-theme-landing — regress-final.md

- change: add-roles-theme-landing
- date: 2026-11-23T13:16:02+00:00
- commit: fd68b434e5df1a3a8b16560f8af08451d50671d1
- worktree: /home/hermes-bot/auto-school
- verdict: FAIL
- tier: domain (эшелон 1: доменный regress)
- duration: 842.0s
- diff source: git diff main...HEAD
- domain map: project map test-model/regress-domains.json задана, правил нет — применен дефолт
- changed files: 21
- changed files: 21
  - architecture/map.md
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
  - openspec/changes/add-roles-theme-landing/proposal.md
  - openspec/changes/add-roles-theme-landing/specs/landing-assistant/spec.md
  - openspec/changes/add-roles-theme-landing/specs/registration/spec.md
  - openspec/changes/add-roles-theme-landing/specs/theme/spec.md
  - openspec/changes/add-roles-theme-landing/tasks.md
  - test-model/impact/add-roles-theme-landing.md
  - tests/web/test_ui_playwright.py
- suites: tests
- pytest exit code: 1

## Хвост лога (до 50 строк)

```
        stu_email = unique_email("cabstu")
        status, data = api("POST", "/api/register", base=server, body={
            "surname": "Петров", "name": "Пётр", "patronymic": "Петрович",
            "email": stu_email, "phone": "+7 905 777-66-55",
            "password": "S3cretPass!", "password_confirm": "S3cretPass!",
            "consent": True,
        })
        assert status == 200 and data and data["ok"], (status, data)
        page.goto(f"{server}/")
        page.locator('.auth [data-open="login"]').click()
        page.fill("#login-email", stu_email)
        page.fill("#login-password", "S3cretPass!")
        page.locator("#login-submit").click()
        page.wait_for_url("**/cabinet")
    
        # главная кабинета: сайдбарный логотип есть, дубля в шапке нет
        expect(page.locator(".side-brand")).to_be_visible()
        assert page.locator("header .brand").count() == 0
        assert page.get_by_text("Личный кабинет · Ученик").count() == 0
        # «Выйти» на месте — в САЙДБАРЕ снизу (замечание Заказчика 2026-11-15 №4:
        # учётка перенесена из шапки в нижний левый угол сайдбара)
        expect(page.locator(".side-user .logout")).to_be_visible()
    
        # подстраница «Выбор инструктора»: те же инварианты + крошка убрана
        page.goto(f"{server}/instructor-choice")
        expect(page.locator(".side-brand")).to_be_visible()
        assert page.locator("header .brand").count() == 0
        assert page.get_by_text("Кабинет ученика · Выбор инструктора").count() == 0
        # учётка — в САЙДБАРЕ снизу (замечание №4), прижата к нижнему краю
        # сайдбара (margin-top:auto); BUG-061/BUG-062 (шапка) не применимы —
        # шапки на подстранице больше нет
        box = page.locator(".side-user").bounding_box()
        side = page.locator(".side").bounding_box()
        bottom_gap = side["y"] + side["height"] - (box["y"] + box["height"])
>       assert bottom_gap < 40, f"учётка не у нижнего края сайдбара (зазор {bottom_gap}px)"
E       AssertionError: учётка не у нижнего края сайдбара (зазор 101px)
E       assert 101 < 40

tests/web/test_ui_playwright.py:4779: AssertionError
=============================== warnings summary ===============================
tests/api/test_s9_backend.py::test_tc_s9be_007_parallel_exchanges_exactly_one_200
  /home/hermes-bot/.hermes/installs/bc3c7f3f7c048e26/environments/4b83f5f31e1241558bbf5d735879fde0/venv/lib/python3.14/site-packages/pydantic/_internal/_generate_schema.py:2274: UnsupportedFieldAttributeWarning: The 'alias' attribute with value 'status' was provided to the `Field()` function, which has no effect in the context it was used. 'alias' is field-specific metadata, and can only be attached to a model field using `Annotated` metadata or by assignment. This may have happened because an `Annotated` type alias using the `type` statement was used, or if the `Field()` function was attached to a single member of a union type.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/web/test_login_modal.py::test_tc_auth_login_modal_texts_verbatim
FAILED tests/web/test_login_modal.py::test_tc_auth_login_modal_no_stub_submit
FAILED tests/web/test_ui_playwright.py::test_tc_ui_059_student_cabinet_single_logo_no_crumbs
3 failed, 628 passed, 1 warning in 840.33s (0:14:00)
```
