from pix import *

# Left half is drawn by hand, then mirrored. On the mirrored side the
# a/s and C/N pairs swap, so the light stays on the upper left.
PAL = {
    't': 'b6433d', 'a': 'b6433d',   # lit
    'e': 'b6433d', 'f': '792727',   # lit on the left, mid on the right
    'b': '792727',                  # body
    'd': '531b1c', 's': '531b1c',   # shade
    'c': 'e8e0c0', 'C': 'e8e0c0',   # bone
    'm': 'cebe82',
    'n': 'b29e5c', 'N': 'b29e5c',
}
SWAP = {'a': 's', 's': 'a', 'C': 'N', 'N': 'C', 'e': 'f'}
W, H = 25, 45
g = [['.'] * W for _ in range(H)]


def s(y, x0, x1, ch):
    for x in range(x0, x1 + 1):
        g[y][x] = ch


def pts(lst, ch):
    for x, y in lst:
        g[y][x] = ch


# ---- barbs, behind the body
pts([(1, 0), (1, 1), (2, 2), (2, 3), (3, 4), (3, 5), (4, 6), (4, 7), (5, 8), (5, 9), (6, 10)], 'c')
pts([(4, 5), (5, 7), (6, 8), (6, 9), (7, 10)], 'N')
pts([(9, 3), (9, 4), (10, 5), (10, 6), (10, 7), (11, 8), (11, 9), (11, 10), (12, 11), (12, 12)], 'c')
pts([(11, 7), (12, 8), (12, 9), (12, 10), (13, 11), (13, 12)], 'N')
pts([(18, 8), (18, 9), (18, 10), (19, 11), (19, 12), (19, 13), (20, 14), (20, 15), (20, 16)], 'c')
pts([(20, 12), (20, 13), (21, 14), (21, 15), (21, 16)], 'N')
pts([(15, 11), (15, 12), (16, 13), (16, 14)], 'c')
for y in range(3, 7):
    g[y][24] = 'c'
for y in range(7, 18):
    g[y][23] = 'C'
    g[y][24] = 'm'

# ---- side spurs on the legs
pts([(1, 16), (2, 17), (3, 18)], 'c')
pts([(1, 24), (2, 25)], 'c')
pts([(0, 31), (1, 32), (2, 33)], 'c')
pts([(9, 25), (10, 26)], 'c')
pts([(9, 33), (10, 34)], 'c')

# ---- arms and shoulders
for y, x0, x1 in [(11, 6, 9), (12, 5, 11), (13, 4, 12), (14, 4, 13), (15, 4, 15), (16, 4, 17),
                  (17, 4, 24), (18, 4, 24), (19, 4, 7), (19, 10, 24), (20, 4, 7), (20, 11, 24),
                  (21, 3, 6), (21, 11, 24), (22, 3, 6), (22, 11, 24), (23, 3, 6), (23, 11, 16),
                  (24, 3, 5), (24, 11, 15)]:
    s(y, x0, x1, 'b')

# ---- legs
for y in range(25, 27):
    s(y, 3, 5, 'b')
for y in range(27, 36):
    s(y, 3, 4, 'b')
for y in range(36, 41):
    s(y, 2, 3, 'b')
for y in range(25, 31):
    s(y, 11, 13, 'b')
for y in range(31, 36):
    s(y, 11, 12, 'b')
for y in range(36, 41):
    s(y, 10, 11, 'b')

# leg shade: lit on the outer side, dark on the inner
for y in range(13, 27):
    x = 4 if y < 21 else 3
    g[y][x] = 'a'
    g[y][x + 3 if y < 21 else x + 2] = 's'
for y in range(27, 36):
    g[y][3], g[y][4] = 'a', 's'
for y in range(36, 41):
    g[y][2], g[y][3] = 'a', 's'
for y in range(21, 31):
    g[y][11], g[y][13] = 'a', 's'
for y in range(31, 36):
    g[y][11], g[y][12] = 'a', 's'
for y in range(36, 41):
    g[y][10], g[y][11] = 'a', 's'

# arm tops catch the light, undersides fall dark
pts([(6, 11), (7, 11), (8, 11), (9, 11), (5, 12), (10, 12), (11, 12), (12, 13), (13, 14),
     (14, 15), (15, 15), (16, 16), (17, 16), (18, 17), (19, 17), (20, 17), (21, 17), (22, 17), (23, 17), (24, 17)], 't')
pts([(8, 18), (9, 18), (10, 19), (14, 22), (15, 23), (15, 24), (14, 24)], 'd')

# ---- ridges cut across the arms
pts([(9, 13), (9, 14), (10, 15), (10, 16)], 'K')
pts([(14, 17), (14, 18), (15, 19), (15, 20)], 'K')
pts([(19, 18), (19, 19), (19, 20)], 'K')
# shoulder and hip joints
pts([(7, 16), (7, 17), (7, 18)], 'K')
pts([(14, 20), (13, 21), (12, 22)], 'K')
# notches at the knees
pts([(4, 28), (4, 35), (13, 28), (12, 35)], 'K')

# ---- head: seam, then skull
pts([(20, 21), (21, 21), (22, 21), (23, 21), (24, 21), (18, 22), (19, 22), (17, 23), (16, 24), (16, 25)], 'K')
s(22, 20, 24, 't')
s(23, 18, 24, 't')
s(24, 17, 24, 't')
for y in range(25, 30):
    s(y, 17, 24, 't')
for y in range(30, 34):
    s(y, 17, 18, 't')
for y in range(34, 37):
    g[y][18] = 'b'
s(37, 19, 24, 'b')
s(38, 20, 24, 'd')
s(39, 22, 24, 'd')

# the far side of the skull turns from the light
for y in range(24, 34):
    g[y][17] = 'a'
    g[y][18] = 'e'
g[23][18] = 'e'
g[34][18] = 's'
g[35][18] = 's'
g[36][18] = 's'

# brow, suture, eye, nose, cheek hollow
pts([(19, 25), (20, 25), (21, 26), (22, 27)], 'b')
pts([(24, 23), (24, 24), (24, 25)], 'b')
pts([(19, 27), (20, 27)], 'K')
pts([(24, 28), (24, 29), (23, 29)], 'K')
pts([(19, 29)], 'b')

# mouth
s(30, 19, 24, 'K')
for y in range(31, 37):
    s(y, 19, 24, 'K')
for x in (20, 22, 24):
    pts([(x, 31), (x, 32)], 'c')
pts([(20, 33), (22, 33)], 'm')
g[33][24] = 'c'
for x in (19, 21, 23):
    pts([(x, 36), (x, 35)], 'c')
g[34][21] = 'm'
g[34][23] = 'm'

# ---- feet
for cx in (2, 10):
    pts([(cx, 41), (cx + 1, 41)], 'c')
    s(42, cx - 2 if cx > 2 else 0, cx + 3, 'c')
    g[42][cx + 3] = 'N'
    pts([(cx - 2 if cx > 2 else 0, 43), (cx + 3, 43)], 'c')
    g[43][cx] = 'm'

rows = [''.join(r) + ''.join(SWAP.get(c, c) for c in r[-2::-1]) for r in g]
im = grid(rows, PAL)
im = outline(im)
save(im)
