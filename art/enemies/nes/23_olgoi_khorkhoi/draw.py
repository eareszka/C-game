from pix import *
from math import hypot, floor, atan2, pi

LIT, MID, DRK = 'ec8476', 'b6433d', '792727'
GUM = '531b1c'
BONE, BONE2 = 'e8e0c0', 'b29e5c'

W, H = 158, 80
im = canvas(W, H)
HX, HY = 44, 40


def put(c, x, y, col):
    if 0 <= x < W and 0 <= y < H:
        dot(c, x, y, col)


def seg(a, b):
    """Integer points from a to b."""
    (x0, y0), (x1, y1) = a, b
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    return [(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)) for i in range(n + 1)]


def path(pts):
    out = []
    for a, b in zip(pts, pts[1:]):
        for p in seg(a, b):
            if not out or out[-1] != p:
                out.append(p)
    return out


def edge(part):
    return outline(part).crop((1, 1, part.width + 1, part.height + 1))


# ---- feelers, behind everything: straight runs with drooping tips
FEELERS = [
    [(50, 14), (45, 6), (38, 1), (30, 0), (25, 3)],
    [(43, 22), (37, 11), (29, 5), (20, 4), (15, 8)],
    [(39, 26), (31, 17), (22, 12), (13, 13), (8, 18)],
    [(36, 31), (27, 25), (18, 21), (9, 23), (5, 28)],
]
for f in FEELERS:
    pts = path(f)
    for i, (x, y) in enumerate(pts):
        if i < len(pts) * 0.7:
            put(im, x, y, LIT)
            put(im, x + 1, y + 1, MID)
            put(im, x, y + 1, MID)
        else:
            put(im, x, y, MID)


# ---- body: rings laid along a spine
SPINE = [
    (HX, HY, 6), (46, 25, 6.5), (54, 13, 8), (70, 10, 9.5), (88, 17, 10.5), (98, 33, 11),
    (104, 50, 11.5), (116, 63, 11.5), (131, 67, 11), (147, 61, 10.5), (168, 52, 10),
]


def catmull(p0, p1, p2, p3, t):
    return tuple(
        0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (3 * b - a - 3 * c + d) * t ** 3)
        for a, b, c, d in zip(p0, p1, p2, p3)
    )


samples = []
ctrl = [SPINE[0]] + SPINE + [SPINE[-1]]
for i in range(len(ctrl) - 3):
    for k in range(60):
        samples.append(catmull(ctrl[i], ctrl[i + 1], ctrl[i + 2], ctrl[i + 3], k / 60))

q = 0.0
info = []
for i, (x, y, r) in enumerate(samples):
    if i:
        q += hypot(x - samples[i - 1][0], y - samples[i - 1][1]) / (0.5 * r + 0.9)
    a = samples[max(i - 2, 0)]
    b = samples[min(i + 2, len(samples) - 1)]
    tx, ty = b[0] - a[0], b[1] - a[1]
    m = hypot(tx, ty) or 1
    info.append((x, y, r, q, tx / m, ty / m))

best = {}
for smp in info:
    x, y, r = smp[:3]
    R = int(r) + 2
    for py in range(max(0, int(y) - R), min(H, int(y) + R + 1)):
        for px in range(max(0, int(x) - R), min(W, int(x) + R + 1)):
            d = hypot(px - x, py - y)
            if d <= r + 0.4 and ((px, py) not in best or d < best[(px, py)][0]):
                best[(px, py)] = (d, smp)

ring, tone = {}, {}
for (px, py), (d, (x, y, r, qq, tx, ty)) in best.items():
    nx, ny = -ty, tx
    s = (px - x) * nx + (py - y) * ny
    sn = max(-1, min(1, s / r))
    bow = 0.75 * sn * sn
    v = qq + bow
    idn = floor(v)
    u = v - idn
    rl = 0.5 * r + 0.9
    if min(u, 1 - u) * rl < 0.9 and d > r - 0.8:
        continue                                    # ring seam nips the silhouette
    ring[(px, py)] = idn
    light = (nx * sn + tx * (u - 0.5) * 0.9) * -0.707 + (ny * sn + ty * (u - 0.5) * 0.9) * -0.707
    tone[(px, py)] = LIT if light > 0.34 else DRK if light < -0.3 else MID

