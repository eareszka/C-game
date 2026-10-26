"""25 Myrmecoleon's map mini: the ant-lion, a lion's maned head and forelegs on an ant's body, its long red insect
legs scuttling, at the player's scale, four views, two frames (tools/minis.py).

Its battle sheet only faces front. Its shapes come from PixelLab (art/enemies/pixellab/25_myrmecoleon/mini,
pixellab-out/25-mini: its battle frame rotated to its eight views, a four-frame scuttle on the front, the back and
the left side). Shrunk, those read as blobs and the body jumped between frames (the user: "have its legs move
instead of the sprite just hopping around, make the body overall more readable"), so it is built here from flat
parts after them, back to front, each with its own black edge where it overlaps what is behind: the ant's legs
(one red pixel wide, bent at a high knee), the striped abdomen raised behind, the mane, the lion's face, its tan
chest and forelegs. The body holds still from frame to frame; only the legs step, the left pair and the right
pair by turns, the forelegs with them.
28 px tall (the user, 2026-10-23: 20 "needs to be larger"), too big for the sheet's 40 x 28 cells: a 48 x 32 canvas,
a strip of its own (assets/enemies/minis_25.png). Three of its battle colours and black: its dark red (the ant:
legs and abdomen), its tan (the lion), its brown (the mane).

Its chase: it scuttles like an ant (the user's pick), never stopping (the user: "constantly moving"), weaving a
little side to side on its long legs (chase_speed() and chase_bend(), src/main.cpp).

    python art/enemies/minis/25_myrmecoleon_mini.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'R': '792727', 'T': 'f4ce80', 'M': '94703d'}
CHASE = 'scuttle'
CW, CH = 48, 32                              # its canvas; the feet on row 30, the outline under them on 31


def ellipse(cx, cy, rx, ry):
    return {(x, y) for y in range(int(cy - ry), int(cy + ry) + 1) for x in range(int(cx - rx), int(cx + rx) + 1)
            if ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 <= 1}


def rect(x0, y0, x1, y1):
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}


def line(*pts):
    """A one-pixel line through the points."""
    out = set()
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        out |= {(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)) for i in range(n + 1)}
    return out


def build(parts):
    """parts, back to front: (pixels, letter) or (pixels, letter, marks) -- marks {(x, y): letter} set on top. Each
    part takes a black edge on whatever it covers, so overlapping parts stay apart."""
    g = {}
    for part in parts:
        px, c = part[0], part[1]
        for x, y in px:
            for dx, dy in ff.N4:
                if (x + dx, y + dy) not in px: g[x + dx, y + dy] = 'K'
        for p in px: g[p] = c
        for p, m in (part[2] if len(part) > 2 else {}).items(): g[p] = m
    return ff.outline(g)


def stripes(px, rows):
    return {(x, y): 'K' for x, y in px if y in rows}


def leg(hip, knee, foot):
    return (line(hip, knee, foot), 'R')


def front(step):
    """Facing you. step 0: its left legs reach, its right legs gather; 1 the other way."""
    a, b = (0, 1) if step == 0 else (1, 0)
    abdomen = ellipse(24, 9, 6, 4)
    mane = ellipse(24, 17, 8, 6)
    face = rect(20, 13, 28, 21) - {(20, 13), (28, 13), (20, 21), (28, 21)}
    marks = {(21, 15): 'K', (22, 16): 'K', (27, 15): 'K', (26, 16): 'K', (24, 17): 'K',     # its brows and eyes, its nose
             **{(x, 18): 'K' for x in range(22, 27)}, (22, 19): 'K', (26, 19): 'K', (23, 19): 'T', (25, 19): 'T',
             (24, 19): 'R', **{(x, 20): 'K' for x in range(23, 26)}}                     # its roaring mouth, two fangs
    legs = []
    for side in (-1, 1):
        s = a if side < 0 else b                # this side's phase: 0 reaching, 1 gathered
        mx = lambda x: 24 + side * (x - 24)
        legs += [leg((mx(17), 15), (mx(11), 7 + s), (mx(9 - s), 30 - 2 * s)),
                 leg((mx(17), 19), (mx(14), 12 + s), (mx(13 + s), 30 - 2 * (1 - s)))]
    fore = [rect(18, 23, 21, 30 - 2 * a), rect(27, 23, 30, 30 - 2 * b)]
    ears = [(rect(17, 11, 18, 12), 'T'), (rect(30, 11, 31, 12), 'T')]
    return build(legs + [(abdomen, 'R', stripes(abdomen, (8, 11))), (rect(19, 21, 29, 25), 'T'),
                         (fore[0], 'T'), (fore[1], 'T')] + ears + [(mane, 'M'), (face, 'T', marks)])


def back(step):
    """Going from you: the mane's back, its tan rump, the abdomen raised over them."""
    a, b = (0, 1) if step == 0 else (1, 0)
    legs = []
    for side in (-1, 1):
        s = a if side < 0 else b
        mx = lambda x: 24 + side * (x - 24)
        legs += [leg((mx(17), 15), (mx(11), 7 + s), (mx(9 - s), 30 - 2 * s)),
                 leg((mx(17), 19), (mx(14), 12 + s), (mx(13 + s), 30 - 2 * (1 - s)))]
    fore = [rect(18, 23, 21, 30 - 2 * a), rect(27, 23, 30, 30 - 2 * b)]
    abdomen = ellipse(24, 10, 6, 4)
    ears = [(rect(17, 11, 18, 12), 'T'), (rect(30, 11, 31, 12), 'T')]
    return build(legs + [(rect(19, 21, 29, 25), 'T'), (fore[0], 'T'), (fore[1], 'T')] + ears +
                 [(ellipse(24, 17, 8, 6), 'M'), (abdomen, 'R', stripes(abdomen, (9, 12)))])


def side(step):
    """Its head to the left, its abdomen raised behind; its six ant legs splay back from behind the lion's body,
    the near three and the far three stepping by turns."""
    a, b = (0, 1) if step == 0 else (1, 0)
    hips = [(29, 18), (30, 19), (31, 18)]
    legs = [leg(h, (k + 1 * s, 10 + s), (f + 2 * s, 30 - 2 * s))
            for h, k, f, s in zip(hips, (25, 31, 36), (24, 32, 39), (a, b, a))]
    abdomen = ellipse(35, 10, 5, 5)
    body = ellipse(24, 21, 8, 3)
    mane = ellipse(15, 17, 6, 7)
    face = rect(8, 14, 14, 22) - {(8, 14), (8, 22)}
    marks = {(11, 15): 'K', (12, 16): 'K', (8, 17): 'K', **{(x, 19): 'K' for x in range(8, 13)},
             (9, 20): 'T', (10, 20): 'R', (11, 20): 'R', **{(x, 21): 'K' for x in range(9, 12)}}
    fore = [rect(14, 23, 16, 30 - 2 * a), rect(19, 23, 21, 30 - 2 * b)]
    return build(legs + [(line((31, 17), (33, 14)), 'R'), (abdomen, 'R', stripes(abdomen, (9, 12))), (body, 'T'),
                         (fore[1], 'T'), (rect(16, 9, 17, 10), 'T'), (mane, 'M'), (face, 'T', marks), (fore[0], 'T')])


FRAMES = {'D': [front(0), front(1)], 'U': [back(0), back(1)], 'L': [side(0), side(1)]}
FRAMES['R'] = [{(CW - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(25, 'myrmecoleon', FRAMES, PAL, cap=28, cell=(CW, CH))
    minis.chase_gif(25, CHASE, FRAMES, PAL, cell=(CW, CH))
