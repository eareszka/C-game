from pix import *

G1, G2, G3 = 'a4aaba', '848694', '595965'
M1, M2 = '4fa667', '2c6c44'
R1, R2 = '7c0a1b', 'b6433d'
T = 'e8e0c0'
K = '000000'

W, H = 90, 62
OY = 5  # head room for the moss


def P(pts):
    return [(x, y + OY) for x, y in pts]


def ln(im, pts, c):
    ImageDraw.Draw(im).line(P(pts), fill=rgba(c))


def onto(im, pts, c, within):
    tmp = canvas(im.width, im.height)
    poly(tmp, P(pts), c)
    a, b = tmp.load(), im.load()
    want = rgba(within)
    for y in range(im.height):
        for x in range(im.width):
            if a[x, y][3] and b[x, y] == want:
                b[x, y] = a[x, y]


im = canvas(W, H)

# --- body and tail, rock grey, with knocked-out rock notches on the edge
poly(im, P([(1, 16), (3, 10), (7, 6), (12, 3), (20, 2), (28, 4), (36, 8), (44, 13), (50, 19), (56, 25),
            (62, 29), (66, 28), (67, 26), (70, 24), (71, 21), (74, 18), (75, 14), (77, 12), (78, 7), (80, 2),
            (81, 10), (80, 12), (81, 18), (79, 20), (79, 27), (77, 29), (76, 35), (73, 37), (72, 41),
            (69, 42), (67, 45), (63, 45), (58, 47), (54, 48), (52, 50), (46, 50), (44, 52), (36, 52),
            (34, 53), (27, 53), (25, 52), (14, 52), (3, 52), (0, 50), (5, 45), (8, 42), (4, 30)]), G2)

# belly and under-tail shade
onto(im, [(33, 46), (42, 46), (52, 44), (62, 40), (68, 36), (74, 28), (77, 16), (83, 16), (83, 34),
          (70, 47), (50, 54), (0, 55), (0, 51), (14, 51), (24, 49)], G3, G2)

# lit brow and snout
onto(im, [(1, 16), (3, 10), (7, 6), (12, 3), (15, 3), (15, 6), (10, 8), (7, 11), (6, 14), (5, 16)], G1, G2)
# lit spine of the tail
onto(im, [(66, 29), (71, 24), (75, 16), (80, 2), (79, 12), (75, 22), (71, 28), (67, 32)], G1, G2)
# lit chin
onto(im, [(2, 49), (9, 47), (14, 48), (22, 46), (30, 42), (31, 44), (22, 48), (14, 50), (3, 51)], G1, G2)

# --- the mouth
LIP = [(1, 17), (9, 18), (16, 20), (23, 24), (28, 29), (31, 35), (31, 38), (26, 41), (20, 44), (13, 47), (9, 47)]
poly(im, P(LIP + [(6, 40), (3, 29)]), R1)

# throat: cut by ribs of gum so it never sits as a black hole
poly(im, P([(25, 29), (28, 32), (29, 36), (27, 35), (25, 32)]), K)
ln(im, [(21, 27), (24, 31), (24, 35)], K)
ln(im, [(8, 23), (11, 27), (11, 33)], K)
ln(im, [(13, 24), (16, 27), (17, 31)], K)
ln(im, [(18, 26), (20, 30)], K)
ln(im, [(6, 28), (7, 33)], K)
ln(im, [(9, 24), (12, 28), (12, 32)], R2)
ln(im, [(14, 24), (17, 27), (18, 30)], R2)

# tongue
poly(im, P([(12, 45), (10, 41), (11, 37), (15, 33), (21, 32), (26, 35), (28, 38), (24, 40), (18, 43)]), R2)
ln(im, [(14, 43), (15, 39), (19, 35), (23, 36)], R1)
ln(im, [(12, 40), (13, 36)], R1)
ln(im, [(17, 41), (20, 39)], R1)

# lips
ln(im, LIP, K)


