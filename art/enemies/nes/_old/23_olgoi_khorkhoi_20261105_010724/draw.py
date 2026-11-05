from pix import *
import math

W, H = 88, 50
LIGHT, MID, SHADE = 'ec8476', 'b6433d', '792727'
THROAT = '531b1c'
BONE, BONE_D = 'e8e0c0', 'cebe82'
LX, LY = -0.6, -0.8

im = canvas(W, H)
px = im.load()
BK = rgba('000000')


def set_part(part, sep=True):
    """Paint a dict of pixels; where it meets something already drawn, a black line separates them."""
    if sep:
        for (x, y) in part:
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + a, y + b)
                if n not in part and 0 <= n[0] < W and 0 <= n[1] < H and px[n][3]:
                    px[n] = BK
    for (x, y), c in part.items():
        if 0 <= x < W and 0 <= y < H:
            px[x, y] = rgba(c)


# ---- body: rings walked along a spine ----
KNOTS = [(28, 30), (29, 24), (31, 14), (39, 7), (49, 8), (56, 15), (58, 25), (62, 33),
         (69, 37), (77, 35), (84, 31), (92, 28), (100, 26)]


def catmull(p0, p1, p2, p3, t):
    return tuple(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (3 * b - a - 3 * c + d) * t ** 3)
                 for a, b, c, d in zip(p0, p1, p2, p3))


spine = []
pts = [KNOTS[0]] + KNOTS + [KNOTS[-1]]
for i in range(1, len(pts) - 2):
    for k in range(40):
        spine.append(catmull(pts[i - 1], pts[i], pts[i + 1], pts[i + 2], k / 40))
samples = []
s = 0.0
for i, p in enumerate(spine):
    if i:
        s += math.dist(p, spine[i - 1])
    q = spine[min(i + 1, len(spine) - 1)]
    r = spine[max(i - 1, 0)]
    dx, dy = q[0] - r[0], q[1] - r[1]
    n = math.hypot(dx, dy) or 1
    samples.append((p[0], p[1], s, dx / n, dy / n))

PERIOD = 5.0
BOW = 1.6


def halfwidth(s, ring_u):
    base = 5.4 + 1.4 * min(1.0, s / 40)
    return base + (0.55 if 0.2 < ring_u < 0.8 else 0.0)


def axis_at(s):
    best = min(samples, key=lambda q: abs(q[2] - s))
    return best[3], best[4]


info = {}
for y in range(H):
    for x in range(W):
        best, bd = None, 1e9
        for q in samples:
            d = (x - q[0]) ** 2 + (y - q[1]) ** 2
            if d < bd:
                best, bd = q, d
        qx, qy, qs, tx, ty = best
        side = (x - qx) * -ty + (y - qy) * tx
        dist = math.sqrt(bd)
        if dist > 8.6:
            continue
        adj = qs + BOW * (min(1.0, dist / 6.5) ** 2)
        u = (adj / PERIOD) % 1.0
        if dist <= halfwidth(qs, u):
            info[x, y] = (adj, side, qs)

