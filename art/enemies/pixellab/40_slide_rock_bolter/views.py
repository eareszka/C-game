"""40 Slide-Rock Bolter's new battle frame (the user, 2026-11-02: "just be rocky and mossy", then picked concept 2,
pixellab-out/40-concepts/sprites/v6/c2.png): the jaws-agape whale under a mantle of moss, side on.

Its flippers and fluke come off (legless; the user took the fluke off the last design and wanted the tail to end
like a snake's): the belly rests on the ground, the tail tapers up into a hook. Hide on stone greys, moss two flat
greens, throat and tongue the cast's two reds, teeth one cream, 8 colours plus black. The eye is one 2 px mark in a
black socket. Clumps of 3 px or fewer merge into what surrounds them; one black outline round it. Placed on the big
98x65 frame, its base on the bottom row.

    python art/enemies/pixellab/40_slide_rock_bolter/views.py     # writes frame0.png, frame0_x6.png
"""
from pathlib import Path
from collections import Counter
import colorsys
from PIL import Image

HERE = Path(__file__).parent
ROOT = HERE.parents[3]
SRC = ROOT / 'pixellab-out/40-concepts/sprites/v6/c2.png'
W, H = 98, 65
LIGHT, MID, DARK = 'a4aaba', '848694', '474751'
MOSS, MOSS_D = '4fa667', '2c6c44'
THROAT, TONGUE, TOOTH = '7c0a1b', 'b6433d', 'e8e0c0'
K = '000000'
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
SPARE = {TOOTH}


def fold(p):
    r, g, b = p
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h *= 360
    if s > 0.5 and h >= 280 and v < 0.3: return THROAT                           # the throat's dark plum, before black takes it
    if v < 0.12: return K
    if 60 <= h <= 150 and s > 0.4: return MOSS if v > 0.55 else MOSS_D           # moss
    if v < 0.28 and (h >= 280 or h < 20): return THROAT                          # the throat's dark plum
    if (h >= 280 or h < 30) and s > 0.3: return TONGUE if v > 0.7 else THROAT    # tongue and its folds
    if 15 <= h <= 50 and v > 0.6: return TOOTH if v > 0.8 else TONGUE            # teeth, gums
    if v > 0.45: return MID      # one stone and one shade: the pale third shade went when it was toned down
    return DARK


def load():
    im = Image.open(SRC).convert('RGBA')
    return {(x, y): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}


def belly(x):
    """The new underside, from the jaw's corner to the tail: straight runs between hand-placed points."""
    pts = [(38, 54), (50, 54), (60, 53), (68, 51), (74, 48), (79, 44), (83, 39)]
    for (a, ya), (b, yb) in zip(pts, pts[1:]):
        if a <= x <= b: return ya + (yb - ya) * (x - a) / (b - a)
    return None


def surgery(g):
    # the fluke off
    g = {p: c for p, c in g.items() if not (p[0] >= 68 and p[1] < 31)}
    # the flippers off: nothing under the belly line, the belly filled in up to where the hide was whole
    for x in range(38, 84):
        by = belly(x)
        for y in range(38, 64):
            if y > by: g.pop((x, y), None)
        if x >= 40:
            for y in range(max(43, round(by) - 12), round(by) + 1):
                if x < 77 and y >= 44 or x >= 77 and y >= round(by) - 2:
                    g[x, y] = DARK if y > by - 3 else MID
    # the tail, tapering up to a hook from under the moss
    spine = [(82 + (31 - y) * 0.18, y) for y in range(31, 14, -1)]
    for i, (cx, y) in enumerate(spine):
        half = max(0, 2.2 - i * 0.14)
        for x in range(round(cx - half), round(cx + half) + 1):
            g[x, y] = MID if x <= cx else DARK
    return g


CRACKS = [[(50, 36), (53, 38), (52, 41), (56, 43)], [(62, 45), (65, 47), (69, 46)], [(16, 15), (18, 17), (21, 16)]]


