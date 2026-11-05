from pix import *

W, H = 204, 136
L, M, S = 'cebe82', 'b2966a', '94703d'   # sand hide
D, E = '605028', '463422'                # dark shag and far legs
P1, P2, P3 = 'f4ce80', 'c18a39', '815423'  # pyramid stone
K = '000000'


def over(im, lay):
    """Put a layer on top, inking a black line where its edge crosses what is below."""
    a, b = im.load(), lay.load()
    ink = []
    for y in range(H):
        for x in range(W):
            if b[x, y][3]:
                continue
            if not a[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H and b[nx, ny][3]:
                    ink.append((x, y))
                    break
    im.alpha_composite(lay)
    for x, y in ink:
        a[x, y] = BLACK


JAG = [0, 0, 3, 3, 3, -1, -1, 4, 4, 1, 1, 1, 5, 5, 0, 2, 2, 2, -2, -2, 3, 3]
JAG2 = [0, 0, 0, 2, 2, 2, -1, -1, 3, 3, 1, 1, 1, 4, 4, 0, 0, 2]
TOPJAG = [0, 0, 0, 1, 1, 0, 0, 2, 2, 2, 0, 1, 1]


def shade(lay, top=2, bot=9, right=4, jag=True):
    """Hard body shading: lit along the top and left, dark along the bottom and right.
    The edge of the shade is toothed, like the fur it falls on."""
    src = lay.copy().load()
    px = lay.load()

    def solid(x, y):
        return 0 <= x < W and 0 <= y < H and src[x, y][3]
    for y in range(H):
        for x in range(W):
            if not src[x, y][3]:
                continue
            b = bot + (JAG[x % len(JAG)] if jag else 0)
            r = right + (JAG2[y % len(JAG2)] if jag else 0)
            t = top + (TOPJAG[x % len(TOPJAG)] if jag else 0)
            if any(not solid(x, y + k) for k in range(1, b + 1)) or any(not solid(x + k, y) for k in range(1, r + 1)):
                px[x, y] = rgba(S)
            elif any(not solid(x, y - k) for k in range(1, t + 1)) or not solid(x - 1, y):
                px[x, y] = rgba(L)


def line(im, pts, colour=K):
    ImageDraw.Draw(im).line(pts, fill=rgba(colour), width=1)


im = canvas(W, H)

# ---- far legs, in the dark hide
far = canvas(W, H)
poly(far, [(13, 88), (34, 88), (32, 108), (28, 116), (29, 124), (33, 131), (10, 131), (13, 122), (16, 112), (15, 100)], D)
poly(far, [(124, 90), (146, 88), (145, 104), (141, 114), (142, 124), (149, 131), (124, 131), (127, 122), (127, 110)], D)
rect(far, 24, 92, 6, 22, E)
rect(far, 136, 92, 6, 22, E)
rect(far, 10, 128, 23, 3, E)
rect(far, 124, 128, 25, 3, E)
for x in (16, 23, 131, 139):
    rect(far, x, 126, 1, 5, K)
over(im, far)

# ---- shag under the neck, behind the body
neckshag = canvas(W, H)
for x, w, y2 in ((148, 3, 104), (151, 3, 107), (154, 4, 103), (158, 3, 106), (161, 3, 104), (164, 3, 101), (167, 3, 99)):
    rect(neckshag, x, 90, w, y2 - 90 - 1, D)
    rect(neckshag, x + 1, y2 - 1, w - 2 if w > 2 else 1, 1, D)
    rect(neckshag, x + w - 1, 90, 1, y2 - 92, E)
over(im, neckshag)

# ---- tail
tail = canvas(W, H)
poly(tail, [(16, 72), (21, 76), (15, 88), (10, 100), (7, 112), (5, 118), (2, 118), (3, 106), (6, 94), (10, 82)], M)
shade(tail, top=1, bot=2, right=2, jag=False)
over(im, tail)

# ---- the body, neck and near legs are one mass
body = canvas(W, H)
poly(body, [(14, 80), (20, 72), (30, 63), (42, 58), (126, 58), (136, 68), (146, 76), (156, 82), (165, 84),
            (171, 79), (175, 71), (177, 60), (178, 52), (192, 52), (192, 62), (191, 72), (186, 82), (178, 91),
            (168, 97), (156, 101), (132, 102), (50, 102), (32, 102), (16, 96)], M)
# near hind leg
poly(body, [(26, 88), (58, 88), (56, 104), (52, 114), (52, 122), (58, 131), (31, 131), (34, 122), (35, 112), (30, 102)], M)
# near fore leg
poly(body, [(102, 88), (130, 88), (129, 104), (125, 114), (125, 122), (132, 131), (104, 131), (107, 122), (108, 112), (104, 102)], M)
shade(body)
over(im, body)

# ---- the shag fringe along the belly
fringe = canvas(W, H)
strands = [(53, 4, 96, 110), (57, 3, 95, 106), (60, 4, 97, 113), (64, 3, 95, 108), (67, 4, 96, 111), (71, 3, 95, 106),
           (74, 5, 97, 115), (79, 3, 96, 108), (82, 4, 95, 112), (86, 3, 97, 107), (89, 4, 95, 114), (93, 3, 96, 109),
           (96, 4, 95, 112), (100, 3, 97, 107), (103, 3, 96, 110)]
for i, (x, w, y1, y2) in enumerate(strands):
    rect(fringe, x, y1, w, y2 - y1 - 2, D)
    rect(fringe, x + 1, y2 - 2, max(w - 2, 1), 2, D)
    rect(fringe, x + w - 1, y1 + 3, 1, y2 - y1 - 6, E)
    if i % 2:
        rect(fringe, x, y1 + 5, w, y2 - y1 - 8, E)
over(im, fringe)

# ---- pyramid: courses of brick, stepped like a real stack
AX, AY = 80, 1
BASE = 70
pyr = canvas(W, H)
COURSE = 5
row = 0
y = AY
ridge_cols = []
while y < BASE:
    yb = min(y + COURSE - 1, BASE - 1)
    d = yb - AY + 1
    left = AX - round(d * 0.70)
    right = AX + round(d * 0.82)
    ridge = AX + round(d * 0.38)
    rect(pyr, left, y, ridge - left + 1, COURSE, P1)
    rect(pyr, ridge + 1, y, right - ridge, COURSE, P2)
    # the course line under the bricks
    rect(pyr, left, yb, ridge - left + 1, 1, P3)
    rect(pyr, ridge + 1, yb, right - ridge, 1, K)
    # joints
    off = 3 if row % 2 else 0
    for idx, jx in enumerate(range(AX - 91 + off, AX + 91, 7)):
        # a few whole bricks are weathered, cut exactly to their joints
        tint = (row * 7 + idx * 13 + row * idx) % 9 == 0
        if tint and row > 2:
            lx, rx = max(jx + 1, left), min(jx + 6, ridge - 1)
            if rx >= lx:
                rect(pyr, lx, y, rx - lx + 1, COURSE - 1, P2)
            lx, rx = max(jx + 1, ridge + 1), min(jx + 6, right)
            if rx >= lx:
                rect(pyr, lx, y, rx - lx + 1, COURSE - 1, P3)
        if left + 1 < jx < ridge:
            rect(pyr, jx, y, 1, COURSE - 1, P3)
        elif ridge + 1 < jx < right:
            rect(pyr, jx, y, 1, COURSE - 1, P3)
    # the ridge between the two faces
    rect(pyr, ridge, y, 1, COURSE, K)
    row += 1
    y += COURSE

# the niche up high
rect(pyr, 67, 36, 14, 1, P3)
rect(pyr, 66, 37, 16, 4, K)
rect(pyr, 68, 38, 12, 2, E)
rect(pyr, 64, 41, 20, 1, P2)
# the doorway low down, with a heavy lintel
rect(pyr, 58, 50, 24, 1, K)
rect(pyr, 58, 51, 24, 3, P1)
rect(pyr, 58, 54, 24, 1, K)
rect(pyr, 61, 55, 18, 13, K)
rect(pyr, 62, 56, 16, 12, E)
rect(pyr, 62, 56, 16, 3, D)
rect(pyr, 72, 59, 6, 9, D)
# cracks
line(pyr, [(84, 8), (82, 12), (85, 18), (83, 22), (87, 28), (85, 34), (88, 40)])
line(pyr, [(62, 30), (65, 35), (63, 40), (66, 46)])
line(pyr, [(109, 34), (106, 40), (110, 46), (108, 52), (112, 58), (110, 64)])
line(pyr, [(50, 46), (53, 50), (51, 55), (54, 60)])
over(im, pyr)

# ---- ragged sand fur over the foot of the pyramid
fur = canvas(W, H)
x = 26
hs = [3, 6, 2, 8, 4, 1, 7, 3, 5, 9, 2, 6, 3, 7, 1, 5, 8, 3, 6, 2, 4, 9, 3, 6, 1, 7, 4]
ws = [4, 3, 5, 3, 4, 5, 3, 4, 3, 3, 5, 4, 3, 3, 5, 4, 3, 4, 3, 5, 4, 3, 4, 3, 5, 3, 4]
i = 0
while x < 134:
    h = hs[i % len(hs)]
    w = ws[i % len(ws)]
    fy = 70 - h
    if x < 34:
        fy = max(fy, 66)
    if x > 124:
        fy = max(fy, 66)
    low = 73 + (h * 3) % 5           # the lower edge is ragged too
    rect(im, x, 72, w, low - 72 + 3, S)   # shadow the fur throws on the hide
    rect(fur, x, fy, w, low - fy, M)
    rect(fur, x, fy, w - 1, 2, L)
    rect(fur, x + w - 1, fy + 1, 1, 3, S)
    rect(fur, x, low - 2, w - 1, 1, S)
    x += w
    i += 1
over(im, fur)

# ---- line work on the hide
haunch = [(50, 75), (54, 78), (57, 84), (58, 92), (56, 99)]
line(im, [(p[0] + 1, p[1]) for p in haunch], S)
line(im, [(p[0] + 2, p[1]) for p in haunch], S)
line(im, haunch)
shoulder = [(108, 74), (103, 79), (100, 86), (100, 93), (102, 99)]
line(im, [(p[0] - 1, p[1]) for p in shoulder], S)
line(im, [(p[0] - 2, p[1]) for p in shoulder], S)
line(im, shoulder)
# ribs
for rx, top in ((66, 82), (75, 84), (84, 82), (92, 85)):
    line(im, [(rx + 2, top), (rx, top + 4), (rx, top + 9), (rx + 1, top + 11)], S)
    line(im, [(rx + 3, top), (rx + 1, top + 4), (rx + 1, top + 9)], S)
    line(im, [(rx + 2, top - 2), (rx + 1, top + 3)])
# tufts of hair, each a small lit tooth over a dark one
for tx, ty in ((38, 82), (46, 88), (34, 92), (42, 96), (62, 80), (72, 82), (80, 80), (90, 81), (112, 84), (120, 90),
               (110, 96), (124, 96), (140, 78), (150, 84), (162, 88), (181, 62), (184, 76), (172, 84), (36, 100),
               (46, 104), (116, 104)):
    rect(im, tx, ty, 3, 1, S)
    rect(im, tx + 1, ty + 1, 2, 1, S)
    rect(im, tx, ty - 1, 2, 1, L)
    dot(im, tx + 3, ty + 1, K)
# wrinkles on the rump and side
line(im, [(26, 79), (30, 76), (36, 75)])
line(im, [(26, 80), (30, 77), (36, 76)], S)
line(im, [(21, 90), (25, 87), (28, 87)])
line(im, [(21, 91), (25, 88), (28, 88)], S)
line(im, [(116, 80), (122, 79), (127, 82)])
line(im, [(116, 81), (122, 80), (127, 83)], S)
# neck folds
for pts in ([(176, 69), (182, 72), (190, 70)], [(173, 76), (178, 80), (186, 80)], [(166, 86), (171, 88), (178, 88)],
            [(154, 86), (157, 91), (162, 94)], [(140, 82), (144, 88), (148, 94)], [(130, 78), (133, 85), (136, 92)]):
    line(im, pts)
    line(im, [(p[0], p[1] + 1) for p in pts], S)
# knees and ankles
for pts in ([(37, 110), (42, 112), (49, 110)], [(110, 110), (115, 112), (122, 110)]):
    line(im, pts)
    line(im, [(p[0], p[1] + 1) for p in pts], L)
for pts in ([(36, 121), (42, 123), (50, 121)], [(109, 121), (115, 123), (123, 121)]):
    line(im, pts)
# toes
for x in (38, 46, 111, 119):
    rect(im, x, 126, 1, 5, K)
for x, w in ((33, 4), (40, 5), (48, 7), (106, 4), (113, 5), (121, 8)):
    rect(im, x, 129, w, 2, L)

# ---- head, turned to the player
HEAD = [
    "........hh............mm......",
    ".......hmmm..........mmmss....",
    ".......hmdms........mmdmss....",
    ".......hmdms........mmdss.....",
    ".......hmdmm.......mmmdms.....",
    "........hmmmhhhhhhhmmmmss.....",
    "........hhmmmmmmmmmmmmmss.....",
    ".......hhmmmmmmmmmmmmmmmss....",
    "......hhmmmsssmmmmmsssmmmss...",
    "......hmmmmmmmmmmmmmmmmmmss...",
    "......hmmmmKmmmmmmmmKmmmmss...",
    "......hmmmmKmmmmmmmmKmmmmss...",
    ".....hhmmmmmmmmmmmmmmmmmmss...",
    "....hhmmmmmmmsmmmmmmmmmmmss...",
    "...hhmmmmmmmmsmmmmmmmmmmsss...",
    "..hhmmmmmmmmsmmmmmmKmmmmss....",
    ".hhmmmmmmmmmmmmmmmmmKmmsss....",
    ".hmmmmmmmmmmmmmmmmmmKmss.....",
    "hhmKKmmmmmKKmmmmmmmmmmsss.....",
    "hmmmmmmmmmmmmmmmmmmmmmss......",
    "hmmmmmmmmmmmmmmmmmmmmsss......",
    "mKKKKKKKKKKKKKKKmmmmsss.......",
    ".mssssssssssssssKmmss.........",
    "..sssssssssssssmmsss..........",
    "....ssssssssssss..............",
]
head = canvas(W, H)
stamp(head, grid(HEAD, {'h': L, 'm': M, 's': S, 'd': D}), 166, 34)
over(im, head)

im = outline(im)
save(im)
