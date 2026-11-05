from pix import *

L = 'cebe82'   # sand light
M = 'b2966a'   # sand mid
D = '8d6b4f'   # sand dark
BL = 'f4ce80'  # brick light
BM = 'c18a39'  # brick mid
BD = '815423'  # brick dark
F = '583518'   # fringe / far legs
K = '000000'
PAL = {'l': L, 'm': M, 'd': D, 'f': F, 'b': BD}

W, H = 134, 92
im = canvas(W, H)


def line(target, pts, colour):
    ImageDraw.Draw(target).line(pts, fill=rgba(colour))


def shade(layer, lit, mid, dark, top=2, side=0, under=5, right=3):
    """Flat three-tone shade from the upper left, following the layer's edge."""
    src = layer.copy().load()
    px = layer.load()

    def solid(x, y):
        return 0 <= x < layer.width and 0 <= y < layer.height and src[x, y][3]
    for y in range(layer.height):
        for x in range(layer.width):
            if not src[x, y][3]:
                continue
            c = mid
            if (under and not solid(x, y + under)) or (right and not solid(x + right, y)):
                c = dark
            if (top and not solid(x, y - top)) or (side and not solid(x - side, y)):
                c = lit
            px[x, y] = rgba(c)


def paste(layer, seam_from=0, sides=((1, 0), (-1, 0), (0, 1), (0, -1))):
    """Put a layer on the sprite with black where it overlaps what's already drawn."""
    src = layer.load()
    dst = im.load()
    marks = []
    for y in range(layer.height):
        for x in range(layer.width):
            if not src[x, y][3] or y < seam_from:
                continue
            for a, b in sides:
                xx, yy = x + a, y + b
                if 0 <= xx < W and 0 <= yy < H and not src[xx, yy][3] and dst[xx, yy][3]:
                    marks.append((x, y))
                    break
    im.alpha_composite(layer)
    for x, y in marks:
        dst[x, y] = BLACK


# ---- far legs: dark, behind everything ----
for pts, tx in (
    ([(13, 62), (28, 64), (27, 75), (25, 79), (26, 84), (28, 88), (10, 88), (13, 84), (15, 76)], 13),
    ([(62, 64), (79, 64), (77, 75), (75, 79), (76, 84), (79, 88), (60, 88), (64, 84), (65, 76)], 62),
):
    leg = canvas(W, H)
    poly(leg, pts, F)
    shade(leg, BD, F, F, top=0, side=2, under=0, right=0)
    im.alpha_composite(leg)
    line(im, [(tx + 2, 79), (tx + 11, 79)], K)
    line(im, [(tx + 3, 80), (tx + 10, 80)], BD)
    line(im, [(tx + 2, 88), (tx + 2, 85)], K)
    line(im, [(tx + 8, 88), (tx + 8, 85)], K)

# ---- tail ----
tail = canvas(W, H)
poly(tail, [(16, 49), (18, 56), (13, 60), (10, 66), (9, 72), (6, 72), (6, 66), (8, 60), (11, 54)], M)
shade(tail, L, M, D, top=0, side=2, under=0, right=2)
im.alpha_composite(tail)
tuft = canvas(W, H)
poly(tuft, [(5, 70), (10, 70), (11, 76), (9, 82), (7, 78), (6, 84), (4, 79), (2, 82), (3, 75)], F)
im.alpha_composite(tuft)
line(im, [(5, 73), (4, 78)], BD)
line(im, [(8, 72), (8, 78)], BD)
line(im, [(5, 70), (10, 70)], K)

# ---- body and neck ----
body = canvas(W, H)
poly(body, [
    (22, 45), (30, 43), (95, 44), (99, 48), (102, 52), (106, 54), (110, 53), (112, 49), (113, 45), (114, 38),
    (125, 38), (126, 46), (126, 52), (124, 57), (120, 62), (115, 66), (109, 69), (102, 72), (94, 74),
    (82, 71), (60, 69), (40, 69), (30, 71), (20, 71), (15, 65), (13, 57), (15, 51), (18, 47),
], M)
shade(body, L, M, D, top=2, under=5, right=3)
im.alpha_composite(body)

