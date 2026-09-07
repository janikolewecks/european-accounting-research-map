# Handover — European Accounting Research Map

**Stand 2026-08-25, zweite Fassung. Diese Datei zuerst lesen.** Sie beschreibt den
IST-Zustand. Das fachliche Warum steht in `README.md`.

Dieses Projekt ist ein **Nebenstrang** der EAA-Metastudie. Das Paper selbst
wird in einem anderen Chat bearbeitet; Projektstand dort:
`C:\Users\jwecks\Dropbox\17_EAA_Research\idea_Z\PROJECT_STATE.md`.
Hier geht es ausschliesslich um das oeffentliche Dashboard.

---

## 1. Was es ist und wo es liegt

Interaktive Begleitseite zum Konvergenz-Paper: was europaeische
Rechnungslegungsforscher untersuchen, womit, und woher ihre Evidenz kommt.
7.443 EAA-Kongresseinreichungen, neun Jahrgaenge, vier Ansichten:
Trends, Karte, Profile, Kombinationen.

| Was | Wo |
|---|---|
| Projekt | `C:\Users\jwecks\Dropbox\EAA-Research-Map\` |
| **LIVE** | https://janikolewecks.github.io/european-accounting-research-map/ |
| Repository | https://github.com/janikolewecks/european-accounting-research-map (public) |
| Artefakt (Vorschau im Chat) | https://claude.ai/code/artifact/b49ee1ea-481e-4b38-b52a-2e7550c7cfc0 |
| Quellkorpus (nur lesend) | `17_EAA_Research\idea_Z\analysis\out\corpus_with_2026.parquet` |

Ordner: `src/` Quellen, `data/` anonymisierter Auszug, `docs/` das was
GitHub Pages ausliefert, `build/` Einzeldatei fuers Artefakt, `shots/`
Screenshots.

---

## 2. Live-Status (von aussen geprueft, 2026-08-25)

index.html, data.js und preview.png liefern HTTP 200 mit korrektem
Content-Type; HTTP leitet per 301 auf HTTPS um; Titel, viewport, canonical,
og:image und `lang="en"` stehen; drei Charts rendern; keine Konsolenfehler;
Periodenfilter greift; mobil kein Querscroll.

---

## 3. Arbeitsablauf

    python src/export_data.py   # liest den Korpus, schreibt data/
    python src/build_geo.py     # nur noetig, wenn sich die Laenderliste aendert
    python src/build.py         # baut docs/ und build/, faehrt die Pruefung
    python src/test.py          # 64 Funktionstests (Playwright)
    python src/shot.py          # Screenshots hell/dunkel/mobil
    git add -A && git commit -m "..." && git push     # Pages deployt selbst

**KEINE Browser-Previews** (`mcp__Claude_Browser__preview_start`) — hat die
Sitzung mehrfach zum Absturz gebracht. Playwright direkt benutzen, das
laeuft stabil. Chrome und Playwright sind installiert, `gh` nicht.

---

## 4. Feste Entscheidungen (nicht ohne Ruecksprache aendern)

1. **Fuenf kategoriale Farben, nicht sechs.** Palette aus dem EAA-CI
   (Koenigsblau `#225493`, Cyan `#009acc`). Eine sechste Farbe hielt das
   Farbfehlsichtigkeits-Gate im Dunkelmodus nicht. Geprueft mit dem
   Validator des dataviz-Skills: schlechtestes Nachbarpaar dE 19,4 hell /
   15,4 dunkel gegen Zielwert 8. **Bei Farbaenderung neu validieren.**
2. **Schriftpaarung** Newsreader (Serife, Masthead/Ueberschriften/Reiter) +
   IBM Plex Sans (Bedienung) + IBM Plex Mono (Ziffern). Ergebnis eines
   Audits gegen den avoid-ai-design-Katalog; die Fundtabelle steht im
   README. Nicht auf eine einzelne Schrift zurueckbauen.
3. **Keine Karten/Boxen**, Struktur ueber Haarlinien und Weissraum
   (Swiss/International). Radius null.
4. **Datenlueckenbehandlung:** 2019-2021 gestrichelt und abgeblendet
   ueberbrueckt; ein Jahr ohne Einreichungen ist `null`, nicht 0.
