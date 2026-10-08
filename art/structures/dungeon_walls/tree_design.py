"""The giant tree: Mother 1's tower (the user's reference, Desktop/reference/
tree reference.aseprite) -- floors stepping up a wall of solid mass, ladders
up the wall between them -- dressed as the inside of a tree. Above the way in
the trunk's heartwood with shelf fungus for floors; below it soil threaded
with roots, packed dirt underfoot.

    python art/structures/dungeon_walls/tree_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/dungeon_walls/tree

Every swatch tiles; the layout samples walls by (x, rows above the floor the
wall stands on), so courses follow a floor's edge and lean on its diagonals.

    heart, heart_shade     64 x 64: heartwood, the grain running up the trunk,
                           ring knots where branches left; _shade is the same
                           wood on a receding side wall (one tone down)
    soil, soil_deep (+_shade)  64 x 64: dark soil, clods, roots across it --
                           thin near the surface, thick deep down
    fungus, fungus_lip     64 x 64 floor / 64 x 8 edge: a shelf fungus's top
                           in growth zones, its rim and gills below
    dirt, dirt_lip         packed dirt and its broken edge
    ladder_wood, ladder_root  16 x 64 (8 period): a ladder in a dark recess
    door                   32 x 48: the way out, an arched plank door
    bark (+_shade)         64 x 64: the shell round the hollow, plates and furrows

Tones -- four a 16px cell, one palette.
"""
import json, math, random, sys

PAL = {'K': '000000',
       'H': '815423', 'h': '633e1b', 'd': '3c2412', 'x': '22140c',      # heartwood, down to its deepest shade
       'S': '2b190e', 's': '493712', 'R': '785830',                     # soil, clod / root shade, root
       'F': 'd7a175', 'f': 'b2966a', 'G': '8d6b4f',                     # shelf fungus
       'a': '583518', 'A': '764c20',                                    # dirt
       'W': '967448',                                                   # ladder and door wood
       'B': '605028', 'b': '463422', 'c': '2d230c'}                     # bark: plate, its shade, furrow
SHADE = {'heart': {'H': 'h', 'h': 'd', 'd': 'x', 'K': 'K'},
         'soil': {'R': 's', 's': 'S', 'S': 'x', 'K': 'K'},
         'bark': {'B': 'b', 'b': 'c', 'c': 'K', 'K': 'K'}}
VW, VH = 64, 64


def grid(w, h, c):
    return [[c] * w for _ in range(h)]


def ring_knot(g, kx, ky, r):
    """Where a branch left: rings round a dark heart, wrapping at 64."""
    for y in range(ky - r, ky + r + 1):
        for x in range(kx - r, kx + r + 1):
            e = math.hypot((x - kx) * 0.8, y - ky)                  # a little taller than wide
            if e > r + 0.5:
                continue
            c = 'K' if e > r - 0.5 else ('d' if e < 1.6 else ('h' if int(e) % 2 == 0 else 'H'))
            g[y % 64][x % 64] = c


def heart():
    g = grid(64, 64, 'H')
    rng = random.Random(11)
    knots = [(20, 18, 6), (50, 48, 5)]
    for i in range(8):                                               # grain up the trunk, 8 apart
        x0, ph, c = i * 8 + rng.randrange(3), rng.random() * 6.28, 'd' if i % 3 == 0 else 'h'
        for y in range(64):
            x = x0 + round(1.5 * math.sin(2 * math.pi * y / 64 + ph))
            for kx, ky, r in knots:                                  # the grain bows round a knot
                dy = min(abs(y - ky), 64 - abs(y - ky))
                if dy <= r + 1 and abs(x - kx) <= r + 1:
                    x = kx + (r + 1) * (1 if x >= kx else -1)
            g[y][x % 64] = c
    for kx, ky, r in knots:
        ring_knot(g, kx, ky, r)
    for x0, y0, n in ((36, 4, 9), (6, 40, 7)):                       # checks: short splits along the grain
        for y in range(y0, y0 + n):
            g[y % 64][x0 % 64] = 'K'
            g[y % 64][(x0 + 1) % 64] = 'd'
    return g


