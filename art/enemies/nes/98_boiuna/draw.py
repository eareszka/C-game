from pix import *
import math

DK, MD, LT = '163623', '29633e', '4fa667'
TD, TM, TL = '785830', 'b2966a', 'cebe82'
YEL, FANG = 'f0bc3c', 'e8e0c0'
LIGHT = (-0.6, -0.8)
W, H = 224, 228

# One continuous spine, tail to head: x, y, half width.
COIL = [
    (3, 110, 0.6), (16, 113, 1.5), (30, 114, 3), (50, 117, 6), (76, 119, 9), (110, 120, 10),
    (150, 120, 10), (186, 119, 10), (197, 120, 10), (204, 124, 10), (206, 130, 10.5), (203, 136, 11),
    (194, 140, 11), (150, 142, 11.5), (90, 143, 12), (40, 143, 12), (24, 144, 12), (15, 148, 12),
    (12, 154, 12), (15, 161, 12.5), (25, 166, 13), (70, 168, 13), (130, 168, 13.5), (185, 168, 14),
    (198, 169, 14), (206, 174, 14), (209, 182, 14), (205, 190, 14), (194, 196, 14), (172, 200, 14),
    (152, 205, 14),
]
NECK = [
    (136, 209, 14.5), (124, 208, 15), (114, 202, 15), (108, 192, 15), (103, 170, 14.5), (97, 145, 14),
    (90, 118, 13.5), (83, 92, 13), (77, 68, 12.5), (73, 46, 12), (73, 32, 11.5), (78, 20, 11),
    (87, 12, 10.5), (99, 10, 10), (111, 13, 10), (121, 22, 9.5), (129, 34, 9), (136, 47, 8.5),
    (143, 60, 8),
]
SPINE = COIL + NECK

samples = []
for (x0, y0, h0), (x1, y1, h1) in zip(SPINE, SPINE[1:]):
    n = max(1, int(math.hypot(x1 - x0, y1 - y0) * 2))
    for i in range(n):
        f = i / n
        samples.append([x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, h0 + (h1 - h0) * f])
for i, sm in enumerate(samples):
    a, b = samples[max(0, i - 8)], samples[min(len(samples) - 1, i + 8)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1
    sm += [dx / d, dy / d]
S_NECK = sum(max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) * 2)) for a, b in zip(COIL, COIL[1:]))

# Which spine sample owns each pixel. Later body sits over earlier body.
owner = {}
for i, (sx, sy, hw, dx, dy) in enumerate(samples):
    r = int(hw) + 2
    for y in range(int(sy) - r, int(sy) + r + 1):
        for x in range(int(sx) - r, int(sx) + r + 1):
            d = math.hypot(x - sx, y - sy)
            if d > hw:
                continue
            old = owner.get((x, y))
            if old is None or i - old[0] > 60 or d <= old[1]:
                owner[(x, y)] = (i, d)


def cross(x, y):
    """t runs -1 to 1 across the body. Positive is the right of travel."""
    i = owner[(x, y)][0]
    sx, sy, hw, dx, dy = samples[i]
    return i, ((x - sx) * -dy + (y - sy) * dx) / hw, -dy, dx


def lum(t, nx, ny):
    t = max(-1, min(1, t))
    return t * (nx * LIGHT[0] + ny * LIGHT[1]) + 0.32 * math.sqrt(1 - t * t)


def stripe(i, t):
    if i < S_NECK + 6:
        return False
    # The stripe comes to a point where the neck leaves the coils.
    grow = min(1, (i - S_NECK - 6) / 70)
    mid, half = 0.43, 0.31 * grow
    return mid - half < t < mid + half


PERIOD = 18         # samples along the body per scale, 2 samples to the pixel
STRIPE_STEP = 15    # samples per belly plate


def rows_for(i):
    """Scale rows across the green hide: t start, t end, how many."""
    return (-1.0, 0.12, 2) if i >= S_NECK + 6 else (-1.0, 1.0, 4)


