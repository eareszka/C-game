"""40 Slide-Rock Bolter's flop (the user, 2026-11-02: "have it flop around uncomfortable"): PixelLab's animation of the
approved frame (pixellab-out/40-flop/animations/v1, 1 generation) on the frame's own colours, pixel by pixel to the
nearest of them. Frame 0 is the approved frame itself; PixelLab's frame 6 is its return to 0 and is left out.
Clumps of 2 px or fewer merge; one closed black outline; its base stays on the frame's bottom row.

    python art/enemies/pixellab/40_slide_rock_bolter/anim.py     # writes anim/flop_N.png, anim_review.png, flop.gif
"""
from pathlib import Path
from collections import Counter
from PIL import Image

HERE = Path(__file__).parent
ROOT = HERE.parents[3]
SRC = ROOT / 'pixellab-out/40-flop/animations/v1'
W, H = 98, 65
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
K = (0, 0, 0)
BASE = Image.open(HERE / 'frame0.png').convert('RGBA')
PAL = sorted({p[:3] for p in BASE.get_flattened_data() if p[3]})


def near(p):
    return min(PAL, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, p)))


def flat(g, most=2, keep=((232, 224, 192),)):
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
        if c == K or c in keep or len(piece) > most: continue
        n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != K)
        if n:
            for a in piece: out[a] = n.most_common(1)[0][0]
    return out


def biggest(g):
    left, best = set(g), set()
    while left:
        piece, todo = set(), [left.pop()]
        while todo:
            a = todo.pop(); piece.add(a)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                q = (a[0] + dx, a[1] + dy)
                if q in left: left.discard(q); todo.append(q)
        if len(piece) > len(best): best = piece
    return {p: g[p] for p in best}


def outline(g):
    edge = {p for p, c in g.items() if c == K and any((p[0] + dx, p[1] + dy) not in g for dx, dy in N4)}
    body = {p: c for p, c in g.items() if p not in edge}
    out = dict(body)
    for x, y in body:
        for dx, dy in N4:
            if (x + dx, y + dy) not in body: out[x + dx, y + dy] = K
    return out


STONE, RED = (0x84, 0x86, 0x94), (0xb6, 0x43, 0x3d)
INNER = lambda g, p: all((p[0] + dx, p[1] + dy) in g for dx, dy in N4)


def jaws(g, i):
    """Frame 4, its jaws nearly shut, came back a mush of teeth: the mouth one flat throat, a few plain teeth on it."""
    if i != 4: return g
    THROAT, TOOTH = (0x7c, 0x0a, 0x1b), (0xe8, 0xe0, 0xc0)
    mouth = [p for p, c in g.items() if c in (THROAT, TOOTH, RED) and p[0] < 40]
    for p in mouth: g[p] = THROAT
    for x in range(min(p[0] for p in mouth) + 2, max(p[0] for p in mouth), 5):
        col = [y for a, y in mouth if a == x]
        if col:
            for u in (x, x + 1):
                if (u, min(col)) in g and g[u, min(col)] == THROAT: g[u, min(col)] = TOOTH
    return g


def tail(g, i):
    """PixelLab keeps starting a fluke: nothing of the tail below its own underside past the tip (the user has
    taken the fluke off twice). Only frame 4 needs it."""
    if i != 4: return g
    return {p: c for p, c in g.items() if not (p[0] >= 86 and p[1] >= 57)}


def eye(g, i):
    """PixelLab shut the eye to a curved lid after frame 1. Every enemy keeps its 1-2 px mark: the lid is the inner
    black nearest where the eye was, carried with the head, and becomes the same socket and mark as frame 0."""
    if i < 2: return g
    top = min(y for x, y in g)
    near_eye = [p for p, c in g.items() if c == K and INNER(g, p) and 27 <= p[0] <= 38 and top + 8 <= p[1] <= top + 20]
    if near_eye:
        cx = round(sum(x for x, y in near_eye) / len(near_eye)); cy = round(sum(y for x, y in near_eye) / len(near_eye))
    else:
        cx, cy = 29, top + 15                # frame 4 drew no lid: where its neighbours' eye is, the head leaning left
    for p in near_eye: g[p] = STONE
    for x in range(cx - 2, cx + 2):
        for y in range(cy - 1, cy + 2): g[x, y] = K
    g[cx - 1, cy] = g[cx, cy] = RED
    return g


def frame(i):
    if i == 0: return BASE.copy()
    im = Image.open(SRC / f'flop-{i:02d}.png').convert('RGBA')
    g = {(x, y): near(im.getpixel((x, y))[:3]) for y in range(H) for x in range(W) if im.getpixel((x, y))[3] > 127}
    g = outline(flat(biggest(g)))
    g = outline(eye(jaws(tail(g, i), i), i))
    drop = H - 1 - max(y for x, y in g)                # its base on the bottom row
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= y + drop < H and 0 <= x < W: out.putpixel((x, y + drop), c + (255,))
    return out


FRAMES = [frame(i) for i in range(6)]
(HERE / 'anim').mkdir(exist_ok=True)
for i, f in enumerate(FRAMES): f.save(HERE / 'anim' / f'flop_{i}.png')

if __name__ == '__main__':
    S, GREEN = 5, (0x6f, 0x9e, 0x5c, 255)
    b = Image.new('RGBA', (W * S * 3, H * S * 2), GREEN)
    for i, f in enumerate(FRAMES):
        b.alpha_composite(f.resize((W * S, H * S), 0), ((i % 3) * W * S, (i // 3) * H * S))
        cols = Counter(p[:3] for p in f.get_flattened_data() if p[3])
        print(i, f.getbbox(), len(cols) - 1, 'colours + black')
    b.save(HERE / 'anim_review.png')
    big = []
    for f in FRAMES:
        bg = Image.new('RGBA', (W, H), GREEN); bg.alpha_composite(f)
        big.append(bg.resize((W * 4, H * 4), 0))
    big[0].save(HERE / 'flop.gif', save_all=True, append_images=big[1:], duration=120, loop=0, disposal=1)
