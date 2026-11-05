from pix import *

W, H = 63, 54
LIT, TAN, DUN = 'f0b890', 'd7a175', '967448'
PINK, RED, DEEP, DARK = 'ec8476', 'b6433d', '792727', '531b1c'
CREAM = 'e8e0c0'
K = '000000'

PAL = {'c': CREAM, 'd': DEEP, 'x': DARK}

# A broken, chipped lump rather than a clean pentagon
SHAPE = [(27, 0), (33, 0), (35, 2), (39, 3), (42, 7), (47, 8), (52, 13), (54, 18), (58, 20),
         (62, 26), (62, 30), (59, 33), (60, 38), (56, 42), (56, 47), (52, 50), (50, 53),
         (13, 53), (10, 51), (7, 46), (8, 42), (3, 38), (4, 33), (0, 30), (0, 25), (5, 21),
         (7, 16), (11, 12), (15, 10), (20, 6), (24, 4)]
CENTRE = [(24, 7), (39, 7), (45, 30), (49, 53), (14, 53), (17, 30)]

im = canvas(W, H)
d = ImageDraw.Draw(im)


def ln(pts, c=K):
    d.line(pts, fill=rgba(c))


sil = canvas(W, H)
poly(sil, SHAPE, 'ffffff')
mid = canvas(W, H)
poly(mid, CENTRE, 'ffffff')
sp, mp, ip = sil.load(), mid.load(), im.load()

# Strata per facet. Bands bend at each facet edge, in steps 5 px long.
STONE = {'l': (TAN, LIT), 'm': (TAN, DUN), 'r': (DUN, TAN)}
ROCK = {'l': (RED, PINK), 'm': (RED, DEEP), 'r': (DEEP, RED)}


def band(t, f):
    if t < 11:
        return STONE[f][1] if f == 'l' else STONE[f][0]
    if t < 12:
        return STONE[f][1] if f != 'l' else STONE[f][0]
    if t < 14:
        return STONE[f][0]
    if t < 15:
        return STONE[f][1]
    if t < 23:
        return STONE[f][0]
    if t < 24:
        return STONE[f][1]
    if t < 25:
        return K
    if t < 26:
        return ROCK[f][1] if f == 'l' else ROCK[f][0]
    if t < 30:
        return ROCK[f][0]
    if t < 31:
        return K
    if t < 32 and f == 'l':
        return LIT
    if t < 37:
        return STONE[f][0]
    if t < 38:
        return K
    if t < 39:
        return ROCK[f][1] if f == 'l' else ROCK[f][0]
    if t < 45:
        return ROCK[f][0]
    if t < 46:
        return ROCK[f][1]
    return ROCK[f][0]


for y in range(H):
    for x in range(W):
        if not sp[x, y][3]:
            continue
        if mp[x, y][3]:
            f, t = 'm', y
        elif x < 31:
            f, t = 'l', y - (18 - (x // 5) * 5) // 5
        else:
            f, t = 'r', y - ((x // 5) * 5 - 44) // 5
        ip[x, y] = rgba(band(t, f))

# Red cap
poly(im, [(27, 0), (33, 0), (35, 2), (39, 3), (41, 6), (21, 6), (24, 4)], RED)
poly(im, [(33, 0), (35, 2), (39, 3), (41, 6), (35, 6), (33, 3)], DEEP)
rect(im, 27, 1, 4, 1, PINK)
rect(im, 25, 4, 5, 1, PINK)
ln([(20, 7), (42, 7)])

# Facet edges
ln([(24, 7), (17, 30)])
ln([(39, 7), (45, 30)])
ln([(17, 30), (17, 38), (14, 53)])
ln([(45, 30), (45, 38), (49, 53)])
# Cracks
ln([(11, 12), (14, 14)])
ln([(47, 8), (46, 12), (50, 14)])
ln([(4, 33), (7, 35)])
ln([(59, 33), (56, 34)])
ln([(22, 39), (20, 44), (17, 46)])
ln([(41, 39), (43, 43), (46, 45)])
ln([(19, 53), (21, 49)])
ln([(44, 53), (42, 50)])

# Central red boss
poly(im, [(21, 25), (22, 20), (26, 14), (36, 14), (40, 20), (41, 25)], K)
poly(im, [(22, 24), (23, 20), (27, 15), (35, 15), (39, 20), (40, 24)], RED)
poly(im, [(33, 15), (35, 15), (39, 20), (40, 24), (35, 24), (34, 20)], DEEP)
rect(im, 27, 16, 5, 1, PINK)
rect(im, 25, 19, 3, 1, PINK)
ln([(26, 24), (28, 21), (35, 21)], DARK)

# Zigzag panel
rect(im, 18, 31, 27, 7, DEEP)
for i in range(6):
    x = 19 + i * 4
    ln([(x, 36), (x + 2, 33), (x + 4, 36)], CREAM)

# Cleft
for x0, x1, y0 in ((28, 33, 41), (25, 36, 43), (24, 38, 46), (22, 39, 49)):
    rect(im, x0, y0, x1 - x0 + 1, H - y0, K)
for x0, x1, y0 in ((29, 32, 42), (26, 35, 44), (25, 37, 47), (23, 38, 50)):
    rect(im, x0, y0, x1 - x0 + 1, H - y0, DEEP)
for x0, x1, y0 in ((30, 32, 44), (28, 35, 46), (27, 37, 48), (26, 38, 51)):
    rect(im, x0, y0, x1 - x0 + 1, H - y0, DARK)

# Petroglyphs: cream lines with a carved red edge
SPIRAL = ['.cccccc..',
          'c......c.',
          'c.cccc..c',
          'c.c..c..c',
          'c.c.cc..c',
          'c.c.....c',
          'c..ccccc.',
          '.c.......']
SHADE = {'c': DEEP}
for flip, x in ((False, 8), (True, 45)):
    line = grid(SPIRAL, PAL)
    edge = grid(SPIRAL, SHADE)
    if flip:
        line = line.transpose(Image.FLIP_LEFT_RIGHT)
        edge = edge.transpose(Image.FLIP_LEFT_RIGHT)
    stamp(im, edge, x + 1, 15)
    stamp(im, line, x, 14)

MAN = grid(['c...c',
            'c.c.c',
            '.ccc.',
            '..c..',
            '..c..',
            '.c.c.',
            'c...c'], PAL)
stamp(im, MAN, 9, 41)
stamp(im, MAN, 50, 41)

SUN = grid(['..x..',
            'x.x.x',
            '.xxx.',
            'x.x.x',
            '..x..'], PAL)
stamp(im, SUN, 9, 33)
stamp(im, SUN, 49, 33)

im = outline(im)
save(im)
