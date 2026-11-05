from pix import *
# Chipekwe, head-on. Parts and where they attach:
# hind legs: behind the belly, under its left and right ends, feet on the ground
# belly: under the hump, between the two front legs
# hump: the great back, rises behind the head, its base runs into the shoulders
# front legs: shoulder joins the hump's lower corners, leg runs down to a big foot
# feet: under each front leg, three pale claws on the front edge
# ears: on the upper corners of the head, in front of the hump
# head: low in the middle, in front of hump and chest, widening to a broad muzzle
# horn: rooted on top of the snout, curves up and off to the viewer's left
# eyes: on the brow, just right of the horn's curve and level across the head
# teeth: two, hanging below the muzzle, over the dark chest

K = '000000'
H = '375a94'
L = '3e91cc'
S = '37387b'
D = '2b1f40'
T = 'b2966a'
U = '8d6b4f'
P = 'e8e0c0'
Y = 'f0bc3c'

im = canvas(80, 90)

# hind legs
poly(im, [(23, 58), (34, 58), (34, 74), (35, 76), (35, 81), (23, 81)], S)
poly(im, [(43, 58), (54, 58), (54, 81), (42, 81), (42, 76), (43, 74)], S)
# hind claws
rect(im, 26, 78, 3, 3, T)
rect(im, 31, 79, 3, 2, T)
rect(im, 44, 79, 3, 2, T)
rect(im, 49, 78, 3, 3, T)

# belly underside line, only over the hind legs
rect(im, 24, 65, 3, 1, K)
rect(im, 27, 66, 2, 1, K)
rect(im, 29, 67, 2, 1, K)
rect(im, 31, 68, 4, 1, K)
rect(im, 43, 68, 4, 1, K)
rect(im, 47, 67, 2, 1, K)
rect(im, 49, 66, 2, 1, K)
rect(im, 51, 65, 3, 1, K)

# belly
poly(im, [(20, 44), (57, 44), (57, 62), (52, 65), (46, 67), (31, 67), (25, 65), (20, 62)], S)

# chest gap under the head
oval(im, 27, 44, 24, 11, D)

# hump
poly(im, [(36, 0), (41, 0), (45, 2), (50, 5), (55, 8), (60, 12), (65, 17), (69, 21), (71, 25), (71, 46),
          (6, 46), (6, 25), (8, 21), (12, 17), (17, 12), (22, 8), (27, 5), (32, 2)], H)
# lit crown of the hump
poly(im, [(32, 3), (38, 1), (38, 16), (35, 16), (33, 9), (27, 7)], L)
# shaded right slope
poly(im, [(49, 4), (55, 8), (60, 12), (65, 17), (69, 21), (70, 24), (64, 22), (59, 16), (53, 10)], S)

# black line where the shoulders meet the hump
rect(im, 11, 23, 5, 1, K)
rect(im, 9, 24, 2, 1, K)
rect(im, 7, 25, 2, 1, K)
rect(im, 6, 26, 1, 1, K)
rect(im, 62, 23, 5, 1, K)
rect(im, 67, 24, 2, 1, K)
rect(im, 69, 25, 2, 1, K)
rect(im, 71, 26, 1, 1, K)

# black line where the front legs meet the belly and hind legs
rect(im, 26, 31, 1, 13, K)
rect(im, 25, 44, 1, 3, K)
rect(im, 24, 47, 1, 2, K)
rect(im, 25, 49, 1, 8, K)
rect(im, 24, 57, 1, 7, K)
rect(im, 23, 64, 1, 9, K)
rect(im, 23, 73, 1, 1, K)
rect(im, 23, 74, 2, 1, K)
rect(im, 24, 75, 2, 1, K)
rect(im, 25, 76, 1, 6, K)
rect(im, 51, 31, 1, 13, K)
rect(im, 52, 44, 1, 3, K)
rect(im, 53, 47, 1, 2, K)
rect(im, 52, 49, 1, 8, K)
rect(im, 53, 57, 1, 7, K)
rect(im, 54, 64, 1, 9, K)
rect(im, 54, 73, 1, 1, K)
rect(im, 53, 74, 2, 1, K)
rect(im, 52, 75, 2, 1, K)
rect(im, 52, 76, 1, 6, K)

# front legs
poly(im, [(5, 30), (7, 26), (11, 24), (18, 24), (23, 27), (25, 32), (25, 42), (23, 47), (24, 52), (23, 58),
          (22, 73), (3, 73), (3, 70), (1, 62), (0, 55), (2, 48), (5, 46), (3, 42), (3, 33)], H)
