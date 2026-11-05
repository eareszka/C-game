from pix import *

FUR = 'f4ce80'
FUS = 'c18a39'
MAM = '94703d'
MAD = '633e1b'
RED = 'b6433d'
RMD = '792727'
RDK = '5d1e1f'
WHT = 'fcfcfc'
K = '000000'
PAL = {'l': FUR, 's': FUS, 'r': RMD, 'R': RED, 'w': WHT, 'd': MAD, 'm': MAM}

im = canvas(65, 59)


def stroke(x0, y0, x1, y1, lit=RED, dim=RMD):
    n = max(abs(x1 - x0), abs(y1 - y0))
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        y = round(y0 + (y1 - y0) * i / n)
        dot(im, x, y, lit)
        dot(im, x + 1, y, dim)


def line(x0, y0, x1, y1, c):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        dot(im, round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), c)


def leg(pts):
    for a, b in zip(pts, pts[1:]):
        stroke(a[0], a[1], b[0], b[1])
    for a, b in zip(pts, pts[1:]):
        stroke(63 - a[0], a[1], 63 - b[0], b[1])


# insect legs, behind everything
outer = [(16, 28), (7, 10), (1, 55)]
inner = [(14, 30), (8, 24), (5, 55)]
leg(outer)
leg(inner)
for x, y in ((7, 9), (56, 9), (8, 23), (55, 23)):
    rect(im, x, y, 2, 1, RED)
# foot claws and joint bands
for x, y in ((0, 56), (4, 56), (59, 56), (63, 56)):
    rect(im, x, y, 2, 1, RDK)
for x, y in ((3, 32), (6, 42), (58, 32), (55, 42)):
    rect(im, x, y, 2, 1, RDK)

# thorax peak
poly(im, [(32, 11), (38, 18), (26, 18)], MAM)
poly(im, [(32, 11), (28, 16), (26, 18), (31, 18)], FUS)

# belly and forelegs
rect(im, 25, 43, 15, 9, FUS)
rect(im, 25, 50, 15, 1, MAD)
rect(im, 25, 51, 15, 1, K)


def foreleg(flip):
    def X(x):
        return 64 - x if flip else x
    poly(im, [(X(18), 42), (X(30), 42), (X(27), 53), (X(15), 53)], FUR)
    if flip:
        poly(im, [(X(18), 42), (X(21), 42), (X(18), 53), (X(15), 53)], FUS)
    else:
        poly(im, [(27, 42), (30, 42), (27, 53), (24, 53)], FUS)
    lo = min(X(13), X(25))
    rect(im, lo, 54, 13, 4, FUR)
    rect(im, lo + 1, 53, 11, 1, FUR)
    rect(im, lo, 57, 13, 1, FUS)
    rect(im, lo + 12, 54, 1, 4, FUS)
    for t in (4, 8):
        rect(im, lo + t, 55, 1, 3, K)


foreleg(False)
foreleg(True)

# mane: shaggy tufts flowing out and down, shaded rim to the lower right
half = [(32, 15), (26, 15), (21, 16), (20, 20), (15, 20), (15, 25), (12, 27), (14, 31),
        (11, 34), (14, 37), (13, 41), (17, 40), (17, 44), (22, 42), (23, 46), (27, 44), (32, 47)]
shape = half + [(64 - x, y) for x, y in reversed(half[:-1])]
poly(im, [(x + 1, y + 1) for x, y in shape], MAD)
poly(im, shape, MAM)

# inner ruff, so the pale face stands off the mane
ruff = [(32, 19), (26, 19), (23, 22), (20, 25), (21, 30), (18, 33), (21, 37), (22, 41), (27, 41), (32, 43)]
poly(im, ruff + [(64 - x, y) for x, y in reversed(ruff[:-1])], MAD)

# black lines between tufts, running in from each notch
for a, b in (((20, 20), (22, 23)), ((15, 25), (19, 27)), ((14, 31), (18, 32)),
             ((14, 37), (18, 37)), ((17, 40), (20, 40)), ((22, 42), (24, 43)), ((27, 44), (28, 42))):
    line(a[0], a[1], b[0], b[1], K)
    line(64 - a[0], a[1], 64 - b[0], b[1], K)

# lit streaks on the upper left tufts, shade streaks on the lower right ones
for a, b in (((22, 17), (24, 18)), ((16, 21), (18, 23)), ((13, 27), (16, 28)),
             ((12, 34), (15, 34)), ((27, 16), (30, 16))):
    line(a[0], a[1], b[0], b[1], FUS)
for a, b in (((47, 21), (45, 23)), ((51, 27), (48, 28)), ((52, 34), (49, 34)),
             ((50, 40), (47, 38)), ((41, 44), (40, 42)), ((18, 42), (20, 41))):
    line(a[0], a[1], b[0], b[1], MAD)

# ears, set into the mane
ear = ['..KK..',
       '.KccK.',
       'KcddcK',
       'KcddcK',
       'KcddcK',
       '.KKKK.']
for x, c in ((21, FUS), (38, MAM)):
    stamp(im, grid(ear, {'c': c, 'd': MAD}), x, 17)

# face
face = [
    '....lllllllls....',
    '..lllllllllllss..',
    '.lllllllllllllss.',
    '.lKKlllllllllKKs.',
    '.lllKKlllllKKlss.',
    '.llllllllllllsss.',
    '.lllKKlllllKKlss.',
    '.llllllKKKllllls.',
    '.sllllllKlllllss.',
    '.slKKKKKKKKKKKss.',
    '.slKwwrwwwrwwKss.',
    '.ssKwrrrrrrrwKss.',
    '.ssKrrRRRRRrrKss.',
    '..ssKwRRRRRwKss..',
    '..ssKKwKwKwKKss..',
    '...ssKKKKKKKss...',
    '....sssssssss....',
]
stamp(im, outline(grid(face, PAL)), 23, 21)

# abdomen: a ball, banded across the lower half, sitting behind the body
ab = canvas(65, 21)
oval(ab, 21, 0, 23, 21, RDK)
oval(ab, 21, 0, 22, 20, RMD)
poly(ab, [(25, 3), (29, 1), (33, 1), (30, 3), (27, 5), (25, 7)], RED)
px = ab.load()
reds = ((0x79, 0x27, 0x27), (0xb6, 0x43, 0x3d), (0x5d, 0x1e, 0x1f))
for y0, c in ((6, K), (7, RED), (9, K), (10, RDK), (12, K), (13, RDK), (15, K)):
    for x in range(21, 44):
        y = y0 + round(3 * (1 - ((x - 32) / 11.5) ** 2))
        if 0 <= y < 21 and px[x, y][3] and px[x, y][:3] in reds:
            dot(ab, x, y, c)

whole = canvas(65, 62)
stamp(whole, ab, 0, 0)
stamp(whole, im, 0, 3)
im = whole

im = outline(im)
save(im)
