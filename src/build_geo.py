# -*- coding: utf-8 -*-
"""Build the map geometry the dashboard draws, as inlined SVG path data.

The page may not call out to a tile server or a CDN: the privacy audit
allows the font service and nothing else, and a map that depends on a
third party stops working the day that third party does. So the outlines
travel with the page.

Source   Natural Earth, public domain (naturalearthdata.com), cached in
         src/vendor/ and not committed.
Frame    ETRS89 / LAEA (EPSG:3035), the standard European frame. The map is
         European on purpose: evidence from outside Europe is reported as a
         count under the map rather than drawn, because this is a map of
         European accounting research and not a world atlas.

Output   data/map_geo.json   {frame: {w, h, paths{code: d}, cent{code: [x,y]},
                                      area{code: px2}}}
"""
import json
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "src" / "vendor"
OUT = ROOT / "data" / "map_geo.json"

# Natural Earth writes the United Kingdom as GB; the corpus uses UK.
RECODE = {"GB": "UK"}

# Countries too small to survive simplification at either scale. Without these
# a reader would find Malta or Luxembourg simply missing from the map.
DOTS = {"MC": (7.42, 43.73), "MT": (14.45, 35.90), "LU": (6.13, 49.61),
        "LI": (9.55, 47.16), "SM": (12.45, 43.94), "AD": (1.52, 42.51),
        "CY": (33.20, 35.10), "SG": (103.82, 1.35), "HK": (114.17, 22.32),
        "MO": (113.55, 22.20), "BH": (50.55, 26.06), "XK": (20.90, 42.60)}
DROP = {"AQ", "-99", "", None}


def frame(src, crs, clip, tol, width, drop_below=None, prec=1,
          focus=None, focus_window=None):
    gdf = gpd.read_file(VENDOR / src)
    col = "ISO_A2_EH" if "ISO_A2_EH" in gdf.columns else "ISO_A2"
    gdf = gdf[[col, "geometry"]].rename(columns={col: "code"})
    gdf = gdf.assign(code=gdf["code"].map(lambda c: RECODE.get(c, c)))
    gdf = gdf[~gdf["code"].isin(DROP)]
    gdf = gdf.set_crs(4326, allow_override=True)
    if clip:
        gdf = gpd.clip(gdf, box(*clip))
    elif drop_below is not None:
        gdf = gpd.clip(gdf, box(-180, drop_below, 180, 84))
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()]
    gdf = gdf.to_crs(crs)
    if focus:
        # A rectangle in degrees becomes a wedge once projected, which puts a
        # meaningless triangle of Russia in the corner of the map. Cut the
        # frame in projected space instead, around the countries that matter.
        # The frame is measured on the mainland: Norway reaches Svalbard, and
        # letting that set the northern edge would leave the map mostly sea.
        f = gdf[gdf["code"].isin(focus)]
        if focus_window:
            f = gpd.clip(f.to_crs(4326), box(*focus_window)).to_crs(crs)
            f = f[~f.geometry.is_empty & f.geometry.notna()]
        x0, y0, x1, y1 = f.total_bounds
        mx, my = (x1 - x0) * 0.03, (y1 - y0) * 0.03
        gdf = gpd.clip(gdf, box(x0 - mx, y0 - my, x1 + mx, y1 + my))
        gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()]
    gdf = gdf.set_geometry(gdf.geometry.simplify(tol, preserve_topology=True))
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()]
    gdf = gdf.dissolve(by="code", as_index=False)

    minx, miny, maxx, maxy = gdf.total_bounds
    s = width / (maxx - minx)
    height = round((maxy - miny) * s, 1)
    q = (lambda v: round(v, 1)) if prec else (lambda v: int(round(v)))
    X = lambda x: q((x - minx) * s)
    Y = lambda y: q((maxy - y) * s)

    def rings(geom):
        # clipping can hand back stray lines and points alongside the polygons
        if geom.geom_type == "Polygon":
            return [geom.exterior]
        if hasattr(geom, "geoms"):
            out = []
            for g in geom.geoms:
                out.extend(rings(g))
            return out
        return []

    paths, cent, area = {}, {}, {}
    for _, row in gdf.iterrows():
        d = []
        for ring in rings(row.geometry):
            pts = list(ring.coords)
            if len(pts) < 4:
                continue
            # a ring smaller than a pixel or two adds bytes and no information
            xs = [X(p[0]) for p in pts]
            ys = [Y(p[1]) for p in pts]
            if max(xs) - min(xs) < 1.2 and max(ys) - min(ys) < 1.2:
                continue
            d.append("M" + " ".join(f"{x} {y}" for x, y in zip(xs, ys)) + "Z")
        if not d:
            continue
        paths[row["code"]] = "".join(d)
        c = row.geometry.representative_point()
        cent[row["code"]] = [X(c.x), Y(c.y)]
        area[row["code"]] = round(row.geometry.area * s * s, 1)

    from pyproj import Transformer
    tr = Transformer.from_crs(4326, crs, always_xy=True)
    for code, (lon, lat) in DOTS.items():
        x, y = tr.transform(lon, lat)
        if not (minx <= x <= maxx and miny <= y <= maxy):
            continue
        cent[code] = [X(x), Y(y)]
        area.setdefault(code, 0.0)
    return {"w": width, "h": height, "paths": paths, "cent": cent, "area": area}


if __name__ == "__main__":
    # The Europe frame is cut around the countries the corpus actually has,
    # so the map is not mostly ocean.
    europe_codes = {c["code"] for c in
                    json.loads((ROOT / "data" / "dashboard_data.json").read_text(encoding="utf-8"))["countries"]
                    if c.get("eu")}
    out = {
        "europe": frame("ne_50m.geojson", 3035, (-60, 20, 110, 84), 7000, 700,
                        focus=europe_codes, focus_window=(-26, 33, 46, 72)),
    }
    OUT.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    for k, v in out.items():
        print(f"{k:7s} {len(v['paths']):3d} shapes   {v['w']}x{v['h']}")
    print(f"data/map_geo.json  {kb:.0f} KB")
