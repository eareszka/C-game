from pix import *

D = '163623'   # coat shade
G = '2c6c44'   # moss coat
L = '4fa667'   # coat light / mint shade
M = 'a8f0bc'   # pale mint
E = 'f0e880'   # eye
C = '848694'   # claw
PAL = {'d': D, 'g': G, 'l': L, 'm': M, 'e': E, 'c': C}

W, H = 66, 74
CX = 24
im = canvas(W, H)


def put(part):
    """Lay a part on top, with a 1 px black line where it crosses what is below."""
    src, dst = part.load(), im.load()
    for y in range(H):
        for x in range(W):
            if src[x, y][3]:
                continue
            if not dst[x, y][3]:
                continue
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + a < W and 0 <= y + b < H and src[x + a, y + b][3]:
                    dst[x, y] = BLACK
                    break
    im.alpha_composite(part)


def edge_shade(part, base, light, dark, dark_w=2):
    """Light on the upper left edge, shade on the lower right, following the part."""
    src = part.copy().load()
    px = part.load()
    want = rgba(base)
    for y in range(H):
        for x in range(W):
            if src[x, y] != want:
                continue
            def empty(a, b):
                return not (0 <= x + a < W and 0 <= y + b < H) or not src[x + a, y + b][3]
            if any(empty(i, 0) for i in range(1, dark_w + 1)) or empty(0, 1):
                px[x, y] = rgba(dark)
            elif empty(-1, 0) or empty(0, -1):
                px[x, y] = rgba(light)


