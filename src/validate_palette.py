# -*- coding: utf-8 -*-
"""Check the palette against colour vision deficiency, in both themes.

The readme claims the colours were checked with a validator rather than by
eye. This is that validator, so the claim can be re-run rather than believed.

Method: sRGB to linear RGB, to LMS, simulate dichromacy with the Vienot 1999
reduction, back to sRGB, then compare in CIELAB with dE76. Every pair that
has to stay apart on screen is listed explicitly, because the pairs that
matter are the ones the eye is asked to compare, not every pair in the file.

    python src/validate_palette.py        # prints a table, exits 1 on failure
"""
import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "template.html"

# Separation targets in dE76. Adjacent steps of a ramp may be close, because
# a ramp is read as an order; colours that carry different meanings may not.
TARGET_ADJACENT = 6.0
TARGET_MEANING = 12.0


def srgb(hexcode):
    h = hexcode.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def unlin(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def mul(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


RGB2LMS = ((17.8824, 43.5161, 4.11935),
           (3.45565, 27.1554, 3.86714),
           (0.0299566, 0.184309, 1.46709))
LMS2RGB = ((0.080944, -0.130504, 0.116721),
           (-0.0102485, 0.0540194, -0.113615),
           (-0.000365294, -0.00412163, 0.693513))
SIM = {
    "normal": None,
    "protan": ((0, 2.02344, -2.52581), (0, 1, 0), (0, 0, 1)),
    "deutan": ((1, 0, 0), (0.494207, 0, 1.24827), (0, 0, 1)),
    "tritan": ((1, 0, 0), (0, 1, 0), (-0.395913, 0.801109, 0)),
}


def simulate(hexcode, kind):
    r, g, b = (lin(c) for c in srgb(hexcode))
    if SIM[kind] is None:
        return (r, g, b)
    lms = mul(RGB2LMS, (r, g, b))
    lms = mul(SIM[kind], lms)
    return mul(LMS2RGB, lms)


def lab(rgb_linear):
    r, g, b = rgb_linear
    x = 0.4124 * r + 0.3576 * g + 0.1805 * b
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = 0.0193 * r + 0.1192 * g + 0.9505 * b
    xn, yn, zn = 0.95047, 1.0, 1.08883

    def f(t):
        t = max(t, 0.0)
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x / xn), f(y / yn), f(z / zn)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def de(a, b, kind):
    la, lb = lab(simulate(a, kind)), lab(simulate(b, kind))
    return sum((x - y) ** 2 for x, y in zip(la, lb)) ** 0.5


def tokens(block):
    return dict(re.findall(r"(--[a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{6})", block))


def blocks():
    css = TEMPLATE.read_text(encoding="utf-8")
    css = css[css.index("<style>"):css.index("</style>")]
    light = css[css.index(":root {"):css.index("@media (prefers-color-scheme: dark)")]
    dark = css[css.index('@media (prefers-color-scheme: dark)'):css.index(':root[data-theme="dark"]')]
    return {"light": tokens(light), "dark": tokens(dark)}


def main():
    fails = []
    for theme, t in blocks().items():
        print(f"\n{theme}")
        ramps = [("categorical series", [t[f"--s{i}"] for i in range(1, 6)], TARGET_MEANING),
                 ("sequential ramp", [t[f"--q{i}"] for i in range(1, 8)], TARGET_ADJACENT),
                 ("diverging ramp", [t[f"--d{i}"] for i in range(1, 8)], TARGET_ADJACENT)]
        for name, cols, target in ramps:
            worst, where = 999, ""
            for i in range(len(cols) - 1):
                for kind in SIM:
                    d = de(cols[i], cols[i + 1], kind)
                    if d < worst:
                        worst, where = d, f"{cols[i]}/{cols[i+1]} {kind}"
            ok = worst >= target
            print(f"  {name:20s} worst adjacent dE {worst:5.1f}  (target {target:4.1f})  {where}")
            if not ok:
                fails.append(f"{theme} {name}: dE {worst:.1f} at {where}")

        # The two arms of a diverging ramp must never be mistaken for each
        # other: that is the whole point of the scale.
        for a, b in ((1, 7), (2, 6), (3, 5)):
            worst = min(de(t[f"--d{a}"], t[f"--d{b}"], k) for k in SIM)
            ok = worst >= TARGET_MEANING
            print(f"  diverging arms d{a}/d{b}   dE {worst:5.1f}  (target {TARGET_MEANING:4.1f})")
            if not ok:
                fails.append(f"{theme} diverging arms d{a}/d{b}: dE {worst:.1f}")

        # On the map the states that are not data carry no fill at all: too
        # little to say is hatched, not part of the map is an outline. What
        # still has to hold is that a filled country never looks like bare
        # ground, or a country with one paper reads as no country at all.
        pairs = [("--q1", "--surface", "lowest count step vs the page ground"),
                 ("--d4", "--surface", "at the average vs the page ground"),
                 ("--d4", "--d3", "at the average vs the first step below"),
                 ("--d4", "--d5", "at the average vs the first step above")]
        for a, b, why in pairs:
            worst = min(de(t[a], t[b], k) for k in SIM)
            ok = worst >= TARGET_MEANING
            print(f"  {why:42s} dE {worst:5.1f}  {'ok' if ok else 'TOO CLOSE'}")
            if not ok:
                fails.append(f"{theme} {why}: dE {worst:.1f}")

    print()
    if fails:
        for f in fails:
            print("FAIL", f)
        return 1
    print("palette holds in both themes, for normal vision and all three dichromacies")
    return 0


if __name__ == "__main__":
    sys.exit(main())
