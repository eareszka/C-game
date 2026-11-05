from pix import *

G1, G2, G3 = 'a4aaba', '848694', '595965'
R1, R2 = 'b6433d', '7c0a1b'
CREAM = 'e8e0c0'
SP = 'dcf0ff'
EYE = 'fc9838'
K = '000000'
CX = 54

im = canvas(170, 110)


def mask_of(pts):
    m = canvas(im.width, im.height)
    poly(m, pts, 'ffffff')
    return m


def part(pts, base, light=None, dark=None, edge=True):
    """Fill a polygon, cut hard light and dark bands that follow its edge, ring it in black."""
    src = mask_of(pts).load()
    layer = canvas(im.width, im.height)
    out = layer.load()
    w, h = im.size

    def inside(x, y):
        return 0 <= x < w and 0 <= y < h and src[x, y][3]

    for y in range(h):
        for x in range(w):
            if not src[x, y][3]:
                continue
            c = base
            if dark and not inside(x + dark[0], y + dark[1]):
                c = dark[2]
            if light and not inside(x - light[0], y - light[1]):
                c = light[2]
            out[x, y] = rgba(c)
    if edge:
        ringed = outline(layer)
        im.paste(ringed, (-1, -1), ringed)
    else:
        im.alpha_composite(layer)


def only(pts, colour, on):
    """Fill a polygon, but only over the given colours."""
    m = mask_of(pts).load()
    px = im.load()
    want = {rgba(c) for c in on}
    for y in range(im.height):
        for x in range(im.width):
            if m[x, y][3] and px[x, y] in want:
                px[x, y] = rgba(colour)


def line(pts, colour, width=1):
    ImageDraw.Draw(im).line(pts, fill=rgba(colour), width=width)


def both(half):
    """Build a symmetric polygon from (dx, y) pairs running from top centre to bottom centre."""
    right = [(CX + a, b) for a, b in half]
    left = [(CX - a, b) for a, b in reversed(half) if a]
    return right + left


def at(table, dx):
    dx = abs(dx)
    for (a0, y0), (a1, y1) in zip(table, table[1:]):
        if a0 <= dx <= a1:
            return y0 + (y1 - y0) * (dx - a0) / (a1 - a0)
    return table[-1][1]


def barnacle(x, y):
    rect(im, x, y, 3, 2, G3)
    rect(im, x, y, 1, 1, G1)
    rect(im, x + 1, y + 1, 1, 1, K)


# ---- tail: a thick S rising behind the head, ending in a big fluke
body = [(76, 34), (82, 27), (90, 22), (99, 20), (106, 23), (112, 29), (117, 36), (120, 42), (123, 44),
        (126, 41), (127, 34), (128, 27), (135, 27), (136, 35), (136, 43), (134, 50), (130, 57), (124, 61),
        (118, 61), (112, 57), (106, 53), (100, 51), (94, 52), (88, 56), (83, 62), (76, 62)]
part(body, G2, light=(0, 4, G1), dark=(-1, -6, G3))

fluke = [(129, 32), (125, 27), (120, 23), (115, 18), (113, 13), (113, 7), (117, 10), (122, 12), (127, 15),
         (131, 20), (134, 16), (139, 13), (146, 11), (150, 12), (148, 17), (145, 22), (140, 27), (136, 30), (135, 34)]
part(fluke, G2, light=(2, 2, G1), dark=(-2, -2, G3))
line([(131, 21), (132, 29)], K)
for a, b in (((117, 14), (122, 20)), ((122, 15), (126, 22)), ((142, 15), (139, 22)), ((137, 17), (135, 23))):
    line([a, b], G3)

# belly pleats: short black ticks in the shaded underside only
for a, b in (((91, 47), (90, 52)), ((97, 45), (97, 50)), ((103, 46), (104, 51)), ((109, 49), (111, 54)),
             ((115, 53), (117, 58)), ((121, 55), (122, 60)), ((127, 53), (129, 56)), ((130, 48), (134, 50)),
             ((131, 42), (135, 43))):
    line([a, b], K)
# hide wrinkles on the back
for a, b in (((87, 31), (92, 28)), ((95, 27), (100, 27)), ((104, 30), (108, 34)), ((110, 37), (113, 42)),
             ((84, 39), (88, 36)), ((129, 32), (132, 32))):
    line([a, b], G3)
barnacle(98, 34)
barnacle(114, 45)

# ---- flippers, tucked behind the head
left_f = [(26, 50), (19, 52), (13, 57), (8, 63), (4, 70), (11, 70), (18, 69), (25, 66)]
part(left_f, G2, light=(1, 3, G1), dark=(-1, -3, G3))
line([(10, 66), (17, 59)], K)
line([(15, 67), (20, 62)], K)
right_f = [(82, 54), (90, 56), (97, 60), (103, 66), (108, 74), (100, 75), (92, 74), (84, 70)]
part(right_f, G2, light=(1, 3, G1), dark=(-1, -3, G3))
line([(93, 62), (100, 71)], K)
line([(90, 66), (94, 72)], K)

# ---- horns: small and cream
horn_l = [(23, 34), (19, 29), (16, 24), (15, 17), (20, 21), (26, 25), (31, 28)]
part(horn_l, CREAM, dark=(-1, -2, G1))
horn_r = [(108 - a, b) for a, b in horn_l]
part(horn_r, CREAM, dark=(-1, -2, G1))

# ---- head: a faceted dome
head = both([(0, 20), (10, 20), (18, 22), (25, 25), (30, 30), (34, 36), (37, 44), (38, 52), (38, 60), (36, 68),
             (32, 75), (26, 81), (18, 85), (9, 88), (0, 89)])
