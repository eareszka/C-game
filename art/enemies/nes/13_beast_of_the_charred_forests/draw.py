from pix import *

D, M, L = '34343e', '595965', '848694'
R, O, Y = 'b6433d', 'fc9838', 'fae488'
W = 'fcfcfc'
K = '000000'
FLIP = 78

im = canvas(79, 85)
draw = ImageDraw.Draw(im)
NB = ((1, 0), (-1, 0), (0, 1), (0, -1))


def flip(pts):
    return [(FLIP - x, y) for x, y in pts]


def part(pts, shade=3, lite=1, flat=None):
    """One plate: black seam where it overlaps what is behind, lit upper left, dark lower right."""
    mask = canvas(im.width, im.height)
    poly(mask, pts, M)
    m = mask.load()
    px = im.load()
    old = im.copy().load()
    inside = lambda x, y: 0 <= x < im.width and 0 <= y < im.height and m[x, y][3] > 0
    painted = lambda x, y: 0 <= x < im.width and 0 <= y < im.height and old[x, y][3] > 0
    for y in range(im.height):
        for x in range(im.width):
            if not inside(x, y):
                continue
            if any(not inside(x + a, y + b) and painted(x + a, y + b) for a, b in NB):
                px[x, y] = rgba(K)
                continue
            c = flat or M
            if not flat:
                if any(not inside(x + i, y + i) for i in range(1, shade + 1)):
                    c = D
                elif any(not inside(x - i, y - i) for i in range(1, lite + 1)):
                    c = L
            px[x, y] = rgba(c)


def pair(pts, shade=(2, 4), lite=(2, 1)):
    part(pts, shade[0], lite[0])
    part(flip(pts), shade[1], lite[1])


def whole(pts, shade=3, lite=1, flat=None):
    part(pts + flip(pts)[::-1], shade, lite, flat)


def ln(pts, c=K, mirrored=True):
    draw.line(pts, fill=rgba(c))
    if mirrored:
        draw.line(flip(pts), fill=rgba(c))


# --- spines along the back, big and uneven ---
for pts, s in [
    ([(35, 13), (39, 0), (43, 13)], 2),
    ([(24, 14), (24, 3), (32, 12)], 2),
    ([(46, 12), (55, 5), (54, 15)], 3),
    ([(15, 22), (11, 11), (24, 16)], 2),
    ([(55, 15), (67, 12), (63, 23)], 3),
]:
    part(pts, s, 1)

# --- arm tufts, behind the arms ---
pair([(7, 62), (0, 62), (5, 55)], (1, 2), (1, 1))
pair([(6, 52), (0, 47), (6, 44)], (1, 2), (1, 1))
# shoulder spikes
pair([(8, 37), (0, 27), (15, 30)], (2, 3), (1, 1))

# --- back plates, shingled: lower ones first, jagged edges hanging over them ---
whole([(39, 25), (30, 25), (22, 31), (18, 40), (19, 50), (22, 54), (24, 46), (27, 50), (30, 42), (39, 44)], 3, 1)
whole([(39, 16), (30, 16), (22, 21), (16, 30), (13, 40), (18, 35), (21, 42), (26, 30), (30, 36), (34, 27), (39, 33)], 2, 1)
whole([(39, 8), (31, 9), (24, 13), (18, 19), (14, 29), (19, 25), (22, 31), (27, 20), (31, 25), (35, 16), (39, 21)], 2, 2)

# --- arms, planted wide with a gap to the head: paw up to shoulder ---
pair([(0, 71), (19, 71), (22, 79), (0, 79)], (2, 3), (1, 1))
pair([(2, 58), (19, 57), (19, 70), (15, 74), (11, 70), (7, 74), (3, 68)])
pair([(3, 46), (18, 46), (20, 56), (16, 60), (11, 56), (7, 60), (1, 54)])
pair([(15, 27), (8, 30), (3, 37), (1, 46), (5, 52), (9, 47), (13, 53), (18, 47), (21, 40), (20, 32)], (3, 5), (2, 1))

# --- chest, deep shadow behind the head ---
whole([(21, 44), (39, 44), (39, 64), (28, 62), (23, 56)], flat=D)

# --- head, hanging low: lower jaw, skull, then a heavy brow and snarling muzzle ---
whole([(39, 62), (27, 62), (25, 68), (28, 78), (33, 84), (39, 84)], 3, 1)
whole([(39, 30), (33, 31), (28, 36), (26, 44), (27, 52), (39, 54)], 3, 2)
whole([(39, 48), (33, 48), (28, 52), (24, 58), (26, 66), (31, 58), (35, 54), (39, 53)], 2, 2)
pair([(38, 48), (31, 41), (26, 40), (24, 44), (30, 46), (36, 51)], (2, 2), (1, 1))

# --- knuckles and small ridges ---
ln([(6, 75), (6, 78)])
ln([(12, 75), (12, 78)])
ln([(18, 75), (18, 78)])
ln([(39, 31), (39, 37)], mirrored=False)

# --- mouth ---
whole([(39, 53), (32, 54), (27, 59), (26, 66), (28, 74), (33, 80), (39, 80)], flat=K)
whole([(39, 55), (33, 56), (29, 60), (28, 66), (30, 72), (34, 78), (39, 78)], flat=R)
whole([(39, 58), (35, 58), (31, 62), (30, 66), (32, 70), (35, 76), (39, 76)], flat=O)
whole([(39, 66), (37, 66), (36, 68), (36, 70), (37, 72), (39, 74)], flat=Y)

# upper teeth, spaced out along the lip
for x, y, t in [(30, 58, 9), (34, 55, 6), (37, 54, 5)]:
    for pts in ([(x - 1, y), (x + 1, y), (x, y + t)],):
        poly(im, pts, W)
        poly(im, flip(pts), W)
# lower teeth
for x, y, t in [(32, 77, 8), (36, 78, 5)]:
    pts = [(x - 1, y), (x + 1, y), (x, y - t)]
    poly(im, pts, W)
    poly(im, flip(pts), W)

# --- embers in the neck cracks and arm seams ---
ln([(22, 45), (22, 50), (24, 55)], O)
ln([(24, 55), (24, 60)], R)
ln([(15, 60), (14, 66)], O)

# --- claws ---
for x in (1, 7, 13, 19):
    pts = [(x, 79), (x + 3, 79), (x + 1, 84)]
    poly(im, pts, W)
    poly(im, flip(pts), W)

im = outline(im)
save(im)
