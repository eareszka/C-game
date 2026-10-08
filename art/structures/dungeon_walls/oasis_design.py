"""The oasis: a flooded cave under the spring, seen from the side, swum through
left to right (user: a water level like Mario's, free float, a parallax of a
sunken oasis behind). Drawn through the plugin:

    python art/structures/dungeon_walls/oasis_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/dungeon_walls/oasis

Four tones a cell, the NES way, and the water is one of them everywhere: so
the rock and the sand share theirs -- the desert's sandstone (the pyramid's
b2966a and 785830) and the black line -- and tell themselves apart by marks,
the rock by clumpy cracks lit on their upper side (the cave walls'), the sand
by ripples.

    rock        64 x 64  sandstone cobbles under water, tiling (the cave walls' kind)
    sand        64 x 64  the seabed, tiling
    weed_0..2   16 x 32  three frames of a weed swaying (rooted at the foot)
    bubbles     a small, a middle and a big bubble (3, 5, 7 across)
    surface_0..2 64 x 6  an air pocket's water line, three frames
    far         128 x 208  the far wall: rock and the light down from the spring
    palm, ruin  the oasis that sank: a palm and a stretch of town wall
    hud         8 x 8 x 3  the oxygen bubble: full, popping, gone
    eye_0..2    16 x 8  an eye in the dark, blinking (open, half, shut)
    leviathan   128 x 48  something huge drifting far behind
    leviathan_near 256 x 72  the same up close, for the stretch it passes near
    palm_stand_64, palm_stand_96  palms standing on the seabed, the forest's
    shaft_bright 64 x 208  a brighter shaft of light, for the open cavern
Dark and strange (user): eyes open in the dark, a leviathan passes far off.
"""
import json, math, random, sys

# Dark and strange (user): deep indigo water, the sandstone and weed a step
# into shadow, the light from the spring faint, the bubbles dim.
PAL = {'K': '000000',
       'R': '5c4616', 'L': '785830',            # the sandstone, its light
       'W': '2b1f40',                          # the water, deep
       'g': '163623', 'G': '235436',           # weed
       'b': '5e486a', 'w': 'c6ccda', 'a': '423c70',   # bubbles, light, air
       'f': '181224', 's': '3b2a58',           # the far wall, the light shafts
       'r': '7c0a1b'}                          # an eye's iris (its white is the light's)
VW, VH = 256, 208


def blank(w, h, c='.'):
    return [[c] * w for _ in range(h)]


def rock():
    """Sandstone cobbles packed together, as the cave walls are: each rounded,
    lit along its upper left, the gaps between them black; tiling 64."""
    g = blank(64, 64, 'K')
    rng = random.Random(21)
    for row in range(8):
        y0 = row * 8
        x = rng.randrange(-6, 0) + (row % 2) * 5
        while x < 64:
            w = rng.randrange(8, 13)
            for yy in range(8):
                for xx in range(w):
                    nx, ny = (xx + 0.5 - w / 2) / (w / 2), (yy + 0.5 - 4) / 4
                    if nx * nx + ny * ny > 1.0:
                        continue
                    lit = (nx + ny < -0.55) and nx * nx + ny * ny > 0.25
                    g[(y0 + yy) % 64][(x + xx) % 64] = 'L' if lit else 'R'
            x += w
    return g


