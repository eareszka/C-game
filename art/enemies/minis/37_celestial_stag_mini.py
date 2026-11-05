"""37 Celestial Stag's map mini: the spectral stag of the shard caves -- purple, tall branching antlers that burn
in the cave torches' rainbow, a wispy lilac tail -- at the player's scale, four views, two frames (tools/minis.py).

Through PixelLab as 35's and 36's were (art/enemies/pixellab/37_celestial_stag/mini, pixellab-out/37-mini, four
generations): its approved battle front three-quarter sent small (28 px), so PixelLab draws it at about the mini's
size, rotated to eight views, then its front (south-west), back (north-east) and side (west: head to the left)
each given a high-stepping trot. Each mini frame is one of those on the mini's palette (minis.recolour) pixel for
pixel, its own black lines kept, scaled in blocks by one SCALE for every view so its thin legs and antler tines
stay joined, one black outline round it. Only its body, the largest piece, kept. The right view is the left
mirrored. Three of its battle colours and black: the cave purple of its coat, the lilac of its tail, and the
torch flame's yellow for its antlers (one stripe of the rainbow: three colours is the overworld's limit).

Its chase: the pounce (chase_speed(), chase_frame(), src/main.cpp), from its lore: it begs the miners to carry it
up and, refused, attacks -- it waits, then lunges.

    python art/enemies/minis/37_celestial_stag_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'P': '664b95', 'L': 'b69cee', 'Y': 'fae488'}
CHASE = 'pounce'
HEIGHT = 26
SRC = ROOT / 'pixellab-out/37-mini/animations'
RUNS = {'D': ('v1/rund', (0, 2)), 'U': ('v2/runu', (0, 2)), 'L': ('v3/runl', (0, 2))}   # stepping, gathered
NO_HORNS = set()         # views whose frames keep nothing above their first frame's head: none


def tone(h, s, v):
    """Its darks black; its purples by brightness, the pale lilac of its tail over the coat; every other hue (the
    antlers' rainbow) the flame yellow."""
    if v < 0.16: return 'K'
    if 230 <= h <= 320 or s < 0.15: return 'L' if v > 0.65 else 'P'
    return 'Y'


def biggest(g):
    """Only its largest 8-connected piece: PixelLab's stray specks dropped."""
    left, best = set(g), set()
    while left:
        piece, todo = set(), [left.pop()]
        while todo:
            p = todo.pop(); piece.add(p)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (p[0] + dx, p[1] + dy)
                    if q in left: left.discard(q); todo.append(q)
        if len(piece) > len(best): best = piece
    return {p: g[p] for p in best}


def frames(name, picks, v):
    letters = {tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)): k for k, c in PAL.items()}
    gs = []
    for i in picks:
        im = minis.recolour(Image.open(SRC / f'{name}-{i:02d}.png').convert('RGBA'), tone, PAL)
        gs.append(biggest({(x, y): letters[im.getpixel((x, y))[:3]] for y in range(im.height) for x in range(im.width)
                           if im.getpixel((x, y))[3]}))
    if v in NO_HORNS:
        top = min(y for x, y in gs[0])
        gs = [{p: c for p, c in g.items() if p[1] >= top} for g in gs]
    return gs


RAW = {v: frames(*RUNS[v], v) for v in RUNS}
SCALE = (HEIGHT - 2) / max(max(y for x, y in g) - min(y for x, y in g) + 1 for gs in RAW.values() for g in gs)


def place(g):
    """Scaled by SCALE in blocks -- a pixel drawn wherever its block holds any drawing, its most common colour
    (black only where the block is all black), so its thin legs stay joined to their hooves (nearest
    sampling skipped them) -- its outer black taken off and the outline redrawn, its feet on the cell's last but
    one row, centred."""
    from collections import Counter
    xs, ys = [x for x, y in g], [y for x, y in g]
    x0, y0 = min(xs), min(ys)
    w, h = round((max(xs) - x0 + 1) * SCALE), round((max(ys) - y0 + 1) * SCALE)
    s = {}
    for y in range(h):
        for x in range(w):
            blk = [g[q] for q in ((x0 + i, y0 + j) for j in range(int(y / SCALE), max(int(y / SCALE) + 1, int((y + 1) / SCALE)))
                                  for i in range(int(x / SCALE), max(int(x / SCALE) + 1, int((x + 1) / SCALE)))) if q in g]
            if blk:
                n = Counter(c for c in blk if c != 'K')
                s[x, y] = n.most_common(1)[0][0] if n else 'K'
    edge = {p for p, c in s.items() if c == 'K' and any((p[0] + dx, p[1] + dy) not in s for dx, dy in ff.N4)}
    s = {p: c for p, c in s.items() if p not in edge}
    xs, ys = [x for x, y in s], [y for x, y in s]
    dx, dy = minis.W // 2 - (min(xs) + max(xs)) // 2, minis.H - 2 - max(ys)
    return ff.outline({(x + dx, y + dy): c for (x, y), c in s.items()})


FRAMES = {v: [place(g) for g in RAW[v]] for v in RAW}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(37, 'celestial_stag', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(37, CHASE, FRAMES, PAL)
