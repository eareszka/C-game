from pix import *

A, B, C = 'c18a39', '876a1f', '5c4616'      # hide: light, mid, dark
D, E = 'cebe82', 'b29e5c'                   # belly: light, shade
F, G, H = 'a8f0bc', '4edc4a', '058f3a'      # skull green, also the eyes
K = '000000'
PAL = {'a': A, 'b': B, 'c': C, 'd': D, 'e': E, 'f': F, 'g': G, 'h': H}

im = canvas(90, 72)
px = im.load()


def col(p):
    return px[p[0], p[1]]


def setp(p, c):
    if 0 <= p[0] < im.width and 0 <= p[1] < im.height:
        px[p[0], p[1]] = rgba(c)


def filled(p):
    return 0 <= p[0] < im.width and 0 <= p[1] < im.height and col(p)[3] > 0


def oval_set(x, y, w, h):
    t = canvas(im.width, im.height)
    oval(t, x, y, w, h, A)
    d = t.load()
    return {(i, j) for j in range(t.height) for i in range(t.width) if d[i, j][3]}


def poly_set(pts):
    t = canvas(im.width, im.height)
    poly(t, pts, A)
    d = t.load()
    return {(i, j) for j in range(t.height) for i in range(t.width) if d[i, j][3]}


def shift(s, a, b):
    return {(x + a, y + b) for x, y in s}


def hide(s, lx=3, ly=2, sx=4, sy=3):
    """Flat hide with a light rim to the upper left and a dark rim to the lower right."""
    for x, y in s:
        if (x + sx, y + sy) not in s:
            setp((x, y), C)
        elif (x - lx, y - ly) not in s:
            setp((x, y), A)
        else:
            setp((x, y), B)


def drop(s):
    """Black line and cast shadow from a part on whatever already lies under it."""
    shadow = shift(s, 2, 3) - s
    for p in shadow:
        if filled(p) and col(p)[:3] in (rgba(A)[:3], rgba(B)[:3]):
            setp(p, C)
    for p in shift(s, 0, 1) - s:
        if filled(p):
            setp(p, K)


BLOT = ['..ccc..',
        '.ccccc.',
        'ccccccK',
        '.ccccK.',
        '..KKK..']
BLOT_S = ['.cc.',
          'cccK',
          '.KK.']


def ring(x, y, w, h, bel, blots):
    sil = oval_set(x, y, w, h)
    back = oval_set(x, y, w, h - bel)
    cx = x + (w - 1) / 2
    a = w / 2
    drop(sil)
    # belly: pale crescent with plates
    for p in sil - back:
        u = p[0] - cx
        setp(p, E if u > a * 0.45 or (p[0] + 1, p[1] + 1) not in sil else D)
    for p in sil - back:
        if (p[0] - int(x)) % 5 == 2:
            setp(p, C)
    hide(back)
    for p in (shift(back, 0, 1) - back) & sil:
        setp(p, K)
    # saddles along the back, following the curve of the coil
    cy = y + (h - bel) / 2
    hb = h - bel
    for t in blots:
        bx = int(cx + t * a)
        by = int(cy + hb * 0.2 * (1 - t * t))
        big = abs(t) < 0.72
        rows = BLOT if big else BLOT_S
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch == '.':
                    continue
                p = (bx + i - len(row) // 2, by + j - len(rows) // 2)
                if p in back and p not in (shift(back, 0, 1) - back):
                    setp(p, K if ch == 'K' else C)


# ---- tail: rises to a thin tip at the far left
tail = poly_set([(1, 42), (2, 49), (5, 56), (11, 61), (22, 63), (22, 69), (9, 67), (3, 62), (0, 54), (0, 44)])
hide(tail, 2, 1, 2, 2)
for p in [(3, 50), (4, 54), (7, 59), (11, 63), (15, 65)]:
    for q in (p, (p[0] + 1, p[1])):
        if q in tail:
            setp(q, C)

# ---- the three stacked coils
ring(8, 49, 78, 21, 5, [-0.78, -0.42, -0.1, 0.2, 0.5, 0.82])
ring(15, 37, 64, 20, 5, [-0.82, -0.5, -0.14, 0.2, 0.52, 0.84])
ring(25, 26, 44, 18, 4, [-0.72, -0.34, 0.34, 0.72])

# ---- neck, pale throat with plates
neck = poly_set([(40, 18), (54, 18), (56, 32), (38, 32)])
drop(neck)
hide(neck, 2, 0, 2, 0)
throat = poly_set([(43, 18), (51, 18), (52, 32), (42, 32)])
for p in throat:
    setp(p, E if p[0] > 48 else D)
for yy in (25, 28, 31):
    for xx in range(42, 53):
        if (xx, yy) in throat:
            setp((xx, yy), C)
for yy in range(18, 33):
    for xx in range(38, 56):
        if (xx, yy) in neck and (xx, yy) not in throat and ((xx + 1, yy) in throat or (xx - 1, yy) in throat):
            setp((xx, yy), K)

# ---- head, facing the player
HEAD = mirror([
    '........aaaaaaaa',
    '.....aaaaaaaaaaa',
    '...aaaaaaaaabbbb',
    '..aaaaaaaabbcccc',
    '.aaaaaaabbbccccc',
    '.aaaaabbbbbbcccc',
    'aaaabbbbbbbbbccc',
    'aaabKKbbbbbbbbbb',
    'aaabbcKKKbbbbbbb',
    'aabbbccggKKbbbbb',
    'aabbbbcccccKbbbb',
    'abbbbbbbbbbbbbbb',
    'abbbbbbbbbbbbKbb',
    'abbbbbbbbbbbbbbb',
    'bbbbbbbbbbbbbbbb',
    'bcbbbbbbbbbbbbbb',
    '.KKKKKKKKKKKKKKK',
    '.bKcdddccccccccc',
    '..Kccddccccccccc',
    '...KcdcKKKKKKKKK',
    '....bKKddddddddd',
    '.....bbKdeddedde',
    '......ccKddddddd',
    '........cKKKKKKK',
])
head = grid(HEAD, PAL)
hd = head.load()
HX, HY = 31, 0
hs = {(i, j) for j in range(head.height) for i in range(head.width) if hd[i, j][3]}
mid = (head.width - 1) // 2
for i, j in hs:
    if hd[i, j][:3] == (0, 0, 0):
        continue
    if i > mid + 1 and hd[i, j] == rgba(A):
        hd[i, j] = rgba(B)
    if i > mid and hd[i, j] == rgba(D):
        hd[i, j] = rgba(E) if i > mid + 8 else rgba(D)
    if ((i + 2, j + 1) not in hs or (i + 1, j + 2) not in hs) and hd[i, j] in (rgba(A), rgba(B)):
        hd[i, j] = rgba(C)
drop(shift(hs, HX, HY))
stamp(im, head, HX, HY)

# ---- floating skulls
SKULL = [
    '..fffff..',
    '.fffffffg',
    'fffffffgg',
    'fKKfffKKg',
    'fKKfffKKg',
    'ffffKfffg',
    '.gfffffg.',
    '..fKfKg..',
    '..hKhKh..',
]
SMALL = [
    '.fffff.',
    'ffffffg',
    'fKKfKKg',
    'fKKfKKg',
    'fffKffg',
    '.gfffg.',
    '.hKhKh.',
]
stamp(im, grid(SKULL, PAL), 16, 9)
stamp(im, grid(SMALL, PAL), 73, 7)
stamp(im, grid(SKULL, PAL), 5, 31)

im = outline(im)
save(im)
