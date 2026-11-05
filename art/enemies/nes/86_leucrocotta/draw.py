from pix import *

L = 'd89830'   # tawny light
T = 'c18a39'   # tawny
D = '815423'   # tawny shade, mane light
N = '583518'   # mane dark, hooves
W = 'e8e0c0'   # head white
S = 'b2966a'   # head shade
G = '34343e'   # badger stripe
E = 'f0bc3c'   # eye
K = '000000'

PAL = {'l': L, 't': T, 'm': D, 'n': N, 'w': W, 's': S, 'g': G, 'e': E}

im = canvas(44, 62)
px = im.load()
CX = 25


def span(y, x0, x1, c):
    rect(im, x0, y, x1 - x0 + 1, 1, c)


def both(y, a, b, c):
    """Fill offsets a..b from the centre on the left and the same on the right."""
    span(y, CX - b, CX - a, c)
    span(y, CX + a, CX + b, c)


def hoof(x, y):
    """Cloven hoof, 2 rows of toes under a 3 px fetlock."""
    span(y, x - 1, x + 1, N)
    rect(im, x - 2, y + 1, 2, 2, N)
    rect(im, x + 1, y + 1, 2, 2, N)
    dot(im, x - 2, y + 1, D)
    dot(im, x + 1, y + 1, D)
    dot(im, x, y + 1, K)


# ---- tail, behind everything ----
tail = [
    '.....ttt',
    '....tlt.',
    '...tlt..',
    '..tlm...',
    '..tlm...',
    '..tlm...',
    '..tlm...',
    '..tlm...',
    '..tlm...',
    '..tlm...',
    '..tlm...',
    '.mmlmm..',
    'mmnmmnm.',
    'mnmKmnm.',
    'mmnKmmn.',
    'mnmmKmn.',
    'mmnmKnn.',
    '.mnmnn..',
    '.mn.nm..',
    '..n..n..',
]
stamp(im, grid(tail, PAL), CX - 22, 28)

# ---- hind legs: further away, darker ----
HIND = [
    (32, 4, 7), (33, 4, 7), (34, 4, 7), (35, 4, 7), (36, 4, 7), (37, 4, 7),
    (38, 4, 7), (39, 5, 7), (40, 5, 7), (41, 5, 7), (42, 5, 8), (43, 5, 8),
    (44, 6, 8), (45, 6, 7), (46, 6, 7), (47, 6, 7), (48, 6, 7), (49, 6, 7),
    (50, 6, 7), (51, 6, 7), (52, 6, 7),
]
for y, a, b in HIND:
    both(y, a, b, D)
    dot(im, CX - a, y, N)
    dot(im, CX + b, y, N)
hoof(CX - 6, 53)
hoof(CX + 6, 53)

# ---- body and shoulders ----
BODY = [
    (15, 11), (16, 12), (17, 13), (18, 14), (19, 14), (20, 14), (21, 15),
    (22, 15), (23, 15), (24, 15), (25, 15), (26, 15), (27, 14), (28, 14),
    (29, 14), (30, 14), (31, 14), (32, 14), (33, 10),
]
for y, h in BODY:
    both(y, 0, h, T)
    span(y, CX - h, CX - h + 2, L)
    span(y, CX + h - 2, CX + h, D)
# belly, stepped so it is not a flat shelf
span(29, CX - 8, CX + 8, D)
span(30, CX - 9, CX + 9, D)
span(31, CX - 10, CX + 10, D)
span(32, CX - 10, CX + 10, N)
span(33, CX - 8, CX + 8, N)

# ---- front legs: long and thin, a stag's ----
FRONT = [
    (33, 11, 14), (34, 11, 14), (35, 12, 14), (36, 12, 14), (37, 12, 14),
    (38, 12, 14), (39, 12, 14), (40, 13, 14), (41, 13, 14), (42, 13, 14),
    (43, 12, 15), (44, 12, 15), (45, 13, 15), (46, 13, 14), (47, 13, 14),
    (48, 13, 14), (49, 13, 14), (50, 13, 14), (51, 13, 14), (52, 13, 14),
    (53, 13, 14), (54, 13, 14),
]
for y, a, b in FRONT:
    both(y, a, b, T)
    dot(im, CX - b, y, L)
    dot(im, CX - a, y, D)
    dot(im, CX + a, y, T)
    dot(im, CX + b, y, D)
hoof(CX - 13, 55)
hoof(CX + 14, 55)

# ---- lines: shoulder down into each leg, and muscle ticks ----
for x, y in ((11, 28), (11, 29), (11, 30), (11, 31), (11, 32), (10, 27), (10, 26),
             (10, 33), (11, 33), (12, 34), (12, 22), (13, 23), (13, 24)):
    dot(im, CX - x, y, K)
    dot(im, CX + x, y, K)
# knee creases, short
dot(im, CX - 14, 42, K); dot(im, CX + 14, 42, K)
dot(im, CX - 13, 46, K); dot(im, CX + 13, 46, K)

# ---- mane: layered shaggy locks ----
mane = [
    '.......m......',
    '......mmm.....',
    '.....mmmm.....',
    '...m.mmnm.....',
    '...mmmmnm.....',
    '..mmmmmnm.....',
    '..mmKnmmn.....',
    '.m.mKnmmm.....',
    '.mmmmKnmn.....',
    'mmmmmKnmmm....',
    '.mmKnmmmKnmmmm',
    'mmmKnmmmKnmmmm',
    '.mmmKnmmmKnmmm',
    '.mmmKnmmmKnmmm',
    'mmmmmKnmmmKnmm',
    '.nmmmKnmmmKnmm',
    '.nmmmmKnmmmKnm',
    '..nmmmmmmmmmmm',
    '...mmKnmmmKnmm',
    '...nmKnmmmKnmm',
    '....nmKnmmmKnm',
    '.....nKnmmmKnm',
    '.....nmKnmmmKn',
    '......nKnmmmKn',
    '.......nmnmmmm',
    '.........nmmmm',
    '..........nmmm',
    '...........nmm',
    '............nm',
    '.............n',
]
stamp(im, grid(mirror(mane), PAL), CX - 13, 4)
# the right side of the mane falls into shade as a block, not a speckle
for y in range(4, 34):
    for x in range(CX + 8, CX + 14):
        if px[x, y][:3] == rgba(D)[:3]:
            px[x, y] = rgba(N)

# ---- head: badger bands from the ears down through the eyes to the nose ----
head = [
    '.ww.ggwwwww',
    '.wsgggwwwww',
    '.wggggwwwww',
    'wwgggggwwww',
    'wwwggggwwww',
    'wwwgggggwww',
    'wwwgeegggww',
    'swwwggggwww',
    '.swwwggggww',
    '..swwwgggww',
    '...swwgggww',
    '...swwwggww',
    '....wwwwwgg',
    '....sKKKKKK',
    '.....wKwKwK',
    '......sssss',
]
stamp(im, grid(mirror(head), PAL), CX - 10, 0)
# right cheek falls into shade
for y in range(0, 16):
    for x in range(CX + 7, CX + 11):
        if px[x, y][:3] == rgba(W)[:3]:
            px[x, y] = rgba(S)

im = outline(im)
save(im)
