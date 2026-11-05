from pix import *
# Bregdi, side on, facing left. Every part below is its own closed shape.
# tail        : behind the body, leaves the back at x 47-53, rises to upper right
# tail belly  : flat green strip on the tail's underside, inside the tail's closed shape
# hook        : closes on the tail's tip at x 65, curls down and in
# back ridge  : behind the body, sits on the back from x 29 to 54
# front web   : hangs from the front arm, scalloped trailing edge, folds end at arm and notch
# front arm   : behind the jaw, joins under the neck at x 16-30, runs down left
# front claws : five, each on a web lobe, all different
# body        : arches in the middle, joins neck on the left, tail and ridge above
# belly       : green, closed under the body, from neck to back arm
# neck        : between head and body, gill slits run from its crease to its lower edge
# head        : on the neck, holds the eye
# upper jaw   : on the front of the head
# lower jaw   : hinges under the head
# mouth       : between the jaws, closed against the head and lower jaw
# back web    : hangs from the back arm, scalloped trailing edge, folds end at arm and notch
# back arm    : on the body's rear, over the belly's right end
# back claws  : five, each on a web lobe, all different

W, H = 76, 58
HIDE, HS = '375a94', '37387b'
BEL, BS = '4fa667', '2c6c44'
CL, CS = 'cebe82', 'b2966a'
MO, MS = 'fc74b4', '664b95'
INK = '000000'
CP = {'c': CL, 's': CS}


def part(im, pts, col, shade=None, shcol=None):
    p = canvas(W, H)
    poly(p, pts, col)
    if shade:
        poly(p, shade, shcol)
    stamp(im, outline(p), 0, 0)


def ln(im, a, b):
    p = canvas(W, H)
    poly(p, [a, b], INK)
    stamp(im, p, 1, 1)


def d(im, x, y, col):
    dot(im, x + 1, y + 1, col)


def claw(im, rows, x, y):
    stamp(im, outline(grid(rows, CP)), x, y)


im = canvas(W + 2, H + 2)

# tail, its green underside, then the hook
part(im, [(47, 7), (52, 5), (56, 4), (60, 1), (65, 0), (66, 5), (64, 5), (61, 8), (57, 11), (53, 13), (48, 13)], HIDE, [(64, 3), (64, 5), (61, 8), (57, 11), (53, 13), (51, 11), (55, 9), (59, 6)], BEL)
part(im, [(65, 0), (68, 0), (71, 3), (71, 6), (69, 9), (66, 10), (66, 8), (68, 7), (68, 5), (66, 5)], HIDE)

# back ridge
part(im, [(29, 11), (31, 7), (33, 1), (35, 5), (38, 0), (41, 4), (44, 1), (46, 5), (49, 3), (50, 7), (53, 5), (54, 9), (50, 11), (40, 9), (32, 12)], HIDE)

# front flipper: web, folds, arm, claws
p = canvas(W, H)
poly(p, [(16, 27), (30, 27), (28, 31), (26, 34), (25, 39), (26, 41), (24, 43), (22, 41), (21, 45), (18, 46), (17, 42), (15, 48), (12, 48), (11, 43), (9, 48), (7, 48), (6, 43), (3, 44), (1, 42), (4, 36), (9, 31)], BS)
poly(p, [(1, 42), (3, 44), (6, 43), (8, 36), (4, 36)], BEL)
poly(p, [(6, 43), (7, 48), (9, 48), (11, 43), (10, 36), (8, 36)], BEL)
poly(p, [(11, 43), (12, 48), (15, 48), (17, 42), (16, 36), (11, 36)], BEL)
stamp(im, outline(p), 0, 0)
ln(im, (11, 36), (11, 43))
ln(im, (17, 36), (17, 42))
ln(im, (23, 33), (22, 41))
part(im, [(16, 28), (30, 26), (29, 30), (24, 33), (16, 36), (9, 36), (8, 33), (12, 30)], HS)
claw(im, ['...cc', '..cs.', '.cs..', 'cs...', 'c....', 'c....', 'c....'], 0, 43)
claw(im, ['cc.', 'cs.', 'cs.', '.cs', '.cs', '.c.', '.c.'], 7, 47)
claw(im, ['cc...', 'cs...', '.cs..', '.cs..', '..cs.', '...cc', '....c'], 12, 47)
claw(im, ['cc..', 'cs..', '.cs.', '..cs', '...c'], 18, 45)
claw(im, ['cc..', '.cs.', '..c.', '...c'], 24, 42)

