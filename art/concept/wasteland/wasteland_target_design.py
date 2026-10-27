"""The wasteland's visual target: the whole biome restyled after the user's
Yume Nikki references (Desktop/insp, 2026-10-27), everything but the island
mountains. A mock-up, not wired into the game: it guides the tiles, props and
layouts still to be drawn.

    python art/concept/wasteland/wasteland_target_design.py [mountain.png]

mountain.png is a halved crop of a real `SHOT_KIND=waste shot.exe` render
(the cliffs are drawn by code, not the sheet); without it the scene has none.

What each thing in the wasteland becomes:
  ground       the cracked earth kept, with worn bands in dirt's shade
  lava         the void: 2c0c47, whole marks in 301b5a/3b2a58, a 110000 drop
  red pool     the void in the reds, rare
  lava bridge  a stone causeway in the bridges' geometry
  dead tree    the red figures, in stands
  village      the barracks huts in the maze's stone, inside a walled compound
  ruins        the entrance at the heart of a wall maze (stone yard walls)
  landmark     a lone gate standing in the waste, the chest before it
  props        shore rubble, fallen wall, red stand, bones

Writes wasteland_target.png (1:1), wasteland_target_x3.png and
wasteland_pieces.png beside this file.
"""
import os, random, sys
from collections import deque
from math import hypot  # noqa
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from prop_paint import paint

T = 16
TW, TH = 48, 30
W, H = TW * T, TH * T


def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


K = rgb('000000')
# the floor after the references (the user, 2026-10-27): a flat red-brown -- not the maroon, which
# read violet -- with broad flat blocks of a lighter ground stepped a tile at a time, grit only under
# the rubble, lighter worn bands; trails retoned to match
GROUND, CRACK = rgb('3e1c0e'), rgb('110000')
BLOCK_T = rgb('583518')                                      # the broad lighter blocks
CLOD = rgb('583518')                                         # the plain ground's rare clod
GRIT_D = rgb('270800')                                       # grit, round the rubble's feet
BAND = rgb('633e1b')                                         # the worn bands
TRAIL, TRAIL_EDGE = rgb('633e1b'), rgb('270800')
VOID, VOID_A, VOID_B = rgb('2c0c47'), rgb('301b5a'), rgb('3b2a58')
POOL, POOL_A = rgb('7c0a1b'), rgb('b70000')
# waste stone: built stone a step darker, sitting in the gloom as the references' blocks do
STONE = [rgb(c) for c in ('9797aa', '595965', '34343e')]      # lit, base, dark
WASTE_STONE = {'c6ccda': '9797aa', '9797aa': '595965', '595965': '34343e'}
SLAB = [rgb(c) for c in ('5e486a', '3b2a58', '2b1f40')]       # the purple slabs
RED = {'l': rgb('ec8476'), 'm': rgb('b70000'), 'd': rgb('7c0a1b')}
ROCK = {'l': rgb('595965'), 'm': rgb('595965'), 'd': rgb('34343e')}   # rock: base and shade, no lit; grey
BONE = {'l': rgb('e8e0c0'), 'm': rgb('b2966a'), 'd': rgb('8d6b4f')}

R = random.Random(1027)


# ---------------------------------------------------------------- the map
# The void comes in pools, laid as the game lays its ponds and lava pools: tiles under
# radius-2 brushes (paint_stream_brush), a few overlapping for a bigger pool. 1 void, 2 red.
LIQ_T = [[0] * TW for _ in range(TH)]


def brush(cx, cy, kind, r=2):
    for by in range(-r, r + 1):
        for bx in range(-r, r + 1):
            if bx * bx + by * by <= r * r and 0 <= cx + bx < TW and 0 <= cy + by < TH:
                LIQ_T[cy + by][cx + bx] = kind


for c in ((36, 2), (36, 4), (37, 7), (36, 9), (36, 11)):     # the long pool, the level causeway over it
    brush(*c, 1)
for c in ((26, 22), (28, 23), (30, 24), (32, 26)):  # the south pool, the slanted one over it
    brush(*c, 1)
for c in ((11, 23), (12, 24)):                                # small pools
    brush(*c, 1)
brush(21, 4, 1)
brush(44, 23, 1); brush(45, 25, 1)
brush(44, 6, 2); brush(45, 8, 2, r=1)                         # the red pool, rare

KEEP_LAND = [(31, 5, 33, 8), (40, 5, 41, 8),                  # causeway heads, in tiles
             (22, 26, 26, 28), (31, 17, 34, 19)]
for x0, y0, x1, y1 in KEEP_LAND:
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            LIQ_T[ty][tx] = 0


def cover_hash(x, y, salt):
    """src/tilemap.cpp cover_hash, in 32 bits."""
    m = 0xFFFFFFFF
    h = ((x * 73856093) & m) ^ ((y * 19349663) & m) ^ salt
    h ^= h >> 13
    h = (h * 1274126177) & m
    h ^= h >> 16
    return h


