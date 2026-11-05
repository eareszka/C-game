from pix import *

L, G, D = 'a8f0bc', '4fa667', '2c6c44'
C, B = 'e8e0c0', 'cebe82'
P, R = 'ec8476', 'b6433d'
PAL = {'l': L, 'g': G, 'd': D, 'c': C, 'b': B, 'p': P, 'r': R}

im = canvas(48, 46)
CX = 26  # the cat's centre column


def shade_right(top, bottom, cx, edge):
    """Light from the upper left: drop the right side of the part one tone."""
    px = im.load()
    g, d, l = rgba(G), rgba(D), rgba(L)
    for y in range(top, bottom):
        for x in range(cx + 1, im.width):
            if px[x, y] == l:
                px[x, y] = g
            if px[x, y] == g and x >= cx + edge:
                px[x, y] = d


# --- cactus tail, behind everything ---
def stem(x, top, bottom):
    for y in range(top, bottom):
        rect(im, x, y, 1, 1, L)
        rect(im, x + 1, y, 1, 1, G)
        rect(im, x + 2, y, 1, 1, BLACK[:3])
        rect(im, x + 3, y, 1, 1, G)
        rect(im, x + 4, y, 1, 1, D)


def flower(x, y):
    stamp(im, grid(['.p.', 'pcr', '.r.'], PAL), x, y)


stem(5, 5, 19)
stem(6, 19, 27)
stem(7, 27, 33)
stem(9, 33, 40)
# arms
rect(im, 1, 17, 4, 3, G); rect(im, 1, 19, 4, 1, D)
rect(im, 1, 11, 3, 6, G); rect(im, 1, 11, 1, 6, L); rect(im, 3, 11, 1, 6, D)
rect(im, 10, 15, 3, 3, G); rect(im, 10, 17, 3, 1, D)
rect(im, 11, 8, 3, 7, G); rect(im, 11, 8, 1, 7, L); rect(im, 13, 8, 1, 7, D)
# tail joints
for y, x in ((12, 5), (22, 6), (30, 7), (36, 9)):
    rect(im, x, y, 5, 1, BLACK[:3])
flower(1, 8)
flower(11, 5)
stamp(im, grid(['..p..', '.prp.', 'prcrp', '.prp.'], PAL), 5, 1)
# tail spines
for x, y in ((4, 8), (10, 10), (4, 15), (11, 20), (5, 24), (12, 26), (6, 29), (13, 31), (7, 34), (0, 14), (4, 13), (14, 11)):
    rect(im, x, y, 1, 1, C)

# --- haunches ---
oval(im, 11, 30, 13, 15, G)
oval(im, 29, 31, 13, 14, D)
poly(im, [(12, 34), (15, 32), (15, 35)], L)
for x, y in ((14, 37), (18, 35), (16, 41), (20, 40), (36, 36), (33, 40), (38, 41)):
    rect(im, x, y, 1, 1, C)
    rect(im, x, y + 1, 1, 1, BLACK[:3])
stamp(im, grid(['.cccccc', 'cccbcbb', 'cKcKcKb'], PAL), 12, 43)
stamp(im, grid(['ccccbb.', 'cbcbbbb', 'bKbKbKb'], PAL), 34, 43)
for x, y in ((10, 33), (11, 39), (41, 34), (42, 39), (14, 30), (38, 30)):
    rect(im, x, y, 1, 1, C)

# --- body ---
body = mirror([
    '...ggggggc',
    '..gggggccc',
    '.cgglcccbc',
    '.Kggggcccc',
    '.ggcggKccc',
    'cggKggcbcc',
    '.ggggKcccc',
    '.gcgggKccb',
    'cgKggKcccK',
    '.gggKcccbK',
    '.gcgKcccbK',
    '.gKKccccbK',
    'cggKccbcbK',
    '.gcKccccbK',
    '.gKKcbcbbK',
    '.ggKccccbK',
    '.gcKcbccbK',
    '.gKKcccbbK',
    '.ggKccccbK',
    '..gKccbcbK',
    '..KcccccbK',
    '..KcKcKcbK',
    '..KcKcKbbK',
])
stamp(im, grid(body, PAL), CX - 9, 23)
shade_right(23, 46, CX, 3)

# --- head ---
head = mirror([
    '..c.........',
    '..c.........',
    '..cg........',
    '.ggg........',
    '.gpgg......c',
    '.gpggg.....c',
    '.gprgg..c.gg',
    '.gprgllggKgK',
    '.gprlllggKgK',
    '.gggllgcgggK',
    'cggcgggKgggg',
    '.ggKgddggggg',
    'cggggggddggg',
    '.ggggggggggg',
    'cgggggKggggg',
    '.gggggKgccpp',
    'cgppggggcccr',
    '.gppggggcccK',
    'cgggcgggcKKK',
    '.cggKgggcccc',
    '..cggggggbbb',
    '...cgggggbbb',
    '.....KKKKKKK',
])
stamp(im, grid(head, PAL), CX - 11, 0)
shade_right(4, 23, CX, 7)
# pale face mask running across both eyes and the nose bridge, so the black eyes sit on lit skin
px = im.load()
for y, half in ((13, 6), (14, 8), (15, 8), (16, 7), (17, 5)):
    for x in range(CX - half, CX + half + 1):
        if px[x, y] in (rgba(G), rgba(D)):
            px[x, y] = rgba(L)

im = outline(im)
save(im)
