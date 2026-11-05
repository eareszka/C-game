"""31 Man-Eating Boulder's map mini: the living rock shuffling, its jaws chomping, four views at the game's ground-level camera, two frames each (tools/minis.py).

Drawn by PixelLab alone: front sprite at the mini's size and palette (pixellab-out/31-mini, f1), side and back PixelLab's turns of it (ts2, tb2), red flecks on the stone cleaned before animating, each given a heaving shuffle (pixellab-out/31-mini-anim);
front and side frames 0 and 3, open and shut; back 0 and 2. The right view is the left mirrored. Three colours and black: stone grey, moss green, gullet red. No legs, so its chase is the roll (chase_speed(), src/main.cpp): kicked off fast, rolling out.

    python art/enemies/minis/31_man_eating_boulder_mini.py
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / 'art/enemies/pixellab/31_man_eating_boulder/redo/mini'
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'G': '848694', 'M': '4fa667', 'R': '7c0a1b'}
CHASE = 'roll'
HEIGHT = 27
RGB = {k: tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) for k, c in PAL.items()}
N8 = ff.N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def logged(name):
    return [l.strip() for l in (HERE / name).read_text().splitlines() if l.strip().endswith('.png')]


def frame(path):
    im = Image.open(path).convert('RGBA')
    g = {}
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] > 127: g[x, y] = min(RGB, key=lambda k: sum((a - b) ** 2 for a, b in zip(RGB[k], p[:3])))
    left, pieces = set(g), []
    while left:
        piece, todo = set(), [left.pop()]
        while todo:
            a = todo.pop(); piece.add(a)
            for d in N8:
                q = (a[0] + d[0], a[1] + d[1])
                if q in left: left.discard(q); todo.append(q)
        pieces.append(piece)
    g = {p: g[p] for p in max(pieces, key=len)}
    seen = set()
    for p, c in list(g.items()):     # small red flecks are stone: red belongs in the mouth
        if p in seen or c != 'R': continue
        piece, todo = {p}, [p]
        while todo:
            a = todo.pop()
            for d in ff.N4:
                q = (a[0] + d[0], a[1] + d[1])
                if q not in piece and g.get(q) == 'R': piece.add(q); todo.append(q)
        seen |= piece
        if len(piece) <= 4:
            for a in piece: g[a] = 'G'
    g = {p: c for p, c in g.items() if not (c == 'K' and any((p[0] + a, p[1] + b) not in g for a, b in ff.N4))}
    while max(x for x, y in g) - min(x for x, y in g) + 1 > 35:   # the rubble's tips, to clear the cell's edges
        g = {p: c for p, c in g.items() if p[0] != max(x for x, y in g)}
        if max(x for x, y in g) - min(x for x, y in g) + 1 > 35: g = {p: c for p, c in g.items() if p[0] != min(x for x, y in g)}
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = minis.W // 2 - (min(xs) + max(xs)) // 2, minis.H - 2 - max(ys)
    return ff.outline({(x + dx, y + dy): c for (x, y), c in g.items()})


Dn, Up, L = logged('anim_d.log'), logged('anim_u.log'), logged('anim_l.log')
LEFT = [frame(L[0]), frame(L[3])]
RIGHT = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in LEFT]
FRAMES = {'D': [frame(Dn[0]), frame(Dn[3])], 'U': [frame(Up[0]), frame(Up[2])], 'L': LEFT, 'R': RIGHT}

if __name__ == '__main__':
    minis.make(31, 'man_eating_boulder', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(31, CHASE, FRAMES, PAL)
    for v, gs in FRAMES.items():
        print(v, [(max(x for x, y in g) - min(x for x, y in g) + 1, max(y for x, y in g) - min(y for x, y in g) + 1) for g in gs])
