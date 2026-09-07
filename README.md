# European Accounting Research Map

Evidence from the Annual Congress of the European Accounting Association,
2015 to 2026.

An interactive companion to the convergence paper. It shows what European
accounting researchers study, how they study it and where their evidence
comes from, across nine congress years, filterable by country, accounting
family and period. Four views: trends over time, a map, country and family
profiles, and cross-tabulations.

## Layout

    data/     dashboard_data.json    the anonymized extract the page reads
              map_geo.json           country outlines as SVG path data
    src/      export_data.py         builds that extract from the labelled corpus
              build_geo.py           builds the outlines from Natural Earth
              template.html          the page, with __DATA__ and __GEO__ placeholders
              build.py               splices both into the two output shapes
              audit_privacy.py       the gate build.py runs before publishing
              validate_palette.py    colour-blindness check, run by test.py
              config.py              the site address, used by build and audit
              test.py                64 functional checks (Playwright)
              shot.py                screenshots, light and dark, desktop and mobile
              vendor/                cached Natural Earth source, not committed
    docs/     index.html, data.js,   >>> this is what GitHub Pages serves <<<
              preview.png, .nojekyll
    build/    dashboard.html         bare fragment, for the Artifact viewer
    shots/    rendered screenshots
    LICENSE, LICENSE-DATA.txt        MIT for the code, CC BY 4.0 for the data

The labelled corpus itself stays in the research repository
(`17_EAA_Research`); `src/export_data.py` points at it and is the only file
that touches it.

## Updating for a new congress year

    python src/export_data.py     # re-reads the corpus, rewrites data/
    python src/build.py           # rebuilds docs/ and build/, runs the privacy gate
    python src/test.py            # 64 checks should pass

The map outlines change only if the country list does:

    python src/build_geo.py       # re-fetches Natural Earth, rewrites data/map_geo.json

Then `git add -A && git commit -m "congress year 2027" && git push`. Pages
redeploys in about a minute. The page reads the vocabularies, the country
list and the year list out of the data file, so a new topic, a new country
or a tenth congress year needs no code change.

## Hosting

The page is static: no server, no database, no build step on the host.
Everything it needs is in `docs/` (about 390 KB including the preview image).

### GitHub Pages, the recommended route

1. Create a **public** repository named `european-accounting-research-map`.
   Public is required for Pages on a free account, and the data is meant to
   be public anyway.
2. From this folder:

       git remote add origin https://github.com/janikolewecks/european-accounting-research-map.git
       git branch -M main
       git push -u origin main

3. In the repository, **Settings > Pages**, set Source to *Deploy from a
   branch*, branch `main`, folder `/docs`, and save.
4. After a minute the site is live at
   `https://janikolewecks.github.io/european-accounting-research-map/`.

The address is set in `src/config.py` (`GH_USER`, `GH_REPO`, `DOMAIN`) and
everything derives from it: the canonical link, the social-card tags, the
`CNAME` file and the host allowlist of the privacy audit. Change it there and
rerun `python src/build.py`.

### A custom domain

Buy the domain at a registrar, keep the files on GitHub Pages, point the
domain at Pages. Pages issues a free certificate for it, so the address is
yours while the hosting stays free and maintenance-free.

1. Set `DOMAIN` in `src/config.py` and run `python src/build.py`. That writes
   `docs/CNAME` and rewrites the canonical link and the social-card URLs.
   The privacy audit follows the same constant, so the new host is tolerated
   automatically.
2. At the registrar, for the bare domain create four **A** records to
   `185.199.108.153`, `185.199.109.153`, `185.199.110.153`,
   `185.199.111.153`, and four **AAAA** records to `2606:50c0:8000::153`,
   `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`.
   For `www`, one **CNAME** record to `janikolewecks.github.io`.
3. Commit and push, then enter the domain under **Settings > Pages**. Once
   the DNS check passes, tick **Enforce HTTPS**. The certificate can take up
   to 24 hours.

