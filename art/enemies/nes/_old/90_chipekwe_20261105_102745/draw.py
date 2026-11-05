from pix import *

L, M, D = 'dcf0ff', '5c94fc', '2850a0'
H1, H2, H3 = 'e8e0c0', 'cebe82', 'b2966a'
K = '000000'
PAL = {'a': H1, 'b': H2, 'c': H3}

im = canvas(84, 84)
d = ImageDraw.Draw(im)


def ln(pts, c=K):
    d.line(pts, fill=rgba(c))


def claws(x, y, n=3, gap=4):
    # pale claws poking out under a foot, split by short black lines
    for i in range(n):
        cx = x + i * gap
        rect(im, cx, y, 3, 2, H2)
        dot(im, cx, y, H1)
        dot(im, cx + 1, y, H1)
        dot(im, cx + 2, y + 1, H3)
        ln([(cx + 1, y - 1), (cx + 2, y - 1)], D)
        if i:
            ln([(cx - 1, y - 3), (cx - 1, y + 1)])


def folds(x0, x1, ys):
    # leg wrinkles: a black fold with a short lit run sitting on it
    for i, y in enumerate(ys):
        a = x0 + (i % 2)
        ln([(a, y), (x1 - (i % 2), y)])
        ln([(a + 1, y - 1), (a + 3, y - 1)], L)
        ln([(x1 - 5, y - 1), (x1 - 2, y - 1)], D)
        ln([(a + 2, y + 1), (a + 4, y + 1)], D)


# ---- far leg, in shadow ----
poly(im, [(25, 54), (38, 54), (39, 62), (37, 66), (38, 72), (24, 72), (25, 66), (24, 60)], D)
poly(im, [(27, 58), (31, 58), (31, 64), (28, 66), (27, 70), (26, 70)], M)
ln([(25, 65), (36, 65)])
claws(26, 71)

# ---- body mass: one smooth-backed hunch ----
poly(im, [(9, 24), (13, 14), (19, 8), (27, 3), (38, 2), (46, 4), (53, 8), (59, 14), (64, 21),
          (68, 29), (71, 38), (73, 47), (73, 58), (66, 62), (20, 62), (8, 48)], M)
snap = im.copy()
body = snap.load()


def plate(x, y, w, h):
    # one hide plate, toned by where it sits on the hunched body
    light = (-(x - 38) * 0.55 - (y - 34) * 0.8) / 30
    if light > 0.3:
        fill, hi, lo, run = M, L, D, w - 5
    elif light > -0.35:
        fill, hi, lo, run = M, L, D, 2
    else:
        fill, hi, lo, run = D, M, D, w - 4
    pts = []
    for yy in range(y, y + h):
        inset = 1 if yy in (y, y + h - 1) else 0
        for xx in range(x + inset, x + w - inset):
            pts.append((xx, yy, fill))
    for xx in range(x + 1, x + 1 + max(run, 1)):
        pts.append((xx, y + 1, hi))
    for xx in range(x + 3, x + w - 1):
        pts.append((xx, y + h - 2, lo))
    for xx in range(x + 1, x + w):
        pts.append((xx, y + h, K))
    for yy in range(y + 1, y + h):
        pts.append((x + w, yy, K))
    for xx, yy, c in pts:
        if 0 <= xx < im.width and 0 <= yy < im.height and body[xx, yy][3]:
            dot(im, xx, yy, c)


widths = (11, 8, 13, 9, 12, 7)
for r, y0 in enumerate(range(-2, 66, 8)):
    x0 = 2 + (r * 5) % 9
    i = r
    while x0 < 80:
        w = widths[i % len(widths)]
        bend = int(((x0 - 40) / 36.0) ** 2 * 18)
        plate(x0, y0 + bend, w, 7)
        x0 += w + 1
        i += 1

# ---- belly: stepped dark hollow with a lit middle ----
poly(im, [(24, 39), (36, 38), (42, 42), (45, 50), (44, 58), (40, 63), (24, 63), (20, 58), (19, 46)], D)
poly(im, [(27, 45), (35, 44), (40, 48), (41, 55), (37, 60), (27, 60), (23, 55), (23, 49)], M)
ln([(27, 46), (32, 46)], L)
ln([(25, 48), (27, 48)], L)
ln([(29, 54), (36, 54)])
ln([(26, 57), (33, 57)])
ln([(32, 51), (38, 51)])
ln([(23, 44), (27, 41), (36, 41), (41, 45), (43, 52)])

