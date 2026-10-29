#!/usr/bin/env python3
"""BUG-050: самопроверка hero-верстки frontend/index.html на пересечения.

На ширинах 1440/1280/1024/768/375 открывает лендинг (headless chromium,
статика раздается встроенным http.server), снимает скриншот и проверяет
попарные пересечения bounding-box элементов .intro, .steps, .assistant
и footer, а также горизонтальный выход за вьюпорт (наложение = регресс
абсолютной верстки). Печать: OK / список пересечений по каждой ширине.

Запуск: python scripts/check_hero_overlap.py [--root /path/to/repo]
Код возврата 0 — пересечений нет, 1 — есть.

Скриншоты: ${HERO_SHOTS:-<tmp>/hero-shots-bug050}/hero-<width>.png
"""
import argparse
import functools
import http.server
import os
import socket
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

WIDTHS = (1440, 1280, 1024, 768, 375)
SELECTORS = (".intro", ".steps", ".assistant", "footer")
TOLERANCE = 1.0  # px: допустимое «касание» рамок


def _serve(root: Path):
    """http.server на эфемерном порту, раздача frontend/ (демон-поток)."""
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(root))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{httpd.server_address[1]}/index.html", httpd


def _boxes(page):
    out = {}
    for sel in SELECTORS:
        loc = page.locator(sel)
        if loc.count() == 0:
            out[sel] = None
            continue
        box = loc.first.bounding_box()
        out[sel] = box
    return out


def _overlap(a, b):
    """Пересечение прямоугольников > TOLERANCE по обеим осям, иначе None."""
    if a is None or b is None:
        return None
    w = min(a["x"] + a["width"], b["x"] + b["width"]) - max(a["x"], b["x"])
    h = min(a["y"] + a["height"], b["y"] + b["height"]) - max(a["y"], b["y"])
    if w > TOLERANCE and h > TOLERANCE:
        return (round(w, 1), round(h, 1))
    return None


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=repo / "frontend",
                        help="каталог со статикой (по умолчанию frontend/)")
    args = parser.parse_args()

    shots_dir = Path(os.environ.get(
        "HERO_SHOTS", os.path.join(tempfile.gettempdir(), "hero-shots-bug050")))
    shots_dir.mkdir(parents=True, exist_ok=True)

    url, httpd = _serve(args.root)
    problems = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for width in WIDTHS:
            page = browser.new_page(
                viewport={"width": width, "height": 900})
            page.goto(url)
            page.wait_for_selector(".assistant")
            boxes = _boxes(page)
            shot = shots_dir / f"hero-{width}.png"
            page.screenshot(path=str(shot), full_page=True)

            issues = []
            missing = [s for s, b in boxes.items() if b is None]
            if missing:
                issues.append(f"не найдены: {', '.join(missing)}")
            names = [s for s in SELECTORS if boxes.get(s)]
            for i, a in enumerate(names):
                for b in names[i + 1:]:
                    ov = _overlap(boxes[a], boxes[b])
                    if ov:
                        issues.append(
                            f"ПЕРЕСЕЧЕНИЕ {a} x {b}: {ov[0]}x{ov[1]}px")
            # горизонтальный выход за вьюпорт (наезд на соседа/край)
            for s in names:
                bx = boxes[s]
                if bx["x"] < -TOLERANCE or \
                        bx["x"] + bx["width"] > width + TOLERANCE:
                    issues.append(
                        f"ВЫХОД ЗА ВЬЮПОРТ {s}: "
                        f"x={bx['x']:.0f}..{bx['x'] + bx['width']:.0f} "
                        f"(width={width})")
            if issues:
                problems.append((width, issues))
                print(f"{width}px: FAIL")
                for it in issues:
                    print(f"  - {it}")
            else:
                print(f"{width}px: OK (скриншот {shot})")
            page.close()
        browser.close()
    httpd.shutdown()

    if problems:
        print("FAIL: пересечения/выходы за вьюпорт на ширине(ах) "
              + ", ".join(str(w) for w, _ in problems))
        return 1
    print("OK: пересечений .intro/.steps/.assistant/footer нет "
          "на ширинах " + ", ".join(str(w) for w in WIDTHS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