# edge_coverage's weights: each of the 3x3 tiles round a pixel by nearness, kernel 1.6 tiles
KR = 1.6
WEIGHTS = []
for py in range(T):
    for px in range(T):
        u, v = (px + .5) / T, (py + .5) / T
        ws = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ex, ey = u - (dx + .5), v - (dy + .5)
                t = 1 - (ex * ex + ey * ey) / (KR * KR)
                if t > 0:
                    ws.append((dx, dy, t * t))
        WEIGHTS.append(ws)
SHORE_JITTER, SHORE_BAND = .025, .05

# per pixel: 0 land, 1 void, 2 red; RIM marks the band on the land side, as water's shallows
LIQ = [[0] * W for _ in range(H)]
RIM = set()
for ty in range(TH):
    for tx in range(TW):
        variant = cover_hash(tx, ty, 0xF7149E00) % 2
        for py in range(T):
            for px in range(T):
                ws = WEIGHTS[py * T + px]
                den = sum(w for _, _, w in ws)
                cov = {1: 0.0, 2: 0.0}
                for dx, dy, w in ws:
                    x, y = tx + dx, ty + dy
                    k = LIQ_T[y][x] if 0 <= x < TW and 0 <= y < TH else 0
                    if k:
                        cov[k] += w
                th = .5 + SHORE_JITTER * ((cover_hash(px, py, 0x54093E00 + variant) % 2001) / 1000 - 1)
                X, Y = tx * T + px, ty * T + py
                for k in (1, 2):
                    f = cov[k] / den
                    if f >= th:
                        LIQ[Y][X] = k
                    elif f >= th - SHORE_BAND and not LIQ[Y][X]:
                        RIM.add((X, Y))


def is_void(px, py):
    return 0 <= px < W and 0 <= py < H and LIQ[py][px] == 1


def is_pool(px, py):
    return 0 <= px < W and 0 <= py < H and LIQ[py][px] == 2


def rough_mask(tw, th, near, seed, share=.17, reach=1.5, cell=10, sub=1):
    """Where the rough ground lies, in half tiles: a slow value noise (patches some 4-12 tiles
    across) cut to about `share` of the ground, and grown within `reach` tiles of the tiles in
    `near` (pools, rock, walls) -- the references' rough lies round the edges of a place. The
    grid, `sub` cells a tile, is what steps its edges, as the references' patches step."""
    rr = random.Random(seed)
    gw, gh = tw // cell + 3, th // cell + 3
    grid = [[rr.random() for _ in range(gw)] for _ in range(gh)]

    def noise(x, y):
        fx, fy = x / cell, y / cell
        ix, iy = int(fx), int(fy)
        u, v = fx - ix, fy - iy
        u, v = u * u * (3 - 2 * u), v * v * (3 - 2 * v)
        a = grid[iy][ix] * (1 - u) + grid[iy][ix + 1] * u
        b = grid[iy + 1][ix] * (1 - u) + grid[iy + 1][ix + 1] * u
        return a * (1 - v) + b * v

    hw, hh = tw * sub, th * sub
    dist = [[99.0] * hw for _ in range(hh)]                   # half tiles to the nearest `near` tile
    q = deque()
    for (x, y) in near:
        for j in range(sub):
            for i in range(sub):
                hx, hy = x * sub + i, y * sub + j
                if 0 <= hx < hw and 0 <= hy < hh and dist[hy][hx]:
                    dist[hy][hx] = 0
                    q.append((hx, hy))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < hw and 0 <= ny < hh and dist[ny][nx] > dist[y][x] + 1:
                dist[ny][nx] = dist[y][x] + 1
                q.append((nx, ny))
    vals = sorted(noise(x / sub, y / sub) for y in range(hh) for x in range(hw))
    cut = vals[int(len(vals) * (1 - share))]
    return [[noise(x / sub, y / sub) + max(0.0, .22 * (1 - dist[y][x] / (reach * sub))) * (1 if dist[y][x] < reach * sub else 0) >= cut
             for x in range(hw)] for y in range(hh)]


def paint_floor(im, rough):
    """The floor: plain red-brown with a rare clod, and where rough(px, py) holds, a broad flat block
    of the lighter ground. Placed by a fixed hash so any two pieces of it agree."""
    q = im.load()
    for py in range(im.height):
        for px in range(im.width):
            if rough(px, py):
                q[px, py] = BLOCK_T
            elif cover_hash(px, py, 0x6A17C0DE) % 1000 < 2 and px + 1 < im.width and not rough(px + 1, py):
                q[px, py] = CLOD
                q[px + 1, py] = CLOD
            elif q[px, py] != CLOD or q[px, py][3] == 0:
                q[px, py] = GROUND


def grit_under(q, w, h, px, py, rr):
    """Two to four grains of grit round a rock's foot, on whatever ground it lies on."""
    for _ in range(rr.randrange(2, 5)):
        x, y = px + rr.randrange(-6, 7), py + rr.randrange(0, 3)
        if 0 <= x < w and 0 <= y < h and q[x, y] in (GROUND, BLOCK_T):
            q[x, y] = GRIT_D