# ---- pyramid, course by course ----
pyr = canvas(W, H)
AX = 56
TOP = 3
COURSES = 15
for i in range(COURSES):
    y0 = TOP + i * 3
    left = AX - int(2.1 * i) - 1
    right = AX + int(2.6 * i) + 1
    ridge = AX + int(1.05 * i)
    rect(pyr, left, y0, ridge - left + 1, 3, BL)
    rect(pyr, ridge + 1, y0, right - ridge, 3, BM)
    # mortar line under the course
    rect(pyr, left, y0 + 2, ridge - left + 1, 1, BM)
    rect(pyr, ridge + 1, y0 + 2, right - ridge, 1, BD)
    # joints, staggered by course
    off = 3 if i % 2 else 0
    for x in range(left + off, right, 6):
        if x == left or x == right:
            continue
        c = BM if x <= ridge else BD
        rect(pyr, x, y0, 1, 2, c)
    # shaded bricks on the lit face give the wall its worn look
    if i >= 3:
        for n, x in enumerate(range(left + off + 1, ridge - 5, 6)):
            if (n * 5 + i * 3) % 7 == 0:
                rect(pyr, x, y0, 5, 2, BM)
    # dark bricks on the shaded face
    if i >= 2:
        for n, x in enumerate(range(ridge + off + 2, right - 5, 6)):
            if (n * 3 + i * 5) % 5 == 0:
                rect(pyr, x, y0, 5, 2, BD)
    # black ridge
    rect(pyr, ridge, y0, 1, 3, K)
    if i < COURSES - 1:
        rect(pyr, ridge + 1, y0 + 2, 1, 1, K)
# cracks
line(pyr, [(45, 20), (47, 23), (44, 26), (46, 29), (43, 33)], K)
line(pyr, [(52, 12), (50, 15), (52, 18)], K)
line(pyr, [(76, 27), (79, 30), (78, 34), (82, 38)], K)
line(pyr, [(84, 37), (82, 40)], K)
# upper slot
rect(pyr, 46, 25, 10, 1, K)
rect(pyr, 47, 26, 8, 2, F)
rect(pyr, 46, 28, 10, 1, K)
# doorway with lintel
rect(pyr, 42, 33, 16, 2, BD)
rect(pyr, 42, 32, 16, 1, K)
rect(pyr, 42, 35, 16, 1, K)
rect(pyr, 44, 36, 12, 7, F)
rect(pyr, 43, 36, 1, 7, K)
rect(pyr, 56, 36, 1, 7, K)
rect(pyr, 45, 37, 5, 1, BD)
im.alpha_composite(pyr)

# ---- fur draped over the pyramid base ----
drape = canvas(W, H)
xs = list(range(26, 90, 5))
for n, x in enumerate(xs):
    tip = 41 if n % 3 == 0 else (43 if n % 3 == 1 else 40)
    poly(drape, [(x, 48), (x + 2, tip), (x + 5, 48)], L)
rect(drape, 24, 45, 72, 4, L)
dp, bp = drape.load(), body.load()
for y in range(44, 49):
    for x in range(W):
        if dp[x, y][3] and not bp[x, y][3]:
            dp[x, y] = CLEAR
paste(drape, sides=((1, 0), (-1, 0), (0, -1)))

# ---- fringe under the belly ----
fr = canvas(W, H)
teeth = [4, 7, 3, 8, 5, 2, 7, 4, 8, 3, 6, 8, 4, 7, 3, 6, 8, 4, 5]
x = 30
pts = [(30, 62)]
ups = [62, 64, 61, 63, 60, 63, 61, 64, 60, 63, 61, 64, 62, 60, 63, 61, 64, 62, 63]
for n, t in enumerate(teeth):
    pts.insert(n, (x + 3, ups[n]))
    pts.append((x, 70 + t))
    pts.append((x + 3, 70))
    x += 3
pts = [(30, 66)] + [(30 + 3 * n + 1, ups[n]) for n in range(len(teeth))]
low = []
x = 30 + 3 * len(teeth)
for n in range(len(teeth) - 1, -1, -1):
    low.append((x, 70))
    low.append((x - 2, 70 + teeth[n]))
    x -= 3
