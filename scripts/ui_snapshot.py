"""Headless smoke-test helper: open the running app in Chromium, wait for the
Streamlit fragments to settle, then save a full-page screenshot plus the
rendered body text (UTF-8, same path + ".txt").

Usage: python scripts/ui_snapshot.py [output.png] [port]
Requires: pip install -r requirements-dev.txt && python -m playwright install chromium
"""
import sys

from playwright.sync_api import sync_playwright

OUT = sys.argv[1] if len(sys.argv) > 1 else "snapshot.png"
PORT = sys.argv[2] if len(sys.argv) > 2 else "8501"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 1600})
    page.goto(f"http://localhost:{PORT}", wait_until="networkidle")
    page.wait_for_timeout(6000)  # let fragments / price fetch settle
    page.screenshot(path=OUT, full_page=True)
    # Body text goes to a file, not stdout - the Windows console codepage
    # (cp1250) cannot print the emoji used in the UI badges.
    with open(OUT + ".txt", "w", encoding="utf-8") as f:
        f.write(page.inner_text("body"))
    browser.close()
    print(f"Saved {OUT} and {OUT}.txt")
