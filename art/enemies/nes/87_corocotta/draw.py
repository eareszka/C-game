from pix import *
import pix

L, M, D, H = 'a4aaba', '848694', '595965', '474751'
R, P, W, Y = 'b70000', 'ec8476', 'e8e0c0', 'f0bc3c'
K = '000000'

im = canvas(66, 64)
pen = ImageDraw.Draw(im)
OX = 0  # the head and forelegs are drawn further right than the back


def at(pts):
    return [(x + OX, y) for x, y in pts]


def line(pts, c):
    pen.line(at(pts), fill=rgba(c))


def part(pts, c):
    pen.polygon(at(pts), fill=rgba(c), outline=BLACK)


def fill(pts, c):
    pix.poly(im, at(pts), c)


def px(x, y, c):
    pix.dot(im, x + OX, y, c)


def leg(x, top, foot):
    """A long foreleg: broad shoulder, 5 px shin, wrist knob, clawed paw on y=foot."""
    fill([(x, top), (x + 8, top), (x + 7, top + 7), (x + 6, top + 10), (x + 6, foot - 4),
          (x + 8, foot - 2), (x + 8, foot), (x - 1, foot), (x - 1, foot - 2),
          (x + 2, foot - 4), (x + 2, top + 10), (x + 1, top + 7)], M)
    line([(x + 2, top + 2), (x + 3, top + 8), (x + 2, top + 11), (x + 2, foot - 5)], L)
    line([(x + 6, top + 3), (x + 5, top + 9), (x + 6, top + 11), (x + 6, foot - 4)], D)
    line([(x + 3, foot - 6), (x + 5, foot - 6)], D)
    line([(x + 4, foot - 2), (x + 8, foot - 2)], D)
    line([(x + 4, foot - 1), (x + 8, foot - 1)], D)
    for i in (x + 1, x + 4, x + 7):
        px(i, foot - 1, K)
    for i in (x, x + 3, x + 6):
        px(i, foot, W)


# --- the back: far hind leg, barrel and mane, stretched out to the left ---
# short hind leg, set back, so the back slopes down to it
fill([(3, 36), (13, 38), (12, 45), (10, 48), (10, 52), (13, 54), (13, 56), (3, 56), (3, 54),
      (6, 52), (6, 47), (3, 43)], D)
line([(6, 40), (7, 46)], M)
line([(7, 49), (9, 49)], K)
for i in (5, 8, 11):
    px(i, 55, K)
for i in (3, 6, 9, 12):
    px(i, 56, W)

# barrel, falling from high shoulders to a low rump
fill([(35, 14), (6, 28), (2, 35), (5, 42), (14, 46), (39, 44), (43, 22)], M)
fill([(3, 37), (6, 41), (14, 45), (38, 43), (38, 39), (20, 41), (8, 38)], D)
line([(5, 42), (14, 46), (20, 46)], K)
# dark flank stripes
line([(8, 34), (9, 37)], K)
line([(12, 33), (13, 37)], K)
line([(16, 32), (17, 38)], K)
line([(5, 33), (5, 35)], D)
line([(10, 37), (11, 40)], D)
line([(14, 38), (15, 41)], D)

# bristling mane down the sloped back, one saw-edged mass
part([(42, 11), (38, 1), (34, 10), (30, 1), (27, 12), (23, 7), (20, 16), (15, 10), (13, 21),
      (8, 15), (8, 26), (2, 23), (3, 31), (7, 32), (10, 28), (14, 30), (17, 26), (21, 28),
      (25, 22), (28, 25), (38, 20)], H)
for a, b in (((38, 10), (38, 4)), ((31, 11), (30, 4)), ((23, 14), (23, 10)), ((16, 17), (15, 13)),
             ((9, 22), (9, 18)), ((5, 27), (4, 25))):
    line([a, b], D)
for a, b in (((12, 24), (13, 27)), ((18, 20), (20, 25)), ((24, 16), (26, 20))):
    line([a, b], D)
