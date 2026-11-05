"""40 Slide-Rock Bolter's map mini: the rock-hided, moss-backed whale, stranded on land and hating it -- at the player's
scale (51 px drawn in battle x 28/79 = 18, a little more as PixelLab drew it), four views, two frames (tools/minis.py).

Through PixelLab (art/enemies/pixellab/40_slide_rock_bolter/mini, pixellab-out/40-mini-v2, four generations): its
approved battle frame sent at mini size, rotated, then front (south-east: head on), back (north-west) and side
(south-west) given its flop. Each frame is one of those on the mini's palette pixel for pixel, not rescaled, one black
outline round it. PixelLab's whale spout is dropped (only its largest piece kept). Its back is the front's own body
with the face off and the tail on the other side, as PixelLab's was half as tall again as its front. The right
view is the left mirrored. Three of its battle colours and black: stone, moss, the throat's dark red; the teeth take
the stone.

It has no legs. Frame 0 lies slumped, jaws shut to a line; frame 1 is heaved up, jaws agape.

Its chase: the flop (chase_speed(), src/main.cpp), as its battle animation: a heave, then lying there, each veering
the other way.

    python art/enemies/minis/40_slide_rock_bolter_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'S': '848694', 'G': '4fa667', 'R': '7c0a1b'}
CHASE = 'flop'
HEIGHT = 25                              # the side, reared up; the front is 20
SRC = ROOT / 'pixellab-out/40-mini-v2/40/animations'
RUNS = {'D': ('v2/flopd', (3, 0)), 'L': ('v3/flopl', (3, 0))}


def tone(h, s, v):
    """Darks black; greens moss; reds the throat and tongue; everything else, teeth too, stone."""
    if v < 0.2: return 'K'
    if s > 0.15 and 90 <= h <= 170: return 'G'
    if s > 0.3 and (h >= 330 or h <= 25): return 'R'
    return 'S'


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


def place(g):
    edge = {p for p, c in g.items() if c == 'K' and any((p[0] + dx, p[1] + dy) not in g for dx, dy in ff.N4)}
    s = {p: c for p, c in g.items() if p not in edge}
    xs, ys = [x for x, y in s], [y for x, y in s]
    dx, dy = minis.W // 2 - (min(xs) + max(xs)) // 2, minis.H - 2 - max(ys)
    return ff.outline({(x + dx, y + dy): c for (x, y), c in s.items()})


def mirror(g):
    return {(minis.W - 1 - x, y): c for (x, y), c in g.items()}


SCALLOP = (0, 1, 2, 1)         # the moss's lower edge, its ragged hang


def back(front):
    """The front's body from behind: mirrored so the tail goes the other way, the face off, moss over the top of its
    dome with a ragged lower edge (the side's own mantle), stone under it."""
    m = mirror(front)
    ys = [y for x, y in m]
    top, bot = min(ys), max(ys)
    x1 = max(x for x, y in m if y >= top + 3 and y <= top + 8)
    out = {}
    for (x, y), c in m.items():
        edge = any((x + dx, y + dy) not in m for dx, dy in ff.N4)
        moss = x >= x1 - 17 and y <= top + (bot - top) * 0.55 + SCALLOP[x % 4]
        out[x, y] = 'K' if edge else 'G' if moss else 'S'
    return out


def cap(g):
    """The front's moss cap, down over its brow as in battle: PixelLab left it thin at this size."""
    top = min(y for x, y in g)
    right = max(x for x, y in g if y == top + 2) + 3       # short of the tail
    out = dict(g)
    for (x, y), c in g.items():
        if c != 'K' and x < right and y <= top + 3 + SCALLOP[x % 4]: out[x, y] = 'G'
    return out


def teeth(g):
    """Jaws open, teeth along both: the stone, each second and third column of the red's top and bottom."""
    out = dict(g)
    xs = sorted({x for (x, y), c in g.items() if c == 'R'})
    for x in xs[1::3]:
        col = [y for (a, y), c in g.items() if a == x and c == 'R']
        for u in (x, x + 1):
            if g.get((u, min(col))) == 'R': out[u, min(col)] = 'S'
            if g.get((u, max(col))) == 'R': out[u, max(col)] = 'S'
    return out


RAW = {v: frames(*RUNS[v]) for v in RUNS}
FRAMES = {v: [place(g) for g in RAW[v]] for v in RAW}
FRAMES['D'] = [cap(g) for g in FRAMES['D']]
FRAMES['D'][1], FRAMES['L'][1] = teeth(FRAMES['D'][1]), teeth(FRAMES['L'][1])
FRAMES['U'] = [back(g) for g in FRAMES['D']]
FRAMES['R'] = [mirror(g) for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(40, 'slide_rock_bolter', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(40, CHASE, FRAMES, PAL)
