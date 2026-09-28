"""The game's palette, and where every colour not on it goes.

PALETTE is read from game_palette.gpl, which is the source of truth: the
colours the game drew at commit 3a4b41d, before the FC World recolour, with
near-duplicates merged so that sprites meaning the same colour use one. (The
module keeps its old name so the tools that import it need not change.)

REMAP sends colours that are not on the palette to one that is:

- MERGED: the near-duplicates the palette dropped, each to the colour it was
  merged into -- the more-used of the pair.
- FROM_FC: the colours of the FC World recolour (commit 830f1e1), for any art
  still carrying them, each to the old colour playing the same part.

Anything else goes to its nearest palette colour (CIELAB). The per-tile rule
(four colours a cell) lives in tools/palette_pass.py, which applies all this.
"""
import os
from functools import lru_cache

HERE = os.path.dirname(os.path.abspath(__file__))
KEYS = {(255, 0, 0), (0, 0, 255), (255, 0, 255)}


def hx(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def _load_palette():
    out = []
    for line in open(os.path.join(HERE, "game_palette.gpl")):
        f = line.split()
        if len(f) >= 3 and all(v.isdigit() for v in f[:3]):
            out.append(tuple(int(v) for v in f[:3]))
    assert out and len(set(out)) == len(out), "game_palette.gpl: empty or repeated colours"
    return out


PALETTE = _load_palette()
ACCENTS = set()           # none: nearest-colour may land anywhere on the palette

MERGED = {
    "#92744c": "#967448", "#260e00": "#270800", "#2f2f37": "#292931",
    "#391315": "#311113", "#302010": "#341e10", "#545864": "#595965",
    "#9ee8b0": "#a8f0bc", "#52525e": "#595965", "#6f2324": "#792727",
    "#35264f": "#3b2a58", "#ffffff": "#fcfcfc", "#452914": "#3c2412",
    "#193d28": "#163623", "#1c152a": "#181224", "#40404a": "#474751",
    "#1f4c30": "#235436", "#251b38": "#2b1f40", "#24242a": "#292931",
    "#11271a": "#142e1f", "#19181f": "#1e1e24", "#100d18": "#14101e",
}

FROM_FC = {
    # foliage, dark to light: the old trees' body and highlight greens, and the
    # darkest green already in the game (emerald rock) under them
    "#325a23": "#235436", "#649655": "#058f3a", "#82b473": "#05c43a",
    # grounds, back to what they were
    "#6e834f": "#4edc4a", "#9aaa7a": "#a8f0bc", "#9b94b3": "#fcfcfc",
    "#18003b": "#5c94fc", "#644880": "#fcfcfc", "#60413d": "#887000",
    "#b1bf7f": "#d7a175", "#8c7747": "#f0e880", "#75264f": "#fc74b4",
}

REMAP = dict(MERGED, **FROM_FC)
LUT = {hx(k): hx(v) for k, v in REMAP.items()}
assert all(v in PALETTE for v in LUT.values()), \
    [k for k, v in REMAP.items() if hx(v) not in PALETTE]


def _lab(c):
    def lin(u):
        u /= 255
        return ((u + 0.055) / 1.055) ** 2.4 if u > 0.04045 else u / 12.92
    r, g, b = map(lin, c)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return (116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z)))


_AUTO = [(c, _lab(c)) for c in PALETTE if c not in ACCENTS]


def lab_dist(a, b):
    la, lb = _lab(a), _lab(b)
    return sum((p - q) ** 2 for p, q in zip(la, lb))


@lru_cache(maxsize=None)
def nearest(c):
    """The closest palette colour to c."""
    lc = _lab(c)
    return min(_AUTO, key=lambda e: sum((p - q) ** 2 for p, q in zip(lc, e[1])))[0]


def lookup(c):
    """Where colour c goes: itself if on the palette, else REMAP's choice, else
    the nearest palette colour."""
    if c in KEYS or c in PALETTE:
        return c
    return LUT.get(c) or nearest(c)


def luma(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def remap_image(im):
    """Recolour an RGB(A) PIL image onto the palette. Returns the image and the
    colours REMAP did not name (they went to their nearest)."""
    im = im.convert("RGBA")
    px = im.load()
    missed = {}
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            c = (r, g, b)
            if c not in KEYS and c not in PALETTE and c not in LUT:
                missed[c] = missed.get(c, 0) + 1
            px[x, y] = (*lookup(c), a)
    return im, missed
