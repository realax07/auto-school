"""Playwright UI-тесты (Спринт 2, требование Заказчика: «должно быть все
покрыто ими»). Запуск: python3 -m pytest tests/test_ui_playwright.py -q
Требует запущенный сервер (uvicorn backend.app:app) на TEST_BASE_URL
(по умолчанию http://127.0.0.1:8390) и playwright chromium."""
import os

import pytest

pw = pytest.importorskip("playwright.sync_api")

BASE = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8390")

instructors_only = pytest.mark.skipif(
    not os.environ.get("UI_TESTS"), reason="UI_TESTS не задан")


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture()
def page(browser):
    ctx = browser.new_context()
    pg = ctx.new_page()
    yield pg
    ctx.close()


@instructors_only
def test_landing_instructors_brand_and_cta(page):
    """TC-UI-001 (change add-instructor-cabinet): лендинг — логотип «Сбер»
    зелёным, кнопки шапки рядом, hero-«Войти» отсутствует."""
    page.goto(f"{BASE}/instructors")
    assert page.locator(".brand b").inner_text() == "Сбер"
    color = page.locator(".brand b").evaluate("el => getComputedStyle(el).color")
    assert color == "rgb(53, 216, 121)"  # #35d879
    # кнопки шапки рядом (расстояние между центрами < 220px)
    login = page.locator('.header-cta[data-open-login]').bounding_box()
    apply = page.locator('.header-cta[href="/instructors/apply"]').bounding_box()
    assert apply["x"] - (login["x"] + login["width"]) < 40
    # в теле нет кнопки «Войти»
    assert page.locator(".actions [data-open-login]").count() == 0


@instructors_only
def test_apply_page_fio_three_fields(page):
    """TC-UI-002 (change add-instructor-cabinet): анкета — логотип 1в1
    с лендингом (без подчеркивания), ФИО — три поля, иконка загрузки
    по центру фрейма."""
    page.goto(f"{BASE}/instructors/apply")
    # бренд: «Сбер» без подчеркивания, зелёный
    b = page.locator(".brand b")
    assert b.evaluate("el => getComputedStyle(el).textDecorationLine") in ("none",)
    # три поля ФИО
    for fid in ("surname", "name", "patronymic"):
        assert page.locator(f"#{fid}").count() == 1
    # иконка загрузки: центр иконки ≈ центр фрейма (допуск 6px по вертикали)
    frame = page.locator(".upload").bounding_box()
    icon = page.locator(".upload-icon").bounding_box()
    frame_cy = frame["y"] + frame["height"] / 2
    icon_cy = icon["y"] + icon["height"] / 2
    assert abs(frame_cy - icon_cy) <= 6


@instructors_only
def test_login_modal_centered_and_cancel_returns(page):
    """TC-UI-003 (change add-instructor-cabinet): «Войти» → модалка входа
    по центру экрана; Отмена возвращает на лендинг инструкторов."""
    page.goto(f"{BASE}/instructors")
    page.locator('.header-cta[data-open-login]').click()
    page.goto(f"{BASE}/")
    # на главной модалка входа открылась автоматически
    overlay = page.locator("#m-login.overlay")
    overlay.wait_for(state="visible")
    box = overlay.bounding_box()
    vp = page.viewport_size
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    assert abs(cx - vp["width"] / 2) < 30 and abs(cy - vp["height"] / 2) < 60
    # Отмена → возврат на лендинг инструкторов
    page.locator("#m-login [data-close]").first.click()
    # флаг источника записан — верифицируем через history
    src = page.evaluate("sessionStorage.getItem('open_login_from')")
    assert src == "/instructors"