Register with auto-renew on and WHOIS privacy enabled, otherwise the
registrant's home address becomes public. A research artifact that dies
because a domain lapsed is the most common way these things disappear.

### Other hosts

- **Netlify or Cloudflare Pages** — drag the `docs/` folder onto the
  dashboard. No git needed, custom domain in a few clicks.
- **A university server** — copy `docs/` anywhere that serves static files.
  Works, but ties the map to one person's institutional account.
- **Zenodo** — archive each yearly version for a citable DOI. Worth doing if
  the map is cited alongside the paper.

### Before it goes public

- Settle the EAA question, since the page carries the association's name and
  colours.
- Note that publishing is effectively one-way: once the data file is public
  and indexed, taking it down does not un-publish it.

## Licence

The code is under the MIT licence (`LICENSE`). The data are under CC BY 4.0
(`LICENSE-DATA.txt`), which also states the attribution to use and what the
licence does not cover: the underlying congress records, which are not ours
to license and are not published here.

The map outlines in `data/map_geo.json` derive from Natural Earth, which is
public domain and requires no attribution; the credit in the footer and in
the data licence is a courtesy.

The copyright holder named in both files is the repository owner. If the
labelled corpus is joint work, the co-authors belong there too, and both
files need editing before the licence means what it should.

## What the data contains, and how that is enforced

Per submission: congress year, primary-author country, topic labels, method
labels, data source, evidence country. Six integers. Nothing else.

Deliberately excluded: author names, co-author records, paper titles,
abstracts, affiliation strings, model reasoning text, and all
institution-level information including the WRDS membership flag.
Institution level was excluded on purpose. A department with a handful of
submissions is effectively an identifiable person, and the WRDS match is
model-based with known residual errors, so publishing institution claims
would carry risk without informing the reader.

### The guarantee is a gate, not a promise

`src/audit_privacy.py` checks every file that reaches a visitor
(`data/dashboard_data.json`, `docs/data.js`, `docs/index.html`,
`build/dashboard.html`) against the source corpus:

| Check | What it proves | Scope of the last run |
|---|---|---|
| A structure | every data row is six integers, no free text anywhere | 7,443 rows |
| B whitelist | every string comes from the fixed vocabulary or the country list | 236 distinct strings |
| C author names | no primary-author name occurs in any published file | 5,489 names |
| D affiliations | no affiliation string occurs | 2,669 affiliations |
| D co-authors | no co-author record occurs | 5,957 records |
| E titles | no submission title occurs | 7,458 titles |
| F free text | no abstract or model-reasoning text occurs | 7,463 abstracts, 3 reasoning fields |
| G contact data | no e-mail, ORCID or unexpected outbound host | font service, SVG namespace, own repository |
| H map geometry | the outlines carry two-letter country codes and coordinates, nothing else | 238 outlines in 2 frames |

`build.py` runs the audit after writing the files and **deletes the hosted
output if any check fails**, so a leaking site cannot sit on disk waiting to
be pushed. The gate is itself tested: injecting a real author name into the
data makes the build fail and remove `docs/index.html` and `docs/data.js`.

The congress programmes are public, so a determined reader could in principle
match a rare combination of labels back to a paper. That is inherent to any
bibliometric dataset of a public programme. Two mitigations are in place: the
heatmap prints the base `n` of every row so small cells cannot be over-read,
and the page states that the classifications are ours rather than the
authors' own.

## Why the data file is public, and what the alternatives cost

Anything a browser draws, the browser first receives. A dashboard that runs
in the visitor's browser cannot hide its own data. The only real choices are
what the file contains and whether the computation happens on a server.

