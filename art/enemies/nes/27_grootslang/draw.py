from pix import *

W, H = 65, 58
L, M, D = 'bcbeca', '9797aa', '595965'
P, PD = 'ec8476', 'b6433d'
C, CD = 'e8e0c0', 'b2966a'

im = canvas(W, H)
px = im.load()
CX = 27  # the head mirrors round x + x' = 55


def spans(rows):
    """{y: (x0, x1)} -> set of pixels."""
    out = set()
    for y, (a, b) in rows.items():
        out |= {(x, y) for x in range(a, b + 1)}
    return out


def lay(mask):
    """Black separator round a part, only over what is already drawn."""
    for x, y in mask:
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + a, y + b)
            if q in mask or not (0 <= q[0] < W and 0 <= q[1] < H):
                continue
            if px[q][3]:
                px[q] = BLACK


def shade(mask, lx=2, ly=2, dx=3, dy=3):
    """Hard three-tone fill: lit on the upper left, dark on the lower right."""
    lay(mask)
    for x, y in mask:
        if (x, y + dy) not in mask or (x + dx, y) not in mask:
            c = D
        elif (x, y - ly) not in mask or (x - lx, y) not in mask:
            c = L
        else:
            c = M
        px[x, y] = rgba(c)


def put(x, y, c):
    px[x, y] = BLACK if c == 'K' else rgba(c)


def run(x0, x1, y, c):
    for x in range(x0, x1 + 1):
        put(x, y, c)


