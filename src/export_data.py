# -*- coding: utf-8 -*-
"""Build the anonymized data file behind the European Accounting Research Map.

Exports one compact JSON with no personal data: no author names, no titles,
no abstracts, no affiliations, no institution-level flags. Each row is one
submission reduced to
    [year, countryIdx, topicMask, methodMask, sourceIdx, evidenceCountryIdx]
where the masks are bitfields over the fixed vocabularies. Lookup arrays for
countries, topics, methods and sources travel with the file.

Corpus rules follow the paper: resubmissions of the same paper by the same
author under an identical title are counted once, at their first appearance.

Outputs
    out/dashboard_data.json      the file the dashboard loads
    out/dashboard_data.json.gz   size reference for hosting
"""
import gzip
import json
import re
import sys
from pathlib import Path

import pandas as pd

# The labelled corpus lives in the research repository; this project only
# reads from it and writes its own anonymized extract.
RESEARCH = Path(r"C:/Users/jwecks/Dropbox/17_EAA_Research")
PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RESEARCH / "analysis" / "src" / "v3"))
import lib  # noqa: E402

CORPUS = RESEARCH / "idea_Z" / "analysis" / "out"
OUT = PROJECT / "data"
EUROPE = set(lib.EUROPE)

SRC_ORDER = ["public_market_database", "govt_or_regulatory_register",
             "hand_collected_public", "survey_or_experiment",
             "interviews_or_fieldsite", "proprietary_organization",
             "media_or_textual", "none_or_analytical"]
SRC_NICE = ["Commercial database", "State and regulatory registers",
            "Hand-collected public records", "Own survey or experiment",
            "Interviews and field sites", "Proprietary organizational data",
            "Public text and media", "No empirical data"]

FAMILY = {}
for c in ["UK", "IE", "NL"]:
    FAMILY[c] = "Anglo-Dutch"
for c in ["DE", "AT", "CH"]:
    FAMILY[c] = "Germanic"
for c in ["FR", "IT", "ES", "PT", "BE", "GR", "LU", "MT", "CY"]:
    FAMILY[c] = "Latin"
for c in ["SE", "NO", "DK", "FI", "IS"]:
    FAMILY[c] = "Nordic"
for c in ["PL", "CZ", "HU", "RO", "SK", "SI", "HR", "BG", "EE", "LV", "LT",
          "RS", "UA", "TR"]:
    FAMILY[c] = "Central-Eastern"
EU6 = {"BE", "DE", "FR", "IT", "LU", "NL"}

NAME = {
    "UK": "United Kingdom", "IE": "Ireland", "NL": "Netherlands",
    "DE": "Germany", "AT": "Austria", "CH": "Switzerland", "FR": "France",
    "IT": "Italy", "ES": "Spain", "PT": "Portugal", "BE": "Belgium",
    "GR": "Greece", "LU": "Luxembourg", "MT": "Malta", "CY": "Cyprus",
    "SE": "Sweden", "NO": "Norway", "DK": "Denmark", "FI": "Finland",
    "IS": "Iceland", "PL": "Poland", "CZ": "Czech Republic", "HU": "Hungary",
    "RO": "Romania", "SK": "Slovakia", "SI": "Slovenia", "HR": "Croatia",
    "BG": "Bulgaria", "EE": "Estonia", "LV": "Latvia", "LT": "Lithuania",
    "RS": "Serbia", "UA": "Ukraine", "TR": "Turkey", "MD": "Moldova",
    "AL": "Albania", "BA": "Bosnia and Herzegovina", "MK": "North Macedonia",
    "ME": "Montenegro", "GE": "Georgia", "AM": "Armenia", "AZ": "Azerbaijan",
    "LI": "Liechtenstein", "MC": "Monaco", "SM": "San Marino", "AD": "Andorra",
    "US": "United States", "CA": "Canada", "AU": "Australia", "CN": "China",
    "JP": "Japan", "KR": "South Korea", "IN": "India", "BR": "Brazil",
    "NZ": "New Zealand", "SG": "Singapore", "HK": "Hong Kong", "TW": "Taiwan",
    "IL": "Israel", "ZA": "South Africa", "MX": "Mexico", "CL": "Chile",
    "RU": "Russia", "AE": "United Arab Emirates", "SA": "Saudi Arabia",
    "TH": "Thailand", "MY": "Malaysia", "ID": "Indonesia", "VN": "Vietnam",
    "PK": "Pakistan", "BD": "Bangladesh", "LK": "Sri Lanka", "NG": "Nigeria",
    "EG": "Egypt", "KE": "Kenya", "GH": "Ghana", "MA": "Morocco",
    "TN": "Tunisia", "JO": "Jordan", "QA": "Qatar", "KW": "Kuwait",
    "OM": "Oman", "BH": "Bahrain", "LB": "Lebanon", "IR": "Iran",
    "AR": "Argentina", "CO": "Colombia", "PE": "Peru", "UY": "Uruguay",
    "EC": "Ecuador", "VE": "Venezuela", "PH": "Philippines",
}


