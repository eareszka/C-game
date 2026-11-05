from pix import *

L = '967448'   # lit fur
M = '764c20'   # main fur
D = '583518'   # shade fur
S = 'd7a175'   # muzzle
T = 'b2966a'   # muzzle / claw shade
C = 'e8e0c0'   # claw
E = 'ec8476'   # eye
K = '000000'

W, H = 92, 94
CX = 45
im = canvas(W, H)


def fl(pts):
    return [(2 * CX - x, y) for x, y in pts]


def part(pts, colour):
    """Filled polygon with a black line round it."""
    tmp = canvas(W, H)
    poly(tmp, pts, colour)
    stamp(im, outline(tmp).crop((1, 1, W + 1, H + 1)), 0, 0)


def line(pts, colour):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i // n if x1 >= x0 else x0 - (x0 - x1) * i // n
            y = y0 + (y1 - y0) * i // n if y1 >= y0 else y0 - (y0 - y1) * i // n
            if 0 <= x < W and 0 <= y < H:
                dot(im, x, y, colour)


def saw(x0, x1, ys, step=4, depth=3, colour=K):
    """Shaggy fur edge: teeth hanging from a line given as {x: y} keys."""
    keys = sorted(ys)

    def base(x):
        for a, b in zip(keys, keys[1:]):
            if a <= x <= b:
                return ys[a] + (ys[b] - ys[a]) * (x - a) // (b - a)
        return ys[keys[-1]]
    pts = []
    x = x0
    up = True
    while x <= x1:
        pts.append((x, base(x) + (0 if up else depth)))
        up = not up
        x += step
    line(pts, colour)


def both(pts, colour):
    poly(im, pts, colour)
    poly(im, fl(pts), colour)


# ---- hind feet, behind everything
hind = [(5, 58), (15, 58), (17, 74), (15, 78), (4, 78), (3, 74)]
part(hind, D)
part(fl(hind), D)
for hx in (5, 8, 11, 14):
    rect(im, hx, 78, 2, 2, T)
    rect(im, 2 * CX - hx - 1, 78, 2, 2, T)
line([(8, 74), (8, 77)], K)
line([(11, 74), (11, 77)], K)
line([(82, 74), (82, 77)], K)
line([(79, 74), (79, 77)], K)
line([(6, 60), (6, 72)], M)

# ---- great humped body
side = [(45, 1), (38, 1), (37, 2), (31, 2), (30, 4), (26, 5), (26, 8), (22, 9),
        (22, 13), (19, 14), (18, 20), (15, 21), (15, 26), (17, 28), (11, 29), (10, 33), (7, 34),
        (7, 40), (4, 41), (5, 48), (3, 49), (5, 56), (4, 57), (7, 64), (6, 66), (10, 70),
        (14, 72), (20, 74), (45, 76)]
body = side + fl(side)[::-1]
poly(im, body, M)


def on(pts, colour, under=M):
    """Filled polygon that only lands on one existing colour, so it can't change the silhouette."""
    tmp = canvas(W, H)
    poly(tmp, pts, colour)
    src, dst, want = tmp.load(), im.load(), rgba(under)
    for y in range(H):
        for x in range(W):
            if src[x, y][3] and dst[x, y] == want:
                dst[x, y] = src[x, y]


# light falls across the upper left of the hump
lit = [(45, 0), (20, 0), (0, 30), (0, 52), (8, 52), (9, 44), (12, 46), (13, 37), (16, 39), (18, 30), (22, 32),
       (24, 24), (28, 25), (31, 17), (35, 19), (38, 12), (42, 14), (45, 9), (50, 11), (54, 6), (57, 7), (60, 0)]
on(lit, L)

# shade down the right flank and under the belly
shade = [(70, 12), (91, 30), (91, 70), (80, 74), (45, 78), (40, 76),
         (40, 66), (54, 64), (60, 70), (66, 66), (70, 70), (73, 62), (76, 64), (77, 54),
         (80, 55), (80, 45), (82, 44), (78, 36), (75, 37), (73, 28), (70, 29), (68, 21), (66, 22)]
on(shade, D)
shade2 = [(0, 58), (7, 64), (10, 70), (14, 72), (20, 76), (18, 66), (14, 68), (12, 60), (9, 63)]
on(shade2, D)


