from pix import *

W, H = 112, 106
CX = 55
WHITE, LT, MID = 'fcfcfc', 'c6ccda', '848694'
OR, ORD, GOLD = 'fc9838', 'b6433d', 'fae488'
DARK = '474751'

im = canvas(W, H)
px = im.load()


def R(pts):
    return [(CX + a, b) for a, b in pts]


def L(pts):
    return [(CX - a, b) for a, b in pts]


def S(pts):
    return R(pts) + L(pts)[::-1]


def raster(pt):
    m = Image.new('1', (W, H), 0)
    ImageDraw.Draw(m).polygon(pt, fill=1)
    return m.load()


def part(pt, tones=(WHITE, LT, MID), s1=(4, 3), s2=(1, 1)):
    """Fill a polygon. Shade falls on its lower right edge. Line it where it overlaps earlier parts."""
    q = raster(pt)

    def inside(x, y):
        return 0 <= x < W and 0 <= y < H and q[x, y]

    a, b, c = [rgba(t) for t in tones]
    for y in range(H):
        for x in range(W):
            if q[x, y]:
                col = a
                if not inside(x + s1[0], y + s1[1]):
                    col = b
                if not inside(x + s2[0], y + s2[1]):
                    col = c
                px[x, y] = col
    for y in range(H):
        for x in range(W):
            if q[x, y] or not px[x, y][3]:
                continue
            if any(inside(x + i, y + j) for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = BLACK


def recolour(pt, frm, to):
    """Mass shade: swap one tone for another inside a polygon."""
    q = raster(pt)
    f, t = rgba(frm), rgba(to)
    for y in range(H):
        for x in range(W):
            if q[x, y] and px[x, y] == f:
                px[x, y] = t


def ink(pts, colour=BLACK):
    ImageDraw.Draw(im).line([(CX + a, b) for a, b in pts], fill=rgba(colour))


def fur(pts, mirror_it=True):
    """A black fur line with a small clump shadow on its lower right."""
    sets = [pts, [(-a, b) for a, b in pts]] if mirror_it else [pts]
    for p in sets:
        m = Image.new('1', (W, H), 0)
        ImageDraw.Draw(m).line([(CX + a, b) for a, b in p], fill=1)
        q = m.load()
        white, light, mid = rgba(WHITE), rgba(LT), rgba(MID)
        for y in range(H - 2):
            for x in range(W - 2):
                if q[x, y]:
                    for i, j in ((1, 0), (1, 1), (2, 1)):
                        c = px[x + i, y + j]
                        if c == white:
                            px[x + i, y + j] = light
                        elif c == light and (i, j) == (1, 0):
                            px[x + i, y + j] = mid
        ink(p)


# ---- hind legs, set back: one tone down
hind = [(27, 48), (38, 46), (43, 50), (45, 57), (45, 67), (44, 75), (43, 81), (45, 84), (45, 89), (43, 91),
        (29, 91), (28, 84), (29, 76), (27, 64)]
for f in (R, L):
    part(f(hind), (LT, LT, MID), (3, 2), (2, 1))
recolour(R([(41, 50), (46, 50), (46, 92), (42, 92), (42, 70)]), LT, MID)
recolour(L([(40, 74), (46, 74), (46, 84), (40, 84)]), LT, MID)
for x in (33, 37, 41):
    fur([(x, 86), (x, 90)])
fur([(36, 54), (38, 57), (38, 61)])
fur([(40, 66), (40, 70), (38, 72)])
fur([(34, 76), (34, 80), (36, 82)])

# ---- body and hump
body = [(0, 29), (6, 28), (9, 29), (13, 28), (18, 29), (22, 31), (25, 31), (29, 34), (33, 37), (34, 36), (37, 41),
        (39, 45), (39, 47), (41, 53), (41, 62), (39, 70), (33, 75), (24, 77), (17, 79), (14, 77), (11, 81),
        (8, 78), (5, 82), (2, 79), (0, 82)]
part(S(body), (WHITE, LT, MID), (6, 4), (2, 2))
# mass shade on the far side of the hump
recolour(R([(16, 28), (30, 30), (42, 44), (42, 76), (18, 76), (24, 50), (20, 38)]), WHITE, LT)
recolour(R([(32, 40), (42, 50), (42, 72), (34, 72), (36, 56)]), LT, MID)
# belly shadow behind the forelegs
poly(im, S([(0, 70), (12, 70), (12, 79), (11, 80), (8, 77), (5, 81), (2, 78), (0, 81)]), MID)
poly(im, S([(0, 75), (9, 75), (8, 77), (5, 81), (2, 78), (0, 81)]), DARK)

# hump fur lines
fur([(10, 32), (12, 35), (15, 34), (17, 36)])
fur([(19, 33), (21, 36), (24, 35)])
fur([(26, 37), (28, 40), (31, 40), (32, 43)])
fur([(34, 46), (36, 49), (36, 53)])
fur([(30, 46), (30, 49), (32, 50)])
fur([(6, 31), (6, 34), (8, 35)])
fur([(37, 58), (37, 62), (35, 64)])

# ---- forelegs and paws
fore = [(12, 56), (22, 50), (29, 52), (33, 58), (34, 66), (33, 74), (31, 82), (32, 87), (34, 91), (34, 95), (32, 97),
        (10, 97), (8, 95), (8, 91), (10, 87), (11, 80), (10, 70), (10, 62)]
for f in (L, R):
    part(f(fore), (WHITE, LT, MID), (4, 2), (1, 1))
# the near leg's right half falls away from the light
recolour(R([(24, 50), (35, 56), (35, 98), (26, 98), (28, 80), (26, 66)]), WHITE, LT)
recolour(R([(30, 58), (35, 60), (35, 84), (31, 84)]), LT, MID)
# inner side of the left leg
recolour(L([(10, 60), (14, 60), (14, 84), (10, 84)]), WHITE, LT)

# claws: pointed, tone on black
for x in (11, 17, 23, 29):
    for s in (-1, 1):
        cx = CX + s * x - (0 if s > 0 else 1)
        rect(im, cx, 97, 2, 2, MID)
        dot(im, cx + 1, 99, MID)

# toes
for x in (14, 20, 26):
    fur([(x, 90), (x, 96)])
ink([(11, 87), (14, 86), (20, 86), (26, 86), (31, 87)])
ink([(-11, 87), (-14, 86), (-20, 86), (-26, 86), (-31, 87)])

# leg fur lines
fur([(16, 62), (16, 66), (18, 68)])
fur([(25, 58), (25, 62), (27, 64)])
fur([(20, 72), (20, 76), (22, 78)])
fur([(28, 70), (28, 74), (26, 76)])
fur([(14, 78), (14, 81), (16, 83)])
fur([(24, 80), (24, 83), (26, 84)])

# ---- orange ear tufts
tuft = [(21, 45), (26, 42), (31, 44), (34, 49), (36, 55), (34, 58), (35, 63), (32, 62), (31, 67), (28, 64),
        (26, 69), (23, 64)]
for f in (L, R):
    part(f(tuft), (OR, ORD, ORD), (3, 2), (2, 2))
for s in (-1, 1):
    ink([(s * 26, 47), (s * 30, 53), (s * 31, 60)], ORD)
    ink([(s * 25, 52), (s * 27, 58), (s * 27, 63)], ORD)
    ink([(s * 28, 45), (s * 31, 48)], GOLD)

# ---- ears
ear = [(14, 41), (15, 37), (18, 34), (22, 34), (25, 37), (25, 42), (22, 46)]
for f in (L, R):
    part(f(ear), (WHITE, LT, MID), (2, 2), (1, 1))
    poly(im, f([(18, 39), (20, 37), (22, 39), (22, 42), (18, 42)]), MID)

# ---- head
head = [(0, 38), (8, 38), (14, 39), (19, 42), (22, 46), (24, 51), (25, 57), (24, 62), (22, 66), (19, 70), (14, 73),
        (8, 75), (0, 76)]
part(S(head), (WHITE, LT, MID), (4, 3), (1, 1))
# far cheek and brow hollow
recolour(R([(15, 46), (21, 45), (26, 56), (22, 68), (14, 74), (14, 62), (18, 54)]), WHITE, LT)
recolour(L([(14, 68), (18, 67), (16, 72), (10, 75), (9, 72)]), WHITE, LT)

# cheek and brow fur
fur([(22, 60), (20, 62), (20, 65)])
fur([(17, 66), (15, 68), (15, 71)])
fur([(16, 44), (18, 47)])
fur([(9, 42), (9, 44), (11, 45)])

# brows and eyes
for s in (-1, 1):
    ink([(s * 6, 51), (s * 12, 49), (s * 18, 48)], MID)
    ink([(s * 7, 51), (s * 12, 50)], MID)
    x = CX + s * 10 - (0 if s > 0 else 1)
    rect(im, x, 54, 2, 2, BLACK)

# ---- muzzle
muz = [(0, 56), (6, 56), (10, 58), (13, 62), (13, 67), (10, 71), (5, 73), (0, 74)]
part(S(muz), (WHITE, LT, MID), (3, 2), (1, 1))
recolour(R([(7, 59), (14, 60), (14, 70), (8, 72), (9, 64)]), WHITE, LT)

# nose
poly(im, S([(0, 57), (4, 57), (5, 58), (5, 60), (3, 62), (0, 63)]), DARK)
rect(im, CX - 3, 58, 2, 1, MID)
# mouth
ink([(0, 63), (0, 66)])
for s in (-1, 1):
    ink([(0, 66), (s * 3, 68), (s * 7, 67), (s * 9, 65)])
# fangs
rect(im, CX - 6, 68, 2, 2, LT)
rect(im, CX + 5, 68, 2, 2, LT)
dot(im, CX - 5, 70, MID)
dot(im, CX + 5, 70, MID)

# ---- horn, banded, on the brow
q = raster(S([(1, 18), (2, 25), (3, 33), (4, 41), (5, 47), (0, 48)]))
for y in range(H):
    for x in range(W):
        if q[x, y]:
            band = ((y + (x - CX) // 2) // 5) % 2
            shade = x - CX >= 1
            if band:
                px[x, y] = rgba(ORD if shade else OR)
            else:
                px[x, y] = rgba(OR if shade else GOLD)
for y in range(H):
    for x in range(W):
        if q[x, y] or not px[x, y][3]:
            continue
        if any(q[x + i, y + j] for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            px[x, y] = BLACK

# ---- star
STAR = ['....a....',
        '....a....',
        '...aba...',
        'aaaabbccc',
        '.aabbbcc.',
        '..abbbc..',
        '..ab.cc..',
        '.aa...cc.']
stamp(im, grid(STAR, {'a': WHITE, 'b': GOLD, 'c': OR}), CX - 4, 11)

im = outline(im)
save(im)