poly(fr, pts + low, F)
frp = fr.load()
for n, t in enumerate(teeth):
    xx = 30 + 3 * n + 1
    if n % 2 == 0:
        line(fr, [(xx, 66), (xx, 69 + t // 2)], BD)
    elif n % 4 == 1:
        line(fr, [(xx, 65), (xx, 69)], K)
paste(fr)

# chest tufts
ch = canvas(W, H)
poly(ch, [(92, 72), (97, 70), (104, 68), (110, 66), (108, 71), (106, 69), (105, 75), (102, 71), (100, 77), (97, 73), (95, 78), (93, 74)], F)
line(ch, [(101, 71), (100, 74)], BD)
line(ch, [(96, 72), (95, 75)], BD)
paste(ch)

# ---- near legs ----
for pts, tx in (
    ([(26, 60), (43, 60), (42, 73), (40, 78), (41, 84), (44, 88), (24, 88), (27, 84), (28, 76)], 26),
    ([(80, 60), (97, 62), (95, 73), (93, 78), (94, 84), (97, 88), (77, 88), (80, 84), (82, 76)], 80),
):
    leg = canvas(W, H)
    poly(leg, pts, M)
    shade(leg, L, M, D, top=0, side=2, under=2, right=3)
    paste(leg, seam_from=68)
    # knee and toes
    line(im, [(tx + 2, 78), (tx + 13, 78)], K)
    line(im, [(tx + 3, 79), (tx + 12, 79)], D)
    line(im, [(tx + 3, 72), (tx + 7, 72)], D)
    line(im, [(tx + 4, 75), (tx + 9, 75)], D)
    line(im, [(tx + 3, 88), (tx + 3, 85)], K)
    line(im, [(tx + 9, 88), (tx + 9, 85)], K)

# ---- line work on the hide ----
# haunch
line(im, [(40, 50), (43, 53), (44, 58), (43, 64), (41, 68)], K)
line(im, [(39, 51), (42, 54), (43, 58), (42, 63)], D)
# shoulder
line(im, [(82, 51), (79, 55), (78, 60), (79, 65), (81, 69)], K)
line(im, [(83, 53), (80, 56), (79, 60), (80, 64)], D)
# ribs
for rx in (52, 58, 64, 70):
    line(im, [(rx, 54), (rx - 1, 58), (rx, 62)], D)
# rump and chest fur strokes
for tx, ty in ((24, 53), (21, 59), (32, 55), (29, 63)):
    line(im, [(tx, ty), (tx + 2, ty + 2), (tx + 2, ty + 4)], D)
for tx, ty in ((88, 54), (98, 57), (91, 62), (104, 61)):
    line(im, [(tx, ty), (tx + 2, ty + 2), (tx + 2, ty + 4)], D)

# neck folds, stopping short of the edge so the silhouette stays whole
for fy, x0, x1 in ((42, 118, 124), (46, 119, 124), (50, 118, 124), (54, 116, 122), (58, 113, 119)):
    line(im, [(x0, fy), (x1, fy)], D)
    line(im, [(x1 - 3, fy), (x1, fy)], K)
line(im, [(114, 45), (113, 49), (111, 53), (108, 57), (104, 59)], D)

# ---- head ----
head = grid([
    "..........lm......lm..",
    ".........llm.....llm..",
    ".........lmd.....lmd..",
    "..........lllllllmmd..",
    ".........llllllllmmmd.",
    "........lllllllllmmmd.",
    ".......llllKlllllKmmd.",
    ".....llllllKlllllKmmd.",
    "...lllllllllllllmmmmd.",
    "..lllllllllllllmmmmdd.",
    ".llllllllllmmmmmmmmdd.",
    ".lKKlllmmmmmmmmmmmdd..",
    "lllllllmmmmmmmmmmddd..",
    "lmmmmmmmmmmmmmmmddd...",
    "lKKKKKKKKKmmmmmdddd...",
    ".mmmmmmmmKmmmmmmdd....",
    "..dmmmmmmmmmmmmdd.....",
    "...ddddddmmmmmmd......",
    ".......dmmmmmmmd......",
], PAL)
stamp(im, head, 106, 24)

im = outline(im)
save(im)