def main():
    df = pd.read_parquet(CORPUS / "corpus_with_2026.parquet")
    df = df.copy()
    df["Year"] = df["Year"].astype(int)
    df["_a"] = df["Primary_author"].astype(str).str.strip().str.title()
    df["_t"] = df["Title"].apply(lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower()))
    n0 = len(df)
    df = df.sort_values(["_a", "Year"]).drop_duplicates(["_a", "_t"], keep="first")
    print(f"corpus {n0:,} -> {len(df):,} after removing resubmissions")

    TCOL = lib.get_dim_cols(df, "topic")
    MCOL = lib.get_dim_cols(df, "meth")
    topics = [c.replace("topic_", "") for c in TCOL]
    methods = [c.replace("meth_", "") for c in MCOL]
    assert len(topics) == 25 and len(methods) == 14

    # country index: every country appearing as a primary-author location or
    # as an evidence country, sorted by paper count so the common ones sit first
    prim = df["Country"].astype(str).str.strip().str.upper()
    ev = df.get("setting_country_final", pd.Series([""] * len(df), index=df.index))
    ev = ev.astype(str).str.strip().str.upper().replace({"GB": "UK"})
    prim = prim.replace({"GB": "UK"})
    counts = prim.value_counts()
    codes = [c for c in counts.index if c and c not in ("", "NAN", "NONE")]
    extra = sorted({c for c in ev.unique()
                    if c and c not in codes and c not in ("", "NAN", "NONE")
                    and len(c) == 2})
    codes = codes + extra
    cidx = {c: i for i, c in enumerate(codes)}

    src_idx = {s: i for i, s in enumerate(SRC_ORDER)}
    rows = []
    for i, (_, r) in enumerate(df.iterrows()):
        tm = 0
        for k, c in enumerate(TCOL):
            if r.get(c) == 1:
                tm |= 1 << k
        mm = 0
        for k, c in enumerate(MCOL):
            if r.get(c) == 1:
                mm |= 1 << k
        pc = prim.iloc[i]
        ec = ev.iloc[i]
        rows.append([
            int(r["Year"]),
            cidx.get(pc, -1),
            tm,
            mm,
            src_idx.get(str(r.get("sov_origin", "")), -1),
            cidx.get(ec, -1),
        ])

    payload = {
        "meta": {
            "title": "EAA Congress Research Map",
            "papers": len(rows),
            "years": sorted(df["Year"].unique().tolist()),
            "built": "2026-08-24",
            "note": ("Aggregated classification of EAA Annual Congress "
                     "submissions. No author names, titles, abstracts, "
                     "affiliations or institution-level information."),
        },
        "countries": [{"code": c, "name": NAME.get(c, c),
                       "eu": 1 if c in EUROPE else 0,
                       "fam": FAMILY.get(c, ""),
                       "eu6": 1 if c in EU6 else 0} for c in codes],
        "topics": topics,
        "methods": methods,
        "sources": SRC_NICE,
        "rows": rows,
    }

    raw = json.dumps(payload, separators=(",", ":"))
    (OUT / "dashboard_data.json").write_text(raw, encoding="utf-8")
    gz = gzip.compress(raw.encode(), 9)
    (OUT / "dashboard_data.json.gz").write_bytes(gz)
    eu_n = sum(1 for r in rows if r[1] >= 0 and codes[r[1]] in EUROPE)
    print(f"countries {len(codes)}, european papers {eu_n:,}")
    print(f"json {len(raw)/1024:.0f} KB, gzipped {len(gz)/1024:.0f} KB")


if __name__ == "__main__":
    main()
