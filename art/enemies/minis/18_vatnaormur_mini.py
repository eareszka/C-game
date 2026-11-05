"""18 Vatnaormur's map mini, redone with its battle sprite (the user, 2026-11-02): the slug-faced serpent, symmetrical,
looking straight down. The old mini is kept in art/enemies/pixellab/18_vatnaormur/mini/old/.

The user's standing wishes for this mini (2026-10-14) stay: big and intimidating, near its battle size, one drawing in all
four views, moving pretty much straight. So 42 px tall on an 80x48 canvas with a strip of its own (assets/enemies/minis_18.png).

Through PixelLab (art/enemies/pixellab/18_vatnaormur/mini, pixellab-out/18-mini, one generation): its battle frame sent at this
size and given a surge. Frame 0 lies low, frame 1 its body heaved up, on the mini's palette, mirrored from the left half so
it stays exactly symmetrical. One black outline. Submerged as the old mini was (the user): its lower body cut at the waterline, its lake under it with a clean
edge, in the old mini's lake blue; the second frame sinks a pixel as it surges. Peach, dark grey, lake blue and black: the bible's three.

Its chase: straight at you, at the chase pace (the default in chase_speed(), src/main.cpp), as before.

    python art/enemies/minis/18_vatnaormur_mini.py
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'P': 'f0b890', 'D': '34343e', 'W': '3e91cc'}
CHASE = 'straight'
CW, CH = 80, 48
HEIGHT = 44
SRC = next((ROOT / 'pixellab-out/18-mini').rglob('surge-00.png')).parent
PICKS = (1, 4)
N4 = ff.N4


def fold(p):
    if sum(p) < 95: return 'K'
    r, g, b = p
    if r < 110: return 'D'                                  # the greys
    return 'P'                                              # peach and its salmon shade alike: one flat slug


def flat(g, most=2):
    seen, out = set(), dict(g)
    for p, c in g.items():
        if p in seen: continue
        piece, todo = {p}, [p]
        while todo:
            a = todo.pop()
            for dx, dy in N4:
                q = (a[0] + dx, a[1] + dy)
                if q not in piece and g.get(q) == c: piece.add(q); todo.append(q)
        seen |= piece
        if c == 'K' or len(piece) > most: continue
        n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != 'K')
        if n:
            for a in piece: out[a] = n.most_common(1)[0][0]
    return out


def frame(i):
    im = Image.open(SRC / f'surge-{i:02d}.png').convert('RGBA')
    g = {(x, y): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    xs = [x for x, y in g]
    # its own middle: the head's centre, found on the stalks' row span
    mid2 = min(xs) + max(xs)
    left = flat({p: c for p, c in g.items() if p[0] * 2 <= mid2})
    both = dict(left)
    for (x, y), c in left.items(): both[mid2 - x, y] = c
    edge = {p for p, c in both.items() if c == 'K' and any((p[0] + a, p[1] + b) not in both for a, b in N4)}
    body = {p: c for p, c in both.items() if p not in edge}
    xs, ys = [x for x, y in body], [y for x, y in body]
    dx, dy = CW // 2 - (min(xs) + max(xs)) // 2, CH - 2 - max(ys)
    placed = {(x + dx, y + dy): c for (x, y), c in body.items()}
    return placed


WATERLINE = CH - 8           # rows from here down are under the lake
RX, RY = 34, 6               # the lake's half width and half height
SINK = (0, 1)                # frame: rows it has sunk


def submerged(g, f):
    """Its lower body gone under: cut at the waterline, the lake's clean oval below, one black outline round all of it."""
    above = {(x, y + SINK[f]): c for (x, y), c in g.items() if y + SINK[f] < WATERLINE}
    cx, cy = CW // 2, CH - 2 - RY
    lake = {}
    for y in range(cy - RY, cy + RY + 1):
        for x in range(cx - RX, cx + RX + 1):
            if ((x - cx) / RX) ** 2 + ((y - cy) / RY) ** 2 < 1: lake[x, y] = 'W'
    lake.update(above)
    return ff.outline(lake)


pics = [submerged(frame(i), f) for f, i in enumerate(PICKS)]
FRAMES = {v: pics for v in 'DULR'}      # one drawing every way (the user)

if __name__ == '__main__':
    minis.make(18, 'vatnaormur', FRAMES, PAL, cap=HEIGHT, cell=(CW, CH))
    minis.chase_gif(18, CHASE, FRAMES, PAL, cell=(CW, CH))
