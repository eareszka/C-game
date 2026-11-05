from pix import *

D = '3b2a58'
M = '664b95'
L = 'b69cee'
P = 'fc74b4'
W = 'dcf0ff'
B = '5c94fc'
R = '94703d'
S = '583518'
K = '000000'
PAL = {'D': D, 'M': M, 'L': L, 'P': P, 'W': W, 'B': B, 'R': R, 'S': S}

im = canvas(56, 64)


def hl(y, x0, x1, c):
    rect(im, x0, y, x1 - x0 + 1, 1, c)


def line(pts, c=K):
    for x, y in pts:
        dot(im, x, y, c)


def tuft(x, top, base, c):
    # a thin spike of hair, widening to the ground
    for y in range(top, base + 1):
        w = 1 + (y - top) // 6
        hl(y, x - w // 2, x + (w - 1) // 2, c)


def leg(x, top, bottom, a, b, c):
    # thick thigh, then a long thin stilt with a knee and a small hoof
    rect(im, x, top, 1, bottom - top + 1, a)
    rect(im, x + 1, top, 2, bottom - top + 1, b)
    rect(im, x + 3, top, 1, bottom - top + 1, c)
    # thigh
    thigh = top + 9
    rect(im, x - 1, top, 1, thigh - top, a)
    rect(im, x, top, 3, thigh - top, b)
    rect(im, x + 3, top, 2, thigh - top, c)
    # knee
    k = 45
    hl(k, x - 1, x + 4, a)
    hl(k + 1, x - 1, x + 4, b)
    dot(im, x + 4, k, c)
    dot(im, x + 4, k + 1, c)
    hl(k + 2, x, x + 3, K)
    # hoof
    hl(bottom - 2, x - 1, x + 4, a)
    hl(bottom - 1, x - 1, x + 4, b)
    hl(bottom, x - 1, x + 4, c)
    rect(im, x + 2, bottom - 1, 1, 2, K)


# thin spikes of brown hair behind the legs
for x, top, c in [(4, 45, S), (6, 40, R), (15, 42, R), (16, 48, S), (26, 44, S), (27, 40, R), (38, 42, R), (37, 48, S)]:
    tuft(x, top, 59, c)

# far legs, darker
leg(19, 30, 59, M, D, D)

# tail
for x, y in [(0, 16), (1, 17), (1, 18), (2, 19), (3, 20), (4, 21), (5, 22), (6, 23)]:
    hl(y, x, x + 2, M)
    dot(im, x, y, L)
    dot(im, x + 2, y, D)

# chest behind the head, carrying the right front leg
rect(im, 36, 24, 10, 8, D)
# dewlap hanging between the tusks
rect(im, 35, 32, 7, 8, D)

# body: high hump, back sloping off to the rump
rows = {13: (19, 27), 14: (16, 30), 15: (14, 32), 16: (12, 34), 17: (11, 35), 18: (10, 36), 19: (9, 36), 20: (8, 36),
        21: (7, 36), 22: (6, 36), 23: (6, 36), 24: (6, 36), 25: (6, 36), 26: (6, 36), 27: (6, 36), 28: (6, 36),
        29: (7, 36), 30: (8, 36), 31: (10, 34)}
for y, (a, b) in rows.items():
    hl(y, a, b, M)
    hl(y, a, a + (1 if y < 24 else 0), L)
    hl(y, b - 1, b, D)
for y in range(29, 32):
    a, b = rows[y]
    hl(y, a, b, D)

# light along the top of the hump
hl(13, 19, 25, L)
hl(14, 16, 22, L)
hl(15, 14, 19, L)
hl(16, 12, 16, L)
hl(17, 11, 14, L)
hl(18, 10, 12, L)

# brown ridge of hair along the spine
for x, top in [(17, 11), (19, 8), (21, 10), (23, 7), (25, 10)]:
    rect(im, x, top, 1, 14 - top, R)
    rect(im, x + 1, top + 2, 1, 12 - top, S)

# hide lines: shoulder, haunch, wrinkles
line([(26, 17), (26, 18), (25, 19), (25, 20), (24, 21), (24, 22), (24, 23), (24, 24), (25, 25), (25, 26), (25, 27), (26, 28), (26, 29)])
line([(15, 20), (14, 21), (13, 22), (13, 23), (12, 24), (12, 25), (12, 26), (13, 27), (13, 28), (14, 29)])
line([(17, 18), (18, 18), (19, 18), (20, 19)])
line([(16, 25), (17, 25), (18, 25), (19, 26)])
for x in range(14, 19):
    dot(im, x, 31, K)
for x in range(25, 30):
    dot(im, x, 31, K)

# near legs
leg(8, 31, 59, L, M, D)
leg(30, 31, 59, L, M, D)
leg(42, 31, 59, L, M, D)

# the walrus head, ringed in black so it stands clear of the body
head = [
    ".....LLLLLLLLM.....",
    "...LLLLLLLLLLLMM...",
    "..LLLLLLLLLLLLLMMD.",
    "..LLDDDDDLLLDDDDDD.",
    "..LLDDWWDLLLDWWDDD.",
    "..LLMDDDMMMMMDDDMD.",
    ".LLMMMMMMKMMMMMMMD.",
    "LLLLLLMMMKMMLLLLMDD",
    "LMMMMMMMMKMMMMMMMDD",
    "LMKKMMMMMKMMMMKKMDD",
    "DMMMMMMMKKKMMMMMMDD",
    ".DDWWLKKKKKKKWWLDD.",
    "...WWLKPPPPPKWWL...",
    "...WWLKPPKPPKWWL...",
    "...WWLKPPKPPKWWL...",
    "...WWLKPPKPPKWWL...",
    "...WWLKKPPPKKWWL...",
    "...WWL.DKKKD.WWL...",
    "...WWL..DDD..WWL...",
    "....WWL.....WWL....",
    "....WWL.....WWL....",
    ".....WW.....WW.....",
    "......W.....W......",
]
stamp(im, outline(grid(head, PAL)), 27, 15)

# the cup on its head
cup = [
    "LLLLLWWWWWWMMMMM",
    "LKKKKKKKKKKKKKKD",
    ".LLMMMMMMMMMMDD.",
    "...LMMMMMMMMDD..",
    ".....LMMMMDD....",
    "......LMMD......",
    "......LMMD......",
    "......LMMD......",
    ".....LMMMMDD....",
]
stamp(im, grid(cup, PAL), 30, 7)

# the water gushing up out of it and falling over both sides
water = [
    "..........WWWW..........",
    "........WWWWWWWW........",
    ".....BBBWWWWWWWWBBB.....",
    "...BBWWWWBWWWWBWWWWBB...",
    "..BBWWWB..BWWB..BWWWBB..",
    ".BWWWB....BWWB....BWWWB.",
    ".BWWB.....BWWB.....BWWB.",
    ".BWW................WWB.",
    ".BWB................BWB.",
    ".BWB................BWB.",
    "..B..................B..",
]
stamp(im, grid(water, PAL), 26, 0)

im = outline(im)
save(im)
