from pix import *
from math import cos, sin, radians

PD = '3b2a58'  # robe shade
PM = '664b95'  # robe light, axe shade
PL = 'b69cee'  # axe light
AD = '474751'  # armour
AL = '848694'  # armour light
BN = 'e8e0c0'  # bone, feather
TN = 'b2966a'  # bone shade, trim
GR = '058f3a'  # crest band
K = '000000'

OX, OY = 4, 4
im = canvas(140, 110)
d = ImageDraw.Draw(im)


def sh(pts):
    return [(x + OX, y + OY) for x, y in pts]


def fill(pts, c):
    d.polygon(sh(pts), fill=rgba(c))


def part(pts, c):
    p = sh(pts)
    d.polygon(p, fill=rgba(c))
    d.line(p + [p[0]], fill=BLACK)


def line(pts, c=K):
    d.line(sh(pts), fill=rgba(c))


def box(x, y, w, h, c):
    rect(im, x + OX, y + OY, w, h, c)


def px(x, y, c=K):
    dot(im, x + OX, y + OY, c)


def feather(bx, by, tx, ty, w, c, base):
    dx, dy = tx - bx, ty - by
    n = (dx * dx + dy * dy) ** 0.5
    nx, ny = -dy / n, dx / n

    def at(t, off):
        return (round(bx + dx * t + nx * off), round(by + dy * t + ny * off))

    part([at(0, 1.5), at(.6, w), at(.88, w * .75), at(1, 0), at(.88, -w * .75), at(.6, -w), at(0, -1.5)], c)
    if base:
        fill([at(.3, 1), at(.55, w - 1), at(.55, -w + 1), at(.3, -1)], base)
        line([at(.55, 0), at(.84, 0)], base)
        line([at(.6, w - 1), at(.84, w * .6)], base)


# ---------- legs (mirrored about x=75, lit from the left on both)
for s in (-1, 1):
    def X(v):
        return 75 + s * v
    # thigh
    part([(X(10), 68), (X(27), 68), (X(30), 76), (X(27), 83), (X(13), 83), (X(10), 76)], AD)
    # knee and shin
    part([(X(12), 82), (X(25), 82), (X(26), 87), (X(23), 90), (X(14), 90), (X(11), 87)], AD)
    # foot
    part([(X(9), 89), (X(27), 89), (X(30), 93), (X(30), 97), (X(7), 97), (X(7), 93)], AD)
    for t in (14, 20, 26):
        line([(X(t), 93), (X(t), 97)])
    # purple strap round the thigh
    line([(X(11), 71), (X(14), 81), (X(27), 81)], PM)
for x0 in (50, 89):
    # thigh, knee and toe lights
    fill([(x0 - 2, 70), (x0 + 5, 70), (x0 + 2, 72), (x0 - 3, 73)], AL)
    fill([(x0 + 1, 84), (x0 + 9, 84), (x0 + 8, 86), (x0, 86)], AL)
    box(x0 - 4, 91, 19, 1, AL)
    for t in (-4, 3, 9, 15):
        box(x0 + t, 94, 3, 1, AL)

# ---------- banded forearm (viewer's right), stacked plates, clear of the leg
part([(104, 50), (118, 48), (124, 56), (114, 64), (108, 62)], AD)
part([(107, 60), (122, 53), (130, 60), (130, 67), (109, 69)], AD)
part([(108, 67), (129, 63), (133, 70), (132, 76), (110, 76)], AD)
part([(110, 74), (131, 72), (132, 80), (127, 85), (112, 85)], AD)
fill([(109, 61), (121, 55), (123, 57), (110, 64)], AL)
fill([(110, 68), (128, 65), (129, 67), (111, 71)], AL)
fill([(112, 75), (130, 74), (130, 75), (113, 78)], AL)
box(124, 59, 3, 1, TN)
box(127, 68, 2, 1, TN)
for x, y in ((116, 72), (122, 81), (114, 81)):
    px(x, y, AL)
# claws, curled inward
part([(110, 84), (116, 84), (117, 89), (113, 93), (109, 92), (112, 88)], AD)
part([(116, 84), (121, 84), (122, 90), (118, 96), (114, 94), (117, 89)], AD)
part([(121, 84), (126, 83), (128, 90), (124, 96), (120, 95), (122, 90)], AD)
part([(127, 82), (131, 78), (133, 85), (130, 92), (128, 89)], AD)
line([(112, 85), (114, 85), (115, 88)], AL)
line([(117, 85), (119, 85), (120, 89)], AL)
line([(122, 85), (124, 85), (126, 90)], AL)
line([(128, 83), (130, 81), (131, 86)], AL)
box(110, 91, 2, 1, AL)
box(115, 93, 2, 1, AL)
box(121, 94, 2, 1, AL)

