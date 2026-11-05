from pix import *
import math

LIT = '664b95'
DARK = '3b2a58'
BELLY = 'b69cee'
YEL = 'fae488'
YSH = 'f0bc3c'
MINT = 'a8f0bc'
CORAL = 'ec8476'
BLUE = '84a7e9'
K = (0, 0, 0)

# plate colours: (lit face, shaded face)
PY = (YEL, YSH)
PM = (MINT, BLUE)
PC = (CORAL, LIT)
PB = (BLUE, LIT)
PL = (BELLY, LIT)


def spline(pts, step=0.08):
    out = []
    p = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(p) - 2):
        a, b, c, d = p[i - 1], p[i], p[i + 1], p[i + 2]
        t = 0.0
        while t < 1.0:
            q = []
            for j in range(3):
                q.append(0.5 * (2 * b[j] + (c[j] - a[j]) * t
                                + (2 * a[j] - 5 * b[j] + 4 * c[j] - d[j]) * t * t
                                + (3 * b[j] - a[j] - 3 * c[j] + d[j]) * t * t * t))
            out.append(tuple(q))
            t += step
    out.append(pts[-1])
    return out


def disk(im, x, y, r, col):
    r = max(r, 0.5)
    x0, y0, x1, y1 = round(x - r), round(y - r), round(x + r), round(y + r)
    px = im.load()
    for yy in range(y0, y1 + 1):
        for xx in range(x0, x1 + 1):
            if (xx - x) ** 2 + (yy - y) ** 2 <= r * r + 0.3:
                px[xx, yy] = rgba(col)


