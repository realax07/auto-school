"""Одноразовая проверка баланса тегов новых S4-страниц (задача 2/3, отчёт)."""
from html.parser import HTMLParser

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errs = []

    def handle_starttag(self, t, a):
        if t not in VOID:
            self.stack.append((t, self.getpos()))

    def handle_endtag(self, t):
        if t in VOID:
            return
        if not self.stack:
            self.errs.append(f"extra </{t}> at {self.getpos()}")
            return
        if self.stack[-1][0] == t:
            self.stack.pop()
        else:
            self.errs.append(
                f"mismatch </{t}> at {self.getpos()}, top {self.stack[-1]}")


for f in ["frontend/my-cars.html", "frontend/review-form.html",
          "frontend/my-requests.html"]:
    p = P()
    p.feed(open(f, encoding="utf-8").read())
    status = "OK" if not p.errs and not p.stack else (
        f"ERRS={p.errs} UNCLOSED={p.stack}")
    print(f, status)
