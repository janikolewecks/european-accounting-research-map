# -*- coding: utf-8 -*-
"""Splice the exported data into the page template.

Outputs
  build/dashboard.html   bare fragment for the Artifact viewer, which supplies
                         its own document shell
  docs/index.html        a COMPLETE html document for public hosting: doctype,
                         charset, viewport, description, social cards, favicon
  docs/data.js           the data, so a new congress year replaces one file

GitHub Pages can serve a site straight from the docs/ folder of the default
branch, which is why the hosted build lands there.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "dashboard_data.json"
SITE_URL = "https://jwecks.github.io/european-accounting-research-map/"

TITLE = "European Accounting Research Map"
DESC = ("What European accounting researchers study, how they study it and "
        "where their evidence comes from. 7,443 submissions to the Annual "
        "Congress of the European Accounting Association, 2015 to 2026, "
        "classified on 25 topics, 14 methods and 8 data sources.")

# Inline favicon: the letter mark on the EAA royal blue, so no extra request.
FAVICON = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
    "%3Crect width='32' height='32' fill='%23225493'/%3E"
    "%3Cpath d='M7 23V9h5.6M7 16h5M7 23h6M18 23V9l7 14V9' stroke='white' "
    "stroke-width='2.2' fill='none' stroke-linejoin='round' "
    "stroke-linecap='round'/%3E%3C/svg%3E"
)

HEAD = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<link rel="canonical" href="{SITE_URL}">
<link rel="icon" href="{FAVICON}">
<meta name="theme-color" content="#1a4478" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#132c4d" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{TITLE}">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:url" content="{SITE_URL}">
<meta property="og:image" content="{SITE_URL}preview.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{TITLE}">
<meta name="twitter:description" content="{DESC}">
<meta name="twitter:image" content="{SITE_URL}preview.png">
"""

tpl = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
raw = DATA.read_text(encoding="utf-8")
assert tpl.count("__DATA__") == 1, "template must contain exactly one __DATA__ token"

# ---- artifact build: fragment, data inlined ----------------------------
(ROOT / "build").mkdir(exist_ok=True)
single = tpl.replace("__DATA__", raw)
(ROOT / "build" / "dashboard.html").write_text(single, encoding="utf-8", newline="\n")

# ---- hosted build: full document, data in a sibling file ---------------
docs = ROOT / "docs"
docs.mkdir(exist_ok=True)
body = tpl.replace("<script>\nconst D = __DATA__;",
                   '<script src="data.js"></script>\n<script>\nconst D = window.__EAA_DATA__;')
assert "__DATA__" not in body, "hosted splice failed"

# the template opens with its own <title>; the document head already carries one
first_nl = body.index("\n") + 1
assert body[:first_nl].startswith("<title>"), "template no longer starts with <title>"
body = body[first_nl:]

# the stylesheet link belongs in the head, the rest in the body
link_end = body.index("\n", body.index("<link rel=\"stylesheet\"")) + 1
head_link, body = body[:link_end], body[link_end:]

hosted = HEAD + head_link + "</head>\n<body>\n" + body + "\n</body>\n</html>\n"
(docs / "index.html").write_text(hosted, encoding="utf-8", newline="\n")
(docs / "data.js").write_text("window.__EAA_DATA__=" + raw + ";", encoding="utf-8", newline="\n")
(docs / ".nojekyll").write_text("", encoding="utf-8")

print(f"build/dashboard.html  {len(single)/1024:>5.0f} KB   (artifact fragment)")
print(f"docs/index.html       {len(hosted)/1024:>5.0f} KB   (full document)")
print(f"docs/data.js          {len(raw)/1024:>5.0f} KB")