def normal(path, i):
    a = path[max(i - 1, 0)]
    b = path[min(i + 1, len(path) - 1)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1
    return -dy / n, dx / n


def tube(im, path, keyline=True):
    """Dark hide with a lit upper-left stripe, and black bands across it."""
    if keyline:
        for x, y, r in path:
            disk(im, x, y, r + 1, K)
    for x, y, r in path:
        disk(im, x, y, r, DARK)
    for x, y, r in path:
        if r >= 2:
            disk(im, x - r * 0.3, y - r * 0.3, r * 0.62, LIT)


def bands(im, path, every, side=1, reach=1.0):
    """Short black ridges from one edge of the body in towards the middle."""
    dist = 0
    last = path[0]
    px = im.load()
    for i, (x, y, r) in enumerate(path):
        dist += math.hypot(x - last[0], y - last[1])
        last = (x, y, r)
        if dist >= every and r >= 3:
            dist = 0
            nx, ny = normal(path, i)
            for s in range(0, int(r * reach) + 1):
                px[round(x + side * nx * (r - s)), round(y + side * ny * (r - s))] = rgba(K)


def belly(im, path, side, every=4):
    """Pale belly plates down the side of the body that faces the player."""
    for i, (x, y, r) in enumerate(path):
        nx, ny = normal(path, i)
        disk(im, x + side * nx * r * 0.42, y + side * ny * r * 0.42, r * 0.52, BELLY)
    dist = 0
    last = path[0]
    px = im.load()
    for i, (x, y, r) in enumerate(path):
        dist += math.hypot(x - last[0], y - last[1])
        last = (x, y, r)
        if dist >= every:
            dist = 0
            nx, ny = normal(path, i)
            for s in range(0, int(r) + 1):
                px[round(x + side * nx * s), round(y + side * ny * s)] = rgba(K)


def plate(im, path, i, side, h, w, cols, lean=0.0):
    """One crystal on the body's edge: a sharp faceted shard with a black seam."""
    x, y, r = path[i]
    nx, ny = normal(path, i)
    nx, ny = nx * side, ny * side
    tx, ty = -ny, nx
    bx, by = x + nx * (r - 2), y + ny * (r - 2)
    a = (bx + tx * w / 2, by + ty * w / 2)
    b = (bx - tx * w / 2, by - ty * w / 2)
    tip = (bx + nx * h + tx * lean, by + ny * h + ty * lean)
    sa = (bx + tx * w * 0.55 + nx * h * 0.55, by + ty * w * 0.55 + ny * h * 0.55)
    sb = (bx - tx * w * 0.55 + nx * h * 0.55, by - ty * w * 0.55 + ny * h * 0.55)
    shape = [a, sa, tip, sb, b]
    layer = canvas(im.width, im.height)
    poly(layer, shape, cols[1])
    # the face nearer the light gets the lit tone
    near_a = (a[0] + a[1]) < (b[0] + b[1])
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    face = [a, sa, tip, mid] if near_a else [b, sb, tip, mid]
    poly(layer, face, cols[0])
    src = layer.load()
    dst = im.load()
    for yy in range(1, im.height - 1):
        for xx in range(1, im.width - 1):
            if src[xx, yy][3]:
                continue
            if dst[xx, yy][3] and any(src[xx + p, yy + q][3] for p, q in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                dst[xx, yy] = rgba(K)
    im.alpha_composite(layer)


im = canvas(90, 100)
OX, OY = 8, 8

back = spline([
    (62, 81, 0.6), (50, 83, 1.2), (36, 82, 2.2), (22, 77, 3.6), (12, 67, 5),
    (8, 54, 6), (11, 41, 6.5), (21, 32, 6.5), (34, 31, 6.5), (45, 37, 6.5),
    (51, 48, 6.5), (47, 60, 7),
])
front = spline([
    (47, 60, 7), (36, 65, 7), (27, 58, 7), (26, 46, 7), (33, 36, 6.5),
    (43, 27, 6), (48, 18, 5.5), (48, 12, 5),
])
back = [(x + OX, y + OY, r) for x, y, r in back]
front = [(x + OX, y + OY, r) for x, y, r in front]

# back of the body: tail, outer arc, over the top and down the far side
tube(im, back)
bands(im, back, 5, side=1, reach=0.7)
bands(im, back, 5, side=-1, reach=0.5)

# plates on the outer edge of the back run, tail end first
step = len(back) // 15
order = [PL, PY, PY, PM, PC, PY, PM, PB, PY, PC, PM, PY, PB]
idx = len(back) // 6
for n, cols in enumerate(order):
    i = idx + n * step
    if i >= len(back) - 4:
        break
    r = back[i][2]
    plate(im, back, i, 1, 5 + r * 0.55 + (n % 2), 6 + r * 0.45, cols, lean=(n % 3 - 1) * 1.5)

# front of the coil: passes over the back run and rises to the head
tube(im, front)
belly(im, front, -1)

step = len(front) // 7
for n, cols in enumerate([PM, PY, PC, PB]):
    i = len(front) // 2 + n * step
    if i >= len(front) - 2:
        break
    plate(im, front, i, 1, 8, 8, cols, lean=(n % 2) * 2 - 1)

# head, seen from the front
hx, hy = round(front[-1][0]), round(front[-1][1]) - 4


def head_pts(points):
    return [(hx + a, hy + b) for a, b in points]


# crystal crown behind the head
for pts, cols in [
    ([(-8, -3), (-11, -9), (-6, -7), (-3, -5)], PY),
    ([(8, -3), (11, -9), (6, -7), (3, -5)], PC),
    ([(-4, -5), (-2, -11), (0, -14), (2, -11), (4, -5)], PM),
]:
    poly(im, head_pts(pts), cols[1])
    lit = [p for p in pts if p[0] <= 0] + [(0, -5)] if pts[0][0] < 0 and pts[-1][0] > 0 else pts
    if cols is PM:
        poly(im, head_pts([(-4, -5), (-2, -11), (0, -14), (0, -5)]), cols[0])
    elif cols is PY:
        poly(im, head_pts([(-8, -3), (-11, -9), (-6, -7)]), cols[0])
    else:
        poly(im, head_pts([(6, -7), (11, -9), (8, -3)]), cols[0])

shape = [(-9, -3), (-6, -7), (6, -7), (9, -3), (8, 2), (4, 7), (-4, 7), (-8, 2)]
poly(im, head_pts([(a + (1 if a > 0 else -1), b + (1 if b > 0 else -1)) for a, b in shape]), K)
poly(im, head_pts(shape), DARK)
poly(im, head_pts([(-8, -3), (-5, -6), (4, -6), (5, -3), (3, 1), (-5, 2), (-7, 1)]), LIT)
rect(im, hx - 5, hy - 2, 3, 2, MINT)
rect(im, hx + 3, hy - 2, 3, 2, MINT)
rect(im, hx - 3, hy + 5, 7, 1, K)
dot(im, hx - 2, hy + 3, K)
dot(im, hx + 2, hy + 3, K)

im = outline(im)
save(im)
