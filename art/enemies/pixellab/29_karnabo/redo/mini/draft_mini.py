"""29 Karnabo's new map mini, DRAFT (art/enemies/minis/29_* stays until the user approves): the robed quarry bogey gliding, four views at the game's ground-level camera, two frames each (tools/minis.py).

Drawn by PixelLab alone: front sprite at the mini's size and palette (pixellab-out/29-mini, f2), side and back PixelLab's turns of it (ts2, tb2), each given a glide (pixellab-out/29-mini-anim); frames 0 and 1 of each. The right view is the left mirrored.
Three colours and black: skin green, robe slate, eyes yellow. Its chase: the meander (chase_speed(), src/main.cpp), its pace rising and falling, a stalker's creep. A strip of its own, 40x32: its hood rises over a standard cell.

    python art/enemies/pixellab/29_karnabo/redo/mini/draft_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'G': '4fa667', 'S': '474751', 'Y': 'f0bc3c'}
CHASE = 'meander'
HEIGHT = 30
CW, CH = 40, 32
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
    g = {p: c for p, c in g.items() if not (c == 'K' and any((p[0] + a, p[1] + b) not in g for a, b in ff.N4))}
    while max(x for x, y in g) - min(x for x, y in g) + 1 > 35:   # its hands' tips, to clear the cell's edges
        g = {p: c for p, c in g.items() if p[0] != max(x for x, y in g)}
        if max(x for x, y in g) - min(x for x, y in g) + 1 > 35: g = {p: c for p, c in g.items() if p[0] != min(x for x, y in g)}
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = CW // 2 - (min(xs) + max(xs)) // 2, CH - 2 - max(ys)
    return ff.outline({(x + dx, y + dy): c for (x, y), c in g.items()})


Dn, Up, L = logged('anim_d.log'), logged('anim_u.log'), logged('anim_l.log')
LEFT = [frame(L[0]), frame(L[1])]
RIGHT = [{(CW - 1 - x, y): c for (x, y), c in g.items()} for g in LEFT]
FRAMES = {'D': [frame(Dn[0]), frame(Dn[1])], 'U': [frame(Up[0]), frame(Up[1])], 'L': LEFT, 'R': RIGHT}

if __name__ == '__main__':
    minis.HERE = HERE / 'draft'
    minis.make(29, 'karnabo', FRAMES, PAL, cap=HEIGHT, cell=(CW, CH))
    minis.chase_gif(29, CHASE, FRAMES, PAL, cell=(CW, CH))
    for v, gs in FRAMES.items():
        print(v, [(max(x for x, y in g) - min(x for x, y in g) + 1, max(y for x, y in g) - min(y for x, y in g) + 1) for g in gs])
