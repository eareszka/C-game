from pix import *

H, M, D = 'bcbeca', '9797aa', '595965'
P, R = 'ec8476', 'b6433d'
W, T = 'e8e0c0', 'b29e5c'
K = '000000'
PAL = {'h': H, 'm': M, 'd': D, 'p': P, 'r': R, 'w': W, 't': T}

im = canvas(72, 60)
px = im.load()


def lay(cells):
    """Put a part on top; where it crosses an earlier part, a black line separates them."""
    for (x, y) in cells:
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + a, y + b)
            if n not in cells and 0 <= n[0] < im.width and 0 <= n[1] < im.height and px[n][3]:
                px[n] = BLACK
    for (x, y), c in cells.items():
        px[x, y] = rgba(c)


TAPER = {0: 5, 1: 4, 2: 3, 3: 2, 4: 2, 5: 1, 6: 1, 7: 1}


def coil(a, b, yl, yr, th, ticks, phase, lit_to=None, open_right=False):
    """A slanted coil built column by column, so its edges climb in clean steps."""
    cells = {}
    for x in range(a, b + 1):
        u = (x - a) / (b - a)
        cy = round(yl + (yr - yl) * u)
        end = x - a if open_right else min(x - a, b - x)
        h = th - TAPER.get(end, 0)
        top = cy - h // 2
        bot = top + h - 1
        for y in range(top, bot + 1):
            i, j = y - top, bot - y
            c = M
            if i == 0 or (i == 1 and u < 0.6):
                c = H
            if j <= 1:
                c = D
            if not open_right and b - x <= 1:
                c = D
            if lit_to is not None and x > lit_to and c == H:
                c = M
            if j <= 1 and end > 2 and (x + phase) % ticks == 0:
                c = K
            if i == 3 and j > 1 and end > 3 and (x + phase) % 9 < 5:
                c = D
            cells[(x, y)] = c
    return cells


# Tail, rising behind the bottom coil.
tail_rows = []
for ys, a, b in (((15, 19), 58, 62), ((19, 22), 58, 63), ((22, 26), 57, 63), ((26, 30), 57, 64),
                 ((30, 34), 56, 64), ((34, 37), 55, 64), ((37, 39), 54, 63), ((39, 41), 52, 63),
                 ((41, 42), 50, 62), ((42, 43), 48, 62)):
    for y in range(*ys):
        tail_rows.append((y, a, b))
tail = {}
for y, a, b in tail_rows:
    for x in range(a, b + 1):
        c = M
        if x <= a + 1:
            c = H
        if x >= b - 1:
            c = D
        if y % 4 == 0 and x >= a + 2:
            c = K if x <= b - 1 else D
        tail[(x, y)] = c
lay(tail)

# Bottom coil runs into the tail.
c3 = coil(0, 62, 48, 46, 10, 7, 2, lit_to=46, open_right=True)
for k, v in c3.items():
    px[k] = rgba(v)

# Rattle, stacked and narrowing to a tip.
rattle = {}
for (y0, y1, a, b) in ((12, 15, 56, 64), (8, 11, 57, 63), (5, 7, 58, 62), (2, 4, 59, 61), (1, 2, 60, 60)):
    for y in range(y0, y1):
        for x in range(a, b + 1):
            c = W
            if x >= b - 1 and b > a:
                c = T
            if y == y1 - 1 and y1 - y0 > 1:
                c = T
            rattle[(x, y)] = c
for y, a, b in ((11, 57, 63), (7, 58, 62), (4, 59, 61)):
    for x in range(a, b + 1):
        rattle[(x, y)] = K
lay(rattle)

# Middle coil.
lay(coil(5, 51, 40, 36, 9, 7, 5))

# Top coil.
lay(coil(10, 45, 31, 27, 9, 7, 1))

# Head, ears and trunk: drawn as a half and mirrored, then lit from the left.
half = [
    '...............hhhhhhh.',
    '....mhhhm.....hhhhhhhhm',
    '..mhhhhhhhm..hhhhhhmmmd',
    '.mhhmmmmmhmKhhhhhmmmmmd',
    '.mhmpppppmmKhhhmmmmmmmm',
    'mhmpppppppmKhhmmmmmmmmm',
    'mhmppppppprKhmmmmmmmmmm',
    'mhmppppppprKhmmmmmmmmmm',
    'mhmppppppprKhhhhmmmmmmm',
    'mhmppppppprKmmhhhhmmmmh',
    'mhmppppppprKmmmKKmmddhh',
    'mhmppppppprKmmmmmmmdmhh',
    '.mhmppppprrKmmmmmmKmmhh',
    '.mhmpppprrrKdmmmmmKmmhh',
    '.mhmmpprrrKddmmmmdKdmhh',
    '..mhmmprrKddmmmmmdKmmhh',
    '..mmhmmrKddddmmmddKmmhh',
    '...mmmmKK.dddddddKddmhh',
    '....mm....ddddddKKmmmhh',
    '..................mmmhh',
    '..................ddmhh',
    '..................mmmhh',
    '..................mmmhh',
    '..................ddmhh',
    '..................mmmhh',
    '..................mmmhh',
    '..................ddmhh',
    '...................mmhh',
    '...................mmhh',
    '...................ddhh',
    '...................mmhh',
    '...................mmhh',
    '...................ddhm',
    '....................mhm',
    '....................mhm',
    '...................mmhm',
    '...................ddmd',
]
head = grid(mirror(half), PAL)
hp = head.load()
HX, HY = 5, 2
cx = 22
cells = {}
for y in range(head.height):
    for x in range(head.width):
        p = hp[x, y]
        if not p[3]:
            continue
        hexc = '%02x%02x%02x' % p[:3]
        # right side falls away from the light
        if x > cx + 1 and y >= 2 and x <= cx + 10 and y not in (8, 9):
            hexc = {H: M, M: D}.get(hexc, hexc) if y >= 19 or hexc == H else hexc
        if x >= cx + 9 and x <= cx + 10 and 5 <= y <= 16 and hexc == M:
            hexc = D
        if x >= cx + 12:
            hexc = {H: M, M: D}.get(hexc, hexc)
        cells[(x + HX, y + HY)] = hexc
lay(cells)

# Tusks: out and down from beside the trunk, tips hooking outward.
tusk_rows = ((19, 20, 22), (20, 20, 22), (21, 19, 21), (22, 19, 21), (23, 18, 20), (24, 18, 20),
             (25, 17, 19), (26, 17, 19), (27, 16, 18), (28, 16, 17), (29, 15, 16), (30, 14, 15), (31, 13, 14))
tusks = {}
for y, a, b in tusk_rows:
    for x in range(a, b + 1):
        tusks[(x, y)] = T if x == b and b - a > 1 else W
        mx = 54 - x
        tusks[(mx, y)] = T if x == a and b - a > 1 else W
lay(tusks)

im = outline(im)
save(im)
