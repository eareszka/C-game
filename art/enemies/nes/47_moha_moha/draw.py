from pix import *
# Moha-Moha, side on, facing right. Parts, back to front, and where each attaches:
# tail fin   - forked, two points, sits on the tail's left end
# top fin    - grows out of the tail's top edge, swept back
# tail       - runs from under the shell's left side, tapering left, five marks
# neck       - comes out from under the shell's front, curves up to the head, two folds
# shell rim  - pale band under the dome, between the legs
# back toes  - three toes, each with its claw, under the back foot
# front toes - three toes, each with its claw, under the front foot
# back leg   - from under the dome's left side down to its toes, three marks
# front leg  - from under the dome's right side down to its toes, three marks
# shell dome - plain, sits on the rim
# lower jaw  - hinged at the head's base, on the right, with its teeth
# upper jaw with head - on top of the neck, with teeth, eye and spots

W, H = 110, 59
K = '000000'
SHELL, SHELL2 = '595965', '474751'
SKIN, SKIN2 = '4fa667', '2c6c44'
PALE, PALE2 = '9797aa', '595965'
FIN, FIN2 = '8d6b4f', '463422'
BONE = 'e8e0c0'

im = canvas(W + 2, H + 2)

# tail fin
p = canvas(W, H)
poly(p, [(0, 40), (7, 40), (13, 41), (20, 43), (20, 48), (15, 50), (9, 54), (1, 57), (5, 51), (9, 47), (5, 44)], FIN)
poly(p, [(20, 46), (14, 48), (9, 51), (5, 54), (1, 57), (9, 54), (15, 50), (20, 48)], FIN2)
poly(p, [(5, 44), (12, 44), (16, 46), (9, 47)], FIN2)
stamp(im, outline(p), 0, 0)

# top fin
p = canvas(W, H)
poly(p, [(38, 36), (33, 34), (28, 33), (23, 32), (18, 30), (20, 34), (22, 37), (22, 41), (38, 38)], FIN)
poly(p, [(22, 37), (26, 37), (30, 37), (26, 39), (22, 41)], FIN2)
stamp(im, outline(p), 0, 0)

# tail
p = canvas(W, H)
poly(p, [(56, 27), (49, 30), (42, 34), (34, 37), (24, 40), (15, 42), (15, 47), (24, 47), (34, 46), (42, 45), (50, 44), (56, 44)], PALE)
poly(p, [(15, 46), (24, 45), (34, 44), (42, 42), (50, 41), (56, 41), (56, 44), (50, 44), (42, 45), (34, 46), (24, 47), (15, 47)], PALE2)
rect(p, 45, 34, 4, 1, PALE2)
rect(p, 44, 35, 2, 1, PALE2)
rect(p, 38, 38, 3, 2, PALE2)
rect(p, 30, 40, 2, 1, PALE2)
rect(p, 31, 41, 3, 1, PALE2)
rect(p, 24, 42, 2, 2, PALE2)
rect(p, 17, 43, 4, 1, PALE2)
stamp(im, outline(p), 0, 0)

# neck
p = canvas(W, H)
poly(p, [(96, 14), (104, 14), (105, 20), (104, 27), (101, 33), (96, 38), (90, 41), (82, 42), (82, 33), (88, 30), (93, 26), (96, 20)], SKIN)
poly(p, [(102, 14), (104, 14), (105, 20), (104, 27), (101, 33), (96, 38), (90, 41), (84, 42), (84, 39), (90, 38), (95, 35), (99, 30), (102, 24)], SKIN2)
poly(p, [(95, 22), (100, 24)], K)
poly(p, [(100, 24), (105, 23)], K)
poly(p, [(88, 30), (94, 34)], K)
poly(p, [(94, 34), (102, 34)], K)
stamp(im, outline(p), 0, 0)

# shell rim
p = canvas(W, H)
poly(p, [(48, 37), (90, 37), (90, 42), (87, 45), (84, 46), (54, 46), (50, 44), (48, 41)], PALE)
poly(p, [(50, 44), (54, 44), (84, 44), (88, 42), (90, 42), (87, 45), (84, 46), (54, 46)], PALE2)
stamp(im, outline(p), 0, 0)

# back toes
p = canvas(W, H)
poly(p, [(35, 48), (42, 47), (42, 51), (37, 52)], SKIN)
poly(p, [(37, 51), (42, 50), (42, 51), (37, 52)], SKIN2)
rect(p, 33, 51, 3, 1, BONE)
rect(p, 34, 50, 2, 1, BONE)
stamp(im, outline(p), 0, 0)
p = canvas(W, H)
poly(p, [(41, 50), (48, 50), (48, 53), (43, 54)], SKIN)
poly(p, [(43, 53), (48, 53), (43, 54)], SKIN2)
rect(p, 40, 54, 3, 1, BONE)
rect(p, 40, 55, 1, 1, BONE)
stamp(im, outline(p), 0, 0)
p = canvas(W, H)
poly(p, [(49, 50), (55, 50), (55, 52), (50, 53)], SKIN)
rect(p, 48, 53, 2, 1, BONE)
stamp(im, outline(p), 0, 0)

