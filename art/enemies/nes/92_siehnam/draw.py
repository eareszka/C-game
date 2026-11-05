from pix import *

W = 'fcfcfc'   # skull
A = 'bcbeca'   # antler light, skull shade
B = '848694'   # antler shade
R = 'b70000'   # blood
C = '792727'   # chest lit, blood shade
D = '531b1c'   # chest, hooves
T = '967448'   # hide
S = '633e1b'   # hide shade
K = '000000'

im = canvas(67, 68)


def line(a, b, thick, colour, dx=0, dy=0):
    (x0, y0), (x1, y1) = a, b
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(steps + 1):
        x = round(x0 + (x1 - x0) * i / steps) + dx
        y = round(y0 + (y1 - y0) * i / steps) + dy
        rect(im, x, y, thick, thick, colour)


# ---- antlers: (from, to, thickness), left side, mirrored for the right
TINES = [
    ((30, 25), (22, 21), 3),   # beam, root
    ((22, 21), (9, 20), 3),    # beam, out to the bleeding end
    ((9, 20), (5, 16), 2),
    ((5, 16), (1, 12), 1),     # end tip
    ((16, 20), (13, 13), 2),   # great tine
    ((13, 13), (10, 7), 2),
    ((10, 7), (8, 1), 1),
    ((11, 8), (6, 8), 1),      # side prong off the great tine
    ((6, 8), (3, 6), 1),
    ((14, 14), (19, 9), 1),    # forward prong off the great tine
    ((19, 9), (20, 5), 1),
    ((22, 20), (24, 15), 2),   # brow tine
    ((24, 15), (26, 11), 1),
    ((7, 18), (6, 12), 1),     # short prong near the end
]


def flip(p):
    return (65 - p[0], p[1])


for a, b, t in TINES:
    line(a, b, t, B, 1, 1)
    line(flip(a), flip(b), t, B, 1 - t + 1 - 1, 1)
for a, b, t in TINES:
    line(a, b, t, A)
    line(flip(a), flip(b), t, A, 1 - t)

# ---- hide: far legs first
rect(im, 47, 46, 3, 8, S)           # far hind leg: thigh
rect(im, 46, 54, 3, 4, S)           # hock
rect(im, 46, 58, 2, 6, S)           # cannon
rect(im, 45, 64, 4, 2, D)
rect(im, 39, 50, 3, 13, S)          # far foreleg
rect(im, 39, 63, 2, 1, S)
rect(im, 38, 64, 4, 2, D)

# barrel and rump: a sloping back, a tucked belly, a high haunch
poly(im, [(42, 31), (49, 32), (54, 35), (58, 40), (60, 45), (60, 49), (56, 50), (50, 48), (44, 49), (40, 46)], T)
# near hind leg: broad thigh, hock kicked back, thin cannon
poly(im, [(52, 44), (60, 45), (61, 50), (60, 55), (58, 55), (54, 52)], T)
poly(im, [(58, 54), (61, 54), (60, 58), (59, 63), (57, 63), (57, 59)], T)
rect(im, 56, 64, 5, 2, D)
# shade: under the belly, down the rump, back of the leg
for x, y, n in ((43, 47, 3), (46, 46, 4), (50, 47, 3), (53, 48, 2), (42, 45, 2)):
    rect(im, x, y, n, 2, S)
for x, y, h in ((60, 45, 5), (59, 42, 3), (58, 40, 2), (60, 50, 5), (60, 55, 2), (59, 57, 4), (58, 61, 3)):
    rect(im, x, y, 1, h, S)
# coat tufts: short stepped marks that follow the body
for x, y in ((49, 36), (53, 39), (47, 41), (55, 43)):
    rect(im, x, y, 2, 1, S)
    dot(im, x + 2, y + 1, S)
# haunch line
for p in ((52, 42), (51, 43), (51, 44), (51, 45), (52, 46), (53, 47), (54, 48), (55, 49)):
    dot(im, p[0], p[1], K)

# near foreleg and shoulder on the left of the chest
poly(im, [(24, 42), (30, 42), (30, 54), (24, 50)], T)
rect(im, 26, 54, 4, 2, T)
rect(im, 27, 56, 3, 8, T)
rect(im, 29, 52, 1, 12, S)
rect(im, 26, 64, 5, 2, D)

# ---- dark red chest mane
oval(im, 23, 27, 23, 25, D)
# tattered hem: strands of different lengths
for x, bottom in ((24, 47), (25, 50), (27, 53), (29, 51), (31, 56), (33, 53), (35, 58), (37, 52),
                  (39, 55), (41, 51), (43, 49), (44, 47)):
    rect(im, x, 42, 2, bottom - 42, D)
# lit tufts on the upper left, each ending in a point
for x, y, h in ((26, 36, 6), (29, 39, 7), (32, 38, 8), (27, 44, 5), (35, 41, 6), (31, 47, 5), (38, 39, 5)):
    rect(im, x, y, 2, h, C)
    dot(im, x, y + h, C)
# fur partings, black
for x, y, h in ((25, 41, 6), (28, 37, 5), (31, 40, 6), (34, 38, 6), (37, 42, 6), (40, 37, 7), (43, 40, 5),
                (29, 46, 4), (33, 48, 4), (39, 46, 5), (35, 51, 4), (41, 45, 4)):
    rect(im, x, y, 1, h, K)
# chest blood on the lit fur
for x, y, h in ((27, 39, 2), (33, 41, 3), (36, 46, 2)):
    rect(im, x, y, 1, h, R)

# parting line between the mane and the barrel
for p in ((46, 33), (46, 34), (47, 35), (47, 36), (47, 37), (47, 38), (47, 39), (47, 40), (47, 41),
          (46, 42), (46, 43), (46, 44), (45, 45), (45, 46), (44, 47), (43, 48)):
    dot(im, p[0], p[1], K)

# ---- ears either side of the skull
poly(im, [(22, 25), (27, 26), (28, 29), (24, 29)], T)
rect(im, 24, 28, 4, 1, S)
poly(im, [(38, 26), (43, 25), (42, 29), (38, 29)], T)
rect(im, 38, 28, 4, 1, S)

# ---- skull
PAL = {'w': W, 'a': A, 'b': B}
SKULL = [
    '...wwwww...',
    '.wwwwwwwwa.',
    'wwwwwwwwwwa',
    'wwwwwwwwwwa',
    'wKKwwwwKKwa',
    'wwwwwwwwwaa',
    '.wwwwwwwaa.',
    '.wwwKwwwaa.',
    '..wwKwwaa..',
    '..wwwwwaa..',
    '..wwwwwaa..',
    '...wwwaa...',
    '...KwKaa...',
    '...wwwab...',
    '....waa....',
]
stamp(im, grid(SKULL, PAL), 28, 23)

# ---- blood at the beam ends
rect(im, 7, 20, 5, 3, R)
rect(im, 8, 19, 3, 1, R)
rect(im, 8, 22, 3, 1, C)
rect(im, 8, 23, 1, 7, R)
rect(im, 8, 30, 1, 2, C)
rect(im, 11, 23, 1, 3, R)
rect(im, 11, 26, 1, 2, C)

rect(im, 54, 20, 5, 3, R)
rect(im, 55, 19, 3, 1, R)
rect(im, 55, 22, 3, 1, C)
rect(im, 57, 23, 1, 8, R)
rect(im, 57, 31, 1, 2, C)
rect(im, 54, 23, 1, 3, R)
rect(im, 54, 26, 1, 1, C)

im = outline(im)
save(im)
