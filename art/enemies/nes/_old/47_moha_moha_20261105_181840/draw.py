from pix import *

G1 = '4fa667'   # green lit
G2 = '2c6c44'   # green shade
CR = 'cebe82'   # cream edge
S1 = '848694'   # shell lit
S2 = '595965'   # shell mid
S3 = '34343e'   # shell shade
B1 = '94703d'   # fin lit
B2 = '583518'   # fin shade
K = '000000'

im = canvas(74, 44)


def spans(rows, colour):
    for y, x0, x1 in rows:
        rect(im, x0, y, x1 - x0 + 1, 1, colour)


def line(pts, colour=K):
    ImageDraw.Draw(im).line(pts, fill=rgba(colour), width=1)


def dots(pts, colour):
    for x, y in pts:
        rect(im, x, y, 1, 1, colour)


# ---- far legs, in shade, behind everything
rect(im, 30, 35, 17, 2, G2)
poly(im, [(32, 36), (37, 36), (37, 42), (31, 42)], G2)
poly(im, [(41, 36), (46, 36), (47, 42), (41, 42)], G2)
dots([(30, 42), (31, 42), (47, 42), (48, 42)], CR)
line([(34, 40), (34, 42)])
line([(44, 40), (44, 42)])
line([(30, 37), (46, 37)])

# ---- tail: rises to the left, cream along its belly
poly(im, [(5, 29), (9, 29), (20, 32), (24, 36), (18, 38), (12, 35)], G1)
poly(im, [(10, 33), (16, 36), (18, 38), (24, 36), (24, 38), (17, 39), (11, 35)], G2)
line([(7, 31), (12, 35), (16, 38), (20, 39)], CR)
dots([(9, 30), (10, 30), (13, 31), (14, 31), (11, 32)], G2)

# ---- forked brown tail fin
poly(im, [(0, 22), (2, 22), (7, 28), (9, 31), (6, 33), (3, 28)], B1)
poly(im, [(6, 33), (9, 31), (8, 36), (3, 41), (0, 42), (2, 38)], B1)
poly(im, [(3, 28), (6, 33), (2, 38), (0, 42), (3, 41), (8, 36), (8, 34), (6, 31)], B2)
line([(1, 23), (5, 29), (6, 31)], B2)

# ---- back leg, kicked back with cream on its underside
back = [(35, 22, 33), (36, 22, 32), (37, 21, 31), (38, 20, 30), (39, 19, 29),
        (40, 17, 28), (41, 15, 28), (42, 14, 27)]
spans(back, G1)
spans([(y, x1 - 2, x1) for y, x0, x1 in back], G2)
rect(im, 19, 43, 9, 1, G2)
rect(im, 14, 43, 5, 1, CR)
dots([(13, 43), (12, 43), (13, 42)], CR)
line([(22, 35), (21, 37), (18, 40), (15, 41)])     # seam against the tail
line([(18, 41), (18, 43)])                         # toes
line([(22, 41), (22, 43)])
line([(25, 37), (28, 38)])                         # knee crease

# ---- front leg, stepping forward with cream on its front
front = [(36, 46, 58), (37, 46, 58), (38, 47, 59), (39, 47, 59),
         (40, 48, 60), (41, 48, 62), (42, 48, 63)]
spans(front, G1)
spans([(y, x1 - 3, x1 - 1) for y, x0, x1 in front], G2)
spans([(y, x1, x1) for y, x0, x1 in front], CR)
rect(im, 48, 43, 11, 1, G2)
rect(im, 59, 43, 5, 1, CR)
dots([(64, 42), (64, 43), (65, 43)], CR)
line([(46, 36), (47, 39), (48, 42)])               # seam against the far leg
line([(55, 41), (55, 43)])                         # toes
line([(59, 41), (59, 43)])
line([(52, 38), (56, 36)])                         # shoulder crease