def soil(deep):
    g = grid(64, 64, 'S')
    rng = random.Random(21 + deep)
    for _ in range(16):                                              # clods, never a lone pixel
        x0, y0, w, h = rng.randrange(64), rng.randrange(64), rng.randrange(2, 5), rng.randrange(2, 4)
        for y in range(h):
            for x in range(w):
                if (x, y) not in ((0, 0), (w - 1, h - 1)) or w == 2:
                    g[(y0 + y) % 64][(x0 + x) % 64] = 's'
    roots = [(14, 0.0, 6, 2 + 2 * deep)] + ([(44, 2.6, 8, 3)] if deep else [(46, 2.6, 5, 1)])
    for y0, ph, amp, th in roots:                                    # roots across, wandering, wrapping at 64
        def yc(x):
            return y0 + round(amp * math.sin(2 * math.pi * x / 64 + ph) + 0.4 * amp * math.sin(4 * math.pi * x / 64 + 2 * ph))
        for x in range(64):
            w = th + (1 if (x // 16 + y0) % 3 == 0 and th > 1 else 0)   # swelling and thinning
            g[(yc(x) - 1) % 64][x] = 'K'
            for t in range(w):
                g[(yc(x) + t) % 64][x] = 'R' if t < max(1, w - 1) else 's'
            g[(yc(x) + w) % 64][x] = 'K'
        for x0 in range(rng.randrange(8), 64, 23):                   # rootlets hanging off it
            y1 = yc(x0) + th + 1
            for i in range(5 + 3 * deep):
                g[(y1 + i) % 64][(x0 + i // 2) % 64] = 's'
                g[(y1 + i) % 64][(x0 + i // 2 + 1) % 64] = 's'
    return g


def shade(g, kind):
    return [[SHADE[kind].get(c, c) for c in r] for r in g]


def fungus():
    """Growth zones across the shelf, wavy, pores in the dark."""
    g = grid(64, 64, 'f')
    for k in range(4):
        for x in range(64):
            y = 16 * k + 4 + round(2 * math.sin(2 * math.pi * x / 32 + k))
            g[y % 64][x] = 'F'
            g[(y + 1) % 64][x] = 'F'
            g[(y + 5) % 64][x] = 'G'
    rng = random.Random(31)
    for _ in range(24):
        x, y = rng.randrange(64), rng.randrange(64)
        if g[y][x] == 'f' and g[y][(x + 1) % 64] == 'f':
            g[y][x] = g[y][(x + 1) % 64] = 'G'
    return g


def fungus_lip():
    g = grid(64, 8, 'f')
    for x in range(64):
        g[0][x] = g[1][x] = 'F'
        for y in range(3, 7):
            g[y][x] = 'G' if x % 3 == 0 else 'f'                     # gills
        g[7][x] = 'K'
    return g


def dirt():
    g = grid(64, 64, 'a')
    rng = random.Random(41)
    for _ in range(40):
        x, y = rng.randrange(64), rng.randrange(64)
        g[y][x] = g[y][(x + 1) % 64] = 'A'
    for _ in range(10):                                              # pebbles, lit on top
        x, y = rng.randrange(64), rng.randrange(64)
        for dx in range(3):
            g[y % 64][(x + dx) % 64] = 'A'
            g[(y + 1) % 64][(x + dx) % 64] = 'd'
    return g


def dirt_lip():
    g = grid(64, 8, 'd')
    rng = random.Random(51)
    for x in range(64):
        g[0][x] = 'A'
        g[6][x] = 'S'
        g[7][x] = 'K'
    for _ in range(10):
        x, y = rng.randrange(62), rng.randrange(2, 5)
        for dx in range(3):
            g[y][x + dx] = g[y + 1][x + dx] = 'S'
    return g


def ladder(kind):
    """Rails and rungs in a dark recess, an 8-row period."""
    g = grid(16, 64, 'K')
    for y in range(64):
        wob = 0 if kind == 'wood' else (1 if (y // 8) % 2 else 0)
        for x in (1 + wob, 12 - wob):
            g[y][x] = 'W' if kind == 'wood' else 'R'
            g[y][x + 1] = 'R' if kind == 'wood' else 's'
            if kind == 'wood':
                g[y][x + 2] = 'R'
        if y % 8 in (2, 3):
            for x in range(3, 13):
                if g[y][x] == 'K':
                    g[y][x] = ('W' if kind == 'wood' else 'R') if y % 8 == 2 else ('R' if kind == 'wood' else 's')
    return g


def door():
    g = grid(32, 48, '.')
    for y in range(48):
        for x in range(32):
            if y < 16 and math.hypot(x - 15.5, y - 16) > 16:
                continue
            g[y][x] = 'R' if x % 8 in (6, 7) else 'W'                # planks
            if x % 8 == 7:
                g[y][x] = 's'
    for y in range(48):
        for x in range(32):
            if g[y][x] != '.' and any(not (0 <= x + i < 32 and 0 <= y + j < 48) or g[y + j][x + i] == '.'
                                      for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g[y][x] = 'K'
    for x in range(3, 29):                                           # cross bars
        for y in (18, 36):
            g[y][x] = 's'
            g[y + 1][x] = 'K'
    g[28][24] = g[28][25] = g[29][24] = g[29][25] = 'K'              # the handle
    return g


def bark():
    """The tree's shell: vertical plates split by deep furrows, each plate
    broken across here and there, its right side in shade."""
    g = grid(64, 64, 'B')
    rng = random.Random(61)
    for i in range(5):                                               # furrows, wavering, 13 apart (64 wraps: 5 x 13 = 65 -> one is 12)
        x0, ph = i * 13, rng.random() * 6.28
        for y in range(64):
            x = x0 + round(1.5 * math.sin(2 * math.pi * y / 64 + ph))
            g[y][x % 64] = 'K'
            g[y][(x + 1) % 64] = 'c'
            g[y][(x - 1) % 64] = 'c'
            g[y][(x - 2) % 64] = 'b'                                 # the plate's shaded side
        for _ in range(2):                                           # a plate broken across
            y = rng.randrange(64)
            for dx in range(2, 11):
                xx = (x0 + dx) % 64
                if g[y][xx] in 'Bb':
                    g[y][xx] = 'c'
                    if g[(y + 1) % 64][xx] in 'Bb':
                        g[(y + 1) % 64][xx] = 'b'
    return g


def design():
    def pad(rows):
        return [''.join(r) + '.' * (VW - len(r)) for r in rows] + ['.' * VW] * (VH - len(rows))
    h, so, sd = heart(), soil(0), soil(1)
    v = {'heart': h, 'heart_shade': shade(h, 'heart'),
         'soil': so, 'soil_shade': shade(so, 'soil'), 'soil_deep': sd, 'soil_deep_shade': shade(sd, 'soil'),
         'fungus': fungus(), 'fungus_lip': fungus_lip(), 'dirt': dirt(), 'dirt_lip': dirt_lip(),
         'ladder_wood': ladder('wood'), 'ladder_root': ladder('root'), 'door': door(), 'bark': bark()}
    v['bark_shade'] = shade(v['bark'], 'bark')
    v = {k: pad(r) for k, r in v.items()}
    for name, rows in v.items():                         # four colours a cell, as the game holds them
        for cy in range(0, VH, 16):
            for cx in range(0, VW, 16):
                cell = {c for r in rows[cy:cy + 16] for c in r[cx:cx + 16]} - {'.'}
                assert len(cell) <= 4, (name, cx, cy, cell)
    return {'pal': PAL, 'view_w': VW, 'order': list(v), 'views': v}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
