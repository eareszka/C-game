from pix import *
# Chipekwe, head-on rhino. Centre line x = 40.
# hump: rises behind the top of the head, one dome and two low ridges of different height
# ears: join the upper corners of the head, point up and out
# front legs: each joins the back at the shoulder beside the head, runs down to a foot
# feet: end of each front leg, three pale claws each
# chest: shadow mass under the jaw, joins the two shoulders
# belly: black crescent under the chest, above the hind legs
# hind legs: shadow tone, come out from under the belly between the front legs
# head: wedge in front of chest and shoulders, narrowing to a wide snout
# horn: rises from the top of the snout, between the eyes
# tusks: one each side of the snout, curve down and out
# eyes: one orange mark each side of the horn

HIDE = '3e91cc'
DARK = '375a94'
PALE = 'bcbeca'
PALED = '9797aa'
EAR = '595965'
EYE = 'd89830'
BLK = '000000'

im = canvas(84, 92)

# hump
poly(im, [(38, 1), (42, 1), (45, 4), (47, 9), (47, 16), (33, 16), (33, 9), (35, 4)], HIDE)
poly(im, [(43, 2), (45, 4), (47, 9), (47, 16), (43, 16)], DARK)
poly(im, [(33, 11), (47, 11), (47, 16), (33, 16)], DARK)
poly(im, [(29, 8), (33, 10), (34, 16), (26, 16), (26, 11)], HIDE)
poly(im, [(31, 11), (34, 11), (34, 16), (28, 16)], DARK)
poly(im, [(50, 10), (54, 13), (54, 16), (46, 16), (47, 12)], HIDE)
poly(im, [(49, 13), (54, 13), (54, 16), (47, 16)], DARK)

# chest
poly(im, [(24, 40), (56, 40), (56, 56), (48, 59), (32, 59), (24, 56)], DARK)
# belly
poly(im, [(26, 56), (32, 59), (48, 59), (54, 56), (54, 60), (48, 65), (32, 65), (26, 60)], BLK)

# hind legs
poly(im, [(27, 62), (32, 67), (36, 67), (36, 76), (37, 80), (37, 83), (27, 83)], DARK)
poly(im, [(53, 62), (48, 67), (44, 67), (44, 76), (43, 80), (43, 83), (53, 83)], DARK)

# left front leg, then its shadow
poly(im, [(14, 16), (24, 15), (28, 36), (27, 48), (25, 58), (25, 76), (5, 76), (3, 68), (2, 58), (5, 46), (9, 38), (9, 26)], HIDE)
poly(im, [(17, 15), (24, 15), (28, 36), (27, 48), (25, 58), (25, 76), (5, 76), (4, 72), (14, 70), (19, 60), (20, 44), (18, 34), (17, 24)], DARK)
# right front leg, then its shadow
poly(im, [(66, 16), (56, 15), (52, 36), (53, 48), (55, 58), (55, 76), (75, 76), (77, 68), (78, 58), (75, 46), (71, 38), (71, 26)], HIDE)
poly(im, [(68, 18), (71, 26), (71, 38), (75, 46), (78, 58), (77, 68), (75, 76), (55, 76), (55, 72), (65, 70), (71, 62), (71, 50), (67, 40), (66, 26)], DARK)

# feet
poly(im, [(5, 72), (25, 72), (29, 76), (30, 82), (2, 82), (2, 76)], HIDE)
poly(im, [(75, 72), (55, 72), (51, 76), (50, 82), (78, 82), (78, 76)], HIDE)
poly(im, [(72, 74), (75, 72), (78, 76), (78, 82), (73, 82)], DARK)
# toe notches
rect(im, 10, 76, 1, 7, DARK)
rect(im, 21, 77, 1, 6, DARK)
rect(im, 59, 77, 1, 6, DARK)
rect(im, 70, 76, 1, 7, DARK)
# claws, left foot: small, big, middling
poly(im, [(5, 80), (8, 80), (9, 83), (9, 86), (3, 86), (3, 83)], PALE)
rect(im, 8, 83, 2, 4, PALED)
poly(im, [(14, 78), (17, 78), (20, 82), (20, 86), (12, 86), (12, 82)], PALE)
poly(im, [(17, 79), (20, 82), (20, 86), (18, 86)], PALED)
poly(im, [(24, 80), (26, 80), (28, 84), (28, 86), (23, 86), (23, 84)], PALE)
rect(im, 27, 83, 2, 4, PALED)
# claws, right foot
poly(im, [(55, 80), (57, 80), (58, 84), (58, 86), (53, 86), (53, 84)], PALE)
rect(im, 57, 83, 2, 4, PALED)
poly(im, [(63, 78), (66, 78), (68, 82), (68, 86), (60, 86), (60, 82)], PALE)
poly(im, [(65, 79), (68, 82), (68, 86), (66, 86)], PALED)
poly(im, [(72, 80), (75, 80), (77, 83), (77, 86), (71, 86), (71, 83)], PALE)
rect(im, 75, 83, 3, 4, PALED)

# ears
poly(im, [(16, 3), (31, 15), (30, 28), (24, 25)], HIDE)
poly(im, [(20, 9), (28, 16), (27, 24), (25, 22)], EAR)
poly(im, [(64, 3), (49, 15), (50, 28), (56, 25)], HIDE)
poly(im, [(60, 9), (52, 16), (53, 24), (55, 22)], EAR)
poly(im, [(64, 3), (56, 25), (55, 22), (60, 9)], DARK)

# head
poly(im, [(30, 13), (50, 13), (56, 20), (57, 28), (52, 38), (53, 42), (53, 48), (49, 51), (31, 51), (27, 48), (27, 42), (28, 38), (23, 28), (24, 20)], HIDE)
# cheek and jaw shadow
poly(im, [(53, 16), (56, 20), (57, 28), (52, 38), (53, 42), (53, 48), (49, 51), (31, 51), (28, 49), (28, 48), (50, 48), (50, 42), (49, 38), (53, 28)], DARK)
# brows
poly(im, [(28, 24), (36, 28), (36, 26), (30, 23)], DARK)
poly(im, [(52, 24), (44, 28), (44, 26), (50, 23)], DARK)
# nostrils
rect(im, 30, 44, 2, 1, DARK)
rect(im, 48, 44, 2, 1, DARK)

# horn
poly(im, [(40, 8), (42, 22), (44, 33), (46, 42), (46, 43), (34, 43), (34, 42), (36, 33), (38, 22)], PALE)
poly(im, [(41, 11), (42, 22), (44, 33), (46, 42), (46, 43), (41, 43)], PALED)

# tusks
poly(im, [(26, 40), (29, 42), (29, 46), (26, 51), (23, 54), (23, 46)], PALE)
poly(im, [(28, 44), (29, 46), (26, 51), (23, 54), (25, 48)], PALED)
poly(im, [(54, 40), (51, 42), (51, 46), (54, 51), (57, 54), (57, 46)], PALE)
poly(im, [(56, 44), (57, 46), (57, 54), (54, 50)], PALED)

# eyes
dot(im, 32, 28, EYE)
dot(im, 33, 29, EYE)
dot(im, 48, 28, EYE)
dot(im, 47, 29, EYE)

im = outline(im)
save(im)
