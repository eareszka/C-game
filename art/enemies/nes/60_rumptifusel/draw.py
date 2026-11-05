from pix import *

L = 'b2966a'   # pelt light
M = '815423'   # pelt mid
D = '583518'   # pelt shade
P = '664b95'   # underside
Q = 'b69cee'   # underside pattern
R = '301b5a'   # underside shade
KK = (0, 0, 0)

W, H = 40, 26
im = canvas(W, H)
px = im.load()

# Pelt silhouette, row by row: (first x, last x)
PELT = [
    (25, 31), (23, 33), (22, 35), (21, 36), (20, 37), (19, 38), (18, 38), (17, 39),
    (16, 39), (15, 39), (15, 39), (8, 38), (6, 38), (4, 37), (2, 36), (1, 36),
    (0, 35), (0, 34), (0, 33), (0, 32), (0, 31), (0, 31), (0, 30), (1, 30),
    (2, 29), (5, 12),
]
inside = set()
for y, (a, b) in enumerate(PELT):
    for x in range(a, b + 1):
        inside.add((x, y))
inside |= {(x, 25) for x in range(26, 29)}
inside -= {(12, 11), (13, 11)}   # the neck sags behind the head

for x, y in inside:
    px[x, y] = rgba(M)

# Shade follows the body: lower right edges fall dark, upper left edges catch light.
for x, y in inside:
    if (x + 1, y + 1) not in inside or (x + 2, y + 2) not in inside:
        px[x, y] = rgba(D)
for x, y in inside:
    if (x - 1, y - 1) not in inside and (x, y - 1) not in inside:
        px[x, y] = rgba(L)


def put(points, colour, dx=0, dy=0):
    """Stepped line through the points, kept inside the pelt."""
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        steps = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(steps + 1):
            x = round(x0 + (x1 - x0) * i / steps) + dx
            y = round(y0 + (y1 - y0) * i / steps) + dy
            if (x, y) in inside:
                px[x, y] = rgba(colour)


# Transverse pelt stripes, each one a light band, a black crease, a dark band.
STRIPES = [
    [(31, 0), (35, 3), (38, 7), (39, 11)],
    [(25, 0), (30, 3), (33, 7), (35, 12), (35, 16)],
    [(20, 4), (25, 7), (28, 11), (30, 16), (30, 22)],
    [(15, 9), (20, 12), (23, 15)],
]
for s in STRIPES:
    put(s, L, dx=-1)
    put(s, L, dx=-2)
    put(s, D, dx=1)
    put(s, KK)

# Short stripe behind the head, and a fold on the neck.
s = [(10, 11), (12, 14), (13, 16)]
put(s, L, dx=-1)
put(s, D, dx=1)
put(s, KK)
put([(2, 16), (5, 14)], L)
put([(3, 17), (5, 16)], D)
put([(6, 15), (8, 14)], D)

# Purple underside tucked under the arch.
ARCH = [
    (20, 23), (18, 25), (16, 26), (15, 27), (15, 27), (14, 28), (14, 28), (14, 28),
]
for i, (a, b) in enumerate(ARCH):
    y = 17 + i
    for x in range(a - 1, b + 2):
        px[x, y] = rgba(KK)
    if i == 0:
        for x in range(a - 1, b + 2):
            px[x, y - 1] = rgba(KK)
for i, (a, b) in enumerate(ARCH):
    y = 17 + i
    for x in range(a, b + 1):
        px[x, y] = rgba(R if i < 2 and (i == 0 or a + 1 < x < b - 1) else P)
cross = grid(['.q.', 'qqq', '.q.'], {'q': Q})
for x, y in [(17, 19), (22, 19), (14, 22), (19, 22), (25, 22)]:
    tile(im, cross, x, y, 3, 3, within=P)

# Head: black crease behind the jaw, two solid eyes.
put([(13, 19), (13, 25)], KK)
put([(2, 14), (8, 11)], L)
for x, y in [(4, 21), (4, 22), (8, 20), (8, 21)]:
    px[x, y] = rgba(KK)
put([(3, 24), (10, 24)], D)
put([(12, 21), (11, 24)], D)

im = outline(im)
save(im)
