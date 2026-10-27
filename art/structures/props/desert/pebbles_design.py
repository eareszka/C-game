"""Pebbles, desert scenery: loose stones lying on the sand, three ways.

    python art/structures/props/desert/pebbles_design.py

48x16, three single cells side by side -- a cluster of five, a group of
three, a scatter of small ones -- after a PixelLab draft
(pixellab-out/desert-pebbles/sprites/v1). Each stone a squat ellipse lying on
the sand (tools/prop_paint.py blobs), lit at its upper left, its lower right in
shade, a black line round it, in a sandstone a shade lighter than the cliffs' rock.
Redrawn 2026-10-27: fewer, bigger stones -- the small ones were mostly line and read as beetles in the world. They lie flat and are
walked over, as the old bones were.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
from prop_paint import save

# fills only, one 16x16 cell each: l lit, m mid, d shade; the line is laid round them
SETS = [
    ["................",
     "................",
     "................",
     "..........lmm...",
     "....llmm..mmmd..",
     "...lmmmmd..ddd..",
     "...mmmmmdd......",
     "...mmmmddd......",
     "....ddddd.......",
     "................",
     "........lmm.....",
     "........mmdd....",
     ".........dd.....",
     "................",
     "................",
     "................"],
    ["................",
     "................",
     "................",
     "................",
     ".....llmmm......",
     "....lmmmmmd.....",
     "...lmmmmmmdd....",
     "...mmmmmmmdd....",
     "...mmmmmmddd....",
     "....mmdddddd....",
     ".....ddddd.lm...",
     "...........mdd..",
     "................",
     "................",
     "................",
     "................"],
    ["................",
     "................",
     "................",
     "...lmm..........",
     "..lmmmd...lmm...",
     "..mmmdd..lmmmd..",
     "...ddd...mmmdd..",
     "..........ddd...",
     "................",
     "....lmm.........",
     "...lmmmd........",
     "...mmmdd........",
     "....ddd.........",
     "................",
     "................",
     "................"],
]


def outline(rows):
    g = [list(r) for r in rows]
    for y in range(16):
        for x in range(16):
            if rows[y][x] != '.':
                continue
            if any(0 <= x + dx < 16 and 0 <= y + dy < 16 and rows[y + dy][x + dx] != '.'
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g[y][x] = 'K'
    assert all(c == '.' for c in g[0] + g[15] + [r[0] for r in g] + [r[15] for r in g]), 'a stone at the cell edge'
    return g


if __name__ == '__main__':
    rows = [[] for _ in range(16)]
    for fills in SETS:
        g = outline(fills)
        for y in range(16):
            rows[y] += g[y]
    save(rows, os.path.join(HERE, 'pebbles.png'), 'rock', {'l': 'cebe82', 'm': 'b29e5c', 'd': '887000'})   # the sandstone a shade up from the cliffs', to read as stone on the sand