part(head, G2, dark=(-5, -5, G3))

# the lit dome, stepping down from the top left; shade follows the skull on the right
only([(20, 46), (22, 38), (27, 31), (34, 26), (42, 22), (52, 21), (61, 21), (66, 25), (68, 31), (67, 38), (63, 44),
      (58, 48), (20, 50)], G1, [G2])
only([(79, 27), (86, 33), (93, 46), (93, 70), (84, 54), (80, 42), (76, 34)], G3, [G2])

# blowholes
for dx in (-5, 5):
    rect(im, CX + dx - 2, 23, 5, 3, G3)
    rect(im, CX + dx - 1, 24, 3, 1, K)

# hide wrinkles that follow the dome, and a few barnacles
for a, b in (((32, 33), (37, 29)), ((29, 39), (33, 35)), ((43, 29), (48, 28)), ((40, 34), (44, 32)),
             ((60, 29), (64, 31)), ((72, 30), (75, 33)), ((75, 36), (78, 40)), ((50, 33), (58, 33)),
             ((52, 38), (56, 38))):
    line([a, b], G3)
barnacle(45, 37)
barnacle(70, 25)
barnacle(84, 50)

# angry brows and eyes
for s in (-1, 1):
    x = lambda d: CX + s * d
    part([(x(17), 45), (x(31), 39), (x(32), 43), (x(28), 47), (x(20), 47)], G3, edge=False)
    line([(x(14), 45), (x(22), 42), (x(33), 37)], K, 2)
    line([(x(32), 35), (x(24), 38)], G3)
    # a short black slit under the brow, and the eye: one solid mark
    ex = x(25) if s > 0 else x(26)
    rect(im, ex - 2, 43, 6, 3, K)
    rect(im, ex, 44, 2, 1, EYE)

# ---- the huge mouth
TOP = [(0, 55), (9, 54), (17, 52), (24, 49), (30, 47), (35, 48)]
BOT = [(0, 84), (9, 83), (17, 80), (24, 76), (30, 69), (34, 60), (35, 48)]
half = TOP + list(reversed(BOT))[1:]
part([(CX + a, b) for a, b in half] + [(CX - a, b) for a, b in reversed(half) if a], R1)

# the roll of the upper lip
line([(CX - 33, 45), (CX - 24, 47), (CX - 16, 50), (CX - 8, 52), (CX + 8, 52), (CX + 16, 50), (CX + 24, 47),
      (CX + 33, 45)], G3)

# dark gullet inside a ring of bright gum
inner_half = [(0, 60), (9, 59), (16, 57), (23, 54), (28, 53), (31, 56), (29, 63), (24, 70), (17, 75), (9, 78), (0, 79)]
part(both(inner_half), R2, edge=False)

# the tongue, a hump of bright gum at the back
part(both([(0, 69), (7, 69), (12, 71), (15, 74), (16, 79), (0, 80)]), R1, dark=(-1, -2, R2))
line([(CX, 71), (CX, 76)], R2)

# gum ridges at the corners
for dx in (-30, -26, 26, 30):
    line([(CX + dx, 60), (CX + dx + (3 if dx < 0 else -3), 64)], R2)


def tooth(dx, w, n, up):
    """One tooth: base on the lip, tip n px away, leaning toward the middle."""
    table = BOT if up else TOP
    a, b = dx - w / 2, dx + w / 2
    d = -1 if up else 1
    ya, yb = at(table, a) + d, at(table, b) + d
    ym = (ya + yb) / 2
    mid = (a + b) / 2
    lean = -2 if dx > 12 else 2 if dx < -12 else 0
    pts = [(CX + a, ya), (CX + b, yb), (CX + b - 1, ym + d * n * 0.55), (CX + mid + lean, ym + d * n),
           (CX + a + 1, ym + d * n * 0.55)]
    part([(round(p), round(q)) for p, q in pts], CREAM, dark=(-2, 0, G1))


for dx, w, n in ((-27, 5, 6), (-19, 7, 8), (-10, 7, 9), (0, 7, 9), (10, 7, 9), (19, 7, 8), (27, 5, 6)):
    tooth(dx, w, n, True)
for dx, w, n in ((-31, 4, 5), (-24, 6, 8), (-15, 7, 10), (-5, 8, 11), (6, 8, 11), (16, 7, 10), (25, 6, 8), (31, 4, 5)):
    tooth(dx, w, n, False)

# throat pleats under the jaw
for dx in (-24, -16, -8, 0, 8, 16, 24):
    y = at(BOT, dx) + 2
    line([(CX + dx, y), (CX + dx + (0 if dx == 0 else (-1 if dx < 0 else 1)), y + 3)], K)

# ---- two pale spouts curling out from the blowholes
for s in (-1, 1):
    x = lambda d: CX + s * d
    line([(x(5), 23), (x(6), 16), (x(8), 10)], SP, 3)
    line([(x(8), 10), (x(12), 6), (x(18), 4)], SP, 3)
    line([(x(18), 4), (x(24), 5), (x(28), 9)], SP, 2)
    line([(x(28), 9), (x(30), 13)], SP, 2)
    rect(im, x(29) - 1, 16, 2, 2, SP)
    rect(im, x(26) - 1, 13, 2, 2, SP)
    rect(im, x(33) - 1, 11, 1, 2, SP)
    # the shaded side of each stream
    only([(x(6) + 1, 22), (x(6) + 2, 15), (x(9) + 2, 10)], G1, [SP])

im = strip_outline(im)
im = outline(im)
save(im)
