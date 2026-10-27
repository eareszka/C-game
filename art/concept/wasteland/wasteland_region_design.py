"""A large stretch of the restyled wasteland: the target's pieces laid across a real
world's mountains, to see the biome at the scale it is walked.

    python art/concept/wasteland/wasteland_region_design.py

Reads tmp/waste_region_1x.png -- a `SHOT_KIND=waste shot.exe 387 ... -1 -1 150 96`
render, halved -- and keeps only its island mountains (the cliffs are unchanged
by the overhaul). The lava, the dead trees and the old ground are dropped, and the
rest is laid fresh from wasteland_target_design.py's pieces and rules: the void in
pools shaped as the game shapes water, red stands, the barracks compounds, the
ruin mazes, the lone gate, trails routed round the rock and over pools on
causeways. Writes wasteland_region.png beside this file.
"""
import heapq, os, random, sys
from collections import deque
from math import hypot
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
_argv = sys.argv
sys.argv = [_argv[0], os.path.join(ROOT, 'tmp', 'waste_mountain.png')]   # the target rebuilds as it was
import wasteland_target_design as D
sys.argv = _argv

T = D.T
R = random.Random(387)

# ---------------------------------------------------------------- the mountains, from the game
src = Image.open(os.path.join(ROOT, 'tmp', 'waste_region_1x.png')).convert('RGB')
X0 = 150                                                       # the left edge is another biome
TW, TH = (src.width - X0) // T, src.height // T
W, H = TW * T, TH * T
S = src.crop((X0, 0, X0 + W, H)).load()
ROCK_TONES = {(0x88, 0x70, 0x00), (0x49, 0x37, 0x12), (0x81, 0x54, 0x23), (0xb2, 0x9e, 0x5c)}
DROP = {(0x34, 0x1e, 0x10), (0x11, 0x00, 0x00), (0x58, 0x35, 0x18),      # ground
        (0x7c, 0x0a, 0x1b), (0xb7, 0x00, 0x00)}                          # lava
seen = [[False] * W for _ in range(H)]
cliff = Image.new('RGBA', (W, H), (0, 0, 0, 0))
CL = cliff.load()
ROCKMASK = [[False] * W for _ in range(H)]
for y in range(H):
    for x in range(W):
        if seen[y][x] or S[x, y] in DROP:
            continue
        comp, rock, q = [], 0, deque([(x, y)])
        seen[y][x] = True
        while q:
            cx, cy = q.popleft()
            comp.append((cx, cy))
            rock += S[cx, cy] == (0x88, 0x70, 0x00)              # the cliffs' own rock; wood shares the dark
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < W and 0 <= ny < H and not seen[ny][nx] and S[nx, ny] not in DROP:
                        seen[ny][nx] = True
                        q.append((nx, ny))
        if rock >= 20:                            # a mountain; a dead tree or a mark is not
            for cx, cy in comp:
                CL[cx, cy] = S[cx, cy] + (255,)
                ROCKMASK[cy][cx] = True

