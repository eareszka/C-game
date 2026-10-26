"""Dry grass, desert scenery: tufts of straw-coloured blades, two sizes.

    python art/structures/props/desert/grass_design.py

32x16, two single cells -- a full tuft and a small one -- after a PixelLab
draft (pixellab-out/desert-grass/sprites/v1). In the villages' thatch, the
straw it is: two tones and black. Blades fan from one root, each a pixel
wide, placed by hand; a blade leaning to
the left looks to the light and is the lit straw, one leaning right is in shade,
an upright one lit down its left and shaded down its right. Drawn as the
ground draws a tuft, not as an object: no line round it, black dots under its
root (the user, 2026-10-26, over the same tufts outlined). Walked over.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
from prop_paint import save

CELL = 16
# fills only, one 16x16 cell each: l the lit straw, d its shade; the line is laid round them.
# Blades a pixel wide, so they part where they fan and the sand shows between the tips.
TUFTS = [
    ["................",
     "................",
     "........l.......",
     "...l....l...d...",
     "...l...l....d...",
     "....l..l...d....",
     "..l.l..l...d.d..",
     "..l..l.ld.d..d..",
     "...l.l.ld.d.d...",
     "...l.lllddd.d...",
     "....lllldddd....",
     ".....llldd......",
     "......lldd......",
     "......dddd......",
     "................",
     "................"],
    ["................",
     "................",
     "................",
     "................",
     "................",
     "................",
     ".......l........",
     ".....l.l..d.....",
     ".....l.l..d.....",
     "...l..ll.d..d...",
     "....l.lldd.d....",
     ".....lllddd.....",
     ".......lld......",
     ".......ddd......",
     "................",
     "................"],
]


def ground_tuft(fills):
    """The ground's way with a tuft (OVERWORLD_STYLE.md "Ground": the grass cells' tufts):
    no line round it, only black dots in the sand under its root."""
    g = [list(r) for r in fills]
    root = max(y for y in range(CELL) if any(c != '.' for c in g[y]))
    xs = [x for x in range(CELL) if g[root][x] != '.']
    for x in xs[1:-1]:
        g[root + 1][x] = 'K'
    return g


if __name__ == '__main__':
    rows = [[] for _ in range(CELL)]
    for fills in TUFTS:
        g = ground_tuft(fills)
        for y in range(CELL):
            rows[y] += g[y]
    save(rows, os.path.join(HERE, 'grass.png'), 'foliage', {'l': 'c9a433', 'd': '876a1f'})