# ---- rear leg ----
poly(im, [(59, 37), (66, 35), (71, 40), (74, 50), (74, 60), (73, 66), (74, 72), (59, 72), (60, 64), (58, 56), (57, 44)], M)
poly(im, [(70, 42), (72, 44), (74, 50), (74, 60), (73, 66), (74, 72), (69, 72), (69, 64), (70, 54)], D)
ln([(60, 39), (65, 38)], L)
ln([(60, 40), (61, 40)], L)
folds(60, 69, (54, 63))
ln([(58, 46), (63, 49), (69, 46)])
claws(60, 71)

# ---- near thigh and leg ----
poly(im, [(46, 28), (54, 26), (60, 32), (60, 44), (57, 54), (55, 62), (56, 72), (41, 72), (42, 64), (41, 54), (41, 36)], M)
poly(im, [(56, 34), (60, 34), (60, 44), (57, 54), (55, 62), (56, 72), (52, 72), (51, 62), (54, 50)], D)
ln([(46, 31), (52, 29)], L)
ln([(45, 32), (45, 35)], L)
folds(42, 52, (50, 58, 65))
ln([(43, 43), (48, 45), (54, 43)])
claws(42, 71)

# ---- front leg ----
poly(im, [(5, 36), (17, 34), (20, 42), (20, 52), (17, 60), (19, 72), (4, 72), (5, 62), (2, 52), (2, 42)], M)
poly(im, [(16, 42), (20, 42), (20, 52), (17, 60), (19, 72), (15, 72), (14, 60), (16, 52)], D)
ln([(4, 47), (8, 47)], L)
ln([(3, 48), (3, 51)], L)
folds(4, 15, (56, 64))
claws(5, 71)

# ---- head ----
poly(im, [(17, 12), (26, 10), (33, 15), (36, 23), (34, 32), (28, 38), (22, 43), (11, 45), (4, 44),
          (1, 39), (2, 33), (8, 29), (12, 21)], M)
poly(im, [(31, 20), (36, 23), (34, 32), (28, 38), (22, 43), (19, 41), (26, 35), (30, 28)], D)
ln([(19, 13), (25, 12)], L)
ln([(18, 14), (18, 16)], L)
ln([(4, 35), (7, 33)], L)
# brow plate, eye, cheek fold
ln([(19, 20), (24, 18), (28, 19)])
rect(im, 19, 21, 11, 7, M)
rect(im, 23, 23, 1, 2, K)
ln([(21, 29), (25, 29)], L)
ln([(30, 26), (28, 32), (23, 37), (18, 38)])
ln([(19, 36), (24, 34)], D)
ln([(8, 37), (13, 37)], D)
ln([(10, 39), (15, 39)], L)
# mouth, nostril
ln([(2, 41), (8, 41), (13, 43), (19, 41)])
rect(im, 5, 38, 2, 1, K)

# ---- horn: thick, pale, curving back off the snout ----
stamp(im, grid([
    'a..........',
    'aa.........',
    'aab........',
    'aab........',
    'aabb.......',
    'aabbc......',
    '.aabc......',
    '.aabbc.....',
    '.aabbc.....',
    '.aabbcc....',
    '.aabbbc....',
    '..aabbcc...',
    '..aabbbc...',
    '..aabbbcc..',
    '..aaabbbc..',
    '...aabbbcc.',
    '...aabbbbc.',
    '...aaabbbcc',
    '...aaabbbbc',
    '....aaabbbc',
], PAL), 6, 10)
ln([(9, 31), (11, 31), (16, 31), (18, 28)])

# ---- creases on the shaded side of each leg, knuckles on the toes ----
for x0, x1, y in ((71, 72, 50), (71, 72, 58), (70, 71, 66), (55, 56, 44), (53, 54, 52), (53, 54, 60),
                  (17, 18, 46), (17, 18, 53), (16, 17, 62), (16, 17, 67), (26, 28, 42), (37, 39, 42),
                  (21, 22, 50), (42, 43, 56), (34, 36, 68), (33, 35, 60), (28, 30, 62)):
    ln([(x0, y), (x1, y)], M)
for fx in (5, 26, 42, 60):
    for i in range(3):
        ln([(fx + i * 4, 68), (fx + i * 4 + 1, 68)], L)

# ---- black line work between the parts ----
ln([(36, 24), (37, 30), (34, 35), (29, 40), (23, 45), (21, 46)])
ln([(34, 14), (37, 22)])
ln([(21, 42), (21, 52), (18, 60), (19, 66)])
ln([(46, 28), (42, 34), (40, 44), (40, 54), (41, 64)])
ln([(46, 28), (54, 26), (60, 31), (61, 44), (58, 54), (56, 62), (57, 66)])
ln([(60, 37), (66, 34), (71, 39)])

# Black that reached the silhouette would double the outline, so lift it first.
im = strip_outline(im)
im = outline(im)
save(im)
