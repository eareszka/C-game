from pix import *

V1 = '664b95'   # violet hide
V2 = '3b2a58'   # violet shade
G1 = 'bcbeca'   # grey light
G2 = '848694'   # grey mid
G3 = '595965'   # grey shade
B1 = '94703d'   # canoe
B2 = '583518'   # canoe shade
R = 'b70000'    # blood, rider eyes
K = '000000'

im = canvas(74, 57)


def run(y, a, b, c):
    rect(im, a, y, b - a + 1, 1, c)


def filled(x, y):
    return im.load()[x, y][3] > 0


# ---------- upper coil: the lobes either side of neck and canoe
for y, a, b in [(38, 9, 16), (39, 7, 16), (40, 6, 16), (41, 5, 16), (42, 4, 16), (43, 4, 16), (44, 3, 16)]:
    run(y, a, b, V1)
run(40, 6, 8, V1)
for y in (42, 43, 44):
    run(y, 4 if y < 44 else 3, 16, V2)
run(41, 7, 9, V2); run(41, 13, 15, V2)
for y, a, b in [(39, 60, 71), (40, 60, 71), (41, 60, 71), (42, 60, 72), (43, 60, 72), (44, 60, 72)]:
    run(y, a, b, V1 if y < 43 else V2)

# ---------- tail: rises off the right of the coil, hooks over and down
TAIL = [
    (12, 58, 66), (13, 56, 68), (14, 54, 70), (15, 52, 71), (16, 51, 72),
    (17, 50, 56), (17, 65, 72), (18, 49, 54), (18, 67, 73), (19, 48, 53), (19, 68, 73),
    (20, 48, 52), (20, 69, 73), (21, 47, 52), (21, 70, 73), (22, 47, 52), (22, 70, 73),
    (23, 47, 52), (23, 71, 73), (24, 47, 52), (24, 71, 73), (25, 47, 52), (25, 72, 73),
    (26, 47, 53), (26, 72, 73), (27, 48, 54), (27, 72, 72), (28, 48, 55), (28, 72, 72),
    (29, 49, 56), (30, 50, 58), (31, 51, 60), (32, 53, 62), (33, 55, 64), (34, 57, 66),
    (35, 59, 67), (36, 60, 68), (37, 61, 69), (38, 61, 70),
]
for y, a, b in TAIL:
    run(y, a, b, V1)
# belly strip on the inside of the S, split from the hide by a black seam
for y, a, b in TAIL:
    if a > 60 and y < 29:      # hook tip, stays hide
        run(y, b - 1, b, V2)
        continue
    if y < 16:
        continue
    if y == 16:
        run(y, 57, 64, G2); run(15, 57, 64, K)
        continue
    if y == 17:
        run(y, 53, 55, K); run(y, 55, 56, G2)
        continue
    if 29 <= y <= 38 and a < 62:
        run(y, b - 2, b, G2); dot(im, b - 3, y, K)
        if y % 3 == 0:
            dot(im, b - 1, y, K)
        continue
    if y >= 18 and y <= 28:
        run(y, b - 1, b, G2); dot(im, b - 2, y, K)
        if y % 3 == 0:
            dot(im, b, y, K)
# hide bands along the tail
for x, y in [(60, 13), (61, 13), (62, 13), (66, 15), (67, 15), (68, 16), (69, 17), (70, 17), (71, 20), (72, 21),
             (54, 14), (55, 14), (52, 16), (53, 16), (49, 21), (50, 21), (49, 22), (48, 26), (49, 26),
             (51, 30), (52, 30), (56, 33), (57, 33), (58, 33)]:
    dot(im, x, y, V2)

