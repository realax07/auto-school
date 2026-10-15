"""Проверка баланса HTML-тегов (Спринт 3, задача 7): редактированные страницы.

Запуск: .venv/bin/python scripts/check_tag_balance.py file1.html ...
Без аргументов проверяет дефолтный набор страниц спринта 3.
"""
import sys
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}

DEFAULT = [
    "frontend/instructor-choice.html",
    "frontend/instructor-dashboard.html",
    "frontend/admin-dashboard.html",
    "frontend/cabinet.html",
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
