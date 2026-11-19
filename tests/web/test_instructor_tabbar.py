"""Носители мобильного таб-бара инструктора (change add-instructor-mobile,
задача 20.4.1; мокапы design/mocks/mobile-instructor/mi-*.html).

Трассировка: TC-S20-001 (таб-бар ≤760px, top-bar инициалы), TC-S20-002
(«Ещё» bottom-sheet: разделы + Выход), TC-S20-003 (навигация Неделя).
"""
import re

import pytest
from playwright.sync_api import expect

# Фикстуры page/server — из носителя test_ui_playwright (прецедент С18:
# общие фикстуры уровня файла; изоляция sessionStorage на тест).
from test_ui_playwright import browser, page, server  # noqa: F401

INSTRUCTOR_TABS = ["День", "Неделя", "Кошелёк", "Профиль", "Ещё"]


def _login(page, server):
    # registration+approve потока инструктора — через API (create_instructor
    # логика: apply → admin approve → login; специфично для e2e — см. С16 16.4)
    import urllib.request
    base = str(server)
    def req(path, body=None, token=None, hdr=None):
        r = urllib.request.Request(base + path, data=(_json.dumps(body).encode("utf-8") if body is not None else None), method=("POST" if body is not None else "GET"))
        r.add_header("Content-Type", "application/json")
        if token: r.add_header("X-Session-Token", token)
        for k, v in (hdr or {}).items(): r.add_header(k, v)
        from urllib.error import HTTPError
        try:
            with urllib.request.urlopen(r, timeout=8) as resp:
                return resp.status, json.loads(resp.read().decode())
        except Exception as e:
            return 0, {}
    import json as _json
    # Учётные данные test-сервера — фикстура server (test_ui_playwright):
    # ui-admin / ui-admin-pass-2026 (ADMIN_PASSWORD_HASH из env сервера)
    st, d = req("/api/admin/login", {"login": "ui-admin", "password": "ui-admin-pass-2026"})
    assert st == 200, d
    ah = {"X-Admin-Token": d["token"]}
    body = {"surname": "Таббаров", "name": "Инструктор", "patronymic": "Тест",
            "phone": "+7 (911) 222-33-77", "email": "itab-e2e@example.com",
            "address": "г. Тест, ул. Полевая, 1", "work_format": "sber",
            "license_number": "9911223344", "license_category": "B",
            "experience_years": 5, "password": "Instr1234",
            "password_confirm": "Instr1234", "consent": True}
    req("/api/instructors/apply", body, hdr=ah)
    st, lst = req("/api/admin/instructor-applications", hdr=ah)
    rows = (lst.get("applications") or []) if isinstance(lst, dict) else []
    app_id = next((r["id"] for r in rows if r.get("email") == "itab-e2e@example.com"), None)
    assert app_id, lst
    st, _ = req(f"/api/admin/instructor-applications/{app_id}/approve", {}, hdr=ah)
    assert st == 200
    st, lg = req("/api/auth/login", {"email": "itab-e2e@example.com", "password": "Instr1234"})
    assert st == 200, lg
    return lg["token"]