ringline = set()
for (x, y), (adj, _, _) in info.items():
    for n in ((x + 1, y), (x, y + 1)):
        if n in info and int(info[n][0] // PERIOD) != int(adj // PERIOD):
            ringline.add((x, y))
            break

body = {}
for (x, y), (adj, side, qs) in info.items():
    ring = int(adj // PERIOD)
    tx, ty = axis_at((ring + 0.5) * PERIOD)
    nx, ny = -ty, tx
    w = 6.2
    val = side * (nx * LX + ny * LY) / w
    val += (tx * LX + ty * LY) * ((adj / PERIOD) % 1.0 - 0.5) * 0.9
    tone = LIGHT if val > 0.28 else SHADE if val < -0.32 else MID
    # a darker saddle of rings in the low bend
    if 14 <= ring <= 17:
        tone = MID if tone == LIGHT else SHADE
    body[x, y] = 'K' if (x, y) in ringline else tone
for p, c in body.items():
    px[p] = BK if c == 'K' else rgba(c)

# ---- bristles: thin feelers fanning up-left from the neck ----


def line(a, b):
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    e = dx + dy
    out = []
    while True:
        out.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return out
        e2 = 2 * e
        if e2 >= dy:
            e += dy
            x0 += sx
        if e2 <= dx:
            e += dx
            y0 += sy


BRISTLES = [
    [(22, 15), (16, 13), (10, 13), (4, 16)],
    [(24, 13), (18, 9), (11, 8), (6, 10)],
    [(26, 11), (22, 5), (15, 3), (10, 5)],
    [(28, 9), (25, 3), (20, 1), (16, 2)],
    [(30, 7), (29, 2), (26, 0), (23, 0)],
]
for path in BRISTLES:
    pixels = []
    for a, b in zip(path, path[1:]):
        pixels += line(a, b)
    for i, (x, y) in enumerate(pixels):
        if 0 <= x < W and 0 <= y < H and not px[x, y][3]:
            px[x, y] = rgba(LIGHT if i > len(pixels) * 0.6 else MID)

# ---- barbed side blades ----
CX, CY = 27, 26
blade = {}
# left blade: base at the left lobe, rising outward in clean steps
for x0, x1, y, thick in ((9, 14, 26, 2), (5, 8, 25, 1), (2, 4, 24, 1), (0, 1, 23, 1)):
    for x in range(x0, x1 + 1):
        blade[x, y] = BONE
        if thick == 2:
            blade[x, y + 1] = BONE_D
# barbs hook back toward the head, above and below the blade
for x, y in ((7, 26), (8, 27), (7, 24), (8, 23),
             (3, 25), (4, 26), (3, 23), (4, 22),
             (10, 28), (11, 29), (10, 25), (11, 24)):
    blade[x, y] = BONE
# right blade mirrors the left
for (x, y), c in list(blade.items()):
    blade[2 * CX - x, y] = c
for (x, y), c in blade.items():
    if 0 <= x < W and 0 <= y < H and not px[x, y][3]:
        px[x, y] = rgba(c)

# ---- four lobes in a pinwheel ----


def lobe(cx, cy, rw, rh):
    part = {}
    for y in range(int(cy - rh - 1), int(cy + rh + 2)):
        for x in range(int(cx - rw - 1), int(cx + rw + 2)):
            a, b = (x - cx) / rw, (y - cy) / rh
            if a * a + b * b <= 1.0:
                v = a * LX + b * LY
                part[x, y] = LIGHT if v > 0.25 else SHADE if v < -0.42 else MID
    return part


LOBES = [
    (lobe(CX - 1, CY - 9.5, 6.0, 4.6), [(CX - 4, CY - 10), (CX - 1, CY - 11), (CX + 2, CY - 10)]),
    (lobe(CX + 9.5, CY - 1, 4.6, 6.0), [(CX + 10, CY - 4), (CX + 11, CY - 1), (CX + 10, CY + 2)]),
    (lobe(CX + 1, CY + 9.5, 6.0, 4.6), [(CX - 2, CY + 10), (CX + 1, CY + 11), (CX + 4, CY + 10)]),
    (lobe(CX - 9.5, CY + 1, 4.6, 6.0), [(CX - 10, CY - 2), (CX - 11, CY + 1), (CX - 10, CY + 4)]),
]
for part, pits in LOBES:
    set_part(part)
    for p in pits:
        px[p] = rgba(BONE)

# ---- the maw ----
MAW = [
    '....lllll....',
    '..llrrrrrmm..',
    '.lrrarararrm.',
    '.lrdddddddrs.',
    'lradddKdddars',
    'lrdddKKKdddrs',
    'laddKKKKKddas',
    'lrdddKKKdddrs',
    'lradddKdddars',
    '.mrdddddddrs.',
    '.mrrarararrs.',
    '..ssrrrrrss..',
    '....sssss....',
]
PAL = {'l': LIGHT, 'm': MID, 's': SHADE, 'r': SHADE, 'a': BONE, 'd': THROAT}
maw = grid(MAW, PAL)
mp = maw.load()
part = {}
for y in range(maw.height):
    for x in range(maw.width):
        if mp[x, y][3]:
            part[CX - 6 + x, CY - 6 + y] = mp[x, y]
for p in part:
    for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = (p[0] + a, p[1] + b)
        if n not in part and px[n][3]:
            px[n] = BK
for p, c in part.items():
    px[p] = c

# ---- no black may sit on the silhouette, or the outline doubles ----
for _ in range(2):
    snap = im.copy().load()
    for y in range(H):
        for x in range(W):
            if snap[x, y][:3] != (0, 0, 0) or not snap[x, y][3]:
                continue
            around = [(x + a, y + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if any(not (0 <= q[0] < W and 0 <= q[1] < H) or not snap[q][3] for q in around):
                near = [snap[q] for q in around if 0 <= q[0] < W and 0 <= q[1] < H and snap[q][3] and snap[q][:3] != (0, 0, 0)]
                px[x, y] = near[0] if near else CLEAR

im = outline(im)
save(im)