def scale_tone(i, t, hw, base):
    """Each scale is lit at its top and shaded along its lower edge."""
    if hw < 6:
        return base
    t0, t1, n = rows_for(i)
    if not t0 <= t <= t1:
        return base
    f = (t - t0) / (t1 - t0) * n
    r = min(n - 1, int(f))
    u = f - r
    v = ((i + r * PERIOD // 2) % PERIOD) / PERIOD
    cell = (t1 - t0) / n * hw
    if u * cell > cell - 1.6:
        return {LT: MD, MD: DK, DK: DK}[base]
    if base == MD and 0.2 < v < 0.65 and 1.0 < u * cell < 3.0:
        return LT
    return base


def belly_tone(i, t, l):
    """Each belly plate is pale at its start and shaded at its end."""
    v = ((i - S_NECK - 12) % STRIPE_STEP) / STRIPE_STEP
    if v > 0.72:
        return TD
    if v < 0.45 and t < 0.5:
        return TL
    return TM


px = {}
for (x, y) in owner:
    i, t, nx, ny = cross(x, y)
    l = lum(t, nx, ny)
    if stripe(i, t):
        px[(x, y)] = belly_tone(i, t, l)
    else:
        base = LT if l > 0.55 else MD if l > -0.1 else DK
        px[(x, y)] = scale_tone(i, t, samples[i][2], base)

black = set()


def line_px(x0, y0, x1, y1):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx, sy = (1 if x1 > x0 else -1), (1 if y1 > y0 else -1)
    err = dx - dy
    while True:
        yield x0, y0
        if (x0, y0) == (x1, y1):
            return
        e = 2 * err
        if e > -dy:
            err -= dy
            x0 += sx
        if e < dx:
            err += dx
            y0 += sy


def at(i, t):
    sx, sy, hw, dx, dy = samples[i]
    return round(sx - dy * t * hw), round(sy + dx * t * hw)


def mark(i, t0, t1, bend=0):
    """A short black line across the body, kept to the stretch of body it belongs to."""
    mid = i + bend
    a = at(max(0, min(len(samples) - 1, i)), t0)
    b = at(max(0, min(len(samples) - 1, mid)), t1)
    for p in line_px(a[0], a[1], b[0], b[1]):
        o = owner.get(p)
        if o and abs(o[0] - i) < 40:
            black.add(p)


# Scale plates: staggered rows of chevrons along the green hide.
for i in range(60, len(samples) - 12):
    if samples[i][2] < 6:
        continue
    t0, t1, n = rows_for(i)
    for r in range(n):
        if (i + r * PERIOD // 2) % PERIOD == 0:
            a = t0 + (t1 - t0) * r / n
            mark(i, a, a + (t1 - t0) / n, 3)

# Belly plates across the tan stripe.
for i in range(S_NECK + 12, len(samples) - 8, STRIPE_STEP):
    grow = min(1, (i - S_NECK - 6) / 70)
    mark(i, 0.43 - 0.31 * grow, 0.43 + 0.31 * grow)

# A black line each side of the stripe.
for (x, y), c in list(px.items()):
    i = owner[(x, y)][0]
    t = cross(x, y)[1]
    if stripe(i, t):
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + a, y + b)
            if q in owner and abs(owner[q][0] - i) < 40 and not stripe(owner[q][0], cross(*q)[1]):
                black.add(q)

# A black line wherever a later stretch of body lies over an earlier one.
for (x, y), o in owner.items():
    for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        q = owner.get((x + a, y + b))
        if q and q[0] - o[0] > 60:
            black.add((x, y))

# Dorsal ridge teeth, breaking up the outer edge of the neck and the top coil.
teeth = {}
for i in range(120, len(samples) - 20, 18):
    in_top = i < 520
    in_neck = i >= S_NECK + 40
    if not (in_top or in_neck):
        continue
    sx, sy, hw, dx, dy = samples[i]
    if hw < 6:
        continue
    for h in range(1, 4):
        wide = 3 - h
        for w in range(-wide, wide + 1):
            p = (round(sx + dy * (hw + h - 0.5) + dx * w), round(sy - dx * (hw + h - 0.5) + dy * w))
            if p not in owner:
                teeth[p] = LT if h == 3 else MD

im = canvas(W, H)
d = im.load()
for (x, y), c in teeth.items():
    if 0 <= x < W and 0 <= y < H:
        d[x, y] = rgba(c)
for (x, y), c in px.items():
    if 0 <= x < W and 0 <= y < H:
        d[x, y] = BLACK if (x, y) in black else rgba(c)

# The head, looking down at the player.
PAL = {'d': DK, 'm': MD, 'l': LT, 'y': YEL, 'w': FANG, 't': TM}
HEAD = mirror([
    '.........ddmmmmmmm',
    '.......ddmmmmmmlmm',
    '.....ddmmmKmmmlllm',
    '...ddmmmmKKmmmmllm',
    '..dmmllmmmmmmmKmmm',
    '.dmmmllllmmmmKKmmm',
    'dmmmmmllllllmKmmmm',
    'dmKKmmmmlllllmmmmm',
    '.dmKKKmmmmmmmmmmmm',
    '.ddmKKyyKmmmmmmmmm',
    '..dmmKKKKmmmmlllmm',
    '..ddmmmmmmmmmmlmmm',
    '...dmmmmmmmmmmmmmm',
    '...ddmmmmmmKmmmmmm',
    '....ddmmmmmKKmmmmm',
    '....ddddmmmmmmmmmm',
    '.....dKKKKKKKKKKKK',
    '.....dKwKddddddddd',
    '.....dKwwKddddKwKd',
    '.....ddKwwKdddKwKd',
    '......dKwwKdddKddd'[:18],
    '......ddKwKddddddd',
    '.......dKwKKKKKKKK',
    '.......ddKKddddddd',
    '.........dddddddd.',
])
stamp(im, grid(HEAD, PAL), 133, 56)

im = outline(im)
save(im)