# front toes
p = canvas(W, H)
poly(p, [(69, 48), (76, 47), (76, 51), (71, 52)], SKIN)
poly(p, [(71, 51), (76, 50), (76, 51), (71, 52)], SKIN2)
rect(p, 67, 51, 4, 1, BONE)
stamp(im, outline(p), 0, 0)
p = canvas(W, H)
poly(p, [(75, 51), (82, 51), (82, 54), (77, 54)], SKIN)
poly(p, [(78, 54), (82, 53), (82, 54)], SKIN2)
rect(p, 74, 55, 3, 1, BONE)
rect(p, 74, 54, 2, 1, BONE)
stamp(im, outline(p), 0, 0)
p = canvas(W, H)
poly(p, [(83, 50), (88, 49), (89, 52), (85, 54)], SKIN)
rect(p, 83, 54, 2, 1, BONE)
rect(p, 83, 55, 1, 1, BONE)
stamp(im, outline(p), 0, 0)

# back leg
p = canvas(W, H)
poly(p, [(46, 35), (58, 35), (60, 40), (59, 44), (56, 47), (51, 49), (43, 49), (40, 47), (43, 44), (45, 40)], SKIN)
poly(p, [(58, 35), (60, 40), (59, 44), (56, 47), (51, 49), (43, 49), (42, 47), (50, 47), (54, 44), (56, 40), (56, 35)], SKIN2)
rect(p, 48, 39, 3, 1, SKIN2)
rect(p, 49, 40, 1, 2, SKIN2)
rect(p, 52, 43, 2, 1, SKIN2)
rect(p, 44, 45, 3, 1, SKIN2)
rect(p, 45, 44, 1, 1, SKIN2)
stamp(im, outline(p), 0, 0)

# front leg
p = canvas(W, H)
poly(p, [(78, 35), (92, 34), (95, 38), (94, 42), (90, 46), (85, 49), (76, 49), (73, 47), (76, 44), (78, 40)], SKIN)
poly(p, [(92, 34), (95, 38), (94, 42), (90, 46), (85, 49), (76, 49), (75, 47), (84, 47), (88, 44), (91, 41), (92, 38)], SKIN2)
rect(p, 82, 41, 2, 3, SKIN2)
rect(p, 86, 40, 3, 1, SKIN2)
rect(p, 87, 39, 1, 1, SKIN2)
rect(p, 78, 45, 4, 1, SKIN2)
stamp(im, outline(p), 0, 0)

# shell dome
p = canvas(W, H)
poly(p, [(50, 38), (51, 32), (53, 28), (56, 25), (60, 22), (65, 20), (71, 19), (76, 20), (80, 22), (84, 26), (86, 30), (88, 35), (88, 38)], SHELL)
poly(p, [(88, 38), (58, 38), (70, 36), (77, 33), (81, 29), (82, 24), (84, 26), (86, 30), (88, 35)], SHELL2)
stamp(im, outline(p), 0, 0)

# lower jaw
p = canvas(W, H)
poly(p, [(105, 0), (107, 1), (107, 10), (106, 14), (104, 17), (102, 17), (103, 12), (104, 7), (105, 1)], SKIN)
poly(p, [(106, 1), (107, 1), (107, 10), (106, 14), (104, 17), (103, 17), (105, 13), (106, 9)], SKIN2)
rect(p, 103, 3, 2, 1, BONE)
rect(p, 102, 7, 2, 1, BONE)
rect(p, 103, 8, 1, 1, BONE)
stamp(im, outline(p), 0, 0)

# upper jaw with head
p = canvas(W, H)
poly(p, [(93, 0), (97, 0), (98, 3), (99, 7), (100, 11), (102, 14), (103, 17), (95, 18), (92, 16), (90, 12), (90, 6), (91, 3)], SKIN)
poly(p, [(97, 0), (98, 3), (99, 7), (100, 11), (102, 14), (103, 17), (95, 18), (94, 16), (99, 15), (98, 11), (97, 7), (96, 3)], SKIN2)
rect(p, 98, 1, 3, 1, BONE)
rect(p, 98, 2, 2, 1, BONE)
rect(p, 99, 5, 2, 1, BONE)
rect(p, 100, 9, 1, 1, BONE)
rect(p, 92, 5, 2, 1, K)
rect(p, 91, 9, 2, 1, FIN)
rect(p, 92, 10, 1, 1, FIN)
rect(p, 94, 11, 2, 1, FIN)
rect(p, 92, 13, 1, 2, FIN)
rect(p, 95, 13, 2, 2, FIN)
stamp(im, outline(p), 0, 0)

im = strip_outline(im)
im = outline(im)
save(im)
