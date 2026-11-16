"""Замечание Заказчика 2026-11-15 №1: сайдбар ученика — СТАТИЧНЫЙ ЕДИНЫЙ
элемент при переходах по разделам/страницам (пропадали новые разделы ПДД
на instructor-choice). Канонический список ученика — 9 пунктов, тот же
состав и порядок на всех носителях:

- cabinet.html + src/pages/cabinet/App.vue — SPA-кнопки (data-tab;
  «Выбрать инструктора» — data-goto);
- instructor-choice.html + src/pages/instructor-choice/App.vue — ссылки
  (активный пункт «Выбрать инструктора» — текущая страница);
- instructor-choice.html + его App.vue — ссылки (активный «Выбрать
  не входит в список).

ПДД-хеши (#/pdd-*) и разделы кабинета (#/my-requests, #/my-bookings,
#/wallet) роутятся App.vue кабинета при загрузке (bootstrap-проверки хешей,
test_pdd_sections.py::test_pdd_four_hashes_bootstrap_in_app, e2e TC-UI-070a).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VUE = ROOT / "frontend" / "vue"
SRC = VUE / "src" / "pages"

# канонический список ученика: (текст, иконка, href для ссылочных носителей)
ITEMS = [
    ("Главная", "⌂", "/cabinet"),
    ("Мои заявки", "✉", "/cabinet#/my-requests"),
    ("Выбрать инструктора", "▤", "/instructor-choice"),
    ("Мои брони", "◷", "/cabinet#/my-bookings"),
    ("Кошелек", "₽", "/cabinet#/wallet"),
    ("Знаки", "◈", "/cabinet#/pdd-signs"),
    ("Правила", "☰", "/cabinet#/pdd-rules"),
    ("Билеты", "◉", "/cabinet#/pdd-tickets"),
    ("Штрафы", "⚠", "/cabinet#/pdd-fines"),
]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_snav_buttons_canonical_in_cabinet():
    """cabinet.html и App.vue: все 9 пунктов кнопками в каноническом порядке
    (8 data-tab + data-goto «Выбрать инструктора»)."""
    for carrier in (read(VUE / "cabinet.html"), read(SRC / "cabinet" / "App.vue")):
        pos = -1
        for name, ico, _href in ITEMS:
            if name == "Выбрать инструктора":
                frag = f'<button data-goto="/instructor-choice" type="button"><span class="ico">{ico}</span>{name}</button>'
            elif name == "Главная":
                frag = f'<button class="on" data-tab="{name}" type="button"><span class="ico">{ico}</span>{name}</button>'
            else:
                frag = f'<button data-tab="{name}" type="button"><span class="ico">{ico}</span>{name}</button>'
            cur = carrier.index(frag)
            assert cur > pos, f"порядок сайдбара нарушен: {name}"
            pos = cur


def _nav_of(carrier: str) -> str:
    return carrier.split('<nav class="snav">', 1)[1].split("</nav>", 1)[0]


def test_snav_links_canonical_in_instructor_choice():
    """instructor-choice.html и App.vue: 9 ссылок в каноническом порядке;
    «Выбрать инструктора» — активный пункт (текущая страница)."""
    for carrier in (
        read(VUE / "instructor-choice.html"),
        read(SRC / "instructor-choice" / "App.vue"),
    ):
        nav = _nav_of(carrier)
        cursor = -1
        for name, ico, href in ITEMS:
            on = ' class="on"' if name == "Выбрать инструктора" else ""
            line = f'<a{on} href="{href}"><span class="ico">{ico}</span>{name}</a>'
            cur = nav.index(line)
            assert cur > cursor, f"порядок сайдбара нарушен: {name}"
            cursor = cur
        assert nav.count("<a") == 9


