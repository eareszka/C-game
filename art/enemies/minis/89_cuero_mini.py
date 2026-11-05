"""89 Cuero's map mini: the living stretched cowhide with its clawed rim, at the player's scale (46 px drawn in battle
x 28/79 = 16, a little more as PixelLab drew it), four views, two frames (tools/minis.py).

Through PixelLab (art/enemies/pixellab/89_cuero/mini, pixellab-out/89-mini, four generations): its approved battle frame
sent at mini size, rotated, then front (south), back (north) and side (south-west) given a creeping ripple. Each frame
is one of those on the mini's palette pixel for pixel, not rescaled, its largest piece only (PixelLab's stray antenna
bits dropped; only frames without antennae used), one black outline round it. The back's second frame had grown a
face: its marks taken off. The right view is the left mirrored. Three of its battle colours and black: cream, shade,
claw maroon; the eyes black, on its pale skin.

It has no legs. Frame 0 is gathered up, frame 1 stretched out reaching.

Its chase: the inch (chase_speed(), src/main.cpp), as the Wapaloosie's -- reaching out, then humped up gathering, which
is how a flat hide creeps.

    python art/enemies/minis/89_cuero_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'H': 'fce4a0', 'S': 'b2966a', 'C': '792727'}
CHASE = 'inch'
HEIGHT = 21
SRC = ROOT / 'pixellab-out/89-mini/89/animations'
RUNS = {'D': ('v1/ripd', (4, 0)), 'U': ('v2/ripu', (1, 0)), 'L': ('v3/ripl', (3, 0))}


def tone(h, s, v):
    if v < 0.22: return 'K'
    if v < 0.6 and (h > 330 or h < 20) and s > 0.3: return 'C'
    return 'H' if v > 0.85 else 'S'


def biggest(g):
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


def frames(name, picks):
    letters = {tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)): k for k, c in PAL.items()}
    gs = []
    for i in picks:
        im = minis.recolour(Image.open(SRC / f'{name}-{i:02d}.png').convert('RGBA'), tone, PAL)
        gs.append(biggest({(x, y): letters[im.getpixel((x, y))[:3]] for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3]}))
    return gs


def faceless(g):
    """No marks on its back: every black pixel fully inside it becomes hide."""
    return {p: ('H' if c == 'K' and all((p[0] + a, p[1] + b) in g for a, b in ff.N4) else c) for p, c in g.items()}


def place(g):
    edge = {p for p, c in g.items() if c == 'K' and any((p[0] + dx, p[1] + dy) not in g for dx, dy in ff.N4)}
    s = {p: c for p, c in g.items() if p not in edge}
    xs, ys = [x for x, y in s], [y for x, y in s]
    dx, dy = minis.W // 2 - (min(xs) + max(xs)) // 2, minis.H - 2 - max(ys)
    return ff.outline({(x + dx, y + dy): c for (x, y), c in s.items()})


RAW = {v: frames(*RUNS[v]) for v in RUNS}
RAW['U'] = [faceless(g) for g in RAW['U']]
FRAMES = {v: [place(g) for g in RAW[v]] for v in RAW}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(89, 'cuero', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(89, CHASE, FRAMES, PAL)