def test_s20_instructor_tabbar_and_more_sheet(page, server):
    """TC-S20-001/TC-S20-002: на 390×844 таб-бар с 5 позициями; «Ещё»
    открывает bottom-sheet (Календарь/Ученики/Автомобили/Материалы/Выход);
    топ-бар показывает инициалы инструктора; десктопный сайдбар скрыт."""
    import json as _json
    import urllib.request
    base = str(server)
    def req(path, body=None, token=None, hdr=None):
        r = urllib.request.Request(base + path, data=(_json.dumps(body).encode("utf-8") if body is not None else None), method=("POST" if body is not None else "GET"))
        r.add_header("Content-Type", "application/json")
        if token: r.add_header("X-Session-Token", token)
        for k, v in (hdr or {}).items(): r.add_header(k, v)
        from urllib.error import HTTPError
        try:
            with urllib.request.urlopen(r, timeout=8) as resp:
                return resp.status, _json.loads(resp.read().decode())
        except HTTPError as e:
            raise AssertionError(f"API {path} → {e.code}: {e.read().decode()[:160]}") from e
    # Учётные данные test-сервера — фикстура server (test_ui_playwright):
    # ui-admin / ui-admin-pass-2026 (ADMIN_PASSWORD_HASH из env сервера)
    st, d = req("/api/admin/login", {"login": "ui-admin", "password": "ui-admin-pass-2026"})
    ah = {"X-Admin-Token": d["token"]}
    body = {"surname": "Таббаров", "name": "Инструктор", "patronymic": "Тест",
            "phone": "+7 (911) 222-33-88", "email": "itab-sheet@example.com",
            "address": "г. Тест, ул. Полевая, 1", "work_format": "sber",
            "license_number": "9911223345", "license_category": "B",
            "experience_years": 5, "password": "Instr1234",
            "password_confirm": "Instr1234", "consent": True}
    req("/api/instructors/apply", body, hdr=ah)
    st, lst = req("/api/admin/instructor-applications", hdr=ah)
    rows = (lst.get("applications") or []) if isinstance(lst, dict) else []
    app_id = next((r["id"] for r in rows if r.get("email") == "itab-sheet@example.com"), None)
    req(f"/api/admin/instructor-applications/{app_id}/approve", {}, hdr=ah)
    st, lg = req("/api/auth/login", {"email": "itab-sheet@example.com", "password": "Instr1234"})
    tok = lg["token"]

    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{server}/instructor/dashboard")
    page.evaluate(f"sessionStorage.setItem('session_token', '{tok}')")
    page.goto(f"{server}/instructor/dashboard")
    page.wait_for_timeout(2200)

    expect(page.locator(".itabs")).to_be_visible()
    expect(page.locator(".itabs .itab")).to_have_count(5)
    labels = [t.strip() for t in page.locator(".itabs .itab span").all_text_contents()]
    assert labels == INSTRUCTOR_TABS, labels
    expect(page.locator(".sidebar")).not_to_be_visible()  # скрыт CSS ≤760px, но в DOM
    expect(page.locator(".itop-ava")).to_be_visible()

    page.locator(".itabs .itab").nth(4).click()
    expect(page.locator(".isheet")).to_be_visible()
    expect(page.locator(".isheet .irow")).to_have_count(5)
    page.locator(".isheet .irow").first.click()  # Календарь
    expect(page.locator(".isheet")).to_have_count(0)


def test_s20_instructor_navigation_week(page, server):
    """TC-S20-003: таб «Неделя» открывает «Расписание» (crumb), контент
    без горизонтального переполнения (scrollWidth ≤390)."""
    import json as _json
    import urllib.request
    base = str(server)
    def req(path, body=None, token=None, hdr=None):
        r = urllib.request.Request(base + path, data=(_json.dumps(body).encode("utf-8") if body is not None else None), method=("POST" if body is not None else "GET"))
        r.add_header("Content-Type", "application/json")
        if token: r.add_header("X-Session-Token", token)
        for k, v in (hdr or {}).items(): r.add_header(k, v)
        from urllib.error import HTTPError
        try:
            with urllib.request.urlopen(r, timeout=8) as resp:
                return resp.status, _json.loads(resp.read().decode())
        except HTTPError as e:
            raise AssertionError(f"API {path} → {e.code}: {e.read().decode()[:160]}") from e
    # Учётные данные test-сервера — фикстура server (test_ui_playwright):
    # ui-admin / ui-admin-pass-2026 (ADMIN_PASSWORD_HASH из env сервера)
    st, d = req("/api/admin/login", {"login": "ui-admin", "password": "ui-admin-pass-2026"})
    ah = {"X-Admin-Token": d["token"]}
    body = {"surname": "Таббаров", "name": "Инструктор", "patronymic": "Тест",
            "phone": "+7 (911) 222-33-99", "email": "itab-week@example.com",
            "address": "г. Тест, ул. Полевая, 1", "work_format": "sber",
            "license_number": "9911223346", "license_category": "B",
            "experience_years": 5, "password": "Instr1234",
            "password_confirm": "Instr1234", "consent": True}
    req("/api/instructors/apply", body, hdr=ah)
    st, lst = req("/api/admin/instructor-applications", hdr=ah)
    rows = (lst.get("applications") or []) if isinstance(lst, dict) else []
    app_id = next((r["id"] for r in rows if r.get("email") == "itab-week@example.com"), None)
    req(f"/api/admin/instructor-applications/{app_id}/approve", {}, hdr=ah)
    st, lg = req("/api/auth/login", {"email": "itab-week@example.com", "password": "Instr1234"})
    tok = lg["token"]

    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{server}/instructor/dashboard")
    page.evaluate(f"sessionStorage.setItem('session_token', '{tok}')")
    page.goto(f"{server}/instructor/dashboard")
    page.wait_for_timeout(2200)
    page.locator(".itabs .itab").nth(1).click()
    page.wait_for_timeout(700)
    crumb = page.evaluate("document.getElementById('crumb') ? document.getElementById('crumb').textContent : ''")
    assert crumb == "Расписание", crumb
    sw = page.evaluate("document.documentElement.scrollWidth")
    assert sw <= 390, f"scrollWidth={sw}"

