from pix import *

# Lomie: tall blue moose, broad brown antlers, great pale peach bladder under the neck.
A = '5c94fc'  # hide light
B = '2850a0'  # hide mid
C = '37387b'  # hide shade
E = '94703d'  # antler light
F = '633e1b'  # antler shade
G = 'f0b890'  # bladder
H = 'd7a175'  # bladder shade
I = 'fce4a0'  # bladder shine
K = (0, 0, 0)

W, H_ = 55, 71
CX = 27
im = canvas(W, H_)
px = im.load()


def span(y, hw, col, cx=CX):
    rect(im, cx - hw, y, hw * 2 + 1, 1, col)


def both(x, y, w, h, col):
    """A rect and its mirror image across the centre line."""
    rect(im, x, y, w, h, col)
    rect(im, 2 * CX - x - w + 1, y, w, h, col)


# ---- antlers: palm with tines, mirrored, then lit from the upper left
ANTLER = [
    '.e.....e......e.........',
    '.ee....e......ee........',
    '.ee...ee.....ee......e..',
    '.ee...ee.....ee.....ee..',
    '..ee..ee....ee......ee..',
    '..ee..eee...ee.....ee...',
    'e.eee.eee..eee.....ee...',
    'ee.eeeeeeeeeee....ee....',
    'eee.eeeeeeeeee...eee....',
    '.eeeeeeeeeeeee..eee.....',
    '..eeeeeeeeeeeeeeeee.....',
    '...eeeeeeeeeeeeeee......',
    '....eeeeeeeeeeeee.......',
    '.......eeeeeeeee........',
    '..........eeeee.........',
    '............eeee........',
    '.............eeee.......',
    '..............eeee......',
    '...............eeee.....',
    '................eeee....',
    '.................eeee...',
]
for y, row in enumerate(ANTLER):
    for x, ch in enumerate(row):
        if ch == 'e':
            px[x, y] = rgba(E)
            px[2 * CX - x, y] = rgba(E)
# shade every lower and right edge of the antler
snap = im.copy().load()
for y in range(22):
    for x in range(W):
        if snap[x, y][3] and (x + 1 >= W or not snap[x + 1, y][3] or not snap[x, y + 1][3]):
            px[x, y] = rgba(F)
# grooves across each palm, where the tines root
for x, y in [(5, 9), (6, 10), (7, 11), (8, 11), (9, 11), (10, 10), (11, 9), (12, 11), (13, 12), (14, 12)]:
    px[x, y] = rgba(F)
    px[2 * CX - x, y] = rgba(F)
for x, y in [(8, 8), (9, 8), (9, 9), (12, 8), (13, 8), (13, 9)]:
    px[x, y] = BLACK
    px[2 * CX - x, y] = BLACK

# ---- ears
for y, x0, x1 in [(21, 15, 19), (22, 11, 20), (23, 9, 20), (24, 10, 20), (25, 13, 20), (26, 16, 20)]:
    both(x0, y, x1 - x0 + 1, 1, B)
both(11, 23, 7, 1, C)
both(14, 24, 5, 1, C)
rect(im, 11, 22, 5, 1, A)
rect(im, 9, 23, 2, 1, A)
rect(im, 44, 24, 1, 1, C)
rect(im, 45, 23, 1, 1, C)

# ---- body behind the bladder
for y, hw in [(35, 8), (36, 9), (37, 10), (38, 12), (39, 13), (40, 14), (41, 14), (42, 15), (43, 15),
              (44, 15), (45, 15), (46, 15), (47, 15), (48, 15), (49, 15), (50, 15), (51, 15), (52, 14), (53, 13)]:
    span(y, hw, B)
# shaggy flanks
for x, y, h in [(11, 41, 2), (10, 44, 3), (9, 45, 1), (10, 48, 2), (9, 49, 1), (11, 51, 2)]:
    both(x, y, 1, h, B)
# lit shoulder, shaded far side
for y, x0, x1 in [(37, 17, 20), (38, 15, 19), (39, 14, 17), (40, 13, 15), (41, 11, 15), (42, 11, 14), (43, 12, 14),
                  (44, 10, 13), (45, 9, 13), (46, 10, 13), (47, 11, 13), (48, 10, 13), (49, 9, 12), (50, 10, 13)]:
    rect(im, x0, y, x1 - x0 + 1, 1, A)
for y, x0, x1 in [(38, 36, 39), (39, 37, 40), (40, 38, 41), (41, 38, 43), (42, 39, 43), (43, 39, 42), (44, 39, 44),
                  (45, 39, 45), (46, 39, 44), (47, 39, 42), (48, 39, 44), (49, 39, 45), (50, 39, 44), (51, 39, 43),
                  (52, 39, 43), (53, 37, 40)]:
    rect(im, x0, y, x1 - x0 + 1, 1, C)
# fur ticks on the flanks
for x, y, c in [(13, 44, B), (14, 45, B), (12, 47, B), (13, 48, B), (11, 50, B), (12, 49, B)]:
    px[x, y] = rgba(c)
