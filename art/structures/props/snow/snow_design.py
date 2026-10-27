"""The snow's props: eighteen things for the snowfields, one function each, in three groups
that never mix -- the ice field, the abandoned expedition camp, the mammoth graveyard.

    python art/structures/props/snow/snow_design.py              # every prop
    python art/structures/props/snow/snow_design.py tent         # one

Each writes art/structures/props/snow/<name>.png (the ice spire its frames too, a strip).
The list was approved by the user on 2026-10-27 (sizes in cells, materials, drops); PixelLab
drafts under pixellab-out/snow-*/ gave the shapes of the ice spire, icicle rock, mammoth
skull, ribcage, sled, snowman and tent.

Objects keep the objects' rule (OVERWORLD_STYLE.md): one black line round the silhouette,
three colours and black, flat fills, the light sparse and high on the left, the dark massed
low and on the right. Ice is the palette's three pale blues; snow lying on a thing is white,
its shade the palette's cold grey. The tent, the ice block and the crate are built, in the
houses' projection; the frozen grass is ground cover, drawn as the ground draws a tuft.
No cell holds more than four colours, black among them (keep4).
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
sys.path.insert(0, os.path.join(HERE, '..', 'forest'))
from entrance_shapes import Scene
from forest_design import blank, outline, typed, stroke, ellipse, log_side, log_end, write

# tools/overworld_style.py MATERIALS
ICE = ('dcf0ff', '84a7e9', '3e91cc')
SNOW = ('fcfcfc', 'dcf0ff', 'a4aaba')      # white, its cold shade (snowpack)
STONE = ('c6ccda', '9797aa', '595965')
BARK = ('605028', '463422', '2d230c')
WOOD = ('967448', '785830', '493712')
BONE = ('e8e0c0', 'b2966a', '8d6b4f')
HIDE = ('b2966a', '8d6b4f')                 # the bone ramp's browns: tanned hide
RED = ('b70000', '7c0a1b')


# ---------------------------------------------------------------- shared
def piece(g, part):
    """Lay a part over what is drawn, a black line round it first, so a nearer part is parted
    from the one behind it by a line."""
    h, w = len(g), len(g[0])
    for y in range(h):
        for x in range(w):
            if part[y][x] == '.':
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q, r = x + dx, y + dy
                if 0 <= q < w and 0 <= r < h and part[r][q] == '.':
                    g[r][q] = 'K'
    for y in range(h):
        for x in range(w):
            if part[y][x] != '.':
                g[y][x] = part[y][x]
    return g


def keep4(g, pal, cell=16):
    """Four colours a cell, black among them: in a cell with more, its rarest tone takes the
    nearest of the others there, until it fits."""
    rgb = lambda c: tuple(int(pal[c][i:i + 2], 16) for i in (0, 2, 4))
    h, w = len(g), len(g[0])
    for cy in range(0, h, cell):
        for cx in range(0, w, cell):
            pix = [(x, y) for y in range(cy, min(cy + cell, h)) for x in range(cx, min(cx + cell, w))]
            while True:
                tones = {g[y][x] for x, y in pix} - {'.', 'K'}
                if len(tones) <= 3:
                    break
                n = {t: sum(g[y][x] == t for x, y in pix) for t in tones}
                rare = min(tones, key=lambda t: (n[t], t))
                into = min(tones - {rare}, key=lambda t: sum((a - b) ** 2 for a, b in zip(rgb(rare), rgb(t))))
                for x, y in pix:
                    if g[y][x] == rare:
                        g[y][x] = into
    return g


def shard(W, H, bl, br, yb, ax, ay, lit=0.55):
    """A crystal standing on row yb, its base bl..br, its point at (ax, ay): the face left of
    its ridge the mid tone, right of it in shade, its left edge lit in the upper part, its
    foot in shade."""
    p = blank(W, H)
    ridge_b = (bl + br) / 2 + 1
    for y in range(int(ay), yb + 1):
        t = (y - ay) / max(1, yb - ay)
        xl, xr = ax + (bl - ax) * t, ax + (br - ax) * t
        ridge = ax + (ridge_b - ax) * t
        for x in range(int(math.floor(xl + 0.5)), int(math.floor(xr + 0.5)) + 1):
            if not (0 <= x < W):
                continue
            c = 'd' if x > ridge else 'm'
            if x <= xl + 1.2 and t < lit:
                c = 'l'
            if y >= yb - 1:
                c = 'd'
            p[y][x] = c
    return p


def mound(g, cx, cy, rx, ry, top=True):
    """A drift of snow: white, its cold shade along its underside at the right."""
    inside = ellipse(cx, cy, rx, ry)
    for y in range(len(g)):
        for x in range(len(g[0])):
            if inside(x, y) and (not top or y + 0.5 <= cy + ry * 0.35):
                u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                g[y][x] = 's' if u + 2 * v > 0.9 else 'w'
    return g


# ---------------------------------------------------------------- ice field
def ice_spire(frame=0):
    """The ice field's anchor: a tall jagged crystal, two smaller ones at its feet; a glint
    runs up its lit face, one step a frame."""
    W, H = 32, 48
    g = blank(W, H)
    piece(g, shard(W, H, 3, 10, 44, 6, 27))
    piece(g, shard(W, H, 21, 28, 44, 26, 31))
    piece(g, shard(W, H, 8, 23, 44, 15, 3, lit=0.7))
    k = frame % 4
    y = 37 - 9 * k
    xs = [x for x in range(W) if g[y][x] == 'm']
    if xs:
        x = (xs[0] + xs[-1]) // 2 - 1
        for dx, dy in ((0, 0), (1, -1), (-1, 1), (0, -1), (0, 1), (-1, 0), (1, 0), (0, -2), (0, 2)):
            if g[y + dy][x + dx] == 'm':
                g[y + dy][x + dx] = 'l'
    return keep4(g, P_ICE), P_ICE


P_ICE = {'l': ICE[0], 'm': ICE[1], 'd': ICE[2], 'K': '000000'}


def ice_cluster():
    W = H = 16
    g = blank(W, H)
    piece(g, shard(W, H, 2, 6, 13, 3, 7))
    piece(g, shard(W, H, 9, 13, 13, 12, 5))
    piece(g, shard(W, H, 5, 10, 13, 7, 3))
    return keep4(g, P_ICE), P_ICE


def ice_block():
    """A cracked cube of ice, built: its top lit, its south face the mid, its east in shade,
    a crack down the face and a glint at its upper left."""
    sc = Scene(16, 16, 13)
    sc.box(0, 2, 9, 0, 3, 0, 7, front='M')
    g = sc.render().g
    for x, y in ((6, 6), (6, 7), (7, 8), (7, 9), (6, 10), (8, 9)):
        if g[y][x] == 'M':
            g[y][x] = 'D'
    for x, y in ((3, 6), (4, 6), (3, 7)):
        if g[y][x] == 'M':
            g[y][x] = 'L'
    pal = {'L': ICE[0], 'M': ICE[1], 'D': ICE[2], 'K': '000000'}
    return keep4(g, pal), pal


def snow_boulder():
    g = blank(32, 32)
    inside = ellipse(15.5, 20.5, 12.5, 9.5)
    for y in range(32):
        for x in range(32):
            if inside(x, y) and y <= 29:
                u, v = (x + 0.5 - 15.5) / 12.5, (y + 0.5 - 20.5) / 9.5
                g[y][x] = 'd' if u + v > 0.55 or y >= 28 else 'm'
    cap = lambda x: 16 + 1.8 * math.sin(x * 0.7) + 0.1 * (x - 14) ** 2 / 3
    for y in range(32):
        for x in range(32):
            if g[y][x] != '.' and y < cap(x):
                g[y][x] = 'w'                                      # snow over its crown
    for x, y in ((8, 17), (21, 18), (14, 19)):                     # caught in the hollows below
        if g[y][x] != '.':
            g[y][x] = 'w'
    for x, y in ((13, 22), (14, 23), (14, 24), (15, 25), (19, 21), (20, 22)):   # a crack
        g[y][x] = 'K'
    pal = {'w': SNOW[0], 'm': STONE[1], 'd': STONE[2], 'K': '000000'}
    return keep4(outline(g), pal), pal


def icicle_rock():
    """A shelf of dark rock overhanging its base, built: the base set back beneath it in its
    shadow, snow on the shelf's top, icicles hanging the length of the shelf's front."""
    sc = Scene(32, 32, 29)
    sc.box(0, 1, 22, 0, 6, 8, 20, front='M')
    sc.box(1, 3, 18, 2, 6, 0, 8, front='N')                       # set back under the overhang
    g = sc.render().g
    for y in range(32):
        for x in range(32):
            if g[y][x] == 'L':
                g[y][x] = 'w' if sc.pid[y][x] == 0 else 'N'        # snow on the shelf only
    front_top = 29 - 20                                            # the shelf's lit top edge row
    for i, n in enumerate((4, 6, 3, 5, 7, 4, 2, 5, 6, 3)):        # icicles down its face
        x = 3 + 2 * i
        for k in range(n):
            y = front_top + 1 + k
            if 0 <= y < 32 and g[y][x] in 'M':
                g[y][x] = 'i' if k < n - 1 else 's'
    pal = {'w': SNOW[0], 's': ICE[0], 'i': ICE[1], 'M': STONE[2], 'D': '474751', 'N': '34343e', 'K': '000000'}
    return keep4(g, pal), pal


def frozen_tufts(variant=0):
    """Ground cover, drawn as the ground draws a tuft: grey blades through the snow, no line
    round them, a dot of shadow under the root."""
    rows = ([
        "................",
        "................",
        "................",
        "................",
        "....g.....g.....",
        "....g.g...g..g..",
        ".g..Gg...gG.g...",
        "..g.G.g..G.gG...",
        "..GgG.G..GgG....",
        "...GG.G...GG....",
        "....GGK....GK...",
        ".....K......K...",
        "................",
        "................",
        "................",
        "................"], [
        "................",
        "................",
        "................",
        "................",
        "................",
        ".......g........",
        "...g...g..g.....",
        "...gg.gG.g......",
        "....G.G..G..g...",
        "....GgG.GG.gG...",
        ".....GGK.G.G....",
        "......K..GGK....",
        ".........K......",
        "................",
        "................",
        "................"])[variant]
    g = [list(r) for r in rows]
    return g, {'g': STONE[1], 'G': STONE[2], 'K': '000000'}


# ---------------------------------------------------------------- the expedition camp
def tent():
    """The camp's anchor, built: hide over a ridge pole, its front hide too with the doorway
    dark in it, a pole up each side and crossed over the ridge, snow lying along the ridge and
    drifted against the foot of its far slope."""
    sc = Scene(48, 32, 29)
    sc.gable(0, 6, 32, 0, 9, 0, 15)
    g = sc.render()
    front = [(x, y) for y in range(g.h) for x in range(g.w) if sc.pid[y][x] == 1000 and g.g[y][x] != 'K']
    rows = sorted({y for x, y in front})
    span = {y: (min(x for x, yy in front if yy == y), max(x for x, yy in front if yy == y)) for y in rows}
    top, bot = rows[0], rows[-1]
    xm = (span[bot][0] + span[bot][1]) / 2
    for x, y in front:                                             # the front's hide, the doorway in it
        door = y > top + (bot - top) * 0.35 and abs(x - xm) < (y - top) * 0.32
        g.g[y][x] = 'K' if door else 'D'
    for y in rows:                                                 # a pole up each side
        g.g[y][span[y][0]] = 'p'
        g.g[y][span[y][1]] = 'p'
    xs = span[top]
    xc = (xs[0] + xs[1]) // 2
    for k in range(1, 4):                                          # the poles crossed over the ridge
        for x, y in ((xc - k, top - k), (xc + k, top - k)):
            if 0 < y and 0 < x < g.w - 1:
                g.g[y][x] = 'p'
                if g.g[y - 1][x] == '.':
                    g.g[y - 1][x] = 'K'
    for y in range(g.h):
        for x in range(g.w):
            if g.g[y][x] == 'p':
                for dx, dy in ((1, 0), (-1, 0), (0, -1)):
                    if g.g[y + dy][x + dx] == '.':
                        g.g[y + dy][x + dx] = 'K'
    roof = [(x, y) for y in range(g.h) for x in range(g.w) if sc.pid[y][x] == 0 and g.g[y][x] in 'LMD']
    for x, y in roof:                                              # two seams down the hide
        if (x - y) in (14, 22) and g.g[y][x] in 'LD':
            g.g[y][x] = 'D' if g.g[y][x] == 'L' else 'K'
    first = {}
    for x, y in roof:
        first[x] = min(first.get(x, 99), y)
    for x, y in roof:
        ridge = y - first[x] < 3 and (x + y) % 5 != 0             # snow along the ridge, a little broken
        drift = y > 27 - 0.12 * (x - 20) and x > 20                # and banked against the foot
        if ridge or drift:
            g.g[y][x] = 'w'
    pal = {'L': HIDE[0], 'M': HIDE[0], 'D': HIDE[1], 'p': BARK[1], 'w': SNOW[0], 'K': '000000'}
    return keep4(g.g, pal), pal


def sled():
    g = typed([
        "................................",
        "................................",
        "................................",
        "................................",
        "................................",
        "..........llllllllllllllllll....",
        ".........llllllllllllllllll.....",
        "........llllllllllllllllll......",
        ".......mmmmmmmmmmmmmmmmmmd......",
        ".......dddddddddddddddddd.......",
        "..d......m.......m.......m......",
        ".d.......m.......m.......m......",
        ".d.dddddddddddddddddddddddd.....",
        "..dd............................",
        "................................",
        "................................"])
    for y in range(16):                                            # the slats' gaps across its deck
        for x in range(32):
            if g[y][x] == 'l' and (x + y) % 6 == 0:
                g[y][x] = 'm'
    pal = {'l': WOOD[0], 'm': WOOD[1], 'd': WOOD[2], 'K': '000000'}
    return keep4(outline(g), pal), pal


def skis():
    """Two skis crossed, stuck tails-down in a drift."""
    g = blank(16, 32)
    pick = lambda x, y, t, side: 'm' if side < 0.3 else 'd'
    stroke(g, [(4, 27, 2.4), (10.5, 5, 2.2)], 'm', pick)
    stroke(g, [(10.5, 5, 2.0), (12, 3.5, 1.6)], 'm', pick)                # its tip turned up
    part = blank(16, 32)
    stroke(part, [(12, 27, 2.4), (5.5, 6, 2.2)], 'm', pick)
    stroke(part, [(5.5, 6, 2.0), (4, 4.5, 1.6)], 'm', pick)
    piece(g, part)
    snow = mound(blank(16, 32), 8, 29.5, 5.5, 4.0)
    piece(g, snow)
    pal = {'m': WOOD[1], 'd': WOOD[2], 'w': SNOW[0], 's': SNOW[2], 'K': '000000'}
    return keep4(outline(g), pal), pal


def crate():
    """A supply crate, built, snow on its lid: planks across its face, a brace corner to corner."""
    sc = Scene(16, 16, 13)
    sc.box(0, 2, 9, 0, 3, 0, 7, front='M')
    g = sc.render().g
    face = [(x, y) for y in range(16) for x in range(16) if g[y][x] == 'M']
    x0, x1 = min(x for x, y in face), max(x for x, y in face)
    y0, y1 = min(y for x, y in face), max(y for x, y in face)
    for x, y in face:
        if y == (y0 + y1) // 2 or x in (x0, x1) or round((x - x0) * (y1 - y0) / max(1, x1 - x0)) == y1 - y:
            g[y][x] = 'D'
    for y in range(16):
        for x in range(16):
            if g[y][x] == 'L':
                g[y][x] = 'w'
    pal = {'w': SNOW[0], 'M': WOOD[1], 'D': WOOD[2], 'K': '000000'}
    return keep4(g, pal), pal


def campfire():
    """A ring of stones round charred logs, long cold. It lies flat and is walked over."""
    g = blank(32, 16)
    for i in range(8):                                             # the stones, back to front
        a = math.pi + i * math.pi / 4 + 0.3
        cx, cy = 16 + 10 * math.cos(a), 8.5 + 4 * math.sin(a)
        part = blank(32, 16)
        inside = ellipse(cx, cy, 2.4, 1.8)
        for y in range(16):
            for x in range(32):
                if inside(x, y):
                    part[y][x] = 'd' if (x + 0.5 - cx) + (y + 0.5 - cy) > 0.6 else 'm'
        piece(g, part)
    logs = blank(32, 16)
    stroke(logs, [(9, 10.5, 2.4), (22, 6.5, 2.2)], 'b')
    stroke(logs, [(10, 6.5, 2.2), (23, 10.5, 2.4)], 'b')
    piece(g, logs)
    for x, y in ((14, 8), (17, 8), (19, 9), (12, 9)):              # the char's cracks
        if g[y][x] == 'b':
            g[y][x] = 'K'
    pal = {'m': STONE[1], 'd': STONE[2], 'b': BARK[0], 'K': '000000'}
    return keep4(outline(g), pal), pal


def snowman():
    g = blank(16, 32)
    for cx, cy, rx, ry in ((8, 24, 5.6, 4.6), (8, 16.5, 4.4, 3.8), (8, 10, 3.4, 3.2)):
        part = blank(16, 32)
        inside = ellipse(cx, cy, rx, ry)
        for y in range(32):
            for x in range(16):
                if inside(x, y):
                    u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                    part[y][x] = 's' if u + v > 0.7 else 'w'
        piece(g, part)
    for x, y in ((7, 9), (9, 9), (8, 15), (8, 17), (8, 19)):       # coal: eyes and buttons
        g[y][x] = 'K'
    for x in range(5, 12):                                         # the scarf, its end hanging
        g[13][x] = 'r'
    for y in (14, 15, 16):
        g[y][10] = 'r'
    arms = blank(16, 32)
    stroke(arms, [(3.8, 16, 1.2), (2.6, 12.5, 1.0)], "K")          # twig arms, drawn in the line
    stroke(arms, [(12.2, 16, 1.2), (13.4, 12.5, 1.0)], "K")
    for y in range(32):
        for x in range(16):
            if arms[y][x] != '.' and g[y][x] == '.':
                g[y][x] = 'K'
    pal = {'w': SNOW[0], 's': SNOW[2], 'r': RED[0], 'K': '000000'}
    return keep4(outline(g), pal), pal


# ---------------------------------------------------------------- the mammoth graveyard
def bone_pick(x, y, t, side):
    return 'l' if side < 0.15 else 'm' if side < 0.6 else 'd'


def mammoth_skull():
    """The graveyard's anchor: a mammoth's skull lying in the snow, side on and facing left --
    the high dome of its crown, the broad face dropping steeply from it to the tusks' roots,
    the eye socket and the cheek running back, and the two great tusks sweeping forward and
    down out of the face and curling up in front of it, the far one inside the near one's arc.
    Facing straight out it read as a face or an octopus in the world, three-quarter as a bird
    (redrawn 2026-10-27): the tusks' arcs are what say mammoth. Three tones: the bone's light
    and dark, the snow."""
    W, H = 48, 32
    g = blank(W, H)
    def tusk(pts, pick):
        part = blank(W, H)
        stroke(part, pts, 'l', pick)
        piece(g, part)
    tusk([(26, 22, 4.0), (19, 26.5, 3.4), (13.5, 25.5, 2.8), (10.5, 20.5, 2.2), (11.5, 15, 1.6), (14, 12, 1.0)],
         lambda x, y, t, side: 'l' if side < 0.0 else 'd')                        # the far tusk, behind
    skull = blank(W, H)                                                            # one solid: crown, back, face
    for cx, cy, rx, ry in ((35, 21, 7, 6), (32, 12, 9, 8.5)):
        inside = ellipse(cx, cy, rx, ry)
        for y in range(H):
            for x in range(W):
                if inside(x, y):
                    skull[y][x] = 'l'
    stroke(skull, [(27, 12, 9.0), (24, 22, 9.0)], 'l')
    solid = {(x, y) for y in range(H) for x in range(W) if skull[y][x] == 'l'}
    for x, y in solid:                                                             # its shade along the lower right
        if (x + 2, y + 2) not in solid or (x + 1, y + 3) not in solid:
            skull[y][x] = 'd'
    for x, y in ((31, 18), (32, 18), (33, 19), (34, 19), (35, 19), (36, 20)):    # the cheek running back
        skull[y][x] = 'd'
    piece(g, skull)
    inside = ellipse(28.5, 15.5, 2.4, 2.1)                                         # the eye socket
    for y in range(H):
        for x in range(W):
            if inside(x, y):
                g[y][x] = 'K'
    for x, y in ((33, 5), (34, 6), (35, 6), (36, 7)):                             # a suture over the crown
        g[y][x] = 'd'
    piece(g, mound(blank(W, H), 29, 31, 14, 4))
    tusk([(22, 24, 5.0), (14, 28.5, 4.4), (7, 27.5, 3.6), (3.8, 21.5, 2.8), (4.8, 14.5, 1.9), (8.5, 10.5, 1.1)],
         lambda x, y, t, side: 'l' if side < 0.35 else 'd')                       # the near tusk, in front
    for y in range(H):
        for x in range(W):
            if g[y][x] == 's':
                g[y][x] = 'w'
    pal = {'l': BONE[0], 'd': BONE[2], 'w': SNOW[0], 'K': '000000'}
    return keep4(outline(g), pal), pal


def ribcage():
    """Ribs rising from a drift in a row of arches, the nearest at the left."""
    W, H = 32, 32
    g = blank(W, H)
    for i in reversed(range(4)):                                   # the farthest first
        cx, top = 9.5 + 4.5 * i, 6 + 2 * i
        rx, ry = 5.8 - 0.3 * i, 24 - top
        pts = []
        for k in range(13):
            a = math.pi * k / 12
            pts.append((cx - rx * math.cos(a), 28 - ry * math.sin(a), 2.4 - 0.08 * k))
        part = blank(W, H)
        stroke(part, pts, 'm', bone_pick)
        piece(g, part)
    snow = mound(blank(W, H), 16, 30, 13, 5)
    piece(g, snow)
    for y in range(H):                                             # three tones: the bone's two, the snow
        for x in range(W):
            g[y][x] = {'l': 'm', 's': 'w'}.get(g[y][x], g[y][x])
    pal = {'m': BONE[0], 'd': BONE[2], 'w': SNOW[0], 'K': '000000'}
    return keep4(outline(g), pal), pal


def vertebrae():
    """Three vertebrae and a broken tusk, scattered. Lying flat, walked over."""
    W, H = 32, 16
    g = blank(W, H)
    tusk = blank(W, H)
    stroke(tusk, [(18, 11, 2.6), (24, 10.5, 2.3), (28.5, 7, 1.6)], 'm', bone_pick)
    piece(g, tusk)
    for cx, cy in ((5, 9), (10, 11), (14.5, 8)):
        part = blank(W, H)
        inside = ellipse(cx, cy, 2.6, 2.0)
        for y in range(H):
            for x in range(W):
                if inside(x, y):
                    part[y][x] = 'd' if (x + 0.5 - cx) + (y + 0.5 - cy) > 0.8 else 'l'
        part[int(cy)][int(cx)] = 'K'                               # the spinal hole
        for dx in (-3, 3):                                         # its wings
            x = int(cx) + dx
            if 0 <= x < W and part[int(cy)][x] == '.':
                part[int(cy)][x] = 'm'
        piece(g, part)
    pal = {'l': BONE[0], 'm': BONE[1], 'd': BONE[2], 'K': '000000'}
    return keep4(outline(g), pal), pal


def frost_bush():
    """Bare twigs from one root, rimed white along their upper sides."""
    g = blank(16, 32)
    pick = lambda x, y, t, side: 'm' if side < 0.3 else 'd'
    for pts in ([(8, 29, 2.2), (7.5, 20, 1.8), (5, 12, 1.2), (3.5, 6, 1.0)],
                [(7.5, 20, 1.6), (10.5, 13, 1.2), (12, 7, 1.0)],
                [(8, 25, 1.6), (12.5, 19, 1.0)],
                [(6.5, 16, 1.2), (3, 15, 1.0)],
                [(9.5, 15, 1.0), (8.5, 9, 0.9)]):
        stroke(g, pts, 'm', pick)
    for y in range(1, 32):                                         # rime on whatever has open sky above it
        for x in range(16):
            if g[y][x] in 'md' and g[y - 1][x] == '.' and y < 26:
                g[y][x] = 'w'
    pal = {'w': SNOW[0], 'm': BARK[1], 'd': BARK[2], 'K': '000000'}
    return keep4(outline(g), pal), pal


def snowy_log():
    g = blank(32, 16)
    log_side(g, 3, 25, 7, 13)
    log_end(g, 26, 10.5, 2.6, 3.9)
    snow = lambda x: 6 + 1.2 * math.sin(x * 0.5)                   # snow piled the length of it
    for x in range(4, 26):
        for y in range(int(snow(x)) - 1, 9):
            if 0 <= y < 16 and (g[y][x] != '.' or y >= int(snow(x))):
                g[y][x] = 'w'
    for y in range(16):
        for x in range(32):
            if g[y][x] == 'l':
                g[y][x] = 'm'
    pal = {'w': SNOW[0], 'm': BARK[1], 'd': BARK[2], 'K': '000000'}
    return keep4(outline(g), pal), pal


def fur_thornbush():
    """A low thornbush with a tuft of white fur snagged on it."""
    g = blank(16, 16)
    for pts in ([(8, 13, 1.6), (4, 6, 1.0)], [(8, 13, 1.6), (12, 5, 1.0)], [(8, 13, 1.4), (8, 4.5, 1.0)],
                [(6, 9.5, 1.0), (2.5, 9, 0.9)], [(10, 9, 1.0), (13.5, 10, 0.9)]):
        stroke(g, pts, 'd')
    for x, y in ((5, 7), (11, 7), (3, 8), (13, 9), (8, 6), (6, 11), (10, 11)):   # thorns
        if g[y][x] == '.':
            g[y][x] = 'd'
    fur = blank(16, 16)
    inside = ellipse(10, 7.5, 2.8, 2.0)
    for y in range(16):
        for x in range(16):
            if inside(x, y):
                fur[y][x] = 's' if (y + 0.5 - 7.5) > 0.6 else 'w'
    fur[9][9] = fur[9][11] = 'w'                                   # wisps hanging from it
    piece(g, fur)
    pal = {'w': SNOW[0], 's': SNOW[2], 'd': BARK[2], 'K': '000000'}
    return keep4(outline(g), pal), pal


PROPS = [
    ('ice_spire', ice_spire), ('ice_cluster', ice_cluster), ('ice_block', ice_block),
    ('snow_boulder', snow_boulder), ('icicle_rock', icicle_rock),
    ('frozen_tufts', None),
    ('tent', tent), ('sled', sled), ('skis', skis), ('crate', crate), ('campfire', campfire),
    ('snowman', snowman),
    ('mammoth_skull', mammoth_skull), ('ribcage', ribcage), ('vertebrae', vertebrae),
    ('frost_bush', frost_bush), ('snowy_log', snowy_log), ('fur_thornbush', fur_thornbush),
]


if __name__ == '__main__':
    want = sys.argv[1:]
    for name, make in PROPS:
        if want and name not in want:
            continue
        if name == 'ice_spire':
            os.makedirs(os.path.join(HERE, 'ice_spire_frames'), exist_ok=True)
            frames = [make(k) for k in range(4)]
            for k, (g, pal) in enumerate(frames):
                write(g, pal, os.path.join(HERE, 'ice_spire_frames', f'ice_spire_{k}.png'))
            strip = [sum((f[0][y] for f in frames), []) for y in range(48)]
            write(strip, frames[0][1], os.path.join(HERE, 'ice_spire.png'))
        elif name == 'frozen_tufts':
            tufts = [frozen_tufts(v) for v in range(2)]
            strip = [tufts[0][0][y] + tufts[1][0][y] for y in range(16)]
            write(strip, tufts[0][1], os.path.join(HERE, 'frozen_tufts.png'))
        else:
            g, pal = make()
            write(g, pal, os.path.join(HERE, name + '.png'))
        print(name)
