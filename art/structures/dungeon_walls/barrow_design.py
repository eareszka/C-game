"""The stonehenge barrow's maze walls: the user's reference is Mother 1's ice
maze -- free-standing walls one block thick, a lit top, a front face, the
walls running east-west and back at 45 degrees -- built here as the user had
it: stone blocks with the overworld's grass on top, nothing below the floor.

    python art/structures/dungeon_walls/barrow_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/dungeon_walls/barrow

A block measured off the reference at its own pixels: 32 wide, 16 deep, 64
tall, in the game's oblique (x + d, B - z - d). Each face is sampled from a
swatch by where it is -- the front by (X, z), its joints every 32 so the
blocks show as the reference's do; the side by (d, z); the top by its screen
pixel, as the overworld's ground is laid -- and the black line falls on the
walls' outline, where faces meet, and down every joint.

    front   96 x 64   the stone, in the stonehenge stones' lit grey (pale, as
                      by a moon -- user: surreal, in the game's palette): two
                      courses a block, one stone over two, a crack, roots,
                      the grass's lip
    carvings 24 x 24  each: spiral, rings round a cup, zigzags, triple spiral,
                      an eye -- laid on a stone here and there
    stars, const_*    the sky the maze stands in (user: starry, moonlit): two
                      chunky stars, and constellations shaped like the game's
                      cryptids, from their carved icons
The grass is the overworld's own cells, laid moonlit: its two greens mapped to
the palette's cooler two.
    top     96 x 48   plain grass; over it the overworld's own blades
    tufts             (tileset 18-20, 2-3, user: match it), bunch by bunch,
                      gathered into thick patches, each only where it fits
                      whole on a top
    side    48 x 64   the stone in shade

Tones -- four a 16px cell, one palette: K line, M stone, D its shade, S the
side in shade (the stonehenge stones' three greys), G grass (the
overworld's), E dark grass (its blades).
"""
import json, math, os, random, sys
from PIL import Image

PAL = {'K': '000000', 'M': 'c6ccda', 'D': '9797aa', 'S': '595965', 'G': '4fa667', 'E': '235436'}
# the overworld grass's own colours, read off its cells and laid moonlit
OVERWORLD_GRASS = {'K': '000000', 'G': '4edc4a', 'E': '00881b'}
VW, VH = 96, 64
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')


def lip(g, w):
    """The grass over the top edge: the overworld's dark blades, hanging."""
    for x in range(w):
        n = 2 + int(1.5 + 1.5 * math.sin(2 * math.pi * x / 24))
        for y in range(n):
            g[y][x] = 'E'
        if x % 7 in (2, 5):
            g[n][x] = 'E'