img = Image.new('RGBA', (W, H), GROUND)
P = img.load()

# the floor: rough round the pools and through the maze, plain in the open middles
ROUGH = rough_mask(TW, TH, [(x, y) for y in range(TH) for x in range(TW) if LIQ_T[y][x]]
                   + [(x, y) for x in range(22, 35) for y in range(6, 19) if (x + y) % 5 == 0], seed=7)


def rough(px, py):
    return ROUGH[py // T][px // T]


paint_floor(img, rough)

# worn bands: long stripes north to south, after the totem court and the pyramid field
BANDS = [(3, 18, 30, 2), (7, 19, 29, 1), (25, 2, 8, 2), (29, 3, 8, 1), (44, 15, 29, 2)]
for bx, y0, y1, bw in BANDS:
    for py in range(y0 * T, y1 * T):
        for px in range(bx * T, (bx + bw) * T):
            edge = min(px - bx * T, (bx + bw) * T - 1 - px, py - y0 * T, y1 * T - 1 - py)
            if edge < 3 and (px + py) % (2 + edge) != 0:
                continue                                       # the grounds' stippled fringe
            if P[px, py] == GROUND and not rough(px, py):
                P[px, py] = BAND
# a cross band, the stripes joined as in the totem court
for py in range(24 * T + 4, 25 * T + 4):
    for px in range(3 * T, 9 * T):
        if P[px, py] == GROUND and not rough(px, py) and not (py in (24 * T + 4, 25 * T + 3) and px % 2):
            P[px, py] = BAND

# the void and the red pool: hard-edged on the smoothed field, the band on the land side
for py in range(H):
    for px in range(W):
        if LIQ[py][px] == 1:
            P[px, py] = VOID
        elif LIQ[py][px] == 2:
            P[px, py] = POOL
for x, y in RIM:
    if not LIQ[y][x]:
        P[x, y] = CRACK


def wet(x, y):
    return 0 <= x < W and 0 <= y < H and LIQ[y][x] != 0


def land(x, y):
    return 0 <= x < W and 0 <= y < H and not wet(x, y)


# whole marks on the void, as the water's foam
for _ in range(700):
    px, py = R.randrange(W), R.randrange(H)
    n = R.choice((3, 4, 5))
    if all(is_void(px + i, py + j) and P[px + i, py + j] == VOID for i in range(-2, n + 2) for j in (-3, -2, -1, 0, 1, 2)):
        tone = VOID_A if R.random() < .7 else VOID_B
        for i in range(n):
            P[px + i, py] = tone
        if n >= 4 and R.random() < .5:
            P[px + 1, py - 1] = tone
            P[px + n - 2, py - 1] = tone
for _ in range(60):
    px, py = R.randrange(42 * T, 47 * T), R.randrange(4 * T, 10 * T)
    if all(P[px + i, py] == POOL for i in range(-1, 4)):
        for i in range(3):
            P[px + i, py] = POOL_A

# ---------------------------------------------------------------- the trail
ROUTE = [
    [(0, 18.6), (4, 18.6), (7.5, 18.0), (7.6, 16.4), (8.5, 15.2), (16, 15.0), (18.6, 14.6), (22, 15.2),
     (27, 15.2), (29.3, 14.0)],
    [(22, 15.2), (24.5, 17.2), (30, 17.6), (32.5, 18.3)],
    [(29.3, 14.0), (31.6, 11.0), (31.7, 8.4), (32.5, 6.9)],
]


def stamp_trail(route):
    pts = []
    for (ax, ay), (bx, by) in zip(route, route[1:]):
        n = int(hypot(bx - ax, by - ay) * 16)
        for i in range(n + 1):
            t = i / max(n, 1)
            pts.append(((ax + (bx - ax) * t) * T, (ay + (by - ay) * t) * T))
    pave = set()
    for x, y in pts:
        for dy in range(-10, 11):
            for dx in range(-11, 12):
                if dx * dx + dy * dy <= 112:
                    pave.add((int(x + dx), int(y + dy)))
    return pave


pave = set()
for r in ROUTE:
    pave |= stamp_trail(r)
edge = set()
for x, y in pave:                                              # three rows of edge above, one below
    for k in (1, 2, 3):
        if (x, y - k) not in pave:
            edge.add((x, y - k))
    if (x, y + 1) not in pave:
        edge.add((x, y + 1))
    for dx in (-1, 1):
        if (x + dx, y) not in pave:
            edge.add((x + dx, y))
for x, y in edge - pave:
    if 0 <= x < W and 0 <= y < H and not is_void(x, y):
        P[x, y] = TRAIL_EDGE
for x, y in pave:
    if 0 <= x < W and 0 <= y < H and not is_void(x, y):
        P[x, y] = TRAIL

# ---------------------------------------------------------------- causeways
def causeway(deck, face_h=8, piers=True):
    """A stone deck from above, its front in courses, its east side flat and dark, piers
    standing in the void, a black line round the whole: the bridges' geometry in stone."""
    if not deck:
        return
    bottom = max(y for _, y in deck)
    out = {}
    for x, y in deck:
        out[(x, y)] = STONE[0] if (y % 8 != 0) else STONE[1]   # slabs: lit, seams in the base
    cols = {}
    for x, y in deck:
        if (x, y + 1) not in deck:
            cols.setdefault(x, []).append(y)
    for x, ys in cols.items():
        for yb in ys:
            front = yb == bottom
            for k in range(1, face_h + 1):
                if (x, yb + k) in deck:
                    break
                y = yb + k
                if front:
                    row = (k - 1) % 4
                    off = 3 if ((k - 1) // 4) % 2 else 0
                    c = STONE[0] if row == 0 else STONE[2] if (x + off) % 6 == 5 or row == 3 else STONE[1]
                else:
                    c = STONE[2]
                out.setdefault((x, y), c)
    if piers:
        xs = sorted(cols)
        for x in xs:
            for yb in cols[x]:
                if yb == bottom and (x - xs[0]) % 32 in range(10, 16):
                    for k in range(face_h + 1, face_h + 7):
                        if is_void(x, yb + k):
                            out.setdefault((x, yb + k), STONE[2] if (x - xs[0]) % 32 < 15 else STONE[2])
    ink = set(out)
    for x, y in list(ink):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in ink:
                out[q] = K
    for (x, y), c in out.items():
        if 0 <= x < W and 0 <= y < H:
            P[x, y] = c


# level: from the mainland's shore east to the far island
level = {(x, y) for x in range(int(32.6 * T), int(40.6 * T)) for y in range(6 * T + 4, 6 * T + 28)}
causeway(level)
# slanted, crossing the moat: lower left on the ring's inside, up and to the right a pixel a row
y_lo, y_hi, x_lo = 27 * T + 8, 18 * T + 8, 23 * T + 8
slant = {(x_lo + (y_lo - y) + i, y) for y in range(y_hi, y_lo + 1) for i in range(24)}
causeway(slant)

# ---------------------------------------------------------------- standing things
stand = []                                                     # (ground line, x, image)


def put(im, x, y_ground, anywhere=True):
    if not anywhere and (wet(int(x + im.width // 2), int(y_ground) - 1) or wet(int(x + 1), int(y_ground) - 1)
                         or wet(int(x + im.width - 2), int(y_ground) - 1)):
        return                                                 # nothing stands in the void
    stand.append((y_ground, x, im))


def grid_image(g, ramp):
    h, w = len(g), len(g[0])
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for y in range(h):
        for x in range(w):
            c = g[y][x]
            if c == 'K':
                im.putpixel((x, y), K)
            elif c in ramp:
                im.putpixel((x, y), ramp[c])
    return im


def outlined(mask, ramp, g=None):
    h, w = len(mask) + 2, len(mask[0]) + 2
    m = [[False] * w for _ in range(h)]
    for y, row in enumerate(mask):
        for x, v in enumerate(row):
            m[y + 1][x + 1] = v
    g = paint(m) if g is None else g
    for y in range(h):
        for x in range(w):
            if not m[y][x] and any(0 <= x + dx < w and 0 <= y + dy < h and m[y + dy][x + dx]
                                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g[y][x] = 'K'
    return grid_image(g, ramp)


# the mini volcanoes (the user, 2026-10-27: "red stands should be like mini volcanos"): a broad
# red cone, slopes flaring to the foot, a notched crater at the top -- three sizes
VOLCANOES = [(31, 20, 7, 1), (25, 16, 6, 2), (19, 13, 5, 3), (13, 9, 3, 4)]   # width, height, crater, seed


def volcano(n):
    vw, vh, cw, seed = VOLCANOES[n]
    rr = random.Random(seed)
    w, h = vw + 2, vh + 2                                      # room for the line round it
    cx = w / 2
    m = [[False] * w for _ in range(h)]
    half = []
    for y in range(vh):
        t = y / (vh - 1)
        hw = cw / 2 + (vw / 2 - cw / 2) * t ** 1.15            # a cone, just flaring at the foot
        half.append(hw)
        for x in range(w):
            if abs(x + .5 - cx) <= hw:
                m[y + 1][x] = True
    nick = rr.randrange(vh // 3, vh - 2) + 1                   # a bite out of one slope
    side = rr.choice((-1, 1))
    row = [x for x in range(w) if m[nick][x]]
    if len(row) > 6:
        m[nick][row[0] if side < 0 else row[-1]] = False
    g = [['.'] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if not m[y][x]:
                continue
            hw = half[y - 1]
            u = (x + .5 - cx) / hw                             # -1 the left slope, +1 the right
            if y >= h - 3 or u > .4:
                g[y][x] = 'd'                                  # massed low and on the right
            elif u < -.55 and y < 1 + vh * .6 and (x == 0 or not m[y][x - 1] or not m[y][x - 2]):
                g[y][x] = 'l'                                  # lit, sparse, high on the left
            else:
                g[y][x] = 'm'
    # the crater: its rim lit on the left lip, its mouth black, a dark tongue inside
    for x in range(w):
        if m[1][x]:
            dxc = x + .5 - cx
            g[1][x] = 'K' if abs(dxc) < cw / 2 - .5 else 'l' if dxc < 0 else 'd'
        if m[2][x] and abs(x + .5 - cx) < cw / 2 - 1.5:
            g[2][x] = 'd'                                      # the crater's throat
    return _ink(m, g, RED)


def _ink(m, g, ramp):
    h, w = len(m), len(m[0])
    for y in range(h):
        for x in range(w):
            if not m[y][x] and any(0 <= x + dx < w and 0 <= y + dy < h and m[y + dy][x + dx]
                                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g[y][x] = 'K'
    return grid_image(g, ramp)


def rock(rw, rh, seed):
    rr = random.Random(seed)
    m = [[((x - rw / 2 + .5) / (rw / 2)) ** 2 + ((y - rh / 2 + .5) / (rh / 2)) ** 2 <= 1.05 - rr.random() * .1
          for x in range(rw)] for y in range(rh)]
    h, w = rh + 2, rw + 2
    big = [[False] * w for _ in range(h)]
    for y, row in enumerate(m):
        for x, v in enumerate(row):
            big[y + 1][x + 1] = v
    g = [['m' if big[y][x] else '.' for x in range(w)] for y in range(h)]
    for y in range(h):
        for x in range(w):
            if big[y][x] and (not big[y + 1][x] or not big[y][x + 1] or (y > h * .6 and x > w * .45)):
                g[y][x] = 'd'                                  # shade massed low and on the right
    if rw >= 9:
        cx = w // 2 + rr.randrange(-1, 1)
        for k in range(3):                                     # a crack slanting down its front
            if big[2 + k][cx + k] and g[2 + k][cx + k] == 'm':
                g[2 + k][cx + k] = 'K'
    return _ink(big, g, ROCK)


def bone():
    rows = ['.KK.......KK.',
            'KlmK.....KlmK',
            'KmlmKKKKKmmdK',
            '.KmllllmmmdK.',
            'KmmdKKKKKmmdK',
            'KmdK.....KddK',
            '.KK.......KK.']
    return grid_image([list(r) for r in rows], BONE)


def stone_post_stub(n):
    """A fallen wall's stub: a few courses of the maze's stone, its top lit, its east side dark."""
    w, h = 6 * n + 2, 10
    im = Image.new('RGBA', (w + 3, h + 3), (0, 0, 0, 0))
    q = im.load()
    for y in range(3, h + 3):
        for x in range(0, w):
            row = (y - 3) % 4
            off = 3 if ((y - 3) // 4) % 2 else 0
            q[x, y] = STONE[0] if row == 0 else STONE[2] if (x + off) % 6 == 5 or row == 3 else STONE[1]
    for k in range(3):                                         # the top, going back up and right
        for x in range(w):
            q[x + k + 1, 2 - k] = STONE[0]
        for y in range(3 - k, h + 3 - k):
            q[w + k, y] = STONE[2]
    ink = {(x, y) for y in range(h + 3) for x in range(w + 3) if q[x, y][3]}
    out = Image.new('RGBA', (w + 5, h + 5), (0, 0, 0, 0))
    o = out.load()
    for x, y in ink:
        o[x + 1, y + 1] = q[x, y]
    for x, y in ink:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in ink:
                o[x + dx + 1, y + dy + 1] = K
    return out


def lone_gate():
    """The landmark: a doorway of the maze's stone standing alone in the waste, ground seen
    through it. Two piers in courses, a lintel, the oblique top and east side."""
    w, h, d = 36, 40, 5
    im = Image.new('RGBA', (w + d + 2, h + d + 2), (0, 0, 0, 0))
    q = im.load()
    body = set()
    for y in range(h):
        for x in range(w):
            if y >= 10 and 9 <= x < w - 9:
                continue                                       # the opening
            body.add((x, y))
    for x, y in body:
        row = y % 4
        off = 3 if (y // 4) % 2 else 0
        c = STONE[0] if row == 0 else STONE[2] if (x + off) % 6 == 5 or row == 3 else STONE[1]
        if 10 <= y <= 13 and 9 <= x < w - 9 and (x - 9) % 6 in (0,):
            c = STONE[2]
        q[x + 1, y + d + 1] = c
    for k in range(1, d + 1):
        for x in range(w):
            q[x + k + 1, d - k + 1] = STONE[0]
        for y in range(h):
            if (w - 1, y) in body:
                q[w + k, y + d + 1 - k] = STONE[2]
        for y in range(10, h):                                 # the inner face of the right pier
            if q[w - 9 + k, y + d + 1 - k][3] == 0 and k <= 3:
                q[w - 9 + k - 1 + 1, y + d + 1 - k] = STONE[2]
    a = im.getchannel('A').load()
    ink = {(x, y) for y in range(im.height) for x in range(im.width) if a[x, y]}
    for x, y in list(ink):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in ink and 0 <= x + dx < im.width and 0 <= y + dy < im.height:
                q[x + dx, y + dy] = K
    return im


def recolour(im, mapping):
    im = im.copy()
    q = im.load()
    for y in range(im.height):
        for x in range(im.width):
            c = q[x, y]
            if c[3]:
                h = '%02x%02x%02x' % c[:3]
                if h in mapping:
                    q[x, y] = rgb(mapping[h])
    return im


# the walls: the game's stone yard-wall pieces, arms W 1, E 2, SW 4, NE 8
yard = Image.open(os.path.join(ROOT, 'art', 'structures', 'entrances', 'yard_walls.png')).convert('RGBA')
yard = recolour(yard, WASTE_STONE)
SLAB_MAP = {'c6ccda': '5e486a', '9797aa': '3b2a58', '595965': '2b1f40'}
WALL = {}
SLABS = set()


def run(x0, x1, y, slab=()):
    for x in range(x0, x1 + 1):
        WALL[(x, y)] = True
        if x in slab:
            SLABS.add((x, y))


def back(x, y, n, slab=()):
    """A run going back at 45 degrees: up a tile for every tile across."""
    for i in range(n + 1):
        WALL[(x + i, y - i)] = True
        if i in slab:
            SLABS.add((x + i, y - i))


# the barracks compound: a parallelogram, its gate south, broken through on the east
run(1, 6, 17); run(9, 15, 17)
run(8, 15, 10); run(18, 22, 10)
back(1, 17, 7)
back(15, 17, 1); back(19, 13, 3)
# the ruin maze round the ruins' mouth, after images (2)
run(22, 26, 18); run(29, 31, 18)
back(26, 18, 2); back(31, 18, 3)
run(23, 26, 12); back(23, 12, 3)
run(33, 34, 13)
run(26, 30, 7); back(26, 7, 0)
run(36, 37, 19)                                        # a lone length out in the waste
WALL.pop((31, 18), None)


def wall_piece(x, y):
    n = (1 if (x - 1, y) in WALL else 0) | (2 if (x + 1, y) in WALL else 0) \
        | (4 if (x - 1, y + 1) in WALL else 0) | (8 if (x + 1, y - 1) in WALL else 0)
    im = yard.crop(((16 + n) * T, 0, (17 + n) * T, 2 * T))
    return recolour(im, SLAB_MAP) if (x, y) in SLABS else im


for (x, y) in WALL:
    put(wall_piece(x, y), x * T, y * T + 12)

# the ruins' mouth, at the heart of the maze
ruins = recolour(Image.open(os.path.join(ROOT, 'art', 'structures', 'entrances', 'ruins.png')).convert('RGBA'), WASTE_STONE)
put(ruins, 24 * T, 17 * T)

# the barracks, in the maze's stone under purple slate; the well in the same stone
huts = Image.open(os.path.join(ROOT, 'art', 'structures', 'villages', 'waste.png')).convert('RGBA')
HUT_MAP = {'292931': '595965', '1e1e24': '34343e', '34343e': '9797aa', '474751': '3b2a58'}
hut_a = recolour(huts.crop((2, 0, 57, 80)), HUT_MAP)
hut_b = recolour(huts.crop((66, 0, 139, 80)), HUT_MAP)
well = recolour(huts.crop((245, 0, 267, 80)), HUT_MAP)
put(hut_a, 8 * T, 14 * T - 2)
put(hut_b, 8 * T + 55, 14 * T - 2)
put(well, 18 * T, 13 * T)

# the lone gate and its chest, in an open stretch of the waste
put(lone_gate(), 4 * T, 23 * T)
chest = Image.open(os.path.join(ROOT, 'art', 'structures', 'landmarks', 'chest.png')).convert('RGBA').crop((0, 0, 16, 16))
put(chest, 5 * T + 4, 24 * T + 4)

# red stands: the far island, the red pool's shore, and lone figures where dead trees stood
def ring_pts(cx, cy, rx, ry, n, a0=0.0, gap=None):
    """n points round an ellipse, leaving out those within `gap` (centre angle, half width) radians."""
    from math import cos, sin, pi, atan2
    out = []
    for k in range(n):
        a = a0 + 2 * pi * k / n
        if gap and abs(atan2(sin(a - gap[0]), cos(a - gap[0]))) < gap[1]:
            continue
        out.append((cx + rx * cos(a), cy + ry * sin(a), sin(a)))
    return out


def stand_pts(kind, cx, cy, rr, gap=None):
    """Where a stand's cones go, as (x, ground line, size) in pixels: a grove packs an ellipse on a
    jittered grid, big cones in the middle and back, small at the edges; a double ring hugs a red
    pool's shore."""
    pts = []
    if kind == 'grove':
        rx, ry = 55, 35
        for j, y in enumerate(range(-ry, ry + 1, 11)):
            for x in range(-rx + (10 if j % 2 else 0), rx + 1, 20):
                d = (x / rx) ** 2 + (y / ry) ** 2
                if d > 1:
                    continue
                d = d ** .5 - (.12 if y < 0 else 0)
                size = 0 if d < .4 else 1 if d < .65 else 2 if d < .88 else 3
                pts.append((cx + x + rr.randrange(-4, 5), cy + y + rr.randrange(-2, 3), size))
    else:
        for x, y, sn in ring_pts(cx, cy, 58, 40, 8, rr.random(), gap):
            pts.append((x, y, 1 if sn < 0 else 2))
        for x, y, sn in ring_pts(cx, cy, 84, 58, 11, rr.random(), gap):
            pts.append((x, y, 0 if sn < 0 else 1))
    return pts


from math import pi as _pi
STANDS = [(x / T, y / T, n) for x, y, n in stand_pts('ring', 44.9 * T, 7.3 * T, random.Random(5), gap=(_pi, .55))]
STANDS += [(x / T, y / T, n) for x, y, n in stand_pts('grove', 37.0 * T, 21.2 * T, random.Random(6))]
STANDS += [(24.4, 3.0, 2), (2.6, 21.0, 3), (11.5, 7.4, 3)]
GROVES = [(37.0 * T, 21.2 * T, 62, 42)]
for fx, fy, n in STANDS:
    im = volcano(n)
    put(im, int(fx * T) - im.width // 2, int(fy * T), anywhere=False)

# rubble massed along the shores, a pile in each dead end, bones
def near_void(px, py, r):
    return any(is_void(px + dx, py + dy) for dx in (-r, 0, r) for dy in (-r, 0, r))


occupied = []
for _ in range(2600):
    px, py = R.randrange(8, W - 8), R.randrange(8, H - 4)
    if is_void(px, py) or P[px, py] in (TRAIL, TRAIL_EDGE, K) or P[px, py] in STONE or not (near_void(px, py, 22) or rough(px, py)) or near_void(px, py, 5):
        continue
    if (px // T, py // T) in WALL or any(abs(px - ox) < 10 and abs(py - oy) < 8 for ox, oy in occupied):
        continue
    if 8 * T < px < 23 * T and 9 * T < py < 18 * T:
        continue
    clump = (px // 96 + py // 96) % 3 != 0
    if R.random() > ((.09 if clump else .015) if near_void(px, py, 22) else .025):
        continue
    if any(((px - gx) / grx) ** 2 + ((py - gy) / gry) ** 2 < 1 for gx, gy, grx, gry in GROVES):
        continue
    occupied.append((px, py))
    grit_under(P, W, H, px, py, R)
    s = R.random()
    im = rock(4, 3, px) if s < .55 else rock(7, 5, px) if s < .88 else rock(11, 8, px)
    put(im, px - im.width // 2, py, anywhere=False)
for px, py, n in ((27.4 * T, 13.6 * T, 3), (22.6 * T, 11.6 * T, 2), (36.4 * T, 18.6 * T, 2), (1.6 * T, 9.5 * T, 3)):
    for k in range(n):
        im = rock(R.choice((4, 7)), R.choice((3, 5)), int(px + k))
        put(im, int(px + k * 7) - im.width // 2, int(py + (k % 2) * 4), anywhere=False)
for px, py in ((10.2 * T, 19.6 * T), (37.0 * T, 21.6 * T)):
    img.alpha_composite(bone(), (int(px), int(py)))           # lying flat: walked over

# fallen wall: stubs of the maze's stone strayed from it
put(stone_post_stub(2), 36 * T + 6, 24 * T + 6, anywhere=False)
put(stone_post_stub(1), 9 * T, 21 * T, anywhere=False)
put(stone_post_stub(1), 21 * T + 4, 19 * T + 2, anywhere=False)

# the player, on the trail by the gate, for scale
player = Image.open(os.path.join(ROOT, 'assets', 'player_small.png')).convert('RGBA').crop((0, 0, 14, 20))
put(player, int(19.6 * T), int(15.7 * T))

# the island mountain, unchanged: a halved crop of the game's own render
if len(sys.argv) > 1:
    mt = Image.open(sys.argv[1]).convert('RGBA')
    img.alpha_composite(mt, (0, 0))   # its ground cleared: the scene's ground shows through

for yg, x, im in sorted(stand, key=lambda s: (s[0], s[1])):
    img.alpha_composite(im, (int(x), int(yg - im.height)))

img.save(os.path.join(HERE, 'wasteland_target.png'))
img.resize((W * 3, H * 3), Image.NEAREST).save(os.path.join(HERE, 'wasteland_target_x3.png'))

# ---------------------------------------------------------------- the pieces board
S = 4
plain_sw = Image.new('RGBA', (64, 48)); paint_floor(plain_sw, lambda x, y: False)
rough_sw = Image.new('RGBA', (64, 48)); paint_floor(rough_sw, lambda x, y: x >= 32 or y >= 32)
board_items = [
    ('plain ground', '3e1c0e, clod 583518', plain_sw),
    ('ground block, stepped a tile', '583518 on 3e1c0e', rough_sw),
    ('void pool (ground)', '2c0c47 / 301b5a 3b2a58 / 110000 rim', img.crop((42 * T, 20 * T, 48 * T, 28 * T))),
    ('red pool (ground)', '7c0a1b / b70000', img.crop((41 * T, 3 * T, 48 * T, 11 * T))),
    ('worn band (ground)', '633e1b on 3e1c0e', img.crop((2 * T, 26 * T, 6 * T, 29 * T))),
    ('causeway, level (built)', 'waste stone 9797aa 595965 34343e', img.crop((32 * T, 5 * T, 37 * T, 8 * T + 8))),
    ('causeway, back (built)', 'stone; east face 595965', img.crop((25 * T, 21 * T, 31 * T, 28 * T + 8))),
    ('wall run (built)', 'yard wall in stone, one colour', None),
    ('barracks hut (built)', 'stone; slate 3b2a58', hut_b),
    ('well (built)', 'stone, wood', well),
    ('lone gate (landmark)', 'stone', lone_gate()),
    ('mini volcanoes (object)', 'ec8476 b70000 7c0a1b + black', None),
    ('rubble (object)', '595965 34343e + black', None),
    ('bones / fallen wall', 'bone; stone', None),
]
# composites for the rows that are groups
strip = Image.new('RGBA', (80, 34), (0, 0, 0, 0))
for i, x in enumerate(range(4)):
    p = wall_piece(10 + i, 10) if False else yard.crop(((16 + (1 if i else 0) + (2 if i < 3 else 0)) * T, 0,
                                                        (17 + (1 if i else 0) + (2 if i < 3 else 0)) * T, 2 * T))
    strip.alpha_composite(p, (i * 16, 0))
board_items[7] = (board_items[7][0], board_items[7][1], strip)
figs = Image.new('RGBA', (104, 22), (0, 0, 0, 0))
x = 0
for n in range(4):
    f = volcano(n)
    figs.alpha_composite(f, (x, 22 - f.height))
    x += f.width + 2
board_items[11] = (board_items[11][0], board_items[11][1], figs)
rk = Image.new('RGBA', (40, 14), (0, 0, 0, 0))
rk.alpha_composite(rock(4, 3, 1), (0, 14 - 5)); rk.alpha_composite(rock(7, 5, 2), (8, 14 - 7))
rk.alpha_composite(rock(11, 8, 3), (20, 14 - 10))
board_items[12] = (board_items[12][0], board_items[12][1], rk)
bs = Image.new('RGBA', (44, 20), (0, 0, 0, 0))
bs.alpha_composite(bone(), (0, 8)); bs.alpha_composite(stone_post_stub(2), (16, 0))
board_items[13] = (board_items[13][0], board_items[13][1], bs)

BG = rgb('1e1e24')
col_w, pad = 3, 14
cells_w = [max(it[2].width for it in board_items[i::col_w]) * S for i in range(col_w)]
rows = [board_items[i:i + col_w] for i in range(0, len(board_items), col_w)]
row_h = [max(it[2].height for it in r) * S + 30 for r in rows]
board = Image.new('RGBA', (sum(cells_w) + pad * (col_w + 1), sum(row_h) + pad * (len(rows) + 1)), BG)
dr = ImageDraw.Draw(board)
dr.fontmode = '1'
y = pad
for r, rh in zip(rows, row_h):
    x = pad
    for i, (name, tones, im) in enumerate(r):
        sw = Image.new('RGBA', im.size, GROUND)
        sw.alpha_composite(im)
        board.paste(sw.resize((im.width * S, im.height * S), Image.NEAREST), (x, y))
        dr.text((x, y + im.height * S + 4), name, fill=rgb('fcfcfc'))
        dr.text((x, y + im.height * S + 16), tones, fill=rgb('9797aa'))
        x += cells_w[i] + pad
    y += rh + pad
board.save(os.path.join(HERE, 'wasteland_pieces.png'))

# every new piece on its own: no 16px cell over four colours (black counts; clear does not)
def cell_colours(im):
    worst = 0
    for cy in range(0, im.height, T):
        for cx in range(0, im.width, T):
            c = {px for px in im.crop((cx, cy, cx + T, cy + T)).get_flattened_data() if px[3]}
            worst = max(worst, len(c))
    return worst


causeway_alone = Image.new('RGBA', (W, H), (0, 0, 0, 0))
CHECK = {'volcano %d' % n: volcano(n) for n in range(4)}
CHECK.update({'rock small': rock(4, 3, 1), 'rock mid': rock(7, 5, 2), 'boulder': rock(11, 8, 3),
              'bone': bone(), 'fallen wall': stone_post_stub(2), 'lone gate': lone_gate(),
              'hut': hut_b, 'well': well, 'wall run': strip})
bad = 0
for name, im in CHECK.items():
    n = cell_colours(im)
    bad += n > 4
    print('%-12s %d colours a cell at most%s' % (name, n, '  OVER' if n > 4 else ''))
print('pieces over four colours a cell:', bad)
print('wrote', os.path.join(HERE, 'wasteland_target.png'), 'and the board')