def rock(g):
    """What makes it stone: short angular black cracks across the hide, and a clump of moss on the tail's back
    instead of the band PixelLab left round it."""
    for x, y in [p for p, c in g.items() if c in (MOSS, MOSS_D) and p[0] >= 76 and p[1] >= 28]: g[x, y] = MID
    for line in CRACKS:
        for (a, ya), (b, yb) in zip(line, line[1:]):
            for t in range(max(abs(b - a), abs(yb - ya)) + 1):
                n = max(abs(b - a), abs(yb - ya)) or 1
                p = (round(a + (b - a) * t / n), round(ya + (yb - ya) * t / n))
                if g.get(p) in (LIGHT, MID, DARK): g[p] = K
    return g


GROUPS = ({MID, DARK}, {MOSS, MOSS_D}, {THROAT, TONGUE})


def smooth(g, passes=2):
    """Toned down (the user: "too detailed compared to other enemies"): each material's two shades by the 3x3
    majority, so their edges are plain shapes instead of ragged ones. Black and teeth stay."""
    for _ in range(passes):
        out = dict(g)
        for (x, y), c in g.items():
            grp = next((m for m in GROUPS if c in m), None)
            if not grp: continue
            n = Counter(g.get((x + a, y + b)) for a in (-1, 0, 1) for b in (-1, 0, 1))
            n = {k: v for k, v in n.items() if k in grp}
            out[x, y] = max(n, key=n.get)
        g = out
    return g


def flat(g, most=3):
    """Clumps of `most` px or fewer, 4-connected, into the colour most round them; black and teeth kept."""
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
        if c == K or c in SPARE or len(piece) > most: continue
        n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != K)
        if n:
            for a in piece: out[a] = n.most_common(1)[0][0]
    return out


def outline(g):
    """Outer black off, one closed black line round what is left."""
    edge = {p for p, c in g.items() if c == K and any((p[0] + dx, p[1] + dy) not in g for dx, dy in N4)}
    body = {p: c for p, c in g.items() if p not in edge}
    out = dict(body)
    for (x, y) in body:
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q not in body: out[q] = K
    return out


def teeth(g):
    """A few big plain teeth, as the cast has: flattening fused PixelLab's small ones into a band, so the band goes
    back to throat, the black fleck across the throat goes too, and triangles are stamped along each jaw."""
    mouth = {THROAT, TONGUE, TOOTH}
    for p, c in list(g.items()):
        if c == TOOTH: g[p] = THROAT
    for _ in range(2):
        for (x, y), c in list(g.items()):
            if c == K and 16 <= x <= 40 and 22 <= y <= 50 and sum(g.get((x + a, y + b)) in mouth for a, b in N4) >= 2:
                if all((x + a, y + b) in g for a, b in N4): g[x, y] = THROAT
    col = lambda x: [y for (a, y), c in g.items() if a == x and c in mouth]
    for x in (14, 19, 24, 29, 34):           # the upper jaw, points down
        y0 = min(col(x))
        for i in range(3):
            for u in range(x - (1 if i < 2 else 0), x + (2 if i < 2 else 1)):
                if g.get((u, y0 + i)) in mouth: g[u, y0 + i] = TOOTH
    for x in (20, 25, 30, 35):               # the lower jaw, points up
        y0 = max(col(x))
        for i in range(3):
            for u in range(x - (1 if i < 2 else 0), x + (2 if i < 2 else 1)):
                if g.get((u, y0 - i)) in mouth: g[u, y0 - i] = TOOTH
    return g


def eye(g):
    """One 2 px mark in a black socket."""
    for x in range(32, 36):
        for y in range(18, 21): g[x, y] = K
    g[33, 19] = g[34, 19] = TONGUE
    return g


def main():
    g = eye(rock(teeth(flat(smooth(flat(surgery(load()), 6)), 14))))
    g = outline(g)
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = (W - (max(xs) - min(xs) + 1)) // 2 - min(xs), H - 1 - max(ys)
    im = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        im.putpixel((x + dx, y + dy), tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,))
    im.save(HERE / 'frame0.png')
    bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(im)
    bg.resize((W * 8, H * 8), 0).save(HERE / 'frame0_x8.png')
    n = len(g)
    cols = Counter(g.values())
    inner = sum(1 for p, c in g.items() if c == K and all((p[0] + a, p[1] + b) in g for a, b in N4))
    print('bbox', im.getbbox(), 'colours', len(cols) - 1, '+ black', 'interior black %.1f%%' % (100 * inner / n), dict(cols))


main()
