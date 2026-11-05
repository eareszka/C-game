from pix import *
import math

LITE = 'f0b890'
MID = 'ec8476'
DEEP = 'b6433d'
RED = '792727'
DARK = '531b1c'
BONE = 'e8e0c0'
BONE2 = 'cebe82'
K = '000000'

W, H = 172, 172
im = canvas(W, H)


def mask_of(pts=None, ovals=()):
    t = canvas(W, H)
    if pts:
        poly(t, pts, 'ffffff')
    for o in ovals:
        oval(t, *o, 'ffffff')
    p = t.load()
    return {(x, y) for y in range(H) for x in range(W) if p[x, y][3]}


def paint(m, base=LITE, shade=MID, rim=DEEP, d=(5, 4), r=(1, 1)):
    for x, y in m:
        c = base
        if (x + d[0], y + d[1]) not in m:
            c = shade
        if (x + r[0], y + r[1]) not in m:
            c = rim
        dot(im, x, y, c)


def line(pts, c):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            dot(im, round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), c)


def blob(x, y, w, h, c, step=3, power=2.6):
    """Rounded shape built from flat runs and clear steps."""
    cx, cy = x + w / 2, y + h / 2
    for yy in range(y, y + h):
        band = y + ((yy - y) // step) * step + step / 2
        v = min(abs(band - cy) / (h / 2), 1)
        half = (w / 2) * (1 - v ** power) ** (1 / power)
        half = max(2, int(half / 2) * 2)
        rect(im, int(cx - half), yy, half * 2, 1, c)


def crease(pts, dark=K, under=DEEP):
    """Black skin line with a pink step under it."""
    line([(a, b + 1) for a, b in pts], under)
    line(pts, dark)


# ---------- fingers ----------
index = [(39, 11), (43, 6), (50, 3), (56, 6), (59, 14), (60, 24), (63, 28), (64, 38), (67, 44),
         (69, 54), (72, 68), (52, 70), (51, 54), (47, 46), (47, 38), (43, 30), (41, 20)]
middle = [(81, 8), (85, 2), (92, 0), (99, 2), (103, 8), (103, 20), (101, 26), (101, 36), (99, 42),
          (98, 54), (98, 68), (74, 68), (76, 52), (79, 44), (79, 34), (81, 26), (81, 16)]
ring = [(116, 28), (122, 24), (130, 23), (136, 26), (138, 32), (135, 42), (131, 46), (127, 54),
        (122, 58), (119, 68), (116, 76), (98, 70), (102, 56), (107, 50), (109, 42), (113, 36)]
pinky = [(122, 68), (127, 62), (133, 60), (138, 54), (146, 51), (153, 52), (157, 57), (156, 63),
         (150, 68), (143, 71), (138, 77), (133, 80), (129, 88), (126, 98), (112, 92)]
for f in (index, middle, ring, pinky):
    paint(mask_of(f))

# ---------- thumb ----------
thumb = mask_of([(20, 88), (30, 92), (40, 98), (50, 96), (58, 92), (66, 136), (52, 128),
                 (40, 120), (30, 112), (18, 110)], [(1, 84, 28, 28)])
paint(thumb)

# ---------- palm and wrist ----------
palm = mask_of([(48, 66), (56, 62), (70, 66), (78, 62), (96, 62), (104, 66), (114, 68), (124, 74),
                (129, 84), (128, 94), (123, 106), (119, 118), (116, 130), (112, 140), (111, 148),
                (113, 157), (70, 157), (72, 148), (68, 140), (60, 132), (54, 122), (50, 110),
                (47, 96), (46, 80)])
paint(palm, d=(6, 4))
# blend the joins: no rim where a part runs into another part
for x, y in thumb & palm:
    if 46 <= x <= 62 and 94 <= y <= 130:
        dot(im, x, y, LITE)

# finger gaps run down into the palm
line([(72, 68), (72, 62)], K)
line([(98, 68), (98, 62)], K)
line([(116, 74), (116, 66)], K)

# knuckle pads along the finger bases
for x, y, w in ((54, 60, 14), (78, 60, 16), (102, 62, 11)):
    rect(im, x, y, w, 2, MID)
    rect(im, x + 2, y + 2, w - 4, 1, DEEP)

# ---------- finger creases ----------
crease([(49, 47), (54, 44), (64, 42)])
crease([(52, 52), (58, 50), (66, 48)])
crease([(78, 44), (86, 46), (99, 43)])
crease([(77, 50), (86, 52), (98, 49)])
crease([(106, 50), (113, 54), (124, 55)])
crease([(102, 57), (110, 60), (120, 62)])
crease([(127, 63), (130, 68), (134, 75)])
crease([(122, 69), (125, 75), (129, 84)])
crease([(51, 32), (55, 30), (61, 28)], DEEP, MID)
crease([(82, 34), (90, 36), (99, 34)], DEEP, MID)
crease([(112, 40), (118, 44), (130, 46)], DEEP, MID)
crease([(140, 58), (142, 64), (145, 70)], DEEP, MID)

# thumb: a crescent under the pad, and joints
blob(7, 91, 16, 16, MID, 2)
blob(6, 89, 15, 15, LITE, 2)
line([(10, 104), (16, 106), (21, 103)], DEEP)
crease([(29, 92), (27, 100), (30, 110)])
crease([(35, 96), (34, 106), (38, 116)], DEEP, MID)
crease([(46, 100), (47, 112), (52, 124)], DEEP, MID)

# small wrinkles
crease([(50, 22), (54, 20), (58, 21)], DEEP, MID)
crease([(53, 38), (57, 36), (62, 36)], DEEP, MID)
crease([(82, 38), (90, 40), (98, 38)], DEEP, MID)
crease([(114, 34), (120, 37), (126, 38)], DEEP, MID)
crease([(108, 46), (115, 49), (126, 50)], DEEP, MID)
crease([(136, 62), (138, 67), (140, 73)], DEEP, MID)
crease([(40, 100), (41, 110), (45, 120)], DEEP, MID)
crease([(58, 126), (62, 130), (68, 134)], DEEP, MID)
crease([(116, 110), (113, 118), (112, 128)], DEEP, MID)

# ---------- palm mouth: lips ----------
blob(55, 69, 68, 72, DEEP)
blob(57, 71, 64, 68, MID)
blob(59, 73, 60, 64, LITE)
blob(61, 75, 56, 60, MID)
blob(63, 77, 52, 56, DEEP)
blob(64, 78, 50, 54, K)
blob(65, 79, 48, 52, DARK)

# palm creases round the lips
crease([(50, 76), (54, 72), (60, 68)])
crease([(52, 84), (52, 96), (54, 108)], DEEP, MID)
crease([(120, 84), (123, 92), (121, 104)])
crease([(112, 134), (106, 138), (100, 141)])
crease([(66, 136), (72, 140), (78, 142)])
crease([(84, 64), (92, 67), (100, 66)], DEEP, MID)

# ridges round the lips
for deg in range(0, 360, 24):
    t = math.radians(deg + 7)
    line([(round(89 + 28 * math.cos(t)), round(105 + 30 * math.sin(t))),
          (round(89 + 31 * math.cos(t)), round(105 + 33 * math.sin(t)))], DEEP)

# ---------- palm mouth: gums and teeth ----------
blob(68, 80, 42, 14, RED, 2)
rect(im, 70, 92, 38, 1, K)
blob(70, 118, 38, 12, RED, 2)
rect(im, 72, 118, 34, 1, K)

# upper teeth: two fangs and a row between
for x, y, w, h in ((68, 84, 7, 17), (104, 84, 7, 17), (76, 81, 6, 9), (83, 80, 6, 11),
                   (90, 80, 6, 11), (97, 81, 6, 9)):
    rect(im, x - 1, y - 1, w + 2, h + 2, K)
for x, y, w, h in ((68, 84, 7, 17), (104, 84, 7, 17)):
    rect(im, x, y, w, h - 4, BONE)
    rect(im, x + 1, y + h - 4, w - 2, 2, BONE)
    rect(im, x + 2, y + h - 2, w - 4, 2, BONE)
    rect(im, x + w - 2, y, 2, h - 4, BONE2)
for x, y, w, h in ((76, 81, 6, 9), (83, 80, 6, 11), (90, 80, 6, 11), (97, 81, 6, 9)):
    rect(im, x, y, w, h, BONE)
    rect(im, x + w - 2, y, 2, h, BONE2)
    rect(im, x, y + h - 1, w, 1, BONE2)

# ---------- palm mouth: coiled throat ----------
blob(73, 92, 33, 30, DEEP, 2, 2.2)
blob(75, 94, 29, 26, RED, 2, 2.2)
blob(78, 97, 23, 20, K, 2, 2.2)
blob(79, 98, 21, 18, DEEP, 2, 2.2)
blob(81, 100, 17, 14, RED, 2, 2.2)
blob(84, 102, 11, 10, K, 2, 2.2)
blob(85, 103, 9, 8, DARK, 2, 2.2)
# breaks in the rings turn them into a coil
rect(im, 78, 103, 3, 3, RED)
rect(im, 97, 106, 4, 3, RED)
rect(im, 90, 97, 3, 3, RED)
rect(im, 84, 106, 3, 2, DEEP)
rect(im, 92, 103, 2, 2, DEEP)

# lower teeth round an off-centre tongue
for x, y, w, h in ((69, 112, 6, 10), (104, 112, 6, 10), (92, 120, 5, 6), (98, 118, 5, 6)):
    rect(im, x - 1, y - 1, w + 2, h + 1, K)
    rect(im, x, y, w, h, BONE)
    rect(im, x + w - 2, y, 2, h, BONE2)
    rect(im, x, y, w, 1, BONE2)

# ---------- tongue, off to the left, ending over the lip ----------
tongue = [(80, 110), (90, 110), (92, 116), (91, 124), (91, 132), (88, 138), (82, 140), (77, 138),
          (75, 132), (76, 124), (77, 116)]
outer = mask_of(tongue)
for x, y in outer:
    if any((x + a, y + b) not in outer for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
        dot(im, x, y, K)
inner = {(x, y) for x, y in outer
         if all((x + a, y + b) in outer for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
paint(inner, MID, DEEP, RED, d=(4, 2))
line([(84, 114), (84, 124), (83, 134)], K)
line([(80, 114), (79, 122)], LITE)
line([(78, 126), (78, 133)], LITE)

# ---------- wrist ----------
for y, x0, x1 in ((149, 73, 110), (152, 72, 112)):
    line([(x0, y), (x0 + 8, y + 1), (x1 - 8, y + 1), (x1, y)], DEEP)
line([(74, 147), (84, 148)], K)
line([(96, 148), (108, 147)], K)
rect(im, 72, 155, 41, 2, DEEP)


# ---------- fingertip mouths ----------
def fingertip(x, y, w, h):
    m = x + w // 2
    # head of the mouth, with cut corners
    rect(im, x + 3, y, w - 6, 1, RED)
    rect(im, x + 1, y + 1, w - 2, 2, RED)
    rect(im, x, y + 3, w, 11, RED)
    rect(im, x + 1, y + 14, w - 2, 2, RED)
    rect(im, x + 3, y + 1, w - 7, 1, DEEP)
    rect(im, x + 1, y + 3, 1, 9, DEEP)
    # opening with cut corners and a few chunky teeth
    rect(im, x + 4, y + 3, w - 8, 1, K)
    rect(im, x + 3, y + 4, w - 6, 8, K)
    rect(im, x + 4, y + 12, w - 8, 1, K)
    rect(im, x + 4, y + 7, w - 8, 5, DARK)
    for tx in range(x + 4, x + w - 5, 3):
        rect(im, tx, y + 4, 2, 2, BONE)
    # tongue comes out of the opening and hangs down
    tx = m - 3
    tw = 6
    rect(im, tx - 1, y + 8, tw + 2, h - 8, K)
    rect(im, tx, y + 9, tw, h - 11, DEEP)
    rect(im, tx + tw - 2, y + 10, 2, h - 12, RED)
    rect(im, tx + 1, y + 10, 1, 4, MID)
    rect(im, tx + 2, y + 13, 1, h - 21, K)
    rect(im, tx, y + h - 3, 1, 1, K)
    rect(im, tx + tw - 1, y + h - 3, 1, 1, K)


fingertip(34, 15, 15, 31)
fingertip(84, 4, 16, 30)
fingertip(123, 27, 14, 27)
fingertip(143, 53, 14, 26)

# thin thick black inside the palm mouth, so nothing reads as a black-only part
p = im.load()
thick = [(x, y) for y in range(78, 134) for x in range(64, 116)
         if p[x, y] == BLACK and sum(p[x + a, y + b] == BLACK for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 3]
for x, y in thick:
    dot(im, x, y, DARK)

# black touching the edge would double the outline
while True:
    p = im.load()
    edge = [(x, y) for y in range(H) for x in range(W) if p[x, y] == BLACK and any(
        not (0 <= x + a < W and 0 <= y + b < H) or not p[x + a, y + b][3]
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    if not edge:
        break
    for x, y in edge:
        dot(im, x, y, None)

im = outline(im)
save(im)