poly(im, [(72, 30), (70, 26), (66, 24), (59, 24), (54, 27), (52, 32), (52, 42), (54, 47), (53, 52), (54, 58),
          (55, 73), (74, 73), (74, 70), (76, 62), (77, 55), (75, 48), (72, 46), (74, 42), (74, 33)], H)
# feet
poly(im, [(2, 74), (22, 74), (24, 76), (24, 82), (23, 85), (1, 85), (0, 82), (0, 76)], H)
poly(im, [(75, 74), (55, 74), (53, 76), (53, 82), (54, 85), (76, 85), (77, 82), (77, 76)], H)

# leg shade: right side of each leg, light from upper left
poly(im, [(18, 51), (24, 52), (23, 58), (22, 73), (22, 74), (24, 76), (24, 85), (16, 85), (17, 70)], S)
poly(im, [(70, 51), (75, 48), (77, 55), (76, 62), (74, 70), (74, 73), (75, 74), (77, 76), (77, 82), (76, 85), (70, 85), (71, 68)], S)
# shoulder shade
poly(im, [(20, 32), (25, 32), (25, 42), (23, 47), (18, 46), (21, 40)], S)
poly(im, [(69, 30), (72, 30), (74, 33), (74, 42), (72, 46), (65, 46), (69, 40)], S)
# lit shoulder tops
poly(im, [(8, 27), (11, 25), (16, 25), (12, 28), (9, 32)], L)
poly(im, [(63, 25), (66, 25), (69, 27), (70, 29), (66, 28)], L)
# elbow crease
rect(im, 15, 49, 9, 1, K)
rect(im, 12, 48, 3, 1, K)
rect(im, 53, 49, 8, 1, K)
rect(im, 61, 48, 3, 1, K)

# ears
oval(im, 15, 18, 13, 13, K)
oval(im, 16, 19, 11, 11, H)
oval(im, 20, 23, 7, 7, D)
oval(im, 49, 18, 13, 13, K)
oval(im, 50, 19, 11, 11, H)
oval(im, 50, 23, 7, 7, D)

# head
poly(im, [(32, 16), (45, 16), (49, 20), (52, 26), (53, 32), (51, 38), (48, 41), (47, 43), (50, 46), (49, 50),
          (28, 50), (27, 46), (30, 43), (29, 41), (26, 38), (24, 32), (25, 26), (28, 20)], K)
poly(im, [(33, 17), (44, 17), (48, 21), (51, 27), (52, 32), (50, 37), (47, 40), (46, 43), (49, 46), (48, 49),
          (29, 49), (28, 46), (31, 43), (30, 40), (27, 37), (25, 32), (26, 27), (29, 21)], H)
# forehead
oval(im, 33, 19, 10, 7, L)
# head shade
poly(im, [(48, 24), (51, 27), (52, 32), (50, 37), (47, 40), (46, 43), (49, 46), (48, 49), (38, 49), (38, 47),
          (45, 46), (44, 42), (45, 38), (48, 33)], S)

# brows
rect(im, 33, 29, 3, 1, K)
rect(im, 42, 29, 3, 1, K)
# eyes
rect(im, 34, 31, 2, 1, Y)
rect(im, 42, 31, 2, 1, Y)

# nostrils
rect(im, 33, 45, 2, 1, K)
rect(im, 43, 45, 2, 1, K)

# teeth
rect(im, 31, 50, 2, 3, P)
rect(im, 45, 50, 2, 3, P)

# horn
poly(im, [(28, 18), (29, 18), (30, 25), (30, 29), (33, 33), (38, 37), (40, 41), (37, 43), (32, 42), (28, 38), (26, 33), (26, 28), (27, 22)], T)
poly(im, [(31, 37), (34, 39), (38, 39), (40, 41), (37, 43), (32, 42)], U)

# front claws
poly(im, [(3, 81), (5, 81), (6, 85), (2, 85)], P)
poly(im, [(10, 79), (12, 79), (14, 85), (8, 85)], P)
poly(im, [(18, 81), (20, 81), (21, 85), (17, 85)], P)
poly(im, [(57, 81), (59, 81), (60, 85), (56, 85)], P)
poly(im, [(65, 79), (67, 79), (69, 85), (63, 85)], P)
poly(im, [(72, 81), (74, 81), (75, 85), (71, 85)], P)

im = outline(im)
save(im)