5. **Adresse zentral** in `src/config.py` (`DOMAIN`, `GH_USER`, `GH_REPO`).
   Alles leitet sich davon ab: canonical, Social-Cards, CNAME und die
   Host-Freigabe der Datenschutzpruefung. Nirgends sonst haendisch setzen.
6. **Kartengeometrie liegt in der Seite**, nicht bei einem Kartendienst.
   Natural Earth (gemeinfrei), vereinfacht und projiziert, 50 KB, EPSG:3035.
   **Nur Europa.** Eine Weltkarte war gebaut und wurde auf Wunsch wieder
   entfernt; was ausserhalb Europas liegt, steht als Zahl unter der Karte.
   `EU` und `XX` in der Laenderliste sind keine Laender und zaehlen zu den
   Papieren ohne einzelnes Land. Der Rahmen wird **im projizierten Raum**
   zugeschnitten; ein Grad-Rechteck erzeugt sonst einen Russland-Keil.
   Malta, Luxemburg und Monaco werden als Punkte gezeichnet, sonst
   verschwinden sie. Zaehlungen werden wurzelskaliert, Anteile linear,
   Anteile unter 10 Einreichungen schraffiert statt eingefaerbt.
7. **Lizenz:** Code MIT (`LICENSE`), Daten CC BY 4.0 (`LICENSE-DATA.txt`,
   enthaelt den amtlichen Volltext). Als Rechteinhaber steht dort bisher nur
   Janik Ole Wecks &#8212; **vor Veroeffentlichung klaeren, ob die Koautoren
   dazugehoeren.**
8. **`data.js` wird mit Inhalts-Hash angefordert** (`data.js?v=...`), und
   jede Ansicht wird einzeln gezeichnet (`draw()` in der Seite). Grund: nach
   dem ersten Karten-Deploy paarte ein Browser die neue Seite mit der alten
   gecachten Datendatei, `GEO` fehlte, `drawMap` warf &#8212; und weil Profile
   und Kombinationen danach gezeichnet wurden, blieben **drei** Reiter leer.
   Beides nicht zurueckbauen. Bei Fehlern zuerst hart neu laden (Strg+F5).
9. **Die Karte faerbt NIE einen Rohanteil.** Zypern hat 17 von 19 Papieren in
   Capital Markets und waere als Rohanteil das dunkelste Land Europas,
   obwohl das bei der Groesse eine Arbeitsgruppe ist und keine Community.
   Eine reine Anzahl ist kaum besser: log(Themenpapiere) korreliert mit
   r = 0,90 mit log(Gesamtpapieren), ist also im Wesentlichen eine Karte der
   Groesse des akademischen Marktes. Gefaerbt wird deshalb der **Abstand zum
   europaeischen Durchschnitt in Prozentpunkten**, divergierende Skala,
   neutrale Mitte = wie Europa, gleiche Referenz wie die Profilansicht.
   Mindestbasis 30 Einreichungen, darunter schraffiert; die Tabelle zeigt den
   Rohanteil weiterhin. **Anzahlen laufen logarithmisch** und jedes Land hat
   eine sichtbare Kontur: mit Wurzelskala und weissen Grenzen landeten alle
   kleinen Laender im blassesten Schritt und waren vom Papier nicht zu
   unterscheiden. Ein Koautor meldete, Georgien sei von der Karte
   verschwunden, obwohl es in Tabelle A.1 steht &#8212; es war die ganze Zeit da,
   vier Papiere tief im hellsten Ton.
10. **Drei Zustaende, drei Formen:** Flaeche = hat Daten, Schraffur = zu
   wenig, Umriss = nicht Teil dieser Auswahl. Grund: `validate_palette.py`
   zeigte, dass im Dunkelmodus "am Durchschnitt" und "keine Daten" **exakt
   dieselbe Farbe** waren (dE 0,0). Farbe kann diese Bedeutungen bei geringer
   Saettigung nicht tragen, erst recht nicht fuer farbfehlsichtige Leser.
   `python src/validate_palette.py` laeuft in der Testsuite mit.