for a, b in (((34, 11), (34, 15)), ((27, 13), (27, 17)), ((20, 17), (20, 20)), ((13, 22), (13, 24))):
    line([a, b], K)

# --- the front: forelegs, ruff and head ---
OX = 5

leg(14, 36, 58)
leg(32, 38, 58)
line([(14, 37), (16, 46)], K)

# ruff round the neck, under the head
part([(18, 17), (9, 21), (14, 26), (7, 31), (14, 33), (10, 41), (18, 39), (17, 49), (23, 43),
      (27, 51), (30, 45), (34, 50), (36, 44), (38, 42), (36, 24)], H)
for a, b in (((17, 23), (11, 22)), ((17, 30), (10, 31)), ((18, 36), (13, 40)),
             ((23, 39), (19, 46)), ((27, 42), (27, 48)), ((33, 42), (34, 47))):
    line([a, b], D)
for a, b in (((19, 28), (16, 28)), ((20, 35), (17, 35)), ((24, 41), (22, 43)), ((30, 42), (30, 44))):
    line([a, b], K)

# ears
part([(18, 20), (14, 4), (28, 13)], M)
fill([(20, 17), (17, 9), (25, 14)], H)
line([(15, 5), (18, 16)], L)
part([(36, 13), (48, 2), (45, 21)], M)
fill([(39, 13), (46, 7), (44, 17)], H)
line([(37, 13), (47, 3)], L)

# skull with jagged cheek fur
part([(18, 19), (24, 12), (36, 12), (44, 18), (45, 25), (41, 30), (30, 32), (24, 32),
      (22, 29), (15, 30), (19, 27), (14, 25), (18, 23)], M)
fill([(19, 19), (24, 13), (34, 13), (29, 16), (24, 18), (21, 23), (19, 23)], L)
fill([(20, 25), (24, 27), (30, 31), (24, 31), (22, 28)], D)
fill([(44, 25), (40, 29), (39, 25)], D)

# open red jaws
part([(24, 30), (32, 30), (45, 38), (42, 45), (34, 45), (28, 38)], R)
fill([(30, 36), (33, 37), (37, 40), (39, 43), (36, 44), (32, 41)], P)
line([(33, 39), (36, 42)], R)

# lower jaw
part([(22, 29), (26, 30), (30, 38), (35, 44), (43, 44), (43, 47), (34, 48), (28, 43)], M)
line([(25, 32), (29, 41), (35, 46)], L)
line([(33, 47), (42, 46)], D)

# upper muzzle, thrusting down and right; only the jaw side is inked
fill([(29, 19), (37, 19), (43, 26), (51, 32), (51, 37), (44, 39), (36, 33), (30, 27)], M)
fill([(32, 20), (36, 20), (42, 27), (47, 31), (44, 32), (38, 27)], L)
fill([(31, 26), (35, 28), (45, 36), (44, 38), (36, 32)], D)
line([(30, 27), (36, 33), (44, 39)], K)
part([(45, 32), (52, 31), (53, 35), (50, 38), (45, 36)], H)
px(47, 33, L)
px(48, 33, L)

# teeth: placed one by one so red shows between them
for x, y in ((41, 39), (42, 39), (41, 40), (42, 40), (41, 41)):      # big upper fang
    px(x, y, W)
for x, y in ((36, 35), (37, 35), (36, 36)):                          # smaller upper tooth
    px(x, y, W)
for x, y in ((38, 43), (39, 43), (39, 42)):                          # lower fang
    px(x, y, W)

# brows and eyes
line([(23, 20), (28, 23)], K)
line([(44, 19), (39, 22)], K)
fill([(25, 23), (26, 23)], Y)
fill([(40, 22), (41, 22)], Y)
line([(30, 15), (31, 18)], K)

im = strip_outline(im)
im = outline(im)
save(im)