# tiles the rock stands on or beside: nothing is laid there
ROCKT = [[False] * TW for _ in range(TH)]
for y in range(H):
    for x in range(W):
        if ROCKMASK[y][x]:
            ROCKT[y // T][x // T] = True
BLOCK = [[False] * TW for _ in range(TH)]
for ty in range(TH):
    for tx in range(TW):
        if ROCKT[ty][tx]:
            for dy in (-1, 0, 1, 2):
                for dx in (-1, 0, 1):
                    if 0 <= ty + dy < TH and 0 <= tx + dx < TW:
                        BLOCK[ty + dy][tx + dx] = True
NEARROCK = [row[:] for row in BLOCK]                          # rock and a tile round it, plateau tops open
# plateau tops walled round by their faces cannot be walked to: keep to the largest open country
comp_id = [[-1] * TW for _ in range(TH)]
sizes = []
for sy in range(TH):
    for sx in range(TW):
        if BLOCK[sy][sx] or comp_id[sy][sx] >= 0:
            continue
        q, n = deque([(sx, sy)]), 0
        comp_id[sy][sx] = len(sizes)
        while q:
            x, y = q.popleft()
            n += 1
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < TW and 0 <= ny < TH and not BLOCK[ny][nx] and comp_id[ny][nx] < 0:
                    comp_id[ny][nx] = len(sizes)
                    q.append((nx, ny))
        sizes.append(n)
MAIN = sizes.index(max(sizes))
for y in range(TH):
    for x in range(TW):
        if comp_id[y][x] != MAIN:
            BLOCK[y][x] = True
TAKEN = [[False] * TW for _ in range(TH)]


def free(x0, y0, w, h, pad=1):
    if x0 - pad < 0 or y0 - pad < 0 or x0 + w + pad > TW or y0 + h + pad > TH:
        return False
    return not any(BLOCK[y][x] or TAKEN[y][x] for y in range(y0 - pad, y0 + h + pad) for x in range(x0 - pad, x0 + w + pad))


def take(x0, y0, w, h):
    for y in range(max(0, y0), min(TH, y0 + h)):
        for x in range(max(0, x0), min(TW, x0 + w)):
            TAKEN[y][x] = True


def place(w, h, near, pad=1, reach=200):
    """The free spot of w x h tiles nearest `near`."""
    best = None
    for y0 in range(max(1, near[1] - reach), min(TH - h - 1, near[1] + reach)):
        for x0 in range(max(1, near[0] - reach), min(TW - w - 1, near[0] + reach)):
            d = hypot(x0 + w / 2 - near[0], y0 + h / 2 - near[1])
            if (best is None or d < best[0]) and free(x0, y0, w, h, pad):
                best = (d, x0, y0)
    if best is None:
        raise SystemExit('no room for a %dx%d near %s' % (w, h, near))
    return best[1], best[2]


# ---------------------------------------------------------------- the settlements and places
stand = []          # (ground line, x, image)
WALL, SLABS = {}, set()


def put(im, x, yg):
    stand.append((yg, x, im))


def run(x0, x1, y, slab=()):
    for x in range(x0, x1 + 1):
        WALL[(x, y)] = True
        if x in slab:
            SLABS.add((x, y))


def back(x, y, n, slab=()):
    for i in range(n + 1):
        WALL[(x + i, y - i)] = True
        if i in slab:
            SLABS.add((x + i, y - i))


def hamlet(ox, oy):
    """The barracks compound of the target, its top left at (ox, oy); returns its gate and its way out."""
    o = lambda x, y: (x - 1 + ox, y - 8 + oy)
    run(*o(1, 17)[:1], o(6, 17)[0], o(1, 17)[1]); run(o(9, 17)[0], o(15, 17)[0], o(9, 17)[1])
    run(o(8, 10)[0], o(15, 10)[0], o(8, 10)[1])
    run(o(18, 10)[0], o(22, 10)[0], o(18, 10)[1])
    back(*o(1, 17), 7); back(*o(15, 17), 1); back(*o(19, 13), 3)
    hx, hy = o(8, 14)
    put(D.hut_a, hx * T, hy * T - 2)
    put(D.hut_b, hx * T + 55, hy * T - 2)
    wx, wy = o(18, 13)
    put(D.well, wx * T, wy * T)
    take(ox, oy, 22, 10)
    return o(7.5, 18.8), o(19.5, 14.6), [o(7.6, 16.4), o(8.5, 15.2), o(16, 15.0), o(18.6, 14.6)]


def maze(ox, oy):
    """The ruin maze round the ruins' mouth, its top left at (ox, oy); returns the mouth's doorstep."""
    o = lambda x, y: (x - 22 + ox, y - 5 + oy)
    run(o(22, 0)[0], o(26, 0)[0], o(0, 18)[1]); run(o(29, 0)[0], o(30, 0)[0], o(0, 18)[1])
    back(*o(26, 18), 2); back(*o(31, 18), 3)
    run(o(23, 0)[0], o(26, 0)[0], o(0, 12)[1]); back(*o(23, 12), 3)
    run(o(33, 0)[0], o(34, 0)[0], o(0, 13)[1])
    run(o(26, 0)[0], o(30, 0)[0], o(0, 7)[1]); back(*o(26, 7), 0)
    rx, ry = o(24, 17)
    put(D.ruins, rx * T, ry * T)
    take(ox, oy, 14, 15)
    return o(28.0, 19.4)


def lone_gate(ox, oy):
    put(D.lone_gate(), ox * T, (oy + 3) * T)
    put(D.chest, ox * T + 20, (oy + 4) * T + 4)
    take(ox, oy, 4, 5)
    return (ox + 1.7, oy + 5.6)


M = (TW // 2, TH // 2)
ha = hamlet(*place(22, 10, (M[0] - 40, M[1] - 2)))
ma = maze(*place(14, 15, (M[0] - 8, M[1] + 2)))
hb = hamlet(*place(22, 10, (M[0] + 30, M[1] + 30)))
mb = maze(*place(14, 15, (M[0] + 40, M[1] - 22)))
gate = lone_gate(*place(4, 5, (M[0] - 30, M[1] + 32)))

# ---------------------------------------------------------------- trails: shortest ways round the rock
def snap(p):
    """The nearest open tile to p: an end in the rock or at the map's edge comes out to the country."""
    p = (min(TW - 1, max(0, int(p[0]))), min(TH - 1, max(0, int(p[1]))))
    q, seen_ = deque([p]), {p}
    while q:
        c = q.popleft()
        if not BLOCK[c[1]][c[0]]:
            return c
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c[0] + dx, c[1] + dy)
            if 0 <= n[0] < TW and 0 <= n[1] < TH and n not in seen_:
                seen_.add(n)
                q.append(n)
    return p


def route(a, b):
    a, b = snap(a), snap(b)
    dist, prev, q = {a: 0}, {}, [(0, a)]
    while q:
        d, c = heapq.heappop(q)
        if c == b:
            break
        if d > dist[c]:
            continue
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (c[0] + dx, c[1] + dy)
                if not (0 <= n[0] < TW and 0 <= n[1] < TH) or (dx == dy == 0):
                    continue
                if BLOCK[n[1]][n[0]] and n != b:
                    continue
                nd = d + (1.41 if dx and dy else 1.0) + (6 if TAKEN[n[1]][n[0]] else 0) + (0.6 if any(
                    0 <= n[1] + j < TH and 0 <= n[0] + i < TW and BLOCK[n[1] + j][n[0] + i]
                    for i in (-2, 2) for j in (-2, 2)) else 0)
                if nd < dist.get(n, 1e9):
                    dist[n], prev[n] = nd, c
                    heapq.heappush(q, (nd, n))
    path, c = [b], b
    while c != a:
        c = prev[c]
        path.append(c)
    path.reverse()
    pts = [(x + .5, y + .5) for x, y in path]
    for _ in range(3):                                         # worn smooth, not stepped
        pts = [pts[0]] + [((pts[i - 1][0] + pts[i][0] + pts[i + 1][0]) / 3,
                           (pts[i - 1][1] + pts[i][1] + pts[i + 1][1]) / 3) for i in range(1, len(pts) - 1)] + [pts[-1]]
    return pts


def unblock(p):
    x, y = int(p[0]), int(p[1])
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if 0 <= y + dy < TH and 0 <= x + dx < TW:
                TAKEN[y + dy][x + dx] = False


for p in (ha[0], ha[1], hb[0], hb[1], ma, mb, gate):
    unblock(p)
ROUTES = [route((0, ha[0][1]), ha[0]), ha[2], route(ha[1], ma), route(ma, mb), route(ma, hb[0]), hb[2],
          route(hb[1], (TW - 1, hb[1][1] - 6)), route(ha[0], gate)]

# ---------------------------------------------------------------- pools
LIQ_T = [[0] * TW for _ in range(TH)]


def brush(cx, cy, kind, r=2):
    for by in range(-r, r + 1):
        for bx in range(-r, r + 1):
            x, y = cx + bx, cy + by
            if bx * bx + by * by <= r * r and 0 <= x < TW and 0 <= y < TH:
                LIQ_T[y][x] = kind


def trail_tiles(margin):
    out = set()
    for r in ROUTES:
        for x, y in r:
            for dy in range(-margin, margin + 1):
                for dx in range(-margin, margin + 1):
                    out.add((int(x) + dx, int(y) + dy))
    return out


NEAR_TRAIL = trail_tiles(2)


def pool_fits(cx, cy, r=2, pad=2):
    for y in range(cy - r - pad, cy + r + pad + 1):
        for x in range(cx - r - pad, cx + r + pad + 1):
            if not (0 <= x < TW and 0 <= y < TH) or NEARROCK[y][x] or TAKEN[y][x] or (x, y) in NEAR_TRAIL:
                return False
    return True


# causeways: a pool laid across the trail where it runs level, the deck over it along the trail
BRIDGES = []
for r in (ROUTES[3], ROUTES[6]):
    best = None
    for i in range(6, len(r) - 6):
        seg = r[i - 6:i + 7]
        flat = max(p[1] for p in seg) - min(p[1] for p in seg)
        if flat < .6 and all(not BLOCK[int(y) + j][int(x)] for x, y in seg for j in (-3, 3) if 0 <= int(y) + j < TH):
            if best is None or abs(i - len(r) / 2) < abs(best - len(r) / 2):
                best = i
    if best is not None:
        cx, cy = r[best]
        for k in (-2, 0, 2):
            brush(int(cx) + k, int(cy) - 1 + (k == 0), 1)
        BRIDGES.append((r[best - 6], r[best + 6]))

kinds = [1] * 24 + [2, 2, 2]
R.shuffle(kinds)
placed = 0
for _ in range(20000):
    if placed >= len(kinds):
        break
    cx, cy = R.randrange(4, TW - 4), R.randrange(4, TH - 4)
    if not pool_fits(cx, cy):
        continue
    kind = kinds[placed]
    n = 1 if kind == 2 else R.choice((1, 2, 2, 3, 4))
    ang = R.random() * 6.28
    x, y = cx, cy
    for k in range(n):
        if pool_fits(int(x), int(y), pad=1):
            brush(int(x), int(y), kind)
        x += 2.2 * __import__('math').cos(ang)
        y += 2.2 * __import__('math').sin(ang)
        ang += R.uniform(-.7, .7)
    for yy in range(cy - 6, cy + 7):
        for xx in range(cx - 6, cx + 7):
            if 0 <= yy < TH and 0 <= xx < TW and LIQ_T[yy][xx]:
                TAKEN[yy][xx] = True
    placed += 1

# the edge field, as the game draws water (see wasteland_target_design.py)
LIQ = [[0] * W for _ in range(H)]
RIM = set()
for ty in range(TH):
    for tx in range(TW):
        if not any(0 <= ty + j < TH and 0 <= tx + i < TW and LIQ_T[ty + j][tx + i] for i in (-1, 0, 1) for j in (-1, 0, 1)):
            continue
        variant = D.cover_hash(tx, ty, 0xF7149E00) % 2
        for py in range(T):
            for px in range(T):
                ws = D.WEIGHTS[py * T + px]
                den = sum(w for _, _, w in ws)
                cov = {1: 0.0, 2: 0.0}
                for dx, dy, w in ws:
                    x, y = tx + dx, ty + dy
                    k = LIQ_T[y][x] if 0 <= x < TW and 0 <= y < TH else 0
                    if k:
                        cov[k] += w
                th = .5 + D.SHORE_JITTER * ((D.cover_hash(px, py, 0x54093E00 + variant) % 2001) / 1000 - 1)
                X, Y = tx * T + px, ty * T + py
                for k in (1, 2):
                    f = cov[k] / den
                    if f >= th:
                        LIQ[Y][X] = k
                    elif f >= th - D.SHORE_BAND and not LIQ[Y][X]:
                        RIM.add((X, Y))


def is_void(x, y):
    return 0 <= x < W and 0 <= y < H and LIQ[y][x] == 1


def wet(x, y):
    return 0 <= x < W and 0 <= y < H and LIQ[y][x] != 0


# ---------------------------------------------------------------- painting
img = Image.new('RGBA', (W, H), D.GROUND)
P = img.load()
# the floor: rough round the rock, the pools and the walls, plain in the open
NEAR = [(x, y) for y in range(TH) for x in range(TW) if ROCKT[y][x] or LIQ_T[y][x]] + list(WALL)
ROUGH = D.rough_mask(TW, TH, NEAR, seed=387)


def rough(px, py):
    return ROUGH[py // T][px // T]


D.paint_floor(img, rough)

# worn bands: stripe fields in the open, a court of them round each maze
FIELDS = []
for mx, my in (ma, mb):
    FIELDS.append((int(mx) - 9, int(my) - 1, [0, 3, 13, 16], 9))
for _ in range(60):
    if len(FIELDS) >= 7:
        break
    x0, y0 = R.randrange(4, TW - 16), R.randrange(4, TH - 16)
    if free(x0, y0, 10, 12, 0):
        FIELDS.append((x0, y0, [0, 3, 5, 9], 12))
for x0, y0, cols, length in FIELDS:
    for c in cols:
        bw = 2 if c % 3 == 0 else 1
        for py in range(y0 * T, (y0 + length) * T):
            for px in range((x0 + c) * T, (x0 + c + bw) * T):
                if not (0 <= px < W and 0 <= py < H):
                    continue
                e = min(px - (x0 + c) * T, (x0 + c + bw) * T - 1 - px, py - y0 * T, (y0 + length) * T - 1 - py)
                if e < 3 and (px + py) % (2 + e) != 0:
                    continue
                if P[px, py] == D.GROUND and not rough(px, py):
                    P[px, py] = D.BAND


def stamp_trail(pts):
    dense = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        n = max(1, int(hypot(bx - ax, by - ay) * 16))
        dense += [((ax + (bx - ax) * i / n) * T, (ay + (by - ay) * i / n) * T) for i in range(n + 1)]
    pave = set()
    for x, y in dense:
        for dy in range(-10, 11):
            for dx in range(-11, 12):
                if dx * dx + dy * dy <= 112:
                    pave.add((int(x + dx), int(y + dy)))
    return pave


pave = set()
for r in ROUTES:
    pave |= stamp_trail(r)
edge = set()
for x, y in pave:
    for k in (1, 2, 3):
        if (x, y - k) not in pave:
            edge.add((x, y - k))
    if (x, y + 1) not in pave:
        edge.add((x, y + 1))
    for dx in (-1, 1):
        if (x + dx, y) not in pave:
            edge.add((x + dx, y))
for x, y in edge - pave:
    if 0 <= x < W and 0 <= y < H:
        P[x, y] = D.TRAIL_EDGE
for x, y in pave:
    if 0 <= x < W and 0 <= y < H:
        P[x, y] = D.TRAIL

for y in range(H):
    for x in range(W):
        if LIQ[y][x] == 1:
            P[x, y] = D.VOID
        elif LIQ[y][x] == 2:
            P[x, y] = D.POOL
for x, y in RIM:
    if not LIQ[y][x]:
        P[x, y] = D.CRACK
for _ in range(9000):
    px, py = R.randrange(3, W - 8), R.randrange(4, H - 4)
    n = R.choice((3, 4, 5))
    k = LIQ[py][px]
    if k and all(LIQ[py + j][px + i] == k for i in range(-2, n + 2) for j in (-3, -2, -1, 0, 1, 2)):
        tone = (D.VOID_A if R.random() < .7 else D.VOID_B) if k == 1 else D.POOL_A
        for i in range(n):
            P[px + i, py] = tone
        if k == 1 and n >= 4 and R.random() < .5:
            P[px + 1, py - 1] = tone
            P[px + n - 2, py - 1] = tone


def causeway(deck, face_h=8):
    bottom = max(y for _, y in deck)
    out = {}
    for x, y in deck:
        out[(x, y)] = D.STONE[0] if y % 8 else D.STONE[1]
    cols = {}
    for x, y in deck:
        if (x, y + 1) not in deck:
            cols.setdefault(x, []).append(y)
    for x, ys in cols.items():
        for yb in ys:
            for k in range(1, face_h + 1):
                y = yb + k
                row, off = (k - 1) % 4, 3 if ((k - 1) // 4) % 2 else 0
                c = D.STONE[0] if row == 0 else D.STONE[2] if (x + off) % 6 == 5 or row == 3 else D.STONE[1]
                out.setdefault((x, y), c if yb == bottom else D.STONE[2])
    xs = sorted(cols)
    for x in xs:
        if (x - xs[0]) % 32 in range(10, 16):
            for k in range(face_h + 1, face_h + 7):
                if is_void(x, bottom + k):
                    out.setdefault((x, bottom + k), D.STONE[2])
    ink = set(out)
    for x, y in list(ink):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in ink:
                out[(x + dx, y + dy)] = D.K
    for (x, y), c in out.items():
        if 0 <= x < W and 0 <= y < H:
            P[x, y] = c


for (ax, ay), (bx, by) in BRIDGES:
    yc = int((ay + by) / 2 * T)
    causeway({(x, y) for x in range(int(min(ax, bx) * T), int(max(ax, bx) * T)) for y in range(yc - 12, yc + 12)})

img.alpha_composite(cliff)                                     # the island mountains, as the game draws them

# ---------------------------------------------------------------- what stands
for (x, y) in WALL:
    n = (1 if (x - 1, y) in WALL else 0) | (2 if (x + 1, y) in WALL else 0) \
        | (4 if (x - 1, y + 1) in WALL else 0) | (8 if (x + 1, y - 1) in WALL else 0)
    im = D.yard.crop(((16 + n) * T, 0, (17 + n) * T, 2 * T))
    put(im, x * T, y * T + 12)

FIG = [D.volcano(n) for n in range(4)]


def open_px(px, py, r=6):
    tx, ty = int(px // T), int(py // T)
    return (0 <= tx < TW and 0 <= ty < TH and not NEARROCK[ty][tx] and not TAKEN[ty][tx]
            and not any(wet(px + i, py + j) or (px + i, py + j) in pave or (0 <= px + i < W and 0 <= py + j < H and ROCKMASK[py + j][px + i])
                        for i in (-r, 0, r) for j in (-r, 0, 2)))


# red stands, arranged as the references arrange things (a ring of pyramids round a centre): a
# ring of volcanoes round each red pool, and in the open a ring round nothing, or a row
from math import cos, sin, pi
reds = [(x, y) for y in range(TH) for x in range(TW) if LIQ_T[y][x] == 2]
pools2, left = [], set(reds)
while left:                                                    # each red pool and its middle
    q, blob = deque([left.pop()]), []
    while q:
        c = q.popleft()
        blob.append(c)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c[0] + dx, c[1] + dy)
            if n in left:
                left.discard(n)
                q.append(n)
    pools2.append((sum(x for x, _ in blob) / len(blob) * T + 8, sum(y for _, y in blob) / len(blob) * T + 8))
STANDS = [('ring', cx, cy) for cx, cy in pools2]          # a double ring round each red pool
for _ in range(600):                                           # and dense groves in the open
    if len(STANDS) >= 10:
        break
    c = (R.randrange(80, W - 80), R.randrange(60, H - 60))
    if open_px(*c, 40) and all(hypot(c[0] - s_[1], c[1] - s_[2]) > 320 for s_ in STANDS):
        STANDS.append(('grove', c[0], c[1]))
GROVES = [(sx, sy, 62, 42) for kind, sx, sy in STANDS if kind == 'grove']
used = []
for kind, sx, sy in STANDS:
    for px, py, size in D.stand_pts(kind, sx, sy, R):
        px, py = int(px), int(py)
        if open_px(px, py, 4) and all(abs(px - u) > 9 or abs(py - v) > 5 for u, v in used):
            f = FIG[size]
            put(f, px - f.width // 2, py)
            used.append((px, py))
seeds = STANDS
# lone figures where the dead trees stood, one in six of them
for _ in range(3000):
    px, py = R.randrange(10, W - 10), R.randrange(24, H - 4)
    if R.random() < .025 and open_px(px, py) and all(hypot(px - u, py - v) > 90 for u, v in used):
        f = FIG[R.choice((2, 3))]
        put(f, px - f.width // 2, py)
        used.append((px, py))


def near_void(px, py, r):
    return any(wet(px + dx, py + dy) for dx in (-r, 0, r) for dy in (-r, 0, r))


occupied = []
for _ in range(60000):
    px, py = R.randrange(8, W - 8), R.randrange(8, H - 4)
    if wet(px, py) or (px, py) in pave or not (near_void(px, py, 22) or rough(px, py)) or near_void(px, py, 5):
        continue
    if not open_px(px, py, 3) or any(abs(px - ox) < 10 and abs(py - oy) < 8 for ox, oy in occupied):
        continue
    if R.random() > ((.09 if (px // 96 + py // 96) % 3 else .015) if near_void(px, py, 22) else .02):
        continue
    if any(((px - gx) / grx) ** 2 + ((py - gy) / gry) ** 2 < 1 for gx, gy, grx, gry in GROVES):
        continue
    occupied.append((px, py))
    D.grit_under(P, W, H, px, py, R)
    s = R.random()
    im = D.rock(4, 3, px) if s < .55 else D.rock(7, 5, px) if s < .88 else D.rock(11, 8, px)
    put(im, px - im.width // 2, py)
strays = 0
for _ in range(4000):
    px, py = R.randrange(20, W - 40), R.randrange(30, H - 10)
    if strays < 14 and R.random() < .02 and open_px(px, py, 14):
        if R.random() < .5:
            put(D.stone_post_stub(R.choice((1, 2))), px, py)
        else:
            img.alpha_composite(D.bone(), (px, py - 7))
        strays += 1

pl = ROUTES[2][len(ROUTES[2]) // 2]
put(D.player, int(pl[0] * T) - 7, int(pl[1] * T) + 4)

for yg, x, im in sorted(stand, key=lambda s: (s[0], s[1])):
    img.alpha_composite(im, (int(x), int(yg - im.height)))

out = os.path.join(HERE, 'wasteland_region.png')
img.save(out)
print('wrote', out, img.size, '-', len(BRIDGES), 'causeways,', placed, 'pools,', len(seeds), 'red stands')