**Shipping only pre-computed aggregates was measured, not guessed.** The full
cube the dashboard needs for its 162 filter states (2 populations x 27 groups
x 3 periods, trends plus all six ordered dimension pairs) is **142 KB
delivered, against 41 KB for the paper rows**. Aggregates are 3.5 times
larger here, because 7,443 rows of six small integers are more compact than
every cross-tabulation of them. They would also freeze the interface: a new
view or a new filter combination would need a new export. So that route
costs bandwidth and flexibility and buys very little.

**A server-side API would genuinely change the exposure**, since the browser
would only ever receive the aggregate it asked for. The price is a backend
that must be paid for, kept patched and kept alive for as long as the map is
cited. It also ends the property that makes this thing durable: a static file
set that any host can serve, forever, for nothing.

**Obfuscating the file is not protection.** Anyone with the browser's
developer tools has it in under a minute. Building it would only mislead us
about our own exposure.

What the file does *not* contain is the part that matters: no names, no
titles, no abstracts, no affiliations, no institution-level flags. It is a
bibliometric extract of a public conference programme, which is the kind of
dataset open science expects to be shared.

The real lever is timing rather than technology. If the concern is being
scooped, the answer is to publish the map when the paper is out or at least
on a preprint server with a DOI, and to attach a licence that requires
citation.

## Design audit

The first build carried a recognisable machine-generated signature. It was
audited against the avoid-ai-design tell catalogue and rebuilt. Findings and
fixes:

| Tell | Finding in the first build | Fix |
|---|---|---|
| T1 no display/body pairing | one sans at different sizes, no typographic voice | Newsreader serif for masthead, section titles and tabs, paired with Plex Sans for interface and Plex Mono for figures |
| T5 reflexive all-caps eyebrows | uppercase letter-spaced micro-labels above every control, figure and table column | sentence case throughout |
| L4 generic stat strip | four equal-weight tiles of big numbers | one lead figure with a sentence, the rest folded into the standfirst |
| L6 default page shell | every band in one centred container of the same width | full-bleed masthead on an asymmetric grid, full-bleed rules on the filter band, varied measures |
| K2 uniform radius and shadow | identical rounded bordered cards regardless of role | boxes removed; hairline rules and whitespace carry the structure, radius set to zero |
| S1 uniform padding | one gap value repeated everywhere | modular scale (`--sp1` to `--sp6`), the lead figure given isolation |

Direction chosen: **Swiss/International**, which suits a research instrument
and lets the EAA blue act as the single signal colour against a near
monochrome ground.

## Design decisions

**Colour follows the EAA identity.** Royal blue `#225493` (the association
mark and its site chrome) and cyan `#009acc` (its secondary accent) anchor
the categorical slots and supply the sequential ramp for the heatmap. The
remaining hues were chosen and stepped so the whole set clears the
colour-vision gates in both light and dark mode, checked with a validator
rather than by eye. That validator is `src/validate_palette.py` and runs as
part of the test suite: it simulates the three dichromacies, compares every
pair the eye is actually asked to tell apart, and fails the suite if any
falls under its target.

**Five categorical slots, not six.** A sixth hue could not hold the gate in
dark mode, so the label picker caps at five. Fewer, cleanly separated
colours beat six that blur for a colour-blind reader.

**The 2019 to 2021 gap is bridged, not hidden.** No congress data exist for
those years. The series are drawn solid up to 2018 and from 2022, and joined
across the gap by a dashed, faded segment, so a line can be followed without
suggesting that a value was observed in between.

**The map carries its own cartography rather than a tile service.** The
outlines are simplified Natural Earth geometry, projected and inlined as SVG
path data: 50 KB, no external request, nothing to keep alive. The projection
is ETRS89 / LAEA (EPSG:3035), the standard European frame, and the frame is
cut in projected space around the countries the corpus actually contains,
since a rectangle in degrees becomes a wedge once projected and leaves a
meaningless triangle of Russia in the corner. Countries too small to survive
simplification, Malta, Luxembourg and Monaco, are drawn as markers so they
cannot silently disappear.

