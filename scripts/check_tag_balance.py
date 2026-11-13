"""Проверка баланса HTML-тегов (Спринт 3, задача 7): редактированные страницы.

Запуск: .venv/bin/python scripts/check_tag_balance.py file1.html ...
Без аргументов проверяет дефолтный набор страниц спринта 3.
"""
import sys
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}

DEFAULT = [
    # Спринт 15 (change add-vue-s15-final-migration, задача 5.1): легаси
    # instructor-choice.html/admin-dashboard.html/cabinet.html удалены
    # (замена монолита целиком, ADR-008) — носителиdesign-guard'ов теперь
    # входы каркаса Vue (перенос: −3 легаси, +6 входов партии)
    "frontend/vue/cabinet.html",
    "frontend/vue/instructor-choice.html",
    "frontend/vue/admin-dashboard.html",
    "frontend/vue/admin-login.html",
    "frontend/vue/registered.html",
    "frontend/vue/policy.html",
    # Спринт 14 (change add-vue-s14-instructor-loop, задача 4.1): носитель
    # кабинета — вход каркаса Vue (легаси instructor-dashboard.html удален)
    "frontend/vue/instructor-dashboard.html",
]


class Balance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errs = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
        else:
            self.errs.append(
                f"mismatch </{tag}> at {self.getpos()} "
                f"(top={self.stack[-1] if self.stack else None})")


def main(paths):
    failed = False
    for f in paths:
        p = Balance()
        p.feed(open(f, encoding="utf-8").read())
        p.close()
        if p.errs or p.stack:
            failed = True
            print(f"{f}: ERRS={p.errs[:5]} "
                  f"UNCLOSED={[(t, pos) for t, pos in p.stack][:8]}")
        else:
            print(f"{f}: OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or DEFAULT))
