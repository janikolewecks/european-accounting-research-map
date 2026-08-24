# -*- coding: utf-8 -*-
"""Render docs/preview.png, the 1200x630 card shown when the link is shared,
and verify the hosted build (index.html + data.js) actually works."""
import http.server, socketserver, threading, functools, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

DOCS = Path(__file__).resolve().parent.parent / "docs"
PORT = 8731
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS))
srv = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{PORT}/index.html"

with sync_playwright() as pw:
    b = pw.chromium.launch()
    errs = []
    pg = b.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=2)
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(URL); pg.wait_for_timeout(1400)

    ok = pg.evaluate("""() => ({
        data: typeof window.__EAA_DATA__ === 'object',
        papers: document.getElementById('f-papers').textContent,
        charts: document.querySelectorAll('.panel svg').length,
        viewport: !!document.querySelector('meta[name=viewport]'),
        doctype: !!document.doctype,
        lang: document.documentElement.lang,
        og: document.querySelectorAll('meta[property^="og:"]').length })""")
    print("hosted build:", ok, "| errors:", errs[:2] or "none")
    pg.screenshot(path=str(DOCS / "preview.png"))
    pg.close()

    # mobile now works because the viewport meta is present
    m = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    m.goto(URL); m.wait_for_timeout(1000)
    print("mobile: no h-scroll =",
          m.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth"))
    m.close(); b.close()
srv.shutdown()

from PIL import Image
im = Image.open(DOCS / "preview.png").resize((1200, 630), Image.LANCZOS)
im.save(DOCS / "preview.png", optimize=True)
print("docs/preview.png:", im.size, f"{(DOCS/'preview.png').stat().st_size/1024:.0f} KB")