**The map stays European, and says what it leaves out.** A world frame was
built and then dropped: this is a map of European accounting research, not a
world atlas. That matters most in the evidence view, where a large part of
the corpus looks outside Europe, so the count is reported in words under the
map instead of being quietly omitted. Two entries in the country list are not
countries at all, a Union-wide setting and an unidentified one; they are
counted with the papers that name no single country rather than passed off as
foreign states.

**The map never colours a raw share.** A share map answers the wrong
question twice over. Cyprus has 17 capital-markets papers out of 19, so as a
raw share it is the darkest country in Europe, although at that size a
"country" is one research group. Meanwhile the countries that actually
produce most of the capital-markets research look pale, because their output
is spread across everything. And a count map is barely better: the log of a
country's papers on a topic correlates at r = 0.90 with the log of its total
output, so it is mostly a map of how large a country's academic market is.
What the map therefore colours is the distance from the European average in
percentage points, on the same reference the profiles view uses, on a
diverging scale whose neutral middle means "the same as Europe". Counts
remain available as their own view, on a logarithmic scale, because the
counts run from one paper to more than a thousand: on a linear or even a
square-root scale every small country lands in the palest step and cannot be
told apart from bare paper. That is not hypothetical. A co-author reported
that Georgia had disappeared from the map although it is in the paper's
country table; it was there all along, four papers deep in the palest tint,
outlined in white against a white page.

**A country needs at least 30 submissions before it is shaded.** Below that
the number describes a research group rather than a research community. Such
countries are hatched, and the table still reports their raw share, so
nothing is hidden. The rule costs 15 of 32 countries over all years and 15 of
30 in the thinner early period; the alternative was letting nineteen papers
set the darkest colour on the map.

**Countries are outlined, not separated by white.** White borders erase a
pale country: at the bottom of the ramp the fill sits close to the page, so
without a boundary the country reads as background rather than as a country
with little in it.

**Three states, three forms, so colour is not asked to carry meaning it
cannot.** A country with data is filled; a country with too little is
hatched; a country outside the current selection is an outline. This was not
an aesthetic choice: `src/validate_palette.py` showed that in dark mode the
neutral middle of the diverging ramp and the "no data" grey were the same
colour, dE 0.0, and that in light mode four further pairs sat under dE 7. No
arrangement of near-neutral fills separates those meanings for a
colour-blind reader, so form carries them instead.

**The data file is requested with its content hash.** The first deployment
of the map paired a fresh page with a browser's cached copy of the previous
`data.js`. The outlines it expected were simply absent, the map threw, and
because two more views were drawn after it, three tabs went blank at once.
The page now asks for `data.js?v=<hash>`, so a new page can never receive an
old payload, and each view is drawn independently: a view that fails says so
in its own panel and leaves the others standing.

**Every chart has a table view.** Colour is never the only route to a value.
The heatmap also prints the row base, deviations are labelled at the bar
ends, and lines are labelled directly at the right edge.

**Both themes are designed, not inverted.** Each mode has its own steps,
validated against its own surface.

Typography pairs **Newsreader** (serif, for the masthead, section titles and
tabs) with **IBM Plex Sans** for the interface and **IBM Plex Mono** for
figures. The serif gives the page the scholarly register of the paper it
accompanies and breaks the single-sans signature of generated interfaces.
The EAA site itself uses Inter, which is a generic default rather than a
distinguishing mark, so the map keeps a face of its own while the colour
carries the association's identity.

## Open questions

- Whether the co-authors of the corpus should be named as copyright holders
  in `LICENSE` and `LICENSE-DATA.txt`. Only the repository owner is named now.
- Whether to approach the EAA before publishing, and whether they want to
  host or endorse it. Recommendation: show them the working prototype.
- The 2017 spike in the sustainability series (17.3 percent against roughly
  9 percent in the neighbouring years) is in the labels as classified. Worth
  checking whether it is a real congress effect before the map goes public,
  since a reader sees it immediately where the paper averages it away.
