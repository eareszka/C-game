from pix import *
# Parts and where they attach:
# far hind leg  - hangs from belly, behind near hind leg
# far front leg - hangs from chest, knee forward, foot just ahead of near front leg
# tail          - thin point from top of rump, hanging clear behind near hind leg
# torso         - broad arched back, neck hump at left
# near hind leg - pillar from rump, wide clawed foot
# near front leg- pillar from shoulder, foot steps forward with claws
# head          - rhino head on short thick neck, reaches forward and left
# lower jaw     - small hook under the head behind the snout
# horn          - long pale horn from top of snout, sweeps forward and up

H = '9797aa'
S = '595965'
P = 'e8e0c0'
Q = 'cebe82'
K = '000000'

im = canvas(76, 54)

# far hind leg
poly(im, [(50, 30), (59, 30), (59, 46), (50, 46), (51, 38)], S)
rect(im, 49, 44, 9, 3, S)
rect(im, 48, 46, 3, 1, Q)
dot(im, 48, 47, Q)
rect(im, 52, 47, 2, 1, Q)

# far front leg
poly(im, [(33, 26), (40, 28), (40, 42), (36, 46), (31, 46), (30, 42), (29, 37)], S)
rect(im, 29, 45, 3, 1, Q)
dot(im, 29, 46, Q)
rect(im, 33, 46, 2, 1, Q)

# tail
poly(im, [(67, 15), (70, 22), (71, 29), (72, 36), (70, 32), (69, 26), (67, 22)], H)

# torso
poly(im, [(19, 9), (24, 5), (30, 5), (35, 8), (40, 7), (50, 8), (57, 6), (63, 7), (66, 11), (69, 19), (68, 30), (58, 32), (46, 32), (36, 30), (30, 25), (22, 20)], H)
# belly and rump shade
poly(im, [(30, 24), (42, 27), (58, 28), (65, 22), (69, 19), (68, 32), (58, 32), (46, 32), (36, 30)], S)

# near hind leg, with a line where it crosses the far hind leg
rect(im, 56, 33, 1, 15, K)
poly(im, [(57, 26), (68, 22), (67, 34), (67, 44), (69, 49), (55, 49), (57, 42), (58, 34)], H)
poly(im, [(64, 25), (68, 22), (67, 34), (67, 44), (69, 49), (64, 49), (63, 42)], S)
rect(im, 55, 48, 3, 2, P)
dot(im, 55, 50, P)
rect(im, 60, 49, 2, 1, P)
dot(im, 60, 50, P)
rect(im, 63, 48, 2, 2, P)
dot(im, 63, 50, P)
rect(im, 67, 49, 2, 1, Q)

# near front leg line then fill
poly(im, [(37, 27), (37, 43), (34, 50), (46, 49), (44, 42), (46, 30)], K)
poly(im, [(38, 25), (46, 26), (47, 31), (45, 42), (47, 49), (36, 49), (39, 42)], H)
poly(im, [(44, 27), (47, 31), (45, 42), (47, 49), (44, 49), (43, 40)], S)
rect(im, 34, 48, 3, 2, P)
dot(im, 33, 50, P)
dot(im, 34, 50, P)
rect(im, 38, 49, 2, 1, P)
dot(im, 38, 50, P)
rect(im, 41, 49, 3, 1, P)
dot(im, 41, 50, P)

# head
poly(im, [(10, 13), (14, 10), (20, 8), (24, 5), (30, 6), (34, 12), (32, 20), (24, 20), (20, 18), (14, 20), (11, 23), (8, 22), (6, 19), (7, 15)], H)
# under neck shade
poly(im, [(21, 18), (24, 16), (32, 15), (32, 20), (24, 20)], S)

# lower jaw, with the mouth line above it
poly(im, [(22, 18), (18, 20), (16, 21), (15, 24), (16, 24), (18, 22), (23, 21)], H)
rect(im, 19, 21, 4, 1, S)
rect(im, 15, 20, 7, 1, K)
rect(im, 20, 19, 3, 1, K)

# horn
poly(im, [(0, 0), (4, 6), (11, 10), (13, 12), (9, 15), (6, 11)], P)
poly(im, [(6, 11), (9, 15), (11, 13), (5, 8)], Q)

# eye and nostril
rect(im, 21, 12, 2, 2, K)
rect(im, 9, 18, 2, 1, K)

# neck fold
rect(im, 34, 12, 1, 7, K)
rect(im, 33, 19, 1, 2, K)

im = outline(im)
save(im)