def fang(x, y, w, h, down=True):
    """Stepped fang: base w wide at (x, y), tapering over h rows."""
    for i in range(h):
        n = max(1, w - (i * w) // h)
        off = (w - n) // 2
        yy = y + i if down else y - i
        rect(im, x + off, yy + OY, n, 1, T)


# upper fangs
fang(3, 18, 3, 6)
fang(8, 19, 3, 4)
fang(12, 20, 4, 7)
fang(18, 22, 3, 4)
fang(22, 25, 3, 5)
# lower fangs
fang(11, 46, 4, 7, False)
fang(17, 44, 3, 4, False)
fang(21, 43, 3, 5, False)
fang(26, 40, 3, 4, False)

# --- rock plates: black cracks, lit upper edge, shaded lower edge
PLATES = (
    [(33, 22), (37, 27), (35, 33), (40, 37), (47, 36)],
    [(35, 33), (33, 39), (36, 45)],
    [(47, 36), (52, 41), (51, 47)],
    [(47, 36), (55, 33), (60, 36)],
    [(60, 36), (63, 42)],
    [(36, 45), (44, 47), (51, 47)],
    [(21, 47), (28, 45), (36, 45)],
    [(8, 50), (15, 49)],
    [(40, 37), (39, 42)],
    [(55, 33), (56, 28)],
    [(68, 31), (71, 35), (69, 40)],
    [(73, 26), (76, 29), (75, 33)],
    [(76, 17), (79, 19)],
    [(24, 18), (28, 22), (32, 21)],
    [(60, 41), (66, 39)],
    [(26, 50), (34, 49)],
)
for pts in PLATES:
    ln(im, pts, K)
for pts in (
    [(38, 28), (36, 33)],
    [(36, 34), (41, 38), (46, 37)],
    [(48, 37), (55, 34), (59, 36)],
    [(34, 39), (37, 44)],
    [(53, 42), (52, 45)],
    [(41, 38), (40, 41)],
    [(61, 37), (64, 41)],
    [(69, 32), (72, 35)],
    [(25, 19), (28, 23)],
):
    ln(im, pts, G1)
for pts in (
    [(36, 27), (34, 33)],
    [(39, 38), (40, 37)],
    [(46, 38), (51, 42), (50, 46)],
    [(37, 46), (44, 48)],
    [(59, 37), (62, 43)],
    [(32, 39), (35, 45)],
    [(34, 24), (37, 28)],
):
    ln(im, pts, G3)

# --- moss back: stepped clumps, back to front
MOSS = {'a': M2, 'b': M1}
BIG = grid([
    '....aaaaaa....',
    '..aaabbbbaaa..',
    '.aabbbbbbbbaa.',
    '.abbbbbbbaaaaa',
    'aabbbbbaaaaaaK',
    'aabbbaaaaaaaaK',
    'aaaaaaaaaaaaKK',
    '.aaaaaaaaaKKK.',
    '..KKaaaaKKK...',
    '....KKKK......',
], MOSS)
MID = grid([
    '...aaaaa...',
    '.aaabbbaaa.',
    'aabbbbbaaaa',
    'abbbbaaaaaK',
    'aabbaaaaaKK',
    'aaaaaaaaKK.',
    '.KaaaaaKK..',
    '..KKKKK....',
], MOSS)
LOW = grid([
    '..aaaa..',
    '.abbbaa.',
    'abbbaaaK',
    'abaaaaaK',
    '.aaaaKK.',
    '..KKKK..',
], MOSS)
# one solid mat first, so the clumps read as a single mossy back
MAT = [(13, 2), (20, -1), (30, -1), (38, 3), (46, 9), (53, 16), (60, 23), (63, 28), (58, 30), (52, 29),
       (47, 29), (41, 27), (35, 24), (29, 20), (24, 17), (20, 13), (15, 8)]
poly(im, P([(x, y + 1) for x, y in MAT]), K)
poly(im, P(MAT), M2)
TALL = grid([
    '...aaaa...',
    '..abbbaa..',
    '.abbbbbaa.',
    'aabbbaaaaa',
    'abbbaaaaaK',
    'aabaaaaaaK',
    'aaaaaaaKK.',
    '.aaaaKK...',
    '..KKK.....',
], MOSS)
for part, x, y in (
    (BIG, 12, -3), (TALL, 24, -5), (MID, 31, -1), (BIG, 36, 3), (TALL, 46, 8), (MID, 50, 15), (LOW, 58, 21),
    (MID, 17, 4), (BIG, 24, 5), (TALL, 35, 10), (LOW, 44, 17), (LOW, 51, 23),
    (LOW, 21, 12), (TALL, 28, 13), (MID, 38, 19), (LOW, 45, 24), (LOW, 33, 19),
):
    stamp(im, part, x, y + OY)

# bare rock breaking through the moss
NUB = grid([
    '.gg..',
    'ghhgK',
    'ghggK',
    '.KKK.',
], {'g': G2, 'h': G1})
for x, y in ((32, 8), (44, 14), (22, 8)):
    stamp(im, NUB, x, y + OY)

# tufts on the skyline
for x, y, w in ((16, -4, 2), (22, -4, 1), (28, -5, 2), (36, 0, 2), (47, 6, 1), (53, 12, 2)):
    rect(im, x, y + OY, w, 1, M1)

# --- eye in a shaded socket, under a heavy brow
onto(im, [(14, 13), (21, 14), (21, 16), (15, 16)], G1, G2)
poly(im, P([(13, 10), (19, 12), (22, 12), (22, 13), (18, 13), (14, 12)]), K)
rect(im, 17, 14 + OY, 2, 1, R2)

im = outline(im)
save(im)