for (px, py), c in tone.items():
    dot(im, px, py, c)
for (px, py), idn in ring.items():
    for o in ((px + 1, py), (px, py + 1)):
        if o in ring and ring[o] != idn:
            dot(im, px, py, '000000')
            break


# ---- side blades: tapering bone with back-swept barbs
def blade(pts, barb_dir):
    part = canvas(W, H)
    line = path(pts)
    n = len(line)
    for i, (x, y) in enumerate(line):
        put(part, x, y, BONE)
        if i < n * 0.72:
            put(part, x, y + 1, BONE2)
        if i < n * 0.3:
            put(part, x, y - 1, BONE)
        if i % 7 == 5 and i < n - 2:
            for b in range(1, 4):
                put(part, x + barb_dir * b, y - b - (1 if i < n * 0.3 else 0), BONE)
                put(part, x + barb_dir * b, y + b + 1, BONE2)
    return part


stamp(im, edge(blade([(0, 33), (12, 37), (28, 40)], 1)), 0, 0)
stamp(im, edge(blade([(84, 29), (72, 35), (60, 40)], -1)), 0, 0)


# ---- the four lobes
def lobe(cx, cy, rx, ry):
    part = canvas(W, H)
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            dx, dy = (x - cx) / rx, (y - cy) / ry
            if abs(dx) + abs(dy) > 1.45:
                continue
            d = (dx + dy) * -0.707
            put(part, x, y, LIT if d > 0.32 else DRK if d < -0.36 else MID)
    return part


L = 11
LOBES = [(0, -L, 8, 7), (-L, 0, 7, 8), (L, 0, 7, 8), (0, L, 8, 7)]
for ox, oy, rx, ry in LOBES:
    cx, cy = HX + ox, HY + oy
    part = lobe(cx, cy, rx, ry)
    if ox == 0:                                     # two rows of teeth pointing at the mouth
        for tx in (-3, 3):
            for ty in (-4, -1, 2):
                t = ty if oy < 0 else -ty - 1
                dot(part, cx + tx, cy + t, BONE)
                dot(part, cx + tx, cy + t + 1, BONE2)
    else:
        for ty in (-3, 3):
            for tx in (-4, -1, 2):
                t = tx if ox < 0 else -tx - 1
                dot(part, cx + t, cy + ty, BONE)
                dot(part, cx + t + 1, cy + ty, BONE2)
    stamp(im, edge(part), 0, 0)


# ---- the mouth
mouth = canvas(W, H)
for y in range(HY - 10, HY + 11):
    for x in range(HX - 10, HX + 11):
        dx, dy = x - HX, y - HY
        d = hypot(dx, dy)
        if d > 9.4:
            continue
        lit = (dx + dy) * -0.707 / 9
        if d > 6.4:
            put(mouth, x, y, LIT if lit > 0.45 else DRK if lit < -0.25 else MID)
        elif d > 2.4:
            put(mouth, x, y, GUM)
        else:
            put(mouth, x, y, '000000')
for y in range(HY - 8, HY + 9):                     # a ring of 12 teeth, wide at the lip, pointing in
    for x in range(HX - 8, HX + 9):
        dx, dy = x - HX, y - HY
        d = hypot(dx, dy)
        if not 3.4 < d < 7.0:
            continue
        f = (atan2(dy, dx) * 6 / pi) % 1
        if abs(f - 0.5) * 2 < (d - 2.9) / 3.6:
            put(mouth, x, y, BONE2 if dx + dy > 3 else BONE)
stamp(im, edge(mouth), 0, 0)

im = strip_outline(im)
im = outline(im)
save(im)