# body with one shaded rear plate, then the belly
part(im, [(29, 12), (33, 8), (40, 6), (48, 6), (54, 9), (56, 13), (55, 17), (50, 24), (30, 24), (28, 20)], HIDE, [(48, 6), (54, 9), (56, 13), (55, 17), (48, 18)], HS)
part(im, [(29, 23), (33, 20), (41, 19), (47, 21), (49, 24), (47, 27), (38, 28), (30, 27)], BEL, [(30, 27), (38, 28), (47, 27), (48, 25), (40, 25), (33, 26)], BS)

# neck with gill slits between its crease and its lower edge
part(im, [(28, 9), (33, 8), (37, 12), (40, 19), (37, 21), (31, 22), (29, 22), (30, 20), (30, 13)], HIDE)
ln(im, (31, 13), (38, 13))
ln(im, (32, 13), (32, 21))
ln(im, (35, 13), (36, 21))

# head, eye
part(im, [(18, 11), (26, 9), (30, 12), (31, 18), (29, 23), (24, 23), (21, 20), (18, 17)], HIDE, [(31, 17), (29, 23), (24, 23), (27, 20)], HS)
d(im, 23, 14, CL)
d(im, 24, 14, CL)

# upper jaw
part(im, [(3, 17), (4, 14), (8, 12), (14, 13), (18, 11), (20, 11), (20, 19), (19, 19), (14, 17), (9, 18), (5, 19)], HIDE, [(5, 19), (9, 18), (14, 17), (19, 19), (19, 17), (14, 15), (8, 16)], HS)

# lower jaw
part(im, [(3, 28), (8, 28), (14, 26), (20, 24), (26, 23), (30, 24), (27, 27), (19, 27), (13, 28), (8, 30), (4, 30)], HIDE)

# mouth with its purple back
part(im, [(8, 28), (14, 26), (20, 24), (26, 23), (25, 20), (20, 18), (15, 18)], MO, [(15, 18), (20, 18), (25, 20), (25, 22), (17, 22)], MS)

# teeth, a few placed marks
d(im, 5, 20, CL)
d(im, 5, 21, CL)
d(im, 9, 19, CL)
d(im, 13, 18, CL)
d(im, 13, 19, CL)
d(im, 5, 27, CL)
d(im, 5, 26, CL)
d(im, 10, 27, CL)
d(im, 17, 24, CL)

# back flipper: web, folds, arm, claws
p = canvas(W, H)
poly(p, [(46, 26), (58, 16), (63, 18), (65, 22), (64, 25), (67, 27), (67, 33), (70, 35), (70, 38), (68, 39), (66, 37), (67, 40), (66, 42), (64, 42), (63, 40), (62, 44), (59, 45), (58, 44), (57, 40), (56, 44), (54, 45), (52, 44), (51, 39), (49, 43), (47, 44), (45, 42), (46, 37), (47, 31)], HS)
poly(p, [(46, 26), (47, 31), (46, 37), (45, 42), (47, 44), (49, 43), (51, 39), (52, 31), (48, 31)], HIDE)
poly(p, [(51, 39), (52, 44), (54, 45), (56, 44), (57, 40), (57, 30), (52, 31)], HIDE)
stamp(im, outline(p), 0, 0)
ln(im, (57, 30), (57, 40))
ln(im, (60, 28), (63, 40))
ln(im, (63, 24), (66, 37))
part(im, [(38, 17), (43, 14), (50, 14), (55, 15), (60, 17), (63, 20), (63, 24), (60, 28), (54, 31), (48, 31), (47, 26), (45, 22), (42, 19)], HIDE, [(63, 21), (63, 24), (60, 28), (54, 31), (48, 31), (54, 28), (60, 25)], HS)
ln(im, (54, 14), (50, 32))
claw(im, ['cc...', 'cs...', 'cs...', '.cs..', '.cs..', '..c..', '..cc.', '...c.'], 46, 43)
claw(im, ['cc', 'cs', 'cs', 'cs', '.c', '.c', '.c'], 54, 44)
claw(im, ['..cc', '..cs', '..cs', '.cs.', '.cs.', 'cc..', 'c...'], 58, 44)
claw(im, ['.cc', '.cs', 'cs.', 'c..', 'c..'], 64, 41)
claw(im, ['cc.', 'cs.', '.cs', '.cs', '.cs', '.c.', '.c.'], 69, 37)

im = strip_outline(im)
im = outline(im)
save(im)