# ---------- arm reaching to the haft
part([(52, 48), (58, 56), (46, 72), (34, 72), (30, 62)], AD)
line([(34, 62), (50, 50)], AL)
line([(35, 66), (54, 53)])
line([(37, 68), (53, 56)], AL)
line([(38, 71), (55, 58)])

# ---------- pauldrons
part([(52, 30), (56, 20), (61, 32)], AL)
part([(106, 28), (113, 18), (114, 32)], AL)
line([(54, 28), (56, 23)], BN)
PA = [(37, 38), (42, 31), (50, 28), (58, 29), (64, 36), (64, 47), (58, 52), (46, 54), (38, 50)]
PB = [(89, 36), (94, 29), (102, 26), (110, 27), (116, 36), (116, 48), (110, 55), (96, 55), (90, 50)]
part(PA, AD)
part(PB, AD)
fill([(40, 38), (44, 33), (50, 31), (54, 32), (50, 36), (44, 40), (42, 44)], AL)
fill([(92, 37), (96, 32), (102, 29), (106, 30), (102, 34), (96, 38), (94, 42)], AL)
for o, w in ((0, 0), (52, 2)):
    line([(38 + o, 45), (48 + o, 48), (63 + o + w, 41)])
    line([(40 + o, 49), (48 + o, 51), (59 + o + w, 47)], AL)
    px(43 + o, 44, AL)
    px(50 + o, 44, AL)
    px(57 + o, 41, AL)
# worn tan scars
box(53, 38, 4, 1, TN)
box(51, 39, 3, 1, TN)
box(104, 37, 5, 1, TN)
box(102, 38, 4, 1, TN)
box(106, 34, 1, 3, TN)

# ---------- robe, centre fringe first
strips = ((60, 86, PD), (64, 92, PM), (68, 88, PD), (72, 94, PM), (76, 89, PD), (80, 93, PM), (84, 87, PD), (88, 84, PM))
for x, end, c in strips:
    part([(x, 70), (x + 4, 70), (x + 4, end - 2), (x + 2, end), (x, end - 2)], c)

# side drapes hanging over the hips, torn ends
for x, end, c in ((52, 80, PM), (56, 84, PD), (90, 83, PD), (94, 79, PM)):
    part([(x, 60), (x + 4, 60), (x + 4, end - 2), (x + 2, end), (x, end - 2)], c)

# chest, wider than the collar, stepped down the sides
part([(58, 38), (92, 38), (97, 48), (100, 56), (100, 66), (94, 72), (92, 76), (58, 76), (56, 72), (50, 66), (50, 56), (53, 48)], PD)
line([(57, 41), (52, 52), (52, 64)], PM)
for x0, x1, y0, y1 in ((55, 55, 52, 68), (59, 60, 50, 72), (91, 90, 50, 72), (95, 95, 52, 68)):
    line([(x0, y0), (x1, y1)], PM)
for x0, x1, y0, y1 in ((57, 58, 50, 70), (93, 92, 50, 70)):
    line([(x0, y0), (x1, y1)])
# cord ends on the chest
for x, y in ((55, 69), (59, 73), (90, 73), (95, 69)):
    box(x - 1, y, 3, 1, TN)

# tan curl on each thigh, opening outward
for x, s in ((47, 1), (103, -1)):
    box(x if s > 0 else x - 5, 74, 6, 2, TN)
    box(x + 4 * s if s > 0 else x - 5, 75, 2, 5, TN)
    box(x + 1 if s > 0 else x - 5, 79, 5, 2, TN)
    box(x + 1 if s > 0 else x - 1, 78, 1, 1, TN)

# waist armour, framed in purple
part([(62, 64), (88, 64), (90, 74), (82, 80), (68, 80), (60, 74)], AD)
line([(63, 66), (73, 66)], AL)
line([(61, 70), (89, 70)])
line([(62, 72), (72, 72)], AL)
for x in (67, 83):
    line([(x, 65), (x, 69)])
line([(62, 75), (68, 79), (82, 79), (88, 75)], PM)
part([(70, 69), (80, 69), (80, 76), (75, 81), (70, 76)], AL)
part([(72, 71), (78, 71), (78, 75), (75, 78), (72, 75)], PM)