# ---- neck: S-curve up from the shoulder
neck = [
    (35, 50, 60), (34, 52, 61), (33, 53, 61), (32, 54, 62), (31, 55, 62),
    (30, 55, 63), (29, 56, 63), (28, 57, 64), (27, 57, 64), (26, 58, 64),
    (25, 58, 65), (24, 58, 65), (23, 59, 65), (22, 59, 65), (21, 59, 65),
    (20, 59, 65), (19, 59, 65), (18, 58, 64), (17, 58, 64), (16, 58, 64),
    (15, 57, 63), (14, 57, 63), (13, 57, 63),
]
spans(neck, G1)
# back-of-neck shade band on the far side from the cream, then the cream edge
spans([(y, x1 - 2, x1 - 1) for y, x0, x1 in neck if y >= 16], G2)
spans([(y, x1, x1) for y, x0, x1 in neck if y >= 16], CR)
spans([(y, x1 - 1, x1) for y, x0, x1 in neck if 20 <= y <= 31], CR)
# neck folds: short black creases where the neck bends
line([(58, 26), (60, 27)])
line([(59, 22), (61, 23)])
line([(58, 18), (60, 19)])
line([(55, 31), (57, 32)])

# ---- head: wedge snout pointing up and right
head = grid([
    '................ccc',
    '.............aaaac.',
    '..........aaaaaaac.',
    '.....aaaaaaaaaaKK..',
    '...aaaaaaaaaaKKcc..',
    '..aaaKKaaaaKKddd...',
    '.aaaaaaaaKKdddd....',
    '.aaaaaaaKddddd.....',
    '.aaaaaaKddddc......',
    '.aaaaaaKdddc.......',
    '.aaaaaaKddc........',
    '.adaaaaaKc.........',
    '.addaaaddc.........',
    '..ddddddc..........',
], {'a': G1, 'c': CR, 'd': G2})
stamp(im, head, 55, 0)

# ---- domed shell
dome = [
    (17, 28, 44), (18, 25, 47), (19, 23, 49), (20, 21, 51), (21, 20, 52),
    (22, 19, 53), (23, 18, 54), (24, 18, 54), (25, 17, 55), (26, 17, 55),
    (27, 16, 56), (28, 16, 56), (29, 16, 56), (30, 16, 56),
]
spans(dome, S2)

# lit and shaded patches per plate, light from the upper left
poly(im, [(30, 18), (42, 18), (40, 20), (31, 20), (28, 23)], S1)
rect(im, 29, 19, 5, 3, S1)
poly(im, [(25, 19), (28, 18), (26, 21), (20, 23)], S1)
poly(im, [(44, 19), (47, 19), (49, 20), (45, 21)], S1)
rect(im, 17, 26, 4, 2, S1)
rect(im, 24, 27, 3, 2, S1)
rect(im, 31, 27, 3, 2, S1)
rect(im, 38, 27, 3, 2, S1)
rect(im, 46, 27, 2, 1, S1)
rect(im, 38, 24, 4, 1, S3)
rect(im, 41, 22, 4, 2, S3)
rect(im, 48, 23, 5, 3, S3)
poly(im, [(50, 21), (53, 23), (52, 26), (49, 24)], S3)
rect(im, 52, 27, 4, 3, S3)
rect(im, 43, 29, 5, 1, S3)
rect(im, 34, 29, 2, 1, S3)
rect(im, 25, 29, 2, 1, S3)

# plate seams
line([(29, 17), (26, 21), (30, 26), (42, 26), (46, 21), (43, 17)])
line([(26, 21), (18, 24)])
line([(46, 21), (54, 24)])
line([(18, 24), (22, 30)])
line([(30, 26), (28, 30)])
line([(36, 26), (36, 30)])
line([(42, 26), (45, 30)])
line([(54, 24), (50, 30)])

# rim: a heavy band round the shell base, with notches
rect(im, 14, 31, 45, 3, S2)
rect(im, 14, 31, 45, 1, S1)
rect(im, 45, 33, 14, 1, S3)
rect(im, 15, 34, 43, 1, S3)
line([(16, 30), (56, 30)])
for x in (21, 27, 33, 39, 45, 51):
    line([(x, 31), (x, 33)])
line([(14, 34), (15, 34)])

im = outline(im)
save(im)
