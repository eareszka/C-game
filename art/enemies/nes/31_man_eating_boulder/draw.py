from pix import *

LITE, ROCK, DARK = '848694', '595965', '34343e'
MOSS, MOSD = '4fa667', '2c6c44'
BONE = 'e8e0c0'
GUM, GUT = 'b6433d', '7c0a1b'
INK = '000000'
W, H = 96, 72


def add(im, part):
    """Lay a part on, with a 1 px black line round it."""
    im.alpha_composite(outline(part), (0, 0), (1, 1, W + 1, H + 1))


def ln(im, pts, c=INK):
    ImageDraw.Draw(im).line(pts, fill=rgba(c), width=1)


def clip(part, mask):
    a, b = part.load(), mask.load()
    for y in range(H):
        for x in range(W):
            if not b[x, y][3]:
                a[x, y] = CLEAR


def tooth(p, x, base, w, h, down=True, lean=0):
    """A chunky stepped tooth: a black edge, bone, a shaded right side."""
    s = 1 if down else -1
    for i in range(h):
        t = i / h
        hw = max(int(round((w / 2) * (1 - t * t * t))), 1)
        if t > 0.8:
            hw = 0
        cx = x + w // 2 + int(round(lean * t * t))
        y = base + s * i
        rect(p, cx - hw - 1, y, hw * 2 + 3, 1, INK)
        rect(p, cx - hw, y, hw * 2 + 1, 1, BONE)
        if hw >= 3:
            rect(p, cx + hw - 1, y, 2, 1, LITE)
        elif hw == 2:
            rect(p, cx + hw, y, 1, 1, LITE)
    rect(p, x + w // 2 + int(round(lean)), base + s * h, 1, 1, INK)


im = canvas(W, H)

# ---- rubble behind, uneven and off to the right
back = canvas(W, H)
poly(back, [(73, 63), (75, 57), (81, 55), (85, 59), (86, 63)], DARK)
poly(back, [(75, 59), (78, 57), (81, 57), (77, 60)], ROCK)
add(im, back)

# ---- the boulder: a lumpy faceted mass that sits right on the ground
body = canvas(W, H)
poly(body, [(7, 34), (10, 26), (15, 22), (15, 17), (22, 12), (27, 11), (30, 7), (38, 4), (47, 5), (52, 3),
            (60, 5), (66, 9), (71, 11), (75, 17), (80, 21), (81, 27), (85, 33), (85, 44), (82, 47), (83, 52),
            (78, 58), (66, 61), (50, 63), (30, 63), (14, 61), (8, 56), (5, 46), (4, 38)], ROCK)
# shade: lower right
poly(body, [(85, 36), (85, 44), (82, 47), (83, 52), (78, 58), (66, 61), (50, 63), (30, 63), (14, 61), (30, 60),
            (50, 59), (64, 56), (72, 50), (78, 44), (80, 36)], DARK)
# lit plates on the flank
poly(body, [(68, 26), (74, 24), (79, 28), (74, 33), (68, 32)], LITE)
poly(body, [(66, 37), (72, 35), (75, 39), (70, 43), (66, 42)], LITE)
# lit upper lip, a heavy brow of stone blocks
poly(body, [(4, 38), (7, 34), (10, 26), (15, 22), (24, 18), (36, 15), (48, 16), (55, 20), (52, 22), (36, 19),
            (24, 21), (15, 26), (11, 32), (8, 40), (5, 44)], LITE)
# lit lower lip, facing up towards the light
poly(body, [(8, 46), (12, 51), (28, 53), (44, 51), (40, 54), (26, 56), (12, 54)], LITE)
add(im, body)

# cracks and plate lines
ln(im, [(68, 32), (66, 37)])
ln(im, [(74, 33), (75, 39), (80, 42)])
ln(im, [(79, 28), (84, 33)])
ln(im, [(70, 43), (66, 50), (58, 54)])
ln(im, [(72, 50), (76, 54)])
ln(im, [(15, 26), (12, 22)])
ln(im, [(36, 15), (35, 19)])
ln(im, [(8, 40), (4, 41)])
ln(im, [(20, 52), (19, 57), (22, 62)])
ln(im, [(40, 54), (43, 58), (41, 62)])
ln(im, [(58, 22), (63, 26), (63, 31)])
# more plates: chips and pits that catch the light from the upper left
ln(im, [(26, 18), (25, 21)])
ln(im, [(46, 16), (47, 20)])
ln(im, [(31, 53), (30, 57)])
ln(im, [(50, 52), (52, 57)])
poly(im, [(24, 57), (29, 57), (28, 59), (25, 59)], LITE)
poly(im, [(34, 56), (38, 56), (37, 58), (35, 58)], LITE)
poly(im, [(46, 54), (49, 54), (48, 56), (46, 56)], LITE)
poly(im, [(58, 50), (62, 49), (61, 51)], LITE)
poly(im, [(30, 60), (35, 60), (34, 61), (31, 61)], ROCK)
poly(im, [(56, 58), (61, 57), (60, 59)], ROCK)
poly(im, [(70, 54), (74, 52), (73, 54)], ROCK)
poly(im, [(79, 38), (82, 37), (83, 40), (80, 41)], ROCK)
poly(im, [(14, 56), (18, 56), (17, 58)], DARK)
poly(im, [(38, 60), (42, 60), (41, 61)], ROCK)
# blocks along the lit lips and the dark base
ln(im, [(9, 30), (12, 33)], DARK)
ln(im, [(18, 21), (20, 25)], DARK)
ln(im, [(14, 52), (13, 55)], DARK)
ln(im, [(24, 54), (23, 56)], DARK)
ln(im, [(38, 52), (39, 55)], DARK)
ln(im, [(62, 54), (64, 58)], ROCK)
ln(im, [(46, 59), (47, 62)], ROCK)
ln(im, [(31, 53), (30, 57)], DARK)
ln(im, [(50, 52), (52, 57)], DARK)
ln(im, [(26, 18), (25, 21)], DARK)
poly(im, [(66, 56), (70, 55), (69, 57)], ROCK)
poly(im, [(7, 49), (10, 50), (9, 52)], ROCK)

# ---- the mouth, wide with a grinning corner
MOUTH = [(8, 35), (12, 28), (19, 24), (30, 21), (42, 22), (51, 25), (57, 30), (61, 36), (64, 43), (56, 46),
         (44, 49), (28, 51), (15, 50), (10, 46), (7, 41)]
mask = canvas(W, H)
poly(mask, MOUTH, GUT)
m = canvas(W, H)
poly(m, MOUTH, GUT)
# gums along the top
poly(m, [(8, 35), (12, 28), (19, 24), (30, 21), (42, 22), (51, 25), (57, 30), (61, 36), (54, 33), (46, 28),
         (36, 26), (24, 28), (15, 32)], GUM)
# gullet ribs round a small throat
ln(m, [(22, 33), (26, 30), (32, 29)], GUM)
ln(m, [(38, 29), (44, 31), (47, 35)], GUM)
ln(m, [(23, 39), (20, 36), (22, 33)], GUM)
ln(m, [(47, 35), (47, 39), (44, 41)], GUM)
ln(m, [(29, 36), (33, 37), (38, 36)], INK)
ln(m, [(27, 33), (31, 32), (37, 32), (42, 33)], GUM)
ln(m, [(26, 39), (32, 40), (40, 40), (44, 38)], GUM)
# tongue
poly(m, [(17, 50), (19, 45), (26, 42), (37, 42), (46, 43), (53, 47), (44, 50), (28, 52)], GUM)
ln(m, [(26, 46), (32, 45), (40, 46)], GUT)
ln(m, [(24, 49), (28, 48)], GUT)
ln(m, [(40, 49), (44, 48)], GUT)
# lower teeth first, then the great upper fangs
for x, base, w, h in ((15, 51, 7, 11), (25, 52, 5, 7), (34, 51, 5, 6), (43, 50, 7, 11), (56, 47, 5, 5)):
    tooth(m, x, base, w, h, down=False)
for x, base, w, h, lean in ((9, 28, 9, 17, 2), (20, 23, 7, 13, 0), (29, 21, 6, 8, 0),
                            (37, 21, 7, 12, 0), (49, 24, 9, 18, -2)):
    tooth(m, x, base, w, h, lean=lean)
clip(m, mask)
add(im, m)

# ---- moss: lumpy cap with rock showing through, long uneven drapes
mo = canvas(W, H)
poly(mo, [(24, 13), (27, 8), (32, 7), (36, 2), (45, 3), (49, 1), (57, 2), (62, 5), (66, 5), (72, 9), (75, 14),
          (80, 18), (84, 25), (86, 32), (82, 33), (77, 27), (70, 22), (62, 18), (52, 13), (40, 12), (30, 14)], MOSD)
for x, y, w, b in ((25, 12, 4, 19), (31, 12, 3, 16), (36, 11, 5, 19), (51, 12, 4, 23),
                   (57, 15, 3, 21), (62, 17, 4, 31), (69, 20, 3, 27), (74, 24, 4, 36), (80, 27, 3, 40)):
    rect(mo, x, y, w, b - y, MOSD)
# clump tips that step in
rect(mo, 37, 19, 3, 2, MOSD)
rect(mo, 52, 23, 2, 3, MOSD)
rect(mo, 63, 31, 2, 3, MOSD)
rect(mo, 75, 36, 2, 3, MOSD)
# left shoulder clump
poly(mo, [(10, 23), (13, 19), (18, 15), (20, 17), (18, 21), (14, 24)], MOSD)
rect(mo, 11, 23, 3, 4, MOSD)
# lit clumps, upper left
poly(mo, [(27, 11), (30, 9), (35, 7), (39, 4), (45, 5), (43, 8), (37, 10), (31, 12)], MOSS)
poly(mo, [(49, 3), (56, 4), (61, 7), (59, 10), (54, 9), (50, 7)], MOSS)
poly(mo, [(64, 8), (70, 10), (73, 15), (68, 15)], MOSS)
poly(mo, [(75, 17), (79, 20), (82, 26), (78, 24)], MOSS)
poly(mo, [(12, 21), (17, 16), (18, 18), (14, 22)], MOSS)
poly(mo, [(41, 7), (46, 7), (47, 10), (42, 10)], MOSS)
rect(mo, 37, 13, 2, 6, MOSS)
rect(mo, 26, 14, 2, 4, MOSS)
rect(mo, 52, 12, 2, 10, MOSS)
rect(mo, 63, 19, 2, 11, MOSS)
rect(mo, 75, 26, 2, 9, MOSS)
rect(mo, 81, 29, 1, 9, MOSS)
rect(mo, 58, 16, 1, 4, MOSS)
rect(mo, 70, 21, 1, 5, MOSS)
rect(mo, 32, 13, 1, 2, MOSS)
rect(mo, 55, 12, 2, 2, MOSS)
rect(mo, 66, 17, 2, 2, MOSS)
rect(mo, 40, 11, 2, 1, MOSS)
add(im, mo)
# clump lines in the moss
ln(im, [(47, 4), (48, 11)])
ln(im, [(62, 8), (60, 14)])
ln(im, [(35, 10), (33, 12)])
ln(im, [(73, 12), (72, 19)])
ln(im, [(40, 11), (44, 12)])
ln(im, [(55, 5), (54, 9)])
ln(im, [(28, 12), (30, 13)])
ln(im, [(78, 22), (81, 25)])
ln(im, [(66, 11), (68, 14)])

# moss patches lower on the flank
pa = canvas(W, H)
poly(pa, [(72, 44), (78, 41), (84, 44), (83, 49), (79, 49), (77, 54), (75, 50), (72, 49)], MOSD)
poly(pa, [(74, 44), (78, 42), (81, 44), (76, 46)], MOSS)
add(im, pa)

# ---- eyes: one solid bone mark each, set on mid rock
rect(im, 42, 14, 7, 3, ROCK)
rect(im, 22, 17, 2, 1, BONE)
rect(im, 44, 15, 2, 1, BONE)

# ---- rubble in front, uneven
fr = canvas(W, H)
poly(fr, [(3, 65), (3, 59), (8, 56), (13, 60), (14, 65)], ROCK)
poly(fr, [(3, 61), (7, 57), (9, 59), (5, 63)], LITE)
poly(fr, [(14, 65), (10, 65), (12, 61)], DARK)
poly(fr, [(16, 65), (18, 62), (22, 62), (24, 65)], DARK)
poly(fr, [(46, 65), (48, 60), (54, 59), (59, 62), (60, 65)], ROCK)
poly(fr, [(48, 62), (52, 60), (54, 61), (50, 63)], LITE)
poly(fr, [(60, 65), (56, 65), (58, 62)], DARK)
add(im, fr)
# moss on the rubble
sp = canvas(W, H)
poly(sp, [(4, 57), (8, 54), (10, 56), (6, 59)], MOSD)
rect(sp, 6, 55, 2, 1, MOSS)
add(im, sp)

im = strip_outline(im)
im = outline(im)
save(im)
