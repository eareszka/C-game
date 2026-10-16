"""18 Vatnaormur's map mini: the lake serpent coming at you through its own water, its head turned three
quarters, at the player's scale, one drawing for every way it goes, two frames (tools/minis.py).

Its battle sheet only faces front (it never leaves its lake). The user, 2026-10-14: "has a single dashing
sprite for all directions where the head is tilted 3/4 directions"; then "should be big size and more
intimadating"; then "should be much bigger and move pretty much straight". So one drawing in all four views,
44 px tall, near its battle size (its battle frames stand 51): the shrink of its battle frame, its bound
tail ends cut so it fits an 80 x 48 canvas (too big for the sheet's 40 x 28 cells, it has a strip of its own,
assets/enemies/minis_18.png), with by hand: its slug's face as in battle (the user: "needs to look more like a
slug in the face like the orignal sprite"), the eye stalks on top and the small round toothed mouth, the mouth
moved 3 px to its right to turn the face three quarters; the lake under it with a clean edge. The second frame
sinks it a pixel as it surges. Four of its battle colours and black, one over the bible's three, as a giant
battle sprite may have more (its slug's face needs its light grey): its dark grey, its grey (the face, the
light down its neck and coils), its pink (the stalk eyes, the teeth, its throat and the undersides of its
coils), its lake blue. Its white goes.

Its chase: straight at you, at the chase pace (the default in chase_speed(), src/main.cpp).

    python art/enemies/minis/18_vatnaormur_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'G': '595965', 'H': '848694', 'P': 'ec8476', 'B': '3e91cc'}
CHASE = 'straight'
CW, CH = 80, 48                              # its canvas; the feet on row 46, the outline under them on 47
LETTERS = {'595965': 'G', '474751': 'G', '848694': 'H', 'a4aaba': 'H', '3e91cc': 'B', '84a7e9': 'B',
           'ec8476': 'P', 'fcfcfc': 'P'}
X0, Y0 = -19, -15                            # the shrink's columns -19..59 and rows -15..27 are the drawing's 0..78, 0..42
MOUTH = (36, 12, 6, 3)                       # its battle mouth, small, round, toothed: column, row, width, height


def drawing():
    g = minis.clean(minis.shrink(minis.battle_views(18)['D'], 44, LETTERS))
    rows = [[g.get((x + X0, y + Y0), '.') for x in range(79)] for y in range(43)]
    x0, y0, w, h = MOUTH                     # its face turned three quarters: the mouth moved 3 to its right
    mouth = [rows[y][x0:x0 + w] for y in range(y0, y0 + h)]
    for y in range(y0, y0 + h):
        rows[y][x0:x0 + w] = 'H' * w
    for i, m in enumerate(mouth):
        for j, c in enumerate(m):
            if c in 'KP': rows[y0 + i][x0 + 3 + j] = c
    for y in range(27, 35):                  # the cut tail ends: the humps' outer walls closed
        for x in (0, 1, 2, 76, 77, 78):
            rows[y][x] = '.'
        if rows[y][3] != '.': rows[y][3] = 'K'
        if rows[y][75] != '.': rows[y][75] = 'K'
    rows[34][:3] = rows[34][76:] = '...'
    rows = [''.join(r)[1:78] for r in rows]  # 77 wide: a column clear either side of the canvas
    rows[35] = '.' + 'K' * 75 + '.'          # the water's edge
    for y in range(36, 40):
        rows[y] = 'K' + 'B' * 75 + 'K'
    return rows


def sink(rows):
    """Its body a pixel lower, the water as it was."""
    return ['.' * 77] + rows[:34] + rows[35:]


BASE = drawing()
VIEWS = {v: [BASE, sink(BASE)] for v in 'DULR'}
FRAMES = {v: [ff.grid([(5 + y, 1, r) for y, r in enumerate(rows)], PAL) for rows in fs] for v, fs in VIEWS.items()}

if __name__ == '__main__':
    minis.make(18, 'vatnaormur', FRAMES, PAL, cap=44, cell=(CW, CH), colours=4)
    minis.chase_gif(18, CHASE, FRAMES, PAL, cell=(CW, CH))
