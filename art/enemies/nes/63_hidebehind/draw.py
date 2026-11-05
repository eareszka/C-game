from pix import *

W, H = 47, 44
CX = 23
DK, MD, LT = '3c2412', '583518', '815423'
IV, IS = 'e8e0c0', 'b29e5c'
BK = '000000'

im = canvas(W, H)


def px(x, y, c):
    dot(im, x, y, c)


# ---- claws: a clear fan of five hooks, written for the left hand and mirrored
CLAWS = [
    [(3, 11), (2, 11), (1, 12), (0, 13), (0, 14), (0, 15), (1, 16)],
    [(3, 9), (2, 8), (1, 7), (0, 6), (0, 5), (0, 4), (1, 3)],
    [(4, 8), (4, 7), (3, 6), (3, 5), (3, 4), (3, 3), (3, 2), (4, 1)],
    [(6, 8), (6, 7), (6, 6), (6, 5), (6, 4), (7, 3), (7, 2), (7, 1), (8, 0), (9, 0)],
    [(8, 8), (9, 7), (10, 6), (10, 5), (11, 4), (12, 4), (13, 5)],
]
for run in CLAWS:
    for x, y in run:
        px(x, y, IV)
        px(2 * CX - x, y, IV)
    # the first two pixels carry a shaded side, away from the upper left light
    for x, y in run[:2]:
        for xx in (x + 1, 2 * CX - x + 1):
            if xx < W and im.getpixel((xx, y))[3] == 0:
                px(xx, y, IS)

# ---- arms: elbow low and out, forearm straight up to the hand
for side in (0, 1):
    def m(x):
        return 2 * CX - x if side else x
    top, mid, low = (MD, DK, DK) if side else (LT, MD, DK)
    for i, x in enumerate(range(16, 6, -1)):
        y = 18 + (i + 1) // 3
        px(m(x), y, top)
        px(m(x), y + 1, mid)
        px(m(x), y + 2, mid)
        px(m(x), y + 3, low)
    for y in range(12, 23):
        px(m(5), y, top)
        px(m(6), y, mid)
        px(m(7), y, mid)
        px(m(8), y, low)
    px(m(5), 22, DK)
    # shaggy tufts on the outer forearm and under the upper arm
    for y in (14, 17, 20):
        px(m(4), y, top)
    for x, y in ((8, 25), (11, 24), (14, 23), (9, 25), (12, 24)):
        px(m(x), y, DK)
    # hand
    for y in range(9, 13):
        for x in range(4, 10):
            px(m(x), y, mid)
    for x in range(5, 9):
        px(m(x), 9, top)
    px(m(4), 9, None)
    px(m(9), 9, None)
    px(m(4), 12, None)
    px(m(9), 12, None)
    px(m(9), 11, low)
    px(m(8), 12, low)

# ---- the point of the cone, with small steps of fur
CONEL = [0, 0, 1, 1, 2, 1, 2, 3, 2, 3, 4, 4, 8, 7]
CONER = [0, 0, 0, 1, 1, 2, 2, 2, 3, 3, 4, 5, 8, 7]
for y in range(14):
    hl, hr = CONEL[y], CONER[y]
    for x in range(CX - hl, CX + hr + 1):
        u = x - CX
        if hl and u <= -hl + 1:
            c = LT
        elif hr and u >= hr - 1:
            c = DK
        else:
            c = MD
        px(x, y, c)
# the brim catches light on the left and hangs in points
for x in range(CX - 8, CX - 2):
    px(x, 12, LT)
for x in (CX - 8, CX - 5, CX + 6, CX + 8):
    px(x, 14, DK if x > CX else MD)


# ---- the fur cone: a saw edge whose locks flare out and cut back
def edge(y, phase):
    base = 6 + (y - 14) * 0.3
    return int(base) + (y + phase) % 4


PEAKS = [(-16, 39), (-12, 43), (-8, 41), (-4, 43), (0, 42), (4, 43), (8, 41), (12, 43), (16, 39)]


def bottom(dx):
    return max(37, max(p - 2 * abs(dx - q) for q, p in PEAKS))


CENTRE = {15: (0, 1), 16: (-1, 1), 17: (-1, 2), 18: (-2, 1), 19: (-1, 2), 20: (-2, 1), 21: (-3, 2), 22: (-2, 2),
          23: (-3, 1), 24: (-4, 2), 25: (-3, 3), 26: (-4, 2), 27: (-5, 2), 28: (-4, 3), 29: (-5, 2), 30: (-6, 3),
          31: (-5, 3), 32: (-6, 2), 33: (-7, 3), 34: (-6, 4), 35: (-7, 3), 36: (-8, 3), 37: (-7, 4), 38: (-8, 4),
          39: (-8, 3), 40: (-8, 4), 41: (-8, 4), 42: (-4, 4), 43: (-4, 4)}

for y in range(14, H):
    hl, hr = edge(y, 0), edge(y, 2)
    for dx in range(-hl, hr + 1):
        if y > bottom(dx) or not 0 <= CX + dx < W:
            continue
        a, b = CENTRE.get(y, (99, -99))
        if a <= dx <= b:
            c = LT
        elif dx >= hr * 0.5 + (y % 4) - 1:
            c = DK
        else:
            c = MD
        px(CX + dx, y, c)

# ---- black lines inside
# the shadow under the brim, with two small marks in it
for x in range(CX - 5, CX + 6):
    px(x, 14, BK)
for x in range(CX - 4, CX + 5):
    px(x, 15, BK)
px(CX - 2, 14, IV)
px(CX + 2, 14, IV)

# lock tips: a long stroke down to a point and a short stroke back up
TIP = [(0, 0), (0, 1), (1, 2), (2, 3), (3, 2), (4, 1)]
TIPS = [(-6, 18), (2, 19), (-9, 24), (-2, 23), (5, 25), (-13, 30), (-6, 29), (1, 30), (8, 31),
        (-11, 35), (-3, 35), (5, 36), (11, 36)]
for dx, y in TIPS:
    for a, b in TIP:
        x = CX + dx + a
        if im.getpixel((x, y + b))[3]:
            px(x, y + b, BK)

# the line between each arm and the side of the cone
for dx, y in ((-7, 20), (-8, 21), (-8, 22), (7, 20), (8, 21), (8, 22)):
    px(CX + dx, y, BK)

im = outline(im)
save(im)