def brush(part, pts, w, colour):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n)
            y = round(y0 + (y1 - y0) * i / n)
            rect(part, x - w // 2, y - w // 2, w, w, colour)


def marks(part, rows, x, y):
    stamp(part, grid(rows, PAL), x, y)


# ---- tail: rises from behind the right hip and coils over the back
t = canvas(W, H)
brush(t, [(CX + 12, 42), (CX + 20, 41), (CX + 27, 36), (CX + 31, 28), (CX + 30, 19),
          (CX + 24, 13), (CX + 16, 13), (CX + 12, 19)], 6, G)
poly(t, [(CX + 32, 31), (CX + 36, 35), (CX + 30, 36)], G)
poly(t, [(CX + 22, 42), (CX + 26, 46), (CX + 19, 45)], G)
edge_shade(t, G, L, D)
put(t)
t = canvas(W, H)
brush(t, [(CX + 12, 19), (CX + 13, 26), (CX + 18, 30), (CX + 24, 27), (CX + 25, 21), (CX + 21, 19)], 5, G)
edge_shade(t, G, L, D)
put(t)
t = canvas(W, H)
rect(t, CX + 18, 19, 5, 4, M)
rect(t, CX + 22, 21, 2, 3, L)
rect(t, CX + 18, 22, 3, 2, M)
put(t)

# ---- hind legs, set back and showing outside the forelegs
for side in (-1, 1):
    h = canvas(W, H)
    s = side
    poly(h, [(CX + s * 11, 42), (CX + s * 17, 45), (CX + s * 18, 50), (CX + s * 16, 56), (CX + s * 12, 58), (CX + s * 11, 52)], G)
    edge_shade(h, G, L, D, 1)
    x = CX - 16 if s < 0 else CX + 12
    shank = canvas(W, H)
    rect(shank, x, 54, 4, 12, L)
    rect(shank, x - 1, 65, 6, 5, L)
    rect(shank, x + 3, 54, 1, 12, G)
    put(shank)
    put(h)
    for tx in (x, x + 2):
        rect(im, tx, 66, 1, 3, BLACK)
    for tx in (x - 1, x + 1, x + 3):
        dot(im, tx, 69, C)

# ---- forelegs: pale mint, coming out from under the coat
for side in (-1, 1):
    f = canvas(W, H)
    x = CX - 10 if side < 0 else CX + 5
    rect(f, x, 42, 6, 15, M)
    rect(f, x + 1 if side < 0 else x, 56, 5, 10, M)
    rect(f, x - 1, 65, 8, 5, M)
    dot(f, x - 1, 65, None)
    dot(f, x + 6, 65, None)
    # shade down the right of each leg, wider on the far side from the light
    w = 2 if side < 0 else 3
    rect(f, x + 6 - w, 42, w, 15, L)
    rect(f, x + 6 - w + (1 if side < 0 else 0), 57, w - (1 if side < 0 else 1) + (0 if side < 0 else 0), 8, L)
    rect(f, x + 5, 66, 2, 4, L)
    put(f)
    # wrist crease
    rect(im, x + 1, 56, 3, 1, BLACK)
    for tx in (x + 1, x + 3):
        rect(im, tx, 66, 1, 3, BLACK)
    for tx in (x, x + 2, x + 4):
        dot(im, tx, 69, C)

# ---- trunk and shoulders, tapering to the belly with a shaggy hem over the legs
b = canvas(W, H)
poly(b, [(CX - 12, 22), (CX + 12, 22), (CX + 16, 31), (CX + 15, 40),
         (CX + 12, 46), (CX - 12, 46), (CX - 15, 40), (CX - 16, 31)], G)
poly(b, [(CX - 15, 28), (CX - 19, 34), (CX - 14, 35)], G)
poly(b, [(CX + 15, 28), (CX + 19, 34), (CX + 14, 35)], G)
poly(b, [(CX - 15, 36), (CX - 18, 41), (CX - 13, 42)], G)
poly(b, [(CX + 15, 36), (CX + 18, 41), (CX + 13, 42)], G)
edge_shade(b, G, L, D)
# shaggy hem over the leg tops, kept in the moss tone so it doesn't read as claws
for x, drop, col in ((-10, 4, G), (-6, 5, L), (-2, 3, G), (2, 4, G), (6, 5, G), (10, 4, D)):
    poly(b, [(CX + x - 2, 45), (CX + x + 2, 45), (CX + x, 45 + drop)], col)
put(b)

# ---- shaggy pale chest: narrow at the throat, tiers of fur, jagged edge
c = canvas(W, H)
poly(c, [(CX - 7, 24), (CX + 7, 24), (CX + 9, 30), (CX + 9, 36), (CX + 6, 42),
         (CX + 4, 40), (CX + 2, 45), (CX, 42), (CX - 2, 47), (CX - 4, 41),
         (CX - 6, 43), (CX - 9, 36), (CX - 9, 30)], M)
poly(c, [(CX - 9, 29), (CX - 12, 34), (CX - 8, 35)], M)
poly(c, [(CX + 9, 29), (CX + 12, 34), (CX + 8, 35)], M)
poly(c, [(CX - 9, 35), (CX - 11, 40), (CX - 7, 40)], M)
poly(c, [(CX + 9, 35), (CX + 11, 40), (CX + 7, 40)], M)
# shade side, away from the light
poly(c, [(CX + 7, 26), (CX + 9, 30), (CX + 12, 34), (CX + 9, 35), (CX + 11, 40), (CX + 7, 40),
         (CX + 6, 42), (CX + 5, 36), (CX + 6, 31)], L)
put(c)
# fur tiers: chunky stepped lines across the chest
marks(im, ['ll..ll..ll', '..ll..ll..'], CX - 6, 30)
marks(im, ['ll..ll..l', '..ll..ll.'], CX - 5, 35)
marks(im, ['ll..l', '..ll.'], CX - 3, 40)

# ---- moss clumps in the coat
for x, y in ((CX - 15, 37), (CX - 15, 30), (CX + 12, 37), (CX + 13, 29)):
    marks(im, ['ddd', '.d.'], x, y)
for x, y in ((CX - 14, 34), (CX + 13, 34)):
    marks(im, ['ll', 'l.'], x, y)

# ---- head, with floppy ears and a long muzzle
HALF = [
    '..........llll',
    '.......lllllll',
    '....ggglllllll',
    '..gglllKllllgl',
    '.gllllgKlllggg',
    '.glllggKllgggg',
    'gllggdgKlggggg',
    'glgggdgKlKKKgg',
    'glgggdgKlgeegd',
    'glgggdgKglgggd',
    'glgdgdgKgglggd',
    'gggdgdgKggllgd',
    'dggdgddKdgllll',
    'dgddgddKdgllll',
    'dgdgdd.KdKglll',
    '.gdgd...Kgllll',
    '.ddgd...Kglddd',
    '.dd.d...Kglddd',
    '..d.....KgllKd',
    '........KgllgK',
    '........KgKKKK',
    '.........Kdddd',
    '..........dddd',
]
head = canvas(W, H)
stamp(head, grid(mirror(HALF), PAL), CX - 13, 2)
px = head.load()
for y in range(H):
    for x in range(CX + 1, W):
        if px[x, y] == rgba(L):
            px[x, y] = rgba(G)
put(head)

im = outline(im)
save(im)
