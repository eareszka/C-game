from pix import *

D, R, L = '7c0a1b', 'b70000', 'ec8476'     # hide: shade, base, light
O, G, Y = 'fc9838', 'f0bc3c', 'fae488'     # chest glow, horns, claws, teeth
H = 'c18a39'                               # horn shade
W, HT = 90, 84
KC = (0, 0, 0)


def line(im, pts, c, width=1):
    ImageDraw.Draw(im).line(pts, fill=rgba(c), width=width)


def add(base, lay, ink=True):
    """Lay a part over the base, with a black line where it crosses what is behind it."""
    a, b = lay.load(), base.load()
    for y in range(HT):
        for x in range(W):
            if a[x, y][3]:
                b[x, y] = a[x, y]
            elif ink and b[x, y][3]:
                if any(0 <= x + i < W and 0 <= y + j < HT and a[x + i, y + j][3]
                       for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    b[x, y] = BLACK


def bevel(lay, base=R, dark=D, light=L, dk=2, lt=1):
    """Shade one flat part: light on the upper left edge, shade on the lower right."""
    src = lay.copy().load()
    px = lay.load()
    want = rgba(base)
    on = lambda x, y: 0 <= x < W and 0 <= y < HT and src[x, y][3]
    for y in range(HT):
        for x in range(W):
            if src[x, y] != want:
                continue
            if any(not on(x + n, y + n) or not on(x + n, y) or not on(x, y + n) for n in range(1, dk + 1)):
                px[x, y] = rgba(dark)
            elif light and (not on(x - lt, y) and not on(x, y - lt)):
                px[x, y] = rgba(light)


im = canvas(W, HT)


# ---- wings ----
def wing(side):
    X = (lambda x: x) if side == 0 else (lambda x: W - 1 - x)
    P = lambda pts: [(X(a), b) for a, b in pts]
    lay = canvas(W, HT)
    wrist = (23, 9)
    tips = [(0, 30), (3, 45), (10, 56), (21, 57)]
    notch = [(8, 37), (11, 46), (17, 49)]
    outer = [wrist, (15, 15), (8, 21), tips[0], notch[0], tips[1], notch[1], tips[2], notch[2], tips[3],
             (26, 48), (33, 48), (35, 34)]
    poly(lay, P(outer), R)

    # shade under each finger
    poly(lay, P([wrist, tips[0], notch[0], (17, 26)]), D)
    poly(lay, P([wrist, tips[1], notch[1], (20, 32)]), D)
    poly(lay, P([wrist, tips[2], notch[2], (24, 34)]), D)
    poly(lay, P([wrist, tips[3], (26, 48), (28, 36)]), D)

    # fingers: one solid black line each, stopping short of the tip
    for tip in tips:
        tx, ty = tip
        wx, wy = wrist
        line(lay, P([wrist, (tx + (wx - tx) // 7, ty + (wy - ty) // 7)]), KC)

    # leading edge and arm
    line(lay, P([wrist, (15, 15), (8, 21), (1, 29)]), R, 2)
    line(lay, P([(23, 8), (15, 14), (8, 20), (2, 27)]), L)
    poly(lay, P([(21, 8), (25, 7), (36, 34), (30, 38)]), R)
    line(lay, P([(21, 9), (30, 37)]), L if side == 0 else R)
    line(lay, P([(26, 9), (36, 36)]), D)
    # thumb claw
    poly(lay, P([(21, 8), (24, 8), (22, 3)]), Y)
    add(im, lay, ink=False)


wing(0)
wing(1)

# ---- tail: chunky steps, tapering, ending in a spade ----
path = [(46, 60, 7), (47, 66, 7), (48, 71, 6), (51, 75, 6), (56, 77, 5), (61, 78, 5),
        (66, 78, 4), (71, 77, 4), (75, 75, 3), (78, 72, 3)]
tail = canvas(W, HT)
for (a, b, s), (c, d, t) in zip(path, path[1:]):
    for n in range(6):
        x = a + (c - a) * n // 6
        y = b + (d - b) * n // 6
        z = s + (t - s) * n // 6
        rect(tail, x - z // 2, y - z // 2, z, z, R)
poly(tail, [(76, 74), (77, 68), (81, 68), (86, 62), (85, 70), (86, 74), (80, 75)], R)
bevel(tail, dk=1)
for x, y in [(52, 73), (57, 75), (62, 76), (67, 76), (72, 75), (76, 72)]:
    line(tail, [(x, y), (x + 1, y + 5)], KC)
line(tail, [(79, 72), (83, 67)], KC)
add(im, tail)

# ---- legs ----
for side in (0, 1):
    X = (lambda x: x) if side == 0 else (lambda x: W - 1 - x)
    leg = canvas(W, HT)
    xs = [(28, 40), (W - 1 - 40, W - 1 - 28)][side]
    oval(leg, xs[0], 50, xs[1] - xs[0] + 1, 16, R)
    poly(leg, [(X(31), 62), (X(39), 62), (X(38), 69), (X(32), 69)], R)
    poly(leg, [(X(26), 72), (X(29), 67), (X(40), 67), (X(42), 72)], R)
    bevel(leg)
    # toes split by black, claws in pale yellow
    for tx in (31, 36):
        line(leg, [(X(tx), 69), (X(tx), 72)], KC)
    for tx in (27, 33, 39):
        rect(leg, min(X(tx), X(tx + 1)), 73, 2, 1, Y)
        dot(leg, X(tx) , 74, Y)
    # thigh muscle line
    line(leg, [(X(33), 56), (X(37), 60), (X(37), 63)], KC)
    add(im, leg)

# ---- torso ----
body = canvas(W, HT)
half = [(38, 28), (32, 33), (30, 40), (31, 47), (34, 54), (37, 60), (44, 63)]
poly(body, half + [(W - 1 - a, b) for a, b in reversed(half)], R)
bevel(body)
# shoulder and flank lines
for side in (0, 1):
    X = (lambda x: x) if side == 0 else (lambda x: W - 1 - x)
    line(body, [(X(32), 36), (X(35), 38)], KC)
    line(body, [(X(32), 44), (X(34), 45)], KC)
    line(body, [(X(34), 51), (X(36), 52)], KC)
    if side == 0:
        line(body, [(X(33), 34), (X(36), 32)], L)
add(im, body)

# ---- glowing chest: stepped teardrop with plates ----
hw = [3, 5, 6, 7, 8, 8, 9, 9, 9, 9, 9, 9, 8, 8, 8, 7, 7, 6, 6, 5, 4, 4, 3, 2, 1]
top = 35
chest = canvas(W, HT)
for i, h in enumerate(hw):
    y = top + i
    rect(chest, 45 - h, y, h * 2, 1, O)
    if 2 <= i <= 22 and h > 2:
        g = h - 2
        rect(chest, 45 - g, y, g * 2, 1, G)
    if 5 <= i <= 18 and h > 5:
        c = h - 5
        rect(chest, 45 - c, y, c * 2, 1, Y)
for y, h in ((40, 7), (45, 7), (50, 6), (55, 3)):
    rect(chest, 45 - h, y, h - 2, 1, O)
    rect(chest, 45 + 2, y, h - 2, 1, O)
add(im, chest)

# ---- head ----
PAL = {'d': D, 'r': R, 'l': L, 'y': Y, 'g': G, 'h': H}
head = [
    "..........ddrr",
    ".........rrlrr",
    "........rrlrrr",
    "......rrrlrrrr",
    "....rrlllrrrrr",
    "...rrlrrrrrrrr",
    "...rlrKKrrrrrr",
    "..rlrrrKKKrrrr",
    "..rrrrrddKKKrr",
    ".rrrrrrdyyddrr",
    ".rdrrrrrddrrlr",
    "..ddrrrrrrrlrr",
    "...ddrrrrrlrrr",
    "....ddrrrlrrrr",
    "......rrlrrrrr",
    "......rrrrrKKr",
    "......rrrrrrKr",
    "......drrrrrrr",
    "......KKKKKKKK",
    "......yKKyKKKK",
    "......yddydddd",
    ".........ddddd",
]
rows = [r + r[::-1] for r in head]
hd = canvas(W, HT)
stamp(hd, grid(rows, PAL), 31, 9)
# light from the upper left: the right side of the head falls into shade
px = hd.load()
for y in range(9, 31):
    xs = [x for x in range(W) if px[x, y][3]]
    if xs:
        for n in range(2):
            x = xs[-1] - n
            if px[x, y] == rgba(R):
                px[x, y] = rgba(D)
    for x in range(45, W):
        if px[x, y] == rgba(L):
            px[x, y] = rgba(R)
add(im, hd)

# ---- horns ----
for side in (0, 1):
    X = (lambda x: x) if side == 0 else (lambda x: W - 1 - x)
    h = canvas(W, HT)
    poly(h, [(X(37), 14), (X(40), 11), (X(33), 6), (X(28), 0)], G)
    line(h, [(X(30), 2), (X(37), 12)], Y)
    line(h, [(X(32), 7), (X(39), 12)], H)
    add(im, h)

im = outline(im)
save(im)
