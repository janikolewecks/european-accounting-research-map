# -*- coding: utf-8 -*-
"""Screenshot the dashboard in both themes and on both tab panels."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
URL = (HERE.parent / "build" / "dashboard.html").as_uri()
SHOTS = HERE.parent / "shots"
SHOTS.mkdir(exist_ok=True)

VIEWS = [("trends", None), ("map", None), ("profiles", None), ("combinations", None)]

with sync_playwright() as p:
    b = p.chromium.launch()
    for scheme in ("light", "dark"):
        pg = b.new_page(viewport={"width": 1280, "height": 1000},
                        color_scheme=scheme, device_scale_factor=2)
        pg.goto(URL)
        pg.wait_for_timeout(1200)
        for view, _ in VIEWS:
            pg.click(f'.tabs button[data-view="{view}"]')
            pg.wait_for_timeout(350)
            pg.screenshot(path=str(SHOTS / f"{view}-{scheme}.png"), full_page=(view == "combinations"))
        # the map has three quite different states worth keeping an eye on
        pg.click('.tabs button[data-view="map"]'); pg.wait_for_timeout(300)
        pg.select_option("#m-show", "family"); pg.wait_for_timeout(450)
        pg.screenshot(path=str(SHOTS / f"map-families-{scheme}.png"))
        pg.select_option("#m-show", "volume"); pg.wait_for_timeout(350)
        pg.click('#m-basis button[data-mbasis="evidence"]'); pg.wait_for_timeout(500)
        pg.screenshot(path=str(SHOTS / f"map-evidence-{scheme}.png"))
        pg.close()
    # mobile check
    pg = b.new_page(viewport={"width": 390, "height": 900}, device_scale_factor=2)
    pg.goto(URL); pg.wait_for_timeout(1000)
    pg.screenshot(path=str(SHOTS / "mobile.png"))
    pg.close()
    b.close()
print("shots written:", sorted(f.name for f in SHOTS.glob("*.png")))
