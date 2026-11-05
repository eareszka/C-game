from pix import *
# Chipekwe, head-on. Parts and where they attach:
# - hind legs: come out from under the body's lower corners, behind the front legs, feet higher up
# - body: wide deep barrel, behind everything but the hind legs
# - front legs: hang from the body's shoulders, in front of it, big clawed feet on the ground
# - jaw: hangs below the muzzle, hooked tip
# - ears: at the head's upper corners
# - head: sits on the chest in the middle of the body, short neck hidden behind it
# - horn: rises from the top of the muzzle, up over the forehead

H = '848694'  # hide
S = '595965'  # hide shadow
P = 'e8e0c0'  # horn and claw
Q = 'b29e5c'  # horn and claw shadow
M = '792727'  # mouth

W, T = 86, 84
im = canvas(W + 2, T + 2)

# hind legs
p = canvas(W, T)
poly(p, [(2, 52), (16, 52), (16, 66), (18, 72), (18, 77), (0, 77), (0, 71), (3, 64)], S)
poly(p, [(83, 52), (69, 52), (69, 68), (67, 72), (67, 77), (85, 77), (85, 73), (82, 67)], S)
poly(p, [(2, 73), (6, 73), (6, 76), (4, 78), (3, 76)], Q)
poly(p, [(79, 74), (84, 73), (83, 76), (81, 78), (80, 76)], Q)
stamp(im, outline(p), 0, 0)

# body
p = canvas(W, T)
poly(p, [(11, 24), (20, 18), (31, 15), (56, 14), (66, 18), (76, 25), (81, 34), (83, 42), (85, 49), (84, 56), (82, 62), (78, 67), (7, 66), (2, 60), (0, 54), (1, 46), (2, 39), (5, 31)], H)
poly(p, [(66, 18), (76, 25), (81, 34), (83, 42), (85, 49), (84, 56), (82, 62), (78, 67), (60, 67), (67, 59), (71, 51), (75, 41), (71, 29)], S)
poly(p, [(2, 60), (7, 66), (60, 67), (60, 64), (30, 63), (8, 61)], S)
poly(p, [(30, 50), (55, 50), (58, 58), (52, 67), (33, 66), (27, 58)], S)
stamp(im, outline(p), 0, 0)

# front legs
p = canvas(W, T)
poly(p, [(15, 46), (33, 46), (35, 55), (34, 64), (36, 71), (38, 75), (38, 81), (9, 81), (9, 77), (12, 72), (14, 64), (12, 56)], H)
poly(p, [(33, 46), (35, 55), (34, 64), (36, 71), (38, 75), (38, 81), (32, 81), (30, 72), (29, 60)], S)
poly(p, [(70, 46), (52, 46), (50, 54), (51, 63), (49, 70), (47, 76), (47, 81), (76, 81), (76, 76), (73, 71), (71, 62), (73, 53)], H)
poly(p, [(70, 46), (73, 53), (71, 62), (73, 71), (76, 76), (76, 81), (69, 81), (66, 71), (65, 58)], S)
rect(p, 17, 63, 7, 1, S)
rect(p, 55, 65, 5, 1, S)
# claws, front left
poly(p, [(11, 76), (16, 76), (16, 79), (14, 82), (12, 80)], P)
poly(p, [(20, 77), (26, 77), (26, 80), (23, 82), (21, 80)], P)
poly(p, [(30, 75), (35, 75), (36, 79), (34, 82), (31, 79)], P)
rect(p, 16, 77, 1, 2, Q)
poly(p, [(25, 78), (26, 78), (26, 80), (24, 81)], Q)
poly(p, [(34, 76), (35, 76), (36, 79), (34, 81)], Q)
# claws, front right
poly(p, [(49, 76), (53, 78), (54, 80), (52, 82), (50, 80)], P)
poly(p, [(57, 74), (64, 76), (64, 79), (60, 82), (58, 78)], P)
poly(p, [(67, 78), (74, 75), (75, 78), (73, 82), (70, 80)], P)
rect(p, 53, 79, 1, 1, Q)
poly(p, [(63, 76), (64, 76), (64, 79), (61, 81)], Q)
poly(p, [(73, 76), (74, 76), (75, 78), (73, 81)], Q)
stamp(im, outline(p), 0, 0)

# let the leg tops melt into the shoulders
p = canvas(W, T)
rect(p, 14, 45, 19, 3, H)
rect(p, 52, 45, 18, 3, H)
stamp(im, p, 1, 1)

# jaw
p = canvas(W, T)
poly(p, [(34, 47), (51, 47), (50, 54), (47, 58), (44, 60), (43, 63), (40, 65), (40, 61), (37, 58), (35, 54)], H)
poly(p, [(44, 47), (51, 47), (50, 54), (47, 58), (44, 60), (43, 63), (41, 64)], S)
poly(p, [(38, 53), (48, 53), (47, 55), (39, 55)], M)
stamp(im, outline(p), 0, 0)

# ears
p = canvas(W, T)
poly(p, [(23, 20), (12, 10), (9, 17), (14, 27), (22, 28)], H)
poly(p, [(13, 16), (20, 21), (20, 26), (16, 25)], S)
poly(p, [(62, 19), (74, 12), (75, 18), (70, 25), (63, 29)], S)
stamp(im, outline(p), 0, 0)

# head
p = canvas(W, T)
poly(p, [(27, 14), (36, 12), (50, 12), (58, 14), (62, 19), (63, 27), (60, 34), (58, 38), (60, 42), (59, 47), (54, 51), (46, 52), (36, 52), (29, 50), (26, 46), (25, 41), (27, 37), (24, 33), (22, 25), (23, 18)], H)
poly(p, [(58, 14), (62, 19), (63, 27), (60, 34), (58, 38), (60, 42), (59, 47), (54, 51), (46, 52), (47, 49), (52, 46), (53, 40), (52, 36), (55, 30), (57, 21)], S)
poly(p, [(30, 49), (38, 48), (47, 49), (46, 52), (36, 52)], S)
# eyes
rect(p, 32, 25, 1, 2, BLACK)
rect(p, 53, 25, 1, 2, BLACK)
# nostrils
rect(p, 33, 43, 2, 1, BLACK)
rect(p, 50, 43, 2, 1, BLACK)
stamp(im, outline(p), 0, 0)

# horn
p = canvas(W, T)
poly(p, [(37, 37), (42, 39), (48, 38), (46, 28), (45, 18), (43, 8), (41, 0), (41, 6), (40, 16), (39, 26)], P)
poly(p, [(43, 39), (48, 38), (46, 28), (45, 18), (43, 8), (43, 18), (44, 28)], Q)
stamp(im, outline(p), 0, 0)

im = strip_outline(im)
im = outline(im)
save(im)