for x, y in [(40, 44), (41, 45), (40, 48), (41, 49), (40, 51)]:
    px[x, y] = rgba(B)

# ---- legs: two rear, darker, then two front
for x0 in (18, 34):
    rect(im, x0, 53, 3, 13, C)
    rect(im, x0, 53, 1, 13, B)
    rect(im, x0 - 1, 60, 5, 2, C)
    rect(im, x0 - 1, 60, 2, 1, B)
    rect(im, x0, 65, 3, 1, K)
    rect(im, x0 - 1, 66, 5, 3, F)
    rect(im, x0 - 1, 66, 2, 1, E)
    rect(im, x0 + 1, 67, 1, 2, K)
for x0 in (12, 40):
    rect(im, x0, 51, 3, 16, B)
    rect(im, x0, 51, 1, 16, A)
    rect(im, x0 + 2, 51, 1, 16, C)
    rect(im, x0 - 1, 58, 5, 3, B)
    rect(im, x0 - 1, 58, 2, 2, A)
    rect(im, x0 + 3, 58, 1, 3, C)
    rect(im, x0, 66, 3, 1, K)
    rect(im, x0 - 1, 67, 5, 3, F)
    rect(im, x0 - 1, 67, 3, 1, E)
    rect(im, x0 + 1, 68, 1, 2, K)

# ---- bladder: black ring, then flat fill with a shaded lower right
BX, BY, BW, BH = 16, 36, 23, 22
oval(im, BX - 1, BY - 1, BW + 2, BH + 2, K)
oval(im, BX, BY, BW, BH, H)
m = canvas(W, H_)
oval(m, BX - 2, BY - 2, BW - 1, BH - 1, G)
ms = m.load()
for y in range(H_):
    for x in range(W):
        if ms[x, y][3] and px[x, y][:3] == rgba(H)[:3] and px[x, y][3]:
            px[x, y] = rgba(G)
# shine
for y, x0, x1 in [(39, 21, 25), (40, 19, 24), (41, 18, 22), (42, 18, 21), (43, 17, 19), (44, 17, 19), (45, 17, 18), (46, 17, 18)]:
    rect(im, x0, y, x1 - x0 + 1, 1, I)
# creases and the tight skin where it hangs
for x, y in [(31, 42), (32, 43), (33, 44), (33, 45),
             (21, 50), (22, 51), (23, 52), (24, 52), (25, 53),
             # one vein running down from the neck, with a short fork
             (28, 40), (28, 41), (28, 42), (29, 43), (29, 44), (29, 45), (30, 46), (30, 47), (31, 48), (31, 49),
             (28, 46), (27, 47), (27, 48)]:
    px[x, y] = rgba(H)

# ---- head, in front of everything
HEAD = [(18, 4), (19, 5), (20, 6), (21, 6), (22, 7), (23, 7), (24, 7), (25, 6), (26, 5), (27, 4), (28, 4), (29, 4),
        (30, 4), (31, 5), (32, 6), (33, 6), (34, 7), (35, 7), (36, 6), (37, 4)]
# black line round the head where it sits on ears and chest
for y, hw in HEAD:
    span(y, hw + 1, K)
span(38, 5, K)
for y, hw in HEAD:
    span(y, hw, B)
# lit brow and blaze
for y, x0, x1 in [(18, 23, 26), (19, 22, 25), (20, 21, 25), (21, 21, 24), (22, 20, 24), (23, 20, 25), (24, 20, 25), (25, 21, 25),
                  (26, 22, 25), (27, 25, 26), (28, 25, 26), (29, 25, 26), (30, 24, 26), (31, 23, 26), (32, 22, 25), (33, 21, 24), (34, 21, 22)]:
    rect(im, x0, y, x1 - x0 + 1, 1, A)
# brow patch for the far eye, so both eyes sit on lit hide
rect(im, 29, 23, 4, 2, A)
rect(im, 29, 25, 3, 1, A)
# shaded right cheek and muzzle
for y, x0, x1 in [(21, 32, 33), (22, 34, 34), (23, 34, 34), (24, 34, 34), (25, 33, 33), (26, 31, 32), (27, 30, 31), (28, 30, 31), (29, 30, 31),
                  (30, 30, 31), (31, 31, 32), (32, 32, 33), (33, 32, 33), (34, 32, 34), (35, 31, 34), (36, 29, 33), (37, 26, 31)]:
    rect(im, x0, y, x1 - x0 + 1, 1, C)
# eyes: solid black marks on lit hide
rect(im, 24, 24, 1, 2, K)
rect(im, 30, 24, 1, 2, K)
# brow ridge line and nostrils, mouth
rect(im, 22, 22, 3, 1, B)
rect(im, 30, 22, 3, 1, B)
rect(im, 22, 34, 2, 2, K)
rect(im, 31, 34, 2, 2, K)
rect(im, 24, 36, 7, 1, K)

# any black left on the silhouette edge would double the outline
im = strip_outline(im)
im = outline(im)
save(im)