def test_s20_instructor_geometry(page, server):
    """TC-S20-004 (задача 20.4.2): геометрия кабинета инструктора на
    390×844 — scrollWidth ≤390, контент-паддинг верха 20–30px (отступ
    логотипа, спека С18), hit-targets таб-бара ≥44px,desktop-инвариант:
    1440×900 — сайдбар видим, таб-бар скрыт (регресс BUG-070-класса)."""
    import json as _json
    import urllib.request
    base = str(server)
    def req(path, body=None, token=None, hdr=None):
        r = urllib.request.Request(base + path, data=(_json.dumps(body).encode("utf-8") if body is not None else None), method=("POST" if body is not None else "GET"))
        r.add_header("Content-Type", "application/json")
        if token: r.add_header("X-Session-Token", token)
        for k, v in (hdr or {}).items(): r.add_header(k, v)
        from urllib.error import HTTPError
        try:
            with urllib.request.urlopen(r, timeout=8) as resp:
                return resp.status, _json.loads(resp.read().decode())
        except HTTPError as e:
            raise AssertionError(f"API {path} → {e.code}") from e
    st, d = req("/api/admin/login", {"login": "ui-admin", "password": "ui-admin-pass-2026"})
    ah = {"X-Admin-Token": d["token"]}
    body = {"surname": "Гео", "name": "Метров", "patronymic": "Тест",
            "phone": "+7 (911) 222-34-00", "email": "itab-geo@example.com",
            "address": "г. Тест, ул. Полевая, 1", "work_format": "sber",
            "license_number": "9911223347", "license_category": "B",
            "experience_years": 5, "password": "Instr1234",
            "password_confirm": "Instr1234", "consent": True}
    req("/api/instructors/apply", body, hdr=ah)
    st, lst = req("/api/admin/instructor-applications", hdr=ah)
    rows = (lst.get("applications") or []) if isinstance(lst, dict) else []
    app_id = next((r["id"] for r in rows if r.get("email") == "itab-geo@example.com"), None)
    req(f"/api/admin/instructor-applications/{app_id}/approve", {}, hdr=ah)
    st, lg = req("/api/auth/login", {"email": "itab-geo@example.com", "password": "Instr1234"})
    tok = lg["token"]

    # --- мобильный 390×844 ---
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{server}/instructor/dashboard")
    page.evaluate(f"sessionStorage.setItem('session_token', '{tok}')")
    page.goto(f"{server}/instructor/dashboard")
    page.wait_for_timeout(2200)
    sw = page.evaluate("document.documentElement.scrollWidth")
    assert sw <= 390, f"scrollWidth={sw} — горизонтальное переполнение"
    pad = page.evaluate("Math.round(parseFloat(getComputedStyle(document.querySelector('main')).paddingTop))")
    assert 20 <= pad <= 30, f"content top pad={pad} (спека: ~26px отступ логотипа)"
    hit = page.evaluate("""(() => {
      const bad = [];
      document.querySelectorAll('.itabs .itab').forEach(el => {
        const h = el.getBoundingClientRect().height;
        if (h < 44) bad.push(el.textContent.trim() + '@' + Math.round(h));
      });
      return bad;
    })()""")
    assert not hit, f"табы <44px: {hit}"

    # --- desktop 1440×900: сайдбар видим, таб-бар/топ-бар скрыты ---
    page.set_viewport_size({"width": 1440, "height": 900})
    page.wait_for_timeout(600)
    st2 = page.evaluate("""(() => {
      const vis = s => { const e = document.querySelector(s); return e ? getComputedStyle(e).display !== 'none' : null; };
      return { sidebar: vis('.sidebar'), tabs: vis('.itabs'), top: vis('.itop') };
    })()""")
    assert st2["sidebar"] is True, st2
    assert st2["tabs"] is not True and st2["top"] is not True, st2  # v-if: элементы отсутствуют на desktop
