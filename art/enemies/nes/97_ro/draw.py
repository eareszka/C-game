from pix import *

DK = '292931'   # hide shadow, dark membrane
HD = '474751'   # hide
LT = '848694'   # lit edges, the lighter charcoal
RD = 'b70000'   # eyes, mouth, veins
DR = '7c0a1b'   # deep mouth, inner ear
CR = 'e8e0c0'   # teeth, claws
K = '000000'

im = canvas(87, 62)
d = ImageDraw.Draw(im)
C = 43


def mx(x):
    return 2 * C - x


def pm(pts, c, c2=None):
    poly(im, pts, c)
    poly(im, [(mx(x), y) for x, y in pts], c2 or c)


def ln(pts, c, c2=None):
    d.line(pts, fill=rgba(c))
    d.line([(mx(x), y) for x, y in pts], fill=rgba(c2 or c))


def dm(x, y, c, c2=None):
    dot(im, x, y, c)
    dot(im, mx(x), y, c2 or c)


# ---- tail, behind everything, sweeping off the right hip
poly(im, [(50, 48), (56, 49), (62, 53), (70, 54), (76, 52), (80, 48), (81, 43), (84, 48),
          (83, 52), (77, 57), (69, 59), (60, 58), (53, 55)], HD)
poly(im, [(55, 56), (60, 58), (69, 59), (77, 57), (83, 52), (83, 50), (77, 55), (69, 57), (60, 56)], DK)
for x, y0, y1 in ((59, 51, 55), (64, 54, 57), (69, 55, 58), (74, 53, 57)):
    d.line([(x, y0), (x, y1)], fill=rgba(K))
d.line([(78, 51), (80, 53)], fill=rgba(K))
d.line([(80, 45), (79, 48)], fill=rgba(LT))

# ---- wings: panels step from the wrist down to scalloped tips
A = (16, 3)
T1, S12, T2, S23, T3, S34, T4 = (0, 39), (6, 31), (8, 47), (13, 32), (16, 43), (20, 29), (29, 24)
pm([A, (10, 9), (4, 21), (1, 31), T1, (4, 34), S12], HD)
pm([A, S12, (7, 38), T2, (11, 37), S23], DK)
pm([A, S23, (15, 37), T3, (18, 34), S34], HD)
pm([A, S34, (25, 27), T4, (34, 20), (25, 13)], DK)

# one red vein down the middle of each panel
ln([(13, 12), (4, 30)], RD)
ln([(14, 13), (9, 30), (9, 37)], RD)
ln([(17, 13), (15, 30), (15, 37)], RD)
ln([(20, 12), (23, 22)], RD)

# finger bones, lit on the upper side, black on the shaded side
ln([A, T2], LT, HD)
ln([(A[0] + 1, A[1] + 1), (T2[0] + 1, T2[1] - 1)], K)
ln([A, T3], LT, HD)
ln([(A[0] + 1, A[1] + 1), (T3[0] + 1, T3[1] - 1)], K)
ln([A, T1], LT, HD)

# wing arm: shoulder, elbow, wrist
pm([(34, 25), (25, 15), (16, 3), (18, 3), (28, 13), (37, 21)], HD)
ln([(16, 3), (25, 14), (31, 19)], LT, HD)
ln([(33, 25), (25, 17), (18, 7)], K)
# wrist hook
for x, y in ((14, 0), (15, 0), (15, 1), (16, 1), (16, 2)):
    dm(x, y, CR)

# ---- legs: wide stance with a gap under the belly
oval(im, 24, 44, 15, 12, HD)
oval(im, 48, 44, 15, 12, HD)
ln([(26, 47), (29, 45), (33, 45)], LT, HD)
pm([(30, 55), (38, 50), (38, 55)], DK)
pm([(22, 54), (36, 54), (36, 57), (22, 57)], HD)
ln([(22, 54), (29, 54)], LT, HD)
ln([(22, 57), (36, 57)], DK)
for x in (26, 31):
    ln([(x, 54), (x, 57)], K)
for x in (22, 27, 32):
    pm([(x, 58), (x + 2, 58), (x + 1, 60)], CR)

