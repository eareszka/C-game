from pix import *

L = 'a8f0bc'
M = '4fa667'
D = '2c6c44'
Y = 'f4ce80'
B = 'b29e5c'
P = 'ec8476'
R = 'b6433d'
T = 'fae488'
K = '000000'

PAL = {'l': L, 'm': M, 'd': D, 'y': Y, 'b': B, 'p': P, 'r': R, 't': T}

im = canvas(44, 49)


def px(x, y, c):
    if 0 <= x < im.width and 0 <= y < im.height:
        dot(im, x, y, c)


def ring(cx, top, w, rows, last=False):
    """One flat coil with rounded ends: green back, yellow belly, shadow, black line."""
    x0 = cx - w // 2
    insets = {5: [2, 1, 0, 0, 1], 6: [2, 1, 0, 0, 0, 1]}[rows]
    for i, ins in enumerate(insets):
        y = top + i
        for x in range(x0 + ins, x0 + w - ins):
            t = (x - x0) / (w - 1)
            below = rows - 1 - i
            if i == 0:
                c = L if t < 0.45 else (M if t < 0.85 else D)
            elif i == 1:
                c = L if x - x0 - ins < 1 else (M if t < 0.88 else D)
            elif below == 0:
                c = D if last else K
            elif below == 1:
                c = D
            elif below == 2:
                c = Y if t < 0.72 else B
                if (x - x0) % 8 == 5:
                    c = B if t < 0.72 else D
            else:
                c = B if t < 0.72 else D
            # the belly wraps out of sight at each end, so the ends are green
            if 2 <= i and below >= 1:
                if x - x0 < 2:
                    c = M
                elif x0 + w - 1 - x < 2:
                    c = D
            px(x, y, c)


def wrap(x, top):
    """A short black step where one turn of the coil laps over the next."""
    for dx, dy in ((0, 1), (1, 2), (1, 3), (2, 4)):
        px(x + dx, top + dy, K)


CX = 20
ring(CX, 25, 21, 5)
ring(CX, 30, 27, 5)
ring(CX, 35, 33, 6)
wrap(29, 35)
ring(CX, 41, 40, 6, last=True)
wrap(7, 41)

# Tail: rises off the base ring on the right.
for y in range(4, 46):
    if y >= 41:
        x = 39
    elif y >= 36:
        x = 38
    elif y >= 30:
        x = 37
    elif y >= 23:
        x = 36
    elif y >= 15:
        x = 35
    else:
        x = 34
    px(x - 1, y, D if y % 8 == 0 else L)
    px(x, y, M)
    if y >= 15:
        px(x + 1, y, D)
for x in range(32, 36):
    px(x, 3, L)

# Neck: green sides, yellow belly with black plates, in a small S.
off = {16: 0, 17: 0, 18: 1, 19: 1, 20: 1, 21: 1, 22: 0, 23: 0, 24: -1, 25: -1, 26: -1, 27: -1, 28: 0, 29: 0, 30: 0, 31: 0, 32: 0}
for y in range(16, 33):
    o = off[y]
    half = 3 if y < 20 else 4
    c = CX + o
    if y >= 25:
        px(c - half - 1, y, K)
        px(c + half + 1, y, K)
    for x in range(c - half, c + half + 1):
        e = x - (c - half)
        r = (c + half) - x
        if e == 0:
            col = L
        elif e == 1:
            col = M
        elif r == 0:
            col = D
        elif r == 1:
            col = M
        else:
            col = Y if x <= c else B
            if y % 3 == 0:
                col = K
        px(x, y, col)
# The neck tucks under into the coil.
for x in range(CX - 3, CX + 4):
    px(x, 33, D)
for x in range(CX - 2, CX + 3):
    px(x, 34, K)
px(CX - 4, 33, K)
px(CX + 4, 33, K)

# Head, hand placed. Ear tips are the top rows.
head = [
    'p.....................r',
    'pp...................pr',
    'ppr.................prr',
    '.pr.lllllllmmmmmmmm.rr.',
    '.prlllmmmmmmmmmmmmmdrr.',
    '..lllmmmmmmmmmmmmmmmdd.',
    '..lmKKmmmmmmmmmmmKKmdd.',
    '..lmmmKKmmmmmmmKKmmmdd.',
    '..lmmmmmKKmmmKKmmmmmdd.',
    '...lmKKmmmmmmmmmKKmdd..',
    '...lmmmmmddmddmmmmmdd..',
    '....lmmmmmmmmmmmmmdd...',
    '....dKKKKKKKKKKKKKd....',
    '.....tKtKKKKKKKtKt.....',
    '.....yyyyyyyyyyyyy.....',
    '......byyyyyyyyyb......',
]
stamp(im, grid(head, PAL), CX - 11, 0)

# Tail tip: hooks in over the right ear and stops it, with the ear tip above.
for x in range(29, 35):
    px(x, 2, L if x > 30 else M)
    px(x, 3, M if x > 30 else D)
px(28, 3, M)
for x in (27, 28, 29, 30):
    px(x, 4, K)
px(27, 3, K)

im = outline(im)
save(im)
