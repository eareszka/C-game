from pix import *
import math

S = 'f0b890'   # skin
P = 'ec8476'   # skin shade
R = 'b6433d'   # crease / tongue
D = '792727'   # mouth folds
E = '531b1c'   # mouth deep
T = 'e8e0c0'   # teeth
K = BLACK
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))

im = canvas(96, 96)


def band(a, b, wa, wb, col):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    n = math.hypot(dx, dy)
    nx, ny = -dy / n, dx / n
    poly(im, [(ax + nx * wa / 2, ay + ny * wa / 2), (bx + nx * wb / 2, by + ny * wb / 2),
              (bx - nx * wb / 2, by - ny * wb / 2), (ax - nx * wa / 2, ay - ny * wa / 2)], col)
    oval(im, bx - wb // 2, by - wb // 2, wb, wb, col)


def steps(x, y, w, h, ins, col, target=None):
    """Rounded box with hand-set corner steps: ins[i] is the inset on row i from top and bottom."""
    for i in range(h):
        k = min(i, h - 1 - i)
        c = ins[k] if k < len(ins) else 0
        rect(target or im, x + c, y + i, w - 2 * c, 1, col)


def edged(part):
    """Stamp a part, turning skin it touches into a 1 px black line, but never at the silhouette."""
    a, b = part.load(), im.load()
    w, h = im.size
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if a[x, y][3] or not b[x, y][3]:
                continue
            if not any(a[x + i, y + j][3] for i, j in N4):
                continue
            if all(b[x + i, y + j][3] or a[x + i, y + j][3] for i, j in N4):
                b[x, y] = K
    stamp(im, part, 0, 0)


# ---- silhouette, all in shade. Each finger is two joints with a knuckle bump ----
FINGERS = [((37, 42), (31, 25), (25, 11), 15, 13, 13),
           ((50, 38), (50, 21), (51, 8), 15, 13, 13),
           ((62, 40), (67, 29), (72, 19), 14, 12, 12),
           ((68, 52), (74, 42), (81, 33), 13, 11, 12)]
for a, j, b, wa, wj, wb in FINGERS:
    band(a, j, wa, wj, P)
    band(j, b, wj, wb - 1, P)
    oval(im, b[0] - wb // 2, b[1] - wb // 2, wb, wb, P)
# thumb: thick root, thin neck, ball tip
band((32, 62), (14, 57), 24, 14, P)
oval(im, 1, 47, 18, 18, P)
# palm, heels, wrist
poly(im, [(29, 36), (42, 32), (58, 32), (68, 38), (73, 47), (71, 58), (68, 68), (66, 76),
          (63, 80), (63, 90), (37, 90), (37, 84), (30, 78), (25, 70), (25, 52)], P)
oval(im, 25, 62, 16, 20, P)
oval(im, 54, 62, 15, 19, P)

# ---- light from the upper left: lit wherever body lies to the lower right ----
src = im.copy().load()
px = im.load()
for y in range(im.height):
    for x in range(im.width):
        if src[x, y][3] and x + 3 < im.width and y + 2 < im.height and src[x + 3, y + 2][3]:
            px[x, y] = rgba(S)


def crease(x, y, w, tilt=0):
    for i in range(w):
        yy = y + (i * tilt) // max(w - 1, 1)
        dot(im, x + i, yy, R)
        if 0 < i < w - 1:
            dot(im, x + i, yy + 1, P)


# ---- knuckle creases ----
crease(28, 24, 7, 1)
crease(30, 27, 6, 1)
crease(46, 20, 8)
crease(46, 23, 8)
crease(63, 28, 6, 1)
crease(62, 31, 7, 1)
crease(70, 41, 5, 1)
crease(69, 44, 5, 1)
crease(32, 36, 7, -1)
crease(46, 33, 7)
crease(60, 36, 6, 1)
# thumb: pad, joint lines, wrinkle
rect(im, 21, 51, 1, 6, R)
rect(im, 22, 52, 1, 4, P)
rect(im, 24, 53, 1, 10, R)
rect(im, 25, 54, 1, 8, P)
steps(11, 54, 7, 8, [2, 1], P)
steps(11, 54, 5, 6, [2, 1], S)
rect(im, 15, 60, 3, 1, R)
# finger root webs
rect(im, 43, 32, 1, 3, R)
rect(im, 57, 33, 1, 3, R)
rect(im, 67, 41, 1, 4, R)
# heels and wrist
rect(im, 26, 68, 3, 1, R)
rect(im, 28, 72, 4, 1, R)
rect(im, 31, 76, 3, 1, R)
rect(im, 65, 66, 2, 1, R)
rect(im, 62, 72, 3, 1, R)
rect(im, 40, 84, 7, 1, R)
rect(im, 54, 84, 7, 1, R)
rect(im, 39, 87, 6, 1, R)
rect(im, 47, 87, 8, 1, P)
rect(im, 57, 87, 4, 1, R)

# ---- palm mouth: stepped rings ----
steps(29, 37, 39, 45, [9, 6, 4, 3, 2, 1, 1], R)
steps(30, 38, 37, 43, [9, 6, 4, 3, 2, 1, 1], S)
# break the outer ring into wrinkle dashes
rect(im, 40, 37, 3, 1, S)
rect(im, 53, 37, 3, 1, S)
rect(im, 29, 50, 1, 4, S)
rect(im, 29, 63, 1, 4, S)
rect(im, 67, 48, 1, 4, S)
rect(im, 67, 62, 1, 4, S)
rect(im, 38, 81, 4, 1, S)
rect(im, 56, 81, 3, 1, S)
steps(32, 40, 33, 39, [8, 5, 3, 2, 1, 1], P)
steps(33, 41, 31, 37, [8, 5, 3, 2, 1, 1], R)
steps(34, 42, 29, 35, [7, 5, 3, 2, 1, 1], K)
steps(35, 43, 27, 33, [7, 5, 3, 2, 1, 1], E)

# ---- gullet folds, a broken spiral ----
steps(37, 50, 23, 25, [5, 3, 2, 1], D)
steps(39, 52, 19, 21, [4, 2, 1], E)
steps(41, 54, 15, 17, [3, 2, 1], D)
steps(43, 56, 11, 13, [3, 1], E)
steps(45, 57, 7, 8, [2, 1], D)
rect(im, 47, 59, 3, 3, E)
rect(im, 46, 56, 5, 1, K)
rect(im, 37, 58, 2, 1, K)
rect(im, 58, 54, 2, 1, K)
rect(im, 41, 60, 2, 1, K)
rect(im, 54, 62, 2, 1, K)
rect(im, 47, 50, 6, 1, K)
rect(im, 42, 53, 3, 1, R)
rect(im, 39, 56, 1, 3, R)

# ---- teeth, upper row ----
for x, y, w, h in [(37, 45, 3, 3), (41, 43, 4, 5), (46, 43, 4, 6), (51, 43, 4, 5), (56, 44, 3, 4)]:
    rect(im, x - 1, y, w + 2, h + 1, K)
    rect(im, x, y, w, h, T)
    dot(im, x + w - 1, y + h - 1, P)
# lower teeth
for x, y, w, h in [(38, 68, 3, 3), (39, 72, 3, 2), (54, 69, 3, 3), (53, 72, 3, 2)]:
    rect(im, x - 1, y - 1, w + 2, h + 1, K)
    rect(im, x, y, w, h, T)

# ---- tongue, stepped and curling out over the lower lip ----
TONGUE = [(46, 6), (46, 6), (46, 6), (45, 7), (45, 7), (45, 8), (44, 9), (44, 9), (44, 10),
          (43, 11), (43, 11), (43, 11), (43, 11), (43, 11), (43, 11), (43, 11), (44, 10), (44, 9),
          (45, 8), (46, 6)]
TY = 63
part = canvas(96, 96)
for i, (x, w) in enumerate(TONGUE):
    rect(part, x, TY + i, w, 1, P)
    rect(part, x + w - 3, TY + i, 3, 1, R)
edged(part)
for i in range(1, len(TONGUE) - 3):
    x, w = TONGUE[i]
    dot(im, x + w // 2 - 1, TY + i, D)
rect(im, 44, 72, 2, 2, S)
rect(im, 44, 77, 2, 2, S)
rect(im, 46, 66, 1, 2, S)


# ---- fingertip mouths with hanging tongues ----
def tip(cx, cy, tx, drop):
    part = canvas(96, 96)
    rect(part, cx - 4, cy - 3, 9, 7, E)
    rect(part, tx - 2, cy + 1, 5, drop, R)
    edged(part)
    rect(im, cx - 3, cy - 2, 7, 2, D)
    rect(im, cx - 3, cy - 3, 2, 2, T)
    rect(im, cx + 2, cy - 3, 2, 2, T)
    rect(im, tx - 2, cy, 5, 1, K)
    rect(im, tx - 2, cy + 1, 1, drop - 1, P)
    rect(im, tx + 2, cy + 1, 1, drop, D)
    rect(im, tx, cy + 2, 1, drop - 4, D)
    rect(im, tx - 2, cy + drop - 1, 3, 1, D)


tip(24, 11, 22, 11)
tip(51, 8, 51, 11)
tip(72, 19, 73, 11)
tip(81, 33, 83, 10)

im = outline(im)
save(im)
