"""68 Shuyu's wingbeat (the flap sheet, phase 2), drawn by hand: PixelLab's animations kept its wings folded
twice (the user chose a hand-drawn beat). Each view's still pose with a red wing spread from each shoulder in
three poses -- up, out, down -- played up, out, down, out (FLAP_FRAMES in src/battle.cpp: wings up, mid,
down, mid). A near wing is drawn over the body with its own outline; a far one only where the body leaves
room, behind it. Seen from behind, the tail fan goes on last, over the wings too (backs.py; the user).
Writes flap_anim_<view>_1..4.png, which the job's map takes in order.

    python art/enemies/pixellab/68_shuyu/wings.py
"""
from pathlib import Path
from PIL import Image

import backs

HERE = Path(__file__).resolve().parent
PAL = {'P': (0xec, 0x84, 0x76), 'M': (0xb6, 0x43, 0x3d), 'D': (0x79, 0x27, 0x27)}
BLACK = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
# A left wing, fill only: its last column is the shoulder, `row` the row of the grid at the shoulder.
UP = (4, [
    'PP.......',
    'PMMP.....',
    '.MMMMP...',
    '.DMMMMMP.',
    '..DDMMMMM',
    '....DDMMM',
])
OUT = (2, [
    '.PPPPPPP.',
    'PMMMMMMMM',
    'MMMMMMMMM',
    'DMDMDMMMM',
    '.D.D.DDD.',
])
DOWN = (0, [
    '....PPPMM',
    '..PMMMMMM',
    '.MMMMMMD.',
    '.MMMMDD..',
    'DMMDD....',
    '.DD......',
])
BEAT = (UP, OUT, DOWN, OUT)
# Each view: its still pose, then (shoulder x, y, which way the wing points, near or far).
VIEWS = {
    'D':  ('idle_frame0_clean.png', [((16, 21), 'left', True), ((34, 21), 'right', True)]),
    'U':  ('idle_view_U.png',       [((15, 21), 'left', True), ((33, 21), 'right', True)]),
    'DR': ('idle_view_DR.png',      [((21, 22), 'left', True), ((36, 21), 'right', False)]),
    'UR': ('idle_view_UR.png',      [((21, 22), 'left', True), ((36, 21), 'right', False)]),
    'R':  ('idle_view_R.png',       [((26, 19), 'left', True), ((28, 17), 'left', False)]),   # it faces right: from the top of its back, sweeping back
}


def wing(pose, shoulder, way):
    row, rows = pose
    w = len(rows[0])
    g = {}
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c == '.':
                continue
            gx = x if way == 'left' else w - 1 - x
            px = shoulder[0] - (w - 1) + gx if way == 'left' else shoulder[0] + gx
            g[px, shoulder[1] - row + y] = c
    return g


def paint(im, g, near):
    out = im.copy()
    clear = lambda p: 0 <= p[0] < im.width and 0 <= p[1] < im.height and not im.getpixel(p)[3]
    for (x, y) in g:
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q not in g and 0 <= q[0] < im.width and 0 <= q[1] < im.height and (near or clear(q)):
                out.putpixel(q, BLACK + (255,))
    for p, c in g.items():
        if 0 <= p[0] < im.width and 0 <= p[1] < im.height and (near or clear(p)):
            out.putpixel(p, PAL[c] + (255,))
    return out


if __name__ == '__main__':
    for v, (still, wings) in VIEWS.items():
        base = Image.open(HERE / still).convert('RGBA')
        for i, pose in enumerate(BEAT, 1):
            im = base
            for shoulder, way, near in sorted(wings, key=lambda w: w[2]):     # far wings first, behind
                im = paint(im, wing(pose, shoulder, way), near)
            if v in backs.VIEWS:                                            # seen from behind: the tail over all
                im = backs.fan(im, backs.VIEWS[v][1])
            im.save(HERE / f'flap_anim_{v}_{i}.png')
        print(v, 'flap', im.getbbox())
