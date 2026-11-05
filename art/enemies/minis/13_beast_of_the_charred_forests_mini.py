"""13 Beast of the Charred Forests' map mini: the eyeless coal beast stomping, four views at the game's ground-level camera, two frames each (tools/minis.py).

Drawn by PixelLab alone: side sprite at the mini's size and palette (pixellab-out/13-mini, s2; its head's orange mark, which read as an eye, painted out), front and back PixelLab's turns of it (tf2, tb1), each given a walk
(pixellab-out/13-mini-anim); side frames 0 and 2 (the tail's tip trimmed to fit the cell), front 0 and 3, back 0 and 4. The right view is the left mirrored. Three colours and black: coal grey, ember, white fangs. Its chase: the plod (chase_speed(), src/main.cpp), slow and heavy.

    python art/enemies/minis/13_beast_of_the_charred_forests_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / 'art/enemies/pixellab/13_beast_of_the_charred_forests/redo/mini'
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'G': '595965', 'E': 'fc9838', 'W': 'fcfcfc'}
CHASE = 'plod'
HEIGHT = 27
RGB = {k: tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) for k, c in PAL.items()}
N8 = ff.N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def logged(name):
    return [l.strip() for l in (HERE / name).read_text().splitlines() if l.strip().endswith('.png')]


def frame(path, side=False):
    im = Image.open(path).convert('RGBA')
    g = {}
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] > 127: g[x, y] = min(RGB, key=lambda k: sum((a - b) ** 2 for a, b in zip(RGB[k], p[:3])))
    left, pieces = set(g), []
    while left:                      # its body, the largest piece: PixelLab's stray specks go
        piece, todo = set(), [left.pop()]
        while todo:
            a = todo.pop(); piece.add(a)
            for d in N8:
                q = (a[0] + d[0], a[1] + d[1])
                if q in left: left.discard(q); todo.append(q)
        pieces.append(piece)
    g = {p: g[p] for p in max(pieces, key=len)}
    if side:                         # no eyes: orange above its jaws is coal
        top = min(y for x, y in g)
        for p, c in list(g.items()):
            if c == 'E' and p[1] < top + 10: g[p] = 'G'
    g = {p: c for p, c in g.items() if not (c == 'K' and any((p[0] + a, p[1] + b) not in g for a, b in ff.N4))}
    if side:                         # its tail tip: 35 columns of fill centre clear of the cell edges once outlined
        while max(x for x, y in g) - min(x for x, y in g) + 1 > 35:
            right = max(x for x, y in g)
            g = {p: c for p, c in g.items() if p[0] != right}
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = minis.W // 2 - (min(xs) + max(xs)) // 2, minis.H - 2 - max(ys)
    return ff.outline({(x + dx, y + dy): c for (x, y), c in g.items()})


L, Dn, Up = logged('anim_l.log'), logged('anim_d.log'), logged('anim_u.log')
LEFT = [frame(L[0], True), frame(L[2], True)]
RIGHT = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in LEFT]
FRAMES = {'D': [frame(Dn[0]), frame(Dn[3])], 'U': [frame(Up[0]), frame(Up[4])], 'L': LEFT, 'R': RIGHT}

if __name__ == '__main__':
    minis.make(13, 'beast_of_the_charred_forests', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(13, CHASE, FRAMES, PAL)
    for v, gs in FRAMES.items():
        print(v, [(max(x for x, y in g) - min(x for x, y in g) + 1, max(y for x, y in g) - min(y for x, y in g) + 1) for g in gs])
