from pix import *

W = 'fcfcfc'; L = 'c6ccda'; M = '9797aa'; D = '595965'
O = 'fc9838'; R = 'b6433d'; Y = 'fae488'; K = '000000'

im = canvas(68, 94)
CX = 33


def mx(x):
    return 2 * CX - x


def sp(rows, c, flip=False):
    for y0, y1, l, r in rows:
        if flip:
            l, r = mx(r), mx(l)
        rect(im, l, y0, r - l + 1, y1 - y0 + 1, c)


def run(pts, c=K, flip=False):
    if flip:
        pts = [(mx(x), y) for x, y in pts]
    ImageDraw.Draw(im).line(pts, fill=rgba(c), width=1)


def px(x, y, c, flip=False):
    dot(im, mx(x) if flip else x, y, c)


def shade(rows, c, was=W, xmax=66):
    p = im.load()
    want = rgba(was)
    for y0, y1, x0 in rows:
        for y in range(y0, y1 + 1):
            for x in range(x0, xmax + 1):
                if p[x, y] == want:
                    p[x, y] = rgba(c)


def box(x0, y0, x1, y1, c, was=W):
    p = im.load()
    want = rgba(was)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if p[x, y] == want:
                p[x, y] = rgba(c)


def tuft(x, y, c=K):
    """A fur clump: a short slash down and to the right, then a step."""
    run([(x, y), (x + 2, y + 2), (x + 3, y + 2)], c)


# ---- legs and feet
LEG = [(80, 84, 15, 30), (85, 86, 13, 30), (87, 90, 11, 30)]
sp(LEG, W)
sp(LEG, W, flip=True)
box(25, 80, 30, 90, L)
box(36, 80, 66, 90, L)
box(44, 80, 66, 90, M, was=L)
box(11, 89, 30, 90, L)
run([(26, 80), (28, 84), (28, 86)])
run([(45, 80), (47, 84), (47, 86)])

# toes and claws
for x in (11, 16, 21, 26):
    rect(im, x, 89, 3, 2, M)
for x in (36, 41, 46, 51):
    rect(im, x, 89, 3, 2, D)
for x in (15, 20, 25, 40, 45, 50):
    run([(x, 86), (x, 90)])
run([(13, 85), (18, 85)])
run([(48, 85), (53, 85)])

# ---- torso, a tall pear
sp([(43, 46, 21, 45), (47, 50, 19, 47), (51, 56, 17, 49), (57, 64, 15, 51),
    (65, 74, 13, 53), (75, 79, 14, 52), (80, 83, 16, 50)], W)
shade([(43, 52, 37), (53, 62, 38), (63, 72, 37), (73, 83, 35)], L)
shade([(43, 52, 43), (53, 62, 44), (63, 72, 44), (73, 83, 42)], M, was=L)
# shade under the belly, the thigh lines and the split between the legs
box(16, 79, 34, 83, L)
box(35, 80, 50, 83, M, was=L)
run([(15, 79), (20, 82), (28, 83), (31, 82)])
run([(51, 79), (46, 82), (38, 83), (35, 82)])
run([(33, 75), (33, 83)])
for y in range(84, 91):
    for x in range(31, 36):
        dot(im, x, y, None)
rect(im, 32, 83, 3, 1, K)

# ---- right arm, hanging at the side
sp([(45, 47, 44, 49), (48, 52, 45, 52), (53, 60, 47, 55), (61, 68, 49, 57),
    (69, 73, 50, 58), (74, 77, 50, 59)], W)
shade([(45, 52, 49), (53, 60, 52), (61, 68, 54), (69, 77, 55)], L)
shade([(48, 52, 51), (53, 60, 54), (61, 68, 56), (69, 77, 58)], M, was=L)
run([(43, 45), (44, 48), (46, 53), (46, 60), (48, 61), (48, 68), (49, 69), (49, 77)])
for x in (50, 53, 56):
    rect(im, x, 78, 2, 3, D)
    run([(x + 2, 74), (x + 2, 77)])
rect(im, 58, 78, 2, 2, D)
tuft(49, 55, L)
tuft(50, 63, L)
tuft(52, 69, L)
run([(50, 72), (53, 72)])
# fur spikes on the elbow
px(56, 58, L); px(58, 66, M)

# ---- left arm, folded across the belly
sp([(45, 47, 17, 22), (48, 52, 14, 21), (53, 58, 11, 20), (59, 62, 9, 21),
    (63, 65, 8, 30), (66, 69, 9, 35), (70, 71, 12, 33)], W)
sp([(61, 62, 31, 35), (63, 65, 31, 36), (66, 69, 36, 36)], W)
box(9, 68, 30, 71, L)
box(31, 67, 36, 71, L)
box(34, 62, 36, 69, L)
box(35, 64, 36, 69, M, was=L)
# edge of the arm against the chest, then along the forearm
run([(23, 45), (22, 49), (22, 53), (21, 54), (21, 58), (22, 59), (22, 62), (25, 62), (28, 61), (31, 60)])
# underside of the forearm, rising to the paw, with its shadow on the belly
run([(10, 70), (12, 72), (22, 72), (28, 71), (33, 71)])
box(14, 73, 34, 74, L)
# paw edge, toe splits and claws
run([(31, 60), (35, 60), (37, 62), (37, 69), (33, 71)])
for y in (61, 64, 67, 70):
    rect(im, 38, y - 0, 2, 2, D)