11. **Datenschutz-Gate:** `src/audit_privacy.py` prueft alle ausgelieferten
   Dateien gegen 5.489 Autorennamen, 2.669 Affiliationen, 5.957
   Ko-Autoren-Eintraege, 7.458 Titel, Abstracts und vier LLM-Freitextfelder.
   `build.py` **loescht die Auslieferungsdateien**, wenn etwas durchrutscht.
   Das Gate wurde durch Einschleusen eines echten Namens getestet.
   Nicht abschalten, nicht umgehen. Pruefung H deckt seit der Karte auch
   `data/map_geo.json` ab.

---

## 5. OFFEN

**Entscheidungen des Nutzers:**
- **Domain.** Frei geprueft und alle verfuegbar: `accounting-research-map.eu`
  (meine Empfehlung, lesbar, deckt sich mit dem Titel),
  `accountingresearchmap.eu`, `accounting-research-trends.eu`,
  `accountingresearchtrends.eu`. Umsetzung: `DOMAIN` in `config.py` setzen,
  neu bauen, DNS beim Registrar (A/AAAA + CNAME, Adressen im README),
  dann "Enforce HTTPS". Registrar-Tipp: WHOIS-Privacy und Auto-Renew an.
- **Titel.** Nutzer erwog "Accounting Research Trends". Mein Rat: bei
  "European Accounting Research Map" bleiben, weil "Trends" nur eine von
  drei Ansichten benennt, "European" (die tatsaechliche Reichweite) faellt
  und der Begriff generisch besetzt ist. Falls doch "Trends": den ersten
  Reiter in "Over time" umbenennen, sonst steht das Wort doppelt.
- **Lizenz-Rechteinhaber.** Die Lizenzen liegen (MIT + CC BY 4.0). Genannt
  ist nur der Repository-Eigentuemer. Falls der annotierte Korpus
  Gemeinschaftsarbeit ist, gehoeren die Koautoren in beide Dateien.
- **EAA ansprechen?** Die Seite traegt Namen und Farben des Verbands. Rat:
  mit der fertigen Seite auf sie zugehen, nicht vorher fragen.
- **`D:\Users\wecks\data_ralph`** — Nutzer nannte diesen Pfad ohne Kontext.
  Es ist der 286-GB-Forschungs-Data-Lake (58 Datensatzordner, `CATALOG.json`
  als maschinenlesbares Inventar). Zweck unklar. Zwei Lesarten: Projekt
  dorthin verschieben (davon abgeraten) oder ein aehnliches Werkzeug fuer
  den Katalog bauen. **Nachfragen, nichts anfassen.**

**Rueckmeldung des Koautors vom 25.08.2026, Stand der Umsetzung:**
- Kartenansicht &#8212; umgesetzt (Reiter "Map": Einreichungen, Familien,
  Anteil eines Labels; Autoren- oder Evidenzland; Europa oder Welt).
- Familien eindeutig beschreiben &#8212; umgesetzt (Familienkarte,
  Nobes-Herkunft und Laenderliste im Abspann, aus den Daten erzeugt).
- Weniger AI-Sprache, konkretere Datenherkunft &#8212; umgesetzt (Abspann
  nennt Annahme statt Einreichung, die neun Jahrgaenge, die 88 Dubletten,
  das Land als Erstautoren-Affiliation und die Validierung gegen die
  Selbstcodierung: 6.013 Papiere, 87,2 Prozent, Kappa 0,739).

**Fachlich zu klaeren:**
- **2017er Ausschlag bei Sustainability**: 17,3 % gegen rund 9 % in den
  Nachbarjahren. So in den Labels, nicht geglaettet. Im Paper faellt es
  nicht auf (Periodenmittel), auf der Seite sieht es jeder sofort. Vor
  breiter Streuung klaeren, ob echter Jahrgangseffekt oder Artefakt.

**Moegliche Ausbaustufen:**
- Konvergenz-Explorer als vierte Ansicht (bewusst zurueckgestellt).
- Zenodo-Archivierung je Jahresversion fuer eine zitierfaehige DOI.

---

## 6. Zahlen, die stimmen muessen

7.443 Einreichungen gesamt, 4.881 mit europaeischem Erstautor, 32
europaeische Laender, neun Jahrgaenge 2015-2018 und 2022-2026, 25 Themen,
14 Methoden, 8 Datenquellen. Datendatei 167 KB roh, 41 KB gepackt.
Vorberechnete Aggregate waeren 142 KB gewesen, also 3,5x groesser — deshalb
liefert die Seite Papierzeilen aus, nicht Aggregate.