# hood rings and pendant
for o, c in ((0, PM), (3, K), (6, PM), (9, K)):
    line([(60 + o // 2, 46 + o), (68, 54 + o), (82, 54 + o), (90 - o // 2, 46 + o)], c)
line([(62, 38), (58, 46)], PM)
line([(88, 38), (92, 46)], PM)
part([(75, 57), (79, 61), (75, 65), (71, 61)], GR)
box(74, 60, 2, 1, BN)

# ---------- crest, over the pauldrons and behind the head
C = (75, 38)
for tx, ty in ((44, 16), (53, 6), (63, 1), (87, 1), (97, 6), (106, 16)):
    feather(C[0], C[1], tx, ty, 2, AD, AL)
part([(75, 0), (71, 16), (79, 16)], AD)
line([(74, 3), (73, 13)], AL)
box(72, 8, 6, 1, TN)
for tx, ty in ((45, 26), (49, 15), (57, 7), (67, 3), (83, 3), (93, 7), (101, 15), (105, 26)):
    feather(C[0], C[1], tx, ty, 4, BN, TN)

# green band, chunky radial blocks hugging the brow
angs = [(-176, -152), (-150, -126), (-124, -102), (-100, -80), (-78, -56), (-54, -30), (-28, -4)]
for a0, a1 in angs:
    r0, r1 = 12, 16
    pts = []
    for r, a in ((r0, a0), (r1, a0), (r1, (a0 + a1) / 2), (r1, a1), (r0, a1), (r0, (a0 + a1) / 2)):
        pts.append((round(75 + r * 1.15 * cos(radians(a))), round(36 + r * sin(radians(a)))))
    part(pts, GR)
part([(73, 13), (77, 13), (78, 20), (72, 20)], GR)

# ---------- bone mask, broad brow and pointed chin
M = [(67, 29), (72, 27), (79, 27), (84, 29), (86, 34), (86, 40), (84, 45), (80, 50), (78, 52), (73, 52), (71, 50), (67, 45), (65, 40), (65, 34)]
part(M, BN)
fill([(84, 33), (85, 35), (85, 40), (83, 44), (79, 49), (76, 52), (75, 51), (78, 47), (82, 42)], TN)
line([(69, 37), (73, 40)], TN)
line([(82, 37), (78, 40)], TN)
box(71, 41, 2, 2, K)
box(78, 41, 2, 2, K)
box(75, 44, 1, 4, TN)
px(73, 49, TN)
px(77, 49, TN)

# ---------- axe blade
B = [(23, 0), (15, 2), (9, 6), (5, 11), (2, 17), (0, 24), (0, 32), (2, 38), (5, 44), (9, 49), (15, 54), (23, 58),
     (22, 50), (21, 44), (25, 37), (28, 34), (28, 18), (25, 15), (21, 9), (22, 4)]
part(B, PM)
fill([(20, 1), (15, 3), (10, 7), (6, 12), (3, 18), (1, 24), (1, 32), (3, 38), (6, 43), (10, 48), (15, 53), (19, 55),
     (13, 44), (10, 36), (9, 28), (10, 20), (13, 12), (18, 5)], PL)
for pts in (((17, 6), (20, 12), (17, 19), (21, 25)),
            ((12, 18), (16, 22), (13, 28), (18, 33)),
            ((14, 44), (18, 40), (16, 34)),
            ((17, 50), (20, 45))):
    line(list(pts))
fill([(21, 12), (25, 17), (26, 24), (21, 24), (19, 19)], PD)
fill([(19, 35), (25, 33), (24, 37), (20, 43)], PD)

# ---------- haft
part([(29, 3), (26, 14), (34, 14), (31, 3)], AD)
line([(29, 5), (28, 13)], AL)
part([(28, 14), (33, 14), (33, 84), (28, 84)], AD)
line([(29, 15), (29, 83)], AL)
for y in (40, 48, 76, 81):
    box(28, y, 6, 1, K)
# socket
part([(25, 16), (36, 16), (37, 24), (36, 36), (25, 36), (24, 24)], AD)
fill([(26, 17), (30, 17), (30, 35), (26, 35)], AL)
line([(25, 22), (36, 22)])
line([(25, 30), (36, 30)])
px(33, 19, AL)
px(33, 26, AL)
px(33, 33, AL)
# pommel
oval(im, 26 + OX, 85 + OY, 10, 10, rgba(AD))
d.arc(sh([(26, 85), (35, 94)]), 0, 360, fill=BLACK)
box(28, 87, 2, 3, AL)
box(30, 87, 2, 1, AL)

# ---------- hand on the haft
part([(22, 60), (28, 57), (38, 58), (40, 64), (38, 72), (26, 73), (22, 68)], AD)
for y in (60, 64, 68):
    line([(23, y + 3), (38, y + 3)])
    line([(24, y + 1), (34, y + 1)], AL)

im = strip_outline(im)
im = outline(im)
save(im)
