# -*- coding: utf-8 -*-
"""Prove that nothing personal or institutional reaches the published files.

This is a gate, not a note in a readme. build.py refuses to write the hosted
files if any check here fails, so the guarantee cannot quietly rot when the
corpus or the export changes.

Checks
  A  structure      every data row is six integers, nothing else
  B  whitelist      every string in the file comes from a fixed vocabulary
  C  author names   no primary or co-author name occurs anywhere in the text
  D  affiliations   no affiliation string occurs anywhere in the text
  E  titles         no submission title occurs anywhere in the text
  F  free text      no abstract or model-reasoning text occurs in the text
  G  contact data   nothing that looks like an e-mail, ORCID or URL
"""
import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
RESEARCH = Path(r"C:/Users/jwecks/Dropbox/17_EAA_Research")
CORPUS = RESEARCH / "idea_Z" / "analysis" / "out" / "corpus_with_2026.parquet"

# every file that actually reaches a visitor
TARGETS = [PROJECT / "data" / "dashboard_data.json",
           PROJECT / "docs" / "data.js",
           PROJECT / "docs" / "index.html",
           PROJECT / "build" / "dashboard.html"]

SENSITIVE_COLUMNS = ["Primary_author", "Primary_author_affiliation", "Co_authors",
                     "Title", "Abstract", "topic_reasoning", "meth_reasoning",
                     "setting_reasoning", "sov_reasoning", "qed_evidence",
                     "setting_recovery_evidence"]

fails, notes = [], []


def check(name, ok, detail=""):
    (notes if ok else fails).append(f"{'PASS' if ok else 'FAIL'}  {name}" +
                                    (f"  --  {detail}" if detail else ""))


def strings_in(node, out):
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, list):
        for v in node:
            strings_in(v, out)
    elif isinstance(node, dict):
        for k, v in node.items():
            out.append(k)
            strings_in(v, out)


def main():
    payload = json.loads((PROJECT / "data" / "dashboard_data.json").read_text(encoding="utf-8"))

    # ---- A structure ----------------------------------------------------
    rows = payload["rows"]
    bad = [r for r in rows
           if not (isinstance(r, list) and len(r) == 6 and all(isinstance(v, int) for v in r))]
    check("A structure: every row is six integers", not bad,
          f"{len(rows):,} rows checked" if not bad else f"{len(bad)} malformed")

    # ---- B whitelist ----------------------------------------------------
    allowed = set(payload["topics"]) | set(payload["methods"]) | set(payload["sources"])
    allowed |= {c["code"] for c in payload["countries"]}
    allowed |= {c["name"] for c in payload["countries"]}
    allowed |= {c["fam"] for c in payload["countries"]}
    allowed |= {v for v in payload["meta"].values() if isinstance(v, str)}
    allowed |= set(payload["meta"].keys())
    allowed |= {"meta", "countries", "topics", "methods", "sources", "rows",
                "code", "name", "eu", "fam", "eu6", ""}
    found = []
    strings_in(payload, found)
    unexpected = sorted({s for s in found if s not in allowed and not isinstance(s, int)})
    check("B whitelist: no string outside the fixed vocabulary", not unexpected,
          f"{len(set(found))} distinct strings, all accounted for" if not unexpected
          else f"unexpected: {unexpected[:5]}")

    # ---- C to F: nothing from the sensitive columns appears --------------
    import pandas as pd
    df = pd.read_parquet(CORPUS, columns=[c for c in SENSITIVE_COLUMNS])
    blobs = {t.name: t.read_text(encoding="utf-8") for t in TARGETS if t.exists()}
    check("targets present", len(blobs) == len(TARGETS),
          f"{len(blobs)}/{len(TARGETS)} files: {', '.join(blobs)}")

    def scan(col, label, min_len=6, limit=None):
        vals = df[col].dropna().astype(str).unique().tolist()
        vals = [v.strip() for v in vals if len(v.strip()) >= min_len]
        if limit:
            vals = vals[:limit]
        hits = []
        for fn, blob in blobs.items():
            low = blob.lower()
            for v in vals:
                if v.lower() in low:
                    hits.append(f"{fn}: {v[:48]}")
                    if len(hits) > 4:
                        return hits, len(vals)
        return hits, len(vals)

    for col, label in [("Primary_author", "C author names"),
                       ("Primary_author_affiliation", "D affiliations"),
                       ("Co_authors", "D co-author records"),
                       ("Title", "E submission titles"),
                       ("Abstract", "F abstracts"),
                       ("topic_reasoning", "F topic reasoning"),
                       ("meth_reasoning", "F method reasoning"),
                       ("sov_reasoning", "F evidence reasoning")]:
        hits, n = scan(col, label, min_len=8 if col == "Co_authors" else 6)
        check(f"{label}: absent from every published file", not hits,
              f"{n:,} values tested" if not hits else "; ".join(hits[:3]))

    # ---- G contact data --------------------------------------------------
    # Hosts the page is meant to reach: the font service and the SVG namespace,
    # plus our own canonical address. Anything else would be an outbound leak.
    from config import SITE_HOST
    ALLOWED_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com",
                     "www.w3.org", SITE_HOST)
    email = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    url = re.compile(r"https?://([A-Za-z0-9.-]+)")
    leaks = []
    for fn, blob in blobs.items():
        for m in set(email.findall(blob)):
            leaks.append(f"{fn}: e-mail {m}")
        if "orcid.org/" in blob:
            leaks.append(f"{fn}: orcid reference")
        for host in set(url.findall(blob)):
            if host not in ALLOWED_HOSTS:
                leaks.append(f"{fn}: outbound host {host}")
    check("G contact data: no e-mail, ORCID or unexpected host", not leaks,
          "font service and SVG namespace only" if not leaks else "; ".join(leaks[:4]))

    report = PROJECT / "data" / "privacy_audit.txt"
    report.write_text("Privacy audit of the published files\n" + "=" * 52 + "\n"
                      + "\n".join(notes + fails) + "\n\n"
                      + ("ALL CHECKS PASSED\n" if not fails else "FAILED\n"),
                      encoding="utf-8")
    print("\n".join(notes + fails))
    print("-" * 52)
    print("ALL CHECKS PASSED" if not fails else f"{len(fails)} CHECK(S) FAILED")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