# ---------- neck and head
BODY = {
    0: (16, 27), 1: (12, 30), 2: (9, 32), 3: (7, 33), 4: (5, 34), 5: (4, 35), 6: (3, 35), 7: (2, 36), 8: (2, 36),
    9: (2, 37), 10: (3, 37), 11: (4, 37), 12: (5, 37), 13: (7, 37), 14: (15, 37), 15: (16, 36), 16: (17, 36),
}
BODY[14] = (15, 37); BODY[15] = (16, 37); BODY[16] = (17, 37)
for ys, span in [(range(17, 22), (18, 37)), (range(22, 28), (19, 36)), (range(28, 33), (18, 35)),
                 (range(33, 38), (17, 34)), (range(38, 42), (16, 33)), (range(42, 46), (14, 33))]:
    for y in ys:
        BODY[y] = span
SPLIT = {1: 17, 2: 19, 3: 21, 4: 22, 5: 23, 6: 24, 7: 25, 8: 25, 9: 26, 10: 26}
for ys, s in [(range(11, 17), 27), (range(17, 22), 28), (range(22, 28), 29), (range(28, 33), 28),
              (range(33, 38), 27), (range(38, 46), 26)]:
    for y in ys:
        SPLIT[y] = s

for y, (a, b) in BODY.items():
    run(y, a, b, V1)
    s = SPLIT.get(y)
    if s is None:
        continue
    run(y, a, s - 2, G2)
    dot(im, s - 1, y, K)
    run(y, s, s, V1)

# violet back: shaded right edge with stepped bands
for y, (a, b) in BODY.items():
    if y >= 3:
        run(y, b - 1, b, V2)
for y in (9, 15, 21, 27, 33, 39):
    s, b = SPLIT[y], BODY[y][1]
    run(y, s + 1, b, V2)
    run(y + 1, s + 3, b, V2)
run(4, 26, 28, V2); run(5, 27, 30, V2)

# belly: lit left side, shade at the seam, scutes that step down toward the seam
for y in range(14, 46):
    a, _ = BODY[y]
    s = SPLIT[y]
    run(y, a, a + 3, G1)
    run(y, s - 3, s - 2, G3)
for y in (17, 22, 27, 32, 37, 42):
    a, _ = BODY[y]
    s = SPLIT[y + 1]
    run(y, a + 2, s - 6, G3)
    run(y + 1, s - 5, s - 2, K)

# head
for y in range(1, 9):
    a, _ = BODY[y]
    run(y, a, SPLIT[y] - 2, G1)
run(1, 12, 15, G2)
for y, a, b in [(3, 20, 19), (4, 19, 20), (5, 18, 21), (6, 18, 22), (7, 17, 23), (8, 17, 23), (9, 18, 24), (10, 17, 24), (11, 16, 25), (12, 16, 25), (13, 16, 25)]:
    if a <= b:
        run(y, a, b, G2)
# cheek plates at the neck join
run(11, 19, 25, K)
run(9, 15, 24, G2)
# upper jaw and mouth line
run(9, 2, 15, K); dot(im, 15, 8, K); dot(im, 16, 8, K); dot(im, 17, 7, K)
run(8, 3, 14, G2)
for y, a, b in [(10, 3, 18), (11, 4, 18), (12, 5, 18), (13, 7, 18)]:
    run(y, a, b, G2)
run(12, 7, 18, G3); run(13, 7, 18, G3)
for x in (17, 18):
    dot(im, x, 14, G2)
# brow ridge and eye
run(4, 11, 15, G3)
dot(im, 10, 5, G3)
run(5, 11, 12, K)
# nostril
dot(im, 5, 7, K)
# fang
dot(im, 6, 10, G1); dot(im, 6, 11, G1); dot(im, 12, 10, G1)

# blood from the mouth, running off the chin, with a falling drop
rect(im, 8, 10, 2, 4, R)
rect(im, 8, 14, 1, 4, R)
rect(im, 8, 21, 1, 2, R)

# ---------- lower coil: wide front band in front of everything so far
LOWER = [(45, 3, 72), (46, 1, 73), (47, 0, 73), (48, 0, 73), (49, 0, 73), (50, 0, 73), (51, 0, 73), (52, 0, 73),
         (53, 1, 72), (54, 3, 70), (55, 7, 66), (56, 13, 60)]