# ---- torso and belly plates
pm([(43, 26), (33, 26), (34, 42), (38, 53), (43, 54)], HD)
pl = [(32, 8), (36, 8), (40, 7), (44, 6), (48, 5)]
for i, (y, hw) in enumerate(pl):
    rect(im, C - hw, y, hw * 2 + 1, 3, HD)
    rect(im, C + hw - 2, y, 3, 3, DK)
    d.line([(C - hw, y), (C - 1, y)], fill=rgba(LT))
    d.line([(C - hw, y + 3), (C + hw, y + 3)], fill=rgba(K))
    dot(im, C - hw - 1, y + 1, K)
    dot(im, C + hw + 1, y + 1, K)
rect(im, 40, 52, 7, 2, DK)

# ---- arms: elbows out, hands turned in at the hips
pm([(32, 26), (25, 30), (21, 36), (23, 42), (27, 47), (33, 47), (32, 43), (27, 37), (31, 33), (35, 32)], HD)
ln([(30, 27), (25, 31), (22, 36)], LT, HD)
ln([(28, 35), (25, 38), (28, 43)], DK)
pm([(26, 44), (33, 44), (34, 47), (27, 47)], HD)
ln([(26, 44), (31, 44)], LT, HD)
ln([(27, 48), (34, 48)], K)
for x in (28, 31):
    ln([(x, 45), (x, 47)], K)
for x in (27, 30, 33):
    ln([(x, 49), (x + 1, 51)], CR)

# ---- spiked ruff round the neck, black line separating it from the wings
RUFF = [(43, 8), (33, 8), (31, 12), (26, 10), (28, 16), (21, 16), (27, 21), (20, 25), (28, 26),
        (25, 32), (32, 29), (32, 35), (38, 30), (40, 36), (43, 32)]
pm(RUFF, HD)
d.line(RUFF + [RUFF[0]], fill=rgba(K))
d.line([(mx(x), y) for x, y in RUFF + [RUFF[0]]], fill=rgba(K))
pm(RUFF[:1] + [(36, 9), (35, 12), (30, 14), (31, 19), (28, 23), (31, 26), (33, 29), (38, 28), (43, 30)], HD)
for a, b in (((27, 11), (30, 13)), ((22, 17), (27, 18)), ((21, 25), (26, 23)), ((26, 31), (29, 27))):
    ln([a, b], LT, HD)
for a, b in (((28, 15), (33, 18)), ((28, 21), (33, 23)), ((29, 26), (34, 26)), ((33, 33), (36, 29))):
    ln([a, b], DK)

# ---- head with ears
pm([(34, 13), (31, 2), (40, 8)], HD)
pm([(35, 10), (33, 6), (38, 9)], DK)
ln([(31, 2), (33, 10)], LT, HD)
pm([(43, 7), (37, 7), (34, 10), (33, 16), (34, 21), (36, 25), (38, 29), (40, 32), (43, 32)], HD)
d.line([(38, 7), (43, 7)], fill=rgba(LT))
d.line([(36, 8), (35, 10), (34, 14)], fill=rgba(LT))
# shade down the right of the face
poly(im, [(53, 10), (53, 16), (52, 21), (50, 25), (48, 29), (46, 32), (47, 28), (49, 22), (51, 16)], DK)
# brows and eyes
pm([(35, 12), (41, 15), (41, 17), (37, 16)], K)
dm(38, 14, RD)
dm(39, 15, RD)
# forehead crease and lit brow ridge
d.line([(43, 8), (43, 13)], fill=rgba(DK))
ln([(39, 10), (41, 12)], DK)
ln([(36, 11), (40, 13)], LT, HD)
# muzzle: lit bridge and black nose
d.line([(41, 13), (41, 17)], fill=rgba(LT))
ln([(38, 19), (41, 18)], K)
rect(im, 42, 17, 3, 2, K)
# mouth
pm([(43, 20), (37, 20), (37, 25), (39, 29), (43, 30)], K)
pm([(43, 21), (38, 21), (38, 25), (40, 28), (43, 29)], RD)
rect(im, 41, 24, 5, 3, DR)
rect(im, 42, 26, 3, 2, RD)
for x, y in ((38, 21), (39, 21), (38, 22), (39, 22), (38, 23), (39, 23), (39, 24)):
    dm(x, y, CR)
dm(41, 21, CR)
dot(im, 43, 21, CR)
dm(40, 28, CR)
dm(40, 27, CR)
dm(40, 26, CR)
dm(41, 28, CR)

im = outline(im)
save(im)
