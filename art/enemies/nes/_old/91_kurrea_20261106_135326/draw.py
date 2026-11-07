from pix import *
import math

DARK = '3b2a58'
MAIN = '664b95'
BELLY = 'b69cee'
YEL = 'fae488'
MINT = 'a8f0bc'
SALM = 'ec8476'
BLUE = '84a7e9'
HI = 'dcf0ff'

SHADE = {YEL: SALM, MINT: BLUE, SALM: MAIN, BLUE: MAIN, BELLY: MAIN}


def path(pts, step=0.25):
    """straight runs between the points: an angular crystal body, not a smooth curve"""
    res, s = [], 0.0
    pts = [(p[0] + OX, p[1], p[2]) for p in pts]
    for a, b in zip(pts, pts[1:]):
        ln = math.dist(a[:2], b[:2])
        n = max(2, int(ln / step))
        tx, ty = (b[0] - a[0]) / ln, (b[1] - a[1]) / ln
        for k in range(n):
            f = k / n
            res.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f,
                        -ty, tx, tx, ty, s + ln * f))
        s += ln
    return res


def draw_band(S, belly, W, H, scute=4):
    lay = canvas(W, H)
    px = lay.load()
    for y in range(H):
        for x in range(W):
            best, bv = None, 9e9
            for q in S:
                d = math.hypot(x - q[0], y - q[1]) / max(q[2], 0.6)
                if d < bv:
                    bv, best = d, q
            if bv > 1:
                continue
            cx, cy, r, nx, ny, tx, ty, s = best
            ox, oy = x - cx, y - cy
            t = (ox * nx + oy * ny) / r
            lit = (-ox - oy) / (r * 1.41)
            saw = ((s + 2 * t) % 7) / 7
            if belly and belly[0] <= t <= belly[1] and r > 2.5:
                c = MAIN if lit < -0.45 else BELLY
                px[x, y] = BLACK if ((s + 2) % scute) < 1.0 else rgba(c)
            else:
                px[x, y] = rgba(DARK if lit + 0.6 * saw < 0.15 else MAIN)
    return lay