for y in (63, 66, 69):
    run([(33, y), (37, y)])
# elbow crease and fur
run([(13, 61), (15, 63), (21, 64)])
tuft(15, 49, L)
tuft(13, 55, L)
tuft(20, 66, L)
tuft(11, 65, L)
# fur spikes on the silhouette
px(8, 62, W); px(7, 64, W); px(10, 57, W); px(13, 51, W); px(16, 47, W)
px(12, 73, W); px(12, 77, None)

# ---- chest ruff, short and centred
run([(25, 46), (27, 49), (29, 47), (31, 51), (33, 48), (35, 51), (37, 47), (39, 49), (41, 46)])
box(22, 43, 44, 45, L)
box(36, 43, 45, 45, M, was=L)
tuft(26, 54)
tuft(33, 55)
tuft(28, 75, L)
tuft(18, 75, L)
tuft(23, 77, L)
tuft(39, 55, M)
tuft(40, 66, M)
tuft(38, 75, M)
run([(40, 60), (43, 63), (43, 66)])

# ---- ears
for f in (False, True):
    sp([(16, 17, 22, 25), (18, 23, 20, 26)], W, flip=f)
    sp([(18, 19, 22, 24), (20, 22, 21, 25)], M, flip=f)
    run([(21, 23), (25, 23)], K, flip=f)
box(40, 16, 46, 23, L)

# ---- head
sp([(20, 21, 25, 41), (22, 23, 22, 44), (24, 26, 20, 46), (27, 33, 19, 47),
    (34, 38, 18, 48), (39, 40, 20, 46), (41, 42, 23, 43)], W)
shade([(20, 26, 41), (27, 33, 42), (34, 38, 43), (39, 42, 42)], L)
shade([(24, 33, 45), (34, 38, 46), (39, 40, 45), (41, 42, 41)], M, was=L)
box(18, 39, 41, 42, L)

# muzzle
sp([(32, 33, 28, 38), (34, 39, 26, 40), (40, 41, 28, 38)], W)
box(36, 38, 40, 41, L)
box(26, 40, 38, 41, L)
run([(27, 32), (25, 34), (25, 39), (27, 41)], L)
run([(39, 32), (41, 34), (41, 39), (39, 41)], M)

# nose
sp([(33, 35, 30, 36), (36, 36, 31, 35), (37, 37, 32, 34)], D)
run([(31, 33), (33, 33)], M)
run([(33, 38), (33, 39)])

# mouth with fangs
rect(im, 29, 40, 9, 2, R)
run([(28, 39), (29, 40), (37, 40), (38, 39)])
run([(30, 42), (36, 42)])
rect(im, 30, 41, 2, 1, W)
rect(im, 35, 41, 2, 1, W)

# eyes and brows
rect(im, 25, 30, 2, 2, K)
rect(im, 40, 30, 2, 2, K)
run([(21, 26), (23, 27), (25, 28), (28, 29)], D)
run([(45, 26), (43, 27), (41, 28), (38, 29)], D)

# chin line against the chest
run([(21, 40), (24, 43), (42, 43), (45, 40)])

# ---- orange ear tufts on both sides of the head
TUFT = [(25, 26, 15, 20), (27, 29, 13, 20), (30, 34, 12, 20), (35, 38, 13, 20),
        (39, 41, 15, 20), (42, 43, 17, 20)]
for f in (False, True):
    sp(TUFT, O, flip=f)
    run([(13, 31), (19, 28)], R, flip=f)
    run([(13, 35), (19, 32)], R, flip=f)
    run([(14, 39), (19, 36)], R, flip=f)
    rect(im, mx(19) if f else 17, 39, 3, 5, R)
    if not f:
        run([(15, 27), (19, 25)], Y)
        run([(13, 30), (17, 28)], Y)
    run([(16, 24), (21, 25), (21, 43), (18, 45)], K, flip=f)
    for x, y in ((13, 30), (12, 34), (13, 38), (15, 41)):
        px(x, y, None, flip=f)
    run([(13, 34), (15, 34)], K, flip=f)
    run([(14, 38), (16, 38)], K, flip=f)
box(45, 23, 60, 46, R, was=Y)

# ---- horn, striped in a twist
for y in range(7, 26):
    h = 1 if y < 12 else 2 if y < 17 else 3 if y < 22 else 4
    for x in range(CX - h, CX + h + 1):
        k = (y - (x - CX) // 2) % 6
        c = O if k < 3 else Y
        if x == CX + h:
            c = R if c == O else O
        dot(im, x, y, c)
run([(28, 25), (29, 26), (37, 26), (38, 25)])

# ---- star on the tip
rect(im, 33, 0, 1, 7, Y)
rect(im, 30, 3, 7, 1, Y)
rect(im, 32, 2, 3, 3, Y)
rect(im, 33, 2, 1, 3, W)
rect(im, 32, 3, 3, 1, W)

im = outline(im)
save(im)