def strokes(rows, region=None):
    """Rows of short fur locks, each a clean 3 px step, in the next tone of whatever they land on."""
    px = im.load()
    swap = {rgba(L): M, rgba(M): None, rgba(D): M}
    for row in rows:
        for i, (x, y) in enumerate(row):
            s = -1 if x < CX else 1
            n = 3 + i % 2
            cells = [(x, y)] + [(x + s * (k // 2 + 1) * (k % 2 == 1) + s * (k // 2) * (k % 2 == 0), y + k) for k in range(1, n)]
            under = [px[a, b] if 0 <= a < W and 0 <= b < H else None for a, b in cells]
            if any(u not in swap for u in under):
                continue
            base = under[0]
            if any(u != base for u in under):
                continue
            c = swap[base] or (L if x < CX else D)
            for a, b in cells:
                dot(im, a, b, c)


def arc(y0, dip, half, step=6, shift=0):
    return [(CX + dx + shift, y0 + dip * dx * dx // (half * half)) for dx in range(-half, half + 1, step)]

# hump ridge lines
saw(21, 69, {21: 19, 33: 13, 45: 11, 57: 13, 69: 19}, step=4, depth=3)
saw(11, 25, {11: 37, 18: 30, 25: 26}, step=4, depth=3)
saw(65, 79, {65: 26, 72: 30, 79: 37}, step=4, depth=3)
saw(30, 60, {30: 8, 45: 6, 60: 8}, step=5, depth=2)
line([(38, 22), (36, 25)], D)
line([(52, 22), (54, 25)], K)
line([(30, 16), (28, 19)], D)
line([(60, 16), (62, 19)], K)

# flank locks
for pts in ([(10, 44), (12, 49), (14, 46)], [(8, 56), (10, 61), (12, 57)],
            [(17, 41), (19, 45), (21, 42)], [(80, 44), (78, 49), (76, 46)],
            [(82, 56), (80, 61), (78, 57)], [(73, 41), (71, 45), (69, 42)]):
    line(pts, K)

# fur layers across hump and shoulders, following the body
strokes([arc(4, 4, 18, 6, 2), arc(16, 10, 30, 6), arc(21, 14, 36, 6, 3), arc(30, 18, 42, 6),
         arc(38, 18, 42, 6, 3), arc(48, 12, 42, 6), arc(57, 8, 42, 6, 3)])

# ---- belly between the forelegs
poly(im, [(34, 58), (56, 58), (58, 72), (54, 76), (50, 73), (45, 77), (40, 73), (36, 76), (32, 72)], D)
line([(38, 66), (40, 71), (43, 67), (45, 72), (47, 67), (50, 71), (52, 66)], K)

# ---- forelegs
leg = [(17, 44), (33, 46), (38, 56), (38, 76), (40, 80), (39, 84), (12, 84), (11, 80), (15, 74), (14, 60)]
part(leg, M)
legr = fl(leg)
part(legr, M)

# left leg light / shade
poly(im, [(16, 46), (22, 47), (20, 56), (19, 66), (18, 74), (14, 78), (15, 60)], L)
poly(im, [(33, 58), (37, 58), (37, 76), (38, 78), (33, 78), (35, 70)], D)
# right leg light / shade
poly(im, [(55, 58), (59, 58), (58, 66), (59, 76), (54, 76)], L)
poly(im, [(68, 47), (73, 45), (75, 60), (75, 74), (78, 79), (72, 79), (71, 70), (70, 58)], D)

# leg fur locks
for ox in (0, 1):
    for pts in ([(21, 58), (23, 63), (25, 59)], [(27, 66), (29, 71), (31, 67)],
                [(20, 70), (22, 75), (24, 71)]):
        p = pts if ox == 0 else fl(pts)
        line(p, K)

strokes([[(x, y) for x in (17, 24, 31, 59, 66, 73)] for y in (50, 62)] +
        [[(x, y) for x in (20, 28, 35, 55, 62, 70)] for y in (55, 70)])

# ---- paws and claws
for flip in (False, True):
    # big toes
    for tx in (12, 17, 22, 27, 32):
        toe = [(tx, 79), (tx + 4, 79), (tx + 5, 81), (tx + 5, 84), (tx, 84), (tx - 1, 82)]
        toe = fl(toe) if flip else toe
        part(toe, L if (tx < 22) != flip else M)
    for tx in (13, 18, 23, 28, 33):
        cx = 2 * CX - tx - 2 if flip else tx
        rect(im, cx, 85, 3, 2, C)
        rect(im, cx + 1, 87, 2, 1, T)
        rect(im, cx + 1, 88, 1, 2, C)
        dot(im, cx + 2, 85, T)
        dot(im, cx + 2, 86, T)

# ---- ears
for flip in (False, True):
    ear = [(22, 23), (24, 19), (28, 17), (33, 18), (36, 22), (36, 30), (25, 33), (21, 29)]
    part(fl(ear) if flip else ear, L if not flip else M)
    if flip:
        line(fl([(35, 21), (33, 19), (28, 18), (25, 20), (23, 23)]), L)
    inner = [(25, 25), (28, 21), (32, 22), (34, 29), (27, 31)]
    poly(im, fl(inner) if flip else inner, D)
    line(fl([(28, 25), (30, 28)]) if flip else [(28, 25), (30, 28)], K)

# ---- head
head = [(45, 25), (36, 25), (31, 27), (28, 30), (26, 35), (25, 41), (24, 46), (22, 47), (25, 51),
        (23, 53), (27, 57), (26, 59), (31, 62), (32, 64), (37, 67), (45, 69)]
part(head + fl(head)[::-1], M)

# forehead light on the left, cheek shade on the right
poly(im, [(44, 26), (36, 26), (32, 28), (29, 31), (27, 36), (26, 42), (25, 47), (28, 45), (30, 38),
          (34, 36), (38, 40), (42, 36), (44, 32)], L)
poly(im, [(66, 41), (67, 46), (68, 47), (65, 51), (67, 53), (63, 57), (64, 59), (59, 62), (58, 64),
          (53, 67), (50, 67), (53, 63), (57, 59), (60, 53), (62, 47)], D)
poly(im, [(27, 53), (30, 58), (33, 62), (37, 65), (38, 62), (33, 57), (30, 52)], D)

# brow crease and head line work
line([(45, 28), (45, 33)], D)
line([(38, 30), (40, 34)], K)
line([(52, 30), (50, 34)], K)
line([(29, 49), (31, 53), (33, 50)], K)
line([(61, 49), (59, 53), (57, 50)], K)

strokes([[(x, 28) for x in (34, 41, 49, 56)], [(x, 33) for x in (31, 36, 54, 59)],
         [(x, 47) for x in (28, 32, 58, 62)], [(x, 55) for x in (31, 59)]])

# bridge of the snout
poly(im, [(41, 36), (49, 36), (51, 46), (39, 46)], T)
rect(im, 41, 36, 3, 10, S)
rect(im, 39, 44, 2, 2, S)
line([(39, 46), (41, 36)], K)
line([(51, 46), (49, 36)], K)

# dark sockets, angry brow, red eyes
both([(30, 39), (33, 37), (38, 41), (38, 45), (33, 45), (30, 42)], D)
line([(29, 37), (33, 37), (34, 38), (35, 38), (36, 39), (37, 40), (38, 41)], K)
line([(61, 37), (57, 37), (56, 38), (55, 38), (54, 39), (53, 40), (52, 41)], K)
rect(im, 34, 42, 2, 1, E)
rect(im, 54, 42, 2, 1, E)

# ---- muzzle
muz = [(38, 47), (52, 47), (55, 51), (55, 58), (52, 63), (47, 66), (43, 66), (38, 63), (35, 58), (35, 51)]
part(muz, S)
poly(im, [(52, 48), (54, 51), (54, 58), (51, 62), (47, 65), (49, 61), (51, 57), (52, 52)], T)
# nose
poly(im, [(41, 49), (49, 49), (50, 51), (47, 54), (43, 54), (40, 51)], D)
line([(41, 49), (49, 49)], K)
line([(43, 54), (47, 54)], K)
rect(im, 42, 50, 3, 1, T)
# mouth: a hard downturned line, not a smile
line([(45, 55), (45, 58)], K)
line([(38, 62), (40, 60), (42, 59), (48, 59), (50, 60), (52, 62)], K)
line([(42, 63), (48, 63)], T)

im = strip_outline(im)
im = outline(im)
save(im)
