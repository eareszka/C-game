from pix import *

L = 'fce4a0'   # hide light
M = 'd0c078'   # hide mid
D = 'b2966a'   # hide shade
R = '792727'   # claw / fang
H = 'b6433d'   # claw lit

PAL = {'h': H, 'r': R}
W, HT = 58, 46
im = canvas(W, HT)


def line(pts, colour):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            dot(im, round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), colour)


def spots(pts, colour):
    for x, y in pts:
        dot(im, x, y, colour)


# hide: one broad stretched star with shallow valleys
poly(im, [(18, 11), (12, 10), (6, 10), (7, 14), (10, 17), (6, 19), (3, 22), (5, 25), (9, 27),
          (8, 31), (7, 34), (11, 34), (15, 33), (18, 33), (19, 38), (22, 38), (25, 36), (28, 34),
          (31, 36), (34, 38), (37, 38), (38, 36), (39, 32), (43, 33), (47, 34), (49, 34), (48, 30),
          (46, 27), (50, 26), (53, 23), (52, 20), (48, 17), (49, 14), (50, 11), (50, 8), (46, 9),
          (42, 11), (38, 11)], L)

# black folds running in from each valley
line([(10, 17), (14, 18)], 'K' and '000000')
line([(9, 27), (13, 26)], '000000')
line([(18, 33), (19, 30)], '000000')
line([(28, 34), (28, 31)], '000000')
line([(39, 32), (37, 29)], '000000')
line([(46, 27), (42, 25)], '000000')
line([(48, 17), (44, 18)], '000000')

# head: a stepped round face, sitting up out of the top rim
HEAD = [(4, 9), (2, 13), (1, 15), (1, 15), (0, 17), (0, 17), (0, 17), (0, 17), (0, 17),
        (0, 17), (1, 15), (2, 13), (3, 11), (5, 7)]
HX, HY = 20, 4
head = set()
for i, (a, n) in enumerate(HEAD):
    for x in range(n):
        head.add((HX + a + x, HY + i))
px = im.load()
for x, y in head:
    for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = (x + a, y + b)
        if n not in head and px[n][3]:
            px[n] = (0, 0, 0, 255)
for x, y in head:
    px[x, y] = rgba(L)

# shade follows the body: light from the upper left
LIGHT, MID, DARK = rgba(L), rgba(M), rgba(D)
src = im.copy().load()


def lit(x, y):
    return 0 <= x < W and 0 <= y < HT and src[x, y] == LIGHT


for y in range(HT):
    for x in range(W):
        if src[x, y] != LIGHT:
            continue
        if not lit(x + 1, y + 1) or not lit(x + 1, y):
            px[x, y] = DARK
        elif not lit(x + 2, y + 2) or not lit(x + 3, y + 1):
            px[x, y] = MID

# stretch creases, one set per lobe
line([(10, 12), (15, 14)], M)
line([(8, 13), (10, 14)], D)
line([(7, 22), (13, 22)], M)
line([(9, 24), (12, 24)], D)
line([(11, 32), (14, 29)], M)
line([(13, 31), (15, 30)], D)
line([(22, 35), (24, 30)], M)
line([(32, 35), (31, 30)], M)
line([(34, 33), (33, 31)], D)
line([(44, 31), (41, 28)], M)
line([(49, 22), (43, 22)], M)
line([(47, 12), (43, 15)], M)
line([(47, 15), (45, 16)], D)
# black strain lines radiating out from the face
line([(19, 20), (15, 21), (13, 22)], '000000')
line([(37, 20), (41, 21), (43, 22)], '000000')
line([(23, 23), (22, 27)], '000000')
line([(33, 23), (34, 27)], '000000')
line([(19, 14), (16, 14), (14, 15)], '000000')
line([(37, 14), (40, 14), (42, 15)], '000000')

# face: solid 2 px eyes, angry brows
spots([(24, 10), (24, 11)], '000000')
spots([(32, 10), (32, 11)], '000000')
line([(22, 8), (25, 9)], D)
line([(34, 8), (31, 9)], D)
spots([(28, 12)], M)

# horns
stamp(im, grid(['...hh..',
                '..hrr..',
                '.hrr...',
                '.hrr...',
                '..hrrr.',
                '...hrrr',
                '....hrr'], PAL), 15, 0)
stamp(im, grid(['.....r',
                '....hr',
                '...hrr',
                '..hrr.',
                'hrrr..',
                'rrr...'], PAL), 35, 1)

# wide black mouth across the face, a row of fangs hanging from it
stamp(im, grid(['..KKKKKKKKKKKKKKKKK..',
                '.hhrKhhrKhhrKhhrKhhr.',
                '.KhK.hhrKhhrKhhr.KrK.',
                '..K..KrKKhhrKKrK..K..',
                '......K..KrK..K......',
                '..........K..........'], PAL), 18, 14)

# claws on the rim, hooked, lit on the upper left
stamp(im, grid(['h.....', 'hr....', '.hrr..', '.hrrr.', '..rrrr', '...rr.'], PAL), 2, 6)
stamp(im, grid(['..hh', 'hhrr', '.rrr', '..rr'], PAL), 0, 21)
stamp(im, grid(['...hr', '..hrr', '..hrr', '.hrr.', '.hr..', 'h....'], PAL), 4, 33)
stamp(im, grid(['hrrrr', '.hrrr', '.hrr.', '..hr.', '..h..', '..r..'], PAL), 18, 37)
stamp(im, grid(['hrrrr', '.hrrr', '.hrr.', '.hr..', '..hr.', '...r.'], PAL), 34, 37)
stamp(im, grid(['hr...', 'hrrr.', '.hrrr', '..hrr', '...hr', '....r'], PAL), 47, 33)
stamp(im, grid(['hh...', 'rhhh.', 'rrrrr', 'rrr..'], PAL), 52, 20)
stamp(im, grid(['....h', '...hr', '..hrr', '.hrr.', 'hrrr.', 'rrr..'], PAL), 49, 3)

im = outline(im)
save(im)