def ring(under, mask_img):
    W, H = under.size
    a = mask_img.load()
    u = under.load()
    for y in range(H):
        for x in range(W):
            if a[x, y][3] or not u[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H and a[xx, yy][3]:
                    u[x, y] = BLACK
                    break


def shard(lay, b, n, t, L, w, col):
    bx, by = b
    side = 1 if (-t[0] - t[1]) > 0 else -1
    lx, ly = t[0] * side, t[1] * side
    tip = (bx + n[0] * L, by + n[1] * L)
    p = canvas(*lay.size)
    sh = 0.5 * L
    a = (bx + lx * w, by + ly * w)
    c = (bx - lx * w, by - ly * w)
    a2 = (a[0] + n[0] * sh, a[1] + n[1] * sh)
    c2 = (c[0] + n[0] * sh, c[1] + n[1] * sh)
    poly(p, [a, a2, tip, c2, c], col)
    poly(p, [(bx - lx, by - ly), tip, c2, c], SHADE[col])
    rect(p, round(a2[0] - n[0] - lx), round(a2[1] - n[1] - ly), 1, 1, HI)
    ring(lay, p)
    lay.alpha_composite(p)


def at(S, f):
    return S[int(f * (len(S) - 1))]


def plates(S, side, specs, W, H):
    lay = canvas(W, H)
    for f, L, w, col in specs:
        cx, cy, r, nx, ny, tx, ty, s = at(S, f)
        n = (nx * side, ny * side)
        b = (cx + n[0] * (r - 1.5), cy + n[1] * (r - 1.5))
        shard(lay, b, n, (tx, ty), L + 1.5, w, col)
    return lay


def chip(im, S, f, off, col):
    """a small crystal set into the hide, with a black line round it"""
    cx, cy, r, nx, ny, *_ = at(S, f)
    x, y = round(cx + nx * off * r), round(cy + ny * off * r)
    p = canvas(*im.size)
    poly(p, [(x, y - 2), (x + 2, y), (x, y + 2), (x - 2, y)], col)
    poly(p, [(x, y), (x + 2, y), (x, y + 2)], SHADE[col])
    ring(im, p)
    im.alpha_composite(p)


def add(im, plate_lay, body_lay):
    both = canvas(*im.size)
    both.alpha_composite(plate_lay)
    both.alpha_composite(body_lay)
    ring(im, both)
    im.alpha_composite(both)


OX = 7  # room on the left so the plates aren't clipped
W, H = 82, 82
im = canvas(W, H)

# back coil: tail tip lower right, under the body, up the left, over the hump
A = path([(58, 71, 1), (50, 74, 2), (40, 74, 3), (29, 73, 5), (18, 69, 6), (10, 59, 6),
          (8, 45, 6), (11, 33, 6), (20, 25, 6), (30, 25, 6.5), (35, 29, 7)])
Ap = plates(A, -1, [
    (0.25, 4, 3, BELLY), (0.34, 6, 3, BELLY), (0.42, 6, 3, YEL), (0.50, 7, 3, MINT), (0.58, 7, 3, YEL),
    (0.66, 7, 3, BLUE), (0.74, 8, 3, SALM), (0.82, 8, 3, MINT), (0.90, 7, 3, YEL),
], W, H)
add(im, Ap, draw_band(A, (0.25, 1.01), W, H))
chip(im, A, 0.46, -0.45, SALM)
chip(im, A, 0.62, -0.45, MINT)
chip(im, A, 0.78, -0.45, YEL)

# front coil: down the middle, round the bottom, up the right to the neck
B = path([(35, 29, 7), (30, 40, 6), (30, 52, 6.5), (37, 62, 7), (48, 60, 6.5), (55, 47, 5.5),
          (55, 35, 5), (51, 27, 4), (46, 22, 3.5)])
Bp = plates(B, 1, [
    (0.08, 4, 3, YEL), (0.18, 5, 3, BLUE), (0.28, 5, 3, MINT),
    (0.58, 5, 3, SALM), (0.66, 6, 3, YEL), (0.74, 6, 3, MINT), (0.82, 6, 3, BLUE), (0.90, 5, 3, YEL),
], W, H)
# blue and yellow crystals standing into the hole of the coil
Bp.alpha_composite(plates(B, -1, [(0.02, 5, 4, BLUE), (0.11, 6, 3, YEL)], W, H))
add(im, Bp, draw_band(B, (-1.01, -0.15), W, H))
chip(im, B, 0.45, 0.5, YEL)
chip(im, B, 0.62, 0.45, MINT)
chip(im, B, 0.78, 0.4, SALM)

HEAD = [
    '.....mmmmmmm.....',
    '...mmmbbmmmmmss..',
    '..mmbbmmmmmmmsss.',
    '.mmbmmmmmmmmmmsss',
    'mmmmmmmmmmmmmmsss',
    'mmmyymmmmmmyysssd',
    'mmmmyymmmyymmssdd',
    '.mmmmmmmmmmmsssd.',
    '..mmbbbbbbbbbsd..',
    '...bbKbbbbKbbm...',
    '...KKKKKKKKKKK...',
    '....bKbbbbbKm....',
    '.....mbbbbbm.....',
]
PAL = {'m': MAIN, 'b': BELLY, 's': DARK, 'd': DARK, 'y': YEL}
head = grid(HEAD, PAL)
hx, hy = 37 + OX, 12

cr = canvas(W, H)
shard(cr, (hx + 3, hy + 3), (-0.6, -0.8), (0.8, -0.6), 7, 2, YEL)
shard(cr, (hx + 14, hy + 3), (0.6, -0.8), (0.8, 0.6), 7, 2, SALM)
shard(cr, (hx + 8, hy + 2), (0, -1), (1, 0), 9, 3, MINT)
head_l = canvas(W, H)
stamp(head_l, head, hx, hy)
add(im, cr, head_l)

im = outline(im)
save(im)