def front():
    """Stone blocks, 32 wide: two courses, one stone over two (the
    reference's bond), each stone shaded along its lower right edge, the
    joints black; a crack in one block of three, roots from the grass in
    another. Rows from the top (z = 63) to the foot (z = 0)."""
    g = [['M'] * VW for _ in range(VH)]
    for y in range(VH):
        for x in range(VW):
            bx = x % 32
            if y == 31 or bx == 31 or (y > 31 and bx == 15):
                g[y][x] = 'K'                                  # the joints
    for x0 in range(0, VW, 32):
        for (a, b, y0, y1) in ((x0, x0 + 30, 0, 30), (x0, x0 + 14, 32, 63), (x0 + 16, x0 + 30, 32, 63)):
            for x in range(a, b + 1):
                for y in (y1 - 1, y1):
                    g[y][x] = 'D'
            for y in range(y0, y1 + 1):
                for x in (b - 1, b):
                    g[y][x] = 'D'
    x = 32 + 19                                                # a crack down the second block
    for y in range(6, 26):
        g[y][x] = 'K'
        x += 1 if y % 5 == 0 else -1 if y % 7 == 0 else 0
    for rx, n in ((64 + 5, 9), (64 + 11, 5), (64 + 26, 11)):  # roots down the third
        for y in range(4, 4 + n):
            g[y][rx + (1 if (y // 4) % 2 else 0)] = 'E'
    lip(g, VW)
    return g


def side():
    """The blocks' side in shade, its course line, a joint every block back."""
    g = [['S'] * 48 + ['.'] * (VW - 48) for _ in range(VH)]
    for x in range(48):
        g[31][x] = 'K'
        if x % 16 == 15:
            for y in range(VH):
                g[y][x] = 'K'
    lip(g, 48)
    return g


# the overworld grass: clumps, tufts and plain cells (tilemap.cpp COVER_GRASS)
GRASS = {'clump_l': (18, 2), 'clump_r': (19, 2), 'tuft_a': (20, 2), 'tuft_b': (18, 3),
         'tuft_c': (19, 3), 'plain': (20, 3)}


def top():
    """The tops' grass: plain moonlit grass. Its clumps and tufts are laid on
    whole, where each fits (tufts()), never sliced by a top's edge (user)."""
    return [['G'] * VW if y < 48 else ['.'] * VW for y in range(VH)]


def tufts():
    """The overworld grass's blades as they stand on its cells (tileset 18-20,
    2-3: the thick patch over four cells, the lone tufts beside it), the base
    left out, laid moonlit. Each bunch -- its blades and the black at its
    root -- is one connected piece; the game and the mock lay the bunches one
    by one, gathering several into a thick patch, each only where it fits
    whole on a top (user: never sliced by its edge)."""
    sheet = Image.open(os.path.join(ROOT, 'assets', 'tileset.png')).convert('RGB')
    tone = {tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)): k for k, v in OVERWORLD_GRASS.items()}
    g = [['.'] * VW for _ in range(VH)]
    for y in range(32):
        for x in range(48):
            c = tone[sheet.getpixel((18 * 16 + x, 2 * 16 + y))]
            g[y][x] = '.' if c == 'G' else c
    return g


def bunches(rows):
    """The separate bunches of a tufts() view, as the overworld draws them:
    each stands on a pair of black roots, so each pair is one bunch and every
    blade pixel goes to the nearest roots at or below it. A bunch is a list of
    (x, y, tone) from its top-left; one that runs off the view's edge is left
    out (the cells cut it)."""
    H, W = len(rows), len(rows[0])
    roots = [(x, y) for y in range(H) for x in range(W) if rows[y][x] == 'K']
    pairs = []                                   # roots side by side, two apart, are one bunch's
    for x, y in roots:
        for p in pairs:
            if any(abs(x - px) <= 3 and y == py for px, py in p):
                p.append((x, y)); break
        else:
            pairs.append([(x, y)])
    centre = [(sum(x for x, _ in p) / len(p), p[0][1]) for p in pairs]
    groups = [list(p) for p in pairs]
    for y in range(H):
        for x in range(W):
            if rows[y][x] in '.K':
                continue
            below = [i for i, (cx, cy) in enumerate(centre) if cy >= y]
            i = min(below or range(len(centre)), key=lambda i: (centre[i][0] - x) ** 2 + 2 * (centre[i][1] - y) ** 2)
            groups[i].append((x, y))
    out = []
    for comp in groups:
        # only what joins its own roots, across a pixel's gap at most -- a
        # stray of a neighbour's blade is not this bunch's
        mine, keep = set(comp), set(p for p in comp if rows[p[1]][p[0]] == 'K')
        grow = list(keep)
        while grow:
            cx, cy = grow.pop()
            for dx in (-2, -1, 0, 1, 2):
                for dy in (-2, -1, 0, 1, 2):
                    n = (cx + dx, cy + dy)
                    if n in mine and n not in keep:
                        keep.add(n); grow.append(n)
        comp = sorted(p for p in keep if any((p[0] + i, p[1] + j) in keep
                                             for i in (-1, 0, 1) for j in (-1, 0, 1) if i or j))   # no specks
        if any(cx in (0, W - 1) or cy in (0, H - 1) for cx, cy in comp):
            continue
        if any(cx >= 48 or cy >= 32 for cx, cy in comp):
            continue
        x0, y0 = min(c[0] for c in comp), min(c[1] for c in comp)
        out.append([(cx - x0, cy - y0, rows[cy][cx]) for cx, cy in comp])
    return out


CARVE = 24


def carvings():
    """Carved into a stone here and there, as on the great tombs under the
    henges (Newgrange, Knowth): a spiral, rings round a cup, a lozenge of
    zigzags, a triple spiral -- and, rarely, an eye. Cut lines in the stone's
    shade; each 24 x 24, laid on a block's upper course."""
    def blank():
        return [['.'] * CARVE for _ in range(CARVE)]
    def dot(g, x, y, c='D'):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < CARVE and 0 <= y < CARVE:
            g[y][x] = c
    def spiral(g, cx, cy, r, turns):
        n = 400
        for i in range(n + 1):
            t = i / n
            a = 2 * math.pi * turns * t
            dot(g, cx + r * t * math.cos(a), cy + r * t * math.sin(a))
    def ring(g, cx, cy, r):
        for i in range(160):
            a = 2 * math.pi * i / 160
            dot(g, cx + r * math.cos(a), cy + r * math.sin(a))
    sp = blank(); spiral(sp, 11.5, 11.5, 10.5, 3)
    rg = blank()
    for r in (4, 7.5, 11):
        ring(rg, 11.5, 11.5, r)
    for dx in (0, 1):
        for dy in (0, 1):
            dot(rg, 11 + dx, 11 + dy)
    zz = blank()
    for row in range(4):
        for x in range(CARVE):
            y = 3 + row * 5 + abs((x % 8) - 4) - 2
            dot(zz, x, y)
    tri = blank()
    for cx, cy in ((7, 8), (16, 8), (11.5, 16)):
        spiral(tri, cx, cy, 5, 2)
    eye = blank()
    for i in range(200):                        # the lids, an almond
        t = -1 + 2 * i / 199
        dot(eye, 11.5 + 11 * t, 11.5 - 6 * (1 - t * t))
        dot(eye, 11.5 + 11 * t, 11.5 + 6 * (1 - t * t))
    ring(eye, 11.5, 11.5, 4.5)
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            dot(eye, 11.5 + dx, 11.5 + dy, 'K')     # the pupil
    g = [['.'] * VW for _ in range(VH)]
    for i, c in enumerate((sp, rg, zz, tri, eye)):
        ox, oy = (i % 4) * CARVE, (i // 4) * CARVE
        for y in range(CARVE):
            for x in range(CARVE):
                g[oy + y][ox + x] = c[y][x]
    return g


def stars():
    """The sky the maze stands in, floor and void alike: chunky stars, a
    2 x 2 and a cross -- no single pixel, so none reads as noise."""
    g = [['.'] * VW for _ in range(VH)]
    for y, x in ((0, 0), (0, 1), (1, 0), (1, 1)):
        g[y][x] = 'M'
    for y, x, c in ((1, 5, 'M'), (0, 5, 'D'), (2, 5, 'D'), (1, 4, 'D'), (1, 6, 'D')):
        g[y][x] = c
    return g


# Constellations in the shape of the game's cryptids, drawn as constellations
# are -- stick figures, stars at the joints -- after their carved icons
# (maya_cryptids_design.SMALL): (stars, lines between them by index).
CONSTELLATIONS = {
    # the Vatnaormur: a serpent in humps, its head raised, jaws open
    'vatnaormur': ([(4, 46), (14, 32), (24, 46), (34, 32), (44, 46), (54, 30), (60, 14), (70, 12), (68, 22)],
                   [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (6, 8)]),
    # the Myrmecoleon: a lion's head and mane on an ant's body and legs
    'myrmecoleon': ([(62, 10), (52, 14), (38, 22), (22, 24), (8, 20), (34, 42), (24, 42), (48, 40), (12, 38), (58, 22)],
                    [(0, 1), (1, 2), (2, 3), (3, 4), (2, 5), (3, 6), (1, 7), (4, 8), (0, 9), (9, 1)]),
    # the Lusca: a shark's forequarters over a mass of arms
    'lusca': ([(66, 16), (50, 10), (22, 12), (8, 4), (8, 22), (36, 0), (40, 16), (30, 42), (40, 46), (50, 42), (60, 34)],
              [(0, 1), (1, 2), (2, 3), (2, 4), (1, 5), (5, 2), (6, 7), (6, 8), (6, 9), (6, 10), (1, 6)]),
}


def constellation(name):
    stars, lines = CONSTELLATIONS[name]
    g = [['.'] * VW for _ in range(VH)]
    for i, j in lines:
        (x0, y0), (x1, y1) = stars[i], stars[j]
        n = max(abs(x1 - x0), abs(y1 - y0))
        for k in range(n + 1):
            g[2 + round(y0 + (y1 - y0) * k / n)][2 + round(x0 + (x1 - x0) * k / n)] = 'D'
    for x, y in stars:
        for dy in (0, 1):
            for dx in (0, 1):
                g[2 + y + dy][2 + x + dx] = 'M'
    return g


def design():
    v = {'front': front(), 'top': top(), 'side': side(), 'carvings': carvings(), 'stars': stars(), 'tufts': tufts()}
    for name in CONSTELLATIONS:
        v['const_' + name] = constellation(name)
    v = {k: [''.join(r) for r in rows] for k, rows in v.items()}
    for name, rows in v.items():                     # four colours a cell, as the game holds it
        for cy in range(0, VH, 16):
            for cx in range(0, VW, 16):
                cell = {c for r in rows[cy:cy + 16] for c in r[cx:cx + 16]} - {'.'}
                assert len(cell) <= 4, (name, cx, cy, cell)
    return {'pal': PAL, 'view_w': VW, 'order': list(v), 'views': v}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