for y, a, b in LOWER:
    above = [filled(x, y - 1) for x in range(a, b + 1)]
    run(y, a, b, V1)
    if y == 45:
        for i, x in enumerate(range(a, b + 1)):
            if above[i]:
                dot(im, x, y, K)
# two loops: the front loop lies over the back loop, its round end marked by a seam
SEAM = {46: 23, 47: 21, 48: 20, 49: 19, 50: 19, 51: 19, 52: 19, 53: 20, 54: 21, 55: 23, 56: 25}
SPANS = {y: (a, b) for y, a, b in LOWER}


def strip_top(x):
    if x < SEAM[50]:                 # back loop sits higher and climbs to its end
        return 45 + min(3, x // 5)
    d = abs(x - 46)                  # front loop sags in the middle, in clear steps
    return 49 if d < 13 else 48 if d < 22 else 47


for x in range(0, 74):
    top = strip_top(x)
    for y in range(46, 57):
        a, b = SPANS[y]
        if x < a or x > b:
            continue
        if y > top + 4:
            dot(im, x, y, V2)
    if x < 3 or x > 70:
        continue
    t = top + (1 if x < SEAM[50] else 0)
    dot(im, x, t - 1, K)
    dot(im, x, t, G1)
    dot(im, x, t + 1, G2)
    dot(im, x, t + 2, G2)
    dot(im, x, t + 3, K)

# plate ticks, set off the lit top row
for x in list(range(26, 70, 6)) + [5, 11, 16]:
    t = strip_top(x) + (1 if x < SEAM[50] else 0)
    rect(im, x, t + 1, 1, 2, K)

for y, x in SEAM.items():
    dot(im, x, y, K)

# hide bands on the top of the front loop
for x in (27, 58, 66):
    t = strip_top(x)
    run(t - 2, x, x + 3, V2)

# ---------- canoe
for y, a, b in [(34, 24, 25), (35, 24, 26), (36, 25, 27), (37, 25, 28), (38, 25, 31)]:
    run(y, a, b, B1)
for y, a, b in [(34, 61, 62), (35, 60, 62), (36, 59, 61), (37, 58, 61), (38, 55, 60)]:
    run(y, a, b, B1)
run(38, 32, 54, B2)
for y, a, b in [(39, 26, 60), (40, 26, 60), (41, 27, 59), (42, 27, 59), (43, 28, 58), (44, 29, 57), (45, 31, 55), (46, 34, 52)]:
    run(y, a, b, B1)
run(41, 27, 59, K)
for y, a, b in [(44, 29, 57), (45, 31, 55), (46, 34, 52)]:
    run(y, a, b, B2)
run(43, 30, 56, B2)
# ribs on the hull
for x in (32, 39, 46, 53):
    rect(im, x, 42, 1, 2, K)
dot(im, 26, 36, B2); dot(im, 27, 37, B2); dot(im, 60, 36, B2); dot(im, 59, 37, B2)

# ---------- paddle, held by the rider
for x, y in [(41, 31), (41, 32), (42, 33), (42, 34), (43, 35), (43, 36), (44, 37), (44, 38)]:
    dot(im, x, y, B1)
rect(im, 39, 26, 3, 5, B1)
rect(im, 41, 27, 1, 4, B2)
dot(im, 40, 25, B1)

# ---------- rider: hooded, dark face, two red eyes
for y, a, b in [(29, 50, 54), (30, 49, 55), (31, 48, 56), (32, 48, 56), (33, 48, 56), (34, 48, 56), (35, 48, 56), (36, 47, 57), (37, 47, 57), (38, 47, 57)]:
    run(y, a, b, G2)
run(29, 50, 53, G1); run(30, 49, 52, G1); run(31, 48, 50, G1); run(32, 48, 49, G1); run(33, 48, 48, G1)
for y in range(31, 39):
    run(y, 55, 57 if y > 35 else 56, G3)
rect(im, 50, 32, 5, 3, K)
dot(im, 51, 33, R); dot(im, 53, 33, R)
run(35, 50, 54, G3)
# arm to the paddle
run(37, 44, 47, G3)

im = outline(im)
save(im)