def sand():
    """The seabed: light sand, ripples in the darker tone, the odd pebble."""
    g = blank(64, 64, 'L')
    for y in range(64):
        for x in range(64):
            if (y + int(2 * math.sin((x + 7 * (y // 8)) / 5.0))) % 8 == 0 and (x // 3) % 3:
                g[y][x] = 'R'
    rng = random.Random(4)
    for _ in range(10):
        x, y = rng.randrange(62), rng.randrange(62)
        g[y][x] = g[y][x + 1] = 'R'; g[y + 1][x] = g[y + 1][x + 1] = 'K'
    return g


def weed(frame):
    """Three blades from one root, 16 x 32, their tips swaying across three
    frames; the stems dark, the blades lit."""
    g = blank(16, 32)
    lean = (-1, 0, 1)[frame]
    for blade, (x0, top, phase) in enumerate(((5, 2, 0.0), (8, 8, 1.7), (10, 14, 3.1))):
        for y in range(top, 32):
            t = (31 - y) / 29.0
            x = x0 + int(round(lean * 3 * t * t + 1.2 * math.sin(y / 3.5 + phase) * t))
            x = max(1, min(13, x))
            g[y][x] = 'G'
            g[y][x + 1] = 'g'
            if y > top + 1 and (y + 2 * blade) % 6 == 0:
                g[y][x - 1] = 'G'                               # a leaf off it
                if y > 0: g[y - 1][x - 1] = 'G'
    return g


def bubbles():
    g = blank(24, 8)
    for x0, r in ((0, 1), (5, 2), (12, 3)):
        c = x0 + r
        for y in range(2 * r + 1):
            for x in range(2 * r + 1):
                d = math.hypot(x - r, y - r)
                if r - 0.6 <= d <= r + 0.4 or (r == 1 and d < 1.5):
                    g[y][x0 + x] = 'b'
        g[1 if r > 1 else 0][x0 + r - 1 + (r == 1)] = 'w'       # the glint
    return g


def surface(frame):
    """The water line under an air pocket: a bright crest moving along."""
    g = blank(64, 6)
    for x in range(64):
        y = 2 + int(round(1.2 * math.sin((x + frame * 7) / 4.0)))
        g[y][x] = 'w'
        for yy in range(y + 1, 6):
            g[yy][x] = 'b' if yy == y + 1 else '.'
        for yy in range(0, y):
            g[yy][x] = 'a'                                      # the air above it
    return g


def far():
    """The far wall: ragged rock top and bottom in the far tone, the light of
    the spring slanting down through the water between."""
    g = blank(128, VH, 'W')
    for x in range(128):
        top = 18 + int(10 * math.sin(x / 13.0) + 5 * math.sin(x / 5.0 + 1))
        bot = VH - 22 - int(9 * math.sin(x / 11.0 + 2) + 4 * math.sin(x / 4.0))
        for y in range(VH):
            if y < top or y > bot:
                g[y][x] = 'f'
    for x0 in (10, 70):                                         # two shafts of light
        for y in range(VH):
            for k in range(14):
                x = (x0 + k + y // 3) % 128
                if g[y][x] == 'W' and (k + y) % 2 == 0 and k not in (0, 13):
                    g[y][x] = 's'
    return g


def palm():
    """A palm that sank, leaning, its fronds limp: a dark shape far off."""
    g = blank(32, 64)
    for y in range(18, 64):
        x = 14 + (64 - y) // 8
        for dx in range(3):
            g[y][x + dx] = 'f' if (y // 4) % 2 else 'g'
    for k, (dx, dy) in enumerate(((-1, 1), (1, 1), (-1, 2), (1, 2), (0, 1))):
        x, y = 20, 16
        for i in range(12):
            x += dx; y += dy if i > 3 else 0
            if 0 <= x < 32 and 0 <= y < 64:
                g[y][x] = 'g'
                if y + 1 < 64: g[y + 1][x] = 'g'
    return g


def ruin():
    """A stretch of the town's wall, broken, in the far tone with its joints."""
    g = blank(48, 40)
    for y in range(40):
        top = 6 + int(5 * abs(math.sin(y * 0)) + 0)
        for x in range(48):
            edge = 6 + int(6 * abs(math.sin(x / 7.0)))
            if y >= edge:
                g[y][x] = 'g' if (y % 8 == 0 or (x + 4 * ((y // 8) % 2)) % 12 == 0) else 'f'
    return g


def eye(frame):
    """An eye open in the dark, 16 x 8: open, half shut, shut -- it blinks."""
    g = blank(16, 8)
    lid = (0, 2, 4)[frame]
    for y in range(8):
        for x in range(16):
            nx, ny = (x + .5 - 8) / 7.5, (y + .5 - 4) / 3.6
            if nx * nx + ny * ny > 1:
                continue
            if y < lid or y >= 8 - lid:
                g[y][x] = 'K'                                  # the lid over it
            elif (x - 8) ** 2 + (y - 4) ** 2 <= 5:
                g[y][x] = 'K' if (x - 8) ** 2 + (y - 4) ** 2 <= 1 else 'r'
            else:
                g[y][x] = 'w'
    return g


def leviathan():
    """Something huge far off in the water: a long eel-like body with a fin
    along its back and a pale eye, 128 x 48, one tone darker than the water."""
    g = blank(128, 48)
    for x in range(128):
        c = 24 + 8 * math.sin(x / 18.0)
        half = 9 * math.sin(math.pi * min(1, (x + 4) / 40.0)) if x < 36 else 9 * (1 - (x - 36) / 100.0) + 2
        for y in range(48):
            if abs(y - c) <= half:
                g[y][x] = 'f'
        if 40 < x < 110 and x % 6 < 4:                         # the fin along its back
            for y in range(int(c - half - 4), int(c - half)):
                if 0 <= y < 48:
                    g[y][x] = 'f'
    g[int(24 + 8 * math.sin(10 / 18.0)) - 2][10] = 'w'          # its pale eye
    return g


def leviathan_near():
    """The same creature up close, 256 x 72: a long body tapering to the tail,
    a ridge of fin spines along its back, its scales in bands, one pale eye
    with a dark iris; black-outlined as the game's sprites are."""
    g = blank(256, 72)
    def mid(x):
        return 36 + 10 * math.sin(x / 34.0)
    def half(x):
        return 16 * math.sin(math.pi / 2 * min(1, (x + 6) / 66.0)) if x < 60 else 16 * (1 - (x - 60) / 210.0) + 2
    for x in range(256):
        c, h = mid(x), half(x)
        for y in range(72):
            if abs(y - c) <= h:
                band = int((y - c + h) / 5) % 2 == 0 and (x // 7) % 2 == 0
                g[y][x] = 's' if band and x >= 32 else 'f'       # no scales by the eye: four tones a cell
        if 50 < x < 230 and x % 9 < 5:                         # fin spines along the back
            top = int(c - h)
            for k in range(1, 7 - (x % 9)):
                if 0 <= top - k < 72:
                    g[top - k][x] = 'f'
    ey = int(mid(16) - 4)
    for dy in range(-2, 3):                                     # the eye, pale, a dark iris
        for dx in range(-3, 4):
            if dx * dx / 9 + dy * dy / 4 <= 1:
                g[ey + dy][16 + dx] = 'w'
    g[ey][16] = g[ey][17] = 'K'
    out = [r[:] for r in g]                                     # its outline
    for y in range(72):
        for x in range(256):
            if g[y][x] != '.' and any(not (0 <= x + i < 256 and 0 <= y + j < 72) or g[y + j][x + i] == '.'
                                      for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = 'K'
    return out


def palm_stand(h):
    """A palm standing on the seabed, 32 wide by h: its ringed trunk rising
    from the sand with a lean, its crown at the top, the fronds arching out
    and drooping (the forest's; user: not hanging from above)."""
    g = blank(32, h)
    top = 16                                                    # the crown's cells above, the trunk's below:
    for y in range(top, h):                                     # their tones never share a cell
        x = 14 + int(round(2 * math.sin((h - y) / 13.0)))
        for dx in range(5):
            g[y][x + dx] = 'L' if (y // 3) % 2 else 'R'         # the trunk's rings
    cx = 16 + int(round(2 * math.sin((h - top) / 13.0)))
    for dx, lift, n in ((-1, 0.9, 14), (1, 0.9, 14), (-1, 0.4, 13), (1, 0.4, 13), (-0.5, 1.4, 9), (0.5, 1.4, 9)):
        x, y = float(cx), float(top - 1)
        for i in range(n):
            x += dx; y += -lift + i * 0.22                        # up and out, then drooping
            for t in range(2):
                yy = int(y) + t
                if 0 <= int(x) < 32 and 0 <= yy < top:
                    g[yy][int(x)] = 'G' if t == 0 else 'g'
    out = [r[:] for r in g]
    for y in range(h):
        for x in range(32):
            if g[y][x] != '.' and any(not (0 <= x + i < 32 and 0 <= y + j < h) or g[y + j][x + i] == '.'
                                      for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = 'K'
    return out


def shaft_bright():
    """A brighter shaft of the spring's light for the open cavern, 64 x 208:
    a wide band slanting down, its inside dithered a step brighter."""
    g = blank(64, VH)
    for y in range(VH):
        for k in range(26):
            x = (6 + k + y // 3) % 64
            if k in (0, 25):
                continue
            g[y][x] = 'a' if 6 <= k <= 19 and (k + y) % 2 == 0 else 's'
    return g


def hud():
    g = blank(24, 8)
    for f in range(3):
        for y in range(8):
            for x in range(8):
                d = math.hypot(x - 3.5, y - 3.5)
                if f == 0:
                    c = 'b' if 2.6 < d <= 3.6 else ('a' if d <= 2.6 else '.')
                elif f == 1:
                    c = 'w' if 3.0 < d <= 3.9 and (x + y) % 2 == 0 else '.'
                else:
                    c = 's' if 2.6 < d <= 3.6 else '.'
                if c != '.':
                    g[y][f * 8 + x] = c
        if f == 0:
            g[2][2] = g[2][3] = g[3][2] = 'w'                   # its glint
    return g


def design():
    v = {'rock': rock(), 'sand': sand(), 'weed_0': weed(0), 'weed_1': weed(1), 'weed_2': weed(2),
         'bubbles': bubbles(), 'surface_0': surface(0), 'surface_1': surface(1), 'surface_2': surface(2),
         'far': far(), 'palm': palm(), 'ruin': ruin(), 'hud': hud(),
         'eye_0': eye(0), 'eye_1': eye(1), 'eye_2': eye(2), 'leviathan': leviathan(),
         'leviathan_near': leviathan_near(), 'palm_stand_64': palm_stand(64), 'palm_stand_96': palm_stand(96),
         'shaft_bright': shaft_bright()}
    def pad(g):
        rows = [''.join(r) + '.' * (VW - len(r)) for r in g]
        return rows + ['.' * VW] * (VH - len(rows))
    v = {k: pad(g) for k, g in v.items()}
    for name, rows in v.items():                     # four a cell, the water counted wherever it shows
        for cy in range(0, VH, 16):
            for cx in range(0, VW, 16):
                cell = {c for r in rows[cy:cy + 16] for c in r[cx:cx + 16]} - {'.'}
                if name not in ('far',):
                    cell |= {'W'}
                assert len(cell) <= 4, (name, cx, cy, cell)
    return {'pal': PAL, 'view_w': VW, 'order': list(v), 'views': v}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