def plates(mask, step, off=0):
    """Belly plates along the underside of a coil, and back ridges along the top."""
    ys = {}
    for x, y in mask:
        ys.setdefault(x, []).append(y)
    for x, col in ys.items():
        bot, top = max(col), min(col)
        if (x + off) % step == 0 and bot - top >= 6:
            for y in range(bot - 3, bot):
                put(x, y, 'K')
        if (x + off + step // 2) % step < 3 and bot - top >= 7:
            put(x, top + 3, D)


# --- tail, rising behind the coils
tail = spans({
    12: (54, 59), 13: (54, 59), 14: (54, 59), 15: (54, 59), 16: (54, 59), 17: (54, 60),
    18: (54, 60), 19: (54, 60), 20: (54, 60), 21: (54, 61), 22: (54, 61), 23: (55, 61),
    24: (55, 61), 25: (55, 62), 26: (55, 62), 27: (56, 62), 28: (56, 63), 29: (56, 63),
    30: (56, 63), 31: (57, 63), 32: (57, 64), 33: (57, 64), 34: (57, 64), 35: (57, 64),
    36: (57, 64), 37: (57, 64), 38: (57, 64), 39: (57, 64), 40: (57, 64), 41: (57, 64),
    42: (57, 64), 43: (57, 64), 44: (56, 64), 45: (56, 64), 46: (56, 64), 47: (55, 64),
    48: (55, 64), 49: (54, 64), 50: (54, 63),
})
shade(tail, lx=2, ly=1, dx=2, dy=1)
# plates on the tail: short ticks from the shaded side, not full rings
for y in (18, 25, 32, 39):
    xs = sorted(x for x, yy in tail if yy == y)
    run(xs[-1] - 3, xs[-1] - 1, y, 'K')

# --- rattle, stacked beads growing downward
beads = [(0, 56, 57), (1, 55, 58), (2, 55, 58), (3, 55, 58), (4, 54, 59), (5, 54, 59), (6, 54, 59),
         (7, 54, 59), (8, 53, 60), (9, 53, 60), (10, 53, 60), (11, 53, 60), (12, 53, 60)]
for y, a, b in beads:
    run(a, b, y, C)
    put(b, y, CD)
    if b - a > 2:
        put(b - 1, y, CD)
for y, a, b in ((3, 56, 57), (7, 55, 58), (12, 54, 59)):
    run(a, b, y, 'K')
for y in (2, 6, 11):
    a, b = [(p[1], p[2]) for p in beads if p[0] == y][0]
    run(a, b, y, CD)

# --- bottom coil
low = spans({
    45: (12, 58), 46: (8, 60), 47: (5, 61), 48: (3, 62), 49: (1, 63), 50: (0, 63), 51: (0, 63),
    52: (0, 62), 53: (0, 60), 54: (1, 56), 55: (3, 50), 56: (6, 42),
})
shade(low, dy=2)
plates(low, 6)

# --- middle coil
mid = spans({
    34: (14, 50), 35: (10, 53), 36: (8, 55), 37: (6, 56), 38: (5, 57), 39: (5, 57), 40: (5, 57),
    41: (5, 57), 42: (5, 57), 43: (6, 56), 44: (8, 54), 45: (11, 50), 46: (16, 44),
})
shade(mid, dy=2)
plates(mid, 6, 3)

# --- top coil
top = spans({
    25: (18, 38), 26: (13, 43), 27: (11, 45), 28: (10, 46), 29: (9, 47), 30: (9, 47), 31: (9, 47),
    32: (9, 47), 33: (10, 46), 34: (12, 44), 35: (16, 40),
})
shade(top, dy=2)
plates(top, 6)

# --- ears: fan shaped, pink inside
ear_rows = {3: (12, 18), 4: (10, 19), 5: (9, 19), 6: (8, 19), 7: (7, 19), 8: (7, 19), 9: (7, 19),
            10: (7, 19), 11: (7, 19), 12: (7, 19), 13: (7, 19), 14: (7, 19), 15: (7, 19), 16: (7, 19),
            17: (8, 19), 18: (8, 19), 19: (9, 19), 20: (10, 19), 21: (11, 19), 22: (13, 19), 23: (15, 19)}
inner_rows = {6: (12, 17), 7: (10, 17), 8: (9, 17), 9: (9, 17), 10: (9, 17), 11: (9, 17), 12: (9, 17),
              13: (9, 17), 14: (9, 17), 15: (9, 17), 16: (9, 17), 17: (10, 17), 18: (10, 17), 19: (11, 17),
              20: (13, 17)}
for side in (0, 1):
    fx = (lambda x: x) if side == 0 else (lambda x: 55 - x)
    ear = {(fx(x), y) for x, y in spans(ear_rows)}
    shade(ear, lx=1, ly=1, dx=1, dy=1)
    for y, (a, b) in inner_rows.items():
        for x in range(a, b + 1):
            put(fx(x), y, PD if x >= 17 else P)
    # folds in the ear
    for x, y in ((12, 10), (13, 10), (14, 10), (15, 10), (16, 10), (12, 15), (13, 15), (14, 15), (15, 15), (16, 15)):
        put(fx(x), y, PD)

# --- head and trunk, one part
head = set()
for y, hw in {2: 5, 3: 7, 4: 8, 5: 9, 6: 10, 7: 10, 8: 10, 9: 10, 10: 10, 11: 10, 12: 10, 13: 10, 14: 10,
              15: 9, 16: 9, 17: 8, 18: 7, 19: 6, 20: 5, 21: 5}.items():
    head |= {(x, y) for x in range(28 - hw, 28 + hw)}
trunk = {}
for y in range(22, 46):
    hw = 4 if y < 30 else 3
    off = 0 if y < 41 else -1 if y < 44 else -2
    trunk[y] = (28 - hw + off, 27 + hw + off)
trunk[44] = (22, 28)
trunk[45] = (23, 27)
head |= spans(trunk)
shade(head, lx=2, ly=2, dx=2, dy=1)

# forehead plates
run(22, 26, 5, L)
run(21, 26, 6, L)
run(21, 26, 7, L)
run(29, 33, 5, L)
run(29, 34, 6, L)
for y in range(3, 8):
    put(27, y, D)
    put(28, y, D)
# brow, angled down to the middle
run(20, 22, 8, D)
run(23, 25, 9, D)
run(33, 35, 8, D)
run(30, 32, 9, D)
# lit skin round the eyes
run(20, 25, 10, L)
run(30, 35, 10, L)
run(20, 25, 11, L)
run(30, 35, 11, L)
run(21, 25, 12, L)
run(30, 34, 12, L)
# eyes: solid 2 px black marks
put(23, 11, 'K')
put(23, 12, 'K')
put(32, 11, 'K')
put(32, 12, 'K')
# cheek folds beside the trunk
for x, y in ((20, 14), (21, 15), (22, 16), (23, 17), (35, 14), (34, 15), (33, 16), (32, 17)):
    put(x, y, 'K')
# trunk: light stripe and ring wrinkles
for y in range(12, 42):
    xs = 26 if y < 30 else 26
    put(xs, y, L)
    put(xs + 1, y, L if y < 26 else M)
for y in range(20, 45, 3):
    xs = sorted(x for x, yy in head if yy == y)
    if y < 22:
        a, b = 24, 31
    else:
        a, b = xs[0] + 1, xs[-1] - 1
    run(a, b, y, 'K')
# nostril
put(24, 44, 'K')
put(25, 44, 'K')

# --- tusks
for side in (0, 1):
    fx = (lambda x: x) if side == 0 else (lambda x: 55 - x)
    cells = [(20, 21, 22), (21, 21, 22), (22, 20, 21), (23, 20, 21), (24, 20, 21), (25, 19, 20), (26, 19, 20),
             (27, 19, 20), (28, 19, 20), (29, 20, 20), (30, 21, 21)]
    mask = set()
    for y, a, b in cells:
        mask |= {(fx(x), y) for x in range(a, b + 1)}
    lay(mask)
    for x, y in mask:
        put(x, y, C)
    for y, a, b in cells:
        if b > a:
            put(max(fx(a), fx(b)), y, CD)

im = outline(im)
save(im)
