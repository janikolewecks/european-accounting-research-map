# -*- coding: utf-8 -*-
"""Where the site lives. Single source of truth for build and audit alike.

Set DOMAIN once a custom domain is registered, for example
"accountingresearchmap.org". Leave it empty to stay on github.io. Everything
follows from it: the canonical link, the social-card URLs, the CNAME file
GitHub Pages reads, and the list of hosts the privacy audit tolerates.
"""

DOMAIN = ""
GH_USER = "janikolewecks"
GH_REPO = "european-accounting-research-map"

SITE_URL = (f"https://{DOMAIN}/" if DOMAIN
            else f"https://{GH_USER}.github.io/{GH_REPO}/")
SITE_HOST = DOMAIN if DOMAIN else f"{GH_USER}.github.io"
